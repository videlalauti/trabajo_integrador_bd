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
import TableroReportes from './pages/reportes/TableroReportes'

const enlaces = [
  { ruta: '/', nombre: 'Inicio' },
  { ruta: '/vinos', nombre: 'Catálogo de vinos' },
  { ruta: '/ventas/nueva', nombre: 'Ventas (bloqueadas)' },
  { ruta: '/transferencias', nombre: 'Transferencias (bloqueadas)' },
  { ruta: '/reportes', nombre: 'Ranking de vinos' },
]

function PantallaBloqueada({ nombre }: { nombre: string }) {
  return (
    <main>
      <h2>{nombre} — operación no disponible</h2>
      <p role="status">
        Esta demostración pública funciona en modo SOLO LECTURA (H1).
        Las operaciones de escritura están deshabilitadas y protegidas por FastAPI.
      </p>
      <p>Podés consultar el catálogo de vinos, sus detalles, los catálogos auxiliares y el ranking público.</p>
    </main>
  )
}

function App() {
  return (
    <BrowserRouter>
      <header>
        <h1>Bodegas del Atuel</h1>
        <p>Sistema de gestión — Fase 8</p>
        <p role="status">Demostración pública — SOLO LECTURA (H1). Altas, ediciones, ventas y transferencias bloqueadas.</p>

        <nav aria-label="Navegación principal">
          {enlaces.map((enlace) => (
            <NavLink
              key={enlace.ruta}
              to={enlace.ruta}
              end
              style={{ marginRight: '16px' }}
            >
              {enlace.nombre}
            </NavLink>
          ))}
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<main><h2>Inicio</h2><EstadoConexion /></main>} />
        <Route path="/vinos" element={<CatalogoVinos />} />
        <Route path="/vinos/:cod_vino" element={<DetalleVino />} />
        <Route path="/vinos/nuevo" element={<PantallaBloqueada nombre="Alta de vinos" />} />
        <Route path="/vinos/:cod_vino/editar" element={<PantallaBloqueada nombre="Edición de vinos" />} />
        <Route path="/ventas/nueva" element={<PantallaBloqueada nombre="Registro de ventas" />} />
        <Route path="/transferencias" element={<PantallaBloqueada nombre="Transferencias" />} />
        <Route path="/reportes" element={<TableroReportes />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
