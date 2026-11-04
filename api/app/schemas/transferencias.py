"""Schemas de transferencias (Pydantic, sin ORM).

La fecha de confeccion NO se recibe: la fija el trigger trg_transferencia_fecha
(RN-11). Cantidades, estados y stock los controla PostgreSQL.
"""
from datetime import date

from pydantic import BaseModel, Field

from app.schemas.ingresos import EstadoDocumento


class TransferenciaCrear(BaseModel):
    id_sala: int = Field(description="Sala que solicita los vinos al deposito central")


class RenglonTransferenciaCrear(BaseModel):
    cod_vino: int
    cantidad: int = Field(description="Botellas; la base exige cantidad > 0 (CHECK)")


class RenglonTransferencia(BaseModel):
    cod_vino: int
    vino: str
    volumen_ml: int
    cantidad: int
    stock_deposito: int = Field(description="Stock actual en el deposito central (leido de la base)")
    stock_sala: int = Field(description="Stock actual en la sala solicitante (leido de la base)")


class TransferenciaDetalle(BaseModel):
    nro_solicitud: int
    fecha_confeccion: date
    estado: EstadoDocumento
    id_sala: int
    sala: str
    localidad: str
    renglones: list[RenglonTransferencia]
