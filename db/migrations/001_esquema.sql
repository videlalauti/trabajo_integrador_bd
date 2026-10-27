BEGIN;

-- TIPOS ENUMERADOS
CREATE TYPE estado_documento AS ENUM (
    'en_confeccion',
    'terminado',
    'procesado'
);

CREATE TYPE tipo_cepa AS ENUM (
    'tinta',
    'blanca'
);

CREATE TYPE tipo_vino AS ENUM (
    'tinto',
    'blanco',
    'rosado',
    'espumante'
);

-- DOMINIOS
CREATE DOMAIN cuit_dom AS CHAR(11);

-- 1. LOCALIDADES, SALAS DE VENTA Y EMPLEADOS
CREATE TABLE localidad (
    id_localidad        SERIAL,
    cod_postal          VARCHAR(12)  NOT NULL,
    nombre              VARCHAR(100) NOT NULL,
    provincia           VARCHAR(100) NOT NULL,
    encargado_regional  VARCHAR(120) NOT NULL,

    CONSTRAINT pk_localidad PRIMARY KEY (id_localidad)
);

CREATE TABLE sala_venta (
    id_sala         SERIAL,
    calle           VARCHAR(120) NOT NULL,
    numero          VARCHAR(15)  NOT NULL,
    dia_cierre      VARCHAR(12)  NOT NULL,
    id_localidad    INTEGER      NOT NULL,

    CONSTRAINT pk_sala_venta PRIMARY KEY (id_sala),
    CONSTRAINT fk_sala_venta_localidad
        FOREIGN KEY (id_localidad) REFERENCES localidad (id_localidad)
);

CREATE TABLE empleado (
    cuit            cuit_dom,
    nombre          VARCHAR(120)  NOT NULL,
    fecha_ingreso   DATE          NOT NULL,
    salario         NUMERIC(10,2) NOT NULL,
    id_sala         INTEGER       NOT NULL,

    CONSTRAINT pk_empleado PRIMARY KEY (cuit),
    CONSTRAINT fk_empleado_sala_venta
        FOREIGN KEY (id_sala) REFERENCES sala_venta (id_sala)
);

-- 2. PRODUCCION DE UVA
CREATE TABLE finca (
    id_finca        SERIAL,
    nombre          VARCHAR(120)  NOT NULL,
    superficie_ha   NUMERIC(10,2) NOT NULL,
    departamento    VARCHAR(100)  NOT NULL,
    provincia       VARCHAR(100)  NOT NULL,

    CONSTRAINT pk_finca PRIMARY KEY (id_finca)
);

CREATE TABLE cepa (
    id_cepa     SERIAL,
    nombre      VARCHAR(100) NOT NULL,
    tipo        tipo_cepa    NOT NULL,

    CONSTRAINT pk_cepa PRIMARY KEY (id_cepa)
);

CREATE TABLE parcela (
    id_finca        INTEGER       NOT NULL,
    nro_parcela     INTEGER       NOT NULL,
    superficie_ha   NUMERIC(10,2) NOT NULL,
    anio_plantacion INTEGER       NOT NULL,
    id_cepa         INTEGER       NOT NULL,

    CONSTRAINT pk_parcela PRIMARY KEY (id_finca, nro_parcela),
    CONSTRAINT fk_parcela_finca
        FOREIGN KEY (id_finca) REFERENCES finca (id_finca),
    CONSTRAINT fk_parcela_cepa
        FOREIGN KEY (id_cepa) REFERENCES cepa (id_cepa)
);

CREATE TABLE bodega (
    cuit            cuit_dom,
    razon_social    VARCHAR(150) NOT NULL,
    domicilio       VARCHAR(200) NOT NULL,

    CONSTRAINT pk_bodega PRIMARY KEY (cuit)
);

