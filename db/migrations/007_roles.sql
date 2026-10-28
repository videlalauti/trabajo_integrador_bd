BEGIN;
-- 1) ROLES Y USUARIOS
DO $roles$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_propietario') THEN
        EXECUTE 'CREATE ROLE bodega_propietario NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_api_rw') THEN
        EXECUTE 'CREATE ROLE bodega_api_rw NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_reportes_ro') THEN
        EXECUTE 'CREATE ROLE bodega_reportes_ro NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_proc_owner') THEN
        EXECUTE 'CREATE ROLE bodega_proc_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_trigger_owner') THEN
        EXECUTE 'CREATE ROLE bodega_trigger_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_view_owner') THEN
        EXECUTE 'CREATE ROLE bodega_view_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_admin') THEN
        EXECUTE 'CREATE ROLE bodega_admin LOGIN PASSWORD NULL NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_api') THEN
        EXECUTE 'CREATE ROLE bodega_api LOGIN PASSWORD NULL NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'bodega_reportes') THEN
        EXECUTE 'CREATE ROLE bodega_reportes LOGIN PASSWORD NULL NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS';
    END IF;
END
$roles$;

ALTER ROLE bodega_propietario  WITH NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE bodega_api_rw       WITH NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE bodega_reportes_ro  WITH NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE bodega_proc_owner   WITH NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE bodega_trigger_owner WITH NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE bodega_view_owner   WITH NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE bodega_admin        WITH LOGIN    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE bodega_api          WITH LOGIN    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
ALTER ROLE bodega_reportes     WITH LOGIN    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

ALTER ROLE bodega_admin    SET search_path = pg_catalog, public, pg_temp;
ALTER ROLE bodega_api      SET search_path = pg_catalog, public, pg_temp;
ALTER ROLE bodega_reportes SET search_path = pg_catalog, public, pg_temp;

-- 2) PERTENENCIAS
GRANT bodega_propietario TO bodega_admin WITH INHERIT TRUE, SET TRUE;
GRANT bodega_api_rw      TO bodega_api   WITH INHERIT TRUE, SET TRUE;
GRANT bodega_reportes_ro TO bodega_reportes WITH INHERIT TRUE, SET TRUE;


DO $limpiar_membresias$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT otorgado.rolname AS rol_otorgado,
               miembro.rolname  AS rol_miembro
          FROM pg_catalog.pg_auth_members m
          JOIN pg_catalog.pg_roles otorgado ON otorgado.oid = m.roleid
          JOIN pg_catalog.pg_roles miembro  ON miembro.oid  = m.member
         WHERE otorgado.rolname IN (
                   'bodega_propietario',
                   'bodega_api_rw',
                   'bodega_reportes_ro',
                   'bodega_proc_owner',
                   'bodega_trigger_owner',
                   'bodega_view_owner'
               )
           AND miembro.rolname IN (
                   'bodega_admin',
                   'bodega_propietario',
                   'bodega_api',
                   'bodega_api_rw',
                   'bodega_reportes',
                   'bodega_reportes_ro',
                   'bodega_proc_owner',
                   'bodega_trigger_owner',
                   'bodega_view_owner'
               )
           AND NOT (otorgado.rolname = 'bodega_propietario' AND miembro.rolname = 'bodega_admin')
           AND NOT (otorgado.rolname = 'bodega_api_rw'      AND miembro.rolname = 'bodega_api')
           AND NOT (otorgado.rolname = 'bodega_reportes_ro' AND miembro.rolname = 'bodega_reportes')
    LOOP
        EXECUTE format('REVOKE %I FROM %I', r.rol_otorgado, r.rol_miembro);
    END LOOP;
END
$limpiar_membresias$;

-- 3) PRIVILEGIOS DE BASE Y ESQUEMA PUBLIC
-- PostgreSQL concede TEMPORARY a PUBLIC por defecto en una BD nueva.
-- La politica de roles y los tests exigen que API/reportes no puedan crear
-- objetos temporales; limitar esto SOLO a la base en ejecucion.
DO $database_privileges$
BEGIN
    EXECUTE format('REVOKE CREATE, TEMPORARY ON DATABASE %I FROM PUBLIC', current_database());
