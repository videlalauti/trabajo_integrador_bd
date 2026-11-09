-- Ejecutar con psql CONECTADO COMO bodega_api, desde un origen permitido.
-- NO desde el SQL Editor como postgres para acreditar TLS API -> BD.
-- Solo SELECT; realizar cuando Jose haya creado roles y esquema.
SELECT current_user AS rol_efectivo,
       session_user AS rol_sesion,
       current_database() AS base;
SELECT ssl, version AS tls_version, cipher
FROM pg_catalog.pg_stat_ssl
WHERE pid = pg_backend_pid();
-- Debe observarse current_user = bodega_api y ssl = true.
-- Si se usa Session pooler, el login cliente suele ser bodega_api.PROJECT_REF.

-- Pruebas de ACL (no ejecutan DML, pero NO sustituyen pruebas negativas reales).
SELECT
  has_table_privilege('bodega_api', 'public.comprobante', 'INSERT') AS api_puede_insertar_comprobante,
  has_table_privilege('bodega_api', 'public.stock_sala', 'SELECT') AS api_puede_leer_stock,
  has_table_privilege('bodega_api', 'public.stock_sala', 'UPDATE') AS api_puede_actualizar_stock,
  has_table_privilege('bodega_api', 'public.auditoria_precio', 'SELECT') AS api_puede_leer_auditoria,
  has_table_privilege('bodega_reportes', 'public.comprobante', 'SELECT') AS reportes_puede_leer_comprobante,
  has_table_privilege('bodega_reportes', 'public.comprobante', 'INSERT') AS reportes_puede_insertar_comprobante,
  has_table_privilege('anon', 'public.comprobante', 'SELECT') AS anon_puede_leer_comprobante,
  has_table_privilege('authenticated', 'public.comprobante', 'SELECT') AS authenticated_puede_leer_comprobante;