CREATE TABLE lote_uva (
    nro_lote        SERIAL,
    campania        INTEGER       NOT NULL,
    fecha_cosecha   DATE          NOT NULL,
    kg_cosechados   NUMERIC(14,2) NOT NULL,
    id_finca        INTEGER       NOT NULL,
    nro_parcela     INTEGER       NOT NULL,
    cuit_bodega     cuit_dom      NOT NULL,

    CONSTRAINT pk_lote_uva PRIMARY KEY (nro_lote),
    CONSTRAINT fk_lote_uva_parcela
        FOREIGN KEY (id_finca, nro_parcela)
        REFERENCES parcela (id_finca, nro_parcela),
    CONSTRAINT fk_lote_uva_bodega
        FOREIGN KEY (cuit_bodega) REFERENCES bodega (cuit)
);

CREATE TABLE analisis_calidad (
    id_analisis         SERIAL,
    fecha               DATE          NOT NULL,
    grado_brix          NUMERIC(5,2)  NOT NULL,
    ph                  NUMERIC(4,2)  NOT NULL,
    acidez_total_gl     NUMERIC(6,2)  NOT NULL,
    nro_lote            INTEGER       NOT NULL,

    CONSTRAINT pk_analisis_calidad PRIMARY KEY (id_analisis),
    CONSTRAINT fk_analisis_calidad_lote_uva
        FOREIGN KEY (nro_lote) REFERENCES lote_uva (nro_lote)
);

-- 3. VINOS Y COMPOSICION
CREATE TABLE vino (
    cod_vino        SERIAL,
    nombre          VARCHAR(150)  NOT NULL,
    tipo            tipo_vino     NOT NULL,
    anada           INTEGER       NOT NULL,
    volumen_ml      INTEGER       NOT NULL,
    graduacion      NUMERIC(4,2)  NOT NULL,
    precio          NUMERIC(14,2) NOT NULL,
    cuit_bodega     cuit_dom      NOT NULL,

    CONSTRAINT pk_vino PRIMARY KEY (cod_vino),
    CONSTRAINT fk_vino_bodega
        FOREIGN KEY (cuit_bodega) REFERENCES bodega (cuit)
);

CREATE TABLE vino_cepa (
    cod_vino    INTEGER       NOT NULL,
    id_cepa     INTEGER       NOT NULL,
    porcentaje  NUMERIC(5,2)  NOT NULL,

    CONSTRAINT pk_vino_cepa PRIMARY KEY (cod_vino, id_cepa),
    CONSTRAINT fk_vino_cepa_vino
        FOREIGN KEY (cod_vino) REFERENCES vino (cod_vino),
    CONSTRAINT fk_vino_cepa_cepa
        FOREIGN KEY (id_cepa) REFERENCES cepa (id_cepa)
);

CREATE TABLE maridaje (
    id_maridaje             SERIAL,
    nombre                  VARCHAR(120) NOT NULL,
    temperatura_servicio_c  NUMERIC(4,1) NOT NULL,

    CONSTRAINT pk_maridaje PRIMARY KEY (id_maridaje)
);

CREATE TABLE vino_maridaje (
    cod_vino        INTEGER NOT NULL,
    id_maridaje     INTEGER NOT NULL,

    CONSTRAINT pk_vino_maridaje PRIMARY KEY (cod_vino, id_maridaje),
    CONSTRAINT fk_vino_maridaje_vino
        FOREIGN KEY (cod_vino) REFERENCES vino (cod_vino),
    CONSTRAINT fk_vino_maridaje_maridaje
        FOREIGN KEY (id_maridaje) REFERENCES maridaje (id_maridaje)
);

-- 4. CLIENTES Y PERMISOS DE EXPORTACION
CREATE TABLE tipo_cliente (
    tipo_cliente    VARCHAR(20),
    descuento       NUMERIC(5,2) NOT NULL,

    CONSTRAINT pk_tipo_cliente PRIMARY KEY (tipo_cliente)
);

