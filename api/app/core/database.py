"""Pool compartido creado al iniciar y cerrado al detener FastAPI."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

from .config import get_db_settings

# Las conexiones inactivas se cierran antes de que las corte el pooler del
# proveedor; además, cada conexión se comprueba antes de entregarla.
MAX_INACTIVIDAD_SEGUNDOS = 300


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_db_settings()
    parametros = {
        "host": cfg.host,
        "port": cfg.port,
        "dbname": cfg.dbname,
        "user": cfg.user,
        "password": cfg.password,
        "connect_timeout": cfg.connect_timeout,
        # TLS explícito: nunca queda librado al valor por defecto de libpq.
        "sslmode": cfg.sslmode,
        "application_name": "bodegas_atuel_api",
    }
    if cfg.sslrootcert:
        parametros["sslrootcert"] = cfg.sslrootcert

    pool = AsyncConnectionPool(
        conninfo="",
        kwargs=parametros,
        min_size=cfg.pool_min,
        max_size=cfg.pool_max,
        timeout=cfg.pool_timeout,
        max_idle=MAX_INACTIVIDAD_SEGUNDOS,
        check=AsyncConnectionPool.check_connection,
        open=False,
    )
    app.state.db_pool = pool
    # /salud usa este dato para exigir TLS real cuando la configuración lo pide.
    app.state.db_requiere_tls = cfg.requiere_tls
    await pool.open(wait=False)
    try:
        yield
    finally:
        await pool.close()
