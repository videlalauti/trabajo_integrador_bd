
"""Servicios de comprobantes y transacciones de ventas."""

from typing import Any

from psycopg_pool import AsyncConnectionPool

from ..repositories import comprobantes as repo
from ..schemas.comprobantes import ComprobanteCrear


class VinoNoEncontradoError(ValueError):
    """El vino solicitado no existe en el catalogo."""


async def crear_comprobante(
    pool: AsyncConnectionPool,
    datos: ComprobanteCrear,
) -> dict[str, Any]:
    """
    Crea una venta completa en una unica transaccion.

    La cabecera, los renglones y la lectura de la respuesta
    se realizan antes del COMMIT.

    PostgreSQL controla el stock, descuentos y totales.
    """

    async with pool.connection() as conn:

        async with conn.transaction():

            # 1. Insertar la cabecera.
            nro = await repo.insertar_cabecera(
                conn,
                datos.id_cliente,
                datos.id_sala,
            )

            # 2. Insertar todos los renglones.
            for renglon in datos.renglones:

                insertado = await repo.insertar_renglon(
                    conn,
                    nro,
                    renglon.cod_vino,
                    renglon.cantidad,
                )

                if not insertado:
                    raise VinoNoEncontradoError(
                        f"El vino {renglon.cod_vino} no existe"
                    )

            # 3. Consultar los importes dentro de la transaccion.
            cabecera = await repo.obtener_cabecera(
                conn,
                nro,
            )

            if cabecera is None:
                raise RuntimeError(
                    "No se encontro el comprobante creado"
                )

            # 4. Recuperar todos los renglones.
            renglones = await repo.obtener_renglones(
                conn,
                nro,
            )

            # 5. Preparar la respuesta antes del COMMIT.
            resultado = {
                **cabecera,
                "renglones": renglones,
            }

        # Al salir correctamente del bloque se ejecuta COMMIT.
        # Ante cualquier excepcion se ejecuta ROLLBACK.

    # Solo devolvemos la respuesta si el COMMIT fue exitoso.
    return resultado


async def consultar_comprobante(
    pool: AsyncConnectionPool,
    nro_comprobante: int,
) -> dict[str, Any] | None:
    """
    Consulta una venta existente con todos sus renglones.
    No modifica los datos.
    """

    async with pool.connection() as conn:

        cabecera = await repo.obtener_cabecera(
            conn,
            nro_comprobante,
        )

        if cabecera is None:
            return None

        renglones = await repo.obtener_renglones(
            conn,
            nro_comprobante,
        )

        return {
            **cabecera,
            "renglones": renglones,
        }
