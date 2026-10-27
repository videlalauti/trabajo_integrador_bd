BEGIN;

-- ============================================================================
-- 004_procedimientos.sql
-- TPI Bodegas del Atuel - Etapa 2
--
-- Procedimientos transaccionales para procesar ingresos y transferencias.
--
-- CONTRATO CON 005_triggers.sql (importante para Padre):
--   1. Estos procedimientos son los UNICOS que mueven stock por ingresos y
--      transferencias. Los triggers de 005 NO deben sumar ni restar stock al
--      cambiar el estado de ingreso/transferencia, para evitar doble impacto.
--   2. 005 debe validar las transiciones de estado (en_confeccion -> terminado
--      -> procesado) y permitir exactamente el UPDATE terminado -> procesado
--      que hacen estos procedimientos. No debe haber retrocesos ni saltos.
--   3. El trigger de estado debe ser inmediato (BEFORE UPDATE), no diferido,
--      para que un rechazo revierta el stock dentro del mismo CALL.
--   4. 005 debe bloquear la edicion directa de renglones cuando la cabecera ya
--      no esta en_confeccion (RN-12). Para sincronizar con estos procedimientos,
--      el trigger de renglon debe tomar el mismo bloqueo de cabecera
--      (SELECT ... FOR UPDATE sobre ingreso/transferencia) antes de validar el
--      estado. Asi, si 004 esta procesando (tiene la cabecera bloqueada), el
--      trigger espera; al continuar ve 'procesado' y rechaza el cambio.
--      Estos procedimientos no modifican renglones, por lo que no hay ciclo
--      de bloqueo: 004 toma cabecera y stock, nunca renglones.
--      El borrado en cascada de un ingreso procesado (decision D5) debe seguir
--      funcionando; 005 debe distinguir ese caso del borrado/edicion directa.
--   5. 005 no debe bloquear el UPDATE de estado de estos procedimientos ni el
--      UPDATE de fecha_confeccion que no cambia la fecha (estos procedimientos
--      no tocan fecha_confeccion).
--   6. El trigger de ventas de 005 tambien debe bloquear stock_sala en orden
--      ascendente de cod_vino, para compartir el orden global de bloqueo.
--
-- LIMITACION CONOCIDA (a resolver con 005 y 007, sin implementar GUC en 004):
--   Un UPDATE directo del tipo
--       UPDATE ingreso SET estado = 'procesado' WHERE cod_ingreso = ...;
--   (o el equivalente sobre transferencia) ejecutado por un usuario con
--   privilegios de UPDATE sobre la cabecera podria saltar el movimiento de
--   stock si el trigger de 005 solo valida el grafo de estados. Alternativas:
--     a) Trigger de estado que exija una marca transaccional puesta por 004
--        (por ejemplo, un GUC local con set_config). Requiere acuerdo previo
--        con el responsable de 005; NO se implementa en esta version.
--     b) En 007, no otorgar UPDATE sobre la columna estado a los roles de API;
--        exponer unicamente CALL sp_procesar_ingreso / sp_procesar_transferencia.
--     c) Un trigger que intente verificar el movimiento de stock (complejo y
--        fragil; no recomendado).
--   Version actual: contrato base. 004 mueve stock y estado; 005 valida las
--   transiciones; 007 restringe los privilegios de escritura directa.
--
-- ORDEN GLOBAL DE BLOQUEO (ambos procedimientos):
--   cabecera (ingreso/transferencia) -> stock_deposito (cod_vino ASC)
--   -> stock_sala (cod_vino ASC)
--
-- Los procedimientos NO hacen COMMIT ni ROLLBACK. La atomicidad queda a cargo
-- de la transaccion que invoca el CALL y de las excepciones de PostgreSQL.
-- ============================================================================


