"""Pruebas unitarias de la configuración para la nube (Fase 8, Antonio).

No necesitan base de datos: verifican las reglas de get_db_settings() y la
lógica de /salud con un pool simulado. Ninguna prueba se omite con skip.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import config
from app.core.config import get_db_settings, usuario_permitido
from app.routers import salud

REF = "abcdefghijklmnopqrst"  # 20 caracteres, formato de PROJECT_REF
SECRETO = "ContraseniaDePrueba123"


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    """Cada prueba arranca sin variables DB_* (ni las del .env local)."""
    for nombre in list(config.os.environ):
        if nombre.startswith("DB_"):
            monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setenv("DB_PASSWORD", SECRETO)


# ---------------------------------------------------------------- usuario

@pytest.mark.parametrize("usuario", ["bodega_api", f"bodega_api.{REF}"])
def test_usuarios_admitidos(usuario):
    assert usuario_permitido(usuario)


@pytest.mark.parametrize(
    "usuario",
    [
        "postgres",
        f"postgres.{REF}",
        "bodega_propietario",
        f"bodega_propietario.{REF}",
        "bodega_api.",
        "bodega_api.corto",
        f"bodega_api.{REF}-x",
        "bodega_api." + "a" * 65,
        f"bodega_api.{REF.upper()}",
        f"bodega_api.{REF}.extra",
        f"xbodega_api.{REF}",
        f" bodega_api.{REF}",
    ],
)
def test_usuarios_rechazados(usuario):
    assert not usuario_permitido(usuario)


def test_postgres_rechazado_sin_mostrar_secretos(monkeypatch):
    monkeypatch.setenv("DB_USER", f"postgres.{REF}")
    monkeypatch.setenv("DB_HOST", "aws-0-sa-east-1.pooler.supabase.com")
    with pytest.raises(RuntimeError) as exc:
        get_db_settings()
    assert SECRETO not in str(exc.value)
    assert REF not in str(exc.value)


# ---------------------------------------------------------------- TLS

def test_local_sin_sslmode_usa_prefer():
    s = get_db_settings()
    assert s.host == "127.0.0.1"
    assert s.sslmode == "prefer"
    assert not s.requiere_tls


def test_remoto_sin_sslmode_exige_require(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-0-sa-east-1.pooler.supabase.com")
    monkeypatch.setenv("DB_USER", f"bodega_api.{REF}")
    s = get_db_settings()
    assert s.sslmode == "require"
    assert s.requiere_tls


def test_configuracion_supabase_session_pooler(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-0-sa-east-1.pooler.supabase.com")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "postgres")
    monkeypatch.setenv("DB_USER", f"bodega_api.{REF}")
    monkeypatch.setenv("DB_SSLMODE", "require")
    monkeypatch.setenv("DB_POOL_MIN", "1")
    monkeypatch.setenv("DB_POOL_MAX", "2")
    s = get_db_settings()
    assert (s.pool_min, s.pool_max) == (1, 2)
    assert s.requiere_tls


@pytest.mark.parametrize("modo", ["prefer", "disable", "allow"])
def test_remoto_sin_tls_rechazado(monkeypatch, modo):
    monkeypatch.setenv("DB_HOST", "aws-0-sa-east-1.pooler.supabase.com")
    monkeypatch.setenv("DB_USER", f"bodega_api.{REF}")
    monkeypatch.setenv("DB_SSLMODE", modo)
    with pytest.raises(RuntimeError):
        get_db_settings()


def test_usuario_pooler_fuera_de_supabase_rechazado(monkeypatch):
    # El formato <rol>.<ref> solo tiene sentido en el pooler de Supabase.
    monkeypatch.setenv("DB_USER", f"bodega_api.{REF}")
    monkeypatch.setenv("DB_SSLMODE", "require")
    with pytest.raises(RuntimeError, match="bodega_api"):
        get_db_settings()


def test_bodega_api_sin_ref_en_pooler_rechazado(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-0-sa-east-1.pooler.supabase.com")
    monkeypatch.setenv("DB_USER", "bodega_api")
    with pytest.raises(RuntimeError, match="PROJECT_REF"):
        get_db_settings()


def test_otro_host_remoto_con_bodega_api_y_tls(monkeypatch):
    monkeypatch.setenv("DB_HOST", "base.ejemplo.com")
    s = get_db_settings()
    assert s.sslmode == "require"


@pytest.mark.parametrize("host", ["db", "postgres", "LOCALHOST"])
def test_hosts_locales_de_docker(monkeypatch, host):
    monkeypatch.setenv("DB_HOST", host)
    assert get_db_settings().sslmode == "prefer"


def test_host_vacio_rechazado(monkeypatch):
    monkeypatch.setenv("DB_HOST", "  ")
    with pytest.raises(RuntimeError, match="DB_HOST"):
        get_db_settings()


@pytest.mark.parametrize("puerto", ["0", "70000"])
def test_puerto_fuera_de_rango(monkeypatch, puerto):
    monkeypatch.setenv("DB_PORT", puerto)
    with pytest.raises(RuntimeError, match="DB_PORT"):
        get_db_settings()


@pytest.mark.parametrize("modo", ["disable", "allow", "cualquiera"])
def test_sslmode_no_admitido_ni_en_local(monkeypatch, modo):
    monkeypatch.setenv("DB_SSLMODE", modo)
    with pytest.raises(RuntimeError):
        get_db_settings()


def test_local_con_require(monkeypatch):
    monkeypatch.setenv("DB_SSLMODE", "require")
    assert get_db_settings().requiere_tls


def test_verify_full_necesita_certificado(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-0-sa-east-1.pooler.supabase.com")
    monkeypatch.setenv("DB_USER", f"bodega_api.{REF}")
    monkeypatch.setenv("DB_SSLMODE", "verify-full")
    with pytest.raises(RuntimeError):
        get_db_settings()
    monkeypatch.setenv("DB_SSLROOTCERT", "/etc/secrets/supabase-ca.crt")
    assert get_db_settings().sslrootcert == "/etc/secrets/supabase-ca.crt"


# ---------------------------------------------------------------- pool y puerto

def test_transaction_pooler_rechazado(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-0-sa-east-1.pooler.supabase.com")
    monkeypatch.setenv("DB_USER", f"bodega_api.{REF}")
    monkeypatch.setenv("DB_PORT", "6543")
    with pytest.raises(RuntimeError, match="Session pooler"):
        get_db_settings()


def test_puerto_6543_fuera_de_supabase_no_se_rechaza(monkeypatch):
    monkeypatch.setenv("DB_PORT", "6543")
    assert get_db_settings().port == 6543


@pytest.mark.parametrize("minimo,maximo", [("0", "2"), ("3", "2")])
def test_rango_de_pool_invalido(monkeypatch, minimo, maximo):
    monkeypatch.setenv("DB_POOL_MIN", minimo)
    monkeypatch.setenv("DB_POOL_MAX", maximo)
    with pytest.raises(RuntimeError):
        get_db_settings()


def test_falta_contrasenia(monkeypatch):
    monkeypatch.delenv("DB_PASSWORD")
    with pytest.raises(RuntimeError):
        get_db_settings()


def test_valor_numerico_invalido(monkeypatch):
    monkeypatch.setenv("DB_PORT", "cinco")
    with pytest.raises(RuntimeError):
        get_db_settings()


# ---------------------------------------------------------------- /salud (pool simulado)

class _CursorFalso:
    def __init__(self, fila):
        self._fila = fila

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def execute(self, sql):
        assert sql == "SELECT 1, current_user"

    async def fetchone(self):
        return self._fila


class _PGconnFalso:
    def __init__(self, ssl_in_use):
        self.ssl_in_use = ssl_in_use


class _ConexionFalsa:
    def __init__(self, ssl_in_use, rol):
        self.pgconn = _PGconnFalso(ssl_in_use)
        self._rol = rol

    def cursor(self):
        return _CursorFalso((1, self._rol))


class _ContextoConexion:
    def __init__(self, conexion):
        self._conexion = conexion

    async def __aenter__(self):
        return self._conexion

    async def __aexit__(self, *args):
        return False


class _PoolFalso:
    def __init__(self, ssl_in_use, rol="bodega_api"):
        self._conexion = _ConexionFalsa(ssl_in_use, rol)

    def connection(self):
        return _ContextoConexion(self._conexion)


def _cliente(ssl_in_use, requiere_tls, rol="bodega_api"):
    app = FastAPI()
    app.include_router(salud.router)
    app.state.db_pool = _PoolFalso(ssl_in_use, rol)
    app.state.db_requiere_tls = requiere_tls
    return TestClient(app)


def test_salud_con_tls_exigido_y_activo():
    r = _cliente(ssl_in_use=True, requiere_tls=True).get("/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "base_datos": "conectada", "tls": True}


def test_salud_con_tls_exigido_e_inactivo():
    r = _cliente(ssl_in_use=False, requiere_tls=True).get("/salud")
    assert r.status_code == 503
    assert r.json()["error"]["codigo"] == "DB_SIN_TLS"


def test_salud_local_sin_tls_exigido():
    r = _cliente(ssl_in_use=False, requiere_tls=False).get("/salud")
    assert r.status_code == 200
    assert r.json()["tls"] is False


def test_salud_rechaza_otro_rol():
    r = _cliente(ssl_in_use=True, requiere_tls=True, rol="postgres").get("/salud")
    assert r.status_code == 503
    assert r.json()["error"]["codigo"] == "DB_ROL_INVALIDO"


def test_la_configuracion_no_muestra_la_contrasenia():
    s = get_db_settings()
    assert SECRETO not in repr(s)
    assert SECRETO not in str(s)


# ---------------------------------------------------------------- tiempos de espera

@pytest.mark.parametrize("valor,esperado", [("10", 10.0), ("2.5", 2.5), ("0.5", 0.5)])
def test_pool_timeout_admite_decimales(monkeypatch, valor, esperado):
    monkeypatch.setenv("DB_POOL_TIMEOUT", valor)
    assert get_db_settings().pool_timeout == esperado


@pytest.mark.parametrize("valor", ["0", "-1", "abc", "nan", "inf"])
def test_pool_timeout_invalido(monkeypatch, valor):
    monkeypatch.setenv("DB_POOL_TIMEOUT", valor)
    with pytest.raises(RuntimeError, match="DB_POOL_TIMEOUT"):
        get_db_settings()


@pytest.mark.parametrize("valor", ["0", "2.5"])
def test_connect_timeout_entero_positivo(monkeypatch, valor):
    monkeypatch.setenv("DB_CONNECT_TIMEOUT", valor)
    with pytest.raises(RuntimeError, match="DB_CONNECT_TIMEOUT"):
        get_db_settings()
