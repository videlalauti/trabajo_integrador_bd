-- Fase 4 - Bodegas del Atuel
-- Integracion de los cinco indices aprobados por coordinacion.
-- Las pruebas experimentales se realizaron sobre una base descartable restaurada desde el dump full.
-- La migracion puede aplicarse posteriormente sobre la base del proyecto, previa validacion.
-- No incluye indices experimentales descartados.

-- Lautaro: S3, igualdad por sala y rango por fecha.
-- Orden: id_sala (=) primero, fecha (rango) despues.
CREATE INDEX IF NOT EXISTS idx_comprobante_sala_fecha
ON public.comprobante (id_sala, fecha);

-- Lautaro: indice sobre FK, mejora en busqueda selectiva por vino;
-- S1 no lo utiliza al procesar todas las ventas.
CREATE INDEX IF NOT EXISTS idx_rc_cod_vino
ON public.renglon_comprobante (cod_vino);

-- Antonio: S12-A; INCLUDE cubre nro_comprobante para Index Only Scan.
CREATE INDEX idx_comprobante_id_cliente_inc
    ON public.comprobante (id_cliente)
    INCLUDE (nro_comprobante);

-- Jose: S4, orden inverso al de PK (nro_solicitud, cod_vino).
CREATE INDEX idx_rt_cod_vino_nro
ON public.renglon_transferencia (cod_vino, nro_solicitud);

-- Jose: S5, parcial. El dump full tiene cero transferencias pendientes.
CREATE INDEX idx_transferencia_pendiente_sala
ON public.transferencia (id_sala)
WHERE estado <> 'procesado';

