-- Bodegas del Atuel - Paso 7. Ejecutar SOLAMENTE en un cluster descartable PG16.
-- Requiere 001-007 compatibles con cuit_dom / tipo_vino / tipo_cepa.
\set ON_ERROR_STOP on
\pset pager off

CREATE TEMP TABLE t_resultado (bloque text, prueba text, sqlstate text);
CREATE TEMP TABLE t_ctx (id_sala integer, vino integer, cepa1 integer, cepa2 integer,
                         cliente integer, distribuidor integer, transporte integer,
                         bodega char(11), ingreso integer, transferencia integer,
                         comprobante integer);
CREATE FUNCTION pg_temp.ok(b text, p text, bien boolean) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 IF bien IS DISTINCT FROM TRUE THEN RAISE EXCEPTION 'FALLO [%] %', b,p; END IF;
 INSERT INTO t_resultado VALUES (b,p,NULL);
 RAISE NOTICE 'OK [%] %',b,p;
END $$;
-- En cada caso negativo se comprueba el SQLSTATE esperado y, si corresponde,
-- una parte del mensaje. Un error diferente o la ausencia de error hacen fallar el test.
CREATE FUNCTION pg_temp.error_esperado(b text,p text,sql_a_ejecutar text, codigo text, fragmento text DEFAULT NULL)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE fallo boolean:=false; codigo_real text; mensaje text;
BEGIN
 BEGIN
  EXECUTE sql_a_ejecutar;
 EXCEPTION WHEN OTHERS THEN
  fallo:=true; codigo_real:=SQLSTATE; mensaje:=SQLERRM;
 END;
 IF NOT fallo THEN RAISE EXCEPTION 'FALLO [%] %: operación aceptada',b,p; END IF;
 IF codigo_real IS DISTINCT FROM codigo OR
    (fragmento IS NOT NULL AND position(lower(fragmento) in lower(mensaje))=0) THEN
    RAISE EXCEPTION 'FALLO [%] %: esperado % (%); recibido % (%)',b,p,codigo,fragmento,codigo_real,mensaje;
 END IF;
 INSERT INTO t_resultado VALUES(b,p,codigo_real);
 RAISE NOTICE 'OK [%] % (%: %)',b,p,codigo_real,mensaje;
END $$;

\echo 'A: DATOS CONTROLADOS'
DO $$
DECLARE l integer; s integer; c1 integer; c2 integer; v integer; cl integer; cd integer; tr integer;
BEGIN
 INSERT INTO public.localidad(cod_postal,nombre,provincia,encargado_regional)
 VALUES('5600','San Rafael Test','Mendoza','Responsable') RETURNING id_localidad INTO l;
 INSERT INTO public.sala_venta(calle,numero,dia_cierre,id_localidad)
 VALUES('Mitre','123','viernes',l) RETURNING id_sala INTO s;
 INSERT INTO public.bodega(cuit,razon_social,domicilio)
 VALUES('30111111111','Bodega prueba','Ruta') ;
 INSERT INTO public.cepa(nombre,tipo) VALUES('Malbec Paso7','tinta') RETURNING id_cepa INTO c1;
 INSERT INTO public.cepa(nombre,tipo) VALUES('Cabernet Paso7','tinta') RETURNING id_cepa INTO c2;
 INSERT INTO public.tipo_cliente(tipo_cliente,descuento)
 VALUES('socio',10),('distribuidor',20),('exportador',30);
 INSERT INTO public.cliente(nombre_razon_social,tipo_doc,nro_doc,direccion,fecha_alta,id_localidad,tipo_cliente)
 VALUES('Socio paso7','DNI','11000001','Calle 1',CURRENT_DATE,l,'socio') RETURNING id_cliente INTO cl;
 INSERT INTO public.cliente(nombre_razon_social,tipo_doc,nro_doc,direccion,fecha_alta,id_localidad,tipo_cliente)
 VALUES('Distribuidor paso7','CUIT','20111111112','Calle 2',CURRENT_DATE,l,'distribuidor') RETURNING id_cliente INTO cd;
 INSERT INTO public.transportista(razon_social,cuit,email,telefono,domicilio)
 VALUES('Transportista prueba','30999999991','transportista@example.test','123','Ruta') RETURNING cod_transporte INTO tr;
 INSERT INTO public.vino(nombre,tipo,anada,volumen_ml,graduacion,precio,cuit_bodega)
 VALUES('PASO7_VINO_API','tinto',2020,750,14.5,850,'30111111111') RETURNING cod_vino INTO v;
 INSERT INTO public.vino_cepa(cod_vino,id_cepa,porcentaje) VALUES(v,c1,100);
 INSERT INTO public.stock_deposito(cod_vino,cantidad) VALUES(v,100);
 INSERT INTO public.stock_sala(id_sala,cod_vino,cantidad) VALUES(s,v,0);
 INSERT INTO t_ctx(id_sala,vino,cepa1,cepa2,cliente,distribuidor,transporte,bodega)
 VALUES(s,v,c1,c2,cl,cd,tr,'30111111111');
 PERFORM pg_temp.ok('A','stock inicial depósito 100', (SELECT cantidad FROM public.stock_deposito WHERE cod_vino=v)=100);
 PERFORM pg_temp.ok('A','stock inicial sala 0', public.fn_stock_sala(s,v)=0);
