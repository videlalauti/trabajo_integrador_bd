
import { useEffect, useRef, useState } from 'react'

import { ErrorApi } from '../../lib/api'

import {
  listarClientes,
  listarSalas,
  listarVinos,
  registrarVenta,
} from './servicioVentas'

import type {
  ClienteVenta,
  ComprobanteCrear,
  ComprobanteRespuesta,
  PaginaApi,
  SalaVenta,
  VinoVenta,
} from './tipos'

const TAMANIO_PAGINA = 20

interface RenglonCarrito {
  vino: VinoVenta
  cantidad: number
}

interface ErrorVenta {
  status: number
  codigo: string
  mensaje: string
}

export default function NuevaVenta() {
  // Datos obtenidos de FastAPI.
  const [clientes, setClientes] =
    useState<PaginaApi<ClienteVenta> | null>(null)

  const [vinos, setVinos] =
    useState<PaginaApi<VinoVenta> | null>(null)

  const [salas, setSalas] = useState<SalaVenta[]>([])

  // Paginacion.
  const [paginaClientes, setPaginaClientes] = useState(1)
  const [paginaVinos, setPaginaVinos] = useState(1)

  // Datos seleccionados por el usuario.
  const [idCliente, setIdCliente] = useState('')
  const [idSala, setIdSala] = useState('')
  const [codVino, setCodVino] = useState('')
  const [cantidad, setCantidad] = useState('1')

  // Carrito.
  const [renglones, setRenglones] = useState<RenglonCarrito[]>([])
  const [aviso, setAviso] = useState<string | null>(null)

  // Estado de las consultas.
  const [cargando, setCargando] = useState(true)
  const [errorCarga, setErrorCarga] = useState<string | null>(null)

  // Estado de registro de venta.
  const [registrando, setRegistrando] = useState(false)
  const [errorVenta, setErrorVenta] = useState<ErrorVenta | null>(null)

  // Comprobante definitivo devuelto por FastAPI.
  const [comprobante, setComprobante] =
    useState<ComprobanteRespuesta | null>(null)

  // Proteccion adicional contra solicitudes duplicadas.
  const envioEnCurso = useRef(false)

  // Obtener clientes, vinos y salas de PostgreSQL mediante FastAPI.
  useEffect(() => {
    let vigente = true

    Promise.all([
      listarClientes(paginaClientes, TAMANIO_PAGINA),
      listarVinos(paginaVinos, TAMANIO_PAGINA),
      listarSalas(),
    ])
      .then(([datosClientes, datosVinos, datosSalas]) => {
        if (!vigente) return

        setClientes(datosClientes)
        setVinos(datosVinos)
        setSalas(datosSalas)
        setErrorCarga(null)
      })
      .catch((error: unknown) => {
        if (!vigente) return

        setErrorCarga(
          error instanceof Error
            ? error.message
            : 'No se pudieron cargar los datos.',
        )
      })
      .finally(() => {
        if (vigente) {
          setCargando(false)
        }
      })

    return () => {
      vigente = false
    }
  }, [paginaClientes, paginaVinos])

  function cambiarPaginaClientes(diferencia: number) {
    setIdCliente('')
    setCargando(true)
    setPaginaClientes((actual) => actual + diferencia)
  }

  function cambiarPaginaVinos(diferencia: number) {
    setCodVino('')
    setCargando(true)
    setPaginaVinos((actual) => actual + diferencia)
  }

  function agregarVino() {
    const vino = vinos?.items.find(
      (item) => item.cod_vino === Number(codVino),
    )

    const unidades = Number(cantidad)

    if (!vino) {
      setAviso('Primero seleccioná un vino.')
      return
    }

    if (
      cantidad.trim() === '' ||
      !Number.isSafeInteger(unidades) ||
      unidades <= 0
    ) {
      setAviso('La cantidad debe ser un número entero positivo.')
      return
    }

    if (
      renglones.some(
        (item) => item.vino.cod_vino === vino.cod_vino,
      )
    ) {
      setAviso('Este vino ya está agregado al comprobante.')
      return
    }

    setRenglones((actuales) => [
      ...actuales,
      { vino, cantidad: unidades },
    ])

    setCodVino('')
    setCantidad('1')
    setAviso(null)
    setErrorVenta(null)
  }

  function quitarVino(codigo: number) {
    setRenglones((actuales) =>
      actuales.filter(
        (item) => item.vino.cod_vino !== codigo,
      ),
    )

    setAviso(null)
    setErrorVenta(null)
  }

  async function registrarComprobante() {
    if (envioEnCurso.current || comprobante) {
      return
    }

    const cliente = Number(idCliente)
    const sala = Number(idSala)

    if (!Number.isSafeInteger(cliente) || cliente <= 0) {
      setAviso('Seleccioná un cliente válido.')
      return
    }

    if (!Number.isSafeInteger(sala) || sala <= 0) {
      setAviso('Seleccioná una sala de venta válida.')
      return
    }

    if (renglones.length === 0) {
      setAviso('Agregá al menos un vino al comprobante.')
      return
    }

    const datos: ComprobanteCrear = {
      id_cliente: cliente,
      id_sala: sala,
      renglones: renglones.map((item) => ({
        cod_vino: item.vino.cod_vino,
        cantidad: item.cantidad,
      })),
    }

    envioEnCurso.current = true
    setRegistrando(true)
    setAviso(null)
    setErrorVenta(null)

    try {
      const resultado = await registrarVenta(datos)

      // No calculamos importes: conservamos la respuesta real.
      setComprobante(resultado)
    } catch (error: unknown) {
      if (error instanceof ErrorApi) {
        setErrorVenta({
          status: error.status,
          codigo: error.codigo,
          mensaje: error.message,
        })
      } else {
        setErrorVenta({
          status: 0,
          codigo: 'ERROR_INESPERADO',
          mensaje:
            error instanceof Error
              ? error.message
              : 'No se pudo registrar la venta.',
        })
      }
    } finally {
      envioEnCurso.current = false
      setRegistrando(false)
    }
  }

  function iniciarOtraVenta() {
    setIdCliente('')
    setIdSala('')
    setCodVino('')
    setCantidad('1')
    setRenglones([])
    setAviso(null)
    setErrorVenta(null)
    setComprobante(null)
  }

  return (
    <main>
      <h2>Nueva venta</h2>

      {comprobante ? (
        <section aria-label="Venta registrada">
          <h3>Venta registrada correctamente</h3>

          <p>
            FastAPI confirmó el registro del comprobante
            en PostgreSQL.
          </p>

          <dl>
            <dt>Número de comprobante</dt>
            <dd>{comprobante.nro_comprobante}</dd>

            <dt>Fecha</dt>
            <dd>{comprobante.fecha}</dd>

            <dt>Cliente</dt>
            <dd>{comprobante.id_cliente}</dd>

            <dt>Sala</dt>
            <dd>{comprobante.id_sala}</dd>

            <dt>Subtotal</dt>
            <dd>${comprobante.subtotal}</dd>

            <dt>Descuento</dt>
            <dd>${comprobante.descuento}</dd>

            <dt>Total definitivo</dt>
            <dd>
              <strong>${comprobante.total}</strong>
            </dd>
          </dl>

          <h4>Detalle del comprobante</h4>

          <table>
            <thead>
              <tr>
                <th>Vino</th>
                <th>Cantidad</th>
                <th>Precio unitario</th>
                <th>Descuento</th>
                <th>Subtotal</th>
              </tr>
            </thead>

            <tbody>
              {comprobante.renglones.map((renglon) => (
                <tr key={renglon.cod_vino}>
                  <td>{renglon.cod_vino}</td>
                  <td>{renglon.cantidad}</td>
                  <td>${renglon.precio_unitario}</td>
                  <td>{renglon.descuento}%</td>
                  <td>${renglon.subtotal}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p>
            Los importes fueron obtenidos del backend.
            No se calcularon en el navegador.
          </p>

          <button
            type="button"
            onClick={iniciarOtraVenta}
          >
            Registrar otra venta
          </button>
        </section>
      ) : (
        <>
          <p>
            Seleccioná un cliente, una sala y los vinos
            que se incluirán en el comprobante.
          </p>

          {cargando && (
            <p>Cargando datos desde FastAPI...</p>
          )}

          {errorCarga && (
            <div role="alert">
              <strong>Error al cargar datos: </strong>
              {errorCarga}
            </div>
          )}

          {/* CLIENTES */}
          <section>
            <h3>1. Seleccionar cliente</h3>

            <label htmlFor="cliente-venta">
              Cliente
            </label>

            <select
              id="cliente-venta"
              value={idCliente}
              onChange={(evento) =>
                setIdCliente(evento.target.value)
              }
              disabled={cargando || registrando || !clientes}
            >
              <option value="">
                Seleccionar cliente
              </option>

              {clientes?.items.map((cliente) => (
                <option
                  key={cliente.id_cliente}
                  value={cliente.id_cliente}
                >
                  {cliente.id_cliente}
                  {' - '}
                  {cliente.nombre_razon_social}
                </option>
              ))}
            </select>

            <p>Página {paginaClientes}</p>

            <button
              type="button"
              disabled={
                cargando ||
                registrando ||
                paginaClientes === 1
              }
              onClick={() => cambiarPaginaClientes(-1)}
            >
              Anterior
            </button>

            <button
              type="button"
              disabled={
                cargando ||
                registrando ||
                !clientes ||
                paginaClientes * TAMANIO_PAGINA >= clientes.total
              }
              onClick={() => cambiarPaginaClientes(1)}
            >
              Siguiente
            </button>
          </section>

          <hr />

          {/* SALAS */}
          <section>
            <h3>2. Seleccionar sala de venta</h3>

            <label htmlFor="sala-venta">
              Sala
            </label>

            <select
              id="sala-venta"
              value={idSala}
              onChange={(evento) =>
                setIdSala(evento.target.value)
              }
              disabled={cargando || registrando}
            >
              <option value="">
                Seleccionar sala
              </option>

              {salas.map((sala) => (
                <option
                  key={sala.id_sala}
                  value={sala.id_sala}
                >
                  {sala.id_sala}
                  {' - '}
                  {sala.calle} {sala.numero}
                  {' - '}
                  {sala.localidad}
                </option>
              ))}
            </select>
          </section>

          <hr />

          {/* VINOS */}
          <section>
            <h3>3. Seleccionar vinos</h3>

            <label htmlFor="vino-venta">
              Vino
            </label>

            <select
              id="vino-venta"
              value={codVino}
              onChange={(evento) =>
                setCodVino(evento.target.value)
              }
              disabled={cargando || registrando || !vinos}
            >
              <option value="">
                Seleccionar vino
              </option>

              {vinos?.items.map((vino) => (
                <option
                  key={vino.cod_vino}
                  value={vino.cod_vino}
                >
                  {vino.cod_vino}
                  {' - '}
                  {vino.nombre}
                  {' - '}
                  ${vino.precio}
                </option>
              ))}
            </select>

            <p>Página {paginaVinos}</p>

            <button
              type="button"
              disabled={
                cargando ||
                registrando ||
                paginaVinos === 1
              }
              onClick={() => cambiarPaginaVinos(-1)}
            >
              Anterior
            </button>

            <button
              type="button"
              disabled={
                cargando ||
                registrando ||
                !vinos ||
                paginaVinos * TAMANIO_PAGINA >= vinos.total
              }
              onClick={() => cambiarPaginaVinos(1)}
            >
              Siguiente
            </button>

            <div>
              <p>
                <label htmlFor="cantidad-vino">
                  Cantidad de botellas
                </label>
              </p>

              <input
                id="cantidad-vino"
                type="number"
                min="1"
                step="1"
                value={cantidad}
                onChange={(evento) =>
                  setCantidad(evento.target.value)
                }
                disabled={cargando || registrando}
              />

              <button
                type="button"
                onClick={agregarVino}
                disabled={cargando || registrando || !codVino}
              >
                Agregar vino
              </button>
            </div>
          </section>

          <hr />

          {/* CARRITO */}
          <section>
            <h3>4. Renglones del comprobante</h3>

            {aviso && (
              <p role="alert">{aviso}</p>
            )}

            {renglones.length === 0 ? (
              <p>Todavía no agregaste ningún vino.</p>
            ) : (
              <ul>
                {renglones.map((item) => (
                  <li key={item.vino.cod_vino}>
                    <strong>{item.vino.nombre}</strong>

                    {' - '}
                    Cantidad: {item.cantidad}

                    {' - '}
                    Precio de referencia: ${item.vino.precio}

                    {' '}

                    <button
                      type="button"
                      disabled={registrando}
                      onClick={() =>
                        quitarVino(item.vino.cod_vino)
                      }
                    >
                      Quitar
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <hr />

          {/* REGISTRO */}
          <section>
            <h3>5. Registrar comprobante</h3>

            <p>
              PostgreSQL calculará los importes definitivos
              y comprobará el stock disponible.
            </p>

            {errorVenta && (
              <div role="alert">
                <h4>La venta no pudo registrarse</h4>

                <p>
                  Estado HTTP: {errorVenta.status}
                </p>

                <p>
                  Código: {errorVenta.codigo}
                </p>

                <p>
                  <strong>{errorVenta.mensaje}</strong>
                </p>

                {errorVenta.status === 409 && (
                  <p>
                    La venta fue rechazada por una regla
                    de negocio. Revisá el mensaje de
                    PostgreSQL antes de volver a intentar.
                  </p>
                )}
              </div>
            )}

            <button
              type="button"
              onClick={registrarComprobante}
              disabled={
                cargando ||
                registrando ||
                !idCliente ||
                !idSala ||
                renglones.length === 0
              }
            >
              {registrando
                ? 'Registrando venta...'
                : 'Registrar venta'}
            </button>
          </section>
        </>
      )}
    </main>
  )
}
