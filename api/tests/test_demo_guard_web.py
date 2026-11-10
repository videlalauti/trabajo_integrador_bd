"""Pruebas OFFLINE de autenticacion web: nunca abren PostgreSQL ni red externa."""
import pytest
from fastapi.testclient import TestClient

from app.core import evaluador
from app.demo_main import app

TOKEN_TECNICO = "t" * 64
CLAVE_FICTICIA = "solo-prueba-unitaria-evaluador-2026"
REF_FICTICIA = "abcdefghijklmnopqrst"


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    evaluador._fallos.clear()
    for campo, valor in {
        "FASE8_DEMO_MODE": "aislado",
        "FASE8_DEMO_PROJECT_REF": REF_FICTICIA,
        "FASE8_DEMO_TOKEN": TOKEN_TECNICO,
        "DB_HOST": "aws-1-us-west-2.pooler.supabase.com",
        "DB_USER": f"bodega_api.{REF_FICTICIA}",
        "DB_NAME": "postgres",
        "DB_PASSWORD": "ficticia",
        "DB_PORT": "5432",
        "DB_SSLMODE": "verify-full",
        "DB_SSLROOTCERT": "/etc/secrets/ca-evaluacion.crt",
        "FASE8_EVAL_ENABLED": "1",
        "FASE8_EVAL_PASSWORD": CLAVE_FICTICIA,
        "FASE8_EVAL_SIGNING_KEY": "s" * 64,
    }.items():
        monkeypatch.setenv(campo, valor)
    yield
    evaluador._fallos.clear()


@pytest.fixture
def cliente():
    # Sin contexto "with": no se ejecuta lifespan; ninguna BD se abre.
    return TestClient(app, base_url="https://testserver")


def test_login_crea_cookie_http_only_secure_y_csrf(cliente):
    res = cliente.post("/demo/acceso", json={"clave": CLAVE_FICTICIA})
    assert res.status_code == 200
    assert res.json()["autorizado"] is True
    assert len(res.json()["csrf"]) == 64
    cookie = res.headers["set-cookie"].lower()
    assert "httponly" in cookie and "secure" in cookie and "samesite=lax" in cookie
    assert res.headers["cache-control"] == "no-store"
    sesion = cliente.get("/demo/sesion")
    assert sesion.status_code == 200
    assert sesion.json()["csrf"] == res.json()["csrf"]
    assert CLAVE_FICTICIA not in res.text


def test_login_incorrecto_no_autoriza(cliente):
    assert cliente.post("/demo/acceso", json={"clave": "incorrecta"}).status_code == 401
    assert cliente.get("/demo/sesion").status_code == 401
    assert cliente.post("/vinos", json={}).status_code == 401


def test_cookie_sin_csrf_no_puede_escribir(cliente):
    login = cliente.post("/demo/acceso", json={"clave": CLAVE_FICTICIA})
    assert login.status_code == 200
    assert cliente.get("/demo/identidad").status_code == 200
    assert cliente.post("/vinos", json={}).status_code == 403
    assert cliente.put("/vinos/1", json={}).status_code == 403
    assert cliente.post("/comprobantes", json={}).status_code == 403
    assert cliente.post("/vinos", json={}, headers={"X-CSRF-Token": "0"*64}).status_code == 403


def test_csrf_valido_permite_llegar_al_validador_sin_acceder_a_bd(cliente):
    csrf = cliente.post("/demo/acceso", json={"clave": CLAVE_FICTICIA}).json()["csrf"]
    # Body vacio -> Pydantic 422 ANTES de cualquier SQL.
    for metodo, ruta in [
        ("POST", "/vinos"), ("PUT", "/vinos/1"),
        ("POST", "/comprobantes"), ("POST", "/transferencias"),
        ("POST", "/ingresos"), ("POST", "/clientes"),
    ]:
        res = cliente.request(metodo, ruta, json={}, headers={"X-CSRF-Token": csrf})
        assert res.status_code == 422, (metodo, ruta, res.status_code)


def test_bearer_tecnico_no_adquiere_nuevas_rutas(cliente):
    auth = {"Authorization": f"Bearer {TOKEN_TECNICO}"}
    assert cliente.post("/vinos", json={}, headers=auth).status_code == 401
    assert cliente.post("/comprobantes", json={}, headers=auth).status_code == 422
    assert cliente.put("/vinos/1", json={}, headers=auth).status_code == 401


def test_logout_invalida_cookie_del_navegador(cliente):
    csrf = cliente.post("/demo/acceso", json={"clave": CLAVE_FICTICIA}).json()["csrf"]
    assert cliente.post("/demo/salir", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert cliente.get("/demo/sesion").status_code == 401


def test_modo_web_fail_closed_si_falta_clave(cliente, monkeypatch):
    monkeypatch.delenv("FASE8_EVAL_SIGNING_KEY")
    assert cliente.get("/salud").status_code == 503
    assert cliente.post("/demo/acceso", json={"clave": CLAVE_FICTICIA}).status_code == 503


def test_no_habilitado_conserva_guard_anterior(cliente, monkeypatch):
    monkeypatch.delenv("FASE8_EVAL_ENABLED")
    assert cliente.post("/demo/acceso", json={"clave": CLAVE_FICTICIA}).status_code == 403
    assert cliente.post("/vinos", json={}).status_code == 403
    auth = {"Authorization": f"Bearer {TOKEN_TECNICO}"}
    assert cliente.post("/comprobantes", json={}, headers=auth).status_code == 422


def test_limite_intentos_incorrectos(cliente):
    for i in range(8):
        assert cliente.post("/demo/acceso", json={"clave": f"equivocada-{i}"}).status_code == 401
    assert cliente.post("/demo/acceso", json={"clave": CLAVE_FICTICIA}).status_code == 429


def test_firma_y_expiracion(monkeypatch):
    cookie = evaluador.crear_sesion()
    assert evaluador.validar_sesion(cookie)
    assert not evaluador.validar_sesion(cookie + "a")
    assert not evaluador.validar_sesion("9999999999." + "a"*48 + "." + "0"*64)
    ahora = evaluador.time.time()
    monkeypatch.setattr(evaluador.time, "time", lambda: ahora + evaluador.DURACION_SEGUNDOS + 1)
    assert not evaluador.validar_sesion(cookie)
