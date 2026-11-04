from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ClienteEntrada(BaseModel):
    """Datos para crear o actualizar un cliente."""

    nombre_razon_social: str = Field(min_length=1, max_length=150)
    tipo_doc: str = Field(min_length=1, max_length=15)
    nro_doc: str = Field(min_length=1, max_length=30)
    direccion: str = Field(min_length=1, max_length=200)
    fecha_alta: date
    id_localidad: int = Field(gt=0)

    tipo_cliente: Literal[
        "socio",
        "distribuidor",
        "exportador",
    ]

    descuento_especial: Decimal | None = None
    zona_cobertura: str | None = Field(default=None, max_length=150)
    nro_habilitacion: str | None = Field(default=None, max_length=50)
    pais_destino: str | None = Field(default=None, max_length=100)


class ClienteSalida(ClienteEntrada):
    """Cliente obtenido desde PostgreSQL."""

    id_cliente: int


class ListadoClientes(BaseModel):
    """Listado con la paginacion del contrato compartido."""

    items: list[ClienteSalida]
    total: int
    pagina: int
    tamanio: int