END
$database_privileges$;


REVOKE ALL ON SCHEMA public FROM PUBLIC;

GRANT USAGE ON SCHEMA public TO
    bodega_propietario,
    bodega_api_rw,
    bodega_reportes_ro,
    bodega_proc_owner,
    bodega_trigger_owner,
    bodega_view_owner;

GRANT CREATE ON SCHEMA public TO bodega_propietario;
GRANT CREATE ON SCHEMA public TO bodega_proc_owner, bodega_trigger_owner, bodega_view_owner;

-- 4) PROCEDIMIENTOS DE CAMBIO DE ESTADO
CREATE OR REPLACE PROCEDURE public.sp_terminar_ingreso(
    IN p_cod_ingreso INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
    v_estado     estado_documento;
    v_renglones  BIGINT;
    v_filas      BIGINT;
BEGIN
    IF p_cod_ingreso IS NULL THEN
        RAISE EXCEPTION 'RN-10: el codigo de ingreso no puede ser nulo'
            USING ERRCODE = 'P0001';
    END IF;

    -- Bloqueo de la cabecera: serializa dos intentos de terminar el documento.
    SELECT estado
      INTO v_estado
      FROM public.ingreso
     WHERE cod_ingreso = p_cod_ingreso
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'RN-10: el ingreso % no existe', p_cod_ingreso
            USING ERRCODE = 'P0001';
    END IF;

    IF v_estado <> 'en_confeccion' THEN
        IF v_estado = 'terminado' THEN
            RAISE EXCEPTION 'RN-10: el ingreso % ya esta terminado', p_cod_ingreso
                USING ERRCODE = 'P0001';
        ELSIF v_estado = 'procesado' THEN
            RAISE EXCEPTION 'RN-10: el ingreso % ya fue procesado', p_cod_ingreso
                USING ERRCODE = 'P0001';
        ELSE
            RAISE EXCEPTION 'RN-10: estado no valido (%) para el ingreso %', v_estado, p_cod_ingreso
                USING ERRCODE = 'P0001';
        END IF;
    END IF;

    SELECT COUNT(*)
      INTO v_renglones
      FROM public.renglon_ingreso
     WHERE cod_ingreso = p_cod_ingreso;

    IF v_renglones = 0 THEN
        RAISE EXCEPTION 'RN-10: el ingreso % no tiene renglones', p_cod_ingreso
            USING ERRCODE = 'P0001';
    END IF;

    -- Solo cambia el estado; no toca stock ni renglones.
    UPDATE public.ingreso
       SET estado = 'terminado'
     WHERE cod_ingreso = p_cod_ingreso
       AND estado = 'en_confeccion';

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas <> 1 THEN
        RAISE EXCEPTION 'RN-10: no se pudo confirmar el estado terminado del ingreso %', p_cod_ingreso
            USING ERRCODE = 'P0001';
    END IF;

    RAISE NOTICE 'RN-10: ingreso % terminado correctamente', p_cod_ingreso;
END;
$$;

CREATE OR REPLACE PROCEDURE public.sp_terminar_transferencia(
    IN p_nro_solicitud INTEGER
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
DECLARE
    v_estado     estado_documento;
    v_renglones  BIGINT;
    v_filas      BIGINT;
BEGIN
    IF p_nro_solicitud IS NULL THEN
        RAISE EXCEPTION 'RN-11: el numero de solicitud no puede ser nulo'
            USING ERRCODE = 'P0001';
    END IF;

    SELECT estado
      INTO v_estado
      FROM public.transferencia
     WHERE nro_solicitud = p_nro_solicitud
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'RN-11: la transferencia % no existe', p_nro_solicitud
            USING ERRCODE = 'P0001';
    END IF;

    IF v_estado <> 'en_confeccion' THEN
        IF v_estado = 'terminado' THEN
            RAISE EXCEPTION 'RN-11: la transferencia % ya esta terminada', p_nro_solicitud
                USING ERRCODE = 'P0001';
        ELSIF v_estado = 'procesado' THEN
            RAISE EXCEPTION 'RN-11: la transferencia % ya fue procesada', p_nro_solicitud
                USING ERRCODE = 'P0001';
        ELSE
            RAISE EXCEPTION 'RN-11: estado no valido (%) para la transferencia %', v_estado, p_nro_solicitud
                USING ERRCODE = 'P0001';
        END IF;
    END IF;

    SELECT COUNT(*)
      INTO v_renglones
      FROM public.renglon_transferencia
     WHERE nro_solicitud = p_nro_solicitud;

    IF v_renglones = 0 THEN
        RAISE EXCEPTION 'RN-11: la transferencia % no tiene renglones', p_nro_solicitud
            USING ERRCODE = 'P0001';
    END IF;

    -- Solo cambia el estado; la fecha de confeccion queda intacta.
    UPDATE public.transferencia
       SET estado = 'terminado'
     WHERE nro_solicitud = p_nro_solicitud
       AND estado = 'en_confeccion';

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas <> 1 THEN
        RAISE EXCEPTION 'RN-11: no se pudo confirmar el estado terminado de la transferencia %', p_nro_solicitud
            USING ERRCODE = 'P0001';
    END IF;

    RAISE NOTICE 'RN-11: transferencia % terminada correctamente', p_nro_solicitud;
END;
$$;

-- 5) AUDITORIA DE PRECIO (RN-13)
CREATE OR REPLACE FUNCTION public.fn_trg_auditoria_precio_vino()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp
AS $$
BEGIN
    IF NEW.precio IS DISTINCT FROM OLD.precio THEN
        INSERT INTO public.auditoria_precio
            (cod_vino, precio_anterior, precio_nuevo, fecha_hora, usuario)
        VALUES
            (OLD.cod_vino, OLD.precio, NEW.precio, CURRENT_TIMESTAMP, session_user);
    END IF;
    RETURN NEW;
END;
$$;

-- 6) PROPIEDAD DE LOS OBJETOS EXISTENTES
DO $owner_tables$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT c.relname, c.relkind
          FROM pg_catalog.pg_class c
          JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = 'public'
           AND c.relkind IN ('r', 'p', 'S')
           -- Las secuencias SERIAL/IDENTITY estan ligadas a su tabla: cambiar
           -- el dueno de la tabla cambia el de la secuencia. ALTER SEQUENCE
           -- directo sobre ellas falla, por eso se omiten.
           AND NOT (
               c.relkind = 'S'
               AND EXISTS (
                   SELECT 1
                     FROM pg_catalog.pg_depend d
                    WHERE d.classid = 'pg_catalog.pg_class'::regclass
                      AND d.objid = c.oid
                      AND d.deptype IN ('a', 'i')
               )
           )
    LOOP
        IF r.relkind = 'S' THEN
            EXECUTE format('ALTER SEQUENCE public.%I OWNER TO bodega_propietario', r.relname);
        ELSE
            EXECUTE format('ALTER TABLE public.%I OWNER TO bodega_propietario', r.relname);
        END IF;
    END LOOP;
