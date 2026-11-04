"""Modelos de respuesta de los reportes de la API."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TopVino(BaseModel):
    """Vino dentro del ranking de ventas."""

    cod_vino: int
    vino: str
    tipo: str
    botellas_vendidas: int


class VentaPorSala(BaseModel):
    """Ventas monetarias de una sala."""

    id_sala: int
    calle: str
    numero: str
    total_ventas: Decimal


class VinoSinStock(BaseModel):
    """Vino sin stock en la sala y disponible en deposito."""

    cod_vino: int
    vino: str
    tipo: str
    anada: int
    volumen_ml: int
    stock_sala: int
    stock_deposito: int


class ListadoVinosSinStock(BaseModel):
    """Resultado paginado del reporte de stock."""

    items: list[VinoSinStock]
    total: int
    pagina: int
    tamanio: int


class TransportistaActivo(BaseModel):
    """Transportista con mayor cantidad de ingresos."""

    cod_transporte: int
    razon_social: str
    cantidad_ingresos: int


class VinoTrazabilidad(BaseModel):
    """Datos del vino y su bodega."""

    cod_vino: int
    nombre_vino: str
    tipo: str
    anada: int
    cuit_bodega: str
    nombre_bodega: str


class LoteBodega(BaseModel):
    """Lote registrado en la bodega del vino."""

    nro_lote: int
    campania: int
    fecha_cosecha: date
    kg_cosechados: Decimal
    id_finca: int
    nombre_finca: str
    nro_parcela: int
    superficie_parcela_ha: Decimal


class ReporteTrazabilidad(BaseModel):
    """Trazabilidad limitada a relaciones comprobables."""

    vino: VinoTrazabilidad
    lotes_registrados_en_bodega: list[LoteBodega]
    total_lotes_bodega: int
    pagina: int
    tamanio: int
    relacion_directa_vino_lote: bool
    aclaracion: str

