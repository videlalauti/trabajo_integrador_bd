-- 1) CONTEO POR TABLA Y MINIMOS DE VOLUMEN
-- Requisitos finales: todas las tablas >= 1; al menos 3 con > 10000;
-- al menos 1 con > 100000. Se usa > (supera), no >=.
WITH conteos (tabla, filas) AS (
    VALUES
        ('localidad'::text, (SELECT COUNT(*) FROM public.localidad)),
        ('sala_venta'::text, (SELECT COUNT(*) FROM public.sala_venta)),
        ('empleado'::text, (SELECT COUNT(*) FROM public.empleado)),
        ('finca'::text, (SELECT COUNT(*) FROM public.finca)),
        ('cepa'::text, (SELECT COUNT(*) FROM public.cepa)),
        ('parcela'::text, (SELECT COUNT(*) FROM public.parcela)),
        ('bodega'::text, (SELECT COUNT(*) FROM public.bodega)),
        ('lote_uva'::text, (SELECT COUNT(*) FROM public.lote_uva)),
        ('analisis_calidad'::text, (SELECT COUNT(*) FROM public.analisis_calidad)),
        ('vino'::text, (SELECT COUNT(*) FROM public.vino)),
        ('vino_cepa'::text, (SELECT COUNT(*) FROM public.vino_cepa)),
        ('maridaje'::text, (SELECT COUNT(*) FROM public.maridaje)),
        ('vino_maridaje'::text, (SELECT COUNT(*) FROM public.vino_maridaje)),
        ('tipo_cliente'::text, (SELECT COUNT(*) FROM public.tipo_cliente)),
        ('cliente'::text, (SELECT COUNT(*) FROM public.cliente)),
        ('permiso_exportacion'::text, (SELECT COUNT(*) FROM public.permiso_exportacion)),
        ('comprobante'::text, (SELECT COUNT(*) FROM public.comprobante)),
        ('renglon_comprobante'::text, (SELECT COUNT(*) FROM public.renglon_comprobante)),
        ('transportista'::text, (SELECT COUNT(*) FROM public.transportista)),
        ('transportista_localidad'::text, (SELECT COUNT(*) FROM public.transportista_localidad)),
        ('ingreso'::text, (SELECT COUNT(*) FROM public.ingreso)),
        ('renglon_ingreso'::text, (SELECT COUNT(*) FROM public.renglon_ingreso)),
        ('transferencia'::text, (SELECT COUNT(*) FROM public.transferencia)),
        ('renglon_transferencia'::text, (SELECT COUNT(*) FROM public.renglon_transferencia)),
        ('stock_sala'::text, (SELECT COUNT(*) FROM public.stock_sala)),
        ('stock_deposito'::text, (SELECT COUNT(*) FROM public.stock_deposito)),
        ('auditoria_precio'::text, (SELECT COUNT(*) FROM public.auditoria_precio))
),
resultados AS (
    SELECT 0 AS orden, tabla AS control, filas AS cantidad,
           CASE WHEN filas >= 1 THEN 'OK' ELSE 'NO CUMPLE' END AS estado
    FROM conteos
    UNION ALL
    SELECT 1, 'RESUMEN: tablas con al menos una fila', COUNT(*) FILTER (WHERE filas >= 1),
           CASE WHEN COUNT(*) FILTER (WHERE filas >= 1) = COUNT(*) THEN 'OK' ELSE 'NO CUMPLE' END
    FROM conteos
    UNION ALL
    SELECT 1, 'RESUMEN: tablas con mas de 10000 filas', COUNT(*) FILTER (WHERE filas > 10000),
           CASE WHEN COUNT(*) FILTER (WHERE filas > 10000) >= 3 THEN 'OK' ELSE 'NO CUMPLE' END
    FROM conteos
    UNION ALL
    SELECT 1, 'RESUMEN: tablas con mas de 100000 filas', COUNT(*) FILTER (WHERE filas > 100000),
           CASE WHEN COUNT(*) FILTER (WHERE filas > 100000) >= 1 THEN 'OK' ELSE 'NO CUMPLE' END
    FROM conteos
)
SELECT control, cantidad, estado
FROM resultados
ORDER BY orden, control;

