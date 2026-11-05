-- Bodegas del Atuel - Fase 6
-- Preparacion de roles globales antes de restaurar el dump.
-- No contiene contrasenas ni habilita inicios de sesion.

DO $roles$
DECLARE
    nombre TEXT;
BEGIN
    FOREACH nombre IN ARRAY ARRAY[
        'bodega_propietario',
        'bodega_api_rw',
        'bodega_reportes_ro',
        'bodega_proc_owner',
        'bodega_trigger_owner',
        'bodega_view_owner',
        'bodega_admin',
        'bodega_api',
        'bodega_reportes'
    ]
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_roles
            WHERE rolname = nombre
        ) THEN
            EXECUTE format(
                'CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS',
                nombre
            );
        END IF;
    END LOOP;
END
$roles$;
