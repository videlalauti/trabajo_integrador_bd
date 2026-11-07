// Botones de cambio de estado de una transferencia.
// Se habilitan segun el estado actual (solo experiencia de usuario):
//   en_confeccion -> Terminar   (sp_terminar_transferencia)
//   terminado     -> Procesar   (sp_procesar_transferencia)
//   procesado     -> sin acciones
// Las transiciones y el movimiento de stock los decide PostgreSQL. Si la API
// responde con un rechazo (400/404/409/422), la transaccion se revirtio y no
// hubo cambios. Ante cualquier otro error (por ejemplo, sin conexion) no se
// puede confirmar el resultado y se pide consultar la transferencia.

import { useState } from 'react'

import { ErrorApi } from '../../lib/api'
import MensajeError from './MensajeError'
import { procesarTransferencia, terminarTransferencia } from './servicio'
import type { TransferenciaDetalle } from './tipos'

type Props = {
  transferencia: TransferenciaDetalle
  onActualizada: (transferencia: TransferenciaDetalle) => void
}

type Accion = 'terminar' | 'procesar'

export default function AccionesTransferencia({ transferencia, onActualizada }: Props) {
  const [enCurso, setEnCurso] = useState<Accion | null>(null)
  const [error, setError] = useState<unknown>(null)

  const { nro_solicitud, estado } = transferencia

  async function ejecutar(accion: Accion) {
    if (
      accion === 'procesar' &&
      !window.confirm(
        `¿Procesar la transferencia ${nro_solicitud}? Se descontará del depósito central y se sumará al stock de la sala.`,
      )
    ) {
      return
    }
    setError(null)
    setEnCurso(accion)
    try {
      const actualizada =
        accion === 'terminar'
          ? await terminarTransferencia(nro_solicitud)
          : await procesarTransferencia(nro_solicitud)
      onActualizada(actualizada)
    } catch (excepcion: unknown) {
      setError(excepcion)
    } finally {
      setEnCurso(null)
    }
  }

  return (
    <section aria-label="Acciones de la transferencia">
      <h4>Acciones</h4>
      <button
        type="button"
        onClick={() => void ejecutar('terminar')}
        disabled={estado !== 'en_confeccion' || enCurso !== null}
      >
        {enCurso === 'terminar' ? 'Terminando…' : 'Terminar'}
      </button>{' '}
      <button
        type="button"
        onClick={() => void ejecutar('procesar')}
        disabled={estado !== 'terminado' || enCurso !== null}
      >
        {enCurso === 'procesar' ? 'Procesando…' : 'Procesar'}
      </button>
      {estado === 'procesado' && (
        <p>La transferencia ya fue procesada: el stock se movió del depósito central a la sala.</p>
      )}
      {error !== null && (
        <>
          <MensajeError error={error} />
          {error instanceof ErrorApi &&
          [400, 404, 409, 422].includes(error.status) ? (
            <p>
              La operación fue rechazada; no se aplicaron cambios.
            </p>
          ) : (
            <p>
              No se pudo confirmar el resultado de la operación.
              Consultá nuevamente la transferencia antes de reintentar.
            </p>
          )}
        </>
      )}
    </section>
  )
}
