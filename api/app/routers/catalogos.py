
"""Endpoints de los catálogos auxiliares del frontend."""

from fastapi import APIRouter, Request

from app.repositories import catalogos as repo
from app.schemas.catalogos import (
    BodegaSalida,
    CepaSalida,
    MaridajeSalida,
)


router = APIRouter(tags=["Catálogos"])


@router.get(
    "/bodegas",
    response_model=list[BodegaSalida],
    summary="Listar bodegas",
)
async def obtener_bodegas(request: Request):
    """Devuelve las bodegas disponibles."""

    async with request.app.state.db_pool.connection() as conn:
        return await repo.listar_bodegas(conn)


@router.get(
    "/cepas",
    response_model=list[CepaSalida],
    summary="Listar cepas",
)
async def obtener_cepas(request: Request):
    """Devuelve las cepas disponibles."""

    async with request.app.state.db_pool.connection() as conn:
        return await repo.listar_cepas(conn)


@router.get(
    "/maridajes",
    response_model=list[MaridajeSalida],
    summary="Listar maridajes",
)
async def obtener_maridajes(request: Request):
    """Devuelve los maridajes disponibles."""

    async with request.app.state.db_pool.connection() as conn:
        return await repo.listar_maridajes(conn)
