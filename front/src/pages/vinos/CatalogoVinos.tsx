import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorApi, solicitarApi } from '../../lib/api'
import type { Bodega, Cepa, TipoVino, VinosPaginados } from './tipos'

type Filtros = { tipo: string; cepa: string; bodega: string; anada: string }
const vacios = (): Filtros => ({ tipo: '', cepa: '', bodega: '', anada: '' })
const TAMANIO = 20

export default function CatalogoVinos() {
  const [borrador, setBorrador] = useState<Filtros>(vacios)
  const [filtros, setFiltros] = useState<Filtros>(vacios)
  const [pagina, setPagina] = useState(1)
  const [revision, setRevision] = useState(0)
  const [datos, setDatos] = useState<VinosPaginados | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [errorFiltro, setErrorFiltro] = useState<string | null>(null)
  const [bodegas, setBodegas] = useState<Bodega[]>([])
  const [cepas, setCepas] = useState<Cepa[]>([])
  const [errorCatalogos, setErrorCatalogos] = useState<string | null>(null)

  useEffect(() => {
    let activo = true
    async function cargarCatalogos() {
      const resultados = await Promise.allSettled([
        solicitarApi<Bodega[]>('/bodegas'),
        solicitarApi<Cepa[]>('/cepas'),
      ])
      if (!activo) return
      if (resultados[0].status === 'fulfilled') setBodegas(resultados[0].value)
      if (resultados[1].status === 'fulfilled') setCepas(resultados[1].value)
      if (resultados.some((r) => r.status === 'rejected')) {
        setErrorCatalogos('No se pudieron cargar todos los selectores. Podés reintentar recargando la página.')
      }
    }
    void cargarCatalogos()
    return () => { activo = false }
  }, [])

  useEffect(() => {
    let activo = true
    const params = new URLSearchParams({ page: String(pagina), page_size: String(TAMANIO) })
    for (const [clave, valor] of Object.entries(filtros)) {
      if (valor) params.set(clave, valor)
    }
    async function cargar() {
      try {
        const respuesta = await solicitarApi<VinosPaginados>(`/vinos?${params}`)
        if (activo) { setDatos(respuesta); setError(null) }
      } catch (err: unknown) {
        if (activo) { setDatos(null); setError(err instanceof ErrorApi ? err.message : 'Error inesperado.') }
      } finally {
        if (activo) setCargando(false)
      }
    }
    void cargar()
    return () => { activo = false }
  }, [pagina, filtros, revision])

  function aplicar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    if (borrador.anada && !Number.isSafeInteger(Number(borrador.anada))) {
      setErrorFiltro('La añada debe ser un número entero.'); return
    }
    setErrorFiltro(null); setDatos(null); setError(null); setCargando(true)
    setPagina(1); setFiltros({ ...borrador }); setRevision((n) => n + 1)
  }
  function limpiar() {
    setBorrador(vacios()); setFiltros(vacios()); setPagina(1)
    setErrorFiltro(null); setDatos(null); setError(null); setCargando(true); setRevision((n) => n + 1)
  }
  function cambiarPagina(valor: number) {
    setPagina(valor); setDatos(null); setError(null); setCargando(true)
  }
  const totalPaginas = datos ? Math.max(1, Math.ceil(datos.total / datos.tamanio)) : 1
  const cambiar = (campo: keyof Filtros, valor: string) => setBorrador((f) => ({ ...f, [campo]: valor }))

  return <main>
    <h2>Catálogo de vinos</h2>
    <p><Link to="/vinos/nuevo">Registrar nuevo vino</Link></p>
    <h3>Filtros</h3>
    {errorCatalogos && <p role="alert">{errorCatalogos}</p>}
    <form onSubmit={aplicar}>
      <label htmlFor="vino-tipo">Tipo</label>
      <select id="vino-tipo" value={borrador.tipo} onChange={(e) => cambiar('tipo', e.target.value as TipoVino | '')}>
        <option value="">Todos</option>
        {(['tinto', 'blanco', 'rosado', 'espumante'] as const).map((tipo) => <option key={tipo} value={tipo}>{tipo}</option>)}
      </select>
      <label htmlFor="vino-cepa">Cepa</label>
      <select id="vino-cepa" value={borrador.cepa} onChange={(e) => cambiar('cepa', e.target.value)}>
        <option value="">Todas</option>
        {cepas.map((c) => <option key={c.id_cepa} value={c.id_cepa}>{c.nombre} ({c.tipo})</option>)}
      </select>
      <label htmlFor="vino-bodega">Bodega</label>
      <select id="vino-bodega" value={borrador.bodega} onChange={(e) => cambiar('bodega', e.target.value)}>
        <option value="">Todas</option>
        {bodegas.map((b) => <option key={b.cuit} value={b.cuit}>{b.razon_social} ({b.cuit})</option>)}
      </select>
      <label htmlFor="vino-anada">Añada</label>
      <input id="vino-anada" type="number" step="1" value={borrador.anada} onChange={(e) => cambiar('anada', e.target.value)} />
      <button type="submit">Aplicar filtros</button>
      <button type="button" onClick={limpiar}>Limpiar filtros</button>
    </form>
    {errorFiltro && <p role="alert">{errorFiltro}</p>}
    {cargando && <p role="status">Cargando vinos...</p>}
    {!cargando && error && <div role="alert"><p>{error}</p><button type="button" onClick={() => { setCargando(true); setRevision((n) => n + 1) }}>Reintentar</button></div>}
    {!cargando && !error && datos && <>
      <p>Total: {datos.total}</p>
      {datos.items.length === 0 ? <p>No se encontraron vinos.</p> : <table>
        <thead><tr><th>Código</th><th>Nombre</th><th>Tipo</th><th>Añada</th><th>Volumen (ml)</th><th>Graduación</th><th>Precio</th><th>Bodega (CUIT)</th><th>Acciones</th></tr></thead>
        <tbody>{datos.items.map((v) => <tr key={v.cod_vino}>
          <td>{v.cod_vino}</td><td>{v.nombre}</td><td>{v.tipo}</td><td>{v.anada}</td><td>{v.volumen_ml}</td><td>{v.graduacion}%</td><td>${v.precio}</td><td>{v.cuit_bodega}</td>
          <td><Link to={`/vinos/${v.cod_vino}`}>Ver detalle</Link> | <Link to={`/vinos/${v.cod_vino}/editar`}>Editar</Link></td>
        </tr>)}</tbody>
      </table>}
      <nav aria-label="Paginación de vinos">
        <button type="button" disabled={pagina <= 1} onClick={() => cambiarPagina(pagina - 1)}>Anterior</button>
        <span> Página {datos.pagina} de {totalPaginas} </span>
        <button type="button" disabled={pagina >= totalPaginas} onClick={() => cambiarPagina(pagina + 1)}>Siguiente</button>
      </nav>
    </>}
  </main>
}
