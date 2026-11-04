"""Respuestas documentadas en OpenAPI para los routers de ingresos y
transferencias, con el formato de error del contrato compartido.

Los errores de PostgreSQL (409/422/400/503) los genera core/errores.py;
aca solo se documentan y se arma el 404 de documento inexistente.
"""
from fastapi.responses import JSONResponse

from app.services.errores_modulo import RecursoNoEncontrado

_ERROR = {
    "application/json": {
        "example": {"error": {"codigo": "P0001", "mensaje": "Mensaje de la regla de negocio"}}
    }
}

RESPUESTAS_ERROR = {
    404: {"description": "El documento no existe (codigo NO_ENCONTRADO)", "content": _ERROR},
    409: {"description": "Rechazo de una regla de la base (P0001), FK o UNIQUE", "content": _ERROR},
    422: {"description": "CHECK o NOT NULL de la base, o JSON con tipos invalidos"},
}


def respuesta_no_encontrado(exc: RecursoNoEncontrado) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": {"codigo": "NO_ENCONTRADO", "mensaje": exc.mensaje}},
    )
