"""Traducción centralizada de SQLSTATE a HTTP (primera versión)."""

import psycopg
from fastapi import Request
from fastapi.responses import JSONResponse
from psycopg_pool import PoolTimeout


ERRORES_SQLSTATE: dict[str, tuple[int, str]] = {
    "23505": (409, "Ya existe un registro con esos datos."),
    "23503": (409, "Existe un problema con una referencia o dependencia."),
    "23514": (422, "La operación incumple una restricción de datos."),
    "23502": (422, "Falta completar un dato obligatorio."),
    "22P02": (400, "El formato de un valor es inválido."),
    "40001": (503, "Conflicto de transacción: reintente."),
    "40P01": (503, "Interbloqueo: reintente."),
}


async def manejador_sqlstate(_request: Request, exc: psycopg.Error) -> JSONResponse:
    if isinstance(exc, PoolTimeout):
        codigo_http, mensaje = 503, "La base de datos no está disponible."
    elif exc.sqlstate == "P0001":
        codigo_http = 409
        # Los triggers/procedimientos definen este mensaje de regla.
        mensaje = getattr(exc.diag, "message_primary", None) or "Operación rechazada por una regla de negocio."
    else:
        codigo_http, mensaje = ERRORES_SQLSTATE.get(
            exc.sqlstate or "", (500, "No se pudo completar la operación.")
        )
    return JSONResponse(
        status_code=codigo_http,
        content={"error": {"codigo": exc.sqlstate or "DB_NO_DISPONIBLE", "mensaje": mensaje}},
    )
