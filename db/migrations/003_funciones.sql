BEGIN;
-- Función 1: fn_stock_sala
-- Propósito: Devuelve la cantidad de botellas disponibles de un vino en una sala específica.
-- Parámetros: p_sala (INTEGER), p_vino (INTEGER).
-- Tipo: STABLE (lee datos que pueden cambiar, no modifica el estado).
CREATE OR REPLACE FUNCTION fn_stock_sala(p_sala INTEGER, p_vino INTEGER)
RETURNS INTEGER
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(
        (SELECT cantidad FROM stock_sala WHERE id_sala = p_sala AND cod_vino = p_vino), 0
    );
$$;

-- Función 2: fn_descuento_cliente
-- Propósito: Obtiene el porcentaje de descuento del cliente (RN-06). Prioriza el descuento especial si existe.
-- Parámetros: p_id_cliente (INTEGER).
-- Tipo: STABLE.
CREATE OR REPLACE FUNCTION fn_descuento_cliente(p_id_cliente INTEGER)
RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(c.descuento_especial, tc.descuento)
    FROM cliente c
    JOIN tipo_cliente tc ON c.tipo_cliente = tc.tipo_cliente
    WHERE c.id_cliente = p_id_cliente;
$$;

-- Función 3: fn_total_comprobante
-- Propósito: Calcula los importes acumulados de la cabecera a partir de sus renglones (RN-08).
-- Parámetros: p_nro_comprobante (INTEGER).
-- Tipo: VOLATILE (se invoca desde triggers AFTER que deben ver los renglones
--       recién insertados/modificados/eliminados).
--

CREATE OR REPLACE FUNCTION fn_total_comprobante(
    p_nro_comprobante INTEGER,
    OUT o_subtotal NUMERIC,
    OUT o_descuento NUMERIC,
    OUT o_total NUMERIC
)
LANGUAGE sql VOLATILE AS $$
    SELECT
        COALESCE(SUM(r.importe_bruto), 0)                  AS o_subtotal,
        COALESCE(SUM(r.importe_bruto - r.importe_neto), 0) AS o_descuento,
        COALESCE(SUM(r.importe_neto), 0)                   AS o_total
    FROM (
        SELECT
            ROUND(cantidad * precio_unitario, 2)                           AS importe_bruto,
            ROUND(cantidad * precio_unitario * (1 - descuento / 100.0), 2) AS importe_neto
        FROM renglon_comprobante
        WHERE nro_comprobante = p_nro_comprobante
    ) AS r;
$$;

-- Función 4: fn_antiguedad_anios
-- Propósito: Calcula los años completos transcurridos desde una fecha de inicio (ej. ingreso laboral o alta de cliente).
-- Parámetros: p_fecha_inicio (DATE).
-- Tipo: STABLE (depende de CURRENT_DATE).
CREATE OR REPLACE FUNCTION fn_antiguedad_anios(p_fecha_inicio DATE)
RETURNS INTEGER
LANGUAGE sql STABLE AS $$
    SELECT EXTRACT(YEAR FROM age(CURRENT_DATE, p_fecha_inicio))::INTEGER;
$$;

COMMIT;