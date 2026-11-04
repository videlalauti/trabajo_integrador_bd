"""Services de transferencias: cada funcion es UNA transaccion.

Si sp_procesar_transferencia rechaza (por ejemplo, stock insuficiente), la
excepcion provoca ROLLBACK: ni el deposito ni la sala ni el estado cambian.
Python no calcula stock ni decide estados.
"""
from psycopg_pool import AsyncConnectionPool

from app.repositories import transferencias as repo
from app.schemas.transferencias import RenglonTransferenciaCrear, TransferenciaCrear
from app.services.errores_modulo import RecursoNoEncontrado


async def _detalle(conn, nro_solicitud: int) -> dict:
    cabecera = await repo.obtener_cabecera(conn, nro_solicitud)
    if cabecera is None:
        raise RecursoNoEncontrado(f"La transferencia {nro_solicitud} no existe.")
    cabecera["renglones"] = await repo.obtener_renglones(conn, nro_solicitud)
    return cabecera


async def _verificar_existe(conn, nro_solicitud: int) -> None:
    if not await repo.existe_transferencia(conn, nro_solicitud):
        raise RecursoNoEncontrado(f"La transferencia {nro_solicitud} no existe.")


async def obtener_transferencia(pool: AsyncConnectionPool, nro_solicitud: int) -> dict:
    async with pool.connection() as conn:
        return await _detalle(conn, nro_solicitud)


async def crear_transferencia(pool: AsyncConnectionPool, datos: TransferenciaCrear) -> dict:
    async with pool.connection() as conn:
        nro = await repo.insertar_transferencia(conn, datos.id_sala)
        return await _detalle(conn, nro)


async def agregar_renglon(pool: AsyncConnectionPool, nro_solicitud: int, datos: RenglonTransferenciaCrear) -> dict:
    async with pool.connection() as conn:
        await _verificar_existe(conn, nro_solicitud)
        await repo.insertar_renglon(conn, nro_solicitud, datos.cod_vino, datos.cantidad)
        return await _detalle(conn, nro_solicitud)


async def terminar_transferencia(pool: AsyncConnectionPool, nro_solicitud: int) -> dict:
    async with pool.connection() as conn:
        await _verificar_existe(conn, nro_solicitud)
        await repo.terminar_transferencia(conn, nro_solicitud)
        return await _detalle(conn, nro_solicitud)


async def procesar_transferencia(pool: AsyncConnectionPool, nro_solicitud: int) -> dict:
    async with pool.connection() as conn:
        await _verificar_existe(conn, nro_solicitud)
        await repo.procesar_transferencia(conn, nro_solicitud)
        return await _detalle(conn, nro_solicitud)
