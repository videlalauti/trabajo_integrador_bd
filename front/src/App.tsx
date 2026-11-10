import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import EstadoConexion from './components/EstadoConexion'
import CatalogoVinos from './pages/vinos/CatalogoVinos'
import DetalleVino from './pages/vinos/DetalleVino'
import NuevoVino from './pages/vinos/NuevoVino'
import EditarVino from './pages/vinos/EditarVino'
import NuevaVenta from './pages/ventas/NuevaVenta'
import TransferenciasPage from './pages/transferencias/TransferenciasPage'
import TableroReportes from './pages/reportes/TableroReportes'
import { establecerCsrfSesion } from './lib/api'

type RespuestaSesion = { autorizado: boolean; csrf: string }

const enlaces = [
  { ruta: '/', nombre: 'Inicio' },
  { ruta: '/vinos', nombre: 'Catálogo de vinos' },
  { ruta: '/vinos/nuevo', nombre: 'Alta de vinos' },
  { ruta: '/ventas/nueva', nombre: 'Nueva venta' },
  { ruta: '/transferencias', nombre: 'Transferencias' },
  { ruta: '/reportes', nombre: 'Reportes' },
]

function AccesoEvaluador({ onAcceso }: { onAcceso: (sesion: RespuestaSesion) => void }) {
  const [clave, setClave] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')

  async function acceder(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (!clave.trim()) return
    setError('')
    setEnviando(true)
    try {
      const respuesta = await fetch('/api/demo/acceso', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        cache: 'no-store',
        body: JSON.stringify({ clave }),
      })
      if (!respuesta.ok) {
        setError(respuesta.status === 429
          ? 'Demasiados intentos. Volvé a probar más tarde.'
          : respuesta.status === 401
            ? 'Clave de evaluación incorrecta.'
            : 'El acceso de evaluación no está disponible en este momento.')
        return
      }
      const sesion = await respuesta.json() as RespuestaSesion
      if (!sesion.autorizado || !/^[a-f0-9]{64}$/.test(sesion.csrf)) {
        setError('La sesión recibida no es válida.')
        return
      }
      setClave('')
      onAcceso(sesion)
    } catch {
      setError('No se pudo conectar al servicio de evaluación.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main>
      <h2>Acceso de evaluación — Bodegas del Atuel</h2>
      <p>El sistema utiliza una base de datos ficticia e independiente.
        Las ventas, altas y transferencias que realices son operaciones reales
        en ese entorno de ensayo.</p>
      <form onSubmit={(evento) => { void acceder(evento) }}>
        <label htmlFor="clave-evaluacion">Clave de acceso para profesores</label>{' '}
        <input
          id="clave-evaluacion"
          type="password"
          value={clave}
          onChange={(evento) => setClave(evento.target.value)}
          autoComplete="current-password"
          maxLength={256}
          required
        />{' '}
        <button type="submit" disabled={enviando}>
          {enviando ? 'Verificando…' : 'Ingresar al sistema'}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      <p>La clave no se incluye en el código de la página y no es una contraseña de PostgreSQL.</p>
    </main>
  )
}

function App() {
  const [estado, setEstado] = useState<'verificando' | 'sin-acceso' | 'autenticado'>('verificando')
  const [csrf, setCsrf] = useState<string | null>(null)
  const [errorSalir, setErrorSalir] = useState('')

  useEffect(() => {
    let vigente = true
    void (async () => {
      try {
        const respuesta = await fetch('/api/demo/sesion', {
          credentials: 'same-origin',
          cache: 'no-store',
        })
        if (!vigente) return
        if (!respuesta.ok) {
          establecerCsrfSesion(null)
          setEstado('sin-acceso')
          return
        }
        const datos = await respuesta.json() as RespuestaSesion
        if (datos.autorizado && /^[a-f0-9]{64}$/.test(datos.csrf)) {
          establecerCsrfSesion(datos.csrf)
          setCsrf(datos.csrf)
          setEstado('autenticado')
        } else {
          setEstado('sin-acceso')
        }
      } catch {
        if (vigente) setEstado('sin-acceso')
      }
    })()
    return () => { vigente = false }
  }, [])

  function completarAcceso(sesion: RespuestaSesion) {
    establecerCsrfSesion(sesion.csrf)
    setCsrf(sesion.csrf)
    setEstado('autenticado')
    setErrorSalir('')
  }

  async function salir() {
    if (!csrf) return
    setErrorSalir('')
    try {
      const respuesta = await fetch('/api/demo/salir', {
        method: 'POST',
        headers: { 'X-CSRF-Token': csrf },
        credentials: 'same-origin',
        cache: 'no-store',
      })
      if (!respuesta.ok) throw new Error('Error al cerrar sesión')
      establecerCsrfSesion(null)
      setCsrf(null)
      setEstado('sin-acceso')
    } catch {
      setErrorSalir('No se pudo cerrar la sesión en el servidor. Intentá nuevamente.')
    }
  }

  if (estado === 'verificando') {
    return <main><h1>Bodegas del Atuel</h1><p role="status">Verificando sesión de evaluación…</p></main>
  }

  if (estado === 'sin-acceso') {
    return <AccesoEvaluador onAcceso={completarAcceso} />
  }

  return (
    <BrowserRouter>
      <header>
        <h1>Bodegas del Atuel</h1>
        <p>Sistema de gestión — Fase 8 (entorno institucional de evaluación)</p>
        <p role="status">
          Base ficticia independiente de FULL. Los cambios en este entorno son reales.
        </p>
        <nav aria-label="Navegación principal">
          {enlaces.map((enlace) => (
            <NavLink key={enlace.ruta} to={enlace.ruta} end style={{ marginRight: '16px' }}>
              {enlace.nombre}
            </NavLink>
          ))}
        </nav>
        <button type="button" onClick={() => { void salir() }}>Cerrar sesión</button>
        {errorSalir && <p role="alert">{errorSalir}</p>}
      </header>

      <Routes>
        <Route path="/" element={<main><h2>Inicio</h2><EstadoConexion /></main>} />
        <Route path="/vinos" element={<CatalogoVinos />} />
        <Route path="/vinos/nuevo" element={<NuevoVino />} />
        <Route path="/vinos/:cod_vino" element={<DetalleVino />} />
        <Route path="/vinos/:cod_vino/editar" element={<EditarVino />} />
        <Route path="/ventas/nueva" element={<NuevaVenta />} />
        <Route path="/transferencias" element={<TransferenciasPage />} />
        <Route path="/reportes" element={<TableroReportes />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
