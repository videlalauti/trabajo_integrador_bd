-- I1 | Responsable: Jose | Origen: fase5/evidencias/jose/I1.sql
-- I1: Incorporar una nueva cobertura de General Alvear
-- al transportista con menos ingresos en el ultimo trimestre.
--

BEGIN;

-- Control anterior.
SELECT COUNT(*) AS coberturas_antes
FROM public.transportista_localidad
WHERE cod_transporte = 10
  AND id_localidad = 2;

-- Insercion solicitada.
INSERT INTO public.transportista_localidad
    (cod_transporte, id_localidad)
SELECT t.cod_transporte, l.id_localidad
FROM public.transportista AS t
CROSS JOIN public.localidad AS l
WHERE l.nombre = 'General Alvear'
  AND l.provincia = 'Mendoza'
  AND t.cod_transporte = (
      SELECT t2.cod_transporte
      FROM public.transportista AS t2
      LEFT JOIN public.ingreso AS i
          ON i.cod_transporte = t2.cod_transporte
         AND i.fecha >= CURRENT_DATE - INTERVAL '3 months'
         AND i.fecha <= CURRENT_DATE
      GROUP BY t2.cod_transporte
      ORDER BY COUNT(i.cod_ingreso) ASC,
               t2.cod_transporte ASC
      LIMIT 1
  )
  AND NOT EXISTS (
      SELECT 1
      FROM public.transportista_localidad AS tl
      WHERE tl.cod_transporte = t.cod_transporte
        AND tl.id_localidad = l.id_localidad
  )
RETURNING cod_transporte, id_localidad;

-- Control posterior.
SELECT
    t.cod_transporte,
    t.razon_social,
    l.id_localidad,
    l.nombre AS localidad,
    l.provincia
FROM public.transportista_localidad AS tl
JOIN public.transportista AS t
    ON t.cod_transporte = tl.cod_transporte
JOIN public.localidad AS l
    ON l.id_localidad = tl.id_localidad
WHERE tl.cod_transporte = 10
  AND tl.id_localidad = 2;

ROLLBACK;


-- I2 | Responsable: Lautaro | Origen: fase5/evidencias/lautaro/i2_prueba_transaccional.sql
-- I2: Prueba transaccional.
BEGIN;

-- ANTES: vinos elegibles.
SELECT COUNT(*) AS vinos_elegibles
FROM vino
WHERE tipo = 'tinto'
  AND graduacion >= 14;

-- ANTES: maridajes y asociaciones existentes.
SELECT COUNT(*) AS maridajes_existentes
FROM maridaje
WHERE LOWER(nombre) = 'cordero al disco';

SELECT COUNT(*) AS asociaciones_antes
FROM vino_maridaje vm
JOIN maridaje m ON m.id_maridaje = vm.id_maridaje
WHERE LOWER(m.nombre) = 'cordero al disco';

-- MODIFICACION: ambas inserciones.


INSERT INTO maridaje (nombre, temperatura_servicio_c)
SELECT 'cordero al disco', 13.0
WHERE EXISTS (
    SELECT 1
    FROM vino
    WHERE tipo = 'tinto'
      AND graduacion >= 14
)
AND NOT EXISTS (
    SELECT 1
    FROM maridaje
    WHERE LOWER(nombre) = 'cordero al disco'
);

INSERT INTO vino_maridaje (cod_vino, id_maridaje)
SELECT
    v.cod_vino,
    m.id_maridaje
FROM vino v
CROSS JOIN maridaje m
WHERE v.tipo = 'tinto'
  AND v.graduacion >= 14
  AND LOWER(m.nombre) = 'cordero al disco'
ON CONFLICT (cod_vino, id_maridaje) DO NOTHING;


-- DESPUES: verificar maridaje y asociaciones.
SELECT COUNT(*) AS maridajes_despues
FROM maridaje
WHERE LOWER(nombre) = 'cordero al disco';

SELECT COUNT(*) AS asociaciones_despues
FROM vino_maridaje vm
JOIN maridaje m ON m.id_maridaje = vm.id_maridaje
WHERE LOWER(m.nombre) = 'cordero al disco';

ROLLBACK;


-- I3 | Responsable: Fabricio | Origen: fase5/evidencias/fabricio/I3.sql
-- I3 - Insertar un comprobante con tres renglones

BEGIN;

-- Control anterior: comprobar que no existe el comprobante.
SELECT COUNT(*) AS comprobante_antes
FROM public.comprobante
WHERE nro_comprobante = 150001;

-- Control anterior: cliente y descuento real.
SELECT
    c.id_cliente,
    c.nombre_razon_social,
    c.tipo_cliente,
    public.fn_descuento_cliente(c.id_cliente) AS descuento
FROM public.cliente c
WHERE c.id_cliente = 1;

-- Control anterior: precios y stock de los tres vinos.
SELECT
    v.cod_vino,
    v.nombre,
    v.precio,
    public.fn_stock_sala(1, v.cod_vino) AS stock_antes
