"""Repositorio de transferencias: una funcion por sentencia SQL parametrizada.

Reciben una conexion abierta; la transaccion la maneja
services/transferencias.py. Estados y stock solo cambian mediante
sp_terminar_transferencia y sp_procesar_transferencia (permisos de 007).
"""
from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def insertar_transferencia(conn: AsyncConnection, id_sala: int) -> int:
    # fecha_confeccion: la fuerza trg_transferencia_fecha (RN-11).
    # estado: DEFAULT 'en_confeccion'.
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO transferencia (id_sala) VALUES (%s) RETURNING nro_solicitud",
            (id_sala,),
        )
        return (await cur.fetchone())[0]


async def existe_transferencia(conn: AsyncConnection, nro_solicitud: int) -> bool:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM transferencia WHERE nro_solicitud = %s", (nro_solicitud,))
        return await cur.fetchone() is not None


async def insertar_renglon(conn: AsyncConnection, nro_solicitud: int, cod_vino: int, cantidad: int) -> None:
    # trg_renglon_transferencia_estado (RN-12) rechaza si no esta en confeccion.
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO renglon_transferencia (nro_solicitud, cod_vino, cantidad) VALUES (%s, %s, %s)",
            (nro_solicitud, cod_vino, cantidad),
        )


async def terminar_transferencia(conn: AsyncConnection, nro_solicitud: int) -> None:
    async with conn.cursor() as cur:
        await cur.execute("CALL sp_terminar_transferencia(%s)", (nro_solicitud,))


async def procesar_transferencia(conn: AsyncConnection, nro_solicitud: int) -> None:
    # Descuenta del deposito y suma a la sala; rechaza si no hay stock (RN-11).
    async with conn.cursor() as cur:
        await cur.execute("CALL sp_procesar_transferencia(%s)", (nro_solicitud,))


async def obtener_cabecera(conn: AsyncConnection, nro_solicitud: int) -> dict | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT t.nro_solicitud,
                   t.fecha_confeccion,
                   t.estado::text            AS estado,
                   t.id_sala,
                   s.calle || ' ' || s.numero AS sala,
                   l.nombre                  AS localidad
            FROM transferencia AS t
            JOIN sala_venta    AS s ON s.id_sala = t.id_sala
            JOIN localidad     AS l ON l.id_localidad = s.id_localidad
            WHERE t.nro_solicitud = %s
            """,
            (nro_solicitud,),
        )
        return await cur.fetchone()


async def obtener_renglones(conn: AsyncConnection, nro_solicitud: int) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT r.cod_vino,
                   v.nombre                 AS vino,
                   v.volumen_ml,
                   r.cantidad,
                   COALESCE(sd.cantidad, 0) AS stock_deposito,
                   COALESCE(ss.cantidad, 0) AS stock_sala
            FROM renglon_transferencia AS r
            JOIN transferencia         AS t  ON t.nro_solicitud = r.nro_solicitud
            JOIN vino                  AS v  ON v.cod_vino = r.cod_vino
            LEFT JOIN stock_deposito   AS sd ON sd.cod_vino = r.cod_vino
            LEFT JOIN stock_sala       AS ss ON ss.id_sala = t.id_sala
                                            AND ss.cod_vino = r.cod_vino
            WHERE r.nro_solicitud = %s
            ORDER BY r.cod_vino
            """,
            (nro_solicitud,),
        )
        return await cur.fetchall()
