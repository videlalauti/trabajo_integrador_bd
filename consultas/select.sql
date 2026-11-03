-- S1 | Responsable: Lautaro | Origen: fase5/evidencias/lautaro/s1.sql
-- S1: Ranking de los 10 vinos con mayor cantidad
-- de botellas vendidas en toda la red de salas.

SELECT
    v.cod_vino,
    v.nombre AS vino,
    v.tipo,
    SUM(rc.cantidad) AS botellas_vendidas
FROM renglon_comprobante rc
JOIN comprobante c
    ON c.nro_comprobante = rc.nro_comprobante
JOIN sala_venta s
    ON s.id_sala = c.id_sala
JOIN vino v
    ON v.cod_vino = rc.cod_vino
GROUP BY
    v.cod_vino,
    v.nombre,
    v.tipo
ORDER BY
    botellas_vendidas DESC,
    v.cod_vino ASC
LIMIT 10;


-- S2 | Responsable: Valentino | Origen: fase5/evidencias/valentino/S2.sql
-- S2. Codigos y nombres de vinos vendidos en todas las salas.

SELECT
    v.cod_vino,
    v.nombre
FROM vino AS v
WHERE NOT EXISTS (
    SELECT 1
    FROM sala_venta AS s
    WHERE NOT EXISTS (
        SELECT 1
        FROM comprobante AS c
        JOIN renglon_comprobante AS rc
            ON rc.nro_comprobante = c.nro_comprobante
        WHERE c.id_sala = s.id_sala
          AND rc.cod_vino = v.cod_vino
    )
)
ORDER BY v.cod_vino;

-- Control de cobertura: los 10 vinos presentes en mas salas distintas.
-- Permite contrastar el resultado con el total de salas existentes.
SELECT
    v.cod_vino,
    v.nombre,
    COUNT(DISTINCT c.id_sala) AS salas_con_ventas
FROM vino AS v
JOIN renglon_comprobante AS rc
    ON rc.cod_vino = v.cod_vino
JOIN comprobante AS c
    ON c.nro_comprobante = rc.nro_comprobante
GROUP BY v.cod_vino, v.nombre
ORDER BY salas_con_ventas DESC, v.cod_vino
LIMIT 10;

SELECT COUNT(*) AS total_salas FROM sala_venta;


-- S3 | Responsable: Fabricio | Origen: fase5/evidencias/fabricio/S3.sql
-- S3 - Clientes por tipo que compraron en la ultima semana

-- S3: consulta principal.
SELECT
    c.tipo_cliente,
    COUNT(DISTINCT c.id_cliente) AS cantidad_clientes
FROM public.comprobante co
JOIN public.cliente c
    ON c.id_cliente = co.id_cliente
WHERE co.id_sala = 1
  AND co.fecha >= CURRENT_DATE - INTERVAL '6 days'
  AND co.fecha < CURRENT_DATE + INTERVAL '1 day'
GROUP BY c.tipo_cliente
ORDER BY c.tipo_cliente;

-- S3: plan de ejecucion real.
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.tipo_cliente,
    COUNT(DISTINCT c.id_cliente) AS cantidad_clientes
FROM public.comprobante co
JOIN public.cliente c
    ON c.id_cliente = co.id_cliente
WHERE co.id_sala = 1
  AND co.fecha >= CURRENT_DATE - INTERVAL '6 days'
  AND co.fecha < CURRENT_DATE + INTERVAL '1 day'
GROUP BY c.tipo_cliente
ORDER BY c.tipo_cliente;


-- S4 | Responsable: Jose | Origen: fase5/evidencias/jose/S4.sql
-- S4: Top 5 de salas que solicitaron mayor cantidad del vino
-- 681 durante los ultimos 15 dias.

SELECT
    t.id_sala,
    SUM(rt.cantidad) AS botellas_solicitadas
FROM public.transferencia AS t
JOIN public.renglon_transferencia AS rt
    ON rt.nro_solicitud = t.nro_solicitud
WHERE rt.cod_vino = 681
  AND t.fecha_confeccion >= CURRENT_DATE - INTERVAL '15 days'
  AND t.fecha_confeccion < CURRENT_DATE + INTERVAL '1 day'
GROUP BY t.id_sala
ORDER BY botellas_solicitadas DESC, t.id_sala
LIMIT 5;

