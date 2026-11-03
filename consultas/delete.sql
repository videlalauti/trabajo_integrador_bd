-- D1 | Responsable: Fabricio | Origen: fase5/evidencias/fabricio/D1.sql
-- D1 - Eliminar comprobantes antiguos de socios

BEGIN;

-- Control anterior: fecha limite y comprobantes candidatos.
SELECT
    CURRENT_DATE AS fecha_actual,
    (CURRENT_DATE - INTERVAL '5 years')::date AS fecha_limite,
    COUNT(DISTINCT co.nro_comprobante) AS comprobantes_antes,
    COUNT(r.cod_vino) AS renglones_asociados_antes
FROM public.comprobante co
JOIN public.cliente c
    ON c.id_cliente = co.id_cliente
LEFT JOIN public.renglon_comprobante r
    ON r.nro_comprobante = co.nro_comprobante
WHERE c.tipo_cliente = 'socio'
  AND co.fecha < CURRENT_DATE - INTERVAL '5 years';

-- Si existen renglones, se aplica ON DELETE CASCADE.
DELETE FROM public.comprobante co
USING public.cliente c
WHERE co.id_cliente = c.id_cliente
  AND c.tipo_cliente = 'socio'
  AND co.fecha < CURRENT_DATE - INTERVAL '5 years';

-- Control posterior: verificar los registros restantes.
SELECT
    COUNT(DISTINCT co.nro_comprobante) AS comprobantes_despues,
    COUNT(r.cod_vino) AS renglones_asociados_despues
FROM public.comprobante co
JOIN public.cliente c
    ON c.id_cliente = co.id_cliente
LEFT JOIN public.renglon_comprobante r
    ON r.nro_comprobante = co.nro_comprobante
WHERE c.tipo_cliente = 'socio'
  AND co.fecha < CURRENT_DATE - INTERVAL '5 years';

-- Deshacer cualquier eliminacion de la prueba.
ROLLBACK;

-- Control final: comprobar el total de comprobantes.
SELECT COUNT(*) AS total_comprobantes_tras_rollback
FROM public.comprobante;



-- D2 | Responsable: Lautaro | Origen: fase5/evidencias/lautaro/d2_prueba_transaccional.sql
-- D2: Prueba transaccional.

BEGIN;

-- ANTES: total de cepas y candidatas a eliminar.
SELECT
    COUNT(*) AS cepas_totales,
    COUNT(*) FILTER (
        WHERE NOT EXISTS (
            SELECT 1 FROM vino_cepa vc
            WHERE vc.id_cepa = c.id_cepa
        )
        AND NOT EXISTS (
            SELECT 1 FROM parcela p
            WHERE p.id_cepa = c.id_cepa
        )
    ) AS cepas_candidatas
FROM cepa c;

-- MODIFICACION: eliminar cepas sin referencias.
DELETE FROM cepa c
WHERE NOT EXISTS (
    SELECT 1 FROM vino_cepa vc
    WHERE vc.id_cepa = c.id_cepa
)
AND NOT EXISTS (
    SELECT 1 FROM parcela p
    WHERE p.id_cepa = c.id_cepa
);

-- DESPUES: verificar nuevamente.
SELECT
    COUNT(*) AS cepas_totales,
    COUNT(*) FILTER (
        WHERE NOT EXISTS (
            SELECT 1 FROM vino_cepa vc
            WHERE vc.id_cepa = c.id_cepa
        )
        AND NOT EXISTS (
            SELECT 1 FROM parcela p
            WHERE p.id_cepa = c.id_cepa
        )
    ) AS cepas_candidatas
FROM cepa c;

ROLLBACK;


-- D3 | Responsable: Antonio | Origen: fase5/evidencias/antonio/D3.sql
-- D3 - La sala de una localidad determinada fue dada de baja: eliminar
--      los empleados de esa sala que trabajaron menos de dos anios.

BEGIN;

-- Control previo 1: empleados de la sala con su antiguedad
SELECT e.cuit, e.nombre, e.fecha_ingreso,
       fn_antiguedad_anios(e.fecha_ingreso) AS antiguedad_anios,
       s.id_sala, l.nombre AS localidad
FROM empleado AS e
JOIN sala_venta AS s ON s.id_sala = e.id_sala
JOIN localidad  AS l ON l.id_localidad = s.id_localidad
WHERE l.nombre = 'San Rafael' AND s.id_sala = 1
ORDER BY e.fecha_ingreso;

-- Control previo 2: total de empleados de la empresa
SELECT count(*) AS empleados_total FROM empleado;

-- Sentencia de la consigna (psql informa la cantidad: DELETE n)
DELETE FROM empleado AS e
USING sala_venta AS s, localidad AS l
WHERE e.id_sala = s.id_sala
  AND s.id_localidad = l.id_localidad
  AND l.nombre = 'San Rafael'
  AND s.id_sala = 1
  AND fn_antiguedad_anios(e.fecha_ingreso) < 2
RETURNING e.cuit, e.nombre, e.fecha_ingreso;

-- Control posterior 1: solo quedan en la sala los de 2 anios o mas
SELECT e.cuit, e.nombre, e.fecha_ingreso,
       fn_antiguedad_anios(e.fecha_ingreso) AS antiguedad_anios
FROM empleado AS e
JOIN sala_venta AS s ON s.id_sala = e.id_sala
JOIN localidad  AS l ON l.id_localidad = s.id_localidad
WHERE l.nombre = 'San Rafael' AND s.id_sala = 1
ORDER BY e.fecha_ingreso;

