"""Configuración de la conexión a PostgreSQL, sin credenciales en el código.

Funciona igual en local (.env en la raíz del repositorio) y en la nube
(variables de entorno del proveedor, por ejemplo el panel de Render).
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
import re

from dotenv import load_dotenv

# .../repo/api/app/core/config.py -> raíz del repositorio.
REPO_ROOT = Path(__file__).resolve().parents[3]
# En la nube no existe .env: las variables del proveedor tienen prioridad.
load_dotenv(REPO_ROOT / ".env", override=False)

# Rol de PostgreSQL obligatorio para la API (privilegios mínimos).
ROL_API = "bodega_api"

# Supabase Session pooler: el usuario de conexión es <rol>.<PROJECT_REF>.
# Solo se admite el rol bodega_api: nunca postgres ni otro rol.
_USUARIO_POOLER = re.compile(r"bodega_api\.[a-z0-9]{8,64}")
# Hosts del pooler compartido de Supabase (aws-<n>-<region>.pooler.supabase.com).
_SUFIJO_POOLER_SUPABASE = ".pooler.supabase.com"
PUERTO_SESSION_POOLER = 5432

# Modos de libpq. "allow" y "disable" no se admiten: nunca se elige
# conectarse sin cifrado de forma explícita.
SSLMODES_ADMITIDOS = ("prefer", "require", "verify-ca", "verify-full")
SSLMODES_CON_TLS = ("require", "verify-ca", "verify-full")

# Hosts considerados locales: la propia PC y los servicios de Docker Compose.
HOSTS_LOCALES = ("127.0.0.1", "localhost", "::1", "db", "postgres")


@dataclass(frozen=True)
class DBSettings:
    host: str
    port: int
    dbname: str
    user: str
    # repr=False: la contraseña nunca aparece al imprimir o registrar la configuración.
    password: str = field(repr=False)
    pool_min: int
    pool_max: int
    sslmode: str
    sslrootcert: str | None
    connect_timeout: int
    pool_timeout: float

    @property
    def requiere_tls(self) -> bool:
        return self.sslmode in SSLMODES_CON_TLS


def usuario_permitido(usuario: str) -> bool:
    """Formato admitido: bodega_api o bodega_api.<PROJECT_REF>."""
    return usuario == ROL_API or _USUARIO_POOLER.fullmatch(usuario) is not None


def es_pooler_supabase(host: str) -> bool:
    return host.lower().endswith(_SUFIJO_POOLER_SUPABASE)


def es_host_local(host: str) -> bool:
    return host.lower() in HOSTS_LOCALES


def _entero(nombre: str, por_defecto: str) -> int:
    valor = os.getenv(nombre, por_defecto)
    try:
        return int(valor)
    except ValueError:
        raise RuntimeError(f"{nombre} debe ser un número entero.") from None


def _decimal(nombre: str, por_defecto: str) -> float:
    valor = os.getenv(nombre, por_defecto)
    try:
        numero = float(valor)
    except ValueError:
        raise RuntimeError(f"{nombre} debe ser un número (por ejemplo 10 o 2.5).") from None
    # float() acepta "nan" e "inf": no son tiempos de espera válidos.
    if numero != numero or numero in (float("inf"), float("-inf")):
        raise RuntimeError(f"{nombre} debe ser un número finito.")
    return numero


def get_db_settings() -> DBSettings:
    host = os.getenv("DB_HOST", "127.0.0.1").strip()
    # Sin DB_SSLMODE explícito: "prefer" solo para un host local;
    # cualquier host remoto exige TLS ("require").
    sslmode_por_defecto = "prefer" if es_host_local(host) else "require"

    s = DBSettings(
        host=host,
        port=_entero("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "bodegas_fase6_dev"),
        user=os.getenv("DB_USER", ROL_API).strip(),
        password=os.getenv("DB_PASSWORD", ""),
        pool_min=_entero("DB_POOL_MIN", "1"),
        pool_max=_entero("DB_POOL_MAX", "5"),
        sslmode=os.getenv("DB_SSLMODE", sslmode_por_defecto).strip().lower(),
        sslrootcert=os.getenv("DB_SSLROOTCERT") or None,
        connect_timeout=_entero("DB_CONNECT_TIMEOUT", "10"),
        pool_timeout=_decimal("DB_POOL_TIMEOUT", "10"),
    )

    # Ningún mensaje incluye la contraseña ni el usuario completo.
    if not s.host:
        raise RuntimeError("DB_HOST no puede estar vacío.")
    if not 1 <= s.port <= 65535:
        raise RuntimeError("DB_PORT debe estar entre 1 y 65535.")
    if es_pooler_supabase(s.host):
        # El pooler compartido exige <rol>.<PROJECT_REF>; el rol efectivo de
        # la sesión SQL sigue siendo bodega_api (lo verifica /salud).
        if _USUARIO_POOLER.fullmatch(s.user) is None:
            raise RuntimeError(
                "Para el Session pooler de Supabase, DB_USER debe ser "
                "bodega_api.<PROJECT_REF> (nunca postgres)."
            )
        # 6543 es el Transaction pooler: no conserva la sesión y es
        # incompatible con los prepared statements de psycopg.
        if s.port != PUERTO_SESSION_POOLER:
            raise RuntimeError("La API requiere el Session pooler de Supabase (puerto 5432).")
    elif s.user != ROL_API:
        raise RuntimeError("La API debe conectarse con el rol bodega_api (nunca postgres).")
    if not s.password:
        raise RuntimeError("Falta DB_PASSWORD (en .env local o en las variables del proveedor).")
    if s.pool_min < 1 or s.pool_max < s.pool_min:
        raise RuntimeError("Rango inválido para DB_POOL_MIN y DB_POOL_MAX.")
    # connect_timeout es entero por libpq; el pool admite fracciones de segundo.
    if s.connect_timeout < 1:
        raise RuntimeError("DB_CONNECT_TIMEOUT debe ser un entero mayor o igual que 1.")
    if s.pool_timeout <= 0:
        raise RuntimeError("DB_POOL_TIMEOUT debe ser mayor que 0.")
    if s.sslmode not in SSLMODES_ADMITIDOS:
        raise RuntimeError(f"DB_SSLMODE debe ser uno de: {', '.join(SSLMODES_ADMITIDOS)}.")
    # Fuera de la propia PC, la conexión debe ir cifrada sí o sí.
    if not es_host_local(s.host) and not s.requiere_tls:
        raise RuntimeError(
            "Para conexiones remotas DB_SSLMODE debe ser require, verify-ca o verify-full."
        )
    if s.sslmode in ("verify-ca", "verify-full") and not s.sslrootcert:
        raise RuntimeError(
            "DB_SSLMODE=verify-ca/verify-full necesita DB_SSLROOTCERT "
            "(ruta al certificado raíz del proveedor)."
        )
    return s
