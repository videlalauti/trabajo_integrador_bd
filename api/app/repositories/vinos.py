
"""Consultas SQL del módulo de vinos."""

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def listar_vinos(
    conn: AsyncConnection,
    pagina: int = 1,
    tamanio: int = 20,
    tipo: str | None = None,
    cepa: int | None = None,
    bodega: str | None = None,
    anada: int | None = None,
) -> dict:
    """Lista vinos con filtros opcionales y paginación."""

    condiciones = []
    parametros = []

    if tipo is not None:
        condiciones.append("v.tipo = %s")
        parametros.append(tipo)

    if cepa is not None:
        condiciones.append(
            "EXISTS (SELECT 1 FROM vino_cepa vc "
            "WHERE vc.cod_vino = v.cod_vino AND vc.id_cepa = %s)"
        )
        parametros.append(cepa)

    if bodega is not None:
        condiciones.append("v.cuit_bodega = %s")
        parametros.append(bodega)

    if anada is not None:
        condiciones.append("v.anada = %s")
        parametros.append(anada)

    where_sql = (
        "WHERE " + " AND ".join(condiciones)
        if condiciones
        else ""
    )

    consulta_total = f"""
        SELECT COUNT(*)
        FROM vino v
        {where_sql}
    """

    consulta_vinos = f"""
        SELECT
            v.cod_vino,
            v.nombre,
            v.tipo,
            v.anada,
            v.volumen_ml,
            v.graduacion,
            v.precio,
            v.cuit_bodega
        FROM vino v
        {where_sql}
        ORDER BY v.cod_vino
        LIMIT %s OFFSET %s
    """

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(consulta_total, parametros)
        fila_total = await cur.fetchone()
        total = fila_total["count"]

        offset = (pagina - 1) * tamanio

        await cur.execute(
            consulta_vinos,
            [*parametros, tamanio, offset],
        )
        vinos = await cur.fetchall()

    return {
        "items": vinos,
        "total": total,
        "pagina": pagina,
        "tamanio": tamanio,
    }


async def obtener_vino_por_codigo(
    conn: AsyncConnection,
    cod_vino: int,
) -> dict | None:
    """Obtiene un vino con sus cepas y maridajes."""

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                cod_vino, nombre, tipo, anada,
                volumen_ml, graduacion, precio, cuit_bodega
            FROM vino
            WHERE cod_vino = %s
            """,
            (cod_vino,),
        )
        vino = await cur.fetchone()

        if vino is None:
            return None

        await cur.execute(
            """
            SELECT
                vc.id_cepa,
                c.nombre,
                vc.porcentaje
            FROM vino_cepa vc
            JOIN cepa c ON c.id_cepa = vc.id_cepa
            WHERE vc.cod_vino = %s
            ORDER BY vc.id_cepa
            """,
            (cod_vino,),
        )
        vino["cepas"] = await cur.fetchall()

        await cur.execute(
            """
            SELECT
                vm.id_maridaje,
                m.nombre,
                m.temperatura_servicio_c
            FROM vino_maridaje vm
            JOIN maridaje m
                ON m.id_maridaje = vm.id_maridaje
            WHERE vm.cod_vino = %s
            ORDER BY vm.id_maridaje
            """,
            (cod_vino,),
        )
        vino["maridajes"] = await cur.fetchall()

    return vino


async def insertar_vino(
    conn: AsyncConnection,
    datos: dict,
) -> int:
    """Inserta un vino y devuelve su código generado."""

    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO vino (
                nombre,
                tipo,
                anada,
                volumen_ml,
                graduacion,
                precio,
                cuit_bodega
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING cod_vino
            """,
            (
                datos["nombre"],
                datos["tipo"],
                datos["anada"],
                datos["volumen_ml"],
                datos["graduacion"],
                datos["precio"],
                datos["cuit_bodega"],
            ),
        )

        fila = await cur.fetchone()
        return fila[0]


async def insertar_cepas_vino(
    conn: AsyncConnection,
    cod_vino: int,
    cepas: list[dict],
) -> None:
    """Inserta las cepas y sus porcentajes para un vino."""

    async with conn.cursor() as cur:
        for cepa in cepas:
            await cur.execute(
                """
                INSERT INTO vino_cepa (
                    cod_vino,
                    id_cepa,
                    porcentaje
                )
                VALUES (%s, %s, %s)
                """,
                (
                    cod_vino,
                    cepa["id_cepa"],
                    cepa["porcentaje"],
                ),
            )


async def insertar_maridajes_vino(
    conn: AsyncConnection,
    cod_vino: int,
    maridajes: list[int],
) -> None:
    """Inserta los maridajes asociados a un vino."""

    async with conn.cursor() as cur:
        for id_maridaje in maridajes:
            await cur.execute(
                """
                INSERT INTO vino_maridaje (
                    cod_vino,
                    id_maridaje
                )
                VALUES (%s, %s)
                """,
                (
                    cod_vino,
                    id_maridaje,
                ),
            )


async def actualizar_datos_vino(
    conn: AsyncConnection,
    cod_vino: int,
    datos: dict,
) -> bool:
    """Actualiza los datos principales de un vino."""

    async with conn.cursor() as cur:
        await cur.execute(
            """
            UPDATE vino
            SET
                nombre = %s,
                tipo = %s,
                anada = %s,
                volumen_ml = %s,
                graduacion = %s,
                precio = %s,
                cuit_bodega = %s
            WHERE cod_vino = %s
            RETURNING cod_vino
            """,
            (
                datos["nombre"],
                datos["tipo"],
                datos["anada"],
                datos["volumen_ml"],
                datos["graduacion"],
                datos["precio"],
                datos["cuit_bodega"],
                cod_vino,
            ),
        )

        fila = await cur.fetchone()
        return fila is not None


async def reemplazar_cepas_vino(
    conn: AsyncConnection,
    cod_vino: int,
    cepas: list[dict],
) -> None:
    """Reemplaza la composición de cepas de un vino."""

    async with conn.cursor() as cur:
        await cur.execute(
            """
            DELETE FROM vino_cepa
            WHERE cod_vino = %s
            """,
            (cod_vino,),
        )

    await insertar_cepas_vino(
        conn=conn,
        cod_vino=cod_vino,
        cepas=cepas,
    )


async def reemplazar_maridajes_vino(
    conn: AsyncConnection,
    cod_vino: int,
    maridajes: list[int],
) -> None:
    """Reemplaza los maridajes asociados a un vino."""

    async with conn.cursor() as cur:
        await cur.execute(
            """
            DELETE FROM vino_maridaje
            WHERE cod_vino = %s
            """,
            (cod_vino,),
        )

    await insertar_maridajes_vino(
        conn=conn,
        cod_vino=cod_vino,
        maridajes=maridajes,
    )


async def eliminar_vino(
    conn: AsyncConnection,
    cod_vino: int,
) -> bool:
    """Elimina un vino si las restricciones de PostgreSQL lo permiten."""

    async with conn.cursor() as cur:
        await cur.execute(
            """
            DELETE FROM vino
            WHERE cod_vino = %s
            RETURNING cod_vino
            """,
            (cod_vino,),
        )

        fila = await cur.fetchone()
        return fila is not None