END $$;

\echo 'B: RESTRICCIONES'
-- Error esperado: SQLSTATE 23505 (unique_violation): vino duplicado por clave unica.
SELECT pg_temp.error_esperado('B','UNIQUE vino',format(
 'INSERT INTO public.vino(nombre,tipo,anada,volumen_ml,graduacion,precio,cuit_bodega) VALUES(%L,%L,2020,750,14.5,850,%L)',
 'PASO7_VINO_API','tinto','30111111111'),'23505');
-- Error esperado: SQLSTATE 23514 (check_violation): precio cero incumple CHECK de precio positivo.
SELECT pg_temp.error_esperado('B','precio mayor a cero',
 'INSERT INTO public.vino(nombre,tipo,anada,volumen_ml,graduacion,precio,cuit_bodega) SELECT ''Precio cero'', ''tinto'',2022,750,12,0,bodega FROM t_ctx','23514');
-- Error esperado: SQLSTATE 23503 (foreign_key_violation): localidad referenciada inexistente.
SELECT pg_temp.error_esperado('B','FK sala-localidad',
 'INSERT INTO public.sala_venta(calle,numero,dia_cierre,id_localidad) VALUES(''Calle'',''1'',''lunes'',999999)','23503');
-- Error esperado: SQLSTATE 23514 (check_violation): vencimiento no posterior a emision.
SELECT pg_temp.error_esperado('B','permiso exportación vencido',
 'INSERT INTO public.permiso_exportacion(codigo_permiso,id_cliente,fecha_emision,fecha_vencimiento) SELECT ''P7_INV'',cliente,current_date,current_date FROM t_ctx','23514');
-- Error esperado: SQLSTATE 23503 (foreign_key_violation): el vino tiene filas dependientes.
SELECT pg_temp.error_esperado('B','borrar vino con dependencias',
 'DELETE FROM public.vino WHERE cod_vino=(SELECT vino FROM t_ctx)','23503');


-- RN-03: Cada empleado trabaja en una sola sala. Mecanismo: FK obligatoria + NOT NULL.
-- Error esperado: SQLSTATE 23502 (not_null_violation) por omitir id_sala.
SELECT pg_temp.error_esperado('B','empleado sin sala',
  $$INSERT INTO public.empleado(cuit,nombre,fecha_ingreso,salario)
    VALUES('20111111112','Empleado sin sala',CURRENT_DATE,50000)$$,
  '23502','id_sala');

