r"""
Uso (PowerShell, variables PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD):
    python .\db\seed\prueba_rendimiento.py --filas 10000 --repeticiones 3 --csv "$env:TEMP\prueba_rendimiento.csv"

No modifica tablas permanentes: utiliza una tabla temporal basada en cliente.
La prueba aisla el metodo de insercion; NO evalua triggers ni FK.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from datetime import date
from pathlib import Path
from time import perf_counter
from typing import Any

COLUMNAS = (
    "id_cliente", "nombre_razon_social", "tipo_doc", "nro_doc",
    "direccion", "fecha_alta", "id_localidad", "tipo_cliente",
)
TABLA = "pg_temp.prueba_cliente"
NOMBRES_COLUMNAS = ", ".join(COLUMNAS)
SQL_INSERT = (
    f"INSERT INTO {TABLA} ({NOMBRES_COLUMNAS}) "
    f"VALUES ({', '.join(['%s'] * len(COLUMNAS))})"
)
SQL_COPY = f"COPY {TABLA} ({NOMBRES_COLUMNAS}) FROM STDIN"


def datos_prueba(cantidad: int, localidad: int) -> list[tuple[Any, ...]]:
    return [
        (numero, f"Cliente prueba {numero}", "DNI", f"PR-{numero:08d}",
         f"Calle ensayo {numero}", date(2026, 9, 30), localidad, "socio")
        for numero in range(1, cantidad + 1)
    ]


def insertar_individual(cur: Any, filas: list[tuple[Any, ...]]) -> None:
    for fila in filas:
        cur.execute(SQL_INSERT, fila)


def insertar_copy(cur: Any, filas: list[tuple[Any, ...]]) -> None:
    # COPY transmite los mismos registros por el protocolo COPY.
    with cur.copy(SQL_COPY) as carga:
        for fila in filas:
            carga.write_row(fila)


def medir(conn: Any, filas: list[tuple[Any, ...]], metodo: str) -> float:
    with conn.cursor() as cur:
        # La preparacion y la verificacion no se cuentan en los tiempos.
        cur.execute(f"TRUNCATE TABLE {TABLA}")
        conn.commit()
        inicio = perf_counter()
        if metodo == "fila_por_fila":
            insertar_individual(cur, filas)
        elif metodo == "copy":
            insertar_copy(cur, filas)
        else:
            raise ValueError(f"Metodo desconocido: {metodo}")
        conn.commit()  # Incluido por igual en los dos metodos.
        segundos = perf_counter() - inicio
        cur.execute(f"SELECT COUNT(*) FROM {TABLA}")
        insertadas = int(cur.fetchone()[0])
        conn.commit()
        if insertadas != len(filas):
            raise RuntimeError(
                f"{metodo}: se esperaban {len(filas)} filas, pero hay {insertadas}"
            )
        return segundos


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TPI Etapa 3: 1 INSERT por fila frente a COPY FROM STDIN"
    )
    parser.add_argument("--filas", type=int, default=10_000)
    parser.add_argument("--repeticiones", type=int, default=3)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    if not 100 <= args.filas <= 50_000:
        parser.error("--filas debe estar entre 100 y 50000")
    if not 2 <= args.repeticiones <= 10:
        parser.error("--repeticiones debe estar entre 2 y 10")

    try:
        import psycopg

        # Sin credenciales embebidas: psycopg/libpq lee variables PG*.
        with psycopg.connect(autocommit=False) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_setting('server_version')")
                base, version = cur.fetchone()
                if not str(base).startswith("bodegas_atuel_"):
                    raise ValueError("Usar una base descartable bodegas_atuel_*, no una base del sistema")
                cur.execute("SELECT MIN(id_localidad) FROM public.localidad")
                localidad = cur.fetchone()[0]
                if localidad is None:
                    raise ValueError("La base no contiene localidades; usar small cargada")
                cur.execute(
                    "CREATE TEMP TABLE prueba_cliente "
                    "(LIKE public.cliente INCLUDING CONSTRAINTS INCLUDING INDEXES) "
                    "ON COMMIT PRESERVE ROWS"
                )
                conn.commit()

            filas = datos_prueba(args.filas, int(localidad))
            metodos = ("fila_por_fila", "copy")
            resultados: dict[str, list[float]] = {nombre: [] for nombre in metodos}
            filas_csv: list[dict[str, object]] = []
            print(f"Base: {base} | PostgreSQL: {version}")
            print(f"Muestra identica: {args.filas} filas | repeticiones: {args.repeticiones}")
            print("Tabla temporal basada en cliente; sin FK ni triggers")
            print("Cronometro: insercion + COMMIT; limpieza y COUNT excluidos")

            # Calentamiento fuera de la medicion principal.
            calentamiento = filas[:min(200, len(filas))]
            for metodo in metodos:
                medir(conn, calentamiento, metodo)

            for nro in range(1, args.repeticiones + 1):
                orden = metodos if nro % 2 else tuple(reversed(metodos))
                ronda: dict[str, float] = {}
                for metodo in orden:
                    segundos = medir(conn, filas, metodo)
                    resultados[metodo].append(segundos)
                    ronda[metodo] = segundos
                    filas_csv.append({
                        "base": base,
                        "postgresql": version,
                        "filas": args.filas,
                        "repeticion": nro,
                        "metodo": metodo,
                        "operaciones": args.filas if metodo == "fila_por_fila" else 1,
                        "segundos": f"{segundos:.6f}",
                    })
                print(f"Repeticion {nro}: fila_por_fila={ronda['fila_por_fila']:.3f} s; "
                      f"COPY={ronda['copy']:.3f} s")

        t_individual = statistics.median(resultados["fila_por_fila"])
        t_copy = statistics.median(resultados["copy"])
        print("\nRESULTADO (medianas)")
        print(f"Fila por fila: {t_individual:.3f} s ({args.filas} INSERT)")
        print(f"COPY:          {t_copy:.3f} s (1 operacion COPY)")
        print(f"Aceleracion COPY: {t_individual / t_copy:.2f}x")
        print(f"Ahorro de tiempo: {100 * (1 - t_copy / t_individual):.1f}%")
        print("Verificacion: misma cantidad de filas en cada repeticion")
        print("Seguridad: no se modificaron tablas permanentes")

        if args.csv:
            args.csv.parent.mkdir(parents=True, exist_ok=True)
            with args.csv.open("w", newline="", encoding="utf-8") as f:
                escritor = csv.DictWriter(f, fieldnames=(
                    "base", "postgresql", "filas", "repeticion", "metodo", "operaciones", "segundos"
                ))
                escritor.writeheader()
                escritor.writerows(filas_csv)
            print(f"Evidencia: {args.csv.resolve()}")
        return 0
    except Exception as exc:
        print(f"ERROR ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
