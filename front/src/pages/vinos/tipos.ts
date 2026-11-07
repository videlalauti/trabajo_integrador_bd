export type TipoVino = 'tinto' | 'blanco' | 'rosado' | 'espumante'
export interface VinoResumen {
  cod_vino: number
  nombre: string
  tipo: TipoVino
  anada: number
  volumen_ml: number
  graduacion: string
  precio: string
  cuit_bodega: string
}
export interface VinosPaginados { items: VinoResumen[]; total: number; pagina: number; tamanio: number }
export interface Bodega { cuit: string; razon_social: string }
export interface Cepa { id_cepa: number; nombre: string; tipo: string }
export interface Maridaje { id_maridaje: number; nombre: string; temperatura_servicio_c: string }
export interface VinoCepaDetalle {
  id_cepa: number
  nombre: string
  porcentaje: number
}
export interface VinoMaridajeDetalle {
  id_maridaje: number
  nombre: string
  temperatura_servicio_c: number
}
export interface VinoDetalle extends Omit<VinoResumen, 'graduacion' | 'precio'> {
  graduacion: number
  precio: number
  cepas: VinoCepaDetalle[]
  maridajes: VinoMaridajeDetalle[]
}
export interface VinoCepaEntrada { id_cepa: number; porcentaje: string }
export interface VinoFormulario {
  nombre: string
  tipo: TipoVino
  anada: number
  volumen_ml: number
  graduacion: string
  precio: string
  cuit_bodega: string
  cepas: VinoCepaEntrada[]
  maridajes: number[]
}
export interface VinoRespuestaOperacion { cod_vino: number; mensaje: string }