END
$owner_tables$;

DO $owner_types$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT t.typname, t.typtype
          FROM pg_catalog.pg_type t
          JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
         WHERE n.nspname = 'public'
           AND t.typtype IN ('e', 'd')
    LOOP
        IF r.typtype = 'd' THEN
            EXECUTE format('ALTER DOMAIN public.%I OWNER TO bodega_propietario', r.typname);
        ELSE
            EXECUTE format('ALTER TYPE public.%I OWNER TO bodega_propietario', r.typname);
        END IF;
    END LOOP;
END
$owner_types$;

DO $owner_routines$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT p.proname, pg_catalog.pg_get_function_identity_arguments(p.oid) AS args
          FROM pg_catalog.pg_proc p
          JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
         WHERE n.nspname = 'public'
           AND p.prokind IN ('f', 'p')
    LOOP
        EXECUTE format('ALTER ROUTINE public.%I(%s) OWNER TO bodega_propietario', r.proname, r.args);
    END LOOP;
END
$owner_routines$;

-- Rutinas privilegiadas: cambian a duenos tecnicos sin membresias para la API.
ALTER FUNCTION public.fn_trg_auditoria_precio_vino()        OWNER TO bodega_trigger_owner;
ALTER FUNCTION public.fn_trg_renglon_ingreso_estado()      OWNER TO bodega_trigger_owner;
ALTER FUNCTION public.fn_trg_renglon_transferencia_estado() OWNER TO bodega_trigger_owner;
ALTER FUNCTION public.fn_trg_renglon_comprobante()         OWNER TO bodega_trigger_owner;
ALTER FUNCTION public.fn_trg_renglon_comprobante_totales() OWNER TO bodega_trigger_owner;

