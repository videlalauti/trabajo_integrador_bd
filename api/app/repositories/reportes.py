"""Consultas SQL de los reportes de Bodegas del Atuel."""

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def top_vinos(conn: AsyncConnection):
    """S1: diez vinos con mas botellas vendidas."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                v.cod_vino,
                v.nombre AS vino,
                v.tipo,
                SUM(rc.cantidad) AS botellas_vendidas
            FROM public.renglon_comprobante rc
            JOIN public.comprobante c
                ON c.nro_comprobante = rc.nro_comprobante
            JOIN public.sala_venta s
                ON s.id_sala = c.id_sala
            JOIN public.vino v
                ON v.cod_vino = rc.cod_vino
            GROUP BY v.cod_vino, v.nombre, v.tipo
            ORDER BY botellas_vendidas DESC, v.cod_vino ASC
            LIMIT 10
            """
        )
        return await cur.fetchall()


async def ventas_por_sala(conn: AsyncConnection):
    """S8: ventas por sala durante los ultimos tres meses."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                s.id_sala,
                s.calle,
                s.numero,
                COALESCE(SUM(c.total), 0) AS total_ventas
            FROM public.sala_venta s
            LEFT JOIN public.comprobante c
                ON c.id_sala = s.id_sala
               AND c.fecha >= CURRENT_DATE - INTERVAL '3 months'
               AND c.fecha < CURRENT_DATE + INTERVAL '1 day'
            GROUP BY s.id_sala, s.calle, s.numero
            ORDER BY total_ventas DESC, s.id_sala
            """
        )
        return await cur.fetchall()


async def existe_sala(conn: AsyncConnection, id_sala: int):
    """Comprueba si existe la sala solicitada."""

    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT 1 FROM public.sala_venta WHERE id_sala = %s",
            (id_sala,),
        )
        return await cur.fetchone() is not None


async def vinos_sin_stock(
    conn: AsyncConnection,
    id_sala: int,
    page: int,
    page_size: int,
):
    """S6: sin stock en una sala, pero con stock en deposito."""

    offset = (page - 1) * page_size

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM public.vino v
            JOIN public.stock_deposito sd
                ON sd.cod_vino = v.cod_vino
               AND sd.cantidad > 0
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.stock_sala ss
                WHERE ss.id_sala = %s
                  AND ss.cod_vino = v.cod_vino
                  AND ss.cantidad > 0
            )
            """,
            (id_sala,),
        )
        total = (await cur.fetchone())["total"]

        await cur.execute(
            """
            SELECT
                v.cod_vino,
                v.nombre AS vino,
                v.tipo,
                v.anada,
                v.volumen_ml,
                public.fn_stock_sala(%s, v.cod_vino) AS stock_sala,
                sd.cantidad AS stock_deposito
            FROM public.vino v
            JOIN public.stock_deposito sd
                ON sd.cod_vino = v.cod_vino
               AND sd.cantidad > 0
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.stock_sala ss
                WHERE ss.id_sala = %s
                  AND ss.cod_vino = v.cod_vino
                  AND ss.cantidad > 0
            )
            ORDER BY sd.cantidad DESC, v.cod_vino
            LIMIT %s OFFSET %s
            """,
            (id_sala, id_sala, page_size, offset),
        )
        items = await cur.fetchall()

    return {
        "items": items,
        "total": total,
        "pagina": page,
        "tamanio": page_size,
    }


async def transportista_activo(conn: AsyncConnection):
    """S7: transportista con mas ingresos en el ultimo mes."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                t.cod_transporte,
                t.razon_social,
                COUNT(i.cod_ingreso) AS cantidad_ingresos
            FROM public.transportista t
            JOIN public.ingreso i
                ON i.cod_transporte = t.cod_transporte
            WHERE i.fecha >= CURRENT_DATE - INTERVAL '1 month'
              AND i.fecha <= CURRENT_DATE
            GROUP BY t.cod_transporte, t.razon_social
            ORDER BY cantidad_ingresos DESC, t.cod_transporte ASC
            LIMIT 1
            """
        )
        return await cur.fetchone()


async def trazabilidad(
    conn: AsyncConnection,
    cod_vino: int,
    page: int,
    page_size: int,
):
    """
    Muestra el vino, su bodega y lotes registrados por ella.

    Importante: NO existe una relacion directa vino-lote_uva
    en el esquema. Los lotes no representan necesariamente
    los utilizados para elaborar el vino consultado.
    """

    offset = (page - 1) * page_size

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                v.cod_vino,
                v.nombre AS nombre_vino,
                v.tipo,
                v.anada,
                v.cuit_bodega,
                b.razon_social AS nombre_bodega
            FROM public.vino v
            JOIN public.bodega b
                ON b.cuit = v.cuit_bodega
            WHERE v.cod_vino = %s
            """,
            (cod_vino,),
        )

        vino = await cur.fetchone()

        if vino is None:
            return None

        await cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM public.lote_uva
            WHERE cuit_bodega = %s
            """,
            (vino["cuit_bodega"],),
        )
        total_lotes = (await cur.fetchone())["total"]

        await cur.execute(
            """
            SELECT
                l.nro_lote,
                l.campania,
                l.fecha_cosecha,
                l.kg_cosechados,
                l.id_finca,
                f.nombre AS nombre_finca,
                l.nro_parcela,
                p.superficie_ha AS superficie_parcela_ha
            FROM public.lote_uva l
            JOIN public.parcela p
                ON p.id_finca = l.id_finca
               AND p.nro_parcela = l.nro_parcela
            JOIN public.finca f
                ON f.id_finca = l.id_finca
            WHERE l.cuit_bodega = %s
            ORDER BY l.nro_lote
            LIMIT %s OFFSET %s
            """,
            (vino["cuit_bodega"], page_size, offset),
        )
        lotes = await cur.fetchall()

    return {
        "vino": vino,
        "lotes_registrados_en_bodega": lotes,
        "total_lotes_bodega": total_lotes,
        "pagina": page,
        "tamanio": page_size,
        "relacion_directa_vino_lote": False,
        "aclaracion": (
            "Los lotes pertenecen a la misma bodega que el vino. "
            "El modelo no permite determinar cuales fueron "
            "utilizados para elaborar este vino."
        ),
    }
