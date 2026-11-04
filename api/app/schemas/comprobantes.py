
"""Esquemas de entrada y salida para comprobantes."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RenglonComprobanteCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cod_vino: int = Field(gt=0, strict=True)
    cantidad: int = Field(gt=0, strict=True)


class ComprobanteCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_cliente: int = Field(gt=0, strict=True)
    id_sala: int = Field(gt=0, strict=True)
    renglones: list[RenglonComprobanteCrear] = Field(min_length=1)


class RenglonComprobanteRespuesta(BaseModel):
    cod_vino: int
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal
    subtotal: Decimal


class ComprobanteRespuesta(BaseModel):
    nro_comprobante: int
    fecha: datetime
    id_cliente: int
    id_sala: int
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    renglones: list[RenglonComprobanteRespuesta]
