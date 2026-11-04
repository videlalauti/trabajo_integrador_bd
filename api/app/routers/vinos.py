
"""Endpoints HTTP del módulo de vinos."""

from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.repositories.vinos import listar_vinos, obtener_vino_por_codigo
from app.schemas.vinos import TipoVino, VinosPaginados

from fastapi import status

from app.schemas.vinos import VinoCrear
from app.services.vinos import crear_vino

from app.schemas.vinos import VinoActualizar
from app.services.vinos import actualizar_vino

from app.repositories.vinos import eliminar_vino

router = APIRouter(prefix="/vinos", tags=["Vinos"])


@router.get(
    "",
    response_model=VinosPaginados,
    summary="Lista vinos con filtros y paginación",
)
async def obtener_vinos(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    tipo: TipoVino | None = None,
    cepa: int | None = Query(default=None, gt=0),
    bodega: str | None = None,
    anada: int | None = None,
):
    """Devuelve un listado paginado de vinos."""

    async with request.app.state.db_pool.connection() as conn:
        resultado = await listar_vinos(
            conn=conn,
            pagina=page,
            tamanio=page_size,
            tipo=tipo,
            cepa=cepa,
            bodega=bodega,
            anada=anada,
        )

    return resultado


@router.get(
    "/{cod_vino}",
    summary="Obtiene un vino con sus cepas y maridajes",
)
async def obtener_vino(
    request: Request,
    cod_vino: int = Path(gt=0),
):
    """Devuelve el detalle completo de un vino."""

    async with request.app.state.db_pool.connection() as conn:
        vino = await obtener_vino_por_codigo(
            conn=conn,
            cod_vino=cod_vino,
        )

    if vino is None:
        raise HTTPException(
            status_code=404,
            detail="El vino solicitado no existe.",
        )

    return vino


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crea un vino con sus cepas y maridajes",
)
async def registrar_vino(
    request: Request,
    datos: VinoCrear,
):
    """Registra un vino completo en una transacción."""

    async with request.app.state.db_pool.connection() as conn:
        cod_vino = await crear_vino(
            conn=conn,
            datos=datos,
        )

    return {
        "cod_vino": cod_vino,
        "mensaje": "Vino creado correctamente.",
    }


@router.put(
    "/{cod_vino}",
    summary="Actualiza un vino con sus cepas y maridajes",
)
async def modificar_vino(
    request: Request,
    datos: VinoActualizar,
    cod_vino: int = Path(gt=0),
):
    """Actualiza un vino completo."""

    async with request.app.state.db_pool.connection() as conn:
        actualizado = await actualizar_vino(
            conn=conn,
            cod_vino=cod_vino,
            datos=datos,
        )

    if not actualizado:
        raise HTTPException(
            status_code=404,
            detail="El vino solicitado no existe.",
        )

    return {
        "cod_vino": cod_vino,
        "mensaje": "Vino actualizado correctamente.",
    }


@router.delete(
    "/{cod_vino}",
    summary="Elimina un vino",
)
async def borrar_vino(
    request: Request,
    cod_vino: int = Path(gt=0),
):
    """Elimina un vino respetando las restricciones de la base."""

    async with request.app.state.db_pool.connection() as conn:
        eliminado = await eliminar_vino(
            conn=conn,
            cod_vino=cod_vino,
        )

    if not eliminado:
        raise HTTPException(
            status_code=404,
            detail="El vino solicitado no existe.",
        )

    return {
        "cod_vino": cod_vino,
        "mensaje": "Vino eliminado correctamente.",
    }
