BEGIN;

-- 1. DOMINIO CUIT
ALTER DOMAIN cuit_dom
    ADD CONSTRAINT chk_cuit_dom_formato
    CHECK (VALUE ~ '^[0-9]{11}$');

-- 2. RESTRICCIONES UNIQUE
-- RN-04: una parcela se cosecha como maximo una vez por campania
ALTER TABLE lote_uva
    ADD CONSTRAINT uq_lote_uva_parcela_campania
    UNIQUE (id_finca, nro_parcela, campania);

-- Clave natural del transportista
ALTER TABLE transportista
    ADD CONSTRAINT uq_transportista_cuit
    UNIQUE (cuit);

-- Un cliente no puede repetir el mismo tipo y numero de documento
ALTER TABLE cliente
    ADD CONSTRAINT uq_cliente_documento
    UNIQUE (tipo_doc, nro_doc);

-- Clave natural del catalogo de cepas
ALTER TABLE cepa
    ADD CONSTRAINT uq_cepa_nombre
    UNIQUE (nombre);

ALTER TABLE vino
    ADD CONSTRAINT uq_vino_nombre_anada_volumen
    UNIQUE (nombre, anada, volumen_ml);

-- Clave natural del catalogo de maridajes
ALTER TABLE maridaje
    ADD CONSTRAINT uq_maridaje_nombre
    UNIQUE (nombre);

-- 3. RESTRICCIONES CHECK
ALTER TABLE sala_venta
    ADD CONSTRAINT chk_sala_venta_dia_cierre
    CHECK (dia_cierre IN ('lunes', 'martes', 'miercoles', 'jueves',
                          'viernes', 'sabado', 'domingo'));

-- EMPLEADO: salario positivo (RN-15)
ALTER TABLE empleado
    ADD CONSTRAINT chk_empleado_salario
    CHECK (salario > 0);

-- FINCA: superficie positiva (RN-15)
ALTER TABLE finca
    ADD CONSTRAINT chk_finca_superficie
    CHECK (superficie_ha > 0);

-- PARCELA: numero y superficie positivos (diccionario, RN-15).
ALTER TABLE parcela
    ADD CONSTRAINT chk_parcela_nro
    CHECK (nro_parcela > 0),
    ADD CONSTRAINT chk_parcela_superficie
    CHECK (superficie_ha > 0);

-- LOTE_UVA: kilos cosechados positivos (RN-15)
ALTER TABLE lote_uva
    ADD CONSTRAINT chk_lote_uva_kg
    CHECK (kg_cosechados > 0);

-- VINO: precio, volumen y graduacion (RN-01, RN-15)
ALTER TABLE vino
    ADD CONSTRAINT chk_vino_precio
    CHECK (precio > 0),
    ADD CONSTRAINT chk_vino_volumen
    CHECK (volumen_ml > 0),
    ADD CONSTRAINT chk_vino_graduacion
    CHECK (graduacion BETWEEN 5 AND 20);

-- VINO_CEPA: porcentaje individual valido (RN-05)
ALTER TABLE vino_cepa
    ADD CONSTRAINT chk_vino_cepa_porcentaje
    CHECK (porcentaje > 0 AND porcentaje <= 100);

