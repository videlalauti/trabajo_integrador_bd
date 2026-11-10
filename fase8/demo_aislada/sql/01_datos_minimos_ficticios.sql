-- Dataset MINIMO 100% ficticio. Solo para el proyecto Supabase demo zfxocudcvriicrzgmxie.
-- No es el perfil SMALL completo, no replica datos personales ni historicos FULL.
BEGIN;
DO $gate$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM fase8_control.proyecto WHERE ref='zfxocudcvriicrzgmxie')
    OR current_user <> 'postgres'
    OR EXISTS (SELECT 1 FROM public.vino)
    OR EXISTS (SELECT 1 FROM public.cliente)
    OR EXISTS (SELECT 1 FROM public.stock_sala)
 THEN RAISE EXCEPTION 'STOP: proyecto inesperado o datos ya cargados'; END IF;
END $gate$;

DO $datos$
DECLARE
  v_localidad INTEGER;
  v_sala1 INTEGER;
  v_sala2 INTEGER;
  v_cepa INTEGER;
  v_maridaje INTEGER;
  v_vino INTEGER;
  v_i INTEGER;
BEGIN
 INSERT INTO public.localidad (cod_postal,nombre,provincia,encargado_regional)
 VALUES ('5500','LOCALIDAD FICTICIA DEMO','Mendoza','RESPONSABLE FICTICIO')
 RETURNING id_localidad INTO v_localidad;

 INSERT INTO public.sala_venta(calle,numero,dia_cierre,id_localidad)
 VALUES ('CALLE DE ENSAYO','S/N','lunes',v_localidad) RETURNING id_sala INTO v_sala1;
 INSERT INTO public.sala_venta(calle,numero,dia_cierre,id_localidad)
 VALUES ('CALLE DE PRUEBA','S/N','martes',v_localidad) RETURNING id_sala INTO v_sala2;

 INSERT INTO public.bodega(cuit,razon_social,domicilio)
 VALUES ('00000000001','BODEGA COMPLETAMENTE FICTICIA','DOMICILIO DE ENSAYO');

 INSERT INTO public.cepa(nombre,tipo)
 VALUES ('CEPA FICTICIA TINTA','tinta') RETURNING id_cepa INTO v_cepa;
 INSERT INTO public.maridaje(nombre,temperatura_servicio_c)
 VALUES ('MARIDAJE FICTICIO',16) RETURNING id_maridaje INTO v_maridaje;

 INSERT INTO public.tipo_cliente(tipo_cliente,descuento)
 VALUES ('socio',10),('distribuidor',20),('exportador',30);

 INSERT INTO public.cliente(nombre_razon_social,tipo_doc,nro_doc,direccion,id_localidad,tipo_cliente,descuento_especial)
 VALUES
 ('CLIENTE FICTICIO A','DNI','DEMO000001','DOMICILIO FICTICIO',v_localidad,'socio',NULL),
 ('CLIENTE FICTICIO B','DNI','DEMO000002','DOMICILIO FICTICIO',v_localidad,'socio',NULL);

 FOR v_i IN 1..3 LOOP
    INSERT INTO public.vino(nombre,tipo,anada,volumen_ml,graduacion,precio,cuit_bodega)
    VALUES ('VINO FICTICIO DEMO '||v_i,'tinto',2024,750,13.5,1200+100*v_i,'00000000001')
    RETURNING cod_vino INTO v_vino;
    INSERT INTO public.vino_cepa(cod_vino,id_cepa,porcentaje) VALUES (v_vino,v_cepa,100);
    INSERT INTO public.vino_maridaje(cod_vino,id_maridaje) VALUES (v_vino,v_maridaje);
    INSERT INTO public.stock_deposito(cod_vino,cantidad) VALUES (v_vino,120);
    INSERT INTO public.stock_sala(id_sala,cod_vino,cantidad)
       VALUES (v_sala1,v_vino,30),(v_sala2,v_vino,25);
 END LOOP;
END $datos$;
COMMIT;
