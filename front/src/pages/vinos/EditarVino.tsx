import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ErrorApi, solicitarApi } from '../../lib/api'
import FormularioVino from './FormularioVino'
import type { VinoDetalle, VinoFormulario, VinoRespuestaOperacion } from './tipos'

export default function EditarVino() {
  const { cod_vino } = useParams()
  return <EditarVinoPorCodigo key={cod_vino} codigo={Number(cod_vino)} />
}

function EditarVinoPorCodigo({ codigo }: { codigo: number }) {
  const navigate = useNavigate()
  const [inicial, setInicial] = useState<VinoFormulario | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    if (!Number.isSafeInteger(codigo) || codigo <= 0) return
    let activo = true
    async function cargar() {
      try {
        const v = await solicitarApi<VinoDetalle>(`/vinos/${codigo}`)
        if (activo) {
          setInicial({ nombre: v.nombre, tipo: v.tipo, anada: v.anada, volumen_ml: v.volumen_ml,
            graduacion: String(v.graduacion), precio: String(v.precio), cuit_bodega: v.cuit_bodega,
            cepas: v.cepas.map((c) => ({ id_cepa: c.id_cepa, porcentaje: String(c.porcentaje) })),
            maridajes: v.maridajes.map((m) => m.id_maridaje) })
          setError(null)
        }
      } catch (err: unknown) {
        if (activo) setError(err instanceof ErrorApi ? err.message : 'Error inesperado.')
      } finally { if (activo) setCargando(false) }
    }
    void cargar()
    return () => { activo = false }
  }, [codigo, revision])

  async function guardar(datos: VinoFormulario) {
    await solicitarApi<VinoRespuestaOperacion>(`/vinos/${codigo}`, { method: 'PUT', body: JSON.stringify(datos) })
    navigate(`/vinos/${codigo}`)
  }
  if (!Number.isSafeInteger(codigo) || codigo <= 0) return <main><p role="alert">Código de vino inválido.</p><Link to="/vinos">Volver</Link></main>
  return <main>
    <p><Link to={`/vinos/${codigo}`}>Volver al detalle</Link></p>
    {cargando && <p role="status">Cargando vino...</p>}
    {!cargando && error && <div role="alert"><p>{error}</p><button type="button" onClick={() => { setCargando(true); setError(null); setRevision((n) => n + 1) }}>Reintentar</button></div>}
    {!cargando && !error && inicial && <FormularioVino key={codigo} titulo={`Editar vino ${codigo}`} inicial={inicial} guardar={guardar} />}
  </main>
}
