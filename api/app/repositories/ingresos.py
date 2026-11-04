"""Repositorio de ingresos: una funcion por sentencia SQL parametrizada.

Reciben una conexion abierta; la transaccion la maneja services/ingresos.py.
Ninguna funcion modifica estado ni stock con UPDATE: eso solo lo hacen los
procedimientos sp_terminar_ingreso y sp_procesar_ingreso (permisos de 007).
"""
from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def insertar_ingreso(conn: AsyncConnection, cod_transporte: int, cuit_bodega: str, fecha) -> int:
    # estado: DEFAULT 'en_confeccion' (RN-10). fecha: CURRENT_DATE si no se informa.
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO ingreso (fecha, cod_transporte, cuit_bodega)
            VALUES (COALESCE(%s::date, CURRENT_DATE), %s, %s)
            RETURNING cod_ingreso
            """,
            (fecha, cod_transporte, cuit_bodega),
        )
        return (await cur.fetchone())[0]


async def existe_ingreso(conn: AsyncConnection, cod_ingreso: int) -> bool:
    async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM ingreso WHERE cod_ingreso = %s", (cod_ingreso,))
        return await cur.fetchone() is not None


async def insertar_renglon(conn: AsyncConnection, cod_ingreso: int, cod_vino: int, cantidad: int) -> None:
    # trg_renglon_ingreso_estado (RN-12) rechaza si el ingreso no esta en confeccion.
    async with conn.cursor() as cur:
        await cur.execute(
            "INSERT INTO renglon_ingreso (cod_ingreso, cod_vino, cantidad) VALUES (%s, %s, %s)",
            (cod_ingreso, cod_vino, cantidad),
        )


async def terminar_ingreso(conn: AsyncConnection, cod_ingreso: int) -> None:
    async with conn.cursor() as cur:
        await cur.execute("CALL sp_terminar_ingreso(%s)", (cod_ingreso,))


async def procesar_ingreso(conn: AsyncConnection, cod_ingreso: int) -> None:
    async with conn.cursor() as cur:
        await cur.execute("CALL sp_procesar_ingreso(%s)", (cod_ingreso,))


async def obtener_cabecera(conn: AsyncConnection, cod_ingreso: int) -> dict | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT i.cod_ingreso,
                   i.fecha,
                   i.estado::text      AS estado,
                   i.cod_transporte,
                   t.razon_social      AS transportista,
                   i.cuit_bodega::text AS cuit_bodega,
                   b.razon_social      AS bodega
            FROM ingreso       AS i
            JOIN transportista AS t ON t.cod_transporte = i.cod_transporte
            JOIN bodega        AS b ON b.cuit = i.cuit_bodega
            WHERE i.cod_ingreso = %s
            """,
            (cod_ingreso,),
        )
        return await cur.fetchone()


async def obtener_renglones(conn: AsyncConnection, cod_ingreso: int) -> list[dict]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT r.cod_vino,
                   v.nombre                 AS vino,
                   v.volumen_ml,
                   r.cantidad,
                   COALESCE(sd.cantidad, 0) AS stock_deposito
            FROM renglon_ingreso     AS r
            JOIN vino                AS v  ON v.cod_vino = r.cod_vino
            LEFT JOIN stock_deposito AS sd ON sd.cod_vino = r.cod_vino
            WHERE r.cod_ingreso = %s
            ORDER BY r.cod_vino
            """,
            (cod_ingreso,),
        )
        return await cur.fetchall()
