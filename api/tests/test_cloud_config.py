"""Pruebas unitarias de configuración: no requieren acceso a la nube."""
import pytest

from app.core.config import get_db_settings


@pytest.fixture(autouse=True)
def env_controlado(monkeypatch):
    for clave in (
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
        "DB_POOL_MIN", "DB_POOL_MAX", "DB_SSLMODE",
    ):
        monkeypatch.delenv(clave, raising=False)
    monkeypatch.setenv("DB_PASSWORD", "contrasena-solo-para-pruebas")


def test_configuracion_local_retrocompatible():
    cfg = get_db_settings()
    assert cfg.user == "bodega_api"
    assert cfg.host == "127.0.0.1"
    assert cfg.sslmode == "prefer"


def test_pooler_supabase_acepta_rol_minimo(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-1-us-west-2.pooler.supabase.com")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_USER", "bodega_api.abcdefghijklmnopqrst")
    monkeypatch.setenv("DB_SSLMODE", "require")
    cfg = get_db_settings()
    assert cfg.user.startswith("bodega_api.")
    assert cfg.sslmode == "require"


def test_rechaza_usuario_administrador(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-1-us-west-2.pooler.supabase.com")
    monkeypatch.setenv("DB_USER", "postgres.abcdefghijklmnopqrst")
    monkeypatch.setenv("DB_SSLMODE", "require")
    with pytest.raises(RuntimeError, match="bodega_api"):
        get_db_settings()


def test_exige_tls_para_supabase(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-1-us-west-2.pooler.supabase.com")
    monkeypatch.setenv("DB_USER", "bodega_api.abcdefghijklmnopqrst")
    monkeypatch.setenv("DB_SSLMODE", "prefer")
    with pytest.raises(RuntimeError, match="DB_SSLMODE"):
        get_db_settings()


def test_exige_session_pooler(monkeypatch):
    monkeypatch.setenv("DB_HOST", "aws-1-us-west-2.pooler.supabase.com")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_USER", "bodega_api.abcdefghijklmnopqrst")
    monkeypatch.setenv("DB_SSLMODE", "require")
    with pytest.raises(RuntimeError, match="Session pooler"):
        get_db_settings()


def test_rechaza_pool_invalido(monkeypatch):
    monkeypatch.setenv("DB_POOL_MIN", "3")
    monkeypatch.setenv("DB_POOL_MAX", "2")
    with pytest.raises(RuntimeError, match="Rango inválido"):
        get_db_settings()


def test_rechaza_password_vacio(monkeypatch):
    monkeypatch.delenv("DB_PASSWORD")
    with pytest.raises(RuntimeError, match="DB_PASSWORD"):
        get_db_settings()
