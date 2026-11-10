"""Contención temporal del despliegue de lectura de Fase 8.

Con DB_HOST remoto se aplica una lista positiva de GET/HEAD públicos.
Todos los demás métodos y endpoints se bloquean antes del router/BD.
Esta medida NO sustituye autenticación ni autorización por usuario.
"""
import os
import re

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_HOSTS_LOCALES = frozenset({"127.0.0.1", "localhost", "::1", "db", "postgres"})
_METODOS_DE_LECTURA = frozenset({"GET", "HEAD"})
# Rutas públicas revisadas para la demostración inicial. Evitar exponer PII
# (clientes/comprobantes) y operaciones de inventario o trazabilidad internas.
_RUTAS_PUBLICAS = frozenset({
    "/salud", "/vinos", "/salas", "/bodegas", "/cepas", "/maridajes",
    "/reportes/top-vinos",
})
_RUTA_VINO = re.compile(r"/vinos/[1-9][0-9]*")


def _get_publico(ruta: str) -> bool:
    return ruta in _RUTAS_PUBLICAS or _RUTA_VINO.fullmatch(ruta) is not None


class BloqueoEscriturasNube(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = os.getenv("DB_HOST", "127.0.0.1").strip().lower()
        if host in _HOSTS_LOCALES:
            # Mantiene el funcionamiento local de Fases 6 y 7.
            return await call_next(request)

        metodo = request.method.upper()
        ruta = request.url.path
        if metodo == "OPTIONS":
            # El preflight no llega a un handler mutante. No es autorización.
            return await call_next(request)
        if metodo in _METODOS_DE_LECTURA and _get_publico(ruta):
            return await call_next(request)

        if metodo not in _METODOS_DE_LECTURA:
            codigo = "ESCRITURA_NUBE_BLOQUEADA"
            mensaje = "Las operaciones de escritura estan deshabilitadas en el despliegue publico inicial."
        else:
            codigo = "LECTURA_NO_PUBLICA"
            mensaje = "Esta consulta no esta habilitada para acceso publico."
        return JSONResponse(
            status_code=403,
            content={"error": {"codigo": codigo, "mensaje": mensaje}},
            headers={"Cache-Control": "no-store"},
        )
