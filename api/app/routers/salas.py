
"""Endpoints de consulta del catálogo de salas de venta."""

from fastapi import APIRouter, Request

from app.repositories import salas as repo
from app.schemas.salas import SalaSalida


router = APIRouter(
    prefix="/salas",
    tags=["Salas"],
)


@router.get(
    "",
    response_model=list[SalaSalida],
    summary="Listar salas de venta",
)
async def obtener_salas(request: Request):
    """Devuelve las salas de venta con sus localidades."""

    async with request.app.state.db_pool.connection() as conn:
        return await repo.listar_salas(conn)
