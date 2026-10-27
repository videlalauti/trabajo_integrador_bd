-- Paso 7 - Pruebas con sesiones LOGIN reales. Ejecutar API ANTES de ADMIN.
-- No usa tablas temporales: 007 revoca TEMPORARY a API/reportes.
\set ON_ERROR_STOP on
\pset pager off
SELECT current_user,session_user,current_database();
DO $$
DECLARE u text:=session_user; v integer; precio_antes numeric; precio_despues numeric; aud integer;
BEGIN
 IF current_user<>session_user THEN RAISE EXCEPTION 'Requiere conexión real (no SET ROLE)'; END IF;
 IF u NOT IN ('bodega_api','bodega_admin','bodega_reportes') THEN
  RAISE EXCEPTION 'Usuario no esperado: %',u;
 END IF;
 IF NOT has_database_privilege(u,current_database(),'CONNECT') THEN RAISE EXCEPTION 'CONNECT denegado para %',u; END IF;
 IF u IN ('bodega_api','bodega_reportes') AND
   (has_database_privilege(u,current_database(),'CREATE') OR
    has_database_privilege(u,current_database(),'TEMPORARY') OR
    has_schema_privilege(u,'public','CREATE')) THEN
   RAISE EXCEPTION 'Privilegios DDL/TEMP excesivos para %',u;
 END IF;
 IF u='bodega_admin' THEN
  PERFORM 1 FROM public.empleado LIMIT 1;
  PERFORM 1 FROM public.auditoria_precio LIMIT 1;
  SELECT cod_vino INTO STRICT v FROM public.vino WHERE nombre='PASO7_VINO_API';
  SELECT COUNT(*) INTO aud FROM public.auditoria_precio
    WHERE cod_vino=v AND usuario='bodega_api' AND precio_anterior=900 AND precio_nuevo=901;
  IF aud<>1 THEN RAISE EXCEPTION 'Auditoría desde LOGIN bodega_api incorrecta: % registros (se esperaba 1)',aud; END IF;
  RAISE NOTICE 'OK ADMIN: empleado, auditoría API (session_user), permisos';
 ELSIF u='bodega_api' THEN
  IF has_table_privilege(u,'public.auditoria_precio','SELECT') THEN RAISE EXCEPTION 'API puede leer auditoría'; END IF;
  SELECT cod_vino INTO STRICT v FROM public.vino WHERE nombre='PASO7_VINO_API';
  SELECT precio INTO precio_antes FROM public.vino WHERE cod_vino=v;
  IF precio_antes<>900 THEN RAISE EXCEPTION 'Precio previo esperado 900, obtenido % (ejecutar sobre base limpia)',precio_antes; END IF;
  UPDATE public.vino SET precio=901 WHERE cod_vino=v;
  SELECT precio INTO precio_despues FROM public.vino WHERE cod_vino=v;
  IF precio_despues<>901 THEN RAISE EXCEPTION 'API no pudo actualizar precio'; END IF;
  UPDATE public.vino SET precio=precio WHERE cod_vino=v;
  RAISE NOTICE 'OK API: UPDATE autorizado precio 900 -> 901';
 ELSIF u='bodega_reportes' THEN
  PERFORM 1 FROM public.v_stock_total_por_vino LIMIT 1;
  PERFORM 1 FROM public.v_ventas_mensuales_por_sala LIMIT 1;
  PERFORM 1 FROM public.v_documentos_pendientes LIMIT 1;
  RAISE NOTICE 'OK REPORTES: lectura de vistas';
 END IF;
END $$;

-- Casos negativos: se espera SQLSTATE 42501 (insufficient_privilege) en
-- operaciones no autorizadas. Se verifica el codigo real de cada excepcion,
-- sin capturar como exito los errores que generan nuestras propias aserciones.
DO $$
DECLARE u text:=session_user; hubo boolean; codigo text; mensaje text;
BEGIN
 IF u NOT IN ('bodega_api','bodega_reportes') THEN RETURN; END IF;
 hubo:=false;
  -- Error esperado: 42501 al intentar leer empleado desde API o reportes.
 BEGIN PERFORM 1 FROM public.empleado LIMIT 1;
 EXCEPTION WHEN OTHERS THEN hubo:=true; codigo:=SQLSTATE; mensaje:=SQLERRM; END;
 IF NOT hubo OR codigo IS DISTINCT FROM '42501' THEN
   RAISE EXCEPTION 'Usuario % debería tener 42501 al leer empleado; error % (%)',u,codigo,mensaje;
 END IF;
 RAISE NOTICE 'OK %: empleado denegado 42501',u;
 hubo:=false; codigo:=NULL;
  -- Error esperado: 42501 al intentar consultar auditoria de precios.
 BEGIN PERFORM 1 FROM public.auditoria_precio LIMIT 1;
 EXCEPTION WHEN OTHERS THEN hubo:=true; codigo:=SQLSTATE; mensaje:=SQLERRM; END;
 IF NOT hubo OR codigo IS DISTINCT FROM '42501' THEN RAISE EXCEPTION '% debería tener 42501 leyendo auditoría; %',u,codigo; END IF;
 RAISE NOTICE 'OK %: auditoría denegada 42501',u;
 hubo:=false; codigo:=NULL;
  -- Error esperado: 42501 al intentar actualizar stock_sala.
  -- WHERE false evita modificar filas; PostgreSQL igualmente comprueba UPDATE.
 BEGIN UPDATE public.stock_sala SET cantidad=cantidad WHERE false;
 EXCEPTION WHEN OTHERS THEN hubo:=true; codigo:=SQLSTATE; mensaje:=SQLERRM; END;
 IF NOT hubo OR codigo IS DISTINCT FROM '42501' THEN RAISE EXCEPTION '% debería tener 42501 actualizando stock; %',u,codigo; END IF;
 RAISE NOTICE 'OK %: UPDATE stock denegado 42501',u;
 IF u='bodega_api' THEN
  hubo:=false;codigo:=NULL;
   -- Error esperado: 42501 al intentar modificar directamente el estado de un ingreso.
   -- WHERE false evita cambios reales, pero el permiso UPDATE sigue siendo necesario.
  BEGIN UPDATE public.ingreso SET estado='terminado' WHERE false;
  EXCEPTION WHEN OTHERS THEN hubo:=true;codigo:=SQLSTATE;mensaje:=SQLERRM;END;
  IF NOT hubo OR codigo IS DISTINCT FROM '42501' THEN RAISE EXCEPTION 'API debería tener 42501 actualizando estado; %',codigo;END IF;
  RAISE NOTICE 'OK API: UPDATE estado denegado';
 END IF;
END $$;

\echo 'ROLES_RESULTADO: PASO (si se llegó aquí sin errores)'