-- RN-04: Una parcela tiene una sola cepa y no puede cosecharse dos veces en una campania.
-- Mecanismo: FK + UNIQUE (id_finca, nro_parcela, campania).
-- Error esperado: SQLSTATE 23505 (unique_violation), restriccion uq_lote_uva_parcela_campania.
SELECT pg_temp.error_esperado('B','dos cosechas misma parcela-campania',
  $$DO $test$ DECLARE c t_ctx%ROWTYPE; f integer; BEGIN
       SELECT * INTO STRICT c FROM t_ctx;
       INSERT INTO public.finca(nombre,superficie_ha,departamento,provincia)
       VALUES('Finca Paso7 RN04',10,'San Rafael','Mendoza') RETURNING id_finca INTO f;
       INSERT INTO public.parcela(id_finca,nro_parcela,superficie_ha,anio_plantacion,id_cepa)
       VALUES(f,99,5,2018,c.cepa1);
       INSERT INTO public.lote_uva(campania,fecha_cosecha,kg_cosechados,id_finca,nro_parcela,cuit_bodega)
       VALUES(2024,CURRENT_DATE,1000,f,99,c.bodega);
       INSERT INTO public.lote_uva(campania,fecha_cosecha,kg_cosechados,id_finca,nro_parcela,cuit_bodega)
       VALUES(2024,CURRENT_DATE,1500,f,99,c.bodega);
     END $test$;$$,
  '23505','uq_lote_uva_parcela_campania');

-- RN-15: las superficies y la graduacion deben respetar sus rangos.
-- Error esperado: SQLSTATE 23514 (check_violation), CHECK de superficie positiva.
SELECT pg_temp.error_esperado('B','RN-15 superficie de finca negativa',
  $$INSERT INTO public.finca(nombre,superficie_ha,departamento,provincia)
    VALUES('Finca invalida RN15',-1,'San Rafael','Mendoza')$$,
  '23514','chk_finca_superficie');

-- RN-15: graduacion alcoholica entre 5 y 20.
-- Error esperado: SQLSTATE 23514 (check_violation), CHECK de graduacion.
SELECT pg_temp.error_esperado('B','RN-15 graduacion fuera de rango',
  $$INSERT INTO public.vino(nombre,tipo,anada,volumen_ml,graduacion,precio,cuit_bodega)
    SELECT 'VINO RN15 INVALIDO','tinto',2025,750,25,500,bodega FROM t_ctx$$,
  '23514','chk_vino_graduacion');

\echo 'C: FUNCIONES Y VENTA'
DO $$
DECLARE c t_ctx%ROWTYPE; nro integer; sub numeric; des numeric; tot numeric; d integer;
BEGIN
 SELECT * INTO STRICT c FROM t_ctx;
 PERFORM pg_temp.ok('C','fn_stock_sala cero exacto',public.fn_stock_sala(c.id_sala,c.vino)=0);
 PERFORM pg_temp.ok('C','descuento socio 10',public.fn_descuento_cliente(c.cliente)=10);
 PERFORM pg_temp.ok('C','descuento distribuidor 20',public.fn_descuento_cliente(c.distribuidor)=20);
 PERFORM pg_temp.ok('C','antigüedad años completos',public.fn_antiguedad_anios(current_date)=0);
 -- El comprobante queda en la base de pruebas para validar la vista mensual.
 INSERT INTO public.comprobante(fecha,id_cliente,id_sala,subtotal,descuento,total)
 VALUES(CURRENT_TIMESTAMP,c.cliente,c.id_sala,0,0,0) RETURNING nro_comprobante INTO nro;
 UPDATE t_ctx SET comprobante=nro;
 -- Primero se transfiere mercadería en el bloque D. Por eso no se insertan renglones aquí.
 SELECT o_subtotal,o_descuento,o_total INTO sub,des,tot FROM public.fn_total_comprobante(nro);
 PERFORM pg_temp.ok('C','comprobante vacío total 0',sub=0 AND des=0 AND tot=0);
END $$;

