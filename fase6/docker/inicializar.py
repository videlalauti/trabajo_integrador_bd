
"""Inicializacion segura de PostgreSQL para Docker - Fase 6."""

import gzip
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = "bodegas_fase6_docker"
RESPALDO = RAIZ / "db/seed/dump_completo.sql.gz"
ROLES = RAIZ / "fase6/docker/00_roles.sql"
INDICES = RAIZ / "db/migrations/008_indices.sql"

SHA_ESPERADO = (
    "D1A066940B9429866FB490D7CE5675159218"
    "BDB7F7376CB9582C490696DD0B78"
)

COMANDO = [
    "docker", "compose", "-f", "compose.fase6.yml",
    "exec", "-T", "db",
    "psql", "-X", "-qAt",
    "-v", "ON_ERROR_STOP=1",
    "--single-transaction",
    "-U", "postgres",
    "-d", BASE,
]


def ejecutar_sql(sql, ocultar_error=False):
    proceso = subprocess.run(
        COMANDO,
        input=sql,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        cwd=RAIZ,
    )

    if proceso.returncode != 0:
        if ocultar_error:
            raise RuntimeError(
                "Fallo la configuracion del usuario de API."
            )
        raise RuntimeError(proceso.stderr[-2000:])

    return proceso.stdout.strip()


def verificar_base():
    resultado = ejecutar_sql("""
        SELECT
            current_database(),
            current_setting('server_version_num'),
            (
                SELECT COUNT(*)
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n
                  ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')
            );
    """)

    nombre, version, objetos = resultado.split("|")

    if nombre != BASE:
        raise RuntimeError("Base de destino incorrecta.")

    if int(version) < 180000:
        raise RuntimeError("Se requiere PostgreSQL 18.")

    return int(objetos)


def verificar_respaldo():
    if not RESPALDO.is_file():
        raise RuntimeError("Falta el respaldo de Fase 3.")

    huella = hashlib.sha256(
        RESPALDO.read_bytes()
    ).hexdigest().upper()

    if huella != SHA_ESPERADO:
        raise RuntimeError("El SHA-256 del respaldo no coincide.")

    print("Respaldo SHA-256: OK")


def restaurar():
    registro = (
        Path(tempfile.gettempdir())
        / "bodegas_fase6_inicializacion.log"
    )

    comando = COMANDO.copy()

    with gzip.open(RESPALDO, "rb") as origen, \
         registro.open("wb") as salida:

        proceso = subprocess.Popen(
            comando,
            stdin=subprocess.PIPE,
            stdout=salida,
            stderr=subprocess.STDOUT,
            cwd=RAIZ,
        )

        try:
            shutil.copyfileobj(
                origen, proceso.stdin, 1024 * 1024
            )
        except BrokenPipeError:
            pass
        finally:
            proceso.stdin.close()

        codigo = proceso.wait()

    if codigo != 0:
        raise RuntimeError(
            f"Restauracion fallida. Revisar: {registro}"
        )

    print("Restauracion: OK")


def configurar_api():
    clave = os.environ["FASE6_API_PASSWORD"]

    if any(c in clave for c in ("\n", "\r", "\x00")):
        raise RuntimeError("Caracteres invalidos en la clave.")

    clave_sql = clave.replace("'", "''")

    sql = f"""
        SET standard_conforming_strings = on;

        ALTER ROLE bodega_api
            WITH LOGIN PASSWORD '{clave_sql}'
            NOSUPERUSER NOCREATEDB NOCREATEROLE
            NOREPLICATION NOBYPASSRLS;

        GRANT bodega_api_rw TO bodega_api
            WITH INHERIT TRUE, SET TRUE;

        ALTER ROLE bodega_api
            SET search_path = pg_catalog, public, pg_temp;

        REVOKE CREATE, TEMPORARY
            ON DATABASE bodegas_fase6_docker
            FROM PUBLIC;
    """

    ejecutar_sql(sql, ocultar_error=True)
    print("Usuario bodega_api: configurado")


def verificar_resultado():
    resultado = ejecutar_sql("""
        SELECT
            (SELECT COUNT(*) FROM pg_catalog.pg_tables
             WHERE schemaname = 'public'),
            (SELECT COUNT(*) FROM pg_catalog.pg_index i
             JOIN pg_catalog.pg_class c
               ON c.oid = i.indexrelid
             WHERE c.relnamespace = 'public'::regnamespace
               AND c.relname IN (
                   'idx_comprobante_sala_fecha',
                   'idx_rc_cod_vino',
                   'idx_comprobante_id_cliente_inc',
                   'idx_rt_cod_vino_nro',
                   'idx_transferencia_pendiente_sala'
               )
               AND i.indisvalid
               AND i.indisready),
            pg_has_role(
                'bodega_api', 'bodega_api_rw', 'MEMBER'
            ),
            (SELECT rolcanlogin FROM pg_catalog.pg_roles
             WHERE rolname = 'bodega_api');
    """)

    tablas, indices, miembro, login = resultado.split("|")

    if (tablas, indices, miembro, login) != (
        "27", "5", "t", "t"
    ):
        raise RuntimeError(
            "La verificacion final no coincide: " + resultado
        )

    print("27 tablas: OK")
    print("5 indices: OK")
    print("Rol bodega_api: OK")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in (
        "--check", "--run"
    ):
        raise RuntimeError("Uso: inicializar.py --check | --run")

    if not os.environ.get("FASE6_PG_ADMIN_PASSWORD"):
        raise RuntimeError("Falta FASE6_PG_ADMIN_PASSWORD.")

    if not os.environ.get("FASE6_API_PASSWORD"):
        raise RuntimeError("Falta FASE6_API_PASSWORD.")

    verificar_respaldo()

    objetos = verificar_base()
    print("Objetos existentes en public:", objetos)

    if sys.argv[1] == "--check":
        if objetos:
            print("Base ya preparada: inicializacion bloqueada.")
        else:
            print("Base vacia: apta para inicializacion.")
        print("MODO VERIFICACION: OK")
        return

    if objetos != 0:
        raise RuntimeError(
            "SEGURIDAD: no se inicializa una base con objetos."
        )

    confirmacion = input(
        "Escribi INICIALIZAR para preparar la base vacia: "
    )

    if confirmacion != "INICIALIZAR":
        raise RuntimeError("Operacion cancelada.")

    ejecutar_sql(ROLES.read_text(encoding="utf-8-sig"))
    print("Roles: OK")

    restaurar()

    ejecutar_sql(INDICES.read_text(encoding="utf-8-sig"))
    print("Indices: creados")

    configurar_api()
    verificar_resultado()

    print("INICIALIZACION COMPLETA: OK")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
