
import {
  BrowserRouter,
  NavLink,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import EstadoConexion from './components/EstadoConexion'

function PantallaPendiente({ titulo }: { titulo: string }) {
  return (
    <main>
      <h2>{titulo}</h2>
      <p>Esta pantalla se desarrollará durante la Fase 7.</p>
    </main>
  )
}

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
        <p>Sistema de gestión — Fase 7</p>

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
          element={<PantallaPendiente titulo="Catálogo de vinos" />}
        />
        <Route
          path="/vinos/nuevo"
          element={<PantallaPendiente titulo="Alta de vinos" />}
        />
        <Route
          path="/vinos/:cod_vino/editar"
          element={<PantallaPendiente titulo="Editar vino" />}
        />
        <Route
          path="/ventas/nueva"
          element={<PantallaPendiente titulo="Nueva venta" />}
        />
        <Route
          path="/transferencias"
          element={<PantallaPendiente titulo="Transferencias" />}
        />
        <Route
          path="/reportes"
          element={<PantallaPendiente titulo="Tablero de reportes" />}
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