-- Plan de ejecucion.
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    t.id_sala,
    SUM(rt.cantidad) AS botellas_solicitadas
FROM public.transferencia AS t
JOIN public.renglon_transferencia AS rt
    ON rt.nro_solicitud = t.nro_solicitud
WHERE rt.cod_vino = 681
  AND t.fecha_confeccion >= CURRENT_DATE - INTERVAL '15 days'
  AND t.fecha_confeccion < CURRENT_DATE + INTERVAL '1 day'
GROUP BY t.id_sala
ORDER BY botellas_solicitadas DESC, t.id_sala
LIMIT 5;


-- S5 | Responsable: Valentino | Origen: fase5/evidencias/valentino/S5.sql
-- S5. Salas con la menor cantidad de transferencias pendientes.

WITH pendientes_por_sala AS (
    SELECT
        s.id_sala,
        s.calle,
        s.numero,
        COUNT(t.nro_solicitud) AS transferencias_pendientes
    FROM sala_venta AS s
    LEFT JOIN transferencia AS t
        ON t.id_sala = s.id_sala
       AND t.estado <> 'procesado'
    GROUP BY s.id_sala, s.calle, s.numero
)
SELECT
    id_sala,
    calle,
    numero,
    transferencias_pendientes
FROM pendientes_por_sala
WHERE transferencias_pendientes = (
    SELECT MIN(transferencias_pendientes)
    FROM pendientes_por_sala
)
ORDER BY id_sala;

-- Control independiente: cantidad global de salas y de pendientes.
SELECT
    (SELECT COUNT(*) FROM sala_venta) AS total_salas,
    (SELECT COUNT(*) FROM transferencia
     WHERE estado <> 'procesado') AS total_pendientes;

-- Control adicional de estados:
SELECT estado, COUNT(*) AS cantidad
FROM transferencia
GROUP BY estado
ORDER BY estado;


-- S6 | Responsable: Antonio | Origen: fase5/evidencias/antonio/S6.sql
-- S6 - Para una sala determinada, los vinos sin stock en la sala pero
--      con stock en el deposito central.

-- Control 1: la sala del parametro existe
SELECT s.id_sala, s.calle, s.numero, l.nombre AS localidad
FROM sala_venta AS s
JOIN localidad  AS l ON l.id_localidad = s.id_localidad
WHERE s.id_sala = 1;                                   -- PARAMETRO

-- Control 2: composicion del stock para esa sala
SELECT
  (SELECT count(*) FROM vino)                                          AS vinos_total,
  (SELECT count(*) FROM stock_deposito WHERE cantidad > 0)             AS vinos_con_stock_deposito,
  (SELECT count(*) FROM stock_sala WHERE id_sala = 1 AND cantidad > 0) AS vinos_con_stock_en_sala,   -- PARAMETRO
  (SELECT count(*) FROM stock_sala WHERE id_sala = 1 AND cantidad = 0) AS vinos_con_fila_en_cero,    -- PARAMETRO
  (SELECT count(*) FROM vino v
     WHERE NOT EXISTS (SELECT 1 FROM stock_sala ss
                       WHERE ss.id_sala = 1 AND ss.cod_vino = v.cod_vino)) AS vinos_sin_fila_en_sala; -- PARAMETRO

-- ---------------------------------------------------------------------
-- Consulta de la consigna
-- ---------------------------------------------------------------------
SELECT v.cod_vino,
       v.nombre,
       v.tipo,
       v.anada,
       v.volumen_ml,
       fn_stock_sala(1, v.cod_vino) AS stock_sala,                    -- PARAMETRO
       CASE WHEN EXISTS (SELECT 1 FROM stock_sala ss
                         WHERE ss.id_sala = 1 AND ss.cod_vino = v.cod_vino)  -- PARAMETRO
            THEN 'fila con cantidad 0'
            ELSE 'sin fila en stock_sala'
       END AS situacion_sala,
       sd.cantidad AS stock_deposito
FROM vino AS v
JOIN stock_deposito AS sd
  ON sd.cod_vino = v.cod_vino
 AND sd.cantidad > 0
WHERE NOT EXISTS (
    SELECT 1
    FROM stock_sala AS ss
    WHERE ss.id_sala = 1                                 -- PARAMETRO
      AND ss.cod_vino = v.cod_vino
      AND ss.cantidad > 0
)
ORDER BY sd.cantidad DESC, v.cod_vino;

