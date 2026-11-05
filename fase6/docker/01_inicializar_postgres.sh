#!/usr/bin/env bash
set -Eeuo pipefail

echo "=== Inicializacion automatica Bodegas del Atuel ==="

if [ "${POSTGRES_DB:-}" != "bodegas_fase6_docker" ]; then
    echo "ERROR: base de destino incorrecta."
    exit 1
fi

: "${POSTGRES_USER:?Falta POSTGRES_USER}"
: "${FASE6_API_PASSWORD:?Falta FASE6_API_PASSWORD}"

DIR="/bootstrap"
DUMP="$DIR/dump_completo.sql.gz"

test -s "$DUMP"
gzip -t "$DUMP"

echo "Verificando SHA-256 del respaldo..."
echo "d1a066940b9429866fb490d7ce5675159218bdb7f7376cb9582c490696dd0b78  $DUMP" | sha256sum -c -

echo "1. Preparando roles..."
psql -X -v ON_ERROR_STOP=1 \
    -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -f "$DIR/00_roles.sql"

echo "2. Restaurando datos..."
gzip -dc "$DUMP" | psql \
    -X -v ON_ERROR_STOP=1 --single-transaction \
    -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    > /tmp/bodegas_restauracion.log

echo "3. Aplicando indices..."
psql -X -v ON_ERROR_STOP=1 \
    -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -f "$DIR/008_indices.sql"

echo "4. Configurando usuario de API..."
psql -X -v ON_ERROR_STOP=1 \
    -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'SQL'
\getenv clave_api FASE6_API_PASSWORD

ALTER ROLE bodega_api
    WITH LOGIN PASSWORD :'clave_api'
    NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOREPLICATION NOBYPASSRLS;

GRANT bodega_api_rw TO bodega_api
    WITH INHERIT TRUE, SET TRUE;

ALTER ROLE bodega_api
    SET search_path = pg_catalog, public, pg_temp;

REVOKE CREATE, TEMPORARY
    ON DATABASE bodegas_fase6_docker
    FROM PUBLIC;

DO $$
BEGIN
    IF (
        SELECT COUNT(*)
        FROM pg_catalog.pg_tables
        WHERE schemaname = 'public'
    ) <> 27 THEN
        RAISE EXCEPTION 'Cantidad de tablas inesperada';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM pg_catalog.pg_class
        WHERE relname IN (
            'idx_comprobante_sala_fecha',
            'idx_rc_cod_vino',
            'idx_comprobante_id_cliente_inc',
            'idx_rt_cod_vino_nro',
            'idx_transferencia_pendiente_sala'
        )
    ) <> 5 THEN
        RAISE EXCEPTION 'Faltan indices';
    END IF;
END
$$;
SQL

echo "INICIALIZACION AUTOMATICA: OK"
