"""Consultas SQL parametrizadas para clientes."""

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.schemas.clientes import ClienteEntrada


COLUMNAS = """
    id_cliente, nombre_razon_social, tipo_doc, nro_doc,
    direccion, fecha_alta, id_localidad, tipo_cliente,
    descuento_especial, zona_cobertura, nro_habilitacion,
    pais_destino
"""


async def listar_clientes(
    conn: AsyncConnection,
    page: int,
    page_size: int,
    tipo_cliente: str | None = None,
):
    """Lista clientes paginados y opcionalmente filtrados por tipo."""

    offset = (page - 1) * page_size

    filtro = """
        WHERE (%s::text IS NULL OR tipo_cliente = %s)
    """

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT COUNT(*) AS total FROM cliente " + filtro,
            (tipo_cliente, tipo_cliente),
        )
        total = (await cur.fetchone())["total"]

        await cur.execute(
            f"""
            SELECT {COLUMNAS}
            FROM cliente
            {filtro}
            ORDER BY id_cliente
            LIMIT %s OFFSET %s
            """,
            (tipo_cliente, tipo_cliente, page_size, offset),
        )
        items = await cur.fetchall()

    return items, total


async def obtener_cliente(conn: AsyncConnection, id_cliente: int):
    """Busca un cliente por su identificador."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""
            SELECT {COLUMNAS}
            FROM cliente
            WHERE id_cliente = %s
            """,
            (id_cliente,),
        )
        return await cur.fetchone()


async def crear_cliente(conn: AsyncConnection, datos: ClienteEntrada):
    """Inserta un cliente y devuelve el registro generado."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""
            INSERT INTO cliente (
                nombre_razon_social, tipo_doc, nro_doc,
                direccion, fecha_alta, id_localidad,
                tipo_cliente, descuento_especial,
                zona_cobertura, nro_habilitacion, pais_destino
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING {COLUMNAS}
            """,
            (
                datos.nombre_razon_social,
                datos.tipo_doc,
                datos.nro_doc,
                datos.direccion,
                datos.fecha_alta,
                datos.id_localidad,
                datos.tipo_cliente,
                datos.descuento_especial,
                datos.zona_cobertura,
                datos.nro_habilitacion,
                datos.pais_destino,
            ),
        )
        return await cur.fetchone()


async def actualizar_cliente(
    conn: AsyncConnection,
    id_cliente: int,
    datos: ClienteEntrada,
):
    """Actualiza todos los campos editables de un cliente."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"""
            UPDATE cliente
            SET nombre_razon_social = %s,
                tipo_doc = %s,
                nro_doc = %s,
                direccion = %s,
                fecha_alta = %s,
                id_localidad = %s,
                tipo_cliente = %s,
                descuento_especial = %s,
                zona_cobertura = %s,
                nro_habilitacion = %s,
                pais_destino = %s
            WHERE id_cliente = %s
            RETURNING {COLUMNAS}
            """,
            (
                datos.nombre_razon_social,
                datos.tipo_doc,
                datos.nro_doc,
                datos.direccion,
                datos.fecha_alta,
                datos.id_localidad,
                datos.tipo_cliente,
                datos.descuento_especial,
                datos.zona_cobertura,
                datos.nro_habilitacion,
                datos.pais_destino,
                id_cliente,
            ),
        )
        return await cur.fetchone()


async def eliminar_cliente(conn: AsyncConnection, id_cliente: int):
    """Elimina un cliente si las restricciones de PostgreSQL lo permiten."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            DELETE FROM cliente
            WHERE id_cliente = %s
            RETURNING id_cliente
            """,
            (id_cliente,),
        )
        return await cur.fetchone()
