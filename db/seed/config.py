"""Configuracion comun de la Fase 3 del TPI Bodegas del Atuel.

Contrato para los modulos:
    seed(conn, rng, faker, config, refs)

No abre conexiones, no crea tablas ni ejecuta cargas. Los catalogos reales
se leen de CSV y no se reemplazan por datos inventados para alcanzar cuotas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import os
from typing import Mapping


SEED_DIR = Path(__file__).resolve().parent
CATALOGS_DIR = SEED_DIR / "catalogs"
DEFAULT_SEED = 20261027

# Objetivos iniciales; se ajustaran tras la carga pequena y las mediciones.
# Son cantidades aproximadas por tabla, NO limites garantizados ni cantidades
# para catalogos reales, que dependen de sus archivos CSV.
PROFILE_COUNTS: Mapping[str, Mapping[str, int]] = {
    "small": {
        "sala_venta": 5,
        "finca": 5,
        "empleado": 5,
        "parcela": 25,
        "vino": 25,
        "lote_uva": 50,
        "analisis_calidad": 50,
        "ingreso": 10,
        "renglon_ingreso": 20,
        "transferencia": 10,
        "renglon_transferencia": 20,
        "cliente": 100,
        "comprobante": 100,
        "renglon_comprobante": 250,
    },
    "full": {
        "sala_venta": 50,
        "finca": 60,
        "empleado": 60,
        "parcela": 750,
        "vino": 750,
        "lote_uva": 3000,  # 750 parcelas x 5 campanias: maximo 3750 lotes
        "analisis_calidad": 8000,
        "ingreso": 2000,
        "renglon_ingreso": 8000,
        "transferencia": 2000,
        "renglon_transferencia": 8000,
        "cliente": 20000,
        "comprobante": 150000,
        "renglon_comprobante": 500000,
    },
}


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name)
    try:
        value = int(raw) if raw is not None else default
    except ValueError as exc:
        raise ValueError(f"{name} debe ser un numero entero; recibido {raw!r}") from exc
    if value < minimum:
        raise ValueError(f"{name} debe ser >= {minimum}")
    return value


@dataclass(frozen=True)
class SeedConfig:
    profile: str
    seed: int
    start_date: date
    end_date: date
    batch_size: int
    counts: Mapping[str, int]
    catalogs_dir: Path
    db_host: str
    db_port: int
    db_name: str | None
    db_user: str | None
    db_password: str | None

    def connection_kwargs(self) -> dict[str, object]:
        """Parametros para psycopg.connect(**kwargs); no imprime contrasenas."""
        if not self.db_name:
            raise ValueError("Definir PGDATABASE con una base descartable de Fase 3")
        kwargs: dict[str, object] = {
            "host": self.db_host,
            "port": self.db_port,
            "dbname": self.db_name,
        }
        if self.db_user:
            kwargs["user"] = self.db_user
        if self.db_password:
            kwargs["password"] = self.db_password
        return kwargs


def load_config() -> SeedConfig:
    """Carga valores compartidos desde el entorno, sin acceder a PostgreSQL."""
    profile = os.getenv("PROFILE", "small").strip().lower()
    if profile not in PROFILE_COUNTS:
        raise ValueError("PROFILE debe ser 'small' o 'full'")

    seed = _int_env("SEED", DEFAULT_SEED, minimum=0)
    batch_size = _int_env("BATCH_SIZE", 1000)
    # Cinco campanias 2022-2026, segun Anexo B del TPI (octubre de 2026).
    # Fechas historicas de cosecha/produccion e ingresos: hasta septiembre de
    # 2026 para que precedan a las transferencias actuales de RN-11.
    # IMPORTANTE: RN-11 impone CURRENT_DATE a las transferencias; ventas que
    # consumen ese stock no deben fecharse antes de las transferencias.
    # Esta regla de fechas operativas se coordina en logistica.py y ventas.py.
    start_date, end_date = date(2022, 1, 1), date(2026, 9, 30)

    return SeedConfig(
        profile=profile,
        seed=seed,
        start_date=start_date,
        end_date=end_date,
        batch_size=batch_size,
        counts=dict(PROFILE_COUNTS[profile]),
        catalogs_dir=CATALOGS_DIR,
        db_host=os.getenv("PGHOST", "localhost"),
        db_port=_int_env("PGPORT", 5432),
        db_name=os.getenv("PGDATABASE") or None,
        db_user=os.getenv("PGUSER") or None,
        db_password=os.getenv("PGPASSWORD") or None,
    )


if __name__ == "__main__":
    config = load_config()
    print(f"Perfil: {config.profile}; semilla: {config.seed}; lote: {config.batch_size}")
    print(f"Periodo historico: {config.start_date} a {config.end_date}")
    print(f"Objetivos de filas: {dict(config.counts)}")
    print("Configuracion cargada. No se conecto ni modifico la base de datos.")
