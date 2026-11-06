
"""Consultas SQL para el catálogo de salas de venta."""

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def listar_salas(conn: AsyncConnection) -> list[dict]:
    """Obtiene las salas de venta con su localidad."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                s.id_sala,
                s.calle,
                s.numero,
                l.nombre AS localidad
            FROM sala_venta AS s
            JOIN localidad AS l
                ON l.id_localidad = s.id_localidad
            ORDER BY s.id_sala
            """
        )

        return await cur.fetchall()
