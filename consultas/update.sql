-- U1 | Responsable: Lautaro | Origen: fase5/evidencias/lautaro/u1_prueba_transaccional.sql
-- U1: Prueba transaccional del recalculo de comprobantes.

BEGIN;

-- ANTES: cantidad de comprobantes y totales inconsistentes.
SELECT
    COUNT(*) AS comprobantes,
    COUNT(*) FILTER (
        WHERE c.subtotal IS DISTINCT FROM t.o_subtotal
           OR c.descuento IS DISTINCT FROM t.o_descuento
           OR c.total IS DISTINCT FROM t.o_total
    ) AS totales_inconsistentes
FROM comprobante c
CROSS JOIN LATERAL fn_total_comprobante(c.nro_comprobante) t;

-- MODIFICACION: activa trg_comprobante_totales.
UPDATE comprobante
SET total = total;

-- DESPUES: verificar nuevamente los totales.
SELECT
    COUNT(*) AS comprobantes,
    COUNT(*) FILTER (
        WHERE c.subtotal IS DISTINCT FROM t.o_subtotal
           OR c.descuento IS DISTINCT FROM t.o_descuento
           OR c.total IS DISTINCT FROM t.o_total
    ) AS totales_inconsistentes
FROM comprobante c
CROSS JOIN LATERAL fn_total_comprobante(c.nro_comprobante) t;

ROLLBACK;


-- U2 | Responsable: Jose | Origen: fase5/evidencias/jose/U2.sql
-- U2:Aumentar un 20% el salario de los empleados que
-- tengan mas de cinco años de antiguedad.

BEGIN;

-- Control anterior.
SELECT
    COUNT(*) AS total_empleados,
    COUNT(*) FILTER (
        WHERE fecha_ingreso < CURRENT_DATE - INTERVAL '5 years'
    ) AS elegibles,
    SUM(salario) AS suma_salarios
FROM empleado;

-- Modificacion solicitada.
UPDATE empleado
SET salario = ROUND(salario * 1.20, 2)
WHERE fecha_ingreso < CURRENT_DATE - INTERVAL '5 years';

-- Control posterior.
SELECT
    COUNT(*) AS total_empleados,
    COUNT(*) FILTER (
        WHERE fecha_ingreso < CURRENT_DATE - INTERVAL '5 years'
    ) AS elegibles,
    SUM(salario) AS suma_salarios
FROM empleado;

ROLLBACK;



-- U3 | Responsable: Antonio | Origen: fase5/evidencias/antonio/U3.sql
-- U3 - Incrementar un 13 % el precio de los vinos elaborados por una
--      bodega determinada.

BEGIN;

-- Control previo 1: vinos de la bodega y precios actuales
SELECT count(*)      AS vinos_bodega,
       sum(v.precio) AS suma_precios,
       min(v.precio) AS precio_min,
       max(v.precio) AS precio_max
FROM vino AS v
JOIN bodega AS b ON b.cuit = v.cuit_bodega
WHERE b.razon_social = 'Bodega DEMO Atuel 001';

-- Control previo 2: filas actuales en la auditoria de precios
SELECT count(*) AS filas_auditoria_antes FROM auditoria_precio;

-- Sentencia de la consigna (psql informa la cantidad de filas: UPDATE n)
UPDATE vino AS v
SET    precio = ROUND(v.precio * 1.13, 2)
FROM   bodega AS b
WHERE  b.cuit = v.cuit_bodega
  AND  b.razon_social = 'Bodega DEMO Atuel 001';

-- Control posterior 1: mismos vinos con los precios nuevos
SELECT count(*)      AS vinos_bodega,
       sum(v.precio) AS suma_precios,
       min(v.precio) AS precio_min,
       max(v.precio) AS precio_max
FROM vino AS v
JOIN bodega AS b ON b.cuit = v.cuit_bodega
WHERE b.razon_social = 'Bodega DEMO Atuel 001';

-- Control posterior 2: el trigger RN-13 debe haber agregado una fila por vino
SELECT count(*) AS filas_auditoria_despues FROM auditoria_precio;

-- Control posterior 3: cada fila de auditoria nueva refleja exactamente +13 %
SELECT count(*) AS auditorias_nuevas,
       count(*) FILTER (WHERE a.precio_nuevo <> ROUND(a.precio_anterior * 1.13, 2))
                AS auditorias_incorrectas