-- RN-06: descuento general del exportador, sin descuento especial.
-- Caso positivo: la funcion devuelve 30 (CHECK de tipo_cliente ya cargado en A).
DO $$
DECLARE v_exportador integer; v_localidad integer;
BEGIN
 SELECT s.id_localidad INTO STRICT v_localidad
 FROM public.sala_venta s JOIN t_ctx c ON c.id_sala=s.id_sala;
 INSERT INTO public.cliente(nombre_razon_social,tipo_doc,nro_doc,direccion,fecha_alta,id_localidad,tipo_cliente)
 VALUES('Exportador Paso7','CUIT','20999999999','Calle 3',CURRENT_DATE,v_localidad,'exportador')
 RETURNING id_cliente INTO v_exportador;
 PERFORM pg_temp.ok('C','RN-06 descuento exportador 30',
   public.fn_descuento_cliente(v_exportador)=30);
END $$;

\echo 'D: INGRESOS, TRANSFERENCIAS Y ESTADOS'
DO $$
DECLARE c t_ctx%ROWTYPE; ing integer; trans integer; dep integer; sala integer;
BEGIN
 SELECT * INTO STRICT c FROM t_ctx;
 INSERT INTO public.ingreso(fecha,estado,cod_transporte,cuit_bodega)
 VALUES(CURRENT_DATE,'en_confeccion',c.transporte,c.bodega) RETURNING cod_ingreso INTO ing;
 INSERT INTO public.renglon_ingreso(cod_ingreso,cod_vino,cantidad) VALUES(ing,c.vino,10);
 UPDATE t_ctx SET ingreso=ing;
 PERFORM pg_temp.ok('D','ingreso en confección',(SELECT estado FROM public.ingreso WHERE cod_ingreso=ing)='en_confeccion');
 CALL public.sp_terminar_ingreso(ing);
 PERFORM pg_temp.ok('D','ingreso terminado',(SELECT estado FROM public.ingreso WHERE cod_ingreso=ing)='terminado');
 PERFORM pg_temp.ok('D','terminar no cambia stock',(SELECT cantidad FROM public.stock_deposito WHERE cod_vino=c.vino)=100);
 CALL public.sp_procesar_ingreso(ing);
 PERFORM pg_temp.ok('D','ingreso procesado',(SELECT estado FROM public.ingreso WHERE cod_ingreso=ing)='procesado');
 PERFORM pg_temp.ok('D','ingreso agrega 10 a depósito',(SELECT cantidad FROM public.stock_deposito WHERE cod_vino=c.vino)=110);
 INSERT INTO public.transferencia(nro_solicitud,fecha_confeccion,estado,id_sala)
 VALUES(DEFAULT,CURRENT_DATE,'en_confeccion',c.id_sala) RETURNING nro_solicitud INTO trans;
 INSERT INTO public.renglon_transferencia(nro_solicitud,cod_vino,cantidad) VALUES(trans,c.vino,5);
 UPDATE t_ctx SET transferencia=trans;
 -- RN-15: una cantidad negativa en un renglon se rechaza por CHECK, no por estado.
 -- Error esperado: SQLSTATE 23514 (check_violation), chk_renglon_transferencia_cantidad.
 PERFORM pg_temp.error_esperado('D','RN-15 cantidad negativa en transferencia',
   format('UPDATE public.renglon_transferencia SET cantidad=-1 WHERE nro_solicitud=%s AND cod_vino=%s',trans,c.vino),
   '23514','chk_renglon_transferencia_cantidad');
 CALL public.sp_terminar_transferencia(trans);
 -- RN-11: la fecha de confeccion de la transferencia se fija a CURRENT_DATE.
 PERFORM pg_temp.ok('D','RN-11 fecha de transferencia actual',
   (SELECT fecha_confeccion FROM public.transferencia WHERE nro_solicitud=trans)=CURRENT_DATE);
 PERFORM pg_temp.ok('D','transferencia terminada',(SELECT estado FROM public.transferencia WHERE nro_solicitud=trans)='terminado');
 CALL public.sp_procesar_transferencia(trans);
 PERFORM pg_temp.ok('D','transferencia procesada',(SELECT estado FROM public.transferencia WHERE nro_solicitud=trans)='procesado');
 SELECT cantidad INTO dep FROM public.stock_deposito WHERE cod_vino=c.vino;
 SELECT cantidad INTO sala FROM public.stock_sala WHERE cod_vino=c.vino AND id_sala=c.id_sala;
 PERFORM pg_temp.ok('D','transferencia resta 5 depósito',dep=105);
 PERFORM pg_temp.ok('D','transferencia suma 5 sala',sala=5);
