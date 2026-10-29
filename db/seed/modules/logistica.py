"""Fase 3 / Rol C: logística, ingresos, transferencias y existencias.

Interfaz acordada con run_seed.py:
    seed(conn, rng, faker, config, refs)

Responsabilidades:
- crear transportistas y su cobertura por localidades;
- crear ingresos y renglones;
- terminar y procesar ingresos con sp_procesar_ingreso;
- crear transferencias y renglones;
- terminar y procesar transferencias con sp_procesar_transferencia;
- dejar stock_deposito y stock_sala como resultado de los procedimientos.

No abre conexiones, no crea tablas y no ejecuta commit() ni rollback().
No modifica stock manualmente.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any, Iterable, Sequence


TABLAS_A_CARGAR = (
    "transportista",
    "transportista_localidad",
    "ingreso",
    "renglon_ingreso",
    "transferencia",
    "renglon_transferencia",
    "stock_deposito",
    "stock_sala",
)


def _require_list(refs: dict[str, Any], key: str) -> list[Any]:
    value = refs.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(
            f"logistica.py requiere refs[{key!r}] como lista no vacia. "
            "Verificar el modulo anterior y el contrato compartido."
        )
    return value


def _distribuir_renglones(cabeceras: int, renglones: int) -> list[int]:
    """Distribuye exactamente N renglones, con al menos uno por cabecera."""
    if cabeceras <= 0:
        raise ValueError("La cantidad de cabeceras debe ser positiva")
    if renglones < cabeceras:
        raise ValueError(
            f"Se requieren al menos {cabeceras} renglones para {cabeceras} documentos; "
            f"config solicita {renglones}"
        )
    base, resto = divmod(renglones, cabeceras)
    return [base + (1 if i < resto else 0) for i in range(cabeceras)]


def _asignar_vinos(
    cantidades_por_documento: Sequence[int],
    vino_ids: Sequence[int],
    rng: Any,
) -> list[list[int]]:
    """Asigna vinos sin repetir dentro de un mismo documento.

    Si hay suficientes renglones globales, intenta dar cobertura al mayor numero
    posible de vinos antes de reutilizarlos.
    """
    vinos = list(dict.fromkeys(int(v) for v in vino_ids))
    if not vinos:
        raise ValueError("No hay vinos disponibles para Logistica")

    max_renglones = max(cantidades_por_documento, default=0)
    if max_renglones > len(vinos):
        raise ValueError(
            f"Un documento requiere {max_renglones} vinos distintos, "
            f"pero solo hay {len(vinos)} vinos disponibles"
        )

    cobertura = vinos.copy()
    rng.shuffle(cobertura)
    pos = 0
    resultado: list[list[int]] = []

    for cantidad in cantidades_por_documento:
        elegidos: list[int] = []

        while len(elegidos) < cantidad and pos < len(cobertura):
            vino = cobertura[pos]
            pos += 1
            if vino not in elegidos:
                elegidos.append(vino)

        if len(elegidos) < cantidad:
            candidatos = [vino for vino in vinos if vino not in elegidos]
            elegidos.extend(rng.sample(candidatos, cantidad - len(elegidos)))

        resultado.append(elegidos)

    return resultado


def _planificar_ingresos_por_bodega(
    cantidades_por_documento: Sequence[int],
    vino_info: Sequence[tuple[int, str, int]],
    rng: Any,
) -> list[tuple[str, list[int]]]:
    """Elige para cada ingreso una bodega y vinos elaborados por esa bodega.

    `vino_info` contiene (cod_vino, cuit_bodega, anada). Los vinos no se
    repiten dentro de un mismo ingreso, respetando la PK
    (cod_ingreso, cod_vino).
    """
    por_bodega: dict[str, list[int]] = {}
    for cod_vino, cuit_bodega, _ in vino_info:
        por_bodega.setdefault(str(cuit_bodega).strip(), []).append(int(cod_vino))

    max_renglones = max(cantidades_por_documento, default=0)
    elegibles = sorted(
        cuit
        for cuit, vinos in por_bodega.items()
        if len(set(vinos)) >= max_renglones
    )
    if not elegibles:
        raise ValueError(
            "No hay ninguna bodega con suficientes vinos distintos para "
            f"armar un ingreso de {max_renglones} renglones"
        )

    rng.shuffle(elegibles)
    resultado: list[tuple[str, list[int]]] = []

    for i, cantidad in enumerate(cantidades_por_documento):
        cuit_bodega = elegibles[i % len(elegibles)]
        candidatos = list(dict.fromkeys(por_bodega[cuit_bodega]))
        elegidos = rng.sample(candidatos, cantidad)
        resultado.append((cuit_bodega, elegidos))

    return resultado


def _cuit(prefix: str, number: int) -> str:
    """CUIT sintetico de 11 digitos con digito verificador aritmetico."""
    base = f"{prefix}{number:08d}"
    if len(base) != 10 or not base.isdigit():
        raise ValueError("Base de CUIT invalida")
    weights = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    digit = (11 - sum(int(c) * w for c, w in zip(base, weights)) % 11) % 11
    if digit == 10:
        raise ValueError("Numero sintetico sin digito verificador utilizable")
    return base + str(digit)


def _synthetic_cuits(prefix: str, count: int) -> list[str]:
    values: list[str] = []
    number = 88_800_000
    while len(values) < count:
        try:
            values.append(_cuit(prefix, number))
        except ValueError:
            pass
        number += 1
    return values


def _insert_returning(cur: Any, sql: str, params: tuple[Any, ...]) -> Any:
    cur.execute(sql, params)
    row = cur.fetchone()
    if not row:
        raise RuntimeError("INSERT RETURNING no devolvio la clave esperada")
    return row[0]


def _executemany_batches(
    cur: Any,
    sql: str,
    rows: Sequence[tuple[Any, ...]],
    batch_size: int,
) -> None:
    if batch_size <= 0:
        raise ValueError("batch_size debe ser positivo")
    for start in range(0, len(rows), batch_size):
        cur.executemany(sql, rows[start:start + batch_size])


def _random_date(rng: Any, start_date: Any, end_date: Any) -> Any:
    span = (end_date - start_date).days
    if span < 0:
        raise ValueError("Rango historico invalido")
    return start_date + timedelta(days=rng.randint(0, span))


def _split_budget(budget: int, parts: int, rng: Any) -> list[int]:
    """Divide un presupuesto entero en partes positivas cuya suma es exacta."""
    if parts <= 0:
        raise ValueError("parts debe ser positivo")
    if budget < parts:
        raise ValueError(f"Presupuesto {budget} insuficiente para {parts} partes positivas")

    base, resto = divmod(budget, parts)
    values = [base + (1 if i < resto else 0) for i in range(parts)]
    rng.shuffle(values)
    return values


def seed(
    conn: Any,
    rng: Any,
    faker: Any,
    config: Any,
    refs: dict[str, Any],
) -> dict[str, int]:
    """Carga completa de Logistica dentro de la transaccion del runner."""

    # Referencias publicadas por catalogos.py.
    localidad_ids = [int(x) for x in _require_list(refs, "localidad_ids")]
    bodega_cuits = [str(x).strip() for x in _require_list(refs, "bodega_cuits")]
    sala_ids = [int(x) for x in _require_list(refs, "sala_ids")]

    # Contrato con produccion.py. Si todavia no fue integrado, el error es
    # intencional y explicito en vez de asumir IDs.
    vino_ids = [int(x) for x in _require_list(refs, "vino_ids")]

    ingreso_count = int(config.counts["ingreso"])
    renglon_ingreso_count = int(config.counts["renglon_ingreso"])
    transferencia_count = int(config.counts["transferencia"])
    renglon_transferencia_count = int(config.counts["renglon_transferencia"])

    if config.profile not in {"small", "full"}:
        raise ValueError("Perfil invalido: elegir small o full")
    if config.end_date < config.start_date:
        raise ValueError("Rango historico invalido en config")

    lineas_ingreso = _distribuir_renglones(ingreso_count, renglon_ingreso_count)
    lineas_transferencia = _distribuir_renglones(
        transferencia_count, renglon_transferencia_count
    )

    # La asignacion de ingresos se arma dentro de la transaccion luego de
    # consultar la bodega y anada reales de los vinos publicados por Produccion.

    # Volumen suficiente para abastecer transferencias y, luego, ventas.
    if config.profile == "small":
        ingreso_min, ingreso_max = 500, 2_000
        transportista_count = 5
        cobertura_extra_max = 3
    else:
        ingreso_min, ingreso_max = 8_000, 20_000
        transportista_count = 30
        cobertura_extra_max = 6

    batch_size = int(config.batch_size)
    counts: dict[str, int] = {}

    transportista_ids: list[int] = []
    ingreso_ids: list[int] = []
    transferencia_ids: list[int] = []

    with conn.cursor() as cur:
        # Carga no incremental: nuestras tablas deben comenzar vacias.
        for table in TABLAS_A_CARGAR:
            cur.execute(f"SELECT COUNT(*) FROM public.{table}")
            cantidad = int(cur.fetchone()[0])
            if cantidad != 0:
                raise ValueError(
                    f"La tabla {table} no esta vacia ({cantidad} filas): "
                    "usar una base descartable nueva"
                )

        # Metadatos reales de los vinos publicados por Produccion. No se agregan
        # nuevas refs: Logistica resuelve aqui la bodega y anada desde la BD.
        vino_id_set = set(vino_ids)
        cur.execute(
            "SELECT cod_vino, cuit_bodega, anada "
            "FROM public.vino ORDER BY cod_vino"
        )
        vino_info = [
            (int(cod_vino), str(cuit_bodega).strip(), int(anada))
            for cod_vino, cuit_bodega, anada in cur.fetchall()
            if int(cod_vino) in vino_id_set
        ]
        encontrados = {cod_vino for cod_vino, _, _ in vino_info}
        faltantes = sorted(vino_id_set - encontrados)
        if faltantes:
            raise ValueError(
                "refs['vino_ids'] contiene vinos inexistentes en public.vino: "
                f"{faltantes[:10]}"
            )

        bodegas_validas = set(bodega_cuits)
        bodegas_fuera_de_refs = sorted({
            cuit_bodega
            for _, cuit_bodega, _ in vino_info
            if cuit_bodega not in bodegas_validas
        })
        if bodegas_fuera_de_refs:
            raise ValueError(
                "Hay vinos cuya bodega no fue publicada por Catalogos: "
                f"{bodegas_fuera_de_refs[:10]}"
            )

        vino_anada = {
            cod_vino: anada
            for cod_vino, _, anada in vino_info
        }
        plan_ingresos = _planificar_ingresos_por_bodega(
            lineas_ingreso, vino_info, rng
        )

        # ------------------------------------------------------------------
        # 1) Transportistas y cobertura.
        # ------------------------------------------------------------------
        for i, cuit in enumerate(_synthetic_cuits("27", transportista_count), start=1):
            razon_social = f"Transportes DEMO Atuel {i:03d}"
            email = f"logistica{i:03d}@demo-atuel.invalid"
            telefono = str(faker.phone_number())[:30]
            domicilio = str(faker.address()).replace("\n", ", ")[:200]

            cod_transporte = int(_insert_returning(
                cur,
                "INSERT INTO public.transportista "
                "(razon_social, cuit, email, telefono, domicilio) "
                "VALUES (%s,%s,%s,%s,%s) RETURNING cod_transporte",
                (razon_social, cuit, email, telefono, domicilio),
            ))
            transportista_ids.append(cod_transporte)

        cobertura: set[tuple[int, int]] = set()

        # Cada transportista cubre al menos una localidad.
        for i, cod_transporte in enumerate(transportista_ids):
            cobertura.add((cod_transporte, localidad_ids[i % len(localidad_ids)]))

        # Cada localidad queda cubierta por al menos un transportista.
        for i, id_localidad in enumerate(localidad_ids):
            cobertura.add((transportista_ids[i % len(transportista_ids)], id_localidad))

        # Coberturas adicionales reproducibles.
        extra_max = min(cobertura_extra_max, len(localidad_ids))
        for cod_transporte in transportista_ids:
            extra = rng.randint(1, extra_max)
            for id_localidad in rng.sample(localidad_ids, extra):
                cobertura.add((cod_transporte, id_localidad))

        cobertura_rows = sorted(cobertura)
        _executemany_batches(
            cur,
            "INSERT INTO public.transportista_localidad "
            "(cod_transporte, id_localidad) VALUES (%s,%s)",
            cobertura_rows,
            batch_size,
        )

        counts["transportista"] = len(transportista_ids)
        counts["transportista_localidad"] = len(cobertura_rows)

        # ------------------------------------------------------------------
        # 2) Ingresos en confeccion.
        # ------------------------------------------------------------------
        transportistas_orden = transportista_ids.copy()
        rng.shuffle(transportistas_orden)

        ingreso_vinos: list[list[int]] = []
        for i, (cuit_bodega, vinos) in enumerate(plan_ingresos):
            # Un vino de anada Y no se ingresa antes de terminar la epoca de
            # cosecha de esa anada. Mayo es una cota conservadora y mantiene
            # los ingresos dentro del periodo historico configurado.
            anada_max = max(vino_anada[cod_vino] for cod_vino in vinos)
            fecha_minima = max(config.start_date, date(anada_max, 5, 1))
            if fecha_minima > config.end_date:
                raise ValueError(
                    f"No hay fecha historica valida para ingresar vinos de anada {anada_max}"
                )
            fecha = _random_date(rng, fecha_minima, config.end_date)
            cod_transporte = transportistas_orden[i % len(transportistas_orden)]

            cod_ingreso = int(_insert_returning(
                cur,
                "INSERT INTO public.ingreso "
                "(fecha, estado, cod_transporte, cuit_bodega) "
                "VALUES (%s, 'en_confeccion', %s, %s) "
                "RETURNING cod_ingreso",
                (fecha, cod_transporte, cuit_bodega),
            ))
            ingreso_ids.append(cod_ingreso)
            ingreso_vinos.append(vinos)

        ingreso_rows: list[tuple[int, int, int]] = []
        for cod_ingreso, vinos in zip(ingreso_ids, ingreso_vinos):
            for cod_vino in vinos:
                cantidad = rng.randint(ingreso_min, ingreso_max)
                ingreso_rows.append((cod_ingreso, cod_vino, cantidad))

        if len(ingreso_rows) != renglon_ingreso_count:
            raise RuntimeError(
                f"Se planificaron {len(ingreso_rows)} renglones de ingreso; "
                f"se esperaban {renglon_ingreso_count}"
            )

        _executemany_batches(
            cur,
            "INSERT INTO public.renglon_ingreso "
            "(cod_ingreso, cod_vino, cantidad) VALUES (%s,%s,%s)",
            ingreso_rows,
            batch_size,
        )

        # RN-10: en_confeccion -> terminado -> procesado.
        _executemany_batches(
            cur,
            "UPDATE public.ingreso SET estado = 'terminado' "
            "WHERE cod_ingreso = %s",
            [(cod_ingreso,) for cod_ingreso in ingreso_ids],
            batch_size,
        )
        for cod_ingreso in ingreso_ids:
            cur.execute("CALL public.sp_procesar_ingreso(%s)", (cod_ingreso,))

        counts["ingreso"] = len(ingreso_ids)
        counts["renglon_ingreso"] = len(ingreso_rows)

        # Stock creado exclusivamente por sp_procesar_ingreso.
        cur.execute(
            "SELECT cod_vino, cantidad "
            "FROM public.stock_deposito "
            "WHERE cantidad > 0 ORDER BY cod_vino"
        )
        deposito_rows = [(int(vino), int(cantidad)) for vino, cantidad in cur.fetchall()]
        if not deposito_rows:
            raise RuntimeError("Los ingresos procesados no generaron stock_deposito")

        stock_inicial = dict(deposito_rows)
        vinos_con_stock = list(stock_inicial)

        # ------------------------------------------------------------------
        # 3) Plan de transferencias.
        # ------------------------------------------------------------------
        asignacion_transferencias = _asignar_vinos(
            lineas_transferencia, vinos_con_stock, rng
        )
        apariciones = Counter(
            cod_vino
            for documento in asignacion_transferencias
            for cod_vino in documento
        )

        # Se transfiere el 80 % del stock de cada vino utilizado. El 20 %
        # restante queda disponible en el deposito central.
        cantidades_por_vino: dict[int, list[int]] = {}
        for cod_vino, veces in apariciones.items():
            disponible = stock_inicial[cod_vino]
            presupuesto = (disponible * 80) // 100
            if presupuesto < veces:
                raise RuntimeError(
                    f"Stock de vino {cod_vino} insuficiente para planificar "
                    f"{veces} renglones de transferencia"
                )
            cantidades_por_vino[cod_vino] = _split_budget(
                presupuesto, veces, rng
            )

        # Consumimos las cantidades de cada vino de forma determinista.
        posicion_cantidad = {cod_vino: 0 for cod_vino in cantidades_por_vino}

        salas_orden = sala_ids.copy()
        rng.shuffle(salas_orden)

        for i in range(transferencia_count):
            id_sala = salas_orden[i % len(salas_orden)]

            # fecha_confeccion y estado usan sus DEFAULT; RN-11 fuerza la
            # fecha actual mediante trigger.
            nro_solicitud = int(_insert_returning(
                cur,
                "INSERT INTO public.transferencia (id_sala) "
                "VALUES (%s) RETURNING nro_solicitud",
                (id_sala,),
            ))
            transferencia_ids.append(nro_solicitud)

        transferencia_rows: list[tuple[int, int, int]] = []
        for nro_solicitud, vinos in zip(
            transferencia_ids, asignacion_transferencias
        ):
            for cod_vino in vinos:
                pos = posicion_cantidad[cod_vino]
                cantidad = cantidades_por_vino[cod_vino][pos]
                posicion_cantidad[cod_vino] = pos + 1
                transferencia_rows.append(
                    (nro_solicitud, cod_vino, cantidad)
                )

        if len(transferencia_rows) != renglon_transferencia_count:
            raise RuntimeError(
                f"Se planificaron {len(transferencia_rows)} renglones de transferencia; "
                f"se esperaban {renglon_transferencia_count}"
            )

        _executemany_batches(
            cur,
            "INSERT INTO public.renglon_transferencia "
            "(nro_solicitud, cod_vino, cantidad) VALUES (%s,%s,%s)",
            transferencia_rows,
            batch_size,
        )

        # RN-11: en_confeccion -> terminado -> procesado.
        _executemany_batches(
            cur,
            "UPDATE public.transferencia SET estado = 'terminado' "
            "WHERE nro_solicitud = %s",
            [(nro,) for nro in transferencia_ids],
            batch_size,
        )
        for nro_solicitud in transferencia_ids:
            cur.execute(
                "CALL public.sp_procesar_transferencia(%s)",
                (nro_solicitud,),
            )

        counts["transferencia"] = len(transferencia_ids)
        counts["renglon_transferencia"] = len(transferencia_rows)

        # ------------------------------------------------------------------
        # 4) Controles internos del modulo.
        # ------------------------------------------------------------------
        # Coherencia semantica: cada vino del ingreso debe pertenecer a la
        # bodega de la cabecera y el ingreso no puede preceder la ventana
        # historica adoptada para la anada de ese vino.
        cur.execute(
            "SELECT COUNT(*) "
            "FROM public.ingreso i "
            "JOIN public.renglon_ingreso ri "
            "  ON ri.cod_ingreso = i.cod_ingreso "
            "JOIN public.vino v "
            "  ON v.cod_vino = ri.cod_vino "
            "WHERE i.cuit_bodega <> v.cuit_bodega "
            "   OR i.fecha < make_date(v.anada, 5, 1)"
        )
        ingresos_incoherentes = int(cur.fetchone()[0])
        if ingresos_incoherentes:
            raise RuntimeError(
                "Se detectaron renglones de ingreso incompatibles con la "
                f"bodega/anada del vino: {ingresos_incoherentes}"
            )

        cur.execute(
            "SELECT COUNT(*) FROM public.ingreso "
            "WHERE estado <> 'procesado'"
        )
        ingresos_no_procesados = int(cur.fetchone()[0])

        cur.execute(
            "SELECT COUNT(*) FROM public.transferencia "
            "WHERE estado <> 'procesado'"
        )
        transferencias_no_procesadas = int(cur.fetchone()[0])

        if ingresos_no_procesados or transferencias_no_procesadas:
            raise RuntimeError(
                "Quedaron documentos sin procesar: "
                f"ingresos={ingresos_no_procesados}, "
                f"transferencias={transferencias_no_procesadas}"
            )

        cur.execute(
            "SELECT "
            "(SELECT COUNT(*) FROM public.stock_deposito WHERE cantidad < 0), "
            "(SELECT COUNT(*) FROM public.stock_sala WHERE cantidad < 0)"
        )
        neg_deposito, neg_sala = (int(x) for x in cur.fetchone())
        if neg_deposito or neg_sala:
            raise RuntimeError(
                f"Stock negativo detectado: deposito={neg_deposito}, sala={neg_sala}"
            )

        # Antes de ventas debe conservarse la cantidad total ingresada:
        # deposito + salas = suma de renglones de ingreso.
        cur.execute(
            "SELECT COALESCE(SUM(cantidad), 0) FROM public.renglon_ingreso"
        )
        total_ingresado = int(cur.fetchone()[0])

        cur.execute(
            "SELECT "
            "COALESCE((SELECT SUM(cantidad) FROM public.stock_deposito), 0) + "
            "COALESCE((SELECT SUM(cantidad) FROM public.stock_sala), 0)"
        )
        total_existencia = int(cur.fetchone()[0])

        if total_ingresado != total_existencia:
            raise RuntimeError(
                "Conservacion de stock invalida antes de ventas: "
                f"ingresado={total_ingresado}, existencia={total_existencia}"
            )

        cur.execute(
            "SELECT cod_vino, cantidad "
            "FROM public.stock_deposito ORDER BY cod_vino"
        )
        stock_deposito_por_vino = {
            int(cod_vino): int(cantidad)
            for cod_vino, cantidad in cur.fetchall()
        }

        cur.execute(
            "SELECT id_sala, cod_vino, cantidad "
            "FROM public.stock_sala "
            "WHERE cantidad > 0 "
            "ORDER BY id_sala, cod_vino"
        )
        stock_sala_rows = [
            (int(id_sala), int(cod_vino), int(cantidad))
            for id_sala, cod_vino, cantidad in cur.fetchall()
        ]
        stock_sala_por_clave = {
            (id_sala, cod_vino): cantidad
            for id_sala, cod_vino, cantidad in stock_sala_rows
        }

        counts["stock_deposito"] = len(stock_deposito_por_vino)
        counts["stock_sala"] = len(stock_sala_rows)

    # Publicar refs solo al terminar correctamente todo el modulo.
    refs.update({
        "transportista_ids": transportista_ids,
        "ingreso_ids": ingreso_ids,
        "transferencia_ids": transferencia_ids,
        "stock_deposito_por_vino": stock_deposito_por_vino,
        "stock_sala_por_clave": stock_sala_por_clave,
    })

    return counts
