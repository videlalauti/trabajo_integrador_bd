import './TableroReportes.css'
import { useEffect, useState } from 'react'
import { ErrorApi, solicitarApi } from '../../lib/api'
import type {
  ListadoVinosSinStock,
  Sala,
  TopVino,
  VentaPorSala,
} from './tipos'

function mensajeError(error: unknown): string {
  if (error instanceof ErrorApi) {
    if (error.status === 0 || error.status === 502 || error.status === 504) {
      return 'No se pudo conectar con FastAPI. Verificá que el servidor esté funcionando.'
    }

    if (error.status === 404) {
      return error.message
    }

    if (error.status === 422) {
      return `Parámetros inválidos: ${error.message}`
    }

    return `Error ${error.status}: ${error.message}`
  }

  return 'Ocurrió un error inesperado al consultar el reporte.'
}

function formatearImporte(valor: string | number): string {
  const numero = Number(valor)

  if (!Number.isFinite(numero)) {
    return 'Importe no disponible'
  }

  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(numero)
}

export function TableroReportes() {
  const [ranking, setRanking] = useState<TopVino[]>([])
  const [ventas, setVentas] = useState<VentaPorSala[]>([])
  const [salas, setSalas] = useState<Sala[]>([])
  const [idSala, setIdSala] = useState<number | null>(null)

  const [stock, setStock] = useState<ListadoVinosSinStock | null>(null)
  const [pagina, setPagina] = useState(1)

  const [cargandoRanking, setCargandoRanking] = useState(true)
  const [cargandoVentas, setCargandoVentas] = useState(true)
  const [cargandoSalas, setCargandoSalas] = useState(true)
  const [cargandoStock, setCargandoStock] = useState(false)

  const [errorRanking, setErrorRanking] = useState('')
  const [errorVentas, setErrorVentas] = useState('')
  const [errorSalas, setErrorSalas] = useState('')
  const [errorStock, setErrorStock] = useState('')

  // Ranking: datos reales de FastAPI.
  useEffect(() => {
    let activo = true

    solicitarApi<TopVino[]>('/reportes/top-vinos')
      .then((datos) => {
        if (activo) setRanking(datos)
      })
      .catch((error: unknown) => {
        if (activo) setErrorRanking(mensajeError(error))
      })
      .finally(() => {
        if (activo) setCargandoRanking(false)
      })

    return () => {
      activo = false
    }
  }, [])

  // Ventas por sala: importes calculados por PostgreSQL.
  useEffect(() => {
    let activo = true

    solicitarApi<VentaPorSala[]>('/reportes/ventas-por-sala')
      .then((datos) => {
        if (activo) setVentas(datos)
      })
      .catch((error: unknown) => {
        if (activo) setErrorVentas(mensajeError(error))
      })
      .finally(() => {
        if (activo) setCargandoVentas(false)
      })

    return () => {
      activo = false
    }
  }, [])

  // Obtener salas reales, sin identificadores fijos.
  useEffect(() => {
    let activo = true

    solicitarApi<Sala[]>('/salas')
      .then((datos) => {
        if (!activo) return

        setSalas(datos)

        if (datos.length > 0) {
          setIdSala(datos[0].id_sala)
        }
      })
      .catch((error: unknown) => {
        if (activo) setErrorSalas(mensajeError(error))
      })
      .finally(() => {
        if (activo) setCargandoSalas(false)
      })

    return () => {
      activo = false
    }
  }, [])

  // Stock: depende de la sala elegida y de la pagina.
  useEffect(() => {
    if (idSala === null) return

    let activo = true

    const consultarStock = async () => {
      setCargandoStock(true)
      setErrorStock('')
      setStock(null)

      try {
        const datos = await solicitarApi<ListadoVinosSinStock>(
          `/reportes/vinos-sin-stock?id_sala=${idSala}&page=${pagina}&page_size=10`,
        )

        if (activo) setStock(datos)
      } catch (error: unknown) {
        if (activo) setErrorStock(mensajeError(error))
      } finally {
        if (activo) setCargandoStock(false)
      }
    }

    void consultarStock()

    return () => {
      activo = false
    }
  }, [idSala, pagina])

  const maxVentas = Math.max(
    1,
    ...ventas.map((sala) => Number(sala.total_ventas) || 0),
  )

  const totalPaginas = stock
    ? Math.max(1, Math.ceil(stock.total / stock.tamanio))
    : 1

  return (
    <main className="tablero-reportes">
      <header>
        <h1>Tablero de reportes</h1>
        <p>
          Información de ventas e inventario obtenida desde
          FastAPI y PostgreSQL.
        </p>
      </header>

      <section aria-labelledby="titulo-ranking">
        <h2 id="titulo-ranking">Vinos más vendidos</h2>

        {cargandoRanking && <p role="status">Cargando ranking...</p>}
        {errorRanking && <p role="alert">{errorRanking}</p>}

        {!cargandoRanking && !errorRanking && ranking.length === 0 && (
          <p>No se encontraron ventas para mostrar.</p>
        )}

        {!cargandoRanking && !errorRanking && ranking.length > 0 && (
          <table>
            <thead>
              <tr>
                <th scope="col">Posición</th>
                <th scope="col">Vino</th>
                <th scope="col">Tipo</th>
                <th scope="col">Botellas vendidas</th>
              </tr>
            </thead>
            <tbody>
              {ranking.map((vino, indice) => (
                <tr key={vino.cod_vino}>
                  <td>{indice + 1}</td>
                  <td>{vino.vino}</td>
                  <td>{vino.tipo}</td>
                  <td>{vino.botellas_vendidas.toLocaleString('es-AR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section aria-labelledby="titulo-ventas">
        <h2 id="titulo-ventas">Ventas por sala</h2>
        <p>Importes correspondientes al último trimestre.</p>

        {cargandoVentas && <p role="status">Cargando ventas...</p>}
        {errorVentas && <p role="alert">{errorVentas}</p>}

        {!cargandoVentas && !errorVentas && ventas.length === 0 && (
          <p>No hay ventas disponibles para el período.</p>
        )}

        {!cargandoVentas && !errorVentas && ventas.length > 0 && (
          <div aria-label="Gráfico de barras de ventas por sala">
            {ventas.map((sala) => (
              <div key={sala.id_sala} className="reporte-barra">
                <label htmlFor={`venta-sala-${sala.id_sala}`}>
                  Sala {sala.id_sala} — {sala.calle} {sala.numero}
                </label>

                <progress
                  id={`venta-sala-${sala.id_sala}`}
                  value={Math.max(0, Number(sala.total_ventas) || 0)}
                  max={maxVentas}
                />

                <strong>{formatearImporte(sala.total_ventas)}</strong>
              </div>
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="titulo-stock">
        <h2 id="titulo-stock">Vinos sin stock en sala</h2>
        <p>
          Vinos agotados en la sala seleccionada que aún tienen
          existencias en el depósito central.
        </p>

        {cargandoSalas && <p role="status">Cargando salas...</p>}
        {errorSalas && <p role="alert">{errorSalas}</p>}

        {!cargandoSalas && !errorSalas && salas.length === 0 && (
          <p>No hay salas disponibles.</p>
        )}

        {salas.length > 0 && (
          <>
            <label htmlFor="reporte-sala">Seleccionar sala: </label>
            <select
              id="reporte-sala"
              value={idSala ?? ''}
              onChange={(evento) => {
                setIdSala(Number(evento.target.value))
                setPagina(1)
              }}
            >
              {salas.map((sala) => (
                <option key={sala.id_sala} value={sala.id_sala}>
                  {sala.calle} {sala.numero} — {sala.localidad}
                </option>
              ))}
            </select>

            {cargandoStock && <p role="status">Consultando stock...</p>}
            {errorStock && <p role="alert">{errorStock}</p>}

            {!cargandoStock && !errorStock && stock && (
              <>
                <p>Total de vinos encontrados: {stock.total}</p>

                {stock.items.length === 0 ? (
                  <p>No se encontraron vinos sin stock para esta sala.</p>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">Vino</th>
                        <th scope="col">Tipo</th>
                        <th scope="col">Añada</th>
                        <th scope="col">Volumen</th>
                        <th scope="col">Stock sala</th>
                        <th scope="col">Stock depósito</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stock.items.map((vino) => (
                        <tr key={vino.cod_vino}>
                          <td>{vino.vino}</td>
                          <td>{vino.tipo}</td>
                          <td>{vino.anada}</td>
                          <td>{vino.volumen_ml} ml</td>
                          <td>{vino.stock_sala}</td>
                          <td>{vino.stock_deposito}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                <nav aria-label="Paginación del reporte de stock">
                  <button
                    type="button"
                    disabled={pagina <= 1}
                    onClick={() => setPagina((actual) => actual - 1)}
                  >
                    Anterior
                  </button>

                  <span>
                    Página {pagina} de {totalPaginas}
                  </span>

                  <button
                    type="button"
                    disabled={pagina >= totalPaginas}
                    onClick={() => setPagina((actual) => actual + 1)}
                  >
                    Siguiente
                  </button>
                </nav>
              </>
            )}
          </>
        )}
      </section>
    </main>
  )
}

export default TableroReportes
