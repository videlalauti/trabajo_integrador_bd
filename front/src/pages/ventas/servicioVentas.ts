
/**
 * Servicio HTTP del modulo de ventas.
 *
 * Todas las solicitudes utilizan el cliente compartido
 * de Valentino. No se calculan importes ni stock.
 */

import { solicitarApi } from '../../lib/api'

import type {
  ClienteVenta,
  VinoVenta,
  SalaVenta,
  PaginaApi,
  ComprobanteCrear,
  ComprobanteRespuesta,
} from './tipos'

// Consultar clientes reales, con paginacion.
export function listarClientes(
  pagina = 1,
  tamanio = 20,
): Promise<PaginaApi<ClienteVenta>> {
  const parametros = new URLSearchParams({
    page: String(pagina),
    page_size: String(tamanio),
  })

  return solicitarApi<PaginaApi<ClienteVenta>>(
    `/clientes?${parametros.toString()}`,
  )
}

// Consultar vinos reales, con paginacion.
export function listarVinos(
  pagina = 1,
  tamanio = 20,
): Promise<PaginaApi<VinoVenta>> {
  const parametros = new URLSearchParams({
    page: String(pagina),
    page_size: String(tamanio),
  })

  return solicitarApi<PaginaApi<VinoVenta>>(
    `/vinos?${parametros.toString()}`,
  )
}

// Obtener las salas de venta desde PostgreSQL.
export function listarSalas(): Promise<SalaVenta[]> {
  return solicitarApi<SalaVenta[]>('/salas')
}

// Registrar una venta mediante FastAPI.
export function registrarVenta(
  datos: ComprobanteCrear,
): Promise<ComprobanteRespuesta> {
  return solicitarApi<ComprobanteRespuesta>(
    '/comprobantes',
    {
      method: 'POST',
      body: JSON.stringify(datos),
    },
  )
}

// Consultar un comprobante ya registrado.
export function consultarComprobante(
  nroComprobante: number,
): Promise<ComprobanteRespuesta> {
  return solicitarApi<ComprobanteRespuesta>(
    `/comprobantes/${nroComprobante}`,
  )
}
