
/**
 * Tipos del modulo de ventas.
 * Basados en los schemas reales de FastAPI.
 */

export type DecimalApi = string | number

export interface ClienteVenta {
  id_cliente: number
  nombre_razon_social: string
}

export interface VinoVenta {
  cod_vino: number
  nombre: string
  precio: DecimalApi
}

export interface SalaVenta {
  id_sala: number
  calle: string
  numero: string
  localidad: string
}

export interface PaginaApi<T> {
  items: T[]
  total: number
  pagina: number
  tamanio: number
}

export interface RenglonVentaCrear {
  cod_vino: number
  cantidad: number
}

export interface ComprobanteCrear {
  id_cliente: number
  id_sala: number
  renglones: RenglonVentaCrear[]
}

export interface RenglonComprobanteRespuesta {
  cod_vino: number
  cantidad: number
  precio_unitario: DecimalApi
  descuento: DecimalApi
  subtotal: DecimalApi
}

export interface ComprobanteRespuesta {
  nro_comprobante: number
  fecha: string
  id_cliente: number
  id_sala: number
  subtotal: DecimalApi
  descuento: DecimalApi
  total: DecimalApi
  renglones: RenglonComprobanteRespuesta[]
}
