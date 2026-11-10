-- PRUEBA CONTROLADA: ejecuta una venta, RN-09 y transferencia dentro
-- de UNA transaccion que SIEMPRE se revierte con ROLLBACK.
-- SOLO Supabase de ensayo zfxocudcvriicrzgmxie; prohibido en FULL.
-- Los identificadores de secuencias pueden avanzar pese al ROLLBACK.
BEGIN;
DO $guard$
BEGIN
 IF current_user <> 'postgres'
    OR NOT EXISTS (SELECT 1 FROM fase8_control.proyecto WHERE ref='zfxocudcvriicrzgmxie')
    OR (SELECT COUNT(*) FROM public.cliente) <> 2
    OR (SELECT COUNT(*) FROM public.vino) <> 3
    OR (SELECT COUNT(*) FROM public.comprobante) <> 0
    OR (SELECT COUNT(*) FROM public.transferencia) <> 0
 THEN RAISE EXCEPTION 'STOP: entorno de ensayo no es el esperado'; END IF;
END $guard$;

-- Membership temporal para probar credenciales efectivas sin configurar LOGIN;
-- este GRANT se revierte integramente al ROLLBACK.
GRANT bodega_api TO postgres WITH INHERIT FALSE, SET TRUE;
SET LOCAL ROLE bodega_api;

DO $prueba$
DECLARE
  p_cliente INT;
  p_sala INT;
  p_vino INT;
  n_venta INT;
  n_trans INT;
  st_antes INT;
  dep_antes INT;
  cantidad_rechazo INT;
  rechazado BOOLEAN := FALSE;
  st_tras_venta INT;
  subtotal_venta NUMERIC;
BEGIN
 IF current_user <> 'bodega_api' THEN
   RAISE EXCEPTION 'STOP: prueba debe usar bodega_api';
 END IF;
 SELECT id_cliente INTO p_cliente FROM public.cliente ORDER BY id_cliente LIMIT 1;
 SELECT id_sala INTO p_sala FROM public.sala_venta ORDER BY id_sala LIMIT 1;
 SELECT cod_vino INTO p_vino FROM public.vino ORDER BY cod_vino LIMIT 1;

 SELECT cantidad INTO st_antes FROM public.stock_sala WHERE id_sala=p_sala AND cod_vino=p_vino;
 SELECT cantidad INTO dep_antes FROM public.stock_deposito WHERE cod_vino=p_vino;
 IF st_antes < 2 OR dep_antes < 2 THEN
   RAISE EXCEPTION 'STOP: stock de ensayo insuficiente';
 END IF;

 -- VENTA VALIDA: reglas RN-06, RN-08 y RN-09 disparadas en PostgreSQL.
 INSERT INTO public.comprobante(fecha,id_cliente,id_sala,subtotal,descuento,total)
 VALUES (CURRENT_TIMESTAMP,p_cliente,p_sala,0,0,0)
 RETURNING nro_comprobante INTO n_venta;

 INSERT INTO public.renglon_comprobante
    (nro_comprobante,cod_vino,cantidad,precio_unitario,descuento,subtotal)
 SELECT n_venta,v.cod_vino,1,v.precio,0,0
 FROM public.vino v WHERE v.cod_vino=p_vino;

 SELECT cantidad INTO st_tras_venta FROM public.stock_sala
 WHERE id_sala=p_sala AND cod_vino=p_vino;
 IF st_tras_venta <> st_antes-1 THEN
   RAISE EXCEPTION 'STOP: venta no desconto exactamente 1 botella';
 END IF;
 SELECT total INTO subtotal_venta FROM public.comprobante WHERE nro_comprobante=n_venta;
 IF subtotal_venta IS NULL OR subtotal_venta <= 0 THEN
   RAISE EXCEPTION 'STOP: total de venta no calculado';
 END IF;

 -- RN-09: la excepcion crea una subtransaccion cuyo encabezado/renglon
 -- se revierten automaticamente. El stock y los conteos deben persistir
 -- sin cambios respecto a la venta valida.
 cantidad_rechazo := st_tras_venta+1;
 BEGIN
   INSERT INTO public.comprobante(fecha,id_cliente,id_sala,subtotal,descuento,total)
   VALUES (CURRENT_TIMESTAMP,p_cliente,p_sala,0,0,0)
   RETURNING nro_comprobante INTO n_venta;
   INSERT INTO public.renglon_comprobante
       (nro_comprobante,cod_vino,cantidad,precio_unitario,descuento,subtotal)
   SELECT n_venta,v.cod_vino,cantidad_rechazo,v.precio,0,0
   FROM public.vino v WHERE v.cod_vino=p_vino;
 EXCEPTION WHEN SQLSTATE 'P0001' THEN
   rechazado := TRUE;
 END;

 IF NOT rechazado THEN
   RAISE EXCEPTION 'STOP: RN-09 no rechazo la venta por P0001';
 END IF;
 IF (SELECT cantidad FROM public.stock_sala WHERE id_sala=p_sala AND cod_vino=p_vino) <> st_tras_venta
    OR (SELECT COUNT(*) FROM public.comprobante) <> 1
    OR (SELECT COUNT(*) FROM public.renglon_comprobante) <> 1
 THEN RAISE EXCEPTION 'STOP: RN-09 no conservo rollback completo'; END IF;

 -- TRANSFERENCIA: RN-11 y RN-12 usando procedimientos de la BD.
 INSERT INTO public.transferencia(id_sala) VALUES(p_sala)
 RETURNING nro_solicitud INTO n_trans;
 INSERT INTO public.renglon_transferencia(nro_solicitud,cod_vino,cantidad)
 VALUES(n_trans,p_vino,1);
 CALL public.sp_terminar_transferencia(n_trans);
 CALL public.sp_procesar_transferencia(n_trans);

 IF (SELECT estado FROM public.transferencia WHERE nro_solicitud=n_trans) <> 'procesado'
    OR (SELECT cantidad FROM public.stock_deposito WHERE cod_vino=p_vino) <> dep_antes-1
    OR (SELECT cantidad FROM public.stock_sala WHERE id_sala=p_sala AND cod_vino=p_vino) <> st_tras_venta+1
 THEN RAISE EXCEPTION 'STOP: transferencia no conservo movimientos de stock'; END IF;

 RAISE NOTICE 'DEMO CLOUD 3/3 OK: venta, RN-09 rollback, transferencia; ROLLBACK al final';
END $prueba$;
RESET ROLE;
ROLLBACK;

-- Poscondicion del ensayo: datos base intactos.
SELECT (SELECT COUNT(*) FROM public.comprobante) AS ventas_persistidas,
       (SELECT COUNT(*) FROM public.transferencia) AS transferencias_persistidas,
       (SELECT COALESCE(SUM(cantidad),0) FROM public.stock_sala) AS stock_sala,
       (SELECT COALESCE(SUM(cantidad),0) FROM public.stock_deposito) AS stock_deposito,
       (SELECT COUNT(*) FROM fase8_control.proyecto WHERE ref='zfxocudcvriicrzgmxie') AS identidad_demo;
