import { Link, useNavigate } from 'react-router-dom'
import { solicitarApi } from '../../lib/api'
import FormularioVino from './FormularioVino'
import type { VinoFormulario, VinoRespuestaOperacion } from './tipos'

export default function NuevoVino() {
  const navigate = useNavigate()
  async function guardar(datos: VinoFormulario) {
    const respuesta = await solicitarApi<VinoRespuestaOperacion>('/vinos', { method: 'POST', body: JSON.stringify(datos) })
    navigate(`/vinos/${respuesta.cod_vino}`)
  }
  return <main><p><Link to="/vinos">Volver al catálogo</Link></p><FormularioVino titulo="Registrar vino" guardar={guardar} /></main>
}