FROM public.vino v
WHERE v.cod_vino IN (15, 19, 23)
ORDER BY v.cod_vino;

-- I3: insertar la cabecera.
-- La fecha toma CURRENT_TIMESTAMP por defecto.
-- El trigger inicializa los importes en cero.
INSERT INTO public.comprobante
    (nro_comprobante, id_cliente, id_sala)
VALUES
    (150001, 1, 1);

-- I3: insertar tres renglones.
-- Los precios se obtienen de los vinos reales.
-- El trigger comprueba stock, aplica el descuento
-- y calcula el subtotal de cada renglon.
INSERT INTO public.renglon_comprobante
    (nro_comprobante, cod_vino, cantidad,
     precio_unitario, descuento, subtotal)
SELECT
    150001,
    v.cod_vino,
    datos.cantidad,
    v.precio,
    public.fn_descuento_cliente(1),
    0.00
FROM (
    VALUES
        (15, 1),
        (19, 2),
        (23, 3)
) AS datos(cod_vino, cantidad)
JOIN public.vino v
    ON v.cod_vino = datos.cod_vino;

-- Control posterior: verificar los tres renglones.
SELECT
    nro_comprobante,
    cod_vino,
    cantidad,
    precio_unitario,
    descuento,
    subtotal
FROM public.renglon_comprobante
WHERE nro_comprobante = 150001
ORDER BY cod_vino;

-- Control posterior: contar renglones y botellas.
SELECT
    COUNT(*) AS renglones_insertados,
    SUM(cantidad) AS botellas_vendidas
FROM public.renglon_comprobante
WHERE nro_comprobante = 150001;

-- Control posterior: comparar importes almacenados
-- con los calculados por fn_total_comprobante.
SELECT
    c.nro_comprobante,
    c.id_cliente,
    c.id_sala,
    c.subtotal AS subtotal_guardado,
    c.descuento AS descuento_guardado,
    c.total AS total_guardado,
    t.o_subtotal AS subtotal_calculado,
    t.o_descuento AS descuento_calculado,
    t.o_total AS total_calculado
FROM public.comprobante c
CROSS JOIN LATERAL public.fn_total_comprobante(
    c.nro_comprobante
) AS t
WHERE c.nro_comprobante = 150001;

-- Control posterior: stock tras las inserciones.
SELECT
    v.cod_vino,
    public.fn_stock_sala(1, v.cod_vino) AS stock_despues
FROM public.vino v
WHERE v.cod_vino IN (15, 19, 23)
ORDER BY v.cod_vino;

-- Deshacer cabecera, renglones y cambios de stock.
ROLLBACK;

-- Control final: el comprobante no debe permanecer.
SELECT COUNT(*) AS comprobante_tras_rollback
FROM public.comprobante
WHERE nro_comprobante = 150001;

-- Control final: comprobar restauracion del stock.
SELECT
    v.cod_vino,
    public.fn_stock_sala(1, v.cod_vino) AS stock_restaurado
FROM public.vino v
WHERE v.cod_vino IN (15, 19, 23)
ORDER BY v.cod_vino;


-- I4 | Responsable: Valentino | Origen: fase5/evidencias/valentino/I4.sql
-- I4. Insertar una nueva bodega.

BEGIN;

-- Estado anterior: comprobar que la bodega no exista.
SELECT cuit, razon_social, domicilio
FROM bodega
WHERE cuit = '30999876540';

-- Inserción de la bodega (una fila).
INSERT INTO bodega (cuit, razon_social, domicilio)
VALUES (
    '30999876540',
    'Bodega Valle del Atuel SRL',
    'Av. Mitre 1250, San Rafael, Mendoza'
);

-- Estado posterior: verificar los datos insertados.
SELECT cuit, razon_social, domicilio
FROM bodega
WHERE cuit = '30999876540';

-- Deshacer la prueba.
ROLLBACK;

-- Verificar que no quedó ningún registro de prueba.
SELECT cuit, razon_social, domicilio
FROM bodega
WHERE cuit = '30999876540';



-- I5 | Responsable: Jose | Origen: fase5/evidencias/jose/I5.sql
-- I5: Insertar una nueva sala de venta.

BEGIN;

-- Control anterior.
SELECT COUNT(*) AS salas_antes
FROM public.sala_venta
WHERE calle = 'Calle Integrador Fase 5'
  AND numero = '901';

-- Insercion solicitada.
INSERT INTO public.sala_venta
    (calle, numero, dia_cierre, id_localidad)
VALUES
    ('Calle Integrador Fase 5', '901', 'martes', 1)
RETURNING
    id_sala, calle, numero, dia_cierre, id_localidad;

-- Control posterior.
SELECT
    s.id_sala,
    s.calle,
    s.numero,
    s.dia_cierre,
    l.nombre AS localidad,
    l.provincia
FROM public.sala_venta AS s
JOIN public.localidad AS l
    ON l.id_localidad = s.id_localidad
WHERE s.calle = 'Calle Integrador Fase 5'
  AND s.numero = '901';

ROLLBACK;



