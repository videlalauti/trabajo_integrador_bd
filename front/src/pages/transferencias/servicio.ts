// Llamadas a la API de transferencias.
// Usan exclusivamente el cliente compartido solicitarApi (proxy /api de Vite).
// Los cambios de estado y de stock los realiza PostgreSQL a traves de FastAPI:
// estas funciones solo envian la solicitud y devuelven la respuesta real.

import { solicitarApi } from '../../lib/api'
import type {
  Bodega,
  FiltrosVinos,
  RenglonTransferenciaCrear,
  Sala,
  TransferenciaCrear,
  TransferenciaDetalle,
  VinosPaginados,
} from './tipos'

const BASE = '/transferencias'

// GET /transferencias/{nro_solicitud}
export function obtenerTransferencia(
  nroSolicitud: number,
): Promise<TransferenciaDetalle> {
  return solicitarApi<TransferenciaDetalle>(`${BASE}/${nroSolicitud}`)
}

// POST /transferencias
export function crearTransferencia(
  datos: TransferenciaCrear,
): Promise<TransferenciaDetalle> {
  return solicitarApi<TransferenciaDetalle>(BASE, {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

// POST /transferencias/{nro_solicitud}/renglones
export function agregarRenglon(
  nroSolicitud: number,
  datos: RenglonTransferenciaCrear,
): Promise<TransferenciaDetalle> {
  return solicitarApi<TransferenciaDetalle>(
    `${BASE}/${nroSolicitud}/renglones`,
    {
      method: 'POST',
      body: JSON.stringify(datos),
    },
  )
}

// POST /transferencias/{nro_solicitud}/terminar  (sp_terminar_transferencia)
export function terminarTransferencia(
  nroSolicitud: number,
): Promise<TransferenciaDetalle> {
  return solicitarApi<TransferenciaDetalle>(
    `${BASE}/${nroSolicitud}/terminar`,
    { method: 'POST' },
  )
}

// POST /transferencias/{nro_solicitud}/procesar  (sp_procesar_transferencia)
export function procesarTransferencia(
  nroSolicitud: number,
): Promise<TransferenciaDetalle> {
  return solicitarApi<TransferenciaDetalle>(
    `${BASE}/${nroSolicitud}/procesar`,
    { method: 'POST' },
  )
}

// ---------------------------------------------------------------------
// Catalogos de solo lectura (autorizados por coordinacion).
// ---------------------------------------------------------------------

// GET /salas  (endpoint compartido de infraestructura)
export function listarSalas(): Promise<Sala[]> {
  return solicitarApi<Sala[]>('/salas')
}

// GET /bodegas  (catalogo compartido de infraestructura)
export function listarBodegas(): Promise<Bodega[]> {
  return solicitarApi<Bodega[]>('/bodegas')
}

// GET /vinos  (modulo de Lautaro, solo lectura)
export function listarVinos(filtros: FiltrosVinos = {}): Promise<VinosPaginados> {
  const parametros = new URLSearchParams()
  if (filtros.page !== undefined) parametros.set('page', String(filtros.page))
  if (filtros.page_size !== undefined) parametros.set('page_size', String(filtros.page_size))
  if (filtros.tipo !== undefined) parametros.set('tipo', filtros.tipo)
  if (filtros.bodega !== undefined) parametros.set('bodega', filtros.bodega)
  if (filtros.anada !== undefined) parametros.set('anada', String(filtros.anada))
  const consulta = parametros.toString()
  return solicitarApi<VinosPaginados>(consulta ? `/vinos?${consulta}` : '/vinos')
}
