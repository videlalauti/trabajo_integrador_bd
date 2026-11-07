// Pantalla de transferencias (Fase 7, Antonio).
// Componente exportado para que coordinacion lo registre en /transferencias.
// Funciones: crear una transferencia, consultarla por numero, agregar
// renglones y cambiar su estado (terminar / procesar). Cada respuesta de la
// API reemplaza el detalle mostrado: estado y stock son siempre los de la base.
// El numero consultado se refleja en la URL (?nro=N) sin modificar App.tsx.

import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'

import AccionesTransferencia from './AccionesTransferencia'
import DetalleTransferencia from './DetalleTransferencia'
import FormNuevaTransferencia from './FormNuevaTransferencia'
import FormRenglon from './FormRenglon'
import MensajeError from './MensajeError'
import { obtenerTransferencia } from './servicio'
import type { TransferenciaDetalle } from './tipos'

type Resultado = {
  nro: number
  intento: number
  transferencia?: TransferenciaDetalle
  error?: unknown
}

// Validacion de formato solamente: entero mayor que cero.
function aNumeroValido(texto: string | null): number | null {
  if (texto === null || texto.trim() === '') return null
  const valor = Number(texto)
  return Number.isInteger(valor) && valor > 0 ? valor : null
}

export default function TransferenciasPage() {
  const [parametros, setParametros] = useSearchParams()
  const nroEnUrl = parametros.get('nro')
  const nro = aNumeroValido(nroEnUrl)

  const [entrada, setEntrada] = useState(nroEnUrl ?? '')
  const [errorFormato, setErrorFormato] = useState<string | null>(null)
  const [resultado, setResultado] = useState<Resultado | null>(null)
  // Cada "Consultar" incrementa el intento: asi se vuelve a consultar aunque
  // el numero no cambie (por ejemplo, despues de un error de conexion).
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    if (nro === null) return
    let activo = true

    obtenerTransferencia(nro)
      .then((transferencia) => {
        if (activo) setResultado({ nro, intento, transferencia })
      })
      .catch((error: unknown) => {
        if (activo) setResultado({ nro, intento, error })
      })

    return () => {
      activo = false
    }
  }, [nro, intento])

  // El resultado solo se muestra si corresponde a la consulta actual
  // (numero de la URL e intento). Mientras tanto no queda ningun mensaje viejo.
  const actual =
    resultado !== null && resultado.nro === nro && resultado.intento === intento
      ? resultado
      : null
  const cargando = nro !== null && actual === null

  // Muestra una transferencia devuelta por la API (por ejemplo, recien creada)
  // y deja su numero en la URL.
  function mostrar(transferencia: TransferenciaDetalle) {
    const nroNuevo = transferencia.nro_solicitud
    setResultado({ nro: nroNuevo, intento, transferencia })
    setEntrada(String(nroNuevo))
    setErrorFormato(null)
    setParametros({ nro: String(nroNuevo) })
  }

  function buscar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const valor = aNumeroValido(entrada)
    if (valor === null) {
      setErrorFormato('Ingresá un número de solicitud entero mayor que 0.')
      return
    }
    setErrorFormato(null)
    setIntento((anterior) => anterior + 1)
    setParametros({ nro: String(valor) })
  }

  return (
    <main>
      <h2>Transferencias</h2>
      <p>Solicitudes de vinos del depósito central a las salas de venta.</p>

      <FormNuevaTransferencia onCreada={mostrar} />

      <section aria-label="Consultar transferencia">
        <h3>Consultar una transferencia</h3>
        <form onSubmit={buscar} noValidate>
          <label htmlFor="nro-solicitud">Número de solicitud </label>
          <input
            id="nro-solicitud"
            type="number"
            min={1}
            step={1}
            value={entrada}
            onChange={(evento) => setEntrada(evento.target.value)}
          />{' '}
          <button type="submit" disabled={cargando}>
            Consultar
          </button>
        </form>
        {errorFormato && (
          <p role="alert" style={{ color: '#b54708' }}>
            {errorFormato}
          </p>
        )}
        {nroEnUrl !== null && nro === null && !errorFormato && (
          <p role="alert" style={{ color: '#b54708' }}>
            El número indicado en la dirección no es válido.
          </p>
        )}
      </section>

      {cargando && <p role="status">Consultando la transferencia {nro}…</p>}
      {actual?.error !== undefined && <MensajeError error={actual.error} />}
      {actual?.transferencia && (
        <>
          <DetalleTransferencia transferencia={actual.transferencia} />
          {actual.transferencia.estado === 'en_confeccion' && (
            <FormRenglon
              key={`renglon-${actual.transferencia.nro_solicitud}`}
              nroSolicitud={actual.transferencia.nro_solicitud}
              onActualizada={mostrar}
            />
          )}
          <AccionesTransferencia
            key={`acciones-${actual.transferencia.nro_solicitud}`}
            transferencia={actual.transferencia}
            onActualizada={mostrar}
          />
        </>
      )}
    </main>
  )
}
