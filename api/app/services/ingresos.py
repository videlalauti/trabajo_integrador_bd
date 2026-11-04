"""Services de ingresos: cada funcion es UNA transaccion.

`async with pool.connection()` hace COMMIT al salir sin errores y ROLLBACK si
ocurre una excepcion (incluidos los RAISE EXCEPTION de triggers y
procedimientos). Asi un rechazo nunca deja cambios a medias.
Python no calcula stock ni decide estados: solo llama a la base.
"""
from psycopg_pool import AsyncConnectionPool

from app.repositories import ingresos as repo
from app.schemas.ingresos import IngresoCrear, RenglonIngresoCrear
from app.services.errores_modulo import RecursoNoEncontrado


async def _detalle(conn, cod_ingreso: int) -> dict:
    cabecera = await repo.obtener_cabecera(conn, cod_ingreso)
    if cabecera is None:
        raise RecursoNoEncontrado(f"El ingreso {cod_ingreso} no existe.")
    cabecera["renglones"] = await repo.obtener_renglones(conn, cod_ingreso)
    return cabecera


async def _verificar_existe(conn, cod_ingreso: int) -> None:
    if not await repo.existe_ingreso(conn, cod_ingreso):
        raise RecursoNoEncontrado(f"El ingreso {cod_ingreso} no existe.")


async def obtener_ingreso(pool: AsyncConnectionPool, cod_ingreso: int) -> dict:
    async with pool.connection() as conn:
        return await _detalle(conn, cod_ingreso)


async def crear_ingreso(pool: AsyncConnectionPool, datos: IngresoCrear) -> dict:
    async with pool.connection() as conn:
        cod = await repo.insertar_ingreso(conn, datos.cod_transporte, datos.cuit_bodega, datos.fecha)
        return await _detalle(conn, cod)


async def agregar_renglon(pool: AsyncConnectionPool, cod_ingreso: int, datos: RenglonIngresoCrear) -> dict:
    async with pool.connection() as conn:
        await _verificar_existe(conn, cod_ingreso)
        await repo.insertar_renglon(conn, cod_ingreso, datos.cod_vino, datos.cantidad)
        return await _detalle(conn, cod_ingreso)


async def terminar_ingreso(pool: AsyncConnectionPool, cod_ingreso: int) -> dict:
    async with pool.connection() as conn:
        await _verificar_existe(conn, cod_ingreso)
        await repo.terminar_ingreso(conn, cod_ingreso)
        return await _detalle(conn, cod_ingreso)


async def procesar_ingreso(pool: AsyncConnectionPool, cod_ingreso: int) -> dict:
    async with pool.connection() as conn:
        await _verificar_existe(conn, cod_ingreso)
        await repo.procesar_ingreso(conn, cod_ingreso)
        return await _detalle(conn, cod_ingreso)
