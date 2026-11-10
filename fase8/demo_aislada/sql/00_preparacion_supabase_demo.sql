-- SOLO proyecto Supabase de ensayo zfxocudcvriicrzgmxie.
-- No ejecutar en el proyecto FULL sjfyocokehaubuwwbhnw.
BEGIN;
DO $gate$
BEGIN
  IF current_user <> 'postgres'
     OR current_database() <> 'postgres'
     OR EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m'))
     OR EXISTS (SELECT 1 FROM pg_roles WHERE rolname='bodega_api')
  THEN
    RAISE EXCEPTION 'STOP: proyecto de ensayo no esta vacio o rol inesperado';
  END IF;
END $gate$;

-- Identificador centinela privado; no expuesto por la Data API.
CREATE SCHEMA fase8_control;
REVOKE ALL ON SCHEMA fase8_control FROM PUBLIC, anon, authenticated, service_role;
CREATE TABLE fase8_control.proyecto (ref TEXT PRIMARY KEY, nombre TEXT NOT NULL);
REVOKE ALL ON TABLE fase8_control.proyecto FROM PUBLIC, anon, authenticated, service_role;
INSERT INTO fase8_control.proyecto(ref, nombre)
VALUES ('zfxocudcvriicrzgmxie', 'bodegas-atuel-demo-aislada');

-- Supabase puede otorgar privilegios automaticamente a roles de la Data API.
-- Se desactiva para todo objeto nuevo que cree postgres en public.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE ALL ON TABLES FROM anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE ALL ON SEQUENCES FROM anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated, service_role;

-- Ningun rol de REST puede usar el esquema de ensayo por permiso explicito.
REVOKE ALL ON SCHEMA public FROM anon, authenticated;
COMMIT;
