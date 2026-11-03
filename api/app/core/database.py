"""Pool compartido creado al iniciar y cerrado al detener FastAPI."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

from .config import get_db_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_db_settings()
    pool = AsyncConnectionPool(
        conninfo="",
        kwargs={
            "host": cfg.host,
            "port": cfg.port,
            "dbname": cfg.dbname,
            "user": cfg.user,
            "password": cfg.password,
            "connect_timeout": 5,
        },
        min_size=cfg.pool_min,
        max_size=cfg.pool_max,
        timeout=5,
        open=False,
    )
    app.state.db_pool = pool
    await pool.open(wait=False)
    try:
        yield
    finally:
        await pool.close()
