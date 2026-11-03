"""Healthcheck real de PostgreSQL, no una respuesta constante."""

import psycopg
from fastapi import APIRouter, Request
from psycopg_pool import PoolTimeout
from starlette.responses import JSONResponse

router = APIRouter(tags=["Salud"])


@router.get("/salud", summary="Comprueba conectividad a PostgreSQL")
async def salud(request: Request):
    try:
        async with request.app.state.db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1, current_user")
                fila = await cur.fetchone()
                if not fila or fila[0] != 1 or fila[1] != "bodega_api":
                    return JSONResponse(
                        status_code=503,
                        content={"error": {"codigo": "DB_ROL_INVALIDO", "mensaje": "Conexión sin el rol requerido."}},
                    )
        return {"estado": "ok", "base_datos": "conectada"}
    except (psycopg.Error, PoolTimeout):
        return JSONResponse(
            status_code=503,
            content={"error": {"codigo": "DB_NO_DISPONIBLE", "mensaje": "No se pudo conectar a la base."}},
        )
