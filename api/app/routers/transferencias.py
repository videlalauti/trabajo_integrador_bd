"""Endpoints de transferencias deposito -> sala (RN-11, RN-12).

Circuito: POST /transferencias -> POST /transferencias/{nro}/renglones ->
POST /transferencias/{nro}/terminar -> POST /transferencias/{nro}/procesar.
Sin SQL en este archivo: todo pasa por services/transferencias.py.
"""
from fastapi import APIRouter, Request, status

from app.routers.respuestas_comunes import RESPUESTAS_ERROR, respuesta_no_encontrado
from app.schemas.transferencias import (
    RenglonTransferenciaCrear,
    TransferenciaCrear,
    TransferenciaDetalle,
)
from app.services import transferencias as servicio
from app.services.errores_modulo import RecursoNoEncontrado

router = APIRouter(prefix="/transferencias", tags=["Transferencias"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TransferenciaDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Crear una transferencia en confeccion (fecha actual fijada por la base)",
)
async def crear_transferencia(datos: TransferenciaCrear, request: Request):
    return await servicio.crear_transferencia(request.app.state.db_pool, datos)


@router.get(
    "/{nro_solicitud}",
    response_model=TransferenciaDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Detalle con renglones y stock actual de deposito y sala",
)
async def obtener_transferencia(nro_solicitud: int, request: Request):
    try:
        return await servicio.obtener_transferencia(request.app.state.db_pool, nro_solicitud)
    except RecursoNoEncontrado as exc:
        return respuesta_no_encontrado(exc)


@router.post(
    "/{nro_solicitud}/renglones",
    status_code=status.HTTP_201_CREATED,
    response_model=TransferenciaDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Agregar un renglon (solo en confeccion, RN-12)",
)
async def agregar_renglon(nro_solicitud: int, datos: RenglonTransferenciaCrear, request: Request):
    try:
        return await servicio.agregar_renglon(request.app.state.db_pool, nro_solicitud, datos)
    except RecursoNoEncontrado as exc:
        return respuesta_no_encontrado(exc)


@router.post(
    "/{nro_solicitud}/terminar",
    response_model=TransferenciaDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Pasar a terminado mediante sp_terminar_transferencia",
)
async def terminar_transferencia(nro_solicitud: int, request: Request):
    try:
        return await servicio.terminar_transferencia(request.app.state.db_pool, nro_solicitud)
    except RecursoNoEncontrado as exc:
        return respuesta_no_encontrado(exc)


@router.post(
    "/{nro_solicitud}/procesar",
    response_model=TransferenciaDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Procesar mediante sp_procesar_transferencia (deposito -> sala)",
)
async def procesar_transferencia(nro_solicitud: int, request: Request):
    try:
        return await servicio.procesar_transferencia(request.app.state.db_pool, nro_solicitud)
    except RecursoNoEncontrado as exc:
        return respuesta_no_encontrado(exc)