CREATE TABLE cliente (
    id_cliente              SERIAL,
    nombre_razon_social     VARCHAR(150) NOT NULL,
    tipo_doc                VARCHAR(15)  NOT NULL,
    nro_doc                 VARCHAR(30)  NOT NULL,
    direccion               VARCHAR(200) NOT NULL,
    fecha_alta              DATE         NOT NULL,
    id_localidad            INTEGER      NOT NULL,
    tipo_cliente            VARCHAR(20)  NOT NULL,
    descuento_especial      NUMERIC(5,2),
    zona_cobertura          VARCHAR(150),
    nro_habilitacion        VARCHAR(50),
    pais_destino            VARCHAR(100),

    CONSTRAINT pk_cliente PRIMARY KEY (id_cliente),
    CONSTRAINT fk_cliente_localidad
        FOREIGN KEY (id_localidad) REFERENCES localidad (id_localidad),
    CONSTRAINT fk_cliente_tipo_cliente
        FOREIGN KEY (tipo_cliente) REFERENCES tipo_cliente (tipo_cliente)
);

CREATE TABLE permiso_exportacion (
    codigo_permiso      VARCHAR(60),
    id_cliente          INTEGER NOT NULL,
    fecha_emision       DATE    NOT NULL,
    fecha_vencimiento   DATE    NOT NULL,

    CONSTRAINT pk_permiso_exportacion PRIMARY KEY (codigo_permiso),
    CONSTRAINT fk_permiso_exportacion_cliente
        FOREIGN KEY (id_cliente) REFERENCES cliente (id_cliente)
);

-- 5. VENTAS Y COMPROBANTES
CREATE TABLE comprobante (
    nro_comprobante     SERIAL,
    fecha               TIMESTAMP     NOT NULL,
    id_cliente          INTEGER       NOT NULL,
    id_sala             INTEGER       NOT NULL,
    subtotal            NUMERIC(14,2) NOT NULL,
    total               NUMERIC(14,2) NOT NULL,
    descuento           NUMERIC(14,2) NOT NULL,

    CONSTRAINT pk_comprobante PRIMARY KEY (nro_comprobante),
    CONSTRAINT fk_comprobante_cliente
        FOREIGN KEY (id_cliente) REFERENCES cliente (id_cliente),
    CONSTRAINT fk_comprobante_sala_venta
        FOREIGN KEY (id_sala) REFERENCES sala_venta (id_sala)
);

CREATE TABLE renglon_comprobante (
    nro_comprobante     INTEGER       NOT NULL,
    cod_vino            INTEGER       NOT NULL,
    cantidad            INTEGER       NOT NULL,
    precio_unitario     NUMERIC(14,2) NOT NULL,
    descuento           NUMERIC(5,2)  NOT NULL,
    subtotal            NUMERIC(14,2) NOT NULL,

    CONSTRAINT pk_renglon_comprobante
        PRIMARY KEY (nro_comprobante, cod_vino),
    CONSTRAINT fk_renglon_comprobante_comprobante
        FOREIGN KEY (nro_comprobante) REFERENCES comprobante (nro_comprobante),
    CONSTRAINT fk_renglon_comprobante_vino
        FOREIGN KEY (cod_vino) REFERENCES vino (cod_vino)
);

-- 6. TRANSPORTISTAS Y COBERTURA
CREATE TABLE transportista (
    cod_transporte  SERIAL,
    razon_social    VARCHAR(150) NOT NULL,
    cuit            cuit_dom     NOT NULL,
    email           VARCHAR(150) NOT NULL,
    telefono        VARCHAR(30)  NOT NULL,
    domicilio       VARCHAR(200) NOT NULL,

    CONSTRAINT pk_transportista PRIMARY KEY (cod_transporte)
);

CREATE TABLE transportista_localidad (
    cod_transporte  INTEGER NOT NULL,
    id_localidad    INTEGER NOT NULL,

    CONSTRAINT pk_transportista_localidad
        PRIMARY KEY (cod_transporte, id_localidad),
    CONSTRAINT fk_transportista_localidad_transportista
        FOREIGN KEY (cod_transporte) REFERENCES transportista (cod_transporte),
    CONSTRAINT fk_transportista_localidad_localidad
        FOREIGN KEY (id_localidad) REFERENCES localidad (id_localidad)
);

