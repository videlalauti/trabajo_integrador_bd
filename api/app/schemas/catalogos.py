
"""Schemas de los catálogos auxiliares del frontend."""

from decimal import Decimal

from pydantic import BaseModel


class BodegaSalida(BaseModel):
    cuit: str
    razon_social: str


class CepaSalida(BaseModel):
    id_cepa: int
    nombre: str
    tipo: str


class MaridajeSalida(BaseModel):
    id_maridaje: int
    nombre: str
    temperatura_servicio_c: Decimal
