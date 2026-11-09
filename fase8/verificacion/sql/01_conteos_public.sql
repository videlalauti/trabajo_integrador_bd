-- Solo SELECT. Ejecutar en origen y destino una vez finalizada restauracion.
-- Salida CSV exacta mediante psql --csv -X -f archivo.sql -o conteos.csv (ver README).
-- NO se ejecuta sobre base vacia (fallaran las tablas ausentes).
SELECT tabla, filas FROM (
SELECT 'localidad'::text AS tabla, COUNT(*)::bigint AS filas FROM public.localidad
UNION ALL
SELECT 'sala_venta'::text AS tabla, COUNT(*)::bigint AS filas FROM public.sala_venta
UNION ALL
SELECT 'empleado'::text AS tabla, COUNT(*)::bigint AS filas FROM public.empleado
UNION ALL
SELECT 'finca'::text AS tabla, COUNT(*)::bigint AS filas FROM public.finca
UNION ALL
SELECT 'cepa'::text AS tabla, COUNT(*)::bigint AS filas FROM public.cepa
UNION ALL
SELECT 'parcela'::text AS tabla, COUNT(*)::bigint AS filas FROM public.parcela
UNION ALL
SELECT 'bodega'::text AS tabla, COUNT(*)::bigint AS filas FROM public.bodega
UNION ALL
SELECT 'lote_uva'::text AS tabla, COUNT(*)::bigint AS filas FROM public.lote_uva
UNION ALL
SELECT 'analisis_calidad'::text AS tabla, COUNT(*)::bigint AS filas FROM public.analisis_calidad
UNION ALL
SELECT 'vino'::text AS tabla, COUNT(*)::bigint AS filas FROM public.vino
UNION ALL
SELECT 'vino_cepa'::text AS tabla, COUNT(*)::bigint AS filas FROM public.vino_cepa
UNION ALL
SELECT 'maridaje'::text AS tabla, COUNT(*)::bigint AS filas FROM public.maridaje
UNION ALL
SELECT 'vino_maridaje'::text AS tabla, COUNT(*)::bigint AS filas FROM public.vino_maridaje
UNION ALL
SELECT 'tipo_cliente'::text AS tabla, COUNT(*)::bigint AS filas FROM public.tipo_cliente
UNION ALL
SELECT 'cliente'::text AS tabla, COUNT(*)::bigint AS filas FROM public.cliente
UNION ALL
SELECT 'permiso_exportacion'::text AS tabla, COUNT(*)::bigint AS filas FROM public.permiso_exportacion
UNION ALL
SELECT 'comprobante'::text AS tabla, COUNT(*)::bigint AS filas FROM public.comprobante
UNION ALL
SELECT 'renglon_comprobante'::text AS tabla, COUNT(*)::bigint AS filas FROM public.renglon_comprobante
UNION ALL
SELECT 'transportista'::text AS tabla, COUNT(*)::bigint AS filas FROM public.transportista
UNION ALL
SELECT 'transportista_localidad'::text AS tabla, COUNT(*)::bigint AS filas FROM public.transportista_localidad
UNION ALL
SELECT 'ingreso'::text AS tabla, COUNT(*)::bigint AS filas FROM public.ingreso
UNION ALL
SELECT 'renglon_ingreso'::text AS tabla, COUNT(*)::bigint AS filas FROM public.renglon_ingreso
UNION ALL
SELECT 'transferencia'::text AS tabla, COUNT(*)::bigint AS filas FROM public.transferencia
UNION ALL
SELECT 'renglon_transferencia'::text AS tabla, COUNT(*)::bigint AS filas FROM public.renglon_transferencia
UNION ALL
SELECT 'stock_sala'::text AS tabla, COUNT(*)::bigint AS filas FROM public.stock_sala
UNION ALL
SELECT 'stock_deposito'::text AS tabla, COUNT(*)::bigint AS filas FROM public.stock_deposito
UNION ALL
SELECT 'auditoria_precio'::text AS tabla, COUNT(*)::bigint AS filas FROM public.auditoria_precio
) AS conteos ORDER BY tabla;