ALTER PROCEDURE public.sp_procesar_ingreso(INTEGER)          OWNER TO bodega_proc_owner;
ALTER PROCEDURE public.sp_procesar_transferencia(INTEGER)    OWNER TO bodega_proc_owner;
ALTER PROCEDURE public.sp_terminar_ingreso(INTEGER)          OWNER TO bodega_proc_owner;
ALTER PROCEDURE public.sp_terminar_transferencia(INTEGER)    OWNER TO bodega_proc_owner;


ALTER VIEW public.v_stock_total_por_vino      OWNER TO bodega_view_owner;
ALTER VIEW public.v_ventas_mensuales_por_sala OWNER TO bodega_view_owner;
ALTER VIEW public.v_documentos_pendientes     OWNER TO bodega_view_owner;


ALTER VIEW public.v_stock_total_por_vino      SET (security_invoker = false);
ALTER VIEW public.v_ventas_mensuales_por_sala SET (security_invoker = false);
ALTER VIEW public.v_documentos_pendientes     SET (security_invoker = false);

-- 7) SECURITY DEFINER Y SEARCH_PATH
DO $routine_security$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT p.proname, pg_catalog.pg_get_function_identity_arguments(p.oid) AS args
          FROM pg_catalog.pg_proc p
          JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
         WHERE n.nspname = 'public'
           AND p.prokind IN ('f', 'p')
    LOOP
        EXECUTE format('ALTER ROUTINE public.%I(%s) SECURITY INVOKER', r.proname, r.args);
        EXECUTE format(
            'ALTER ROUTINE public.%I(%s) SET search_path = pg_catalog, public, pg_temp',
            r.proname, r.args
        );
    END LOOP;
END
$routine_security$;

ALTER FUNCTION public.fn_trg_auditoria_precio_vino()         SECURITY DEFINER;
ALTER FUNCTION public.fn_trg_renglon_ingreso_estado()       SECURITY DEFINER;
ALTER FUNCTION public.fn_trg_renglon_transferencia_estado() SECURITY DEFINER;
ALTER FUNCTION public.fn_trg_renglon_comprobante()          SECURITY DEFINER;
ALTER FUNCTION public.fn_trg_renglon_comprobante_totales()  SECURITY DEFINER;

ALTER PROCEDURE public.sp_procesar_ingreso(INTEGER)          SECURITY DEFINER;
ALTER PROCEDURE public.sp_procesar_transferencia(INTEGER)    SECURITY DEFINER;
ALTER PROCEDURE public.sp_terminar_ingreso(INTEGER)          SECURITY DEFINER;
ALTER PROCEDURE public.sp_terminar_transferencia(INTEGER)    SECURITY DEFINER;

-- 8) REVOCAR PRIVILEGIOS PUBLICOS SOBRE OBJETOS YA EXISTENTES
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL ROUTINES  IN SCHEMA public FROM PUBLIC;

REVOKE USAGE ON TYPE public.estado_documento, public.tipo_cepa, public.tipo_vino FROM PUBLIC;
REVOKE USAGE ON DOMAIN public.cuit_dom FROM PUBLIC;

-- 9) PERMISOS DE LOS TIPOS
GRANT USAGE ON TYPE public.estado_documento, public.tipo_cepa, public.tipo_vino TO
    bodega_propietario,
    bodega_api_rw,
    bodega_reportes_ro,
    bodega_proc_owner,
    bodega_trigger_owner,
    bodega_view_owner;

GRANT USAGE ON DOMAIN public.cuit_dom TO
    bodega_propietario,
    bodega_api_rw,
    bodega_reportes_ro,
    bodega_proc_owner,
    bodega_trigger_owner,
    bodega_view_owner;

