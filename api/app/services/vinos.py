
"""Servicios y transacciones del módulo de vinos."""

from psycopg import AsyncConnection

from app.repositories.vinos import (
    insertar_vino,
    insertar_cepas_vino,
    insertar_maridajes_vino,
    actualizar_datos_vino,
    reemplazar_cepas_vino,
    reemplazar_maridajes_vino,
)
from app.schemas.vinos import VinoCrear, VinoActualizar


async def crear_vino(
    conn: AsyncConnection,
    datos: VinoCrear,
) -> int:
    """Crea un vino con sus cepas y maridajes en una transacción."""

    async with conn.transaction():
        # 1. Insertar el vino y recuperar su código.
        cod_vino = await insertar_vino(
            conn,
            datos.model_dump(exclude={"cepas", "maridajes"}),
        )

        # 2. Insertar las cepas y sus porcentajes.
        await insertar_cepas_vino(
            conn,
            cod_vino,
            [cepa.model_dump() for cepa in datos.cepas],
        )

        # 3. Insertar los maridajes asociados.
        await insertar_maridajes_vino(
            conn,
            cod_vino,
            datos.maridajes,
        )

    return cod_vino


async def actualizar_vino(
    conn: AsyncConnection,
    cod_vino: int,
    datos: VinoActualizar,
) -> bool:
    """Actualiza un vino completo dentro de una transacción."""

    async with conn.transaction():
        # Actualizar los datos principales.
        actualizado = await actualizar_datos_vino(
            conn,
            cod_vino,
            datos.model_dump(exclude={"cepas", "maridajes"}),
        )

        if not actualizado:
            return False

        # Reemplazar la composición de cepas.
        await reemplazar_cepas_vino(
            conn,
            cod_vino,
            [cepa.model_dump() for cepa in datos.cepas],
        )

        # Reemplazar los maridajes.
        await reemplazar_maridajes_vino(
            conn,
            cod_vino,
            datos.maridajes,
        )

    return True
