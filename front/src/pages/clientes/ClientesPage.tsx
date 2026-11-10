import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ErrorApi, solicitarApi } from '../../lib/api'

type TipoCliente = 'socio' | 'distribuidor' | 'exportador'
type ClienteEntrada = {
  nombre_razon_social: string
  tipo_doc: string
  nro_doc: string
  direccion: string
  fecha_alta: string
  id_localidad: number
  tipo_cliente: TipoCliente
  descuento_especial: string | null
  zona_cobertura: string | null
  nro_habilitacion: string | null
  pais_destino: string | null
}
type Cliente = ClienteEntrada & { id_cliente: number }
type PaginaClientes = { items: Cliente[]; total: number; pagina: number; tamanio: number }
type Localidad = { id_localidad: number; nombre: string; provincia: string }

function datosIniciales(): ClienteEntrada {
  return {
    nombre_razon_social: '', tipo_doc: 'DNI', nro_doc: '',
    direccion: '', fecha_alta: new Date().toISOString().slice(0, 10),
    id_localidad: 0, tipo_cliente: 'socio', descuento_especial: null,
    zona_cobertura: null, nro_habilitacion: null, pais_destino: null,
  }
}

function descripcion(error: unknown) {
  return error instanceof ErrorApi ? error.message : 'No fue posible completar la operación.'
}

