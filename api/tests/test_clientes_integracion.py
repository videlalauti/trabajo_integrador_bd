"""Pruebas de integracion HTTP con PostgreSQL real."""

import asyncio
import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_db_settings
from app.core.database import lifespan
from app.core.errores import manejador_sqlstate
from app.routers import clientes


def conexion_prueba_segura(config):
    try:
        return psycopg.connect(
            host=config.host,
            port=config.port,
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            connect_timeout=5,
        )
    except psycopg.Error:
        raise RuntimeError(
            "No se pudo conectar a la base de pruebas de Fabricio."
        ) from None


@pytest.fixture(scope="module")
def cliente_api_real():
    config = get_db_settings()

    assert config.dbname == "bodegas_fase6_fabricio_test", (
        "PROTECCION: base de pruebas incorrecta."
    )
    assert config.user == "bodega_api", (
        "PROTECCION: debe usarse bodega_api."
    )

    # Verificar la identidad REAL de la conexion antes de escribir.
    with conexion_prueba_segura(config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user")
            base_real, usuario_real = cur.fetchone()

    assert base_real == "bodegas_fase6_fabricio_test", (
        f"PROTECCION: base real incorrecta: {base_real}"
    )
    assert usuario_real == "bodega_api", (
        f"PROTECCION: usuario real incorrecto: {usuario_real}"
    )

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(psycopg.Error, manejador_sqlstate)
    app.include_router(clientes.router)

    with TestClient(app, backend_options={"loop_factory": asyncio.SelectorEventLoop}) as cliente:
        yield cliente


def test_listar_y_consultar_clientes_reales(cliente_api_real):
    respuesta = cliente_api_real.get(
        "/clientes?page=1&page_size=2&tipo_cliente=socio"
    )

    assert respuesta.status_code == 200, respuesta.text

    datos = respuesta.json()

    assert datos["total"] > 0
    assert datos["pagina"] == 1
    assert datos["tamanio"] == 2
    assert len(datos["items"]) == 2

    id_cliente = datos["items"][0]["id_cliente"]

    detalle = cliente_api_real.get(f"/clientes/{id_cliente}")

    assert detalle.status_code == 200, detalle.text
    assert detalle.json()["id_cliente"] == id_cliente
    assert detalle.json()["tipo_cliente"] == "socio"


def test_cliente_inexistente_real(cliente_api_real):
    respuesta = cliente_api_real.get("/clientes/999999999")

    assert respuesta.status_code == 404



def test_crud_completo_cliente_real(cliente_api_real):
    """Crea, consulta, actualiza y elimina un cliente real."""

    from uuid import uuid4

    # Obtener datos validos de referencia.
    referencia = cliente_api_real.get(
        "/clientes?page_size=1&tipo_cliente=socio"
    )

    assert referencia.status_code == 200, referencia.text

    ejemplo = referencia.json()["items"][0]

    datos = {
        clave: valor
        for clave, valor in ejemplo.items()
        if clave != "id_cliente"
    }

    identificador = uuid4().hex[:16]

    datos["nombre_razon_social"] = (
        "Cliente Prueba Fase 6 " + identificador
    )
    datos["nro_doc"] = "F6" + identificador

    id_creado = None

    try:
        # 1. Crear cliente.
        creado = cliente_api_real.post(
            "/clientes",
            json=datos,
        )

        assert creado.status_code == 201, creado.text

        id_creado = creado.json()["id_cliente"]

        # 2. Consultar cliente.
        consulta = cliente_api_real.get(
            f"/clientes/{id_creado}"
        )

        assert consulta.status_code == 200, consulta.text
        assert consulta.json()["nro_doc"] == datos["nro_doc"]

        # 3. Actualizar cliente.
        datos["nombre_razon_social"] = (
            "Cliente Actualizado Fase 6"
        )

        actualizado = cliente_api_real.put(
            f"/clientes/{id_creado}",
            json=datos,
        )

        assert actualizado.status_code == 200, actualizado.text

        assert actualizado.json()["nombre_razon_social"] == (
            "Cliente Actualizado Fase 6"
        )

        # 4. Eliminar cliente.
        eliminado = cliente_api_real.delete(
            f"/clientes/{id_creado}"
        )

        assert eliminado.status_code == 204, eliminado.text

        # 5. Comprobar que ya no existe.
        consulta_final = cliente_api_real.get(
            f"/clientes/{id_creado}"
        )

        assert consulta_final.status_code == 404

        id_creado = None

    finally:
        # Limpieza de seguridad si alguna etapa falla.
        if id_creado is not None:
            cliente_api_real.delete(f"/clientes/{id_creado}")


def test_rechazar_eliminacion_cliente_con_ventas(cliente_api_real):
    """PostgreSQL impide eliminar un cliente con comprobantes."""

    from app.core.config import get_db_settings

    config = get_db_settings()

    assert config.dbname == "bodegas_fase6_fabricio_test"
    assert config.user == "bodega_api"

    # Buscar un cliente que tenga comprobantes asociados.
    with conexion_prueba_segura(config) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id_cliente
                FROM public.cliente c
                WHERE EXISTS (
                    SELECT 1
                    FROM public.comprobante co
                    WHERE co.id_cliente = c.id_cliente
                )
                ORDER BY c.id_cliente
                LIMIT 1
            """)
            fila = cur.fetchone()

    assert fila is not None, (
        "No se encontraron clientes con comprobantes."
    )

    id_cliente = fila[0]

    # Intentar eliminarlo mediante el endpoint REST.
    respuesta = cliente_api_real.delete(
        f"/clientes/{id_cliente}"
    )

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["error"]["codigo"] == "23503"

    # Verificar que PostgreSQL conserva el cliente.
    consulta = cliente_api_real.get(
        f"/clientes/{id_cliente}"
    )

    assert consulta.status_code == 200, consulta.text

