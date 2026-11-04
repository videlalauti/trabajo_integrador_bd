
"""Endpoints HTTP para comprobantes de venta."""

from fastapi import APIRouter, Path, Request, status
from fastapi.responses import JSONResponse

from ..schemas.comprobantes import (
    ComprobanteCrear,
    ComprobanteRespuesta,
)
from ..services import comprobantes as servicio


router = APIRouter(
    prefix="/comprobantes",
    tags=["Comprobantes"],
)


@router.post(
    "",
    response_model=ComprobanteRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una venta completa",
    responses={
        404: {"description": "Vino inexistente"},
        409: {"description": "Conflicto o stock insuficiente"},
        422: {"description": "Datos invalidos"},
    },
)
async def crear_comprobante(
    datos: ComprobanteCrear,
    request: Request,
):
    """
    Registra cabecera y renglones en una transaccion.

    Los triggers de PostgreSQL calculan importes,
    aplican descuentos y controlan el stock.
    """

    pool = request.app.state.db_pool

    try:
        resultado = await servicio.crear_comprobante(
            pool,
            datos,
        )
    except servicio.VinoNoEncontradoError as exc:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "codigo": "VINO_NO_ENCONTRADO",
                    "mensaje": str(exc),
                }
            },
        )

    return resultado


@router.get(
    "/{nro_comprobante}",
    response_model=ComprobanteRespuesta,
    summary="Consultar un comprobante",
    responses={
        404: {"description": "Comprobante inexistente"},
    },
)
async def obtener_comprobante(
    request: Request,
    nro_comprobante: int = Path(gt=0),
):
    """
    Consulta la cabecera y todos sus renglones.

    Los importes se leen directamente de PostgreSQL.
    """

    pool = request.app.state.db_pool

    resultado = await servicio.consultar_comprobante(
        pool,
        nro_comprobante,
    )

    if resultado is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "codigo": "COMPROBANTE_NO_ENCONTRADO",
                    "mensaje": (
                        f"El comprobante {nro_comprobante} "
                        "no existe"
                    ),
                }
            },
        )

    return resultado
