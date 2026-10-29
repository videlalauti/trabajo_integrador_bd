"""Fase 3 / Rol B: datos de producción vitivinícola.

Contrato: seed(conn, rng, faker, config, refs).
No abre conexiones ni ejecuta commit/rollback: la transacción pertenece a run_seed.py.
Requiere catálogos y bodegas cargados por modules.catalogos.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Iterable, Sequence

TABLAS_A_CARGAR = (
    "finca",
    "parcela",
    "lote_uva",
    "analisis_calidad",
    "vino",
    "vino_cepa",
    "vino_maridaje",
)
TIPOS_VINO = ("tinto", "blanco", "rosado", "espumante")


def _chunks(rows: Sequence[tuple[Any, ...]], size: int) -> Iterable[Sequence[tuple[Any, ...]]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


def _insert_many(cur: Any, sql: str, rows: list[tuple[Any, ...]], batch_size: int) -> None:
    if not rows:
        return
    for batch in _chunks(rows, batch_size):
        cur.executemany(sql, batch)


def _random_date(rng: Any, start: date, end: date) -> date:
    if end < start:
        raise ValueError(f"Rango de fechas inválido: {start} a {end}")
    return start + timedelta(days=rng.randint(0, (end - start).days))


def _harvest_date(rng: Any, campaign: int, end_date: date) -> date:
    """Cosecha mendocina de verano/otoño, sin exceder el corte histórico."""
    start = date(campaign, 2, 1)
    end = min(date(campaign, 4, 30), end_date)
    if end < start:
        raise ValueError(f"La campaña {campaign} queda fuera del período configurado")
    return _random_date(rng, start, end)


def _percentages(n: int, rng: Any) -> list[Decimal]:
    if n == 1:
        return [Decimal("100.00")]
    if n == 2:
        first = Decimal(rng.choice(["50", "55", "60", "65", "70", "75", "80"]))
        return [first, Decimal("100") - first]
    values = [Decimal("50.00"), Decimal("30.00"), Decimal("20.00")]
    rng.shuffle(values)
    return values


def seed(conn: Any, rng: Any, faker: Any, config: Any, refs: dict[str, Any]) -> dict[str, int]:
    """Carga fincas, parcelas, lotes, análisis, vinos, cortes y maridajes."""
    counts_cfg = config.counts
    finca_count = int(counts_cfg["finca"])
    parcela_count = int(counts_cfg["parcela"])
    lote_count = int(counts_cfg["lote_uva"])
    analisis_count = int(counts_cfg["analisis_calidad"])
    vino_count = int(counts_cfg["vino"])
    batch_size = int(config.batch_size)
    start_date = config.start_date
    end_date = config.end_date

    if min(finca_count, parcela_count, lote_count, analisis_count, vino_count, batch_size) <= 0:
        raise ValueError("Producción requiere cantidades positivas y BATCH_SIZE >= 1")
    if end_date < start_date:
        raise ValueError("El período histórico configurado es inválido")

    bodega_cuits = list(refs.get("bodega_cuits", []))
    cepa_ids_por_nombre = dict(refs.get("cepa_ids_por_nombre", {}))
    cepa_tipos_por_nombre = dict(refs.get("cepa_tipos_por_nombre", {}))
    maridaje_ids = list(refs.get("maridaje_ids", []))
    departamentos = list(refs.get("departamentos_mendoza", []))
    tipos_vino = list(refs.get("tipos_vino", []))

    if not bodega_cuits:
        raise ValueError("Faltan refs['bodega_cuits']; ejecutar primero modules.catalogos")
    if not cepa_ids_por_nombre or not cepa_tipos_por_nombre:
        raise ValueError("Faltan referencias de cepas publicadas por modules.catalogos")
    if not maridaje_ids:
        raise ValueError("Faltan refs['maridaje_ids']; ejecutar primero modules.catalogos")
    if not departamentos:
        raise ValueError("Faltan refs['departamentos_mendoza']; revisar catalogs/departamentos_mendoza.csv")
    if set(tipos_vino) != set(TIPOS_VINO):
        raise ValueError("refs['tipos_vino'] debe contener tinto, blanco, rosado y espumante")

    cepas_por_tipo: dict[str, list[int]] = {"tinta": [], "blanca": []}
    for nombre, ident in cepa_ids_por_nombre.items():
        tipo = cepa_tipos_por_nombre.get(nombre)
        if tipo in cepas_por_tipo:
            cepas_por_tipo[tipo].append(int(ident))
    if not cepas_por_tipo["tinta"] or not cepas_por_tipo["blanca"]:
        raise ValueError("Se necesitan cepas tintas y blancas para producir todos los tipos de vino")

    counts: dict[str, int] = {}
    finca_ids: list[int] = []
    parcela_keys: list[tuple[int, int, int, int]] = []  # finca, parcela, cepa, año de plantación
    lote_info: list[tuple[int, date]] = []
    vino_ids: list[int] = []

    with conn.cursor() as cur:
        # No mezclar una carga nueva con restos de ejecuciones anteriores.
        for table in TABLAS_A_CARGAR:
            cur.execute(f"SELECT COUNT(*) FROM public.{table}")
            if cur.fetchone()[0] != 0:
                raise ValueError(f"La tabla {table} no está vacía: usar una base descartable nueva")

        # 1) Fincas. Se guardan las claves reales retornadas por PostgreSQL.
        for i in range(finca_count):
            ident = cur.execute(
                "INSERT INTO public.finca (nombre, superficie_ha, departamento, provincia) "
                "VALUES (%s, %s, %s, %s) RETURNING id_finca",
                (f"Finca DEMO Atuel {i + 1:04d}",
                 Decimal(rng.randrange(25000, 100001)) / Decimal(100),
                 rng.choice(departamentos), "Mendoza"),
            ).fetchone()[0]
            finca_ids.append(int(ident))
        counts["finca"] = len(finca_ids)

        # 2) Parcelas: reparto equilibrado entre fincas, superficie total holgada.
        parcelas_por_finca = [0] * finca_count
        parcel_rows: list[tuple[int, int, Decimal, int, int]] = []
        for i in range(parcela_count):
            finca_idx = i % finca_count
            parcelas_por_finca[finca_idx] += 1
            tipo_cepa = rng.choice(("tinta", "blanca"))
            cepa_id = int(rng.choice(cepas_por_tipo[tipo_cepa]))
            plant_year = rng.randint(1995, max(1995, start_date.year - 1))
            nro_parcela = parcelas_por_finca[finca_idx]
            superficie = Decimal(rng.randrange(100, 801)) / Decimal(100)
            parcel_rows.append((finca_ids[finca_idx], nro_parcela, superficie, plant_year, cepa_id))
            parcela_keys.append((finca_ids[finca_idx], nro_parcela, cepa_id, plant_year))
        _insert_many(
            cur,
            "INSERT INTO public.parcela (id_finca, nro_parcela, superficie_ha, anio_plantacion, id_cepa) "
            "VALUES (%s, %s, %s, %s, %s)",
            parcel_rows,
            batch_size,
        )
        counts["parcela"] = len(parcel_rows)

        # 3) Un lote por parcela y campaña como máximo (RN-04). Se muestrea
        # entre combinaciones únicas para respetar también el volumen objetivo.
        campaigns = list(range(start_date.year, end_date.year + 1))
        combinations = [(p[0], p[1], year) for p in parcela_keys for year in campaigns
                        if year >= p[3] + 1 and date(year, 2, 1) <= end_date]
        if lote_count > len(combinations):
            raise ValueError(
                f"lote_uva solicitado ({lote_count}) supera las combinaciones parcela/campaña válidas "
                f"({len(combinations)}); reducir el objetivo o ampliar el período"
            )
        selected_combinations = rng.sample(combinations, lote_count)
        parcel_cepa = {(p[0], p[1]): p[2] for p in parcela_keys}
        lot_rows: list[tuple[int, int, int, date, Decimal, str]] = []
        for id_finca, nro_parcela, campaign in selected_combinations:
            harvest = _harvest_date(rng, campaign, end_date)
            kg = Decimal(rng.randrange(80000, 1500001)) / Decimal(100)
            bodega = str(rng.choice(bodega_cuits)).strip()
            lot_rows.append((id_finca, nro_parcela, campaign, harvest, kg, bodega))
        # Se insertan individualmente para capturar las PK reales que usarán los análisis.
        for id_finca, nro_parcela, campaign, harvest, kg, bodega in lot_rows:
            nro_lote = cur.execute(
                "INSERT INTO public.lote_uva "
                "(campania, fecha_cosecha, kg_cosechados, id_finca, nro_parcela, cuit_bodega) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING nro_lote",
                (campaign, harvest, kg, id_finca, nro_parcela, bodega),
            ).fetchone()[0]
            lote_info.append((int(nro_lote), harvest))
        counts["lote_uva"] = len(lote_info)

        # 4) Uno o más análisis por lote; entre 1 y 30 días después de cosechar.
        # El límite superior también respeta el fin del período histórico configurado.
        analysis_rows: list[tuple[date, Decimal, Decimal, Decimal, int]] = []
        for i in range(analisis_count):
            nro_lote, harvest = lote_info[i % len(lote_info)]
            analysis_start = harvest + timedelta(days=1)
            analysis_end = min(harvest + timedelta(days=30), end_date)
            if analysis_end < analysis_start:
                raise ValueError(
                    f"No hay ventana válida para analizar el lote {nro_lote} cosechado el {harvest}"
                )
            fecha = _random_date(rng, analysis_start, analysis_end)
            brix = Decimal(rng.randrange(1800, 2801)) / Decimal(100)
            ph = Decimal(rng.randrange(280, 401)) / Decimal(100)
            acidez = Decimal(rng.randrange(450, 901)) / Decimal(100)
            analysis_rows.append((fecha, brix, ph, acidez, nro_lote))
        _insert_many(
            cur,
            "INSERT INTO public.analisis_calidad (fecha, grado_brix, ph, acidez_total_gl, nro_lote) "
            "VALUES (%s, %s, %s, %s, %s)",
            analysis_rows,
            batch_size,
        )
        counts["analisis_calidad"] = len(analysis_rows)

        # 5) Vinos. Nombre único y composición compatible con el tipo de vino.
        composition_rows: list[tuple[int, int, Decimal]] = []
        pairing_rows: list[tuple[int, int]] = []
        for i in range(vino_count):
            tipo = tipos_vino[i % len(tipos_vino)]
            if tipo == "tinto":
                available = cepas_por_tipo["tinta"]
            elif tipo == "blanco":
                available = cepas_por_tipo["blanca"]
            elif tipo == "rosado":
                available = cepas_por_tipo["tinta"]
            else:  # espumante
                available = cepas_por_tipo["blanca"]
            n_cepas = min(len(available), rng.choice((1, 2, 3)))
            selected_cepas = rng.sample(available, n_cepas)
            percentages = _percentages(n_cepas, rng)
            anada = rng.randint(max(start_date.year, 2022), end_date.year)
            volumen = rng.choice((375, 750, 1500))
            nombre = f"{faker.word().capitalize()} Atuel {i + 1:04d}"
            graduacion = Decimal(rng.randrange(1100, 1501)) / Decimal(100)
            precio = Decimal(rng.randrange(350000, 2500001)) / Decimal(100)
            bodega = str(rng.choice(bodega_cuits)).strip()
            cod_vino = cur.execute(
                "INSERT INTO public.vino (nombre, tipo, anada, volumen_ml, graduacion, precio, cuit_bodega) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING cod_vino",
                (nombre, tipo, anada, volumen, graduacion, precio, bodega),
            ).fetchone()[0]
            cod_vino = int(cod_vino)
            vino_ids.append(cod_vino)
            composition_rows.extend(
                (cod_vino, int(cepa_id), porcentaje)
                for cepa_id, porcentaje in zip(selected_cepas, percentages)
            )
            pair_count = min(len(maridaje_ids), rng.randint(1, min(3, len(maridaje_ids))))
            for maridaje_id in rng.sample(maridaje_ids, pair_count):
                pairing_rows.append((cod_vino, int(maridaje_id)))

        # Los triggers de RN-05 son diferidos: composición completa antes del COMMIT.
        _insert_many(
            cur,
            "INSERT INTO public.vino_cepa (cod_vino, id_cepa, porcentaje) VALUES (%s, %s, %s)",
            composition_rows,
            batch_size,
        )
        _insert_many(
            cur,
            "INSERT INTO public.vino_maridaje (cod_vino, id_maridaje) VALUES (%s, %s)",
            pairing_rows,
            batch_size,
        )
        counts["vino"] = len(vino_ids)
        counts["vino_cepa"] = len(composition_rows)
        counts["vino_maridaje"] = len(pairing_rows)

    # El módulo siguiente (logística) y ventas necesitan las PK reales, no IDs asumidos.
    refs["vino_ids"] = vino_ids
    refs["finca_ids"] = finca_ids
    refs["parcela_keys"] = [(finca_id, nro_parcela) for finca_id, nro_parcela, _, _ in parcela_keys]
    refs["lote_uva_ids"] = [nro_lote for nro_lote, _ in lote_info]
    return counts