END $$;
-- Error esperado: SQLSTATE P0001 (raise_exception), mensaje contiene 'procesado':
-- un ingreso procesado no puede procesarse nuevamente.
SELECT pg_temp.error_esperado('D','no reprocesar ingreso',
 'DO $test$ DECLARE v_ing integer; BEGIN SELECT ingreso INTO STRICT v_ing FROM t_ctx; CALL public.sp_procesar_ingreso(v_ing); END $test$;','P0001','procesado');
-- Error esperado: SQLSTATE P0001 (raise_exception), mensaje contiene 'procesad':
-- una transferencia procesada no puede procesarse nuevamente.
SELECT pg_temp.error_esperado('D','no reprocesar transferencia',
 'DO $test$ DECLARE v_tr integer; BEGIN SELECT transferencia INTO STRICT v_tr FROM t_ctx; CALL public.sp_procesar_transferencia(v_tr); END $test$;','P0001','procesad');
-- Error esperado: SQLSTATE P0001 (raise_exception), mensaje contiene 'RN-12':
-- se rechaza editar renglones de un ingreso ya procesado.
SELECT pg_temp.error_esperado('D','no editar renglón procesado',
 'UPDATE public.renglon_ingreso SET cantidad=cantidad+1 WHERE cod_ingreso=(SELECT ingreso FROM t_ctx)','P0001','RN-12');

-- RN-11: fecha de confeccion inmutable, incluso cuando la transferencia esta procesada.
-- Error esperado: SQLSTATE P0001 (raise_exception), mensaje RN-11.
SELECT pg_temp.error_esperado('D','RN-11 no cambiar fecha de transferencia',
  'UPDATE public.transferencia SET fecha_confeccion=fecha_confeccion-1 WHERE nro_solicitud=(SELECT transferencia FROM t_ctx)',
  'P0001','RN-11');

-- RN-11: no se permite volver de procesado a terminado.
-- Error esperado: SQLSTATE P0001 (raise_exception), mensaje transicion de estado.
SELECT pg_temp.error_esperado('D','RN-11 no retroceder estado',
  'UPDATE public.transferencia SET estado=''terminado'' WHERE nro_solicitud=(SELECT transferencia FROM t_ctx)',
  'P0001','transicion de estado no permitida');

-- RN-14: una bodega con vinos/ingresos asociados no se puede eliminar.
-- Error esperado: SQLSTATE 23503 (foreign_key_violation).
SELECT pg_temp.error_esperado('D','RN-14 no borrar bodega con movimientos',
  'DELETE FROM public.bodega WHERE cuit=(SELECT bodega FROM t_ctx)',
  '23503');

-- RN-14: un transportista con ingresos asociados no se puede eliminar.
-- Error esperado: SQLSTATE 23503 (foreign_key_violation).
SELECT pg_temp.error_esperado('D','RN-14 no borrar transportista con ingresos',
  'DELETE FROM public.transportista WHERE cod_transporte=(SELECT transporte FROM t_ctx)',
  '23503');