-- 10) PERMISOS DE LA API (bodega_api_rw)
GRANT SELECT ON public.vino, public.vino_cepa, public.cepa,
                public.vino_maridaje, public.maridaje, public.bodega
    TO bodega_api_rw;

GRANT INSERT ON public.vino TO bodega_api_rw;
GRANT UPDATE (nombre, tipo, anada, volumen_ml, graduacion, precio, cuit_bodega)
    ON public.vino TO bodega_api_rw;
GRANT DELETE ON public.vino TO bodega_api_rw;

GRANT INSERT, DELETE ON public.vino_cepa TO bodega_api_rw;
GRANT UPDATE (porcentaje) ON public.vino_cepa TO bodega_api_rw;
GRANT INSERT, DELETE ON public.vino_maridaje TO bodega_api_rw;

GRANT SELECT ON public.cliente, public.tipo_cliente, public.localidad,
                public.permiso_exportacion
    TO bodega_api_rw;
GRANT INSERT ON public.cliente TO bodega_api_rw;
GRANT UPDATE (nombre_razon_social, tipo_doc, nro_doc, direccion, fecha_alta,
              id_localidad, tipo_cliente, descuento_especial, zona_cobertura,
              nro_habilitacion, pais_destino)
    ON public.cliente TO bodega_api_rw;
GRANT DELETE ON public.cliente TO bodega_api_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.permiso_exportacion TO bodega_api_rw;

-- Ventas: la API inserta cabecera y renglones. Los triggers de 005 calculan
-- subtotales/totales y descuentan stock con los privilegios del trigger owner.
GRANT SELECT ON public.sala_venta TO bodega_api_rw;
GRANT SELECT, INSERT ON public.comprobante TO bodega_api_rw;
GRANT SELECT, INSERT ON public.renglon_comprobante TO bodega_api_rw;

-- Ingresos: sin UPDATE de cabecera; los renglones solo se editan mientras el
-- trigger RN-12 vea la cabecera en_confeccion.
GRANT SELECT ON public.transportista, public.transportista_localidad TO bodega_api_rw;
GRANT SELECT, INSERT ON public.ingreso TO bodega_api_rw;
GRANT SELECT, INSERT ON public.renglon_ingreso TO bodega_api_rw;
GRANT UPDATE (cod_vino, cantidad) ON public.renglon_ingreso TO bodega_api_rw;
GRANT DELETE ON public.renglon_ingreso TO bodega_api_rw;

-- Transferencias: mismo criterio que ingresos.
GRANT SELECT, INSERT ON public.transferencia TO bodega_api_rw;
GRANT SELECT, INSERT ON public.renglon_transferencia TO bodega_api_rw;
GRANT UPDATE (cod_vino, cantidad) ON public.renglon_transferencia TO bodega_api_rw;
GRANT DELETE ON public.renglon_transferencia TO bodega_api_rw;

-- Stock: solo lectura. Se modifica por procedimientos/triggers, nunca por DML
-- directo de la API.
GRANT SELECT ON public.stock_deposito, public.stock_sala TO bodega_api_rw;

-- Lecturas adicionales justificadas por las consultas S1 a S12 y por las
-- vistas de reportes que la API expone: parcelas/fincas/lotes para S10.
GRANT SELECT ON public.finca, public.parcela, public.lote_uva TO bodega_api_rw;

-- Secuencias de las columnas SERIAL que la API inserta.
GRANT USAGE ON SEQUENCE
    public.vino_cod_vino_seq,
    public.cliente_id_cliente_seq,
    public.comprobante_nro_comprobante_seq,
    public.ingreso_cod_ingreso_seq,
    public.transferencia_nro_solicitud_seq
    TO bodega_api_rw;

-- Vistas de reportes.
GRANT SELECT ON public.v_stock_total_por_vino,
                public.v_ventas_mensuales_por_sala,
                public.v_documentos_pendientes
    TO bodega_api_rw;

-- Funciones de lectura aprobadas en 003.
GRANT EXECUTE ON FUNCTION public.fn_stock_sala(INTEGER, INTEGER)      TO bodega_api_rw;
GRANT EXECUTE ON FUNCTION public.fn_descuento_cliente(INTEGER)        TO bodega_api_rw;
GRANT EXECUTE ON FUNCTION public.fn_total_comprobante(INTEGER)        TO bodega_api_rw;
GRANT EXECUTE ON FUNCTION public.fn_antiguedad_anios(DATE)            TO bodega_api_rw;