-- Control posterior 2: total de empleados (debe bajar en la cantidad borrada)
SELECT count(*) AS empleados_total FROM empleado;

-- Control posterior 3: la sala sigue existiendo (la consigna no la elimina)
SELECT id_sala, calle, numero, id_localidad FROM sala_venta WHERE id_sala = 1;

ROLLBACK;

-- Control despues del ROLLBACK: la sala recupera sus empleados
SELECT e.cuit, e.nombre, e.fecha_ingreso,
       fn_antiguedad_anios(e.fecha_ingreso) AS antiguedad_anios
FROM empleado AS e
WHERE e.id_sala = 1
ORDER BY e.fecha_ingreso;

SELECT count(*) AS empleados_total FROM empleado;



-- D4 | Responsable: Fabricio | Origen: fase5/evidencias/fabricio/D4.sql
-- D4 - Eliminar socios antiguos que nunca compraron

BEGIN;

-- Control anterior: cantidad de socios sin compras
-- y cantidad de candidatos que cumplen D4.
SELECT
    COUNT(*) FILTER (
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.comprobante co
            WHERE co.id_cliente = c.id_cliente
        )
    ) AS socios_sin_compras_antes,

    COUNT(*) FILTER (
        WHERE c.fecha_alta < CURRENT_DATE - INTERVAL '5 years'
          AND NOT EXISTS (
              SELECT 1
              FROM public.comprobante co
              WHERE co.id_cliente = c.id_cliente
          )
    ) AS candidatos_antes
FROM public.cliente c
WHERE c.tipo_cliente = 'socio';

-- D4: eliminar exclusivamente los socios antiguos
-- que nunca registraron un comprobante.
DELETE FROM public.cliente AS c
WHERE c.tipo_cliente = 'socio'
  AND c.fecha_alta < CURRENT_DATE - INTERVAL '5 years'
  AND NOT EXISTS (
      SELECT 1
      FROM public.comprobante co
      WHERE co.id_cliente = c.id_cliente
  );

-- Control posterior: verificar cuantos candidatos
-- siguen cumpliendo la condicion.
SELECT
    COUNT(*) AS candidatos_despues
FROM public.cliente c
WHERE c.tipo_cliente = 'socio'
  AND c.fecha_alta < CURRENT_DATE - INTERVAL '5 years'
  AND NOT EXISTS (
      SELECT 1
      FROM public.comprobante co
      WHERE co.id_cliente = c.id_cliente
  );

-- Deshacer cualquier modificacion de la prueba.
ROLLBACK;

-- Control final: verificar el total de socios.
SELECT
    COUNT(*) AS total_socios_tras_rollback
FROM public.cliente
WHERE tipo_cliente = 'socio';



-- D5 | Responsable: Jose | Origen: fase5/evidencias/jose/D5.sql
-- Eliminar ingresos procesados con mas de 365 dias.


BEGIN;

-- Control anterior.
SELECT
    (SELECT COUNT(*) FROM public.ingreso)
        AS ingresos_totales,
    (SELECT COUNT(*) FROM public.ingreso
     WHERE estado = 'procesado'
       AND fecha < CURRENT_DATE - 365)
        AS ingresos_elegibles,
    (SELECT COUNT(*) FROM public.renglon_ingreso)
        AS renglones_totales,
    (SELECT COUNT(*)
     FROM public.renglon_ingreso ri
     JOIN public.ingreso i
       ON i.cod_ingreso = ri.cod_ingreso
     WHERE i.estado = 'procesado'
       AND i.fecha < CURRENT_DATE - 365)
        AS renglones_asociados;

-- DELETE solicitado.
DELETE FROM public.ingreso
WHERE estado = 'procesado'
  AND fecha < CURRENT_DATE - 365;

-- Control posterior.
SELECT
    (SELECT COUNT(*) FROM public.ingreso)
        AS ingresos_totales,
    (SELECT COUNT(*) FROM public.ingreso
     WHERE estado = 'procesado'
       AND fecha < CURRENT_DATE - 365)
        AS ingresos_elegibles,
    (SELECT COUNT(*) FROM public.renglon_ingreso)
        AS renglones_totales;

-- Restaurar los datos originales.
ROLLBACK;


-- D6 | Responsable: Valentino | Origen: fase5/evidencias/valentino/D6.sql
-- D6. Eliminar clientes socios sin compras que viven en una localidad especifica.

BEGIN;

-- Control anterior: candidatos a eliminar.
SELECT c.id_cliente, c.nombre_razon_social
FROM cliente AS c
WHERE c.tipo_cliente = 'socio'
  AND c.id_localidad = 4
  AND NOT EXISTS (
      SELECT 1
      FROM comprobante AS co
      WHERE co.id_cliente = c.id_cliente
  );

-- Unica sentencia de eliminacion de la consigna.
DELETE FROM cliente
WHERE tipo_cliente = 'socio'
  AND id_localidad = 4
  AND NOT EXISTS (
      SELECT 1
      FROM comprobante
      WHERE comprobante.id_cliente = cliente.id_cliente
  );

-- Control posterior: el candidato identificado debe haber desaparecido.
SELECT id_cliente, nombre_razon_social
FROM cliente
WHERE id_cliente = 15637;

ROLLBACK;

-- Verificacion final: el registro vuelve a existir.
SELECT id_cliente, nombre_razon_social
FROM cliente
WHERE id_cliente = 15637;
