
"""Pruebas HTTP del modulo de comprobantes.

Estas pruebas simulan el servicio.
No modifican PostgreSQL.
"""

from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.comprobantes import router
from app.services import comprobantes as servicio


def crear_cliente_prueba():
    app = FastAPI()
    app.state.db_pool = object()
    app.include_router(router)
    return TestClient(app)


def comprobante_ejemplo():
    return {
        "nro_comprobante": 123,
        "fecha": datetime(2026, 11, 4, 10, 0),
        "id_cliente": 15,
        "id_sala": 3,
        "subtotal": Decimal("1000.00"),
        "descuento": Decimal("0.00"),
        "total": Decimal("1000.00"),
        "renglones": [
            {
                "cod_vino": 681,
                "cantidad": 2,
                "precio_unitario": Decimal("500.00"),
                "descuento": Decimal("0.00"),
                "subtotal": Decimal("1000.00"),
            }
        ],
    }


def test_crear_comprobante_exitoso(monkeypatch):
    async def crear_simulado(pool, datos):
        assert datos.id_cliente == 15
        assert datos.id_sala == 3
        return comprobante_ejemplo()

    monkeypatch.setattr(
        servicio, "crear_comprobante", crear_simulado
    )

    with crear_cliente_prueba() as client:
        respuesta = client.post(
            "/comprobantes",
            json={
                "id_cliente": 15,
                "id_sala": 3,
                "renglones": [
                    {"cod_vino": 681, "cantidad": 2}
                ],
            },
        )

    assert respuesta.status_code == 201
    assert respuesta.json()["nro_comprobante"] == 123
    assert len(respuesta.json()["renglones"]) == 1


def test_consultar_comprobante_exitoso(monkeypatch):
    async def consultar_simulado(pool, nro):
        assert nro == 123
        return comprobante_ejemplo()

    monkeypatch.setattr(
        servicio, "consultar_comprobante", consultar_simulado
    )

    with crear_cliente_prueba() as client:
        respuesta = client.get("/comprobantes/123")

    assert respuesta.status_code == 200
    assert respuesta.json()["id_cliente"] == 15


def test_comprobante_inexistente(monkeypatch):
    async def consultar_simulado(pool, nro):
        return None

    monkeypatch.setattr(
        servicio, "consultar_comprobante", consultar_simulado
    )

    with crear_cliente_prueba() as client:
        respuesta = client.get("/comprobantes/999999")

    assert respuesta.status_code == 404
    assert (
        respuesta.json()["error"]["codigo"]
        == "COMPROBANTE_NO_ENCONTRADO"
    )


def test_cantidad_invalida():
    with crear_cliente_prueba() as client:
        respuesta = client.post(
            "/comprobantes",
            json={
                "id_cliente": 15,
                "id_sala": 3,
                "renglones": [
                    {"cod_vino": 681, "cantidad": 0}
                ],
            },
        )

    assert respuesta.status_code == 422


def test_rechazar_precio_enviado_por_cliente():
    with crear_cliente_prueba() as client:
        respuesta = client.post(
            "/comprobantes",
            json={
                "id_cliente": 15,
                "id_sala": 3,
                "renglones": [
                    {
                        "cod_vino": 681,
                        "cantidad": 2,
                        "precio_unitario": 1,
                    }
                ],
            },
        )

    assert respuesta.status_code == 422


def test_vino_inexistente(monkeypatch):
    async def crear_simulado(pool, datos):
        raise servicio.VinoNoEncontradoError(
            "El vino 999999 no existe"
        )

    monkeypatch.setattr(
        servicio, "crear_comprobante", crear_simulado
    )

    with crear_cliente_prueba() as client:
        respuesta = client.post(
            "/comprobantes",
            json={
                "id_cliente": 15,
                "id_sala": 3,
                "renglones": [
                    {"cod_vino": 999999, "cantidad": 1}
                ],
            },
        )

    assert respuesta.status_code == 404
    assert (
        respuesta.json()["error"]["codigo"]
        == "VINO_NO_ENCONTRADO"
    )


def test_venta_sin_stock_aborta_transaccion(monkeypatch):
    """Simula RN-09 y verifica la salida por error de la transaccion."""

    import asyncio
    from contextlib import asynccontextmanager

    import pytest
    from psycopg.errors import RaiseException

    from app.repositories import comprobantes as repo
    from app.schemas.comprobantes import ComprobanteCrear

    eventos = []

    class ConexionFalsa:
        @asynccontextmanager
        async def transaction(self):
            try:
                yield
            except Exception:
                eventos.append("rollback_simulado")
                raise
            else:
                eventos.append("commit_simulado")

    class PoolFalso:
        @asynccontextmanager
        async def connection(self):
            yield ConexionFalsa()

    async def insertar_cabecera_falsa(conn, id_cliente, id_sala):
        eventos.append("cabecera")
        return 123

    async def insertar_renglon_falso(conn, nro, cod_vino, cantidad):
        eventos.append(f"renglon_{cod_vino}")

        if cod_vino == 999999:
            raise RaiseException(
                "RN-09: Stock insuficiente"
            )

        return True

    monkeypatch.setattr(
        repo, "insertar_cabecera", insertar_cabecera_falsa
    )
    monkeypatch.setattr(
        repo, "insertar_renglon", insertar_renglon_falso
    )

    datos = ComprobanteCrear(
        id_cliente=15,
        id_sala=3,
        renglones=[
            {"cod_vino": 681, "cantidad": 2},
            {"cod_vino": 999999, "cantidad": 1000},
        ],
    )

    with pytest.raises(RaiseException, match="RN-09"):
        asyncio.run(
            servicio.crear_comprobante(PoolFalso(), datos)
        )

    assert eventos == [
        "cabecera",
        "renglon_681",
        "renglon_999999",
        "rollback_simulado",
    ]

    assert "commit_simulado" not in eventos


def test_error_stock_responde_http_409(monkeypatch):
    """
    Comprueba que el manejador compartido transforma
    un error P0001 en HTTP 409.

    Se simula el error: no requiere PostgreSQL.
    """
    import psycopg
    from psycopg.errors import RaiseException

    from app.core.errores import manejador_sqlstate

    app = FastAPI()
    app.state.db_pool = object()

    # Reproducimos el registro del manejador de main.py
    # sin modificar ese archivo compartido.
    app.add_exception_handler(
        psycopg.Error,
        manejador_sqlstate,
    )
    app.include_router(router)

    async def crear_simulado(pool, datos):
        raise RaiseException(
            "RN-09: Stock insuficiente"
        )

    monkeypatch.setattr(
        servicio,
        "crear_comprobante",
        crear_simulado,
    )

    with TestClient(app) as client:
        respuesta = client.post(
            "/comprobantes",
            json={
                "id_cliente": 15,
                "id_sala": 3,
                "renglones": [
                    {"cod_vino": 681, "cantidad": 999999}
                ],
            },
        )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["codigo"] == "P0001"
    assert "mensaje" in respuesta.json()["error"]
