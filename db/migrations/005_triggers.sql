BEGIN;
--1) RN-05: COMPOSICION DE VINOS (AL MENOS UNA CEPA, SUMA EXACTAMENTE 100)
CREATE OR REPLACE FUNCTION fn_trg_vino_composicion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_cod_vino INTEGER;
    v_cuenta   BIGINT;
    v_suma     NUMERIC;
    v_existe   BOOLEAN;
BEGIN
    IF TG_TABLE_NAME = 'vino' THEN
        IF TG_OP = 'INSERT' THEN
            v_cod_vino := NEW.cod_vino;
        ELSIF TG_OP = 'UPDATE' THEN
            v_cod_vino := NEW.cod_vino;
        ELSIF TG_OP = 'DELETE' THEN
            v_cod_vino := OLD.cod_vino;
        ELSE
            RETURN NULL;
        END IF;
    ELSIF TG_TABLE_NAME = 'vino_cepa' THEN
        IF TG_OP = 'INSERT' THEN
            v_cod_vino := NEW.cod_vino;
        ELSIF TG_OP = 'UPDATE' THEN
            IF OLD.cod_vino IS NOT NULL THEN
                SELECT EXISTS(SELECT 1 FROM vino WHERE cod_vino = OLD.cod_vino) INTO v_existe;
                IF v_existe THEN
                    SELECT COUNT(*), COALESCE(SUM(porcentaje), 0)
                      INTO v_cuenta, v_suma
                      FROM vino_cepa
                     WHERE cod_vino = OLD.cod_vino;
                    IF v_cuenta < 1 OR ABS(v_suma - 100) > 0.01 THEN
                        RAISE EXCEPTION 'RN-05: el vino % debe tener al menos una cepa y la suma de porcentajes debe ser 100 (actual: % filas, suma %)', 
                            OLD.cod_vino, v_cuenta, v_suma;
                    END IF;
                END IF;
            END IF;
            v_cod_vino := NEW.cod_vino;
        ELSIF TG_OP = 'DELETE' THEN
            v_cod_vino := OLD.cod_vino;
        ELSE
            RETURN NULL;
        END IF;
    ELSE
        RETURN NULL;
    END IF;

    IF v_cod_vino IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT EXISTS(SELECT 1 FROM vino WHERE cod_vino = v_cod_vino) INTO v_existe;
    IF NOT v_existe THEN
        RETURN NULL;
    END IF;

    SELECT COUNT(*), COALESCE(SUM(porcentaje), 0)
      INTO v_cuenta, v_suma
      FROM vino_cepa
     WHERE cod_vino = v_cod_vino;

    IF v_cuenta < 1 OR ABS(v_suma - 100) > 0.01 THEN
        RAISE EXCEPTION 'RN-05: el vino % debe tener al menos una cepa y la suma de porcentajes debe ser 100 (actual: % filas, suma %)', 
            v_cod_vino, v_cuenta, v_suma;
    END IF;

    RETURN NULL;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_vino_composicion_obligatoria
    AFTER INSERT ON vino
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_vino_composicion();

CREATE CONSTRAINT TRIGGER trg_vino_cepa_sum100
    AFTER INSERT OR UPDATE OR DELETE ON vino_cepa
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_vino_composicion();

-- 2) AUDITORIA DE PRECIO DE VINO (RN-13)
CREATE OR REPLACE FUNCTION fn_trg_auditoria_precio_vino()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.precio IS DISTINCT FROM OLD.precio THEN
        INSERT INTO auditoria_precio (cod_vino, precio_anterior, precio_nuevo, fecha_hora, usuario)
        VALUES (OLD.cod_vino, OLD.precio, NEW.precio, CURRENT_TIMESTAMP, current_user);
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditoria_precio_vino
    AFTER UPDATE ON vino
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_auditoria_precio_vino();

-- 3) TRANSFERENCIAS: FECHA DE CONFECCION (RN-11)
CREATE OR REPLACE FUNCTION fn_trg_transferencia_fecha()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.fecha_confeccion := CURRENT_DATE;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.fecha_confeccion IS DISTINCT FROM OLD.fecha_confeccion THEN
            RAISE EXCEPTION 'RN-11: no se puede modificar la fecha de confeccion de la transferencia';
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_transferencia_fecha
    BEFORE INSERT OR UPDATE ON transferencia
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_transferencia_fecha();

-- 4) CONTROL DE ESTADOS INGRESO/TRANSFERENCIA (RN-10, RN-11)
CREATE OR REPLACE FUNCTION fn_trg_control_estado_documento()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.estado = 'en_confeccion' AND NEW.estado = 'terminado' THEN
            RETURN NEW;
        ELSIF OLD.estado = 'terminado' AND NEW.estado = 'procesado' THEN
            RETURN NEW;
        ELSIF OLD.estado = NEW.estado THEN
            RETURN NEW;
        ELSE
            RAISE EXCEPTION 'RN-10/RN-11: transicion de estado no permitida (% -> %)', OLD.estado, NEW.estado;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_control_estado_ingreso
    BEFORE UPDATE ON ingreso
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_control_estado_documento();