FROM auditoria_precio AS a
JOIN vino   AS v ON v.cod_vino = a.cod_vino
JOIN bodega AS b ON b.cuit = v.cuit_bodega
WHERE b.razon_social = 'Bodega DEMO Atuel 001';

-- Control posterior 4: muestra de 5 registros de auditoria
SELECT a.cod_vino, a.precio_anterior, a.precio_nuevo, a.fecha_hora, a.usuario
FROM auditoria_precio AS a
JOIN vino   AS v ON v.cod_vino = a.cod_vino
JOIN bodega AS b ON b.cuit = v.cuit_bodega
WHERE b.razon_social = 'Bodega DEMO Atuel 001'
ORDER BY a.cod_vino
LIMIT 5;

-- Verificar ahora los controles diferidos de vino (RN-05)
SET CONSTRAINTS ALL IMMEDIATE;

ROLLBACK;

-- Control despues del ROLLBACK: los precios y la auditoria vuelven al estado previo
SELECT count(*)      AS vinos_bodega,
       sum(v.precio) AS suma_precios,
       min(v.precio) AS precio_min,
       max(v.precio) AS precio_max
FROM vino AS v
JOIN bodega AS b ON b.cuit = v.cuit_bodega
WHERE b.razon_social = 'Bodega DEMO Atuel 001';

SELECT count(*) AS filas_auditoria_tras_rollback FROM auditoria_precio;


-- U4 | Responsable: Valentino | Origen: fase5/evidencias/valentino/U4.sql
-- U4. En las salas cuyo día de cierre es lunes, cambiarlo a miércoles
-- y viceversa, utilizando una sola sentencia UPDATE.

BEGIN;

-- Estado anterior.
SELECT dia_cierre, COUNT(*) AS cantidad_salas
FROM sala_venta
GROUP BY dia_cierre
ORDER BY dia_cierre;

-- Única sentencia de modificación para U4.
UPDATE sala_venta
SET dia_cierre = CASE
    WHEN dia_cierre = 'lunes' THEN 'miercoles'
    WHEN dia_cierre = 'miercoles' THEN 'lunes'
END
WHERE dia_cierre IN ('lunes', 'miercoles');

-- Estado posterior, dentro de la misma transacción.
SELECT dia_cierre, COUNT(*) AS cantidad_salas
FROM sala_venta
GROUP BY dia_cierre
ORDER BY dia_cierre;

-- Deshacer la prueba para conservar los datos originales.
ROLLBACK;

-- Comprobar que el estado original se restauró.
SELECT dia_cierre, COUNT(*) AS cantidad_salas
FROM sala_venta
GROUP BY dia_cierre
ORDER BY dia_cierre;


-- U5 | Responsable: Antonio | Origen: fase5/evidencias/antonio/U5.sql
-- U5 - Aplicar un 15 % de descuento de precio a los 10 vinos menos
--      vendidos de toda la red.

BEGIN;

-- Control previo 1: cuantos vinos no tienen ninguna venta
SELECT count(*) AS vinos_sin_ventas
FROM vino AS v
WHERE NOT EXISTS (SELECT 1 FROM renglon_comprobante AS rc WHERE rc.cod_vino = v.cod_vino);

-- Control previo 2: puestos 1 a 12 del ranking ascendente (para ver el
-- limite del puesto 10 y si hay empates entre el 10 y el 11)
WITH ventas AS (
    SELECT v.cod_vino, v.nombre, v.precio, COALESCE(SUM(rc.cantidad), 0) AS botellas
    FROM vino AS v
    LEFT JOIN renglon_comprobante AS rc ON rc.cod_vino = v.cod_vino
    GROUP BY v.cod_vino, v.nombre, v.precio
)
SELECT row_number() OVER (ORDER BY botellas ASC, cod_vino ASC) AS puesto,
       cod_vino, nombre, botellas, precio
FROM ventas
ORDER BY botellas ASC, cod_vino ASC
LIMIT 12;

-- Control previo 3: filas actuales en la auditoria de precios
SELECT count(*) AS filas_auditoria_antes FROM auditoria_precio;

