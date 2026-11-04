"""Configuración compartida de los tests de la API."""

import asyncio
import sys


def pytest_asyncio_loop_factories(config, item):
    """Usar SelectorEventLoop en Windows para psycopg asíncrono."""
    if sys.platform == "win32":
        return {"selector": asyncio.SelectorEventLoop}

    return {"default": asyncio.new_event_loop}