-- 2) REGISTROS HUERFANOS EN TODAS LAS CLAVES FORANEAS DEL ESQUEMA
-- Cada fila indica una relacion; el resultado esperado es 0 huerfanos.
-- Se comprueban explicitamente las 32 FK de 001_esquema.sql.
WITH fk_control (relacion, huerfanos) AS (
    SELECT 'fk_sala_venta_localidad'::text, COUNT(*)
    FROM public.sala_venta h
    LEFT JOIN public.localidad p ON h.id_localidad = p.id_localidad
    WHERE p.id_localidad IS NULL
    UNION ALL
    SELECT 'fk_empleado_sala_venta'::text, COUNT(*)
    FROM public.empleado h
    LEFT JOIN public.sala_venta p ON h.id_sala = p.id_sala
    WHERE p.id_sala IS NULL
    UNION ALL
    SELECT 'fk_parcela_finca'::text, COUNT(*)
    FROM public.parcela h
    LEFT JOIN public.finca p ON h.id_finca = p.id_finca
    WHERE p.id_finca IS NULL
    UNION ALL
    SELECT 'fk_parcela_cepa'::text, COUNT(*)
    FROM public.parcela h
    LEFT JOIN public.cepa p ON h.id_cepa = p.id_cepa
    WHERE p.id_cepa IS NULL
    UNION ALL
    SELECT 'fk_lote_uva_parcela'::text, COUNT(*)
    FROM public.lote_uva h
    LEFT JOIN public.parcela p ON h.id_finca = p.id_finca AND h.nro_parcela = p.nro_parcela
    WHERE p.id_finca IS NULL
    UNION ALL
    SELECT 'fk_lote_uva_bodega'::text, COUNT(*)
    FROM public.lote_uva h
    LEFT JOIN public.bodega p ON h.cuit_bodega = p.cuit
    WHERE p.cuit IS NULL
    UNION ALL
    SELECT 'fk_analisis_calidad_lote_uva'::text, COUNT(*)
    FROM public.analisis_calidad h
    LEFT JOIN public.lote_uva p ON h.nro_lote = p.nro_lote
    WHERE p.nro_lote IS NULL
    UNION ALL
    SELECT 'fk_vino_bodega'::text, COUNT(*)
    FROM public.vino h
    LEFT JOIN public.bodega p ON h.cuit_bodega = p.cuit
    WHERE p.cuit IS NULL
    UNION ALL
    SELECT 'fk_vino_cepa_vino'::text, COUNT(*)
    FROM public.vino_cepa h
    LEFT JOIN public.vino p ON h.cod_vino = p.cod_vino
    WHERE p.cod_vino IS NULL
    UNION ALL
    SELECT 'fk_vino_cepa_cepa'::text, COUNT(*)
    FROM public.vino_cepa h
    LEFT JOIN public.cepa p ON h.id_cepa = p.id_cepa
    WHERE p.id_cepa IS NULL
    UNION ALL
    SELECT 'fk_vino_maridaje_vino'::text, COUNT(*)
    FROM public.vino_maridaje h
    LEFT JOIN public.vino p ON h.cod_vino = p.cod_vino
    WHERE p.cod_vino IS NULL
    UNION ALL
    SELECT 'fk_vino_maridaje_maridaje'::text, COUNT(*)
    FROM public.vino_maridaje h
    LEFT JOIN public.maridaje p ON h.id_maridaje = p.id_maridaje
    WHERE p.id_maridaje IS NULL
    UNION ALL
    SELECT 'fk_cliente_localidad'::text, COUNT(*)
    FROM public.cliente h
    LEFT JOIN public.localidad p ON h.id_localidad = p.id_localidad
    WHERE p.id_localidad IS NULL
    UNION ALL
    SELECT 'fk_cliente_tipo_cliente'::text, COUNT(*)
    FROM public.cliente h
    LEFT JOIN public.tipo_cliente p ON h.tipo_cliente = p.tipo_cliente
    WHERE p.tipo_cliente IS NULL
    UNION ALL
    SELECT 'fk_permiso_exportacion_cliente'::text, COUNT(*)
    FROM public.permiso_exportacion h
    LEFT JOIN public.cliente p ON h.id_cliente = p.id_cliente
    WHERE p.id_cliente IS NULL
    UNION ALL
    SELECT 'fk_comprobante_cliente'::text, COUNT(*)
    FROM public.comprobante h
    LEFT JOIN public.cliente p ON h.id_cliente = p.id_cliente
    WHERE p.id_cliente IS NULL
    UNION ALL
    SELECT 'fk_comprobante_sala_venta'::text, COUNT(*)
    FROM public.comprobante h
    LEFT JOIN public.sala_venta p ON h.id_sala = p.id_sala
    WHERE p.id_sala IS NULL
    UNION ALL
    SELECT 'fk_renglon_comprobante_comprobante'::text, COUNT(*)
    FROM public.renglon_comprobante h
    LEFT JOIN public.comprobante p ON h.nro_comprobante = p.nro_comprobante
    WHERE p.nro_comprobante IS NULL
    UNION ALL
    SELECT 'fk_renglon_comprobante_vino'::text, COUNT(*)
    FROM public.renglon_comprobante h
    LEFT JOIN public.vino p ON h.cod_vino = p.cod_vino
    WHERE p.cod_vino IS NULL
    UNION ALL
    SELECT 'fk_transportista_localidad_transportista'::text, COUNT(*)
    FROM public.transportista_localidad h
    LEFT JOIN public.transportista p ON h.cod_transporte = p.cod_transporte
    WHERE p.cod_transporte IS NULL
    UNION ALL
    SELECT 'fk_transportista_localidad_localidad'::text, COUNT(*)
    FROM public.transportista_localidad h
    LEFT JOIN public.localidad p ON h.id_localidad = p.id_localidad
    WHERE p.id_localidad IS NULL
    UNION ALL
    SELECT 'fk_ingreso_transportista'::text, COUNT(*)
    FROM public.ingreso h
    LEFT JOIN public.transportista p ON h.cod_transporte = p.cod_transporte
    WHERE p.cod_transporte IS NULL
    UNION ALL
    SELECT 'fk_ingreso_bodega'::text, COUNT(*)
    FROM public.ingreso h
    LEFT JOIN public.bodega p ON h.cuit_bodega = p.cuit
    WHERE p.cuit IS NULL
    UNION ALL
    SELECT 'fk_renglon_ingreso_ingreso'::text, COUNT(*)
    FROM public.renglon_ingreso h
    LEFT JOIN public.ingreso p ON h.cod_ingreso = p.cod_ingreso
    WHERE p.cod_ingreso IS NULL
    UNION ALL
    SELECT 'fk_renglon_ingreso_vino'::text, COUNT(*)
    FROM public.renglon_ingreso h
    LEFT JOIN public.vino p ON h.cod_vino = p.cod_vino
    WHERE p.cod_vino IS NULL
    UNION ALL
    SELECT 'fk_transferencia_sala_venta'::text, COUNT(*)
    FROM public.transferencia h
    LEFT JOIN public.sala_venta p ON h.id_sala = p.id_sala
    WHERE p.id_sala IS NULL
    UNION ALL
    SELECT 'fk_renglon_transferencia_transferencia'::text, COUNT(*)
    FROM public.renglon_transferencia h
    LEFT JOIN public.transferencia p ON h.nro_solicitud = p.nro_solicitud
    WHERE p.nro_solicitud IS NULL
    UNION ALL
    SELECT 'fk_renglon_transferencia_vino'::text, COUNT(*)
    FROM public.renglon_transferencia h
    LEFT JOIN public.vino p ON h.cod_vino = p.cod_vino
    WHERE p.cod_vino IS NULL
    UNION ALL
    SELECT 'fk_stock_sala_sala_venta'::text, COUNT(*)
    FROM public.stock_sala h
    LEFT JOIN public.sala_venta p ON h.id_sala = p.id_sala
    WHERE p.id_sala IS NULL
    UNION ALL
    SELECT 'fk_stock_sala_vino'::text, COUNT(*)
    FROM public.stock_sala h
    LEFT JOIN public.vino p ON h.cod_vino = p.cod_vino
    WHERE p.cod_vino IS NULL
    UNION ALL
    SELECT 'fk_stock_deposito_vino'::text, COUNT(*)
    FROM public.stock_deposito h
    LEFT JOIN public.vino p ON h.cod_vino = p.cod_vino
    WHERE p.cod_vino IS NULL
    UNION ALL
    SELECT 'fk_auditoria_precio_vino'::text, COUNT(*)
    FROM public.auditoria_precio h
    LEFT JOIN public.vino p ON h.cod_vino = p.cod_vino
    WHERE p.cod_vino IS NULL
)
SELECT relacion, huerfanos,
       CASE WHEN huerfanos = 0 THEN 'OK' ELSE 'REVISAR' END AS estado
FROM fk_control
ORDER BY relacion;

-- 3) STOCK NEGATIVO (deposito y salas)
-- Resultado esperado: 0 filas negativas en ambas tablas.
SELECT 'stock_deposito' AS tabla, COUNT(*) AS filas_negativas,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'REVISAR' END AS estado
FROM public.stock_deposito WHERE cantidad < 0
UNION ALL
SELECT 'stock_sala', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'REVISAR' END
FROM public.stock_sala WHERE cantidad < 0;

-- 4) COMPROBANTES CON IMPORTES INCONSISTENTES
-- subtotal esperado = suma de cantidades * precios (bruto)
-- descuento esperado = diferencia entre bruto y neto por renglon
-- total esperado = suma de importes netos redondeados por renglon.
-- Se comprueba tambien que el subtotal almacenado en cada renglon
-- totalice correctamente. Resultado esperado: ninguna fila.
WITH importes AS (
    SELECT
        c.nro_comprobante,
        c.subtotal AS subtotal_guardado,
        c.descuento AS descuento_guardado,
        c.total AS total_guardado,
        COALESCE(SUM(ROUND(r.cantidad * r.precio_unitario, 2)), 0) AS subtotal_esperado,
        COALESCE(SUM(
            ROUND(r.cantidad * r.precio_unitario, 2)
            - ROUND(r.cantidad * r.precio_unitario * (1 - r.descuento / 100.0), 2)
        ), 0) AS descuento_esperado,
        COALESCE(SUM(
            ROUND(r.cantidad * r.precio_unitario * (1 - r.descuento / 100.0), 2)
        ), 0) AS total_esperado,
        COALESCE(SUM(r.subtotal), 0) AS total_renglones_guardados
    FROM public.comprobante c
    LEFT JOIN public.renglon_comprobante r
      ON r.nro_comprobante = c.nro_comprobante
    GROUP BY c.nro_comprobante, c.subtotal, c.descuento, c.total
)
SELECT
    nro_comprobante,
    subtotal_guardado, subtotal_esperado,
    descuento_guardado, descuento_esperado,
    total_guardado, total_esperado, total_renglones_guardados
FROM importes
WHERE subtotal_guardado IS DISTINCT FROM subtotal_esperado
   OR descuento_guardado IS DISTINCT FROM descuento_esperado
   OR total_guardado IS DISTINCT FROM total_esperado
   OR total_esperado IS DISTINCT FROM total_renglones_guardados
ORDER BY nro_comprobante;

-- Guardar los resultados reales de estas consultas en el informe de Etapa 3.
-- Este archivo no sustituye el README, la comparacion de tiempos ni el dump.
