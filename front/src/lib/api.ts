
export class ErrorApi extends Error {
  readonly status: number
  readonly codigo: string

  constructor(status: number, codigo: string, mensaje: string) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.status = status
    this.codigo = codigo
  }
}


function obtenerError(datos: unknown): {
  codigo: string
  mensaje: string
} {
  if (datos && typeof datos === 'object') {
    const respuesta = datos as Record<string, unknown>

    if (respuesta.error && typeof respuesta.error === 'object') {
      const error = respuesta.error as Record<string, unknown>

      return {
        codigo: String(error.codigo ?? 'ERROR_API'),
        mensaje: String(error.mensaje ?? 'La operación fue rechazada.'),
      }
    }

    if (typeof respuesta.detail === 'string') {
      return {
        codigo: 'ERROR_API',
        mensaje: respuesta.detail,
      }
    }

    if (Array.isArray(respuesta.detail)) {
      return {
        codigo: 'DATOS_INVALIDOS',
        mensaje: respuesta.detail
          .map((detalle: { msg?: string }) => detalle.msg ?? 'Dato inválido')
          .join('; '),
      }
    }
  }

  return {
    codigo: 'ERROR_API',
    mensaje: 'No se pudo completar la operación.',
  }
}

export async function solicitarApi<T>(
  ruta: string,
  opciones: RequestInit = {},
): Promise<T> {
  const rutaNormalizada = ruta.startsWith('/') ? ruta : `/${ruta}`
  const headers = new Headers(opciones.headers)

  if (opciones.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let respuesta: Response

  try {
    respuesta = await fetch(`/api${rutaNormalizada}`, {
      ...opciones,
      headers,
    })
  } catch {
    throw new ErrorApi(
      0,
      'SIN_CONEXION',
      'No se pudo conectar con el servidor.',
    )
  }

  const texto = await respuesta.text()
  let datos: unknown = null

  if (texto) {
    try {
      datos = JSON.parse(texto)
    } catch {
      throw new ErrorApi(
        respuesta.status,
        'RESPUESTA_INVALIDA',
        'El servidor devolvió una respuesta inesperada.',
      )
    }
  }

  if (!respuesta.ok) {
    const error = obtenerError(datos)

    throw new ErrorApi(
      respuesta.status,
      error.codigo,
      error.mensaje,
    )
  }

  return datos as T
}