\echo 'E: TRIGGERS, COMPOSICIÓN, VENTA, AUDITORÍA'
-- Error esperado en las dos pruebas siguientes: SQLSTATE P0001 (raise_exception),
-- mensaje contiene 'RN-05' por composicion de cepas distinta de 100 %.
-- La evaluacion diferida se fuerza dentro de la operacion capturada.
SELECT pg_temp.error_esperado('E','composición 99.99 rechazada',
 $$DO $test$ DECLARE v integer; BEGIN
    INSERT INTO public.vino(nombre,tipo,anada,volumen_ml,graduacion,precio,cuit_bodega)
    SELECT 'PASO7_BAD_9999','tinto',2024,750,13,900,bodega FROM t_ctx RETURNING cod_vino INTO v;
    INSERT INTO public.vino_cepa(cod_vino,id_cepa,porcentaje) SELECT v,cepa1,99.99 FROM t_ctx;
    SET CONSTRAINTS ALL IMMEDIATE;
 END $test$;$$,'P0001','RN-05');
SELECT pg_temp.error_esperado('E','vino sin cepas rechazado',
 $$DO $test$ BEGIN
    INSERT INTO public.vino(nombre,tipo,anada,volumen_ml,graduacion,precio,cuit_bodega)
    SELECT 'PASO7_SIN_CEPA','tinto',2024,750,13,900,bodega FROM t_ctx;
    SET CONSTRAINTS ALL IMMEDIATE;
 END $test$;$$,'P0001','RN-05');
DO $$
DECLARE v integer; suma numeric;
BEGIN
 INSERT INTO public.vino(nombre,tipo,anada,volumen_ml,graduacion,precio,cuit_bodega)
 SELECT 'PASO7_BLEND_6040','tinto',2023,750,13,500,bodega FROM t_ctx RETURNING cod_vino INTO v;
 INSERT INTO public.vino_cepa(cod_vino,id_cepa,porcentaje)
 SELECT v,cepa1,60 FROM t_ctx UNION ALL SELECT v,cepa2,40 FROM t_ctx;
 SELECT sum(porcentaje) INTO suma FROM public.vino_cepa WHERE cod_vino=v;
 PERFORM pg_temp.ok('E','blend suma exacta 100',suma=100 AND (SELECT count(*) FROM public.vino_cepa WHERE cod_vino=v)=2);
 -- Valida también los triggers diferidos antes de registrar resultado final.
 SET CONSTRAINTS ALL IMMEDIATE;
END $$;
-- Venta autorizada luego de la transferencia: 2 unidades a 100, descuento socio 10.
DO $$
DECLARE c t_ctx%ROWTYPE; sub numeric; des numeric; tot numeric; sala integer;
BEGIN
 SELECT * INTO STRICT c FROM t_ctx;
 INSERT INTO public.renglon_comprobante(nro_comprobante,cod_vino,cantidad,precio_unitario,descuento,subtotal)
 VALUES(c.comprobante,c.vino,2,100,0,0);
 SELECT subtotal,descuento,total INTO sub,des,tot FROM public.comprobante WHERE nro_comprobante=c.comprobante;
 PERFORM pg_temp.ok('E','venta subtotal 200',sub=200);
 PERFORM pg_temp.ok('E','venta descuento 20',des=20);
 PERFORM pg_temp.ok('E','venta total 180',tot=180);
 SELECT cantidad INTO sala FROM public.stock_sala WHERE id_sala=c.id_sala AND cod_vino=c.vino;
 PERFORM pg_temp.ok('E','venta descuenta 2 en sala',sala=3);
END $$;
-- Error esperado: SQLSTATE P0001 (raise_exception), mensaje contiene 'RN-09':
-- venta de 9999 unidades rechazada por stock insuficiente en sala.
SELECT pg_temp.error_esperado('E','venta 9999 rechazada RN-09',
 'UPDATE public.renglon_comprobante SET cantidad=9999 WHERE nro_comprobante=(SELECT comprobante FROM t_ctx)','P0001','RN-09');
