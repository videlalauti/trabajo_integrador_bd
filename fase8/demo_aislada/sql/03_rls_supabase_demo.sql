-- SOLO proyecto Supabase DEMO zfxocudcvriicrzgmxie. NO FULL.
-- Habilita RLS a las 27 tablas del TP; permite roles internos exclusivamente.
-- Los GRANT de 007 siguen siendo el limite efectivo de escritura/lectura.
BEGIN;
DO $rls$
DECLARE r record;
BEGIN
 IF current_user <> 'postgres'
    OR NOT EXISTS (SELECT 1 FROM fase8_control.proyecto WHERE ref='zfxocudcvriicrzgmxie')
    OR (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r') <> 27
 THEN RAISE EXCEPTION 'STOP: RLS solo para 27 tablas de demo'; END IF;
 FOR r IN
    SELECT c.relname FROM pg_class c
    JOIN pg_namespace n ON n.oid=c.relnamespace
    WHERE n.nspname='public' AND c.relkind='r'
 LOOP
   IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename=r.relname)
   THEN RAISE EXCEPTION 'STOP: tabla % ya tiene politicas RLS',r.relname; END IF;
   EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',r.relname);
   EXECUTE format(
     'CREATE POLICY fase8_demo_roles ON public.%I FOR ALL TO bodega_api, bodega_api_rw, bodega_admin, bodega_reportes, bodega_reportes_ro, bodega_propietario, bodega_proc_owner, bodega_trigger_owner, bodega_view_owner USING (true) WITH CHECK (true)',
      r.relname);
 END LOOP;
 IF (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity) <> 27
 THEN RAISE EXCEPTION 'STOP: faltan tablas con RLS'; END IF;
END $rls$;
COMMIT;
