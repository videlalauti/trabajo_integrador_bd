"""Fase 3 / Rol A: catálogos verificables y maestros de demostración.

Interfaz acordada con run_seed.py: seed(conn, rng, faker, config, refs).
No abre conexiones, no crea tablas, ni ejecuta commit o rollback.
La carga NO es incremental: requiere las siete tablas objetivo vacías.
"""
from __future__ import annotations

import csv
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


TIPOS_CLIENTE = (("socio", Decimal("10")),
                 ("distribuidor", Decimal("20")),
                 ("exportador", Decimal("30")))
DIAS_CIERRE = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")
TIPOS_CEPA = {"tinta", "blanca"}
TIPOS_VINO = {"tinto", "blanco", "rosado", "espumante"}
TABLAS_A_CARGAR = (
    "localidad", "cepa", "maridaje", "bodega", "tipo_cliente", "sala_venta", "empleado"
)


def _csv(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"No existe el catálogo: {path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(columns):
            raise ValueError(f"{path.name}: columnas esperadas {list(columns)}, "
                             f"encontradas {reader.fieldnames}")
        rows = []
        for line, r in enumerate(reader, start=2):
            if None in r or not all(r.get(c) is not None and str(r[c]).strip() for c in columns):
                raise ValueError(f"{path.name}:{line}: fila incompleta o mal formada")
            rows.append({c: r[c].strip() for c in columns})
    if not rows:
        raise ValueError(f"{path.name} está vacío")
    return rows


def _unique(rows: list[dict[str, str]], key: str, filename: str) -> None:
    values = [r[key].casefold() for r in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"{filename}: contiene {key} duplicados")


def _load_data(config: Any) -> dict[str, Any]:
    folder = Path(config.catalogs_dir)
    localidades = _csv(folder / "localidades_mendoza.csv", ("cod_postal", "nombre", "provincia"))
    cepas = _csv(folder / "cepas.csv", ("nombre", "tipo"))
    maridajes_raw = _csv(folder / "maridajes.csv", ("nombre", "temperatura_servicio_c"))
    departamentos = _csv(folder / "departamentos_mendoza.csv", ("nombre", "provincia"))
    tipos_vino = _csv(folder / "tipos_vino.csv", ("nombre",))

    for rows, key, filename in (
        (localidades, "nombre", "localidades_mendoza.csv"),
        (cepas, "nombre", "cepas.csv"),
        (maridajes_raw, "nombre", "maridajes.csv"),
        (departamentos, "nombre", "departamentos_mendoza.csv"),
        (tipos_vino, "nombre", "tipos_vino.csv"),
    ):
        _unique(rows, key, filename)
    if any(r["tipo"] not in TIPOS_CEPA for r in cepas):
        raise ValueError("cepas.csv: 'tipo' debe ser tinta o blanca")
    if {r["nombre"] for r in tipos_vino} != TIPOS_VINO:
        raise ValueError("tipos_vino.csv debe reproducir el ENUM tipo_vino completo")
    if len(departamentos) != 18 or any(r["provincia"] != "Mendoza" for r in departamentos):
        raise ValueError("departamentos_mendoza.csv debe contener los 18 departamentos mendocinos")
    if any(r["provincia"] != "Mendoza" or len(r["cod_postal"]) > 12 for r in localidades):
        raise ValueError("localidades_mendoza.csv contiene provincia o código postal inválidos")

    maridajes: list[tuple[str, Decimal]] = []
    for r in maridajes_raw:
        try:
            temp = Decimal(r["temperatura_servicio_c"])
        except InvalidOperation as exc:
            raise ValueError(f"Temperatura inválida para {r['nombre']}") from exc
        if not temp.is_finite() or temp.as_tuple().exponent < -1 or temp < 0 or temp > 30:
            raise ValueError(f"Temperatura fuera de rango o precisión para {r['nombre']}")
        maridajes.append((r["nombre"], temp))

    profile = config.profile
    if profile not in {"small", "full"}:
        raise ValueError("Perfil inválido: elegir small o full")
    # En small se incluyen variedades blancas y tintas para no bloquear Producción.
    if profile == "small":
        tintas = [r for r in cepas if r["tipo"] == "tinta"][:6]
        blancas = [r for r in cepas if r["tipo"] == "blanca"][:6]
        cepas = tintas + blancas
        localidades = localidades[:10]
        maridajes = maridajes[:10]
    return {"localidades": localidades, "cepas": cepas,
            "maridajes": maridajes, "departamentos": [r["nombre"] for r in departamentos],
            "tipos_vino": [r["nombre"] for r in tipos_vino]}


def _cuit(prefix: str, number: int) -> str:
    """CUIT sintético con verificador aritmético, sin atribuir identidad real."""
    base = f"{prefix}{number:08d}"
    weights = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    digit = (11 - sum(int(c) * w for c, w in zip(base, weights)) % 11) % 11
    if digit == 10:
        raise ValueError("Número de CUIT sintético no admite dígito verificador")
    return base + str(digit)


def _synthetic_cuits(prefix: str, count: int) -> list[str]:
    """Produce `count` claves consecutivas válidas, omitiendo verificador imposible."""
    values: list[str] = []
    number = 99_900_000
    while len(values) < count:
        try:
            values.append(_cuit(prefix, number))
        except ValueError:
            pass
        number += 1
    return values


def _insert_returning(cur: Any, sql: str, params: tuple[Any, ...]) -> Any:
    cur.execute(sql, params)
    result = cur.fetchone()
    if not result:
        raise RuntimeError("INSERT RETURNING no devolvió la clave")
    return result[0]


def seed(conn: Any, rng: Any, faker: Any, config: Any, refs: dict[str, Any]) -> dict[str, int]:
    """Carga en una transacción manejada EXCLUSIVAMENTE por run_seed.py.

    Publica referencias solo al finalizar correctamente la etapa completa.
    Requiere esquema 001–007 aplicado y destino vacío/no incremental.
    """
    data = _load_data(config)  # Validación completa antes de empezar a insertar.
    sala_count = int(config.counts["sala_venta"])
    empleado_count = int(config.counts["empleado"])
    bodega_count = 5 if config.profile == "small" else 30
    if sala_count <= 0 or empleado_count <= 0 or bodega_count <= 0:
        raise ValueError("El perfil requiere al menos una sala, empleado y bodega")
    if config.end_date < config.start_date:
        raise ValueError("Rango histórico inválido en config")

    localidad_ids: list[int] = []
    localidad_map: dict[str, int] = {}
    cepa_ids: list[int] = []
    cepa_map: dict[str, int] = {}
    cepa_tipos: dict[str, str] = {}
    maridaje_ids: list[int] = []
    maridaje_map: dict[str, int] = {}
    bodegas: list[str] = []
    sala_ids: list[int] = []
    empleado_cuits: list[str] = []
    counts: dict[str, int] = {}

    with conn.cursor() as cur:
        # Salvaguarda: no alterar silenciosamente datos de cargas anteriores.
        for table in TABLAS_A_CARGAR:
            cur.execute(f"SELECT COUNT(*) FROM public.{table}")
            if cur.fetchone()[0] != 0:
                raise ValueError(f"La tabla {table} no está vacía: usar una base de prueba nueva")

        # 1) Catálogos independientes: IDs leídos con RETURNING.
        for item in data["localidades"]:
            ident = _insert_returning(
                cur,
                "INSERT INTO public.localidad "
                "(cod_postal, nombre, provincia, encargado_regional) "
                "VALUES (%s,%s,%s,%s) RETURNING id_localidad",
                (item["cod_postal"], item["nombre"], item["provincia"], faker.name()[:120]),
            )
            localidad_ids.append(ident)
            localidad_map[item["nombre"]] = ident
        counts["localidad"] = len(localidad_ids)

        for item in data["cepas"]:
            ident = _insert_returning(
                cur, "INSERT INTO public.cepa (nombre, tipo) VALUES (%s,%s) RETURNING id_cepa",
                (item["nombre"], item["tipo"]),
            )
            cepa_ids.append(ident)
            cepa_map[item["nombre"]] = ident
            cepa_tipos[item["nombre"]] = item["tipo"]
        counts["cepa"] = len(cepa_ids)

        for name, temp in data["maridajes"]:
            ident = _insert_returning(
                cur, "INSERT INTO public.maridaje (nombre, temperatura_servicio_c) "
                     "VALUES (%s,%s) RETURNING id_maridaje",
                (name, temp),
            )
            maridaje_ids.append(ident)
            maridaje_map[name] = ident
        counts["maridaje"] = len(maridaje_ids)

        # Bodegas ficticias con CUIT de 11 dígitos y verificador calculado.
        for i, cuit in enumerate(_synthetic_cuits("30", bodega_count)):
            _insert_returning(
                cur, "INSERT INTO public.bodega (cuit, razon_social, domicilio) "
                     "VALUES (%s,%s,%s) RETURNING cuit",
                (cuit, f"Bodega DEMO Atuel {i+1:03d}",
                 f"Domicilio ficticio {i+1}, Mendoza"),
            )
            bodegas.append(cuit)
        counts["bodega"] = len(bodegas)

        for tipo, descuento in TIPOS_CLIENTE:
            _insert_returning(
                cur, "INSERT INTO public.tipo_cliente (tipo_cliente, descuento) "
                     "VALUES (%s,%s) RETURNING tipo_cliente",
                (tipo, descuento),
            )
        counts["tipo_cliente"] = len(TIPOS_CLIENTE)

        # 2) Maestros dependientes: primero salas, después empleados.
        for i in range(sala_count):
            sala_ids.append(_insert_returning(
                cur, "INSERT INTO public.sala_venta (calle, numero, dia_cierre, id_localidad) "
                     "VALUES (%s,%s,%s,%s) RETURNING id_sala",
                (faker.street_name()[:120], str(100+i),
                 DIAS_CIERRE[i % len(DIAS_CIERRE)],
                 localidad_ids[i % len(localidad_ids)]),
            ))
        counts["sala_venta"] = len(sala_ids)

        span = (config.end_date - config.start_date).days
        for i, cuit in enumerate(_synthetic_cuits("20", empleado_count)):
            fecha = config.start_date + timedelta(days=rng.randint(0, span))
            empleado_cuits.append(str(_insert_returning(
                cur, "INSERT INTO public.empleado "
                     "(cuit, nombre, fecha_ingreso, salario, id_sala) "
                     "VALUES (%s,%s,%s,%s,%s) RETURNING cuit",
                (cuit, faker.name()[:120], fecha,
                 Decimal(rng.randrange(400_000, 1_800_001)),
                 sala_ids[i % len(sala_ids)]),
            )).strip())
        counts["empleado"] = len(empleado_cuits)

    # Nombres a coordinar con B/C/D; mantenemos listas y diccionarios explícitos.
    refs.update({
        "localidad_ids": localidad_ids,
        "localidad_ids_por_nombre": localidad_map,
        "cepa_ids": cepa_ids,
        "cepa_ids_por_nombre": cepa_map,
        "cepa_tipos_por_nombre": cepa_tipos,
        "maridaje_ids": maridaje_ids,
        "maridaje_ids_por_nombre": maridaje_map,
        "bodega_cuits": bodegas,
        "tipo_cliente_values": [item[0] for item in TIPOS_CLIENTE],
        "tipo_cliente_descuentos": {tipo: descuento for tipo, descuento in TIPOS_CLIENTE},
        "sala_ids": sala_ids,
        "empleado_cuits": empleado_cuits,
        "departamentos_mendoza": data["departamentos"],
        "tipos_vino": data["tipos_vino"],
    })
    return counts
