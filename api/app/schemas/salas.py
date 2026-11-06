
"""Schemas de respuesta para el catálogo de salas de venta."""

from pydantic import BaseModel


class SalaSalida(BaseModel):
    id_sala: int
    calle: str
    numero: str
    localidad: str
