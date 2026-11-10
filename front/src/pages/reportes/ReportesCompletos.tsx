import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ErrorApi, solicitarApi } from '../../lib/api'
import TableroReportes from './TableroReportes'

type VentaSala = { id_sala: number; calle: string; numero: string; total_ventas: string }
type Transportista = { cod_transporte: number; razon_social: string; cantidad_ingresos: number }
type Sala = { id_sala: number; calle: string; numero: string; localidad: string }
type SinStock = { cod_vino: number; vino: string; stock_sala: number; stock_deposito: number }
type Pagina = { items: SinStock[]; total: number }
type Lote = { nro_lote: number; campania: number; nombre_finca: string; nro_parcela: number }
type Trazabilidad = {
  vino: { nombre_vino: string; nombre_bodega: string }
  lotes_registrados_en_bodega: Lote[]
  total_lotes_bodega: number
  aclaracion: string
}
const explicar = (e: unknown) => e instanceof ErrorApi ? e.message : 'Error al consultar PostgreSQL.'

export default function ReportesCompletos() {
  const [ventas, setVentas] = useState<VentaSala[]>([])
  const [transportista, setTransportista] = useState<Transportista | null>(null)
  const [salas, setSalas] = useState<Sala[]>([])
  const [idSala, setIdSala] = useState('')
  const [sinStock, setSinStock] = useState<Pagina | null>(null)
  const [codigo, setCodigo] = useState('')
  const [trazabilidad, setTrazabilidad] = useState<Trazabilidad | null>(null)
  const [error, setError] = useState('')
  const [errorStock, setErrorStock] = useState('')
  const [errorTraza, setErrorTraza] = useState('')
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let activo = true
    void Promise.all([
      solicitarApi<VentaSala[]>('/reportes/ventas-por-sala'),
      solicitarApi<Transportista | null>('/reportes/transportista-activo'),
      solicitarApi<Sala[]>('/salas'),
    ]).then(([porSala, mejor, listado]) => {
      if (!activo) return
      setVentas(porSala)
      setTransportista(mejor)
      setSalas(listado)
      setError('')
    }).catch((e: unknown) => {
      if (activo) setError(explicar(e))
    })
    return () => { activo = false }
  }, [revision])

  async function buscarStock(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setErrorStock('')
    try {
      const datos = await solicitarApi<Pagina>(
        `/reportes/vinos-sin-stock?id_sala=${idSala}&page=1&page_size=100`)
      setSinStock(datos)
    } catch (e) {
      setSinStock(null)
      setErrorStock(explicar(e))
    }
  }

  async function buscarTraza(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!Number.isSafeInteger(Number(codigo)) || Number(codigo) < 1) {
      setErrorTraza('Ingresá un código entero positivo.')
      return
    }
    setErrorTraza('')
    try {
      setTrazabilidad(await solicitarApi<Trazabilidad>(`/reportes/trazabilidad/${codigo}`))
    } catch (e) {
      setTrazabilidad(null)
      setErrorTraza(explicar(e))
    }
  }

  return (
    <>
      <TableroReportes />
      <section>
        <h2>Otros reportes de PostgreSQL</h2>
        <p>Son consultas reales sobre la base DEMO, no cálculos simulados en React.</p>
        <button type="button" onClick={() => setRevision((v) => v + 1)}>Actualizar reportes</button>
        {error && <p role="alert">{error}</p>}
        <h3>Ventas por sala — último trimestre</h3>
        {ventas.length === 0 ? <p>Sin ventas en el período.</p> : (
          <table><thead><tr><th>Sala</th><th>Dirección</th><th>Total</th></tr></thead>
            <tbody>{ventas.map((v) => <tr key={v.id_sala}>
              <td>{v.id_sala}</td><td>{v.calle} {v.numero}</td><td>{v.total_ventas}</td>
            </tr>)}</tbody>
          </table>
        )}
        <h3>Vinos sin stock en sala, con existencias en depósito</h3>
        <form onSubmit={(e) => { void buscarStock(e) }}>
          <label>Sala{' '}
            <select required value={idSala} onChange={(e) => setIdSala(e.target.value)}>
              <option value="">Seleccionar</option>
              {salas.map((s) => <option key={s.id_sala} value={s.id_sala}>
                Sala {s.id_sala}, {s.calle} {s.numero} ({s.localidad})
              </option>)}
            </select>
          </label>{' '}
          <button type="submit">Consultar</button>
        </form>
        {errorStock && <p role="alert">{errorStock}</p>}
        {sinStock && <p>Total: {sinStock.total} (se muestran los primeros 100).</p>}
        {sinStock && sinStock.items.length > 0 && (
          <table><thead><tr><th>Vino</th><th>Stock sala</th><th>Stock depósito</th></tr></thead>
            <tbody>{sinStock.items.map((v) => <tr key={v.cod_vino}>
              <td>{v.vino}</td><td>{v.stock_sala}</td><td>{v.stock_deposito}</td>
            </tr>)}</tbody>
          </table>
        )}
        <h3>Transportista más activo — último mes</h3>
        {transportista ? <p>{transportista.razon_social}:
          {transportista.cantidad_ingresos} ingresos.</p> : <p>Sin ingresos en el período.</p>}
        <h3>Trazabilidad de vino</h3>
        <form onSubmit={(e) => { void buscarTraza(e) }}>
          <label>Código de vino{' '}
            <input type="number" min="1" required value={codigo}
              onChange={(e) => setCodigo(e.target.value)} />
          </label>{' '}
          <button type="submit">Consultar</button>
        </form>
        {errorTraza && <p role="alert">{errorTraza}</p>}
        {trazabilidad && (
          <>
            <p>{trazabilidad.vino.nombre_vino}, bodega {trazabilidad.vino.nombre_bodega}.</p>
            <p>{trazabilidad.aclaracion}</p>
            <p>Total de lotes de esa bodega: {trazabilidad.total_lotes_bodega}.
              No se presume una relación directa vino-lote.</p>
            {trazabilidad.lotes_registrados_en_bodega.length > 0 && (
              <table><thead><tr><th>Lote</th><th>Campaña</th><th>Finca</th><th>Parcela</th></tr></thead>
                <tbody>{trazabilidad.lotes_registrados_en_bodega.map((l) => (
                  <tr key={l.nro_lote}>
                    <td>{l.nro_lote}</td><td>{l.campania}</td>
                    <td>{l.nombre_finca}</td><td>{l.nro_parcela}</td>
                  </tr>
                ))}</tbody>
              </table>
            )}
          </>
        )}
      </section>
    </>
  )
}
