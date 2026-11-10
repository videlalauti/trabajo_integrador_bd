import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ErrorApi, solicitarApi } from '../../lib/api'
import type { VinoDetalle } from './tipos'

export default function DetalleVino() {
  const { cod_vino } = useParams()
  return <DetalleVinoPorCodigo key={cod_vino} codigo={Number(cod_vino)} />
}

function DetalleVinoPorCodigo({ codigo }: { codigo: number }) {
  const [vino, setVino] = useState<VinoDetalle | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    if (!Number.isSafeInteger(codigo) || codigo <= 0) return
    let activo = true
    async function cargar() {
      try {
        const respuesta = await solicitarApi<VinoDetalle>(`/vinos/${codigo}`)
        if (activo) { setVino(respuesta); setError(null) }
      } catch (err: unknown) {
        if (activo) setError(err instanceof ErrorApi ? err.message : 'Error inesperado.')
      } finally {
        if (activo) setCargando(false)
      }
    }
    void cargar()
    return () => { activo = false }
  }, [codigo, revision])

  if (!Number.isSafeInteger(codigo) || codigo <= 0) return <main><p role="alert">Código de vino inválido.</p><Link to="/vinos">Volver</Link></main>
  return <main>
    <h2>Detalle de vino</h2>
    <p><Link to="/vinos">Volver al catálogo</Link></p>
    {cargando && <p role="status">Cargando detalle...</p>}
    {!cargando && error && <div role="alert"><p>{error}</p><button type="button" onClick={() => { setCargando(true); setError(null); setRevision((n) => n + 1) }}>Reintentar</button></div>}
    {!cargando && !error && vino && <>
      <h3>{vino.nombre}</h3>
      <dl>
        <dt>Código</dt><dd>{vino.cod_vino}</dd>
        <dt>Tipo</dt><dd>{vino.tipo}</dd>
        <dt>Añada</dt><dd>{vino.anada}</dd>
        <dt>Volumen</dt><dd>{vino.volumen_ml} ml</dd>
        <dt>Graduación</dt><dd>{vino.graduacion}%</dd>
        <dt>Precio</dt><dd>${vino.precio}</dd>
        <dt>CUIT bodega</dt><dd>{vino.cuit_bodega}</dd>
      </dl>
      <h3>Cepas</h3>
      <ul>{vino.cepas.map((c) => <li key={c.id_cepa}>{c.nombre}: {c.porcentaje}%</li>)}</ul>
      <h3>Maridajes</h3>
      {vino.maridajes.length ? <ul>{vino.maridajes.map((m) => <li key={m.id_maridaje}>{m.nombre} — {m.temperatura_servicio_c} °C</li>)}</ul> : <p>Sin maridajes asociados.</p>}
      <p>Entorno de evaluación: podés editar este vino en la base de ensayo.</p><p><Link to={`/vinos/${codigo}/editar`}>Editar vino</Link></p>
    </>}
  </main>
}