DO $$
DECLARE c t_ctx%ROWTYPE; b integer; antes numeric; despues numeric;
BEGIN
 SELECT * INTO STRICT c FROM t_ctx;
 SELECT precio INTO antes FROM public.vino WHERE cod_vino=c.vino;
 UPDATE public.vino SET precio=precio+50 WHERE cod_vino=c.vino;
 SELECT precio INTO despues FROM public.vino WHERE cod_vino=c.vino;
 SELECT COUNT(*) INTO b FROM public.auditoria_precio WHERE cod_vino=c.vino;
 PERFORM pg_temp.ok('E','auditoría de cambio precio registrada',b=1 AND EXISTS (
    SELECT 1 FROM public.auditoria_precio WHERE cod_vino=c.vino AND precio_anterior=antes AND precio_nuevo=despues AND usuario=session_user));
 UPDATE public.vino SET precio=precio WHERE cod_vino=c.vino;
 PERFORM pg_temp.ok('E','sin cambio de precio no agrega auditoría',(SELECT COUNT(*) FROM public.auditoria_precio WHERE cod_vino=c.vino)=b);
END $$;

\echo 'F: VALIDACIÓN EXACTA DE VISTAS'
DO $$
DECLARE c t_ctx%ROWTYPE; n integer; b numeric;
BEGIN
 SELECT * INTO STRICT c FROM t_ctx;
 PERFORM pg_temp.ok('F','vista stock 105 depósito + 3 sala =108', EXISTS(
  SELECT 1 FROM public.v_stock_total_por_vino WHERE cod_vino=c.vino AND stock_deposito=105 AND stock_salas=3 AND stock_total=108));
 PERFORM pg_temp.ok('F','vista ventas una venta 180',EXISTS(
  SELECT 1 FROM public.v_ventas_mensuales_por_sala WHERE id_sala=c.id_sala AND anio=extract(year from current_date)
  AND mes=extract(month from current_date) AND cantidad_ventas=1 AND subtotal_bruto=200 AND descuento_total=20 AND total_monetario=180));
 PERFORM pg_temp.ok('F','procesados excluidos de vista pendientes',NOT EXISTS(
  SELECT 1 FROM public.v_documentos_pendientes
  WHERE (tipo_documento='INGRESO' AND nro_documento=c.ingreso)
     OR (tipo_documento='TRANSFERENCIA' AND nro_documento=c.transferencia)));
END $$;

\echo 'G: PRIVILEGIOS ESTRUCTURALES'
SELECT pg_temp.ok('G','API no actualiza stock',NOT has_table_privilege('bodega_api','public.stock_sala','UPDATE'));
SELECT pg_temp.ok('G','API sí actualiza precio vino',has_column_privilege('bodega_api','public.vino','precio','UPDATE'));
SELECT pg_temp.ok('G','reportes lee vista',has_table_privilege('bodega_reportes','public.v_stock_total_por_vino','SELECT'));
SELECT pg_temp.ok('G','reportes no edita vino',NOT has_table_privilege('bodega_reportes','public.vino','UPDATE'));
SELECT pg_temp.ok('G','API no lee auditoría',NOT has_table_privilege('bodega_api','public.auditoria_precio','SELECT'));
SELECT pg_temp.ok('G','API no asume dueño técnico',NOT pg_has_role('bodega_api','bodega_proc_owner','MEMBER'));
SELECT pg_temp.ok('G','API no crea esquemas',NOT has_database_privilege('bodega_api',current_database(),'CREATE'));
SELECT pg_temp.ok('G','reportes no crea temporales',NOT has_database_privilege('bodega_reportes',current_database(),'TEMPORARY'));

\echo 'RESUMEN PASO7 - si falla una aserción, ON_ERROR_STOP aborta'
SELECT bloque,count(*) AS aprobadas FROM t_resultado GROUP BY bloque ORDER BY bloque;
SELECT count(*) AS TOTAL_APROBADAS FROM t_resultado;
\echo 'PASO7_RESULTADO: PASO (sólo si psql llegó aquí sin errores)'
