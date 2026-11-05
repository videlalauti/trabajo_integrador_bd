"""Endpoints REST de los cinco reportes obligatorios."""

from fastapi import APIRouter, HTTPException, Query, Request

from app.repositories import reportes as repo
from app.schemas.reportes import (
    TopVino,
    VentaPorSala,
    ListadoVinosSinStock,
    TransportistaActivo,
    ReporteTrazabilidad,
)


router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
)


@router.get(
    "/top-vinos",
    response_model=list[TopVino],
    summary="Diez vinos mas vendidos",
)
async def top_vinos(request: Request):
    """Ranking global por cantidad de botellas vendidas."""

    async with request.app.state.db_pool.connection() as conn:
        return await repo.top_vinos(conn)


@router.get(
    "/ventas-por-sala",
    response_model=list[VentaPorSala],
    summary="Ventas por sala del ultimo trimestre",
)
async def ventas_por_sala(request: Request):
    """Importes de ventas calculados por PostgreSQL."""

    async with request.app.state.db_pool.connection() as conn:
        return await repo.ventas_por_sala(conn)


@router.get(
    "/vinos-sin-stock",
    response_model=ListadoVinosSinStock,
    summary="Vinos sin stock en una sala",
)
async def vinos_sin_stock(
    request: Request,
    id_sala: int = Query(ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """
    Vinos sin stock en la sala indicada,
    pero disponibles en el deposito central.
    """

    async with request.app.state.db_pool.connection() as conn:
        if not await repo.existe_sala(conn, id_sala):
            raise HTTPException(
                status_code=404,
                detail="Sala no encontrada.",
            )

        return await repo.vinos_sin_stock(
            conn,
            id_sala,
            page,
            page_size,
        )


@router.get(
    "/transportista-activo",
    response_model=TransportistaActivo | None,
    summary="Transportista con mayor actividad",
)
async def transportista_activo(request: Request):
    """
    Transportista con mas ingresos en el ultimo mes.

    Si no existen ingresos en ese periodo, devuelve null.
    """

    async with request.app.state.db_pool.connection() as conn:
        return await repo.transportista_activo(conn)


@router.get(
    "/trazabilidad/{cod}",
    response_model=ReporteTrazabilidad,
    summary="Trazabilidad limitada de un vino",
)
async def trazabilidad(
    request: Request,
    cod: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """
    Informa el vino, su bodega y los lotes registrados
    en esa bodega.

    No afirma una relacion directa vino-lote.
    """

    if cod <= 0:
        raise HTTPException(
            status_code=422,
            detail="El codigo del vino debe ser positivo.",
        )

    async with request.app.state.db_pool.connection() as conn:
        resultado = await repo.trazabilidad(
            conn,
            cod,
            page,
            page_size,
        )

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="Vino no encontrado.",
        )

    return resultado
