-- SOLO LECTURA. Requiere psql con variables -v sala=ID -v vino=ID.
-- Aprobacion de Jose antes de comparar; congelar otras escrituras de ensayo.
-- Verificar nombres en migraciones vigentes. NO ejecutar INSERT/UPDATE desde este archivo.
\if :{?sala}
\else
  \echo ERROR: falta -v sala=<id>
  \quit 2
\endif
\if :{?vino}
\else
  \echo ERROR: falta -v vino=<id>
  \quit 2
\endif
SELECT id_sala, cod_vino, cantidad AS stock_actual
FROM public.stock_sala WHERE id_sala = :sala AND cod_vino = :vino;
SELECT COUNT(*) AS total_comprobantes FROM public.comprobante;
SELECT COUNT(*) AS total_renglones FROM public.renglon_comprobante;
-- IMPORTANTE: los conteos globales solo son concluyentes con ventana sin escrituras.
-- Registrar tambien identificador/cliente/correlation-id de solicitud fallida en logs.
-- Para columnas de correlacion individual, Jose debe aprobar consulta especifica
-- tras confirmar esquema final y endpoint de venta.
