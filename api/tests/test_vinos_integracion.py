

"""Pruebas de integración HTTP del módulo de vinos."""

import uuid
from contextlib import asynccontextmanager

import httpx
import psycopg
import pytest
import pytest_asyncio
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

from app.core.config import get_db_settings
from app.core.errores import manejador_sqlstate
from app.routers.vinos import router


class RollbackDePrueba(Exception):
    """Señal para revertir los cambios al finalizar una prueba."""


class PoolDePrueba:
    """Entrega una conexión controlada por la prueba."""

    def __init__(self, conn):
        self.conn = conn

    @asynccontextmanager
    async def connection(self):
        yield self.conn


def crear_app(pool):
    app = FastAPI()
    app.state.db_pool = pool
    app.add_exception_handler(psycopg.Error, manejador_sqlstate)
    app.include_router(router)
    return app


def configuracion_segura():
    cfg = get_db_settings()

    if cfg.dbname != "bodegas_fase6_lautaro_test":
        pytest.fail(
            "Las pruebas solo pueden ejecutarse contra "
            "bodegas_fase6_lautaro_test."
        )

    return cfg


def datos_vino():
    return {
        "nombre": f"TEST INTEGRACION {uuid.uuid4().hex[:12]}",
        "tipo": "tinto",
        "anada": 2025,
        "volumen_ml": 750,
        "graduacion": "13.50",
        "precio": "15000",
        "cuit_bodega": "30999000300",
        "cepas": [
            {"id_cepa": 21, "porcentaje": 100}
        ],
        "maridajes": [1],
    }


@pytest_asyncio.fixture
async def entorno():
    """
    Entorno con rollback exterior.
    Para pruebas que no necesitan confirmar la transacción.
    """
    cfg = configuracion_segura()

    conn = await psycopg.AsyncConnection.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.dbname,
        user=cfg.user,
        password=cfg.password,
    )

    app = crear_app(PoolDePrueba(conn))

    try:
        async with conn.transaction():
            transport = httpx.ASGITransport(app=app)

            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as cliente:
                yield cliente, conn

            raise RollbackDePrueba()

    except RollbackDePrueba:
        pass

    finally:
        await conn.close()


@pytest_asyncio.fixture
async def entorno_real():
    """
    Entorno con transacciones reales.
    Necesario para verificar triggers diferidos.
    """
    cfg = configuracion_segura()

    pool = AsyncConnectionPool(
        conninfo="",
        kwargs={
            "host": cfg.host,
            "port": cfg.port,
            "dbname": cfg.dbname,
            "user": cfg.user,
            "password": cfg.password,
        },
        min_size=1,
        max_size=2,
        open=False,
    )

    await pool.open(wait=True)

    app = crear_app(pool)

    try:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as cliente:
            yield cliente

    finally:
        await pool.close()


# --------------------------------------------------
# PRUEBA 1: CREACIÓN VÁLIDA
# --------------------------------------------------

@pytest.mark.asyncio
async def test_crear_vino_valido(entorno):
    cliente, _ = entorno
    datos = datos_vino()

    respuesta = await cliente.post("/vinos", json=datos)

    assert respuesta.status_code == 201, respuesta.text

    codigo = respuesta.json()["cod_vino"]

    detalle = await cliente.get(f"/vinos/{codigo}")

    assert detalle.status_code == 200
    assert detalle.json()["nombre"] == datos["nombre"]
    assert len(detalle.json()["cepas"]) == 1


# --------------------------------------------------
# PRUEBA 2: RECHAZO POR RN-05
# --------------------------------------------------

@pytest.mark.asyncio
async def test_rechazar_cepas_rn05(entorno_real):
    cliente = entorno_real
    datos = datos_vino()

    datos["cepas"] = [
        {"id_cepa": 21, "porcentaje": 40},
        {"id_cepa": 23, "porcentaje": 50},
    ]

    respuesta = await cliente.post("/vinos", json=datos)

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["error"]["codigo"] == "P0001"


# --------------------------------------------------
# PRUEBA 3: ROLLBACK ANTE ERROR
# --------------------------------------------------

@pytest.mark.asyncio
async def test_rollback_creacion_invalida(entorno_real):
    cliente = entorno_real
    datos = datos_vino()

    datos["cepas"] = [
        {"id_cepa": 21, "porcentaje": 40},
        {"id_cepa": 23, "porcentaje": 50},
    ]

    respuesta = await cliente.post("/vinos", json=datos)

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["error"]["codigo"] == "P0001"

    cfg = configuracion_segura()

    async with await psycopg.AsyncConnection.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.dbname,
        user=cfg.user,
        password=cfg.password,
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT COUNT(*)
                FROM vino
                WHERE nombre = %s
                """,
                (datos["nombre"],),
            )
            cantidad = (await cur.fetchone())[0]

    assert cantidad == 0


# --------------------------------------------------
# PRUEBA 4: LISTADO PAGINADO Y FILTRADO
# --------------------------------------------------

@pytest.mark.asyncio
async def test_listado_paginado_y_filtrado(entorno):
    cliente, _ = entorno

    respuesta = await cliente.get(
        "/vinos",
        params={
            "page": 1,
            "page_size": 5,
            "cepa": 21,
        },
    )

    assert respuesta.status_code == 200, respuesta.text

    cuerpo = respuesta.json()

    assert cuerpo["pagina"] == 1
    assert cuerpo["tamanio"] == 5
    assert len(cuerpo["items"]) <= 5
    assert cuerpo["total"] >= len(cuerpo["items"])


# --------------------------------------------------
# PRUEBA 5: ELIMINACIÓN CON DEPENDENCIAS
# --------------------------------------------------

@pytest.mark.asyncio
async def test_eliminacion_con_dependencias(entorno):
    cliente, conn = entorno

    # Buscar un vino con dependencias ON DELETE RESTRICT.
    # Solo se consultan tablas autorizadas para bodega_api.
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT v.cod_vino
            FROM vino v
            WHERE EXISTS (
                SELECT 1
                FROM renglon_comprobante rc
                WHERE rc.cod_vino = v.cod_vino
            )
            OR EXISTS (
                SELECT 1
                FROM renglon_ingreso ri
                WHERE ri.cod_vino = v.cod_vino
            )
            OR EXISTS (
                SELECT 1
                FROM renglon_transferencia rt
                WHERE rt.cod_vino = v.cod_vino
            )
            OR EXISTS (
                SELECT 1
                FROM stock_sala ss
                WHERE ss.cod_vino = v.cod_vino
            )
            OR EXISTS (
                SELECT 1
                FROM stock_deposito sd
                WHERE sd.cod_vino = v.cod_vino
            )
            ORDER BY v.cod_vino
            LIMIT 1
            """
        )

        fila = await cur.fetchone()

    if fila is None:
        pytest.skip(
            "No se encontró un vino con dependencias "
            "ON DELETE RESTRICT en la base de pruebas."
        )

    codigo = fila[0]

    # Comprobar que existe mediante la API.
    detalle = await cliente.get(f"/vinos/{codigo}")
    assert detalle.status_code == 200, detalle.text

    # Intentar eliminarlo mediante HTTP.
    respuesta = await cliente.delete(f"/vinos/{codigo}")

    # El manejador actualizado debe devolver HTTP 409.
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["error"]["codigo"] in ("23001", "23503")
