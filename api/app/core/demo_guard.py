"""Guardian de un *servicio aparte* para ensayar RN-09/RN-11.

NO importar/registrar este middleware en app.main de produccion.
La base FULL del proyecto queda prohibida incluso si se intenta utilizar
FASE8_DEMO_MODE=aislado y un token valido.
"""

import hmac
import os
import re

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Referencia publica del proyecto ya aprobado (no es una credencial).
PROYECTO_FULL_PROHIBIDO = "sjfyocokehaubuwwbhnw"
_HOSTS_LOCALES = frozenset({"127.0.0.1", "localhost", "::1", "db", "postgres"})
_REF = re.compile(r"[a-z0-9]{20}")
_NUM = r"[1-9][0-9]*"
_LECTURAS_AUTENTICADAS = frozenset({
    "/vinos", "/bodegas", "/cepas", "/maridajes", "/salas",
    "/clientes", "/reportes/top-vinos",
    "/demo/identidad", "/demo/candidatos", "/demo/estado",
})
_ESCRITURAS_AUTENTICADAS = frozenset({"/comprobantes", "/transferencias"})
_RE_VINO = re.compile(rf"/vinos/{_NUM}")
_RE_CLIENTE = re.compile(rf"/clientes/{_NUM}")
_RE_COMPROBANTE = re.compile(rf"/comprobantes/{_NUM}")
_RE_TRANSFERENCIA = re.compile(rf"/transferencias/{_NUM}")
_RE_PASO_TRANSFERENCIA = re.compile(
    rf"/transferencias/{_NUM}/(?:renglones|terminar|procesar)"
)


class ConfiguracionDemoInsegura(RuntimeError):
    """Fail-closed: nunca abrir conexiones de demo con parametros ambiguos."""


def validar_configuracion_demo() -> None:
    """No imprime ni devuelve secretos; validar antes de crear el pool."""
    if os.getenv("FASE8_DEMO_MODE", "") != "aislado":
        raise ConfiguracionDemoInsegura("FASE8_DEMO_MODE debe ser aislado")

    if len(os.getenv("FASE8_DEMO_TOKEN", "")) < 48:
        raise ConfiguracionDemoInsegura("Falta token largo exclusivo de demostracion")

    host = os.getenv("DB_HOST", "").strip().lower()
    user = os.getenv("DB_USER", "").strip()
    name = os.getenv("DB_NAME", "").strip()
    if not os.getenv("DB_PASSWORD", ""):
        raise ConfiguracionDemoInsegura("Falta credencial de base de ensayo")

    if host in _HOSTS_LOCALES:
        if (os.getenv("FASE8_DEMO_LOCAL", "") != "1"
                or name != "bodegas_fase8_demo_local"
                or user != "bodega_api"):
            raise ConfiguracionDemoInsegura("Base local de demostracion no identificada")
        return

    # La produccion y cualquier base no identificada quedan prohibidas.
    ref = os.getenv("FASE8_DEMO_PROJECT_REF", "").strip()
    if not _REF.fullmatch(ref) or ref == PROYECTO_FULL_PROHIBIDO:
        raise ConfiguracionDemoInsegura("Referencia de proyecto de ensayo invalida")
    if not host.endswith(".pooler.supabase.com"):
        raise ConfiguracionDemoInsegura("Se exige Session Pooler Supabase de ensayo")
    if user != f"bodega_api.{ref}" or name != "postgres":
        raise ConfiguracionDemoInsegura("Usuario o base no corresponde al proyecto de ensayo")
    if (os.getenv("DB_PORT") != "5432"
            or os.getenv("DB_SSLMODE", "").lower() != "verify-full"
            or not os.getenv("DB_SSLROOTCERT", "")):
        raise ConfiguracionDemoInsegura("Se exige Session Pooler 5432 con TLS verify-full")
    if os.getenv("FASE8_DEMO_LOCAL", "") == "1":
        raise ConfiguracionDemoInsegura("Modo local no admitido para host remoto")


def _bearer_valido(authorization: str, esperado: str) -> bool:
    """Validacion constante en bytes; evita TypeError con caracteres no ASCII."""
    esquema, separador, recibido = authorization.partition(" ")
    return (
        separador == " "
        and esquema.lower() == "bearer"
        and hmac.compare_digest(
            recibido.strip().encode("utf-8"),
            esperado.encode("utf-8"),
        )
    )


def _permitido(metodo: str, ruta: str) -> bool:
    if metodo in ("GET", "HEAD"):
        return (ruta in _LECTURAS_AUTENTICADAS
                or bool(_RE_VINO.fullmatch(ruta))
                or bool(_RE_CLIENTE.fullmatch(ruta))
                or bool(_RE_COMPROBANTE.fullmatch(ruta))
                or bool(_RE_TRANSFERENCIA.fullmatch(ruta)))
    if metodo == "POST":
        return (ruta in _ESCRITURAS_AUTENTICADAS
                or bool(_RE_PASO_TRANSFERENCIA.fullmatch(ruta)))
    return False


class GuardianDemoAislada(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            validar_configuracion_demo()
        except ConfiguracionDemoInsegura:
            return JSONResponse(status_code=503,
                                content={"error": {"codigo": "DEMO_NO_CONFIGURADA"}},
                                headers={"Cache-Control": "no-store"})

        metodo, ruta = request.method.upper(), request.url.path
        if ruta == "/salud" and metodo in ("GET", "HEAD"):
            return await call_next(request)
        if not _permitido(metodo, ruta):
            return JSONResponse(status_code=403,
                                content={"error": {"codigo": "RUTA_DEMO_BLOQUEADA"}},
                                headers={"Cache-Control": "no-store"})

        authorization = request.headers.get("authorization", "")
        esperado = os.environ["FASE8_DEMO_TOKEN"]
        if not _bearer_valido(authorization, esperado):
            return JSONResponse(status_code=401,
                                content={"error": {"codigo": "DEMO_NO_AUTORIZADA"}},
                                headers={"WWW-Authenticate": "Bearer",
                                         "Cache-Control": "no-store"})

        resp = await call_next(request)
        resp.headers["Cache-Control"] = "no-store"
        return resp
