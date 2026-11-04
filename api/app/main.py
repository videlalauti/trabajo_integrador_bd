"""Punto único de entrada de la API REST."""

import psycopg
from psycopg_pool import PoolTimeout
from fastapi import FastAPI

from app.core.database import lifespan
from app.core.errores import manejador_sqlstate
from app.routers import salud, vinos

app = FastAPI(
    title="Bodegas del Atuel - API REST",
    version="0.1.0",
    description="Integrador BD - Etapa 6. SQL explícito y reglas de negocio en PostgreSQL.",
    lifespan=lifespan,
)
app.add_exception_handler(psycopg.Error, manejador_sqlstate)
app.add_exception_handler(PoolTimeout, manejador_sqlstate)
app.include_router(salud.router)
app.include_router(vinos.router)

# Los routers de vinos, clientes, comprobantes, transferencias,
# ingresos y reportes se incorporan al integrarlos.
