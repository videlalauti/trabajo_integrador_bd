"""Aplicacion de demostracion; NO es app.main de Render productivo.

Comando exclusivo en un segundo servicio: uvicorn app.demo_main:app.
Nunca registrar GuardianDemoAislada ni su modo en app.main.
"""
from contextlib import asynccontextmanager
import os

import psycopg
from psycopg_pool import PoolTimeout
from fastapi import FastAPI, Query, Request

from app.core.database import lifespan as lifespan_db
from app.core.demo_guard import GuardianDemoAislada, validar_configuracion_demo
from app.core.errores import manejador_sqlstate
from app.routers import salud, vinos, catalogos, salas, clientes, comprobantes, transferencias, reportes


@asynccontextmanager
async def lifespan_demo(app: FastAPI):
    # Fallar ANTES de construir/abrir el pool de conexiones.
    validar_configuracion_demo()
    async with lifespan_db(app):
        yield


app = FastAPI(title="Bodegas del Atuel - DEMO AISLADA", lifespan=lifespan_demo,
              docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GuardianDemoAislada)
app.add_exception_handler(psycopg.Error, manejador_sqlstate)
app.add_exception_handler(PoolTimeout, manejador_sqlstate)
for router in (
    salud.router, vinos.router, catalogos.router, salas.router,
    clientes.router, comprobantes.router, transferencias.router, reportes.router,
):
    app.include_router(router)


# Endpoints exclusivamente de demostracion: no alterar app.main. Solo
# devuelven agregados e identificadores ficticios desde la base aislada.
@app.get("/demo/identidad")
async def demo_identidad():
    return {"modo": "aislado",
            "proyecto_ref": os.getenv("FASE8_DEMO_PROJECT_REF", "LOCAL")}


@app.get("/demo/candidatos")
async def demo_candidatos(request: Request):
    async with request.app.state.db_pool.connection() as conn:
        # Stock suficiente para una venta pequena Y una transferencia desde
        # deposito. No devuelve datos personales, solo identificadores.
        fila = await (await conn.execute("""
            SELECT (SELECT id_cliente FROM public.cliente ORDER BY id_cliente LIMIT 1),
                   ss.id_sala, ss.cod_vino, ss.cantidad AS stock_sala,
                   sd.cantidad AS stock_deposito
              FROM public.stock_sala ss
              JOIN public.stock_deposito sd ON sd.cod_vino = ss.cod_vino
             WHERE ss.cantidad BETWEEN 2 AND 1000000
               AND sd.cantidad BETWEEN 2 AND 1000000
             ORDER BY ss.id_sala, ss.cod_vino
             LIMIT 1
        """)).fetchone()
        if not fila or fila[0] is None:
            return {"disponible": False}
        return {"disponible": True, "id_cliente": fila[0], "id_sala": fila[1],
                "cod_vino": fila[2], "stock_sala": fila[3], "stock_deposito": fila[4]}


@app.get("/demo/estado")
async def demo_estado(request: Request, id_sala: int = Query(gt=0), cod_vino: int = Query(gt=0)):
    async with request.app.state.db_pool.connection() as conn:
        fila = await (await conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM public.comprobante),
                (SELECT COUNT(*) FROM public.renglon_comprobante),
                (SELECT COALESCE(SUM(cantidad), 0) FROM public.stock_sala
                  WHERE id_sala = %s AND cod_vino = %s),
                (SELECT COALESCE(SUM(cantidad), 0) FROM public.stock_deposito
                  WHERE cod_vino = %s),
                (SELECT COUNT(*) FROM public.transferencia)
        """, (id_sala, cod_vino, cod_vino))).fetchone()
        return {"comprobantes": fila[0], "renglones": fila[1],
                "stock_sala": fila[2], "stock_deposito": fila[3],
                "transferencias": fila[4]}