-- Control 3: cantidad de filas del resultado
SELECT count(*) AS vinos_resultado
FROM vino AS v
JOIN stock_deposito AS sd ON sd.cod_vino = v.cod_vino AND sd.cantidad > 0
WHERE NOT EXISTS (SELECT 1 FROM stock_sala AS ss
                  WHERE ss.id_sala = 1 AND ss.cod_vino = v.cod_vino AND ss.cantidad > 0);  -- PARAMETRO



-- S7 | Responsable: Lautaro | Origen: fase5/evidencias/lautaro/s7.sql
-- S7: Empresa de transporte con mayor actividad
-- en el ultimo mes.

SELECT
    t.cod_transporte,
    t.razon_social,
    COUNT(i.cod_ingreso) AS cantidad_ingresos
FROM transportista t
JOIN ingreso i
    ON i.cod_transporte = t.cod_transporte
WHERE i.fecha >= CURRENT_DATE - INTERVAL '1 month'
  AND i.fecha <= CURRENT_DATE
GROUP BY
    t.cod_transporte,
    t.razon_social
ORDER BY
    cantidad_ingresos DESC,
    t.cod_transporte ASC
LIMIT 1;


-- S8 | Responsable: Valentino | Origen: fase5/evidencias/valentino/S8.sql
-- S8. Total de ventas por sala durante el ultimo trimestre, ordenado
-- de mayor a menor importe.

SELECT
    s.id_sala,
    s.calle,
    s.numero,
    COALESCE(SUM(c.total), 0) AS total_ventas
FROM sala_venta s
LEFT JOIN comprobante c
    ON c.id_sala = s.id_sala
   AND c.fecha >= CURRENT_DATE - INTERVAL '3 months'
   AND c.fecha < CURRENT_DATE + INTERVAL '1 day'
GROUP BY s.id_sala, s.calle, s.numero
ORDER BY total_ventas DESC, s.id_sala;

-- Control independiente del numero de comprobantes y del importe global.
SELECT
    COUNT(*) AS comprobantes_trimestre,
    COALESCE(SUM(total), 0) AS total_general
FROM comprobante
WHERE fecha >= CURRENT_DATE - INTERVAL '3 months'
  AND fecha < CURRENT_DATE + INTERVAL '1 day';



-- S9 | Responsable: Lautaro | Origen: fase5/evidencias/lautaro/s9.sql
-- S9: Ficha de un vino.

CREATE OR REPLACE VIEW vw_ficha_vino AS
WITH composicion AS (
    SELECT
        vc.cod_vino,
        STRING_AGG(
            ce.nombre || ' (' || vc.porcentaje || '%)',
            ', ' ORDER BY ce.nombre
        ) AS cepas
    FROM vino_cepa vc
    JOIN cepa ce ON ce.id_cepa = vc.id_cepa
    GROUP BY vc.cod_vino
),
maridajes AS (
    SELECT
        vm.cod_vino,
        STRING_AGG(
            m.nombre,
            ', ' ORDER BY m.nombre
        ) AS maridajes
    FROM vino_maridaje vm
    JOIN maridaje m ON m.id_maridaje = vm.id_maridaje
    GROUP BY vm.cod_vino
),
stock_salas AS (
    SELECT
        cod_vino,
        SUM(cantidad) AS cantidad
    FROM stock_sala
    GROUP BY cod_vino
)
SELECT
    v.cod_vino,
    v.nombre AS vino,
    v.tipo,
    v.anada,
    b.razon_social AS bodega,
    c.cepas,
    m.maridajes,
    COALESCE(sd.cantidad, 0) AS stock_deposito,
    COALESCE(ss.cantidad, 0) AS stock_salas,
    COALESCE(sd.cantidad, 0)
        + COALESCE(ss.cantidad, 0) AS stock_total
FROM vino v
JOIN bodega b ON b.cuit = v.cuit_bodega
LEFT JOIN composicion c ON c.cod_vino = v.cod_vino
LEFT JOIN maridajes m ON m.cod_vino = v.cod_vino
LEFT JOIN stock_deposito sd ON sd.cod_vino = v.cod_vino
LEFT JOIN stock_salas ss ON ss.cod_vino = v.cod_vino;