-- Sentencia de la consigna (psql informa la cantidad de filas: UPDATE n)
WITH ventas AS (
    SELECT v.cod_vino, COALESCE(SUM(rc.cantidad), 0) AS botellas
    FROM vino AS v
    LEFT JOIN renglon_comprobante AS rc ON rc.cod_vino = v.cod_vino
    GROUP BY v.cod_vino
),
menos_vendidos AS (
    SELECT cod_vino FROM ventas
    ORDER BY botellas ASC, cod_vino ASC
    LIMIT 10
)
UPDATE vino AS v
SET    precio = ROUND(v.precio * 0.85, 2)
FROM   menos_vendidos AS m
WHERE  v.cod_vino = m.cod_vino;

-- Control posterior 1: los mismos 10 vinos con su precio nuevo
WITH ventas AS (
    SELECT v.cod_vino, v.nombre, v.precio, COALESCE(SUM(rc.cantidad), 0) AS botellas
    FROM vino AS v
    LEFT JOIN renglon_comprobante AS rc ON rc.cod_vino = v.cod_vino
    GROUP BY v.cod_vino, v.nombre, v.precio
)
SELECT row_number() OVER (ORDER BY botellas ASC, cod_vino ASC) AS puesto,
       cod_vino, nombre, botellas, precio AS precio_nuevo
FROM ventas
ORDER BY botellas ASC, cod_vino ASC
LIMIT 10;

-- Control posterior 2: el trigger RN-13 agrega una fila por vino modificado
SELECT count(*) AS filas_auditoria_despues FROM auditoria_precio;

-- Control posterior 3: auditorias generadas en esta transaccion y
-- verificacion de que todas reflejan exactamente -15 %
SELECT count(*) AS auditorias_de_esta_transaccion,
       count(*) FILTER (WHERE a.precio_nuevo <> ROUND(a.precio_anterior * 0.85, 2))
                AS auditorias_incorrectas
FROM auditoria_precio AS a
WHERE a.fecha_hora >= transaction_timestamp();

-- Verificar ahora los controles diferidos de vino (RN-05)
SET CONSTRAINTS ALL IMMEDIATE;

ROLLBACK;

-- Control despues del ROLLBACK: precios originales y auditoria sin cambios
WITH ventas AS (
    SELECT v.cod_vino, v.precio, COALESCE(SUM(rc.cantidad), 0) AS botellas
    FROM vino AS v
    LEFT JOIN renglon_comprobante AS rc ON rc.cod_vino = v.cod_vino
    GROUP BY v.cod_vino, v.precio
)
SELECT row_number() OVER (ORDER BY botellas ASC, cod_vino ASC) AS puesto,
       cod_vino, botellas, precio AS precio_tras_rollback
FROM ventas
ORDER BY botellas ASC, cod_vino ASC
LIMIT 10;

SELECT count(*) AS filas_auditoria_tras_rollback FROM auditoria_precio;


-- U6 | Responsable: Fabricio | Origen: fase5/evidencias/fabricio/U6.sql
-- U6 - Actualizacion de descuentos a exportadores

BEGIN;

-- Control anterior: cantidad de exportadores candidatos.
SELECT
    COUNT(*) AS candidatos_antes,
    COUNT(*) FILTER (
        WHERE c.descuento_especial = 35.00
    ) AS candidatos_ya_con_35
FROM public.cliente c
WHERE c.tipo_cliente = 'exportador'
  AND c.id_cliente IN (
      SELECT p.id_cliente
      FROM public.permiso_exportacion p
      GROUP BY p.id_cliente
      HAVING COUNT(*) > 3
  );

-- U6: actualizar el descuento al 35 %.
-- Se mantiene literalmente la condicion de mas de 3 permisos.
UPDATE public.cliente AS c
SET descuento_especial = 35.00
WHERE c.tipo_cliente = 'exportador'
  AND c.id_cliente IN (
      SELECT p.id_cliente
      FROM public.permiso_exportacion p
      GROUP BY p.id_cliente
      HAVING COUNT(*) > 3
  );

-- Control posterior: comprobar el descuento de los candidatos.
SELECT
    COUNT(*) AS candidatos_despues,
    COUNT(*) FILTER (
        WHERE c.descuento_especial = 35.00
    ) AS candidatos_con_35
FROM public.cliente c
WHERE c.tipo_cliente = 'exportador'
  AND c.id_cliente IN (
      SELECT p.id_cliente
      FROM public.permiso_exportacion p
      GROUP BY p.id_cliente
      HAVING COUNT(*) > 3
  );

-- Deshacer cualquier modificacion de la prueba.
ROLLBACK;
