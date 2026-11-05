"""Endpoints REST para la gestion de clientes."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from app.repositories import clientes as repo
from app.schemas.clientes import (
    ClienteEntrada,
    ClienteSalida,
    ListadoClientes,
)


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
)


@router.get(
    "",
    response_model=ListadoClientes,
    summary="Listar clientes",
)
async def listar_clientes(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    tipo_cliente: Literal[
        "socio", "distribuidor", "exportador"
    ] | None = None,
):
    """Listado paginado con filtro opcional por tipo."""

    async with request.app.state.db_pool.connection() as conn:
        items, total = await repo.listar_clientes(
            conn,
            page,
            page_size,
            tipo_cliente,
        )

    return ListadoClientes(
        items=items,
        total=total,
        pagina=page,
        tamanio=page_size,
    )


@router.get(
    "/{id_cliente}",
    response_model=ClienteSalida,
    summary="Consultar un cliente",
)
async def obtener_cliente(
    id_cliente: int,
    request: Request,
):
    """Busca un cliente por su clave primaria."""

    async with request.app.state.db_pool.connection() as conn:
        cliente = await repo.obtener_cliente(conn, id_cliente)

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado.",
        )

    return cliente


@router.post(
    "",
    response_model=ClienteSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un cliente",
)
async def crear_cliente(
    datos: ClienteEntrada,
    request: Request,
):
    """Inserta un cliente respetando las reglas de PostgreSQL."""

    async with request.app.state.db_pool.connection() as conn:
        cliente = await repo.crear_cliente(conn, datos)

    return cliente


@router.put(
    "/{id_cliente}",
    response_model=ClienteSalida,
    summary="Actualizar un cliente",
)
async def actualizar_cliente(
    id_cliente: int,
    datos: ClienteEntrada,
    request: Request,
):
    """Actualiza todos los campos editables."""

    async with request.app.state.db_pool.connection() as conn:
        cliente = await repo.actualizar_cliente(
            conn,
            id_cliente,
            datos,
        )

    if cliente is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado.",
        )

    return cliente


@router.delete(
    "/{id_cliente}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un cliente",
)
async def eliminar_cliente(
    id_cliente: int,
    request: Request,
):
    """Elimina el cliente si PostgreSQL lo permite."""

    async with request.app.state.db_pool.connection() as conn:
        eliminado = await repo.eliminar_cliente(conn, id_cliente)

    if eliminado is None:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado.",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
