// Formulario para crear una solicitud de transferencia.
// Las salas se obtienen de GET /salas (datos reales de PostgreSQL).
// Solo se envia id_sala: la fecha la fija la base (RN-11) y el estado
// nace en 'en_confeccion' por DEFAULT.

import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import MensajeError from './MensajeError'
import { crearTransferencia, listarSalas } from './servicio'
import type { Sala, TransferenciaDetalle } from './tipos'

type Props = {
  onCreada: (transferencia: TransferenciaDetalle) => void
}

type CargaSalas = { recarga: number } & ({ salas: Sala[] } | { error: unknown })

export default function FormNuevaTransferencia({ onCreada }: Props) {
  const [cargaGuardada, setCarga] = useState<CargaSalas | null>(null)
  // "Reintentar" incrementa este contador y vuelve a pedir las salas.
  const [recarga, setRecarga] = useState(0)
  const [idSala, setIdSala] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [errorEnvio, setErrorEnvio] = useState<unknown>(null)
  const [aviso, setAviso] = useState<string | null>(null)

  useEffect(() => {
    let activo = true
    listarSalas()
      .then((salas) => {
        if (activo) setCarga({ recarga, salas })
      })
      .catch((error: unknown) => {
        if (activo) setCarga({ recarga, error })
      })
    return () => {
      activo = false
    }
  }, [recarga])

  // Solo se muestra la carga que corresponde al intento actual.
  const carga = cargaGuardada !== null && cargaGuardada.recarga === recarga ? cargaGuardada : null

  async function crear(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    // Cada intento empieza limpio: sin avisos ni errores del intento anterior.
    setAviso(null)
    setErrorEnvio(null)
    if (idSala === '') {
      setAviso('Elegí la sala que solicita los vinos.')
      return
    }
    setEnviando(true)
    try {
      const transferencia = await crearTransferencia({ id_sala: Number(idSala) })
      setIdSala('')
      onCreada(transferencia)
    } catch (error: unknown) {
      setErrorEnvio(error)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section aria-label="Nueva transferencia">
      <h3>Nueva transferencia</h3>

      {carga === null && <p role="status">Cargando salas…</p>}
      {carga !== null && 'error' in carga && (
        <>
          <MensajeError error={carga.error} />
          <button type="button" onClick={() => setRecarga((anterior) => anterior + 1)}>
            Reintentar
          </button>
        </>
      )}

      {carga !== null && 'salas' in carga && (
        <form onSubmit={crear} noValidate>
          <label htmlFor="sala-solicitante">Sala solicitante </label>
          <select
            id="sala-solicitante"
            value={idSala}
            onChange={(evento) => setIdSala(evento.target.value)}
            disabled={enviando}
          >
            <option value="">— Elegí una sala —</option>
            {carga.salas.map((sala) => (
              <option key={sala.id_sala} value={String(sala.id_sala)}>
                {sala.id_sala} — {sala.calle} {sala.numero} ({sala.localidad})
              </option>
            ))}
          </select>{' '}
          <button type="submit" disabled={enviando}>
            {enviando ? 'Creando…' : 'Crear transferencia'}
          </button>
        </form>
      )}

      {aviso && (
        <p role="alert" style={{ color: '#b54708' }}>
          {aviso}
        </p>
      )}
      {errorEnvio !== null && <MensajeError error={errorEnvio} />}
    </section>
  )
}
