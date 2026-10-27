BEGIN;


-- 1) v_stock_total_por_vino
--
-- Objetivo:
--   Mostrar el stock actual total por vino, sumando stock_deposito y
--   stock_sala de todas las salas.
--
-- Requerimientos:
--   - Incluir TODOS los vinos, incluso sin registros de stock.
--   - Sumar stock_sala de todas las salas sin multiplicar filas por joins 1:N.
--   - Mostrar 0 cuando no existan registros de stock (usar COALESCE).
--   - Respetar tipos (las sumatorias de INTEGER pueden retornar BIGINT).
--
-- Tablas involucradas:
--   - vino (maestro de vinos)
--   - stock_deposito (1:1 con vino)
--   - stock_sala (1:N con vino)
--
-- Estrategia:
--   - Partir de vino como base con LEFT JOIN.
--   - Agregar stock_sala por cod_vino en una CTE para evitar multiplicacion.
--   - Usar COALESCE para convertir NULL a 0.

CREATE OR REPLACE VIEW v_stock_total_por_vino AS
WITH stock_salas_agg AS (
    SELECT 
        cod_vino,
        COALESCE(SUM(cantidad), 0)::BIGINT AS stock_salas
    FROM stock_sala
    GROUP BY cod_vino
)
SELECT 
    v.cod_vino,
    v.nombre        AS nombre_vino,
    v.tipo          AS tipo_vino,
    v.anada,
    v.volumen_ml,
    v.graduacion,
    v.precio,
    v.cuit_bodega,
    COALESCE(sd.cantidad, 0)::INTEGER  AS stock_deposito,
    COALESCE(ssa.stock_salas, 0)::BIGINT AS stock_salas,
    (COALESCE(sd.cantidad, 0) + COALESCE(ssa.stock_salas, 0))::BIGINT AS stock_total
FROM vino v
LEFT JOIN stock_deposito sd ON sd.cod_vino = v.cod_vino
LEFT JOIN stock_salas_agg ssa ON ssa.cod_vino = v.cod_vino;



-- 2) v_ventas_mensuales_por_sala
--
-- Objetivo:
--   Agrupar las ventas (comprobantes) por mes y sala, mostrando indicadores
--   coherentes con la cabecera de COMPROBANTE.
--
-- Requerimientos:
--   - Agrupar por año, mes y sala.
--   - Mostrar total monetario y cantidad de ventas.
--   - Usar los importes ya calculados/sincronizados por triggers de 005.
--   - No aplicar descuentos nuevamente ni unir con renglones_comprobante
--     (evita duplicacion de importes).
--   - No generar meses sin ventas (solo combinaciones con al menos un
--     comprobante).
--
-- Tablas involucradas:
--   - comprobante (cabecera con totales ya sincronizados)
--   - sala_venta (datos de la sala)
--
-- Indicadores:
--   - cantidad_ventas  = COUNT(*) de comprobantes
--   - subtotal_bruto   = SUM(comprobante.subtotal)
--   - descuento_total  = SUM(comprobante.descuento)
--   - total_monetario  = SUM(comprobante.total) (importe neto final)

CREATE OR REPLACE VIEW v_ventas_mensuales_por_sala AS
SELECT 
    s.id_sala,
    s.calle,
    s.numero,
    s.dia_cierre,
    s.id_localidad,
    EXTRACT(YEAR FROM c.fecha)::INTEGER  AS anio,
    EXTRACT(MONTH FROM c.fecha)::INTEGER AS mes,
    DATE_TRUNC('month', c.fecha)::DATE   AS mes_fecha,
    COUNT(*)::BIGINT                    AS cantidad_ventas,
    COALESCE(SUM(c.subtotal), 0)        AS subtotal_bruto,
    COALESCE(SUM(c.descuento), 0)       AS descuento_total,
    COALESCE(SUM(c.total), 0)           AS total_monetario
FROM comprobante c
JOIN sala_venta s ON s.id_sala = c.id_sala
GROUP BY 
    s.id_sala, 
    s.calle, 
    s.numero, 
    s.dia_cierre, 
    s.id_localidad,
    EXTRACT(YEAR FROM c.fecha),
    EXTRACT(MONTH FROM c.fecha),
    DATE_TRUNC('month', c.fecha);


-- 3) v_documentos_pendientes
--
-- Objetivo:
--   Mostrar ingresos y transferencias que aun no estan procesados,
--   identificando tipo, numero, fecha, estado, sala/bodega cuando corresponda.
--
-- Requerimientos:
--   - Combinar con UNION ALL (tipos compatibles).
--   - Incluir documentos en estado 'en_confeccion' y 'terminado'.
--   - Excluir documentos 'procesado'.
--   - Identificar tipo (INGRESO / TRANSFERENCIA), numero, fecha, estado,
--     sala/bodega segun corresponda.
--   - Usar conversiones explicitas para mantener compatibilidad de tipos.
--
-- Tablas involucradas:
--   - ingreso
--   - transferencia
--   - sala_venta (para obtener id_localidad de la sala destino)
--
-- Notas:
--   - ingreso.fecha es DATE; transferencia.fecha_confeccion es DATE.
--   - Para ingresos: cuit_bodega corresponde, id_sala es NULL.
--   - Para transferencias: id_sala corresponde, cuit_bodega es NULL.

CREATE OR REPLACE VIEW v_documentos_pendientes AS
SELECT 
    'INGRESO'::VARCHAR(15)      AS tipo_documento,
    i.cod_ingreso               AS nro_documento,
    i.fecha                     AS fecha,
    i.estado,
    NULL::INTEGER               AS id_sala,
    i.cuit_bodega,
    i.cod_transporte,
    NULL::INTEGER               AS id_localidad_sala
FROM ingreso i
WHERE i.estado <> 'procesado'

UNION ALL

SELECT 
    'TRANSFERENCIA'::VARCHAR(15) AS tipo_documento,
    t.nro_solicitud             AS nro_documento,
    t.fecha_confeccion          AS fecha,
    t.estado,
    t.id_sala,
    NULL::cuit_dom              AS cuit_bodega,
    NULL::INTEGER               AS cod_transporte,
    s.id_localidad              AS id_localidad_sala
FROM transferencia t
JOIN sala_venta s ON s.id_sala = t.id_sala
WHERE t.estado <> 'procesado';

COMMIT;