-- ============================================================================
-- sp_procesar_ingreso
--
-- Proposito:
--   Procesar un ingreso en estado 'terminado': sumar las cantidades de sus
--   renglones a stock_deposito y cambiar el estado a 'procesado'.
--
-- Parametro:
--   p_cod_ingreso: codigo del ingreso (ingreso.cod_ingreso).
--
-- Precondiciones:
--   - El ingreso debe existir.
--   - Debe estar en estado 'terminado' (no en_confeccion ni procesado).
--   - Debe tener al menos un renglon en renglon_ingreso.
--
-- Reglas de negocio:
--   RN-10: solo ingresos terminados impactan stock y pasan a procesado;
--          la secuencia no puede retroceder ni repetirse.
--
-- Errores esperados:
--   - RN-10: ingreso inexistente, nulo, en confeccion, ya procesado o sin
--            renglones.
--   - RN-10: no se pudo confirmar el estado procesado (control defensivo).
--
-- Concurrencia:
--   - Bloquea la cabecera con SELECT ... FOR UPDATE. Dos CALL simultaneos del
--     mismo ingreso se serializan; el segundo ve 'procesado' y falla.
--   - Bloquea las filas existentes de stock_deposito en orden ascendente de
--     cod_vino antes del upsert.
--   - Usa INSERT ... ON CONFLICT DO UPDATE para las filas faltantes de
--     stock_deposito, evitando que un UPDATE afecte 0 filas en silencio.
-- ============================================================================
CREATE OR REPLACE PROCEDURE sp_procesar_ingreso(
    IN p_cod_ingreso INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_estado              estado_documento;
    v_cantidad_renglones  BIGINT;
    v_filas               BIGINT;
    v_cod_vino            INTEGER;
BEGIN
    -- Validacion basica del parametro.
    IF p_cod_ingreso IS NULL THEN
        RAISE EXCEPTION 'RN-10: el codigo de ingreso no puede ser nulo'
            USING ERRCODE = 'P0001';
    END IF;

    -- Bloqueo de la cabecera. El FOR UPDATE impide que dos sesiones procesen
    -- el mismo ingreso al mismo tiempo.
    SELECT estado
      INTO v_estado
      FROM ingreso
     WHERE cod_ingreso = p_cod_ingreso
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'RN-10: el ingreso % no existe', p_cod_ingreso
            USING ERRCODE = 'P0001';
    END IF;

    -- Solo un ingreso terminado puede procesarse.
    IF v_estado <> 'terminado' THEN
        IF v_estado = 'procesado' THEN
            RAISE EXCEPTION 'RN-10: el ingreso % ya fue procesado', p_cod_ingreso
                USING ERRCODE = 'P0001';
        ELSIF v_estado = 'en_confeccion' THEN
            RAISE EXCEPTION 'RN-10: el ingreso % esta en confeccion; solo se procesan ingresos terminados', p_cod_ingreso
                USING ERRCODE = 'P0001';
        ELSE
            RAISE EXCEPTION 'RN-10: estado no valido (%) para el ingreso %', v_estado, p_cod_ingreso
                USING ERRCODE = 'P0001';
        END IF;
    END IF;

    -- Un documento sin renglones no representa un movimiento de mercaderia.
    SELECT COUNT(*)
      INTO v_cantidad_renglones
      FROM renglon_ingreso
     WHERE cod_ingreso = p_cod_ingreso;

    IF v_cantidad_renglones = 0 THEN
        RAISE EXCEPTION 'RN-10: el ingreso % no tiene renglones', p_cod_ingreso
            USING ERRCODE = 'P0001';
    END IF;

    -- Bloqueo preventivo de las filas de stock ya existentes, en orden
    -- ascendente de cod_vino. Las filas inexistentes se resuelven con el
    -- upsert posterior.
    FOR v_cod_vino IN
        SELECT cod_vino
          FROM renglon_ingreso
         WHERE cod_ingreso = p_cod_ingreso
         ORDER BY cod_vino
    LOOP
        PERFORM 1
           FROM stock_deposito
          WHERE cod_vino = v_cod_vino
            FOR UPDATE;
    END LOOP;

    -- Alta o incremento atomico en el deposito central. ON CONFLICT cubre el
    -- caso de un vino que todavia no tiene fila en stock_deposito.
    INSERT INTO stock_deposito (cod_vino, cantidad)
    SELECT cod_vino, cantidad
      FROM renglon_ingreso
     WHERE cod_ingreso = p_cod_ingreso
     ORDER BY cod_vino
    ON CONFLICT (cod_vino) DO UPDATE
    SET cantidad = stock_deposito.cantidad + EXCLUDED.cantidad;

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas <> v_cantidad_renglones THEN
        RAISE EXCEPTION 'RN-10: no se pudieron sumar todos los renglones del ingreso % (esperados %, afectados %)',
            p_cod_ingreso, v_cantidad_renglones, v_filas
            USING ERRCODE = 'P0001';
    END IF;

    -- El cambio de estado es el ultimo paso. La guarda AND estado = 'terminado'
    -- es una defensa adicional contra un cambio concurrente.
    UPDATE ingreso
       SET estado = 'procesado'
     WHERE cod_ingreso = p_cod_ingreso
       AND estado = 'terminado';

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas <> 1 THEN
        RAISE EXCEPTION 'RN-10: no se pudo confirmar el estado procesado del ingreso %', p_cod_ingreso
            USING ERRCODE = 'P0001';
    END IF;

    RAISE NOTICE 'RN-10: ingreso % procesado correctamente', p_cod_ingreso;
END;
$$;


-- ============================================================================
-- sp_procesar_transferencia
--
-- Proposito:
--   Procesar una transferencia en estado 'terminado': verificar stock en el
--   deposito para cada vino, restar del deposito, sumar a la sala destino y
--   cambiar el estado a 'procesado'.
--
-- Parametro:
--   p_nro_solicitud: numero de solicitud (transferencia.nro_solicitud).
--
-- Precondiciones:
--   - La transferencia debe existir.
--   - Debe estar en estado 'terminado' (no en_confeccion ni procesado).
--   - Debe tener al menos un renglon en renglon_transferencia.
--   - Debe existir una fila en stock_deposito para cada vino, con cantidad
--     suficiente. La ausencia de fila NO se interpreta como cantidad 0: se
--     informa como error RN-11.
--
-- Reglas de negocio:
--   RN-11: solo transferencias terminadas impactan stock y pasan a procesado;
--          la secuencia no puede retroceder ni repetirse.
--
-- Errores esperados:
--   - RN-11: transferencia inexistente, nula, en confeccion, ya procesada o
--            sin renglones.
--   - RN-11: falta de fila en stock_deposito para un vino.
--   - RN-11: stock insuficiente para un vino (incluye el caso de cantidad 0).
--   - RN-11: no se pudieron descontar/acreditar todas las cantidades.
--
-- Concurrencia:
--   - Bloquea la cabecera con SELECT ... FOR UPDATE.
--   - Bloquea y verifica TODOS los vinos del deposito en orden ascendente de
--     cod_vino antes de modificar cualquier stock. Si un vino no alcanza, no
--     se hizo ningun cambio.
--   - Bloquea las filas existentes de stock_sala de la sala destino tambien
--     en orden ascendente de cod_vino; las filas faltantes se crean con
--     INSERT ... ON CONFLICT DO UPDATE.
--   - Dos transferencias del mismo vino se serializan en stock_deposito.
--     Si el stock total no alcanza, la segunda falla sin dejar cambios
--     parciales.
-- ============================================================================
CREATE OR REPLACE PROCEDURE sp_procesar_transferencia(
    IN p_nro_solicitud INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_estado              estado_documento;
    v_id_sala             INTEGER;
    v_cantidad_renglones  BIGINT;
    v_disponible          INTEGER;
    v_filas               BIGINT;
    r                     RECORD;
BEGIN
    -- Validacion basica del parametro.
    IF p_nro_solicitud IS NULL THEN
        RAISE EXCEPTION 'RN-11: el numero de solicitud no puede ser nulo'
            USING ERRCODE = 'P0001';
    END IF;

    -- Bloqueo de la cabecera y lectura de la sala destino.
    SELECT estado, id_sala
      INTO v_estado, v_id_sala
      FROM transferencia
     WHERE nro_solicitud = p_nro_solicitud
       FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'RN-11: la transferencia % no existe', p_nro_solicitud
            USING ERRCODE = 'P0001';
    END IF;

    -- Solo una transferencia terminada puede procesarse.
    IF v_estado <> 'terminado' THEN
        IF v_estado = 'procesado' THEN
            RAISE EXCEPTION 'RN-11: la transferencia % ya fue procesada', p_nro_solicitud
                USING ERRCODE = 'P0001';
        ELSIF v_estado = 'en_confeccion' THEN
            RAISE EXCEPTION 'RN-11: la transferencia % esta en confeccion; solo se procesan transferencias terminadas', p_nro_solicitud
                USING ERRCODE = 'P0001';
        ELSE
            RAISE EXCEPTION 'RN-11: estado no valido (%) para la transferencia %', v_estado, p_nro_solicitud
                USING ERRCODE = 'P0001';
        END IF;
    END IF;

    -- Un documento sin renglones no representa un movimiento de mercaderia.
    SELECT COUNT(*)
      INTO v_cantidad_renglones
      FROM renglon_transferencia
     WHERE nro_solicitud = p_nro_solicitud;

    IF v_cantidad_renglones = 0 THEN
        RAISE EXCEPTION 'RN-11: la transferencia % no tiene renglones', p_nro_solicitud
            USING ERRCODE = 'P0001';
    END IF;

    -- Primera fase: bloquear y verificar TODOS los vinos en el deposito,
    -- en orden ascendente de cod_vino. No se modifica nada en esta fase.
    -- La fila inexistente es un error distinto de cantidad insuficiente.
    FOR r IN
        SELECT cod_vino, cantidad
          FROM renglon_transferencia
         WHERE nro_solicitud = p_nro_solicitud
         ORDER BY cod_vino
    LOOP
        SELECT cantidad
          INTO v_disponible
          FROM stock_deposito
         WHERE cod_vino = r.cod_vino
           FOR UPDATE;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'RN-11: no existe fila en stock_deposito para el vino % (transferencia %)',
                r.cod_vino, p_nro_solicitud
                USING ERRCODE = 'P0001';
        END IF;

        IF v_disponible < r.cantidad THEN
            RAISE EXCEPTION 'RN-11: stock insuficiente para el vino % en la transferencia % (disponible %, solicitado %)',
                r.cod_vino, p_nro_solicitud, v_disponible, r.cantidad
                USING ERRCODE = 'P0001';
        END IF;
    END LOOP;

    -- Segunda fase: bloquear las filas existentes de stock_sala de la sala
    -- destino, en orden ascendente de cod_vino. Las filas faltantes se crean
    -- luego con ON CONFLICT.
    FOR r IN
        SELECT cod_vino
          FROM renglon_transferencia
         WHERE nro_solicitud = p_nro_solicitud
         ORDER BY cod_vino
    LOOP
        PERFORM 1
           FROM stock_sala
          WHERE id_sala = v_id_sala
            AND cod_vino = r.cod_vino
            FOR UPDATE;
    END LOOP;

    -- Tercera fase: recien ahora se modifica el stock. El descuento incluye
    -- una guarda defensiva de cantidad; si algo no coincide, se revierte todo
    -- por la transaccion.
    UPDATE stock_deposito sd
       SET cantidad = sd.cantidad - rt.cantidad
      FROM renglon_transferencia rt
     WHERE rt.nro_solicitud = p_nro_solicitud
       AND sd.cod_vino = rt.cod_vino
       AND sd.cantidad >= rt.cantidad;

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas <> v_cantidad_renglones THEN
        RAISE EXCEPTION 'RN-11: no se pudieron descontar todos los renglones de la transferencia % (esperados %, afectados %)',
            p_nro_solicitud, v_cantidad_renglones, v_filas
            USING ERRCODE = 'P0001';
    END IF;

    -- Alta o incremento atomico en la sala destino. ON CONFLICT cubre el caso
    -- de una sala que todavia no tiene stock de ese vino.
    INSERT INTO stock_sala (id_sala, cod_vino, cantidad)
    SELECT v_id_sala, cod_vino, cantidad
      FROM renglon_transferencia
     WHERE nro_solicitud = p_nro_solicitud
     ORDER BY cod_vino
    ON CONFLICT (id_sala, cod_vino) DO UPDATE
    SET cantidad = stock_sala.cantidad + EXCLUDED.cantidad;

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas <> v_cantidad_renglones THEN
        RAISE EXCEPTION 'RN-11: no se pudieron acreditar todos los renglones de la transferencia % en la sala % (esperados %, afectados %)',
            p_nro_solicitud, v_id_sala, v_cantidad_renglones, v_filas
            USING ERRCODE = 'P0001';
    END IF;

    -- El cambio de estado es el ultimo paso. La guarda AND estado = 'terminado'
    -- es una defensa adicional contra un cambio concurrente.
    UPDATE transferencia
       SET estado = 'procesado'
     WHERE nro_solicitud = p_nro_solicitud
       AND estado = 'terminado';

    GET DIAGNOSTICS v_filas = ROW_COUNT;
    IF v_filas <> 1 THEN
        RAISE EXCEPTION 'RN-11: no se pudo confirmar el estado procesado de la transferencia %', p_nro_solicitud
            USING ERRCODE = 'P0001';
    END IF;

    RAISE NOTICE 'RN-11: transferencia % procesada correctamente', p_nro_solicitud;
END;
$$;

COMMIT;