-- Unicos procedimientos que pueden cambiar estados/procesar movimientos.
GRANT EXECUTE ON PROCEDURE public.sp_procesar_ingreso(INTEGER)       TO bodega_api_rw;
GRANT EXECUTE ON PROCEDURE public.sp_procesar_transferencia(INTEGER) TO bodega_api_rw;
GRANT EXECUTE ON PROCEDURE public.sp_terminar_ingreso(INTEGER)       TO bodega_api_rw;
GRANT EXECUTE ON PROCEDURE public.sp_terminar_transferencia(INTEGER) TO bodega_api_rw;

-- 11) PERMISOS DEL ROL DE REPORTES (bodega_reportes_ro)
GRANT SELECT ON public.v_stock_total_por_vino,
                public.v_ventas_mensuales_por_sala,
                public.v_documentos_pendientes
    TO bodega_reportes_ro;

GRANT SELECT ON
    public.vino,
    public.vino_cepa,
    public.cepa,
    public.vino_maridaje,
    public.maridaje,
    public.bodega,
    public.stock_deposito,
    public.stock_sala,
    public.comprobante,
    public.renglon_comprobante,
    public.cliente,
    public.tipo_cliente,
    public.localidad,
    public.sala_venta,
    public.transferencia,
    public.renglon_transferencia,
    public.ingreso,
    public.renglon_ingreso,
    public.transportista,
    public.transportista_localidad,
    public.finca,
    public.parcela,
    public.lote_uva
    TO bodega_reportes_ro;

-- 12) PERMISOS DEL PROPIETARIO Y DE LOS PROPIETARIOS TECNICOS
GRANT SELECT ON public.v_stock_total_por_vino,
                public.v_ventas_mensuales_por_sala,
                public.v_documentos_pendientes
    TO bodega_propietario;

GRANT EXECUTE ON ALL ROUTINES IN SCHEMA public TO bodega_propietario;

-- bodega_view_owner: solo lo necesario para evaluar las vistas con derechos de
-- dueno.
GRANT SELECT ON
    public.vino,
    public.stock_deposito,
    public.stock_sala,
    public.comprobante,
    public.sala_venta,
    public.ingreso,
    public.transferencia
    TO bodega_view_owner;

REVOKE SELECT ON public.auditoria_precio FROM bodega_trigger_owner;
GRANT INSERT ON public.auditoria_precio TO bodega_trigger_owner;
GRANT USAGE ON SEQUENCE public.auditoria_precio_id_auditoria_seq TO bodega_trigger_owner;

GRANT SELECT ON public.ingreso, public.transferencia TO bodega_trigger_owner;
GRANT UPDATE (estado) ON public.ingreso, public.transferencia TO bodega_trigger_owner;

GRANT SELECT ON
    public.comprobante,
    public.stock_sala,
    public.cliente,
    public.tipo_cliente,
    public.renglon_comprobante
    TO bodega_trigger_owner;

GRANT INSERT ON public.stock_sala TO bodega_trigger_owner;
GRANT UPDATE (cantidad) ON public.stock_sala TO bodega_trigger_owner;
GRANT UPDATE (subtotal, descuento, total) ON public.comprobante TO bodega_trigger_owner;

-- El trigger de ventas y el de totales invocan funciones de 003 como
-- bodega_trigger_owner; necesitan EXECUTE explicito porque PUBLIC ya no lo
-- tiene.
GRANT EXECUTE ON FUNCTION public.fn_descuento_cliente(INTEGER) TO bodega_trigger_owner;
GRANT EXECUTE ON FUNCTION public.fn_total_comprobante(INTEGER) TO bodega_trigger_owner;