CREATE TRIGGER trg_control_estado_transferencia
    BEFORE UPDATE ON transferencia
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_control_estado_documento();

-- 5) BLOQUEO DE RENGLONES SEGUN ESTADO (RN-12) - INGRESO Y TRANSFERENCIA
--    Permite eliminaciones en cascada requeridas por D5: si cabecera NO
--    existe, es cascade -> permitir. Si cabecera EXISTE y no esta en
--    confeccion -> bloquear.

CREATE OR REPLACE FUNCTION fn_trg_renglon_ingreso_estado()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_estado estado_documento;
    v_existe BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM ingreso WHERE cod_ingreso = OLD.cod_ingreso) INTO v_existe;
    IF NOT v_existe THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;
    
    SELECT estado INTO v_estado
      FROM ingreso
     WHERE cod_ingreso = COALESCE(NEW.cod_ingreso, OLD.cod_ingreso)
       FOR UPDATE;
    
    IF v_estado <> 'en_confeccion' THEN
        RAISE EXCEPTION 'RN-12: no se pueden agregar, modificar ni quitar renglones de un ingreso que no esta en confeccion';
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER trg_renglon_ingreso_estado
    BEFORE INSERT OR UPDATE OR DELETE ON renglon_ingreso
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_renglon_ingreso_estado();

CREATE OR REPLACE FUNCTION fn_trg_renglon_transferencia_estado()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_estado estado_documento;
    v_existe BOOLEAN;
BEGIN
    SELECT EXISTS(SELECT 1 FROM transferencia WHERE nro_solicitud = OLD.nro_solicitud) INTO v_existe;
    IF NOT v_existe THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;

    SELECT estado INTO v_estado
      FROM transferencia
     WHERE nro_solicitud = COALESCE(NEW.nro_solicitud, OLD.nro_solicitud)
       FOR UPDATE;
    
    IF v_estado <> 'en_confeccion' THEN
        RAISE EXCEPTION 'RN-12: no se pueden agregar, modificar ni quitar renglones de una transferencia que no esta en confeccion';
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER trg_renglon_transferencia_estado
    BEFORE INSERT OR UPDATE OR DELETE ON renglon_transferencia
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_renglon_transferencia_estado();


-- 6) VENTAS: COMPROBANTE Y RENGLONES
--    - Descuento ya viene en renglon (corresponde al cliente). No aplicar
--      nuevamente en cabecera.
--    - Subtotal de renglon sigue misma formula que fn_total_comprobante.
--    - INSERT: validar/descontar stock_sala, calcular subtotal renglon.
--    - UPDATE: ajustar stock por delta, recalcular.
--    - DELETE directo de renglon: devolver stock. DELETE de comprobante
--      completo (D1): no devolver stock (cabecera no existe en cascade).
--    - Cabecera: recalcular totales con fn_total_comprobante (VOLATILE),
--      bloquear cambio de id_cliente/id_sala si hay renglones.
CREATE OR REPLACE FUNCTION fn_trg_comprobante_totales()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_subtotal NUMERIC;
    v_descuento NUMERIC;
    v_total NUMERIC;
    v_cantidad_renglones BIGINT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.subtotal := 0;
        NEW.descuento := 0;
        NEW.total := 0;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.id_cliente IS DISTINCT FROM OLD.id_cliente OR 
           NEW.id_sala IS DISTINCT FROM OLD.id_sala THEN
            SELECT COUNT(*) INTO v_cantidad_renglones
              FROM renglon_comprobante
             WHERE nro_comprobante = OLD.nro_comprobante;
            IF v_cantidad_renglones > 0 THEN
                RAISE EXCEPTION 'No se puede modificar cliente o sala de un comprobante con renglones';
            END IF;
        END IF;
        
        SELECT o_subtotal, o_descuento, o_total
          INTO v_subtotal, v_descuento, v_total
          FROM fn_total_comprobante(OLD.nro_comprobante);
        
        NEW.subtotal := v_subtotal;
        NEW.descuento := v_descuento;
        NEW.total := v_total;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_comprobante_totales
    BEFORE INSERT OR UPDATE OR DELETE ON comprobante
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_comprobante_totales();

CREATE OR REPLACE FUNCTION fn_trg_renglon_comprobante()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_sala INTEGER;
    v_stock_actual INTEGER;
    v_descuento_cliente NUMERIC;
    v_cabecera_existe BOOLEAN;
