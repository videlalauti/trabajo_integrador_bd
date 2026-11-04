"""Pruebas HTTP del CRUD de clientes sin base de datos real."""

from unittest.mock import ANY, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.repositories import clientes as repo
from app.routers.clientes import router


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


@pytest.fixture
def cliente_ejemplo():
    return {
        "id_cliente": 1,
        "nombre_razon_social": "Cliente de Prueba",
        "tipo_doc": "DNI",
        "nro_doc": "12345678",
        "direccion": "Calle de Prueba 123",
        "fecha_alta": "2026-11-04",
        "id_localidad": 1,
        "tipo_cliente": "socio",
        "descuento_especial": None,
        "zona_cobertura": None,
        "nro_habilitacion": None,
        "pais_destino": None,
    }


def test_listar_clientes(cliente_http, cliente_ejemplo, monkeypatch):
    funcion = AsyncMock(return_value=([cliente_ejemplo], 1))
    monkeypatch.setattr(repo, "listar_clientes", funcion)

    respuesta = cliente_http.get(
        "/clientes?page=2&page_size=5&tipo_cliente=socio"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1
    assert respuesta.json()["pagina"] == 2
    assert respuesta.json()["tamanio"] == 5
    assert len(respuesta.json()["items"]) == 1
    funcion.assert_awaited_once_with(ANY, 2, 5, "socio")


def test_obtener_cliente(cliente_http, cliente_ejemplo, monkeypatch):
    monkeypatch.setattr(
        repo, "obtener_cliente",
        AsyncMock(return_value=cliente_ejemplo),
    )

    respuesta = cliente_http.get("/clientes/1")

    assert respuesta.status_code == 200
    assert respuesta.json()["id_cliente"] == 1


def test_cliente_inexistente(cliente_http, monkeypatch):
    monkeypatch.setattr(
        repo, "obtener_cliente",
        AsyncMock(return_value=None),
    )

    respuesta = cliente_http.get("/clientes/999999")

    assert respuesta.status_code == 404


def test_crear_cliente(cliente_http, cliente_ejemplo, monkeypatch):
    funcion = AsyncMock(return_value=cliente_ejemplo)
    monkeypatch.setattr(repo, "crear_cliente", funcion)

    entrada = {
        clave: valor
        for clave, valor in cliente_ejemplo.items()
        if clave != "id_cliente"
    }

    respuesta = cliente_http.post("/clientes", json=entrada)

    assert respuesta.status_code == 201
    assert respuesta.json()["id_cliente"] == 1
    assert funcion.await_count == 1


def test_rechazar_tipo_invalido(cliente_http, cliente_ejemplo):
    entrada = {
        clave: valor
        for clave, valor in cliente_ejemplo.items()
        if clave != "id_cliente"
    }
    entrada["tipo_cliente"] = "desconocido"

    respuesta = cliente_http.post("/clientes", json=entrada)

    assert respuesta.status_code == 422


def test_actualizar_cliente(cliente_http, cliente_ejemplo, monkeypatch):
    funcion = AsyncMock(return_value=cliente_ejemplo)
    monkeypatch.setattr(repo, "actualizar_cliente", funcion)

    entrada = {
        clave: valor
        for clave, valor in cliente_ejemplo.items()
        if clave != "id_cliente"
    }

    respuesta = cliente_http.put("/clientes/1", json=entrada)

    assert respuesta.status_code == 200
    assert funcion.await_count == 1


def test_eliminar_cliente(cliente_http, monkeypatch):
    funcion = AsyncMock(return_value={"id_cliente": 1})
    monkeypatch.setattr(repo, "eliminar_cliente", funcion)

    respuesta = cliente_http.delete("/clientes/1")

    assert respuesta.status_code == 204
    assert respuesta.content == b""


def test_paginacion_invalida(cliente_http):
    respuesta = cliente_http.get("/clientes?page_size=101")

    assert respuesta.status_code == 422
