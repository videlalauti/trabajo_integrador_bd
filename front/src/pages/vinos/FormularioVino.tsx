import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ErrorApi, solicitarApi } from '../../lib/api'
import type { Bodega, Cepa, Maridaje, TipoVino, VinoFormulario } from './tipos'

type Campos = {
  nombre: string; tipo: TipoVino; anada: string; volumen_ml: string
  graduacion: string; precio: string; cuit_bodega: string
  cepas: { id_cepa: string; porcentaje: string }[]; maridajes: number[]
}
const vacio = (): Campos => ({ nombre: '', tipo: 'tinto', anada: '', volumen_ml: '750', graduacion: '', precio: '', cuit_bodega: '', cepas: [{ id_cepa: '', porcentaje: '100' }], maridajes: [] })
const entero = (valor: string) => valor.trim() !== '' && Number.isSafeInteger(Number(valor))
const decimal = (valor: string, decimales: number) => new RegExp(`^\\d+(?:\\.\\d{1,${decimales}})?$`).test(valor)

export default function FormularioVino({ inicial, titulo, guardar }: {
  inicial?: VinoFormulario
  titulo: string
  guardar: (datos: VinoFormulario) => Promise<void>
}) {
  const [campos, setCampos] = useState<Campos>(() => inicial ? {
    nombre: inicial.nombre, tipo: inicial.tipo, anada: String(inicial.anada), volumen_ml: String(inicial.volumen_ml),
    graduacion: String(inicial.graduacion), precio: String(inicial.precio), cuit_bodega: inicial.cuit_bodega,
    cepas: inicial.cepas.map((c) => ({ id_cepa: String(c.id_cepa), porcentaje: String(c.porcentaje) })),
    maridajes: [...inicial.maridajes],
  } : vacio())
  const [bodegas, setBodegas] = useState<Bodega[]>([])
  const [cepas, setCepas] = useState<Cepa[]>([])
  const [maridajes, setMaridajes] = useState<Maridaje[]>([])
  const [cargandoCatalogos, setCargandoCatalogos] = useState(true)
  const [errorCatalogos, setErrorCatalogos] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    let activo = true
    async function cargar() {
      try {
        const [b, c, m] = await Promise.all([
          solicitarApi<Bodega[]>('/bodegas'), solicitarApi<Cepa[]>('/cepas'), solicitarApi<Maridaje[]>('/maridajes'),
        ])
        if (activo) { setBodegas(b); setCepas(c); setMaridajes(m); setErrorCatalogos(null) }
      } catch (err: unknown) {
        if (activo) setErrorCatalogos(err instanceof ErrorApi ? err.message : 'No se pudieron cargar los catálogos.')
      } finally {
        if (activo) setCargandoCatalogos(false)
      }
    }
    void cargar()
    return () => { activo = false }
  }, [revision])

  function actualizar<K extends keyof Campos>(clave: K, valor: Campos[K]) {
    setCampos((actual) => ({ ...actual, [clave]: valor }))
  }
  function actualizarCepa(indice: number, campo: 'id_cepa' | 'porcentaje', valor: string) {
    setCampos((actual) => ({ ...actual, cepas: actual.cepas.map((c, i) => i === indice ? { ...c, [campo]: valor } : c) }))
  }
  function validar(): string | null {
    if (!campos.nombre.trim() || campos.nombre.length > 150) return 'El nombre debe tener entre 1 y 150 caracteres.'
    if (!entero(campos.anada)) return 'La añada debe ser un número entero.'
    if (!entero(campos.volumen_ml) || Number(campos.volumen_ml) <= 0) return 'El volumen debe ser un entero positivo.'
    if (!decimal(campos.graduacion, 2) || Number(campos.graduacion) < 5 || Number(campos.graduacion) > 20 || campos.graduacion.replace('.', '').length > 4) return 'La graduación debe estar entre 5 y 20, con hasta dos decimales.'
    if (!decimal(campos.precio, 2) || Number(campos.precio) <= 0 || campos.precio.replace('.', '').length > 14) return 'El precio debe ser positivo y tener hasta dos decimales.'
    if (!/^\d{11}$/.test(campos.cuit_bodega)) return 'Seleccioná una bodega con CUIT válido.'
    if (campos.cepas.length === 0) return 'Agregá al menos una cepa.'
    const ids = new Set<number>()
    let totalCentavos = 0
    for (const c of campos.cepas) {
      if (!entero(c.id_cepa) || Number(c.id_cepa) <= 0 || !cepas.some((op) => op.id_cepa === Number(c.id_cepa))) return 'Seleccioná una cepa válida.'
      if (ids.has(Number(c.id_cepa))) return 'No repitas una misma cepa.'
      ids.add(Number(c.id_cepa))
      if (!decimal(c.porcentaje, 2) || Number(c.porcentaje) <= 0 || Number(c.porcentaje) > 100) return 'Cada porcentaje debe ser mayor que 0 y como máximo 100, con hasta dos decimales.'
      totalCentavos += Math.round(Number(c.porcentaje) * 100)
    }
    if (totalCentavos !== 10000) return 'Los porcentajes de cepas deben sumar exactamente 100%.'
    return null
  }
  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault()
    const mensaje = validar()
    if (mensaje) { setError(mensaje); return }
    const datos: VinoFormulario = {
      nombre: campos.nombre.trim(), tipo: campos.tipo, anada: Number(campos.anada), volumen_ml: Number(campos.volumen_ml),
      graduacion: campos.graduacion, precio: campos.precio, cuit_bodega: campos.cuit_bodega,
      cepas: campos.cepas.map((c) => ({ id_cepa: Number(c.id_cepa), porcentaje: c.porcentaje })),
      maridajes: campos.maridajes,
    }
    setError(null); setGuardando(true)
    try { await guardar(datos) }
    catch (err: unknown) { setError(err instanceof ErrorApi ? `${err.codigo}: ${err.message}` : err instanceof Error ? err.message : 'Error inesperado al guardar.') }
    finally { setGuardando(false) }
  }

  return <section>
    <h2>{titulo}</h2>
    {cargandoCatalogos && <p role="status">Cargando catálogos...</p>}
    {errorCatalogos && <div role="alert"><p>{errorCatalogos}</p><button type="button" onClick={() => { setCargandoCatalogos(true); setRevision((n) => n + 1) }}>Reintentar catálogos</button></div>}
    {!cargandoCatalogos && !errorCatalogos && <form onSubmit={enviar}>
      <div><label htmlFor="nombre-vino">Nombre</label><input id="nombre-vino" required maxLength={150} value={campos.nombre} onChange={(e) => actualizar('nombre', e.target.value)} /></div>
      <div><label htmlFor="tipo-vino">Tipo</label><select id="tipo-vino" value={campos.tipo} onChange={(e) => actualizar('tipo', e.target.value as TipoVino)}>{(['tinto', 'blanco', 'rosado', 'espumante'] as const).map((t) => <option key={t} value={t}>{t}</option>)}</select></div>
      <div><label htmlFor="anada-vino">Añada</label><input id="anada-vino" type="number" required step="1" value={campos.anada} onChange={(e) => actualizar('anada', e.target.value)} /></div>
      <div><label htmlFor="volumen-vino">Volumen (ml)</label><input id="volumen-vino" type="number" required min="1" step="1" value={campos.volumen_ml} onChange={(e) => actualizar('volumen_ml', e.target.value)} /></div>
      <div><label htmlFor="graduacion-vino">Graduación (%)</label><input id="graduacion-vino" type="number" required min="5" max="20" step="0.01" value={campos.graduacion} onChange={(e) => actualizar('graduacion', e.target.value)} /></div>
      <div><label htmlFor="precio-vino">Precio</label><input id="precio-vino" type="number" required min="0.01" step="0.01" value={campos.precio} onChange={(e) => actualizar('precio', e.target.value)} /></div>
      <div><label htmlFor="bodega-vino">Bodega</label><select id="bodega-vino" required value={campos.cuit_bodega} onChange={(e) => actualizar('cuit_bodega', e.target.value)}><option value="">Seleccionar bodega</option>{bodegas.map((b) => <option key={b.cuit} value={b.cuit}>{b.razon_social} ({b.cuit})</option>)}</select></div>
      <fieldset><legend>Cepas (total 100%)</legend>
        {campos.cepas.map((c, i) => <div key={i}>
          <label htmlFor={`cepa-${i}`}>Cepa {i + 1}</label>
          <select id={`cepa-${i}`} required value={c.id_cepa} onChange={(e) => actualizarCepa(i, 'id_cepa', e.target.value)}><option value="">Seleccionar cepa</option>{cepas.map((op) => <option key={op.id_cepa} value={op.id_cepa}>{op.nombre} ({op.tipo})</option>)}</select>
          <label htmlFor={`porcentaje-${i}`}>Porcentaje</label>
          <input id={`porcentaje-${i}`} required type="number" min="0.01" max="100" step="0.01" value={c.porcentaje} onChange={(e) => actualizarCepa(i, 'porcentaje', e.target.value)} />
          <button type="button" disabled={campos.cepas.length === 1} onClick={() => actualizar('cepas', campos.cepas.filter((_, indice) => indice !== i))}>Quitar cepa</button>
        </div>)}
        <button type="button" onClick={() => actualizar('cepas', [...campos.cepas, { id_cepa: '', porcentaje: '' }])}>Agregar cepa</button>
      </fieldset>
      <fieldset><legend>Maridajes (opcionales)</legend>
        {maridajes.map((m) => <label key={m.id_maridaje} style={{ display: 'block' }}>
          <input type="checkbox" checked={campos.maridajes.includes(m.id_maridaje)} onChange={(e) => actualizar('maridajes', e.target.checked ? [...campos.maridajes, m.id_maridaje] : campos.maridajes.filter((id) => id !== m.id_maridaje))} />
          {m.nombre} ({m.temperatura_servicio_c} °C)
        </label>)}
      </fieldset>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={guardando}>{guardando ? 'Guardando...' : 'Guardar vino'}</button>
    </form>}
  </section>
}