export default function ClientesPage() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [localidades, setLocalidades] = useState<Localidad[]>([])
  const [pagina, setPagina] = useState(1)
  const [total, setTotal] = useState(0)
  const [version, setVersion] = useState(0)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [editando, setEditando] = useState<number | null>(null)
  const [formulario, setFormulario] = useState<ClienteEntrada>(datosIniciales)

  useEffect(() => {
    let activo = true
    async function cargar() {
      try {
        const [resultado, ciudades] = await Promise.all([
          solicitarApi<PaginaClientes>(`/clientes?page=${pagina}&page_size=15`),
          solicitarApi<Localidad[]>('/demo/localidades'),
        ])
        if (!activo) return
        setClientes(resultado.items)
        setTotal(resultado.total)
        setLocalidades(ciudades)
        setError('')
      } catch (e) {
        if (activo) setError(descripcion(e))
      } finally {
        if (activo) setCargando(false)
      }
    }
    void cargar()
    return () => { activo = false }
  }, [pagina, version])

  function editar(cliente: Cliente) {
    const { id_cliente, ...datos } = cliente
    setFormulario(datos)
    setEditando(id_cliente)
    setMensaje('')
    setError('')
  }

  function limpiar() {
    setFormulario(datosIniciales())
    setEditando(null)
  }

  function cambiar<K extends keyof ClienteEntrada>(campo: K, valor: ClienteEntrada[K]) {
    setFormulario((actual) => ({ ...actual, [campo]: valor }))
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    setGuardando(true)
    setError('')
    setMensaje('')
    try {
      if (editando === null) {
        const nuevo = await solicitarApi<Cliente>('/clientes', {
          method: 'POST', body: JSON.stringify(formulario),
        })
        setMensaje(`Cliente ficticio ${nuevo.id_cliente} registrado.`)
      } else {
        await solicitarApi<Cliente>(`/clientes/${editando}`, {
          method: 'PUT', body: JSON.stringify(formulario),
        })
        setMensaje(`Cliente ${editando} actualizado en DEMO.`)
      }
      limpiar()
      setVersion((v) => v + 1)
    } catch (e) {
      setError(descripcion(e))
    } finally {
      setGuardando(false)
    }
  }

  async function eliminar(cliente: Cliente) {
    if (!window.confirm(`¿Eliminar al cliente ficticio ${cliente.id_cliente}? PostgreSQL puede rechazarlo si tiene ventas relacionadas.`)) return
    setError('')
    setMensaje('')
    try {
      await solicitarApi<void>(`/clientes/${cliente.id_cliente}`, { method: 'DELETE' })
      setMensaje(`Cliente ${cliente.id_cliente} eliminado de DEMO.`)
      setVersion((v) => v + 1)
    } catch (e) {
      setError(descripcion(e))
    }
  }

  return (
    <main>
      <h2>Clientes — base de evaluación</h2>
      <p>Gestioná clientes ficticios. La base FULL institucional no se modifica.</p>
      {mensaje && <p role="status">{mensaje}</p>}
      {error && <p role="alert">{error}</p>}
      <section>
        <h3>{editando === null ? 'Registrar cliente' : `Editar cliente ${editando}`}</h3>
        <form onSubmit={(evento) => { void guardar(evento) }}>
          <label>Nombre o razón social{' '}
            <input required maxLength={150} value={formulario.nombre_razon_social}
              onChange={(e) => cambiar('nombre_razon_social', e.target.value)} />
          </label>{' '}
          <label>Tipo documento{' '}
            <input required maxLength={15} value={formulario.tipo_doc}
              onChange={(e) => cambiar('tipo_doc', e.target.value)} />
          </label>{' '}
          <label>Número documento{' '}
            <input required maxLength={30} value={formulario.nro_doc}
              onChange={(e) => cambiar('nro_doc', e.target.value)} />
          </label>{' '}
          <label>Dirección{' '}
            <input required maxLength={200} value={formulario.direccion}
              onChange={(e) => cambiar('direccion', e.target.value)} />
          </label>{' '}
          <label>Fecha de alta{' '}
            <input required type="date" value={formulario.fecha_alta}
              onChange={(e) => cambiar('fecha_alta', e.target.value)} />
          </label>{' '}
          <label>Localidad{' '}
            <select required value={formulario.id_localidad || ''}
              onChange={(e) => cambiar('id_localidad', Number(e.target.value))}>
              <option value="">Seleccionar localidad</option>
              {localidades.map((localidad) => (
                <option key={localidad.id_localidad} value={localidad.id_localidad}>
                  {localidad.nombre} ({localidad.provincia})
                </option>
              ))}
            </select>
          </label>{' '}
          <label>Tipo de cliente{' '}
            <select value={formulario.tipo_cliente}
              onChange={(e) => cambiar('tipo_cliente', e.target.value as TipoCliente)}>
              <option value="socio">Socio</option>
              <option value="distribuidor">Distribuidor</option>
              <option value="exportador">Exportador</option>
            </select>
          </label>{' '}
          <label>Descuento especial (%){' '}
            <input type="number" min="0" max="100" step="0.01"
              value={formulario.descuento_especial ?? ''}
              onChange={(e) => cambiar('descuento_especial', e.target.value || null)} />
          </label>{' '}
          {formulario.tipo_cliente !== 'socio' && (
            <label>Zona de cobertura{' '}
              <input maxLength={150} value={formulario.zona_cobertura ?? ''}
                onChange={(e) => cambiar('zona_cobertura', e.target.value || null)} />
            </label>
          )}{' '}
          {formulario.tipo_cliente === 'exportador' && (
            <>
              <label>Número de habilitación{' '}
                <input maxLength={50} value={formulario.nro_habilitacion ?? ''}
                  onChange={(e) => cambiar('nro_habilitacion', e.target.value || null)} />
              </label>{' '}
              <label>País destino{' '}
                <input maxLength={100} value={formulario.pais_destino ?? ''}
                  onChange={(e) => cambiar('pais_destino', e.target.value || null)} />
              </label>
            </>
          )}
          <p>
            <button type="submit" disabled={guardando || !formulario.id_localidad}>
              {guardando ? 'Guardando…' : editando === null ? 'Registrar cliente' : 'Guardar cambios'}
            </button>{' '}
            {editando !== null && <button type="button" onClick={limpiar}>Cancelar edición</button>}
          </p>
        </form>
      </section>
      <section>
        <h3>Clientes registrados</h3>
        {cargando && <p role="status">Consultando clientes…</p>}
        {!cargando && <p>Total: {total}</p>}
        {clientes.length > 0 && (
          <table>
            <thead><tr><th>ID</th><th>Nombre</th><th>Tipo</th><th>Documento</th><th>Acciones</th></tr></thead>
            <tbody>
              {clientes.map((cliente) => (
                <tr key={cliente.id_cliente}>
                  <td>{cliente.id_cliente}</td>
                  <td>{cliente.nombre_razon_social}</td>
                  <td>{cliente.tipo_cliente}</td>
                  <td>{cliente.nro_doc}</td>
                  <td>
                    <button type="button" onClick={() => editar(cliente)}>Editar</button>{' '}
                    <button type="button" onClick={() => { void eliminar(cliente) }}>Eliminar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <button type="button" disabled={pagina <= 1} onClick={() => { setCargando(true); setPagina((p) => p - 1) }}>Anterior</button>{' '}
        Página {pagina} de {Math.max(1, Math.ceil(total / 15))}{' '}
        <button type="button" disabled={pagina * 15 >= total} onClick={() => { setCargando(true); setPagina((p) => p + 1) }}>Siguiente</button>
      </section>
    </main>
  )
}
