#!/usr/bin/env python3
"""Comprueba una API PUBLICA ya desplegada. Solo GET, nunca modifica datos."""
import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def validar_base(url: str) -> str:
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ("", "/"):
        raise ValueError("Se requiere una URL base HTTPS sin credenciales, query ni fragmento")
    return url.rstrip("/")


def solicitar(url: str, timeout: int):
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "bodegas-fase8-auditoria/1.0"})
    with urlopen(request, timeout=timeout) as r:
        status = r.status
        content_type = r.headers.get("Content-Type", "")
        body = r.read(200000)
    return status, content_type, json.loads(body.decode("utf-8"))


def ejecutar(base: str, timeout: int, intentos: int, pausa: float):
    ultima = ""
    for n in range(1, intentos + 1):
        try:
            status, content_type, payload = solicitar(base + "/salud", timeout)
            if status != 200:
                raise ValueError(f"HTTP {status}")
            if not isinstance(payload, dict) or payload.get("estado") != "ok" or payload.get("base_datos") != "conectada":
                raise ValueError("JSON de /salud no acredita DB conectada")
            return {"api": base, "endpoint": "/salud", "status": "OK", "http": status, "intento": n}
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            ultima = f"{type(exc).__name__}: {exc}"
            if n < intentos:
                time.sleep(pausa)
    raise RuntimeError(f"/salud no pasó tras {intentos} intentos; último error: {ultima}")


def main():
    a = argparse.ArgumentParser(description="Comprueba GET /salud HTTPS de FastAPI; sin cambiar datos")
    a.add_argument("--api-url", required=True, help="URL base HTTPS, sin secretos")
    a.add_argument("--timeout", type=int, default=25)
    a.add_argument("--intentos", type=int, default=3)
    a.add_argument("--pausa", type=float, default=8.0)
    args = a.parse_args()
    try:
        if not (1 <= args.intentos <= 5 and 1 <= args.timeout <= 120 and 0 <= args.pausa <= 120):
            raise ValueError("Argumentos de reintentos/tiempo fuera de rango")
        print(json.dumps(ejecutar(validar_base(args.api_url), args.timeout, args.intentos, args.pausa), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"NO APROBADO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
