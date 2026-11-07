// Detalle de una transferencia: cabecera, estado y renglones.
// Los valores de stock son los que devuelve la API en cada respuesta
// (leidos de PostgreSQL). Esta vista no calcula stock ni decide estados.

import { ETIQUETAS_ESTADO } from './tipos'
import type { TransferenciaDetalle } from './tipos'

type Props = {
  transferencia: TransferenciaDetalle
}

// "2026-11-06" -> "06/11/2026" sin usar Date, para evitar corrimientos
// por zona horaria.
function formatearFecha(fechaIso: string): string {
  const [anio, mes, dia] = fechaIso.split('-')
  return anio && mes && dia ? `${dia}/${mes}/${anio}` : fechaIso
}

const COLORES_ESTADO: Record<TransferenciaDetalle['estado'], string> = {
  en_confeccion: '#175cd3',
  terminado: '#b54708',
  procesado: '#246b45',
}

export default function DetalleTransferencia({ transferencia }: Props) {
  const { nro_solicitud, fecha_confeccion, estado, id_sala, sala, localidad, renglones } =
    transferencia

  return (
    <section aria-label={`Transferencia ${nro_solicitud}`}>
      <h3>Transferencia N.° {nro_solicitud}</h3>

      <p>
        Estado:{' '}
        <strong style={{ color: COLORES_ESTADO[estado] }}>{ETIQUETAS_ESTADO[estado]}</strong>
      </p>
      <p>Fecha de confección: {formatearFecha(fecha_confeccion)}</p>
      <p>
        Sala solicitante: {sala} — {localidad} (sala {id_sala})
      </p>

      <h4>Renglones</h4>
      {renglones.length === 0 ? (
        <p>La transferencia todavía no tiene renglones.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th scope="col">Código</th>
              <th scope="col">Vino</th>
              <th scope="col">Volumen (ml)</th>
              <th scope="col">Cantidad</th>
              <th scope="col">Stock depósito</th>
              <th scope="col">Stock sala</th>
            </tr>
          </thead>
          <tbody>
            {renglones.map((renglon) => (
              <tr key={renglon.cod_vino}>
                <td>{renglon.cod_vino}</td>
                <td>{renglon.vino}</td>
                <td>{renglon.volumen_ml}</td>
                <td>{renglon.cantidad}</td>
                <td>{renglon.stock_deposito}</td>
                <td>{renglon.stock_sala}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
