
"""Pruebas reales de comprobantes contra PostgreSQL descartable.

Se ejecutan solamente con JOSE_FASE6_RUN_INTEGRATION=1.
La venta valida queda registrada en la base de pruebas.
"""

import asyncio
import os
import selectors
import sys
from decimal import Decimal

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg_pool import PoolTimeout

from app.core.database import lifespan
from app.core.errores import manejador_sqlstate
from app.routers.comprobantes import router


def conexion_prueba():
    return psycopg.connect(
        host="127.0.0.1",
        port=5435,
        dbname="bodegas_fase6_jose_test",
        user="bodega_api",
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def consultar(sql, parametros=()):
    with conexion_prueba() as conn:
        return conn.execute(sql, parametros).fetchone()


def stock(sala, vino):
    fila = consultar(
        """
        SELECT cantidad
        FROM public.stock_sala
        WHERE id_sala = %s AND cod_vino = %s
        """,
        (sala, vino),
    )
    return fila[0] if fila else 0


def conteos():
    return consultar(
        """
        SELECT
            (SELECT COUNT(*) FROM public.comprobante),
            (SELECT COUNT(*) FROM public.renglon_comprobante)
        """
    )


@pytest.fixture(scope="module")
def cliente_http():
    if os.getenv("JOSE_FASE6_RUN_INTEGRATION") != "1":
        pytest.skip("Pruebas reales no habilitadas")

    # Bloqueo de seguridad antes de cualquier escritura.
    esperado = {
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "5435",
        "DB_NAME": "bodegas_fase6_jose_test",
        "DB_USER": "bodega_api",
    }

    for variable, valor in esperado.items():
        assert os.getenv(variable) == valor, (
            f"Conexion de prueba insegura: {variable}"
        )

    assert os.getenv("DB_PASSWORD"), "Falta DB_PASSWORD"

    identidad = consultar(
        "SELECT current_user, current_database()"
    )
    assert identidad == (
        "bodega_api",
        "bodegas_fase6_jose_test",
    )

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(
        psycopg.Error, manejador_sqlstate
    )
    app.add_exception_handler(
        PoolTimeout, manejador_sqlstate
    )
    app.include_router(router)

    # SelectorEventLoop para psycopg async en Windows.
    opciones = {}
    if sys.platform == "win32":
        opciones["loop_factory"] = lambda: (
            asyncio.SelectorEventLoop(
                selectors.SelectSelector()
            )
        )

    with TestClient(
        app,
        backend_options=opciones,
    ) as cliente:
        yield cliente


def test_01_consultar_comprobante_real(cliente_http):
    respuesta = cliente_http.get("/comprobantes/1")

    assert respuesta.status_code == 200
    assert respuesta.json()["nro_comprobante"] == 1
    assert len(respuesta.json()["renglones"]) > 0


def test_02_venta_real_descuenta_stock_y_calcula_importes(
    cliente_http,
):
    sala = 19
    vino = 17
    cliente = 1
    cantidad = 2

    antes = stock(sala, vino)
    assert antes >= cantidad

    respuesta = cliente_http.post(
        "/comprobantes",
        json={
            "id_cliente": cliente,
            "id_sala": sala,
            "renglones": [
                {"cod_vino": vino, "cantidad": cantidad}
            ],
        },
    )

    assert respuesta.status_code == 201, respuesta.text
    datos = respuesta.json()
    nro = datos["nro_comprobante"]

    # Verificar stock realmente descontado.
    despues = stock(sala, vino)
    assert despues == antes - cantidad

    # Contrastar la respuesta con lo persistido en PostgreSQL.
    cabecera = consultar(
        """
        SELECT subtotal, descuento, total
        FROM public.comprobante
        WHERE nro_comprobante = %s
        """,
        (nro,),
    )
    assert cabecera is not None

    renglon = consultar(
        """
        SELECT cantidad, precio_unitario, descuento, subtotal
        FROM public.renglon_comprobante
        WHERE nro_comprobante = %s AND cod_vino = %s
        """,
        (nro, vino),
    )
    assert renglon is not None
    assert renglon[0] == cantidad

    # El precio y el descuento provienen de la BD.
    precio = consultar(
        "SELECT precio FROM public.vino WHERE cod_vino = %s",
        (vino,),
    )[0]

    descuento = consultar(
        "SELECT public.fn_descuento_cliente(%s)",
        (cliente,),
    )[0]

    assert renglon[1] == precio
    assert renglon[2] == descuento

    # El valor esperado lo calcula PostgreSQL.
    subtotal_esperado = consultar(
        """
        SELECT ROUND(
            %s::numeric * precio *
            (1 - public.fn_descuento_cliente(%s) / 100.0),
            2
        )
        FROM public.vino
        WHERE cod_vino = %s
        """,
        (cantidad, cliente, vino),
    )[0]

    assert renglon[3] == subtotal_esperado
    assert cabecera[2] > 0

    assert Decimal(str(datos["subtotal"])) == cabecera[0]
    assert Decimal(str(datos["descuento"])) == cabecera[1]
    assert Decimal(str(datos["total"])) == cabecera[2]

    assert len(datos["renglones"]) == 1
    assert (
        Decimal(str(datos["renglones"][0]["subtotal"]))
        == renglon[3]
    )

    print(
        f"\nVENTA REAL OK: comprobante={nro}, "
        f"stock={antes}->{despues}, total={cabecera[2]}"
    )


def test_03_sin_stock_http409_y_rollback_completo(
    cliente_http,
):
    sala = 19
    vino_valido = 17

    # Elegir otro vino con stock escaso o inexistente.
    # Así el fallo ocurre por RN-09, no por importes enormes.
    vino_fallido = consultar(
        """
        SELECT v.cod_vino, COALESCE(s.cantidad, 0)
        FROM public.vino AS v
        LEFT JOIN public.stock_sala AS s
          ON s.id_sala = %s AND s.cod_vino = v.cod_vino
        WHERE v.cod_vino <> %s
          AND COALESCE(s.cantidad, 0) BETWEEN 0 AND 10
        ORDER BY COALESCE(s.cantidad, 0), v.cod_vino
        LIMIT 1
        """,
        (sala, vino_valido),
    )

    assert vino_fallido is not None, (
        "No se encontro un vino adecuado para provocar RN-09"
    )

    cod_fallido, disponible = vino_fallido
    cantidad_fallida = disponible + 1

    comprobantes_antes, renglones_antes = conteos()
    stock_valido_antes = stock(sala, vino_valido)
    stock_fallido_antes = stock(sala, cod_fallido)

    assert stock_valido_antes >= 1

    # Primer renglon valido; segundo rechazado por stock.
    respuesta = cliente_http.post(
        "/comprobantes",
        json={
            "id_cliente": 1,
            "id_sala": sala,
            "renglones": [
                {"cod_vino": vino_valido, "cantidad": 1},
                {
                    "cod_vino": cod_fallido,
                    "cantidad": cantidad_fallida,
                },
            ],
        },
    )

    assert respuesta.status_code == 409, respuesta.text

    error = respuesta.json()["error"]
    assert error["codigo"] == "P0001"
    assert "RN-09" in error["mensaje"]

    # Verificar rollback REAL, no simulado.
    comprobantes_despues, renglones_despues = conteos()

    assert comprobantes_despues == comprobantes_antes
    assert renglones_despues == renglones_antes
    assert stock(sala, vino_valido) == stock_valido_antes
    assert stock(sala, cod_fallido) == stock_fallido_antes

    print(
        "\nROLLBACK REAL OK: HTTP 409, "
        "sin nuevas cabeceras ni renglones, "
        "stock intacto"
    )
