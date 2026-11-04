"""Pruebas reales de Reportes con PostgreSQL."""

import asyncio
from decimal import Decimal

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_db_settings
from app.core.database import lifespan
from app.core.errores import manejador_sqlstate
from app.routers import reportes


@pytest.fixture(scope="module")
def api_reportes_real():
    config = get_db_settings()

    assert config.dbname == "bodegas_fase6_fabricio_test", (
        "PROTECCION: base de pruebas incorrecta."
    )
    assert config.user == "bodega_api", (
        "PROTECCION: debe utilizarse bodega_api."
    )

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(psycopg.Error, manejador_sqlstate)
    app.include_router(reportes.router)

    with TestClient(
        app,
        backend_options={
            "loop_factory": asyncio.SelectorEventLoop
        },
    ) as cliente:
        yield cliente


def test_top_vinos_real(api_reportes_real):
    respuesta = api_reportes_real.get("/reportes/top-vinos")

    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()

    assert isinstance(datos, list)
    assert len(datos) == 10

    for vino in datos:
        assert isinstance(vino["cod_vino"], int)
        assert isinstance(vino["vino"], str)
        assert "tipo" in vino
        assert vino["botellas_vendidas"] > 0

    cantidades = [v["botellas_vendidas"] for v in datos]
    assert cantidades == sorted(cantidades, reverse=True)


def test_ventas_por_sala_real(api_reportes_real):
    respuesta = api_reportes_real.get(
        "/reportes/ventas-por-sala"
    )

    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()

    assert isinstance(datos, list)
    assert len(datos) > 0

    for sala in datos:
        assert isinstance(sala["id_sala"], int)
        assert isinstance(sala["calle"], str)
        assert isinstance(sala["numero"], str)
        assert Decimal(str(sala["total_ventas"])) >= 0


def test_vinos_sin_stock_real(api_reportes_real):
    url = "/reportes/vinos-sin-stock"

    respuesta = api_reportes_real.get(
        url + "?id_sala=1&page=1&page_size=5"
    )

    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()

    assert datos["pagina"] == 1
    assert datos["tamanio"] == 5
    assert datos["total"] >= 0
    assert len(datos["items"]) <= 5

    for vino in datos["items"]:
        assert vino["stock_sala"] == 0
        assert vino["stock_deposito"] > 0

    segunda = api_reportes_real.get(
        url + "?id_sala=1&page=2&page_size=5"
    )

    assert segunda.status_code == 200, segunda.text
    datos2 = segunda.json()

    assert datos2["pagina"] == 2
    assert datos2["total"] == datos["total"]

    ids1 = {v["cod_vino"] for v in datos["items"]}
    ids2 = {v["cod_vino"] for v in datos2["items"]}

    assert ids1.isdisjoint(ids2)


def test_sala_inexistente_real(api_reportes_real):
    respuesta = api_reportes_real.get(
        "/reportes/vinos-sin-stock?id_sala=999999"
    )

    assert respuesta.status_code == 404


def test_transportista_activo_real(api_reportes_real):
    respuesta = api_reportes_real.get(
        "/reportes/transportista-activo"
    )

    assert respuesta.status_code == 200, respuesta.text

    datos = respuesta.json()

    # Sin ingresos recientes, el resultado puede ser null.
    if datos is not None:
        assert isinstance(datos["cod_transporte"], int)
        assert isinstance(datos["razon_social"], str)
        assert datos["cantidad_ingresos"] > 0


def test_trazabilidad_real(api_reportes_real):
    # Obtener un codigo de vino que exista realmente.
    top = api_reportes_real.get("/reportes/top-vinos")
    assert top.status_code == 200, top.text

    cod_vino = top.json()[0]["cod_vino"]

    respuesta = api_reportes_real.get(
        f"/reportes/trazabilidad/{cod_vino}"
        "?page=1&page_size=3"
    )

    assert respuesta.status_code == 200, respuesta.text

    datos = respuesta.json()

    assert datos["vino"]["cod_vino"] == cod_vino
    assert "nombre_bodega" in datos["vino"]
    assert datos["relacion_directa_vino_lote"] is False
    assert datos["total_lotes_bodega"] >= 0
    assert datos["pagina"] == 1
    assert datos["tamanio"] == 3

    lotes = datos["lotes_registrados_en_bodega"]
    assert isinstance(lotes, list)
    assert len(lotes) <= 3

    for lote in lotes:
        assert "nro_lote" in lote
        assert "nombre_finca" in lote
        assert "nro_parcela" in lote

    segunda = api_reportes_real.get(
        f"/reportes/trazabilidad/{cod_vino}"
        "?page=2&page_size=3"
    )

    assert segunda.status_code == 200, segunda.text
    assert segunda.json()["pagina"] == 2
    assert (
        segunda.json()["total_lotes_bodega"]
        == datos["total_lotes_bodega"]
    )


def test_vino_inexistente_real(api_reportes_real):
    respuesta = api_reportes_real.get(
        "/reportes/trazabilidad/999999999"
    )

    assert respuesta.status_code == 404


def test_paginacion_invalida_real(api_reportes_real):
    respuesta = api_reportes_real.get(
        "/reportes/vinos-sin-stock"
        "?id_sala=1&page_size=101"
    )

    assert respuesta.status_code == 422