BEGIN
    IF TG_OP = 'INSERT' THEN
        SELECT id_sala INTO v_id_sala
          FROM comprobante
         WHERE nro_comprobante = NEW.nro_comprobante;
        
        IF NOT FOUND THEN
            RAISE EXCEPTION 'El comprobante % no existe', NEW.nro_comprobante;
        END IF;
        
        SELECT fn_descuento_cliente(c.id_cliente) INTO v_descuento_cliente
          FROM comprobante c
         WHERE c.nro_comprobante = NEW.nro_comprobante;
        

        IF NEW.descuento IS DISTINCT FROM v_descuento_cliente THEN
            NEW.descuento := v_descuento_cliente;
        END IF;
        
        NEW.subtotal := ROUND(NEW.cantidad * NEW.precio_unitario * (1 - NEW.descuento / 100.0), 2);
        
        SELECT cantidad INTO v_stock_actual
          FROM stock_sala
         WHERE id_sala = v_id_sala AND cod_vino = NEW.cod_vino
           FOR UPDATE;
        
        IF NOT FOUND THEN
            v_stock_actual := 0;
        END IF;
        
        IF v_stock_actual < NEW.cantidad THEN
            RAISE EXCEPTION 'RN-09: Stock insuficiente del vino % en la sala % (disponible %, solicitado %)', 
                NEW.cod_vino, v_id_sala, v_stock_actual, NEW.cantidad;
        END IF;
        
        IF FOUND THEN
            UPDATE stock_sala
               SET cantidad = cantidad - NEW.cantidad
             WHERE id_sala = v_id_sala AND cod_vino = NEW.cod_vino;
        ELSE
            RAISE EXCEPTION 'RN-09: No existe stock del vino % en la sala %', NEW.cod_vino, v_id_sala;
        END IF;
        
        UPDATE comprobante
           SET subtotal = s.o_subtotal,
               descuento = s.o_descuento,
               total = s.o_total
          FROM fn_total_comprobante(NEW.nro_comprobante) s
         WHERE nro_comprobante = NEW.nro_comprobante;
        
        RETURN NEW;
        
    ELSIF TG_OP = 'UPDATE' THEN
        SELECT id_sala INTO v_id_sala
          FROM comprobante
         WHERE nro_comprobante = NEW.nro_comprobante;
        
        IF NEW.nro_comprobante IS DISTINCT FROM OLD.nro_comprobante OR
           NEW.cod_vino IS DISTINCT FROM OLD.cod_vino THEN
            RAISE EXCEPTION 'No se puede modificar la clave del renglon de comprobante';
        END IF;
        
        SELECT fn_descuento_cliente(c.id_cliente) INTO v_descuento_cliente
          FROM comprobante c
         WHERE c.nro_comprobante = NEW.nro_comprobante;
        
        IF NEW.descuento IS DISTINCT FROM v_descuento_cliente THEN
            NEW.descuento := v_descuento_cliente;
        END IF;
        
        NEW.subtotal := ROUND(NEW.cantidad * NEW.precio_unitario * (1 - NEW.descuento / 100.0), 2);
        
        IF NEW.cantidad IS DISTINCT FROM OLD.cantidad THEN
            IF NEW.cantidad > OLD.cantidad THEN
                SELECT cantidad INTO v_stock_actual
                  FROM stock_sala
                 WHERE id_sala = v_id_sala AND cod_vino = NEW.cod_vino
                   FOR UPDATE;
                
                IF NOT FOUND OR v_stock_actual < (NEW.cantidad - OLD.cantidad) THEN
                    RAISE EXCEPTION 'RN-09: Stock insuficiente para aumentar cantidad del vino % en la sala %', 
                        NEW.cod_vino, v_id_sala;
                END IF;
                
                UPDATE stock_sala
                   SET cantidad = cantidad - (NEW.cantidad - OLD.cantidad)
                 WHERE id_sala = v_id_sala AND cod_vino = NEW.cod_vino;
            ELSIF NEW.cantidad < OLD.cantidad THEN
                UPDATE stock_sala
                   SET cantidad = cantidad + (OLD.cantidad - NEW.cantidad)
                 WHERE id_sala = v_id_sala AND cod_vino = NEW.cod_vino;
            END IF;
        END IF;
        
        UPDATE comprobante
           SET subtotal = s.o_subtotal,
               descuento = s.o_descuento,
               total = s.o_total
          FROM fn_total_comprobante(NEW.nro_comprobante) s
         WHERE nro_comprobante = NEW.nro_comprobante;
        
        RETURN NEW;
        
    ELSIF TG_OP = 'DELETE' THEN
        SELECT EXISTS(SELECT 1 FROM comprobante WHERE nro_comprobante = OLD.nro_comprobante) INTO v_cabecera_existe;
        
        IF v_cabecera_existe THEN
            SELECT id_sala INTO v_id_sala
              FROM comprobante
             WHERE nro_comprobante = OLD.nro_comprobante;
            
            UPDATE stock_sala
               SET cantidad = cantidad + OLD.cantidad
             WHERE id_sala = v_id_sala AND cod_vino = OLD.cod_vino;
            
            UPDATE comprobante
               SET subtotal = s.o_subtotal,
                   descuento = s.o_descuento,
                   total = s.o_total
              FROM fn_total_comprobante(OLD.nro_comprobante) s
             WHERE nro_comprobante = OLD.nro_comprobante;
        ELSE
            NULL;
        END IF;
        
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_renglon_comprobante
    BEFORE INSERT OR UPDATE OR DELETE ON renglon_comprobante
    FOR EACH ROW
    EXECUTE FUNCTION fn_trg_renglon_comprobante();



COMMIT;