-- TIPO_CLIENTE: rango general y correspondencia con el tipo (RN-06)
ALTER TABLE tipo_cliente
    ADD CONSTRAINT chk_tipo_cliente_descuento_rango
    CHECK (descuento BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_tipo_cliente_descuento_tipo
    CHECK (
        (tipo_cliente = 'socio' AND descuento = 10)
        OR (tipo_cliente = 'distribuidor' AND descuento = 20)
        OR (tipo_cliente = 'exportador' AND descuento = 30)
    );

-- CLIENTE: descuento especial opcional dentro de rango
ALTER TABLE cliente
    ADD CONSTRAINT chk_cliente_descuento_especial
    CHECK (descuento_especial IS NULL
           OR descuento_especial BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_cliente_tipo_atributos
    CHECK (
        (tipo_cliente = 'socio'
            AND zona_cobertura IS NULL
            AND nro_habilitacion IS NULL
            AND pais_destino IS NULL)
        OR (tipo_cliente = 'distribuidor'
            AND pais_destino IS NULL)
        OR (tipo_cliente = 'exportador'
            AND zona_cobertura IS NULL
            AND nro_habilitacion IS NULL)
    );

-- PERMISO_EXPORTACION: vencimiento posterior a la emision (RN-07)
ALTER TABLE permiso_exportacion
    ADD CONSTRAINT chk_permiso_fechas
    CHECK (fecha_vencimiento > fecha_emision);

-- COMPROBANTE: importes no negativos (RN-08)
ALTER TABLE comprobante
    ADD CONSTRAINT chk_comprobante_importes
    CHECK (subtotal >= 0 AND descuento >= 0 AND total >= 0);

-- RENGLON_COMPROBANTE: cantidades, precios y descuentos validos
-- (diccionario, RN-08 y RN-15)
ALTER TABLE renglon_comprobante
    ADD CONSTRAINT chk_renglon_comprobante_cantidad
    CHECK (cantidad > 0),
    ADD CONSTRAINT chk_renglon_comprobante_precio
    CHECK (precio_unitario > 0),
    ADD CONSTRAINT chk_renglon_comprobante_descuento
    CHECK (descuento BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_renglon_comprobante_subtotal
    CHECK (subtotal >= 0);

-- RENGLON_INGRESO / RENGLON_TRANSFERENCIA: cantidades positivas (RN-15)
ALTER TABLE renglon_ingreso
    ADD CONSTRAINT chk_renglon_ingreso_cantidad
    CHECK (cantidad > 0);

ALTER TABLE renglon_transferencia
    ADD CONSTRAINT chk_renglon_transferencia_cantidad
    CHECK (cantidad > 0);

-- STOCK: las existencias pueden ser cero, nunca negativas (RN-09)
ALTER TABLE stock_sala
    ADD CONSTRAINT chk_stock_sala_cantidad
    CHECK (cantidad >= 0);

ALTER TABLE stock_deposito
    ADD CONSTRAINT chk_stock_deposito_cantidad
    CHECK (cantidad >= 0);

-- 4. VALORES DEFAULT
ALTER TABLE cliente
    ALTER COLUMN fecha_alta SET DEFAULT CURRENT_DATE;

-- COMPROBANTE: fecha actual e importes iniciales (diccionario, RN-08)
ALTER TABLE comprobante
    ALTER COLUMN fecha SET DEFAULT CURRENT_TIMESTAMP,
    ALTER COLUMN subtotal SET DEFAULT 0,
    ALTER COLUMN descuento SET DEFAULT 0,
    ALTER COLUMN total SET DEFAULT 0;

-- INGRESO: todo ingreso nace en confeccion (RN-10)
ALTER TABLE ingreso
    ALTER COLUMN estado SET DEFAULT 'en_confeccion';

-- TRANSFERENCIA: fecha actual y estado inicial (RN-11)
ALTER TABLE transferencia
    ALTER COLUMN fecha_confeccion SET DEFAULT CURRENT_DATE,
    ALTER COLUMN estado SET DEFAULT 'en_confeccion';

-- 5. ACCIONES REFERENCIALES

-- 5.1 ON DELETE CASCADE: filas dependientes que no existen sin su cabecera
ALTER TABLE renglon_comprobante
    DROP CONSTRAINT fk_renglon_comprobante_comprobante,
    ADD CONSTRAINT fk_renglon_comprobante_comprobante
        FOREIGN KEY (nro_comprobante)
        REFERENCES comprobante (nro_comprobante)
        ON DELETE CASCADE;

ALTER TABLE renglon_ingreso
    DROP CONSTRAINT fk_renglon_ingreso_ingreso,
    ADD CONSTRAINT fk_renglon_ingreso_ingreso
        FOREIGN KEY (cod_ingreso)
        REFERENCES ingreso (cod_ingreso)
        ON DELETE CASCADE;

ALTER TABLE renglon_transferencia
    DROP CONSTRAINT fk_renglon_transferencia_transferencia,
    ADD CONSTRAINT fk_renglon_transferencia_transferencia
        FOREIGN KEY (nro_solicitud)
        REFERENCES transferencia (nro_solicitud)
        ON DELETE CASCADE;

ALTER TABLE vino_cepa
    DROP CONSTRAINT fk_vino_cepa_vino,
    ADD CONSTRAINT fk_vino_cepa_vino
        FOREIGN KEY (cod_vino)
        REFERENCES vino (cod_vino)
        ON DELETE CASCADE;

ALTER TABLE vino_maridaje
    DROP CONSTRAINT fk_vino_maridaje_vino,
    ADD CONSTRAINT fk_vino_maridaje_vino
        FOREIGN KEY (cod_vino)
        REFERENCES vino (cod_vino)
        ON DELETE CASCADE;

ALTER TABLE parcela
    DROP CONSTRAINT fk_parcela_finca,
    ADD CONSTRAINT fk_parcela_finca
        FOREIGN KEY (id_finca)
        REFERENCES finca (id_finca)
        ON DELETE CASCADE;

ALTER TABLE transportista_localidad
    DROP CONSTRAINT fk_transportista_localidad_transportista,
    ADD CONSTRAINT fk_transportista_localidad_transportista
        FOREIGN KEY (cod_transporte)
        REFERENCES transportista (cod_transporte)
        ON DELETE CASCADE;

-- 5.2 ON DELETE RESTRICT: proteccion de historial y de entidades con movimientos

-- RN-14: no se puede borrar un vino con ventas, ingresos, transferencias,
-- stock o auditoria asociados.
ALTER TABLE renglon_comprobante
    DROP CONSTRAINT fk_renglon_comprobante_vino,
    ADD CONSTRAINT fk_renglon_comprobante_vino
        FOREIGN KEY (cod_vino)
        REFERENCES vino (cod_vino)
        ON DELETE RESTRICT;

ALTER TABLE renglon_ingreso
    DROP CONSTRAINT fk_renglon_ingreso_vino,
    ADD CONSTRAINT fk_renglon_ingreso_vino
        FOREIGN KEY (cod_vino)
        REFERENCES vino (cod_vino)
        ON DELETE RESTRICT;

ALTER TABLE renglon_transferencia
    DROP CONSTRAINT fk_renglon_transferencia_vino,
    ADD CONSTRAINT fk_renglon_transferencia_vino
        FOREIGN KEY (cod_vino)
        REFERENCES vino (cod_vino)
        ON DELETE RESTRICT;

ALTER TABLE stock_sala
    DROP CONSTRAINT fk_stock_sala_vino,
    ADD CONSTRAINT fk_stock_sala_vino
        FOREIGN KEY (cod_vino)
        REFERENCES vino (cod_vino)
        ON DELETE RESTRICT;

ALTER TABLE stock_deposito
    DROP CONSTRAINT fk_stock_deposito_vino,
    ADD CONSTRAINT fk_stock_deposito_vino
        FOREIGN KEY (cod_vino)
        REFERENCES vino (cod_vino)
        ON DELETE RESTRICT;

ALTER TABLE auditoria_precio
    DROP CONSTRAINT fk_auditoria_precio_vino,
    ADD CONSTRAINT fk_auditoria_precio_vino
        FOREIGN KEY (cod_vino)
        REFERENCES vino (cod_vino)
        ON DELETE RESTRICT;

-- RN-14: no se puede borrar una bodega con lotes, vinos o ingresos.
-- El CUIT es una clave natural: si se corrige, las referencias se actualizan.
ALTER TABLE lote_uva
    DROP CONSTRAINT fk_lote_uva_bodega,
    ADD CONSTRAINT fk_lote_uva_bodega
        FOREIGN KEY (cuit_bodega)
        REFERENCES bodega (cuit)
        ON DELETE RESTRICT
        ON UPDATE CASCADE;

ALTER TABLE vino
    DROP CONSTRAINT fk_vino_bodega,
    ADD CONSTRAINT fk_vino_bodega
        FOREIGN KEY (cuit_bodega)
        REFERENCES bodega (cuit)
        ON DELETE RESTRICT
        ON UPDATE CASCADE;

ALTER TABLE ingreso
    DROP CONSTRAINT fk_ingreso_bodega,
    ADD CONSTRAINT fk_ingreso_bodega
        FOREIGN KEY (cuit_bodega)
        REFERENCES bodega (cuit)
        ON DELETE RESTRICT
        ON UPDATE CASCADE;

-- RN-14: no se puede borrar un transportista con ingresos.
ALTER TABLE ingreso
    DROP CONSTRAINT fk_ingreso_transportista,
    ADD CONSTRAINT fk_ingreso_transportista
        FOREIGN KEY (cod_transporte)
        REFERENCES transportista (cod_transporte)
        ON DELETE RESTRICT;

ALTER TABLE stock_sala
    DROP CONSTRAINT fk_stock_sala_sala_venta,
    ADD CONSTRAINT fk_stock_sala_sala_venta
        FOREIGN KEY (id_sala)
        REFERENCES sala_venta (id_sala)
        ON DELETE RESTRICT;

ALTER TABLE lote_uva
    DROP CONSTRAINT fk_lote_uva_parcela,
    ADD CONSTRAINT fk_lote_uva_parcela
        FOREIGN KEY (id_finca, nro_parcela)
        REFERENCES parcela (id_finca, nro_parcela)
        ON DELETE RESTRICT
        ON UPDATE CASCADE;

ALTER TABLE cliente
    DROP CONSTRAINT fk_cliente_tipo_cliente,
    ADD CONSTRAINT fk_cliente_tipo_cliente
        FOREIGN KEY (tipo_cliente)
        REFERENCES tipo_cliente (tipo_cliente)
        ON DELETE RESTRICT;
COMMIT;