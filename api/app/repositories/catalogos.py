
"""Consultas SQL para los catálogos auxiliares del frontend."""

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def listar_bodegas(conn: AsyncConnection) -> list[dict]:
    """Obtiene las bodegas disponibles."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                cuit::text AS cuit,
                razon_social
            FROM bodega
            ORDER BY razon_social, cuit
            """
        )

        return await cur.fetchall()


async def listar_cepas(conn: AsyncConnection) -> list[dict]:
    """Obtiene las cepas disponibles."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                id_cepa,
                nombre,
                tipo::text AS tipo
            FROM cepa
            ORDER BY nombre, id_cepa
            """
        )

        return await cur.fetchall()


async def listar_maridajes(conn: AsyncConnection) -> list[dict]:
    """Obtiene los maridajes disponibles."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                id_maridaje,
                nombre,
                temperatura_servicio_c
            FROM maridaje
            ORDER BY nombre, id_maridaje
            """
        )

        return await cur.fetchall()
