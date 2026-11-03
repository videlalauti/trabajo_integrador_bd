"""Configuración local sin credenciales en código ni en commits."""
from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

# .../repo/api/app/core/config.py -> raíz del repositorio.
REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)


@dataclass(frozen=True)
class DBSettings:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    pool_min: int
    pool_max: int


def get_db_settings() -> DBSettings:
    s = DBSettings(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "bodegas_fase6_dev"),
        user=os.getenv("DB_USER", "bodega_api"),
        password=os.getenv("DB_PASSWORD", ""),
        pool_min=int(os.getenv("DB_POOL_MIN", "1")),
        pool_max=int(os.getenv("DB_POOL_MAX", "5")),
    )
    if s.user != "bodega_api":
        raise RuntimeError("La API debe conectarse con el rol bodega_api (no postgres).")
    if not s.password:
        raise RuntimeError("Falta DB_PASSWORD en el .env local (no subir .env a Git).")
    if s.pool_min < 1 or s.pool_max < s.pool_min:
        raise RuntimeError("Rango inválido para DB_POOL_MIN y DB_POOL_MAX.")
    return s