-- bodega_proc_owner: lectura y escritura de los objetos que mueven los
-- procedimientos de procesamiento. No tiene acceso a auditoria, empleado ni
-- vistas. Solo puede cambiar estado y cantidades; no otras columnas.
GRANT SELECT ON public.ingreso, public.transferencia TO bodega_proc_owner;
GRANT UPDATE (estado) ON public.ingreso, public.transferencia TO bodega_proc_owner;
GRANT SELECT ON public.renglon_ingreso, public.renglon_transferencia TO bodega_proc_owner;
GRANT SELECT, INSERT ON public.stock_deposito, public.stock_sala TO bodega_proc_owner;
GRANT UPDATE (cantidad) ON public.stock_deposito, public.stock_sala TO bodega_proc_owner;

-- 13) PRIVILEGIOS POR DEFECTO PARA OBJETOS FUTUROS
DO $default_privileges$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT unnest(ARRAY[
            'bodega_propietario',
            'bodega_proc_owner',
            'bodega_trigger_owner',
            'bodega_view_owner',
            'bodega_admin'
        ]) AS role_name
    LOOP
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE %I REVOKE ALL ON TABLES FROM PUBLIC',
            r.role_name
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE %I REVOKE ALL ON SEQUENCES FROM PUBLIC',
            r.role_name
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE %I REVOKE EXECUTE ON ROUTINES FROM PUBLIC',
            r.role_name
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE %I REVOKE USAGE ON TYPES FROM PUBLIC',
            r.role_name
        );
    END LOOP;
END
$default_privileges$;

ALTER DEFAULT PRIVILEGES FOR ROLE CURRENT_USER
    REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE CURRENT_USER
    REVOKE ALL ON SEQUENCES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE CURRENT_USER
    REVOKE EXECUTE ON ROUTINES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE CURRENT_USER
    REVOKE USAGE ON TYPES FROM PUBLIC;

-- 14) CIERRE DE PRIVILEGIOS TEMPORALES Y VERIFICACIONES
REVOKE CREATE ON SCHEMA public FROM
    bodega_proc_owner,
    bodega_trigger_owner,
    bodega_view_owner;

-- Verificaciones de la propia migracion. Si alguna falla, todo 007 se revierte.
DO $verificaciones$
BEGIN
    IF has_schema_privilege('bodega_api_rw', 'public', 'CREATE') THEN
        RAISE EXCEPTION '007: bodega_api_rw no debe tener CREATE sobre public';
    END IF;

    IF has_schema_privilege('bodega_reportes_ro', 'public', 'CREATE') THEN
        RAISE EXCEPTION '007: bodega_reportes_ro no debe tener CREATE sobre public';
    END IF;

    IF pg_has_role('bodega_admin', 'bodega_proc_owner', 'MEMBER')
       OR pg_has_role('bodega_admin', 'bodega_trigger_owner', 'MEMBER')
       OR pg_has_role('bodega_admin', 'bodega_view_owner', 'MEMBER') THEN
        RAISE EXCEPTION '007: bodega_admin no debe poder asumir roles tecnicos';
    END IF;

    IF has_table_privilege('bodega_api_rw', 'public.auditoria_precio', 'SELECT')
       OR has_table_privilege('bodega_api_rw', 'public.auditoria_precio', 'INSERT')
       OR has_table_privilege('bodega_api_rw', 'public.empleado', 'SELECT') THEN
        RAISE EXCEPTION '007: bodega_api_rw no debe acceder a auditoria_precio ni empleado';
    END IF;

    IF has_table_privilege('bodega_reportes_ro', 'public.auditoria_precio', 'SELECT')
       OR has_table_privilege('bodega_reportes_ro', 'public.empleado', 'SELECT') THEN
        RAISE EXCEPTION '007: bodega_reportes_ro no debe acceder a auditoria_precio ni empleado';
    END IF;

    IF NOT has_table_privilege('bodega_api_rw', 'public.vino', 'INSERT')
       OR NOT has_table_privilege('bodega_api_rw', 'public.renglon_comprobante', 'INSERT')
       OR NOT has_table_privilege('bodega_api_rw', 'public.v_stock_total_por_vino', 'SELECT') THEN
        RAISE EXCEPTION '007: faltan permisos minimos de la API';
    END IF;

    IF NOT has_table_privilege('bodega_reportes_ro', 'public.v_ventas_mensuales_por_sala', 'SELECT') THEN
        RAISE EXCEPTION '007: faltan permisos minimos de reportes';
    END IF;
END
$verificaciones$;

COMMIT;
