"""Endpoints de ingresos al deposito central (RN-10, RN-12).

Circuito: POST /ingresos -> POST /ingresos/{cod}/renglones ->
POST /ingresos/{cod}/terminar -> POST /ingresos/{cod}/procesar.
Sin SQL en este archivo: todo pasa por services/ingresos.py.
"""
from fastapi import APIRouter, Request, status

from app.routers.respuestas_comunes import RESPUESTAS_ERROR, respuesta_no_encontrado
from app.schemas.ingresos import IngresoCrear, IngresoDetalle, RenglonIngresoCrear
from app.services import ingresos as servicio
from app.services.errores_modulo import RecursoNoEncontrado

router = APIRouter(prefix="/ingresos", tags=["Ingresos"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=IngresoDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Crear un ingreso en confeccion",
)
async def crear_ingreso(datos: IngresoCrear, request: Request):
    return await servicio.crear_ingreso(request.app.state.db_pool, datos)


@router.get(
    "/{cod_ingreso}",
    response_model=IngresoDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Detalle del ingreso con renglones y stock actual del deposito",
)
async def obtener_ingreso(cod_ingreso: int, request: Request):
    try:
        return await servicio.obtener_ingreso(request.app.state.db_pool, cod_ingreso)
    except RecursoNoEncontrado as exc:
        return respuesta_no_encontrado(exc)


@router.post(
    "/{cod_ingreso}/renglones",
    status_code=status.HTTP_201_CREATED,
    response_model=IngresoDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Agregar un renglon (solo si el ingreso esta en confeccion, RN-12)",
)
async def agregar_renglon(cod_ingreso: int, datos: RenglonIngresoCrear, request: Request):
    try:
        return await servicio.agregar_renglon(request.app.state.db_pool, cod_ingreso, datos)
    except RecursoNoEncontrado as exc:
        return respuesta_no_encontrado(exc)


@router.post(
    "/{cod_ingreso}/terminar",
    response_model=IngresoDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Pasar a terminado mediante sp_terminar_ingreso",
)
async def terminar_ingreso(cod_ingreso: int, request: Request):
    try:
        return await servicio.terminar_ingreso(request.app.state.db_pool, cod_ingreso)
    except RecursoNoEncontrado as exc:
        return respuesta_no_encontrado(exc)


@router.post(
    "/{cod_ingreso}/procesar",
    response_model=IngresoDetalle,
    responses=RESPUESTAS_ERROR,
    summary="Procesar mediante sp_procesar_ingreso (suma al stock del deposito)",
)
async def procesar_ingreso(cod_ingreso: int, request: Request):
    try:
        return await servicio.procesar_ingreso(request.app.state.db_pool, cod_ingreso)
    except RecursoNoEncontrado as exc:
        return respuesta_no_encontrado(exc)
