"""Apoyo para las pruebas de ingresos y transferencias (Antonio).

PROTECCION DE DATOS
  Estas son pruebas de INTEGRACION que escriben datos con COMMIT (crean
  ingresos y transferencias y mueven stock). Por eso:
  - Solo se ejecutan contra la base descartable BASE_DE_PRUEBA.
  - Antes de crear la app se abre una conexion directa con la configuracion
    del .env y se verifica current_database() y current_user. Si la base no
    es BASE_DE_PRUEBA, se llama a pytest.exit: la sesion se detiene sin
    enviar ninguna solicitud ni modificar datos.
  - Una conexion fallida, una configuracion incompleta o /salud distinto de
    200 se reportan como ERROR (nunca se omiten con pytest.skip). El error de
    conexion se relanza sin la cadena de conexion, para no mostrar la
    contrasenia en la salida de pytest.

APP DE PRUEBA
  Usa el MISMO lifespan (pool como bodega_api) y el MISMO manejador central
  de errores que app/main.py, mas los routers de este modulo, para no
  modificar main.py (reservado a coordinacion).
"""
import asyncio
import sys

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg_pool import PoolTimeout

# psycopg asincronico no funciona con el ProactorEventLoop por defecto de
# Windows: se usa el SelectorEventLoop durante las pruebas.
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.config import get_db_settings  # noqa: E402
from app.core.database import lifespan  # noqa: E402
from app.core.errores import manejador_sqlstate  # noqa: E402
from app.routers import ingresos, salud, transferencias  # noqa: E402

BASE_DE_PRUEBA = "bodegas_fase6_antonio_test"
ROL_ESPERADO = "bodega_api"

# Datos reales del dataset (verificados en Fase 5):
TRANSPORTISTA = 1                # Transportes DEMO Atuel 001
CUIT_BODEGA = "30999000009"      # Bodega DEMO Atuel 001
VINO_DE_LA_BODEGA = 125          # Fuego Atuel 0125, tinto 2023, 750 ml
SALA = 1                         # San Rafael, Boulevard Formosa 100
CANTIDAD_IMPOSIBLE = 10_000_000  # mayor que cualquier stock del deposito


def verificar_base_de_prueba() -> None:
    """Detiene la sesion si la base real no es la descartable de Antonio.

    get_db_settings() lanza RuntimeError si falta la contrasenia o el rol no
    es bodega_api, y psycopg.connect lanza OperationalError si no hay
    conexion: ambos casos quedan como ERROR de la prueba.
    """
    cfg = get_db_settings()
    if cfg.dbname != BASE_DE_PRUEBA:
        pytest.exit(
            f"DB_NAME es '{cfg.dbname}': las pruebas de Antonio solo corren sobre "
            f"'{BASE_DE_PRUEBA}'. No se modifico ningun dato.",
            returncode=3,
        )
    try:
        with psycopg.connect(
            host=cfg.host, port=cfg.port, dbname=cfg.dbname,
            user=cfg.user, password=cfg.password, connect_timeout=5,
        ) as conn:
            base, usuario = conn.execute("SELECT current_database(), current_user").fetchone()
    except psycopg.Error as exc:
        # Se relanza como ERROR (no skip) SIN el traceback interno de psycopg,
        # que mostraria la cadena de conexion con la contrasenia.
        raise RuntimeError(
            f"No se pudo conectar a {cfg.host}:{cfg.port}/{cfg.dbname} como {cfg.user}: "
            f"{type(exc).__name__}: {exc}"
        ) from None
    if base != BASE_DE_PRUEBA or usuario != ROL_ESPERADO:
        pytest.exit(
            f"Conexion real a '{base}' como '{usuario}': se esperaba "
            f"'{BASE_DE_PRUEBA}' como '{ROL_ESPERADO}'. No se modifico ningun dato.",
            returncode=3,
        )


def crear_app_prueba() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(psycopg.Error, manejador_sqlstate)
    app.add_exception_handler(PoolTimeout, manejador_sqlstate)
    app.include_router(salud.router)
    app.include_router(ingresos.router)
    app.include_router(transferencias.router)
    return app


@pytest.fixture(scope="module")
def client():
    verificar_base_de_prueba()
    with TestClient(crear_app_prueba()) as c:
        r = c.get("/salud")
        assert r.status_code == 200, f"/salud no respondio 200 ({r.status_code}): {r.text}"
        yield c
