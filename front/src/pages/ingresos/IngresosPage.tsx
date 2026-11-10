import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ErrorApi, solicitarApi } from '../../lib/api'

type Transportista = { cod_transporte: number; razon_social: string }
type Bodega = { cuit: string; razon_social: string }
type Vino = { cod_vino: number; nombre: string }
type PaginaVinos = { items: Vino[] }
type Renglon = {
  cod_vino: number
  vino: string
  cantidad: number
  stock_deposito: number
}
type Ingreso = {
  cod_ingreso: number
  fecha: string
  estado: 'en_confeccion' | 'terminado' | 'procesado'
  cod_transporte: number
  transportista: string
  cuit_bodega: string
  bodega: string
  renglones: Renglon[]
}

function explicar(e: unknown): string {
  return e instanceof ErrorApi ? e.message : 'No se pudo completar la operación.'
}

export default function IngresosPage() {
  const [transportistas, setTransportistas] = useState<Transportista[]>([])
  const [bodegas, setBodegas] = useState<Bodega[]>([])
  const [vinos, setVinos] = useState<Vino[]>([])
  const [transportista, setTransportista] = useState('')
  const [bodega, setBodega] = useState('')
  const [numeroBuscado, setNumeroBuscado] = useState('')
  const [vino, setVino] = useState('')
  const [cantidad, setCantidad] = useState('1')
  const [ingreso, setIngreso] = useState<Ingreso | null>(null)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [ocupado, setOcupado] = useState(false)

  useEffect(() => {
    let activo = true
    void Promise.all([
      solicitarApi<Transportista[]>('/demo/transportistas'),
      solicitarApi<Bodega[]>('/bodegas'),
      solicitarApi<PaginaVinos>('/vinos?page=1&page_size=100'),
    ]).then(([transportistasDb, bodegasDb, vinosDb]) => {
      if (!activo) return
      setTransportistas(transportistasDb)
      setBodegas(bodegasDb)
      setVinos(vinosDb.items)
    }).catch((e: unknown) => {
      if (activo) setError(explicar(e))
    })
    return () => { activo = false }
  }, [])

  async function ejecutar(operacion: () => Promise<Ingreso>) {
    setOcupado(true)
    setError('')
    setMensaje('')
    try {
      const resultado = await operacion()
      setIngreso(resultado)
      setNumeroBuscado(String(resultado.cod_ingreso))
      setMensaje(`Ingreso ${resultado.cod_ingreso}: ${resultado.estado}.`)
    } catch (e) {
      setError(explicar(e))
    } finally {
      setOcupado(false)
    }
  }

  function crear(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    void ejecutar(() => solicitarApi<Ingreso>('/ingresos', {
      method: 'POST',
      body: JSON.stringify({ cod_transporte: Number(transportista), cuit_bodega: bodega }),
    }))
  }

  function consultar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!Number.isSafeInteger(Number(numeroBuscado)) || Number(numeroBuscado) < 1) {
      setError('Ingresá un número de ingreso válido.')
      return
    }
    void ejecutar(() => solicitarApi<Ingreso>(`/ingresos/${numeroBuscado}`))
  }

  function agregar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!ingreso || !Number.isSafeInteger(Number(cantidad)) || Number(cantidad) <= 0 || !vino) {
      setError('Seleccioná un vino e ingresá una cantidad entera positiva.')
      return
    }
    void ejecutar(() => solicitarApi<Ingreso>(`/ingresos/${ingreso.cod_ingreso}/renglones`, {
      method: 'POST',
      body: JSON.stringify({ cod_vino: Number(vino), cantidad: Number(cantidad) }),
    }))
  }

  function cambiarEstado(accion: 'terminar' | 'procesar') {
    if (!ingreso) return
    if (!window.confirm(`¿${accion === 'terminar' ? 'Terminar' : 'Procesar'} el ingreso ficticio ${ingreso.cod_ingreso}? Se ejecutará el procedimiento real de PostgreSQL.`)) return
    void ejecutar(() => solicitarApi<Ingreso>(`/ingresos/${ingreso.cod_ingreso}/${accion}`, {
      method: 'POST',
    }))
  }

  return (
    <main>
      <h2>Ingresos al depósito</h2>
      <p>Registrá y procesá ingresos de vino en Supabase DEMO. Los procedimientos y controles de stock se ejecutan realmente.</p>
      {error && <p role="alert">{error}</p>}
      {mensaje && <p role="status">{mensaje}</p>}
      <section>
        <h3>Nuevo ingreso</h3>
        <form onSubmit={crear}>
          <label>Transportista{' '}
            <select required value={transportista} onChange={(e) => setTransportista(e.target.value)}>
              <option value="">Seleccionar</option>
              {transportistas.map((t) => <option key={t.cod_transporte} value={t.cod_transporte}>{t.razon_social}</option>)}
            </select>
          </label>{' '}
          <label>Bodega de origen{' '}
            <select required value={bodega} onChange={(e) => setBodega(e.target.value)}>
              <option value="">Seleccionar</option>
              {bodegas.map((b) => <option key={b.cuit} value={b.cuit}>{b.razon_social}</option>)}
            </select>
          </label>{' '}
          <button type="submit" disabled={ocupado}>Crear ingreso</button>
        </form>
      </section>
      <section>
        <h3>Consultar ingreso</h3>
        <form onSubmit={consultar}>
          <label>Número{' '}
            <input type="number" min="1" step="1" required value={numeroBuscado}
              onChange={(e) => setNumeroBuscado(e.target.value)} />
          </label>{' '}
          <button type="submit" disabled={ocupado}>Consultar</button>
        </form>
      </section>
      {ingreso && (
        <section>
          <h3>Ingreso {ingreso.cod_ingreso}</h3>
          <p>Estado: <strong>{ingreso.estado}</strong> · Fecha: {ingreso.fecha}</p>
          <p>Transportista: {ingreso.transportista} · Bodega: {ingreso.bodega}</p>
          <h4>Renglones</h4>
          <table>
            <thead><tr><th>Vino</th><th>Cantidad</th><th>Stock de depósito actual</th></tr></thead>
            <tbody>{ingreso.renglones.map((r) => (
              <tr key={r.cod_vino}>
                <td>{r.vino} (#{r.cod_vino})</td>
                <td>{r.cantidad}</td>
                <td>{r.stock_deposito}</td>
              </tr>
            ))}</tbody>
          </table>
          {ingreso.estado === 'en_confeccion' && (
            <>
              <form onSubmit={agregar}>
                <h4>Agregar renglón</h4>
                <label>Vino{' '}
                  <select value={vino} required onChange={(e) => setVino(e.target.value)}>
                    <option value="">Seleccionar</option>
                    {vinos.map((v) => <option value={v.cod_vino} key={v.cod_vino}>{v.nombre} (#{v.cod_vino})</option>)}
                  </select>
                </label>{' '}
                <label>Cantidad{' '}
                  <input type="number" min="1" step="1" required value={cantidad}
                    onChange={(e) => setCantidad(e.target.value)} />
                </label>{' '}
                <button type="submit" disabled={ocupado}>Agregar vino</button>
              </form>
              <button type="button" disabled={ocupado || ingreso.renglones.length === 0}
                onClick={() => cambiarEstado('terminar')}>Terminar ingreso</button>
            </>
          )}
          {ingreso.estado === 'terminado' && (
            <button type="button" disabled={ocupado} onClick={() => cambiarEstado('procesar')}>
              Procesar ingreso y actualizar stock
            </button>
          )}
        </section>
      )}
    </main>
  )
}
