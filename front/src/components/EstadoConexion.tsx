
import { useEffect, useState } from 'react'
import { solicitarApi } from '../lib/api'

type EstadoSalud = {
  estado: string
  base_datos: string
}

export default function EstadoConexion() {
  const [mensaje, setMensaje] = useState('Verificando conexión...')
  const [error, setError] = useState(false)

  useEffect(() => {
    let activo = true

    async function verificarConexion() {
      try {
        const datos = await solicitarApi<EstadoSalud>('/salud')

        if (activo) {
          setMensaje(
            `API: ${datos.estado} | PostgreSQL: ${datos.base_datos}`,
          )
          setError(false)
        }
      } catch {
        if (activo) {
          setMensaje('No se pudo conectar con FastAPI.')
          setError(true)
        }
      }
    }

    void verificarConexion()

    return () => {
      activo = false
    }
  }, [])

  return (
    <section aria-label="Estado de conexión">
      <h3>Estado del sistema</h3>
      <p role="status" style={{ color: error ? '#b42318' : '#246b45' }}>
        {mensaje}
      </p>
    </section>
  )
}
