"""Offline: nunca abre PostgreSQL ni conexiones HTTP de red."""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.demo_guard import (
    ConfiguracionDemoInsegura, GuardianDemoAislada, _bearer_valido, validar_configuracion_demo,
)

TOKEN = "x" * 64  # Token FICTICIO solo de test
REF = "abcdefghijklmnopqrst"
FULL = "sjfyocokehaubuwwbhnw"


@pytest.fixture(autouse=True)
def limpiar_env(monkeypatch):
    for name in ("FASE8_DEMO_MODE", "FASE8_DEMO_TOKEN", "FASE8_DEMO_PROJECT_REF",
                 "FASE8_DEMO_LOCAL", "DB_HOST", "DB_USER", "DB_NAME", "DB_PASSWORD",
                 "DB_PORT", "DB_SSLMODE", "DB_SSLROOTCERT"):
        monkeypatch.delenv(name, raising=False)


def preparar(monkeypatch, ref=REF):
    for key, value in {
        "FASE8_DEMO_MODE": "aislado",
        "FASE8_DEMO_PROJECT_REF": ref,
        "FASE8_DEMO_TOKEN": TOKEN,
        "DB_HOST": "aws-1-us-west-2.pooler.supabase.com",
        "DB_USER": f"bodega_api.{ref}",
        "DB_NAME": "postgres",
        "DB_PASSWORD": "ficticia-no-real",
        "DB_PORT": "5432",
        "DB_SSLMODE": "verify-full",
        "DB_SSLROOTCERT": "/etc/secrets/prod-ca-2021.crt",
    }.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def cliente():
    app = FastAPI()
    app.add_middleware(GuardianDemoAislada)
    llamadas = []

    @app.api_route("/{ruta:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    async def handler(request: Request):
        llamadas.append((request.method, request.url.path))
        return {"ok": True}

    return TestClient(app), llamadas


@pytest.mark.parametrize("ref", ["", "abc", "password", FULL, "../../unsafe"])
def test_rechaza_proyecto_inseguro(monkeypatch, ref):
    preparar(monkeypatch, ref)
    with pytest.raises(ConfiguracionDemoInsegura):
        validar_configuracion_demo()


@pytest.mark.parametrize("name,value", [
    ("FASE8_DEMO_MODE", ""),
    ("FASE8_DEMO_MODE", "true"),
    ("FASE8_DEMO_TOKEN", "corto"),
    ("DB_HOST", "db.sjfyocokehaubuwwbhnw.supabase.co"),
    ("DB_USER", f"bodega_api.{FULL}"),
    ("DB_USER", "postgres"),
    ("DB_NAME", "bodegas_full"),
    ("DB_PORT", "6543"),
    ("DB_SSLMODE", "require"),
    ("DB_SSLROOTCERT", ""),
    ("DB_PASSWORD", ""),
    ("FASE8_DEMO_LOCAL", "1"),
])
def test_falla_cerrado_si_config_es_insegura(monkeypatch, name, value):
    preparar(monkeypatch)
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfiguracionDemoInsegura):
        validar_configuracion_demo()


def test_configuracion_remota_de_ensayo_correcta(monkeypatch):
    preparar(monkeypatch)
    validar_configuracion_demo()


@pytest.mark.parametrize("ruta", [
    "/comprobantes", "/transferencias",
    "/transferencias/12/renglones",
    "/transferencias/12/terminar",
    "/transferencias/12/procesar",
])
def test_post_solo_bearer(monkeypatch, cliente, ruta):
    preparar(monkeypatch)
    api, llamadas = cliente
    assert api.post(ruta).status_code == 401
    assert api.post(ruta, headers={"Authorization": "Bearer incorrecto"}).status_code == 401
    respuesta = api.post(ruta, headers={"Authorization": f"Bearer {TOKEN}"})
    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-store"
    assert llamadas == [("POST", ruta)]


@pytest.mark.parametrize("ruta", [
    "/vinos", "/vinos/1", "/clientes", "/clientes/3",
    "/comprobantes/1", "/transferencias/3", "/reportes/top-vinos",
    "/demo/identidad", "/demo/candidatos", "/demo/estado",
])
def test_get_protegidos(monkeypatch, cliente, ruta):
    preparar(monkeypatch)
    api, llamadas = cliente
    assert api.get(ruta).status_code == 401
    assert api.get(ruta, headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200
    assert llamadas == [("GET", ruta)]


@pytest.mark.parametrize("metodo,ruta", [
    ("DELETE", "/vinos/1"), ("PUT", "/vinos/1"), ("PATCH", "/clientes/1"),
    ("POST", "/clientes"), ("POST", "/ingresos"), ("POST", "/vinos"),
    ("POST", "/transferencias/0/procesar"), ("GET", "/docs"),
    ("GET", "/openapi.json"), ("GET", "/comprobantes/0"),
    ("GET", "/"), ("OPTIONS", "/comprobantes"),
])
def test_rutas_fuera_de_allowlist_bloqueadas(monkeypatch, cliente, metodo, ruta):
    preparar(monkeypatch)
    api, llamadas = cliente
    assert api.request(metodo, ruta, headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 403
    assert llamadas == []


def test_salud_publica_solo_si_config_segura(monkeypatch, cliente):
    preparar(monkeypatch)
    api, llamadas = cliente
    assert api.get("/salud").status_code == 200
    monkeypatch.setenv("DB_USER", f"bodega_api.{FULL}")
    assert api.get("/salud").status_code == 503
    assert llamadas == [("GET", "/salud")]


def test_no_escrituras_antes_de_configurar(cliente):
    api, llamadas = cliente
    assert api.post("/comprobantes", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 503
    assert llamadas == []


def test_local_solo_base_descartable(monkeypatch, cliente):
    preparar(monkeypatch)
    for k, v in (("DB_HOST", "127.0.0.1"), ("DB_USER", "bodega_api"),
                 ("DB_NAME", "bodegas_fase8_demo_local"), ("FASE8_DEMO_LOCAL", "1")):
        monkeypatch.setenv(k, v)
    api, llamadas = cliente
    assert api.post("/comprobantes", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200
    monkeypatch.setenv("DB_NAME", "bodegas_g1c_final_full")
    assert api.post("/comprobantes", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 503
    assert llamadas == [("POST", "/comprobantes")]


def test_credenciales_no_se_imprimen(monkeypatch, cliente):
    preparar(monkeypatch)
    monkeypatch.setenv("DB_USER", "postgres")
    api, llamadas = cliente
    res = api.post("/comprobantes", headers={"Authorization": f"Bearer {TOKEN}"})
    assert res.status_code == 503
    assert "postgres" not in res.text and TOKEN not in res.text
    assert llamadas == []


@pytest.mark.parametrize("malformado", [
    "Bearer contraseña-española",
    "Bearer tóken-no-ASCII-ñ",
    "Bearer 🙃🙃🙃",
    "Basic " + TOKEN,
    "Bearer " + TOKEN + "ñ",
    "Bearer",
    "",
])
def test_token_malformado_o_unicode_devuelve_falso_sin_typeerror(malformado):
    assert _bearer_valido(malformado, TOKEN) is False


def test_bearer_valido_solo_con_token_exacto():
    assert _bearer_valido(f"Bearer {TOKEN}", TOKEN)
    assert _bearer_valido(f"bearer {TOKEN}", TOKEN)
    assert not _bearer_valido(f"Bearer {TOKEN}x", TOKEN)

