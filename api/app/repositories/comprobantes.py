
"""Consultas SQL parametrizadas para comprobantes."""

from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def insertar_cabecera(
    conn: AsyncConnection,
    id_cliente: int,
    id_sala: int,
) -> int:
    """Inserta la cabecera y devuelve el número generado."""

    sql = """
        INSERT INTO public.comprobante (
            fecha,
            id_cliente,
            id_sala,
            subtotal,
            descuento,
            total
        )
        VALUES (CURRENT_TIMESTAMP, %s, %s, 0, 0, 0)
        RETURNING nro_comprobante;
    """

    async with conn.cursor() as cur:
        await cur.execute(sql, (id_cliente, id_sala))
        fila = await cur.fetchone()

    return fila[0]


async def insertar_renglon(
    conn: AsyncConnection,
    nro_comprobante: int,
    cod_vino: int,
    cantidad: int,
) -> bool:
    """
    Inserta un renglón usando el precio real de vino.

    PostgreSQL calcula descuentos y subtotales, además
    de validar y descontar stock mediante triggers.

    Devuelve False si el vino no existe.
    """

    sql = """
        INSERT INTO public.renglon_comprobante (
            nro_comprobante,
            cod_vino,
            cantidad,
            precio_unitario,
            descuento,
            subtotal
        )
        SELECT
            %s,
            v.cod_vino,
            %s,
            v.precio,
            0,
            0
        FROM public.vino AS v
        WHERE v.cod_vino = %s
        RETURNING cod_vino;
    """

    async with conn.cursor() as cur:
        await cur.execute(
            sql,
            (nro_comprobante, cantidad, cod_vino),
        )
        fila = await cur.fetchone()

    return fila is not None


async def obtener_cabecera(
    conn: AsyncConnection,
    nro_comprobante: int,
) -> dict[str, Any] | None:
    """Obtiene la cabecera con los importes calculados por BD."""

    sql = """
        SELECT
            nro_comprobante,
            fecha,
            id_cliente,
            id_sala,
            subtotal,
            descuento,
            total
        FROM public.comprobante
        WHERE nro_comprobante = %s;
    """

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, (nro_comprobante,))
        fila = await cur.fetchone()

    return fila


async def obtener_renglones(
    conn: AsyncConnection,
    nro_comprobante: int,
) -> list[dict[str, Any]]:
    """Obtiene todos los renglones del comprobante."""

    sql = """
        SELECT
            cod_vino,
            cantidad,
            precio_unitario,
            descuento,
            subtotal
        FROM public.renglon_comprobante
        WHERE nro_comprobante = %s
        ORDER BY cod_vino;
    """

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(sql, (nro_comprobante,))
        filas = await cur.fetchall()

    return filas
