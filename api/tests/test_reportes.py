"""Pruebas HTTP de reportes sin PostgreSQL real."""

from unittest.mock import ANY, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.repositories import reportes as repo
from app.routers.reportes import router


class ConexionFalsa:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class PoolFalso:
    def connection(self):
        return ConexionFalsa()


@pytest.fixture
def cliente_http():
    app = FastAPI()
    app.state.db_pool = PoolFalso()
    app.include_router(router)
    return TestClient(app)


def test_top_vinos(cliente_http, monkeypatch):
    datos = [{
        "cod_vino": 1,
        "vino": "Malbec de Prueba",
        "tipo": "tinto",
        "botellas_vendidas": 150,
    }]

    funcion = AsyncMock(return_value=datos)
    monkeypatch.setattr(repo, "top_vinos", funcion)

    respuesta = cliente_http.get("/reportes/top-vinos")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["botellas_vendidas"] == 150
    funcion.assert_awaited_once()


def test_ventas_por_sala(cliente_http, monkeypatch):
    datos = [{
        "id_sala": 1,
        "calle": "San Martin",
        "numero": "123B",
        "total_ventas": "250000.50",
    }]

    monkeypatch.setattr(
        repo, "ventas_por_sala",
        AsyncMock(return_value=datos),
    )

    respuesta = cliente_http.get("/reportes/ventas-por-sala")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["id_sala"] == 1
    assert respuesta.json()[0]["numero"] == "123B"


def test_vinos_sin_stock(cliente_http, monkeypatch):
    monkeypatch.setattr(
        repo, "existe_sala",
        AsyncMock(return_value=True),
    )

    datos = {
        "items": [{
            "cod_vino": 10,
            "vino": "Vino de Prueba",
            "tipo": "tinto",
            "anada": 2024,
            "volumen_ml": 750,
            "stock_sala": 0,
            "stock_deposito": 100,
        }],
        "total": 1,
        "pagina": 2,
        "tamanio": 5,
    }

    funcion = AsyncMock(return_value=datos)
    monkeypatch.setattr(repo, "vinos_sin_stock", funcion)

    respuesta = cliente_http.get(
        "/reportes/vinos-sin-stock"
        "?id_sala=3&page=2&page_size=5"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1
    assert respuesta.json()["pagina"] == 2
    assert respuesta.json()["items"][0]["stock_sala"] == 0
    funcion.assert_awaited_once_with(ANY, 3, 2, 5)


def test_sala_inexistente(cliente_http, monkeypatch):
    monkeypatch.setattr(
        repo, "existe_sala",
        AsyncMock(return_value=False),
    )

    funcion = AsyncMock()
    monkeypatch.setattr(repo, "vinos_sin_stock", funcion)

    respuesta = cliente_http.get(
        "/reportes/vinos-sin-stock?id_sala=99999"
    )

    assert respuesta.status_code == 404
    funcion.assert_not_awaited()


def test_falta_id_sala(cliente_http):
    respuesta = cliente_http.get(
        "/reportes/vinos-sin-stock"
    )

    assert respuesta.status_code == 422


def test_paginacion_invalida(cliente_http):
    respuesta = cliente_http.get(
        "/reportes/vinos-sin-stock?id_sala=1&page_size=101"
    )

    assert respuesta.status_code == 422


def test_transportista_activo(cliente_http, monkeypatch):
    datos = {
        "cod_transporte": 5,
        "razon_social": "Transporte de Prueba",
        "cantidad_ingresos": 25,
    }

    monkeypatch.setattr(
        repo, "transportista_activo",
        AsyncMock(return_value=datos),
    )

    respuesta = cliente_http.get(
        "/reportes/transportista-activo"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["cantidad_ingresos"] == 25


def test_transportista_sin_actividad(cliente_http, monkeypatch):
    monkeypatch.setattr(
        repo, "transportista_activo",
        AsyncMock(return_value=None),
    )

    respuesta = cliente_http.get(
        "/reportes/transportista-activo"
    )

    assert respuesta.status_code == 200
    assert respuesta.json() is None


def test_trazabilidad(cliente_http, monkeypatch):
    datos = {
        "vino": {
            "cod_vino": 12,
            "nombre_vino": "Vino de Prueba",
            "tipo": "tinto",
            "anada": 2024,
            "cuit_bodega": "30-12345678-9",
            "nombre_bodega": "Bodega de Prueba",
        },
        "lotes_registrados_en_bodega": [{
            "nro_lote": 1,
            "campania": 2025,
            "fecha_cosecha": "2025-03-15",
            "kg_cosechados": "1000.50",
            "id_finca": 2,
            "nombre_finca": "Finca de Prueba",
            "nro_parcela": 1,
            "superficie_parcela_ha": "3.25",
        }],
        "total_lotes_bodega": 1,
        "pagina": 1,
        "tamanio": 10,
        "relacion_directa_vino_lote": False,
        "aclaracion": "No existe relacion directa vino-lote.",
    }

    funcion = AsyncMock(return_value=datos)
    monkeypatch.setattr(repo, "trazabilidad", funcion)

    respuesta = cliente_http.get(
        "/reportes/trazabilidad/12?page_size=10"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["vino"]["cod_vino"] == 12
    assert respuesta.json()["relacion_directa_vino_lote"] is False
    assert len(respuesta.json()["lotes_registrados_en_bodega"]) == 1
    funcion.assert_awaited_once_with(ANY, 12, 1, 10)


def test_vino_inexistente(cliente_http, monkeypatch):
    monkeypatch.setattr(
        repo, "trazabilidad",
        AsyncMock(return_value=None),
    )

    respuesta = cliente_http.get(
        "/reportes/trazabilidad/99999"
    )

    assert respuesta.status_code == 404


def test_codigo_vino_invalido(cliente_http):
    respuesta = cliente_http.get(
        "/reportes/trazabilidad/0"
    )

    assert respuesta.status_code == 422
