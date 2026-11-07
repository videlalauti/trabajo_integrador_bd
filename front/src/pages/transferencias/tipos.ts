// Tipos del modulo de transferencias.
// Derivados campo por campo de api/app/schemas/transferencias.py (FastAPI).
// No agregar campos ni estados que el backend no devuelve.

// Estados del ENUM estado_documento de PostgreSQL (RN-10 / RN-11).
export type EstadoTransferencia = 'en_confeccion' | 'terminado' | 'procesado'

// Texto para mostrar en pantalla. Solo presentacion: la base decide los estados.
export const ETIQUETAS_ESTADO: Record<EstadoTransferencia, string> = {
  en_confeccion: 'En confección',
  terminado: 'Terminada',
  procesado: 'Procesada',
}

// RenglonTransferencia (respuesta)
export type RenglonTransferencia = {
  cod_vino: number
  vino: string
  volumen_ml: number
  cantidad: number
  // Stock actual leido de PostgreSQL en cada respuesta. No se calcula en React.
  stock_deposito: number
  stock_sala: number
}

// TransferenciaDetalle (respuesta de los cinco endpoints)
export type TransferenciaDetalle = {
  nro_solicitud: number
  // Fecha ISO (YYYY-MM-DD). La fija el trigger de la base (RN-11).
  fecha_confeccion: string
  estado: EstadoTransferencia
  id_sala: number
  sala: string
  localidad: string
  renglones: RenglonTransferencia[]
}

// TransferenciaCrear (cuerpo de POST /transferencias). No lleva fecha.
export type TransferenciaCrear = {
  id_sala: number
}

// RenglonTransferenciaCrear (cuerpo de POST /transferencias/{nro}/renglones)
export type RenglonTransferenciaCrear = {
  cod_vino: number
  cantidad: number
}

// ---------------------------------------------------------------------
// Catalogos de solo lectura usados por los selectores de esta pantalla.
// ---------------------------------------------------------------------

// GET /salas  (api/app/schemas/salas.py: SalaSalida)
export type Sala = {
  id_sala: number
  calle: string
  numero: string
  localidad: string
}

// GET /bodegas  (api/app/schemas/catalogos.py: BodegaSalida)
export type Bodega = {
  cuit: string
  razon_social: string
}

// Tipos de vino (api/app/schemas/vinos.py: TipoVino)
export type TipoVino = 'tinto' | 'blanco' | 'rosado' | 'espumante'

// GET /vinos  (api/app/schemas/vinos.py: VinoResumen y VinosPaginados)
// precio y graduacion son Decimal en FastAPI: llegan como texto en el JSON.
export type VinoResumen = {
  cod_vino: number
  nombre: string
  tipo: TipoVino
  anada: number
  volumen_ml: number
  graduacion: string
  precio: string
  cuit_bodega: string
}

export type VinosPaginados = {
  items: VinoResumen[]
  total: number
  pagina: number
  tamanio: number
}

// Filtros admitidos por GET /vinos (bodega = CUIT de la bodega).
export type FiltrosVinos = {
  page?: number
  page_size?: number
  tipo?: TipoVino
  bodega?: string
  anada?: number
}
