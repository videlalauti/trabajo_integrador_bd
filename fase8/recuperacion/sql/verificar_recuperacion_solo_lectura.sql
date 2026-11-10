-- Fase 8: resumen de recuperación e integridad, exclusivamente SELECT.
-- Aplicar solo con permiso de lectura aprobado sobre destino local; no conecta por sí solo.
-- No sustituye control_integridad.sql (27 tablas, 32 relaciones FK y totales).
-- No contiene DML, DDL, ni transacciones que escriban.

-- 1. Identidad del destino y version: guardar salida sin host, usuario ni secretos.
SELECT current_database() AS base_actual, current_setting('server_version') AS version_pg;

-- 2. Cuatro conteos finales declarados por coordinación.
SELECT 'cliente' AS tabla, COUNT(*) AS filas FROM public.cliente
UNION ALL SELECT 'permiso_exportacion', COUNT(*) FROM public.permiso_exportacion
UNION ALL SELECT 'comprobante', COUNT(*) FROM public.comprobante
UNION ALL SELECT 'renglon_comprobante', COUNT(*) FROM public.renglon_comprobante
ORDER BY tabla;

-- 3. Las existencias negativas deben ser cero en ambas fuentes.
SELECT 'stock_sala' AS tabla,
       COUNT(*) FILTER (WHERE cantidad < 0) AS filas_negativas
FROM public.stock_sala
UNION ALL
SELECT 'stock_deposito' AS tabla,
       COUNT(*) FILTER (WHERE cantidad < 0) AS filas_negativas
FROM public.stock_deposito
ORDER BY tabla;

-- 4. Resumen de restricciones FK catalogadas: validadas o pendientes.
-- No demuestra por sí solo que no haya huérfanos: ejecutar también control_integridad.sql.
SELECT
    COUNT(*) AS fk_catalogadas,
    COUNT(*) FILTER (WHERE c.convalidated) AS fk_validadas,
    COUNT(*) FILTER (WHERE NOT c.convalidated) AS fk_sin_validar
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE n.nspname = 'public'
  AND c.contype = 'f';

-- 5. Triggers de usuario y estado de habilitación.
-- tgenabled: O=origin, A=always, R=replica, D=disabled.
SELECT t.tgrelid::regclass::text AS tabla, t.tgname AS trigger,
       t.tgenabled AS estado, t.tgisinternal AS interno
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND NOT t.tgisinternal
ORDER BY 1, 2;

-- 6. RN-13: estado de trigger y contador agregado (sin personas, IDs ni precios).
SELECT t.tgname, t.tgenabled, t.tgfoid::regprocedure::text AS funcion
FROM pg_trigger t
WHERE t.tgrelid = 'public.vino'::regclass
  AND t.tgname = 'trg_auditoria_precio_vino'
  AND NOT t.tgisinternal;

SELECT COUNT(*) AS registros_auditoria_precio,
       COUNT(*) FILTER (WHERE precio_anterior IS DISTINCT FROM precio_nuevo) AS cambios_efectivos
FROM public.auditoria_precio;

-- 7. Distribución de constraints validadas, por tipo.
-- p=PRIMARY KEY, f=FOREIGN KEY, u=UNIQUE, c=CHECK, x=EXCLUSION.
SELECT c.contype AS tipo, COUNT(*) AS cantidad,
       COUNT(*) FILTER (WHERE NOT c.convalidated) AS sin_validar
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE n.nspname = 'public'
GROUP BY c.contype
ORDER BY c.contype;
