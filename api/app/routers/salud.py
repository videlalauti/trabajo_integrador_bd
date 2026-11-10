"""Healthcheck real de PostgreSQL, no una respuesta constante."""

import psycopg
from fastapi import APIRouter, Request
from psycopg_pool import PoolTimeout
from starlette.responses import JSONResponse

router = APIRouter(tags=["Salud"])


def _error(codigo: str, mensaje: str) -> JSONResponse:
    return JSONResponse(status_code=503, content={"error": {"codigo": codigo, "mensaje": mensaje}})


@router.get("/salud", summary="Comprueba conectividad a PostgreSQL")
async def salud(request: Request):
    try:
        async with request.app.state.db_pool.connection() as conn:
            # TLS real de ESTA conexión (lado cliente, informado por libpq).
            tls_activo = bool(conn.pgconn.ssl_in_use)
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1, current_user")
                fila = await cur.fetchone()
                # Con el Session pooler el usuario de conexión es
                # bodega_api.<PROJECT_REF>, pero el rol efectivo es bodega_api.
                if not fila or fila[0] != 1 or fila[1] != "bodega_api":
                    return _error("DB_ROL_INVALIDO", "Conexión sin el rol requerido.")
        if getattr(request.app.state, "db_requiere_tls", False) and not tls_activo:
            return _error("DB_SIN_TLS", "La conexión a la base no está cifrada.")
        return {"estado": "ok", "base_datos": "conectada", "tls": tls_activo}
    except (psycopg.Error, PoolTimeout):
        return _error("DB_NO_DISPONIBLE", "No se pudo conectar a la base.")
