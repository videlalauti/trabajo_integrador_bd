import './TableroReportes.css'
import { useEffect, useState } from 'react'
import { ErrorApi, solicitarApi } from '../../lib/api'
import type { TopVino } from './tipos'

function mensajeError(error: unknown): string {
  if (error instanceof ErrorApi) {
    if (error.status === 0 || error.status === 502 || error.status === 503 || error.status === 504) {
      return 'No se pudo conectar con FastAPI. Volvé a intentar cuando el servicio esté disponible.'
    }
    return `Error ${error.status}: ${error.message}`
  }
  return 'Ocurrió un error inesperado al consultar el ranking.'
}

export default function TableroReportes() {
  const [ranking, setRanking] = useState<TopVino[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let activo = true
    solicitarApi<TopVino[]>('/reportes/top-vinos')
      .then((datos) => {
        if (activo) {
          setRanking(datos)
          setError('')
        }
      })
      .catch((err: unknown) => {
        if (activo) setError(mensajeError(err))
      })
      .finally(() => {
        if (activo) setCargando(false)
      })
    return () => { activo = false }
  }, [intento])

  return (
    <main className="tablero-reportes">
      <h2>Ranking público de vinos</h2>
      <p>Consulta de solo lectura. Los demás reportes y las operaciones de escritura no están habilitados para visitantes durante H1.</p>
      {cargando && <p role="status">Cargando ranking...</p>}
      {!cargando && error && (
        <div role="alert">
          <p>{error}</p>
          <button type="button" onClick={() => {
            setCargando(true)
            setError('')
            setIntento((valor) => valor + 1)
          }}>Reintentar</button>
        </div>
      )}
      {!cargando && !error && ranking.length === 0 && <p>No se encontraron ventas para mostrar.</p>}
      {!cargando && !error && ranking.length > 0 && (
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
    </main>
  )
}
