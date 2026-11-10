-- Ejecutar tanto en origen como en destino, con permiso de leer catalogos.
-- Compara cantidades, no garantiza identidad funcional de las definiciones.
SELECT 'tablas_public' AS tipo, COUNT(*) AS cantidad
FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind IN ('r','p')
UNION ALL
SELECT 'vistas_public', COUNT(*)
FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind IN ('v','m')
UNION ALL
SELECT 'secuencias_public', COUNT(*)
FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND c.relkind='S'
UNION ALL
SELECT 'rutinas_public', COUNT(*)
FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public'
UNION ALL
SELECT 'triggers_public', COUNT(*)
FROM pg_catalog.pg_trigger t JOIN pg_catalog.pg_class c ON c.oid=t.tgrelid
JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='public' AND NOT t.tgisinternal
ORDER BY tipo;

-- SECURITY DEFINER: contrastar nombre, propietario y search_path de CADA rutina.
SELECT p.oid::regprocedure::text AS rutina,
       pg_catalog.pg_get_userbyid(p.proowner) AS propietario,
       p.prosecdef AS security_definer,
       p.proconfig AS configuracion
FROM pg_catalog.pg_proc p
JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public' AND p.prosecdef
ORDER BY rutina;
