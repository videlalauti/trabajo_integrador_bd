"""Orquestador de carga reproducible — Fase 3, Bodegas del Atuel.

Uso (desde db/seed):
    python run_seed.py --check
    python run_seed.py --run

El modo --check NO se conecta ni modifica la base. El modo --run requiere
psycopg, Faker, los cuatro modulos y una base PostgreSQL 16 descartable.
Los modulos exportan seed(conn, rng, faker, config, refs) y NO hacen commit.
"""

from __future__ import annotations

import argparse
import importlib
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from config import SeedConfig, load_config

# Orden obligatorio: datos maestros -> produccion -> existencias -> ventas.
MODULE_NAMES = ("catalogos", "produccion", "logistica", "ventas")


def check_environment(config: SeedConfig) -> None:
    """Valida configuracion sin abrir conexiones ni importar modulos inconclusos."""
    print(f"Perfil: {config.profile} | semilla: {config.seed} | lote: {config.batch_size}")
    print(f"Periodo historico: {config.start_date} a {config.end_date}")
    print(f"Catalogos: {config.catalogs_dir}")
    print("Orden de modulos: " + " -> ".join(MODULE_NAMES))
    print(f"Objetivos de registros: {dict(config.counts)}")
    print("Modo comprobacion: no se abrio conexion ni se insertaron filas.")


def _load_modules() -> list[tuple[str, Any]]:
    loaded = []
    for name in MODULE_NAMES:
        try:
            module = importlib.import_module(f"modules.{name}")
        except ModuleNotFoundError as exc:
            # Mensaje claro cuando aun faltan los archivos de los companeros.
            if exc.name in {"modules", f"modules.{name}"}:
                raise RuntimeError(
                    f"Falta db/seed/modules/{name}.py. Integrar ese modulo antes de ejecutar --run."
                ) from exc
            raise
        seed_fn = getattr(module, "seed", None)
        if not callable(seed_fn):
            raise RuntimeError(f"modules/{name}.py debe exportar seed(conn, rng, faker, config, refs)")
        loaded.append((name, seed_fn))
    return loaded



def generar_auditoria_precio(conn: Any, refs: dict[str, Any]) -> None:
    """Genera una fila de RN-13 mediante el trigger real, tras terminar ventas."""
    vino_ids = refs.get("vino_ids")
    if not isinstance(vino_ids, list) or not vino_ids:
        raise ValueError("RN-13: produccion no publico refs['vino_ids']")

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM public.auditoria_precio")
        auditorias_antes = int(cur.fetchone()[0])
        if auditorias_antes != 0:
            raise ValueError("RN-13: auditoria_precio ya contiene filas; usar base descartable nueva")

        # Modificar un precio despues de ventas mantiene los precios historicos
        # guardados en renglon_comprobante y activa trg_auditoria_precio_vino.
        cur.execute(
            "UPDATE public.vino SET precio = precio + 1.00 "
            "WHERE cod_vino = %s RETURNING cod_vino",
            (int(vino_ids[0]),),
        )
        actualizados = cur.fetchall()
        if len(actualizados) != 1:
            raise RuntimeError("RN-13: no se pudo actualizar exactamente un vino")
        cur.execute("SELECT COUNT(*) FROM public.auditoria_precio")
        auditorias_despues = int(cur.fetchone()[0])
        if auditorias_despues != auditorias_antes + 1:
            raise RuntimeError("RN-13: el trigger no genero exactamente una fila de auditoria")
    print(f"OK RN-13: 1 cambio real de precio; auditoria_precio={auditorias_despues}")


def run(config: SeedConfig) -> None:
    """Carga por fases. Cada modulo es una transaccion indivisible.

    Si ocurre un error se revierte el modulo actual; los modulos anteriores
    que terminaron ya estan confirmados. Por eso usar SIEMPRE una base vacia
    para cada ejecucion de la semilla: no es un cargador incremental.
    """
    # Fallar antes de conectar si faltan dependencias o modulos.
    try:
        import psycopg
        from faker import Faker
    except ImportError as exc:
        raise RuntimeError("Instalar dependencias: python -m pip install 'psycopg[binary]' faker") from exc

    modules = _load_modules()
    kwargs = config.connection_kwargs()
    # Advertencia explicita: el orquestador no recrea ni borra bases.
    if config.db_name in {"postgres", "template0", "template1"}:
        raise ValueError("PGDATABASE debe identificar una base descartable, no una base del sistema")

    refs: dict[str, Any] = {}
    # RNG/Faker por modulo: la salida de uno no cambia la aleatoriedad de los otros.
    print(f"Iniciando perfil={config.profile} en PGDATABASE={config.db_name}")
    total_start = perf_counter()
    with psycopg.connect(**kwargs, autocommit=False) as conn:
        # No se desactivan triggers, FK ni restricciones.
        for index, (name, seed_fn) in enumerate(modules):
            rng = random.Random(config.seed + index)
            fake = Faker("es_AR")
            fake.seed_instance(config.seed + index)
            t0 = perf_counter()
            try:
                # Los modulos NO deben hacer commit ni rollback internamente.
                outcome = seed_fn(conn, rng, fake, config, refs)
                conn.commit()  # valida tambien constraints diferidas.
            except Exception:
                conn.rollback()
                print(f"ERROR en modulo {name}: transaccion revertida", file=sys.stderr)
                raise
            print(f"OK {name}: {perf_counter() - t0:.2f} s" +
                  (f" | resultado: {outcome}" if outcome is not None else ""))
        # Paso final del orquestador: poblar auditoria_precio con el trigger RN-13.
        try:
            generar_auditoria_precio(conn, refs)
            conn.commit()
        except Exception:
            conn.rollback()
            print("ERROR en RN-13: transaccion de auditoria revertida", file=sys.stderr)
            raise
    print(f"Carga finalizada en {perf_counter() - total_start:.2f} s")
    print("PENDIENTE: ejecutar control_integridad.sql y registrar conteos/tiempos de la base.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga Fase 3 Bodegas del Atuel")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Verificar configuracion sin conectarse")
    group.add_argument("--run", action="store_true", help="Ejecutar carga sobre base descartable")
    args = parser.parse_args()
    try:
        config = load_config()
        if args.check:
            check_environment(config)
        else:
            run(config)
    except (RuntimeError, ValueError, ImportError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
