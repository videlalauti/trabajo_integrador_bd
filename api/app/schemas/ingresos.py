"""Schemas de ingresos (Pydantic, sin ORM).

Solo validan TIPOS. Las reglas de negocio (cantidad > 0, estados, FK,
renglones permitidos) las decide PostgreSQL: CHECK, FK, triggers RN-10/RN-12
y procedimientos sp_terminar_ingreso / sp_procesar_ingreso.
"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

EstadoDocumento = Literal["en_confeccion", "terminado", "procesado"]


class IngresoCrear(BaseModel):
    cod_transporte: int = Field(description="Transportista que efectua el traslado")
    cuit_bodega: str = Field(description="CUIT de la bodega de origen (11 digitos, lo valida el dominio cuit_dom)")
    fecha: date | None = Field(
        default=None,
        description="Fecha del ingreso. Si se omite, la base usa CURRENT_DATE.",
    )


class RenglonIngresoCrear(BaseModel):
    cod_vino: int
    cantidad: int = Field(description="Botellas; la base exige cantidad > 0 (CHECK)")


class RenglonIngreso(BaseModel):
    cod_vino: int
    vino: str
    volumen_ml: int
    cantidad: int
    stock_deposito: int = Field(description="Stock actual del vino en el deposito central (leido de la base)")


class IngresoDetalle(BaseModel):
    cod_ingreso: int
    fecha: date
    estado: EstadoDocumento
    cod_transporte: int
    transportista: str
    cuit_bodega: str
    bodega: str
    renglones: list[RenglonIngreso]
