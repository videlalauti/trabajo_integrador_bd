-- SOLO LECTURA. Ejecutar en origen y destino; conservar salidas separadas.
-- DDL de tablas e indices/triggers: comparar ademas pg_dump --schema-only.
SELECT 'tabla' AS tipo, n.nspname || '.' || c.relname AS objeto,
       pg_get_userbyid(c.relowner) AS propietario,
       c.relkind::text AS detalle
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind IN ('r','p')
UNION ALL
SELECT 'indice', n.nspname || '.' || c.relname, pg_get_userbyid(c.relowner),
       pg_get_indexdef(c.oid)
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind='i'
ORDER BY tipo, objeto;

SELECT n.nspname||'.'||c.relname AS tabla, con.conname AS nombre,
       con.contype AS tipo, pg_get_constraintdef(con.oid, true) AS definicion,
       con.convalidated AS validada
FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' ORDER BY tabla,nombre;

SELECT n.nspname||'.'||c.relname AS tabla, t.tgname AS trigger,
       t.tgenabled AS habilitado, pg_get_triggerdef(t.oid) AS definicion
FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND NOT t.tgisinternal
ORDER BY tabla,trigger;

SELECT p.oid::regprocedure::text AS rutina,
       pg_get_userbyid(p.proowner) AS propietario, p.prosecdef AS security_definer,
       p.proconfig AS configuracion,
       pg_get_functiondef(p.oid) AS definicion
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public' ORDER BY rutina;

SELECT n.nspname||'.'||c.relname AS tabla,
       c.relacl::text AS acl_explicita,
       has_table_privilege('bodega_api',c.oid,'SELECT') AS api_select,
       has_table_privilege('bodega_api',c.oid,'INSERT') AS api_insert,
       has_table_privilege('bodega_api',c.oid,'UPDATE') AS api_update
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind IN ('r','p') ORDER BY tabla;