-- 7. INGRESOS DE MERCADERIA
CREATE TABLE ingreso (
    cod_ingreso     SERIAL,
    fecha           DATE             NOT NULL,
    estado          estado_documento NOT NULL,
    cod_transporte  INTEGER          NOT NULL,
    cuit_bodega     cuit_dom         NOT NULL,

    CONSTRAINT pk_ingreso PRIMARY KEY (cod_ingreso),
    CONSTRAINT fk_ingreso_transportista
        FOREIGN KEY (cod_transporte) REFERENCES transportista (cod_transporte),
    CONSTRAINT fk_ingreso_bodega
        FOREIGN KEY (cuit_bodega) REFERENCES bodega (cuit)
);

CREATE TABLE renglon_ingreso (
    cod_ingreso     INTEGER NOT NULL,
    cod_vino        INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL,

    CONSTRAINT pk_renglon_ingreso
        PRIMARY KEY (cod_ingreso, cod_vino),
    CONSTRAINT fk_renglon_ingreso_ingreso
        FOREIGN KEY (cod_ingreso) REFERENCES ingreso (cod_ingreso),
    CONSTRAINT fk_renglon_ingreso_vino
        FOREIGN KEY (cod_vino) REFERENCES vino (cod_vino)
);

-- 8. TRANSFERENCIAS DE MERCADERIA
CREATE TABLE transferencia (
    nro_solicitud       SERIAL,
    fecha_confeccion    DATE             NOT NULL,
    estado              estado_documento NOT NULL,
    id_sala             INTEGER          NOT NULL,

    CONSTRAINT pk_transferencia PRIMARY KEY (nro_solicitud),
    CONSTRAINT fk_transferencia_sala_venta
        FOREIGN KEY (id_sala) REFERENCES sala_venta (id_sala)
);

CREATE TABLE renglon_transferencia (
    nro_solicitud   INTEGER NOT NULL,
    cod_vino        INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL,

    CONSTRAINT pk_renglon_transferencia
        PRIMARY KEY (nro_solicitud, cod_vino),
    CONSTRAINT fk_renglon_transferencia_transferencia
        FOREIGN KEY (nro_solicitud) REFERENCES transferencia (nro_solicitud),
    CONSTRAINT fk_renglon_transferencia_vino
        FOREIGN KEY (cod_vino) REFERENCES vino (cod_vino)
);

-- 9. CONTROL DE STOCK
CREATE TABLE stock_sala (
    id_sala     INTEGER NOT NULL,
    cod_vino    INTEGER NOT NULL,
    cantidad    INTEGER NOT NULL,

    CONSTRAINT pk_stock_sala PRIMARY KEY (id_sala, cod_vino),
    CONSTRAINT fk_stock_sala_sala_venta
        FOREIGN KEY (id_sala) REFERENCES sala_venta (id_sala),
    CONSTRAINT fk_stock_sala_vino
        FOREIGN KEY (cod_vino) REFERENCES vino (cod_vino)
);

CREATE TABLE stock_deposito (
    cod_vino    INTEGER NOT NULL,
    cantidad    INTEGER NOT NULL,

    CONSTRAINT pk_stock_deposito PRIMARY KEY (cod_vino),
    CONSTRAINT fk_stock_deposito_vino
        FOREIGN KEY (cod_vino) REFERENCES vino (cod_vino)
);

-- 10. AUDITORIA
CREATE TABLE auditoria_precio (
    id_auditoria    SERIAL,
    cod_vino        INTEGER       NOT NULL,
    precio_anterior NUMERIC(14,2) NOT NULL,
    precio_nuevo    NUMERIC(14,2) NOT NULL,
    fecha_hora      TIMESTAMP     NOT NULL,
    usuario         VARCHAR(100)  NOT NULL,

    CONSTRAINT pk_auditoria_precio PRIMARY KEY (id_auditoria),
    CONSTRAINT fk_auditoria_precio_vino
        FOREIGN KEY (cod_vino) REFERENCES vino (cod_vino)
);

COMMIT;
