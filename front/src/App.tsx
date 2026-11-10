
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

import TableroReportes from './pages/reportes/TableroReportes'

import TransferenciasPage from './pages/transferencias/TransferenciasPage'

const enlaces = [
  { ruta: '/', nombre: 'Inicio' },
  { ruta: '/vinos', nombre: 'Catálogo de vinos' },
  { ruta: '/vinos/nuevo', nombre: 'Alta de vinos' },
  { ruta: '/ventas/nueva', nombre: 'Nueva venta' },
  { ruta: '/transferencias', nombre: 'Transferencias' },
  { ruta: '/reportes', nombre: 'Reportes' },
]

function App() {
  return (
    <BrowserRouter>
      <header>
        <h1>Bodegas del Atuel</h1>
        <p>Sistema de gestión — Fase 8</p>

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
        <Route
          path="/"
          element={
            <main>
              <h2>Inicio</h2>
              <EstadoConexion />
            </main>
          }
        />

        <Route
          path="/vinos"
          element={<CatalogoVinos />}
        />

        <Route
          path="/vinos/nuevo"
          element={<NuevoVino />}
        />

        <Route
          path="/vinos/:cod_vino"
          element={<DetalleVino />}
        />

        <Route
          path="/vinos/:cod_vino/editar"
          element={<EditarVino />}
        />

        <Route
          path="/ventas/nueva"
          element={<NuevaVenta />}
        />

        <Route
          path="/transferencias"
          element={<TransferenciasPage />}
        />

        <Route
          path="/reportes"
          element={<TableroReportes />}
        />

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
