
"""Modelos de entrada y salida para la API de vinos."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


TipoVino = Literal["tinto", "blanco", "rosado", "espumante"]


class VinoCepaEntrada(BaseModel):
    id_cepa: int = Field(gt=0)
    porcentaje: Decimal = Field(gt=0, le=100, max_digits=5, decimal_places=2)


class VinoCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    tipo: TipoVino
    anada: int
    volumen_ml: int = Field(gt=0)
    graduacion: Decimal = Field(ge=5, le=20, max_digits=4, decimal_places=2)
    precio: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    cuit_bodega: str = Field(pattern=r"^[0-9]{11}$")
    cepas: list[VinoCepaEntrada] = Field(min_length=1)
    maridajes: list[int] = Field(default_factory=list)


class VinoActualizar(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    tipo: TipoVino
    anada: int
    volumen_ml: int = Field(gt=0)
    graduacion: Decimal = Field(ge=5, le=20, max_digits=4, decimal_places=2)
    precio: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    cuit_bodega: str = Field(pattern=r"^[0-9]{11}$")
    cepas: list[VinoCepaEntrada] = Field(min_length=1)
    maridajes: list[int] = Field(default_factory=list)


class VinoResumen(BaseModel):
    cod_vino: int
    nombre: str
    tipo: TipoVino
    anada: int
    volumen_ml: int
    graduacion: Decimal
    precio: Decimal
    cuit_bodega: str


class VinosPaginados(BaseModel):
    items: list[VinoResumen]
    total: int
    pagina: int
    tamanio: int
