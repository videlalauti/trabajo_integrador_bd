// Formulario para agregar un renglon (vino y cantidad) a una transferencia
// en confeccion.
// - Bodegas: GET /bodegas. Vinos: GET /vinos (modulo de Lautaro, solo lectura),
//   filtrados por bodega (CUIT) y tipo, con paginacion.
// - En React solo se valida el formato de la cantidad (entero > 0).
//   El estado del documento (RN-12), la existencia del vino y el CHECK de
//   cantidad los controla PostgreSQL.

import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import MensajeError from './MensajeError'
import { agregarRenglon, listarBodegas, listarVinos } from './servicio'
import type { Bodega, TipoVino, TransferenciaDetalle, VinosPaginados } from './tipos'

type Props = {
  nroSolicitud: number
  onActualizada: (transferencia: TransferenciaDetalle) => void
}

const TIPOS: TipoVino[] = ['tinto', 'blanco', 'rosado', 'espumante']
const TAMANIO_PAGINA = 50

type CargaBodegas = { recarga: number } & ({ bodegas: Bodega[] } | { error: unknown })
type CargaVinos = { clave: string; datos?: VinosPaginados; error?: unknown }

export default function FormRenglon({ nroSolicitud, onActualizada }: Props) {
  const [bodegasGuardadas, setCargaBodegas] = useState<CargaBodegas | null>(null)
  // "Reintentar" incrementa este contador y vuelve a pedir bodegas y vinos.
  const [recarga, setRecarga] = useState(0)
  const [bodega, setBodega] = useState('')
  const [tipo, setTipo] = useState<TipoVino | ''>('')
  const [pagina, setPagina] = useState(1)
  const [cargaVinos, setCargaVinos] = useState<CargaVinos | null>(null)

  const [codVino, setCodVino] = useState('')
  const [cantidad, setCantidad] = useState('')
  const [aviso, setAviso] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [errorEnvio, setErrorEnvio] = useState<unknown>(null)

  useEffect(() => {
    let activo = true
    listarBodegas()
      .then((bodegas) => {
        if (activo) setCargaBodegas({ recarga, bodegas })
      })
      .catch((error: unknown) => {
        if (activo) setCargaBodegas({ recarga, error })
      })
    return () => {
      activo = false
    }
  }, [recarga])

  const cargaBodegas =
    bodegasGuardadas !== null && bodegasGuardadas.recarga === recarga ? bodegasGuardadas : null

  // Clave de la consulta actual de vinos: si cambia, se vuelve a consultar.
  const claveVinos = `${bodega}|${tipo}|${pagina}|${recarga}`

  useEffect(() => {
    let activo = true
    listarVinos({
      page: pagina,
      page_size: TAMANIO_PAGINA,
      bodega: bodega === '' ? undefined : bodega,
      tipo: tipo === '' ? undefined : tipo,
    })
      .then((datos) => {
        if (activo) setCargaVinos({ clave: claveVinos, datos })
      })
      .catch((error: unknown) => {
        if (activo) setCargaVinos({ clave: claveVinos, error })
      })
    return () => {
      activo = false
    }
  }, [bodega, tipo, pagina, recarga, claveVinos])

  const vinosActuales = cargaVinos !== null && cargaVinos.clave === claveVinos ? cargaVinos : null
  const cargandoVinos = vinosActuales === null
  const totalPaginas = vinosActuales?.datos
    ? Math.max(1, Math.ceil(vinosActuales.datos.total / vinosActuales.datos.tamanio))
    : 1

  // Al cambiar un filtro se vuelve a la primera pagina y se limpia la eleccion.
  function cambiarBodega(valor: string) {
    setBodega(valor)
    setPagina(1)
    setCodVino('')
  }

  function cambiarTipo(valor: TipoVino | '') {
    setTipo(valor)
    setPagina(1)
    setCodVino('')
  }

  function cambiarPagina(nueva: number) {
    setPagina(nueva)
    setCodVino('')
  }

  async function agregar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    // Cada intento empieza limpio: no se muestran avisos ni errores de un
    // intento anterior junto con el resultado del actual.
    setAviso(null)
    setErrorEnvio(null)
    const valorCantidad = Number(cantidad)
    if (codVino === '') {
      setAviso('Elegí el vino que se solicita.')
      return
    }
    if (cantidad.trim() === '' || !Number.isInteger(valorCantidad) || valorCantidad <= 0) {
      setAviso('La cantidad debe ser un número entero mayor que 0.')
      return
    }
    setEnviando(true)
    try {
      const transferencia = await agregarRenglon(nroSolicitud, {
        cod_vino: Number(codVino),
        cantidad: valorCantidad,
      })
      setCodVino('')
      setCantidad('')
      onActualizada(transferencia)
    } catch (error: unknown) {
      setErrorEnvio(error)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section aria-label="Agregar renglón">
      <h4>Agregar un vino</h4>

      <div>
        <label htmlFor="filtro-bodega">Bodega </label>
        {cargaBodegas === null && <span role="status">Cargando bodegas…</span>}
        {cargaBodegas !== null && 'error' in cargaBodegas && (
          <MensajeError error={cargaBodegas.error} />
        )}
        {cargaBodegas !== null && 'bodegas' in cargaBodegas && (
          <select
            id="filtro-bodega"
            value={bodega}
            onChange={(evento) => cambiarBodega(evento.target.value)}
            disabled={enviando}
          >
            <option value="">Todas</option>
            {cargaBodegas.bodegas.map((item) => (
              <option key={item.cuit} value={item.cuit}>
                {item.razon_social}
              </option>
            ))}
          </select>
        )}{' '}
        <label htmlFor="filtro-tipo">Tipo </label>
        <select
          id="filtro-tipo"
          value={tipo}
          onChange={(evento) => cambiarTipo(evento.target.value as TipoVino | '')}
          disabled={enviando}
        >
          <option value="">Todos</option>
          {TIPOS.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>

      {cargandoVinos && <p role="status">Cargando vinos…</p>}
      {vinosActuales?.error !== undefined && <MensajeError error={vinosActuales.error} />}
      {((cargaBodegas !== null && 'error' in cargaBodegas) ||
        vinosActuales?.error !== undefined) && (
        <button type="button" onClick={() => setRecarga((anterior) => anterior + 1)}>
          Reintentar
        </button>
      )}

      {vinosActuales?.datos && (
        <form onSubmit={agregar} noValidate>
          <p>
            {vinosActuales.datos.total} vinos · página {vinosActuales.datos.pagina} de{' '}
            {totalPaginas}{' '}
            <button
              type="button"
              onClick={() => cambiarPagina(pagina - 1)}
              disabled={pagina <= 1 || enviando}
            >
              Anterior
            </button>{' '}
            <button
              type="button"
              onClick={() => cambiarPagina(pagina + 1)}
              disabled={pagina >= totalPaginas || enviando}
            >
              Siguiente
            </button>
          </p>

          <label htmlFor="vino-renglon">Vino </label>
          <select
            id="vino-renglon"
            value={codVino}
            onChange={(evento) => setCodVino(evento.target.value)}
            disabled={enviando}
          >
            <option value="">— Elegí un vino —</option>
            {vinosActuales.datos.items.map((vino) => (
              <option key={vino.cod_vino} value={String(vino.cod_vino)}>
                {vino.cod_vino} — {vino.nombre} {vino.anada}, {vino.volumen_ml} ml ({vino.tipo})
              </option>
            ))}
          </select>{' '}
          <label htmlFor="cantidad-renglon">Cantidad </label>
          <input
            id="cantidad-renglon"
            type="number"
            min={1}
            step={1}
            value={cantidad}
            onChange={(evento) => setCantidad(evento.target.value)}
            disabled={enviando}
            style={{ width: '7em' }}
          />{' '}
          <button type="submit" disabled={enviando}>
            {enviando ? 'Agregando…' : 'Agregar renglón'}
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