-- S9: Consultar la ficha del vino seleccionado.
-- Cambiar cod_vino = 1 por el codigo que se desee consultar.

SELECT *
FROM vw_ficha_vino
WHERE cod_vino = 1;



-- S10 | Responsable: Antonio | Origen: fase5/evidencias/antonio/S10.sql
-- S10 - Rendimiento en kg por hectarea de cada parcela y campania, e
--       identificar las parcelas que rinden menos que el promedio de su
--       finca.

-- PARTE 1 - Rendimiento kg/ha de cada parcela y campania
WITH rendimiento AS (
    SELECT l.id_finca,
           l.nro_parcela,
           l.campania,
           l.kg_cosechados,
           p.superficie_ha,
           l.kg_cosechados / p.superficie_ha AS kg_por_ha
    FROM lote_uva AS l
    JOIN parcela  AS p
      ON p.id_finca = l.id_finca
     AND p.nro_parcela = l.nro_parcela
)
SELECT r.id_finca,
       f.nombre AS finca,
       r.nro_parcela,
       r.campania,
       r.kg_cosechados,
       r.superficie_ha,
       ROUND(r.kg_por_ha, 2) AS kg_por_ha
FROM rendimiento AS r
JOIN finca AS f ON f.id_finca = r.id_finca
ORDER BY r.id_finca, r.nro_parcela, r.campania;

-- PARTE 2 - Parcelas que rinden menos que el promedio de su finca
--           (en la misma campania)
WITH rendimiento AS (
    SELECT l.id_finca,
           l.nro_parcela,
           l.campania,
           l.kg_cosechados / p.superficie_ha AS kg_por_ha
    FROM lote_uva AS l
    JOIN parcela  AS p
      ON p.id_finca = l.id_finca
     AND p.nro_parcela = l.nro_parcela
),
comparacion AS MATERIALIZED (
    SELECT r.id_finca,
           r.nro_parcela,
           r.campania,
           r.kg_por_ha,
           -- Subconsulta correlacionada: promedio de la finca y campania
           -- de la fila externa r
           (SELECT AVG(r2.kg_por_ha)
            FROM rendimiento AS r2
            WHERE r2.id_finca = r.id_finca
              AND r2.campania = r.campania) AS promedio_finca
    FROM rendimiento AS r
)
SELECT c.id_finca,
       f.nombre AS finca,
       c.nro_parcela,
       c.campania,
       ROUND(c.kg_por_ha, 2)                      AS kg_por_ha,
       ROUND(c.promedio_finca, 2)                 AS promedio_finca_campania,
       ROUND(c.promedio_finca - c.kg_por_ha, 2)   AS diferencia_kg_por_ha
FROM comparacion AS c
JOIN finca AS f ON f.id_finca = c.id_finca
WHERE c.kg_por_ha < c.promedio_finca
ORDER BY c.id_finca, c.campania, c.nro_parcela;


-- CONTROLES
-- Control 1: filas de la parte 1 (debe coincidir con la cantidad de lotes)
SELECT (SELECT count(*) FROM lote_uva) AS lotes,
       (SELECT count(*) FROM lote_uva l
          JOIN parcela p ON p.id_finca = l.id_finca AND p.nro_parcela = l.nro_parcela)
                                       AS filas_parte_1;

-- Control 2: filas de la parte 2 por subconsulta correlacionada y por
-- funcion de ventana (verificacion cruzada: deben ser iguales)
WITH rendimiento AS (
    SELECT l.id_finca, l.nro_parcela, l.campania,
           l.kg_cosechados / p.superficie_ha AS kg_por_ha
    FROM lote_uva l
    JOIN parcela p ON p.id_finca = l.id_finca AND p.nro_parcela = l.nro_parcela
)
SELECT
  (SELECT count(*) FROM rendimiento r
    WHERE r.kg_por_ha < (SELECT AVG(r2.kg_por_ha) FROM rendimiento r2
                         WHERE r2.id_finca = r.id_finca AND r2.campania = r.campania))
                                                              AS filas_parte_2_correlacionada,
  (SELECT count(*) FROM (
      SELECT r.kg_por_ha,
             AVG(r.kg_por_ha) OVER (PARTITION BY r.id_finca, r.campania) AS prom
      FROM rendimiento r) x
    WHERE x.kg_por_ha < x.prom)                               AS filas_parte_2_ventana;