-- I6 | Responsable: Antonio | Origen: fase5/evidencias/antonio/I6.sql
-- I6 - Crear un ingreso en confeccion de 120 botellas de un vino
--      determinado, elaborado por una bodega dada y trasladado por un
--      transportista dado.

BEGIN;

-- Control previo 1: cantidad de ingresos y renglones, e ingresos en confeccion
SELECT (SELECT count(*) FROM ingreso)                                   AS ingresos,
       (SELECT count(*) FROM ingreso WHERE estado = 'en_confeccion')    AS ingresos_en_confeccion,
       (SELECT count(*) FROM renglon_ingreso)                           AS renglones_ingreso;

-- Control previo 2: stock del vino en el deposito central (no debe cambiar)
SELECT v.cod_vino, v.nombre, COALESCE(sd.cantidad, 0) AS stock_deposito
FROM vino AS v
LEFT JOIN stock_deposito AS sd ON sd.cod_vino = v.cod_vino
WHERE v.nombre = 'Fuego Atuel 0125' AND v.anada = 2023 AND v.volumen_ml = 750;

-- Sentencia 1: cabecera del ingreso (estado por DEFAULT)
INSERT INTO ingreso (fecha, cod_transporte, cuit_bodega)
SELECT CURRENT_DATE, t.cod_transporte, b.cuit
FROM transportista AS t
CROSS JOIN bodega AS b
WHERE t.razon_social = 'Transportes DEMO Atuel 001'
  AND b.razon_social = 'Bodega DEMO Atuel 001'
RETURNING cod_ingreso, fecha, estado, cod_transporte, cuit_bodega;

-- Sentencia 2: renglon con las 120 botellas del vino de esa bodega
INSERT INTO renglon_ingreso (cod_ingreso, cod_vino, cantidad)
SELECT i.cod_ingreso, v.cod_vino, 120
FROM ingreso AS i
JOIN vino AS v ON v.cuit_bodega = i.cuit_bodega
WHERE i.cod_ingreso = currval(pg_get_serial_sequence('ingreso', 'cod_ingreso'))
  AND v.nombre = 'Fuego Atuel 0125'
  AND v.anada = 2023 AND v.volumen_ml = 750
RETURNING cod_ingreso, cod_vino, cantidad;

-- Control posterior 1: el ingreso nuevo completo, con sus datos legibles
SELECT i.cod_ingreso, i.fecha, i.estado, t.razon_social AS transportista,
       b.razon_social AS bodega, v.nombre AS vino, v.volumen_ml, r.cantidad
FROM ingreso AS i
JOIN transportista   AS t ON t.cod_transporte = i.cod_transporte
JOIN bodega          AS b ON b.cuit = i.cuit_bodega
JOIN renglon_ingreso AS r ON r.cod_ingreso = i.cod_ingreso
JOIN vino            AS v ON v.cod_vino = r.cod_vino
WHERE i.cod_ingreso = currval(pg_get_serial_sequence('ingreso', 'cod_ingreso'));

-- Control posterior 2: cantidades (+1 ingreso, +1 en confeccion, +1 renglon)
SELECT (SELECT count(*) FROM ingreso)                                   AS ingresos,
       (SELECT count(*) FROM ingreso WHERE estado = 'en_confeccion')    AS ingresos_en_confeccion,
       (SELECT count(*) FROM renglon_ingreso)                           AS renglones_ingreso;

-- Control posterior 3: RN-10, el stock del deposito NO cambia
SELECT v.cod_vino, v.nombre, COALESCE(sd.cantidad, 0) AS stock_deposito
FROM vino AS v
LEFT JOIN stock_deposito AS sd ON sd.cod_vino = v.cod_vino
WHERE v.nombre = 'Fuego Atuel 0125' AND v.anada = 2023 AND v.volumen_ml = 750;

-- Control posterior 4: el ingreso aparece como documento pendiente (vista)
SELECT tipo_documento, nro_documento, fecha, estado, cuit_bodega, cod_transporte
FROM v_documentos_pendientes
WHERE tipo_documento = 'INGRESO'
  AND nro_documento = currval(pg_get_serial_sequence('ingreso', 'cod_ingreso'));

-- Verificar ahora cualquier control diferido antes de deshacer
SET CONSTRAINTS ALL IMMEDIATE;

ROLLBACK;

-- Control despues del ROLLBACK: cantidades y stock como en el control previo
SELECT (SELECT count(*) FROM ingreso)                                   AS ingresos,
       (SELECT count(*) FROM ingreso WHERE estado = 'en_confeccion')    AS ingresos_en_confeccion,
       (SELECT count(*) FROM renglon_ingreso)                           AS renglones_ingreso;

SELECT v.cod_vino, v.nombre, COALESCE(sd.cantidad, 0) AS stock_deposito
FROM vino AS v
LEFT JOIN stock_deposito AS sd ON sd.cod_vino = v.cod_vino
WHERE v.nombre = 'Fuego Atuel 0125' AND v.anada = 2023 AND v.volumen_ml = 750;