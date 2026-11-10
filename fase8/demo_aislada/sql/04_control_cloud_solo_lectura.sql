-- SOLO SELECT: estado de migraciones, identidad, seguridad y datos ficticios.
-- Ejecutar unicamente en proyecto Supabase DEMO zfxocudcvriicrzgmxie.
SELECT
 (SELECT COUNT(*) FROM fase8_control.proyecto
   WHERE ref='zfxocudcvriicrzgmxie') AS identidad_demo,
 (SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relkind='r') AS tablas,
 (SELECT COUNT(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace
   WHERE n.nspname='public' AND c.contype='f') AS claves_foraneas,
 (SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity) AS tablas_rls,
 (SELECT COUNT(*) FROM pg_policies
   WHERE schemaname='public' AND policyname='fase8_demo_roles') AS politicas,
 (SELECT COUNT(*) FROM public.vino) AS vinos,
 (SELECT COUNT(*) FROM public.cliente) AS clientes,
 (SELECT COUNT(*) FROM public.sala_venta) AS salas,
 (SELECT COALESCE(SUM(cantidad),0) FROM public.stock_sala) AS total_salas,
 (SELECT COALESCE(SUM(cantidad),0) FROM public.stock_deposito) AS total_deposito,
 (SELECT COUNT(*) FROM public.comprobante) AS ventas_persistidas,
 (SELECT COUNT(*) FROM public.transferencia) AS transferencias_persistidas,
 (SELECT COUNT(*) FROM public.stock_sala WHERE cantidad<0)
    +(SELECT COUNT(*) FROM public.stock_deposito WHERE cantidad<0) AS negativos,
 has_table_privilege('anon','public.vino','SELECT') AS anon_lee_vino,
 has_table_privilege('authenticated','public.cliente','SELECT') AS auth_lee_cliente,
 has_table_privilege('service_role','public.cliente','SELECT') AS service_lee_cliente,
 has_table_privilege('bodega_api','public.comprobante','INSERT') AS api_inserta_venta,
 has_table_privilege('bodega_api','public.stock_sala','UPDATE') AS api_actualiza_stock,
 (SELECT rolpassword IS NULL FROM pg_authid WHERE rolname='bodega_api') AS clave_api_sin_configurar;