-- S11 | Responsable: Fabricio | Origen: fase5/evidencias/fabricio/S11.sql
-- S11 - Ranking de vinos y ventas acumuladas mensuales

-- S11-A: Ranking de vinos dentro de cada sala

WITH botellas_por_vino AS (
    SELECT
        co.id_sala,
        r.cod_vino,
        SUM(r.cantidad) AS botellas_vendidas
    FROM public.comprobante co
    JOIN public.renglon_comprobante r
        ON r.nro_comprobante = co.nro_comprobante
    GROUP BY co.id_sala, r.cod_vino
)
SELECT
    b.id_sala,
    b.cod_vino,
    v.nombre AS nombre_vino,
    b.botellas_vendidas,
    RANK() OVER (
        PARTITION BY b.id_sala
        ORDER BY b.botellas_vendidas DESC
    ) AS posicion_ranking
FROM botellas_por_vino b
JOIN public.vino v
    ON v.cod_vino = b.cod_vino
ORDER BY
    b.id_sala,
    posicion_ranking,
    b.cod_vino;


-- S11-B: Ventas acumuladas mensuales por sala

WITH ventas_mensuales AS (
    SELECT
        co.id_sala,
        DATE_TRUNC('month', co.fecha)::date AS mes,
        COUNT(*) AS comprobantes_mes,
        SUM(co.total) AS ventas_mes
    FROM public.comprobante co
    GROUP BY
        co.id_sala,
        DATE_TRUNC('month', co.fecha)::date
)
SELECT
    id_sala,
    mes,
    comprobantes_mes,
    ventas_mes,
    SUM(ventas_mes) OVER (
        PARTITION BY id_sala
        ORDER BY mes
        ROWS BETWEEN UNBOUNDED PRECEDING
                 AND CURRENT ROW
    ) AS ventas_acumuladas
FROM ventas_mensuales
ORDER BY id_sala, mes;



-- S12 | Responsable: Jose | Origen: fase5/evidencias/jose/S12.sql
-- S12: Consultas con NOT EXISTS.

-- S12-A: Clientes que compraron TODOS los vinos de una
-- bodega determinada.

SELECT
    c.id_cliente,
    c.nombre_razon_social
FROM public.cliente AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM public.vino AS v
    WHERE v.cuit_bodega = '30999000203'
      AND NOT EXISTS (
          SELECT 1
          FROM public.comprobante AS cp
          JOIN public.renglon_comprobante AS rc
            ON rc.nro_comprobante = cp.nro_comprobante
          WHERE cp.id_cliente = c.id_cliente
            AND rc.cod_vino = v.cod_vino
      )
)
ORDER BY c.id_cliente;

-- Plan de ejecucion S12-A.
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id_cliente,
    c.nombre_razon_social
FROM public.cliente AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM public.vino AS v
    WHERE v.cuit_bodega = '30999000203'
      AND NOT EXISTS (
          SELECT 1
          FROM public.comprobante AS cp
          JOIN public.renglon_comprobante AS rc
            ON rc.nro_comprobante = cp.nro_comprobante
          WHERE cp.id_cliente = c.id_cliente
            AND rc.cod_vino = v.cod_vino
      )
)
ORDER BY c.id_cliente;


-- S12-B: Clientes que NUNCA compraron vinos tintos.

SELECT
    c.id_cliente,
    c.nombre_razon_social
FROM public.cliente AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM public.comprobante AS cp
    JOIN public.renglon_comprobante AS rc
      ON rc.nro_comprobante = cp.nro_comprobante
    JOIN public.vino AS v
      ON v.cod_vino = rc.cod_vino
    WHERE cp.id_cliente = c.id_cliente
      AND v.tipo = 'tinto'
)
ORDER BY c.id_cliente;

-- Plan de ejecucion S12-B.
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id_cliente,
    c.nombre_razon_social
FROM public.cliente AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM public.comprobante AS cp
    JOIN public.renglon_comprobante AS rc
      ON rc.nro_comprobante = cp.nro_comprobante
    JOIN public.vino AS v
      ON v.cod_vino = rc.cod_vino
    WHERE cp.id_cliente = c.id_cliente
      AND v.tipo = 'tinto'
)
ORDER BY c.id_cliente;