// Presentacion diferenciada de los errores de la API (contrato, seccion 6).
// No reinterpreta las reglas: muestra el mensaje real que devuelve FastAPI,
// que en los rechazos de negocio es el texto del trigger o procedimiento.

import { ErrorApi } from '../../lib/api'

type Props = {
  error: unknown
}

type Presentacion = {
  titulo: string
  color: string
  fondo: string
}

// La API no esta disponible:
// - status 0: fetch no llego a ningun servidor (SIN_CONEXION).
// - 502/503/504: el servidor o la base no responden.
// - 500 con codigo ERROR_API: es la respuesta VACIA del proxy de Vite cuando
//   la API esta apagada (el cliente compartido no encuentra un error del
//   contrato y usa ERROR_API). Un error real de FastAPI siempre trae su
//   propio codigo, y un 500 no JSON se informa como RESPUESTA_INVALIDA.
function esSinConexion(error: ErrorApi): boolean {
  return (
    error.status === 0 ||
    error.status === 502 ||
    error.status === 503 ||
    error.status === 504 ||
    (error.status === 500 && error.codigo === 'ERROR_API')
  )
}

function clasificar(error: ErrorApi): Presentacion {
  if (esSinConexion(error)) {
    return { titulo: 'Sin conexión con el servidor', color: '#7a4b00', fondo: '#fff4e0' }
  }
  if (error.status === 404) {
    return { titulo: 'No encontrado', color: '#344054', fondo: '#f2f4f7' }
  }
  // 23505 (UNIQUE / PRIMARY KEY): en este modulo solo puede producirlo un
  // renglon con un vino que ya esta en la transferencia, por la clave
  // primaria (nro_solicitud, cod_vino) de renglon_transferencia.
  if (error.status === 409 && error.codigo === '23505') {
    return { titulo: 'Ese vino ya está incluido en la transferencia', color: '#b42318', fondo: '#fef3f2' }
  }
  if (error.status === 409) {
    return { titulo: 'Operación rechazada por una regla de negocio', color: '#b42318', fondo: '#fef3f2' }
  }
  if (error.status === 422 || error.status === 400) {
    return { titulo: 'Datos inválidos', color: '#b54708', fondo: '#fffaeb' }
  }
  return { titulo: 'No se pudo completar la operación', color: '#b42318', fondo: '#fef3f2' }
}

export default function MensajeError({ error }: Props) {
  if (!(error instanceof ErrorApi)) {
    return (
      <p role="alert" style={{ color: '#b42318' }}>
        Ocurrió un error inesperado en la pantalla.
      </p>
    )
  }

  const { titulo, color, fondo } = clasificar(error)

  return (
    <div
      role="alert"
      style={{
        color,
        background: fondo,
        border: `1px solid ${color}`,
        borderRadius: '6px',
        padding: '8px 12px',
        margin: '12px 0',
      }}
    >
      <strong>{titulo}</strong>
      <p style={{ margin: '4px 0 0' }}>{error.message}</p>
      {esSinConexion(error) && (
        <p style={{ margin: '4px 0 0' }}>
          Verificá que la API esté en funcionamiento y volvé a intentar.
        </p>
      )}
      <small>
        Código: {error.codigo} · HTTP {error.status === 0 ? '—' : error.status}
      </small>
    </div>
  )
}
