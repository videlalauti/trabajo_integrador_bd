"""Fase 3 / Rol D: clientes, permisos, comprobantes y renglones.

Contrato unico: seed(conn, rng, faker, config, refs).
La conexion y la transaccion pertenecen a run_seed.py; este modulo no hace
commit/rollback, no abre conexiones y no altera tablas, triggers ni funciones.

RN-06/08: la BD calcula descuentos y totales por medio de sus triggers.
RN-09: el trigger resta stock_sala; aqui se descuenta SOLO de una copia local
para planificar las ventas y evitar vender existencias inexistentes.
RN-11: comprobantes en la fecha operativa CURRENT_DATE de PostgreSQL, porque
las transferencias que abastecen las salas fueron fechadas ese mismo dia.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from time import perf_counter
from typing import Any, Iterable, Sequence


_TABLAS = ("cliente", "permiso_exportacion", "comprobante", "renglon_comprobante")
_TIPOS = ("socio", "distribuidor", "exportador")
_DESCUENTOS_BASE = {"socio": Decimal("10"), "distribuidor": Decimal("20"),
                    "exportador": Decimal("30")}
_COLUMNAS_CLIENTE = (
    "nombre_razon_social", "tipo_doc", "nro_doc", "direccion", "fecha_alta",
    "id_localidad", "tipo_cliente", "descuento_especial", "zona_cobertura",
    "nro_habilitacion", "pais_destino",
)


def _lista_ids(refs: dict[str, Any], clave: str) -> list[int]:
    valores = refs.get(clave)
    if not isinstance(valores, list) or not valores:
        raise ValueError(f"ventas: refs[{clave!r}] debe ser una lista no vacia")
    ids = [int(valor) for valor in valores]
    if len(ids) != len(set(ids)):
        raise ValueError(f"ventas: refs[{clave!r}] tiene IDs duplicados")
    return ids


def _validar_tipos(refs: dict[str, Any]) -> None:
    tipos = refs.get("tipo_cliente_values")
    descuentos = refs.get("tipo_cliente_descuentos")
    if not isinstance(tipos, list) or set(tipos) != set(_TIPOS):
        raise ValueError("ventas: se requieren los tipos socio, distribuidor y exportador")
    if not isinstance(descuentos, dict) or set(descuentos) != set(_TIPOS):
        raise ValueError("ventas: faltan descuentos de los tres tipos de cliente")
    for tipo in _TIPOS:
        if Decimal(str(descuentos[tipo])) != _DESCUENTOS_BASE[tipo]:
            raise ValueError(f"ventas: el descuento base de {tipo} difiere de RN-06")
    # Esta verificacion NO aplica descuentos: los calcula fn_descuento_cliente().


def _cuit(prefijo: str, numero: int) -> str | None:
    """CUIT sintetico de 11 digitos con digito verificador valido."""
    base = f"{prefijo}{numero:08d}"
    if len(base) != 10:
        raise ValueError("Numero fuera de rango para CUIT sintetico")
    pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    digito = (11 - sum(int(n) * p for n, p in zip(base, pesos)) % 11) % 11
    return None if digito == 10 else base + str(digito)


def _fecha_aleatoria(rng: Any, desde: date, hasta: date) -> date:
    if desde > hasta:
        raise ValueError(f"Rango de fechas invalido: {desde} > {hasta}")
    return desde + timedelta(days=rng.randrange((hasta - desde).days + 1))


def _insertar_lotes(
    cur: Any, tabla: str, columnas: Sequence[str], filas: Sequence[tuple],
    batch_size: int, returning: str | None = None,
) -> list[tuple]:
    """Insercion multi-VALUES parametrizada; RETURNING recupera PK reales.

    `tabla`, `columnas` y `returning` se pasan solo como constantes internas,
    nunca con entradas de usuario. Se limita el numero de parametros por SQL.
    """
    if batch_size <= 0:
        raise ValueError("batch_size debe ser positivo")
    limite = min(batch_size, 65535 // len(columnas))
    plantilla = "(" + ", ".join(["%s"] * len(columnas)) + ")"
    prefijo = f"INSERT INTO public.{tabla} ({', '.join(columnas)}) VALUES "
    sufijo = f" RETURNING {returning}" if returning else ""
    resultados: list[tuple] = []
    for inicio in range(0, len(filas), limite):
        lote = filas[inicio:inicio + limite]
        query = prefijo + ", ".join([plantilla] * len(lote)) + sufijo
        cur.execute(query, [valor for fila in lote for valor in fila])
        if returning:
            resultados.extend(cur.fetchall())
    return resultados


def _generar_clientes(
    rng: Any, faker: Any, cantidad: int, localidades: list[int],
    fecha_inicio: date, fecha_fin: date,
) -> tuple[list[tuple], list[tuple[str, str, date]]]:
    """Devuelve filas y documentos/altas de los exportadores en orden."""
    filas: list[tuple] = []
    exportadores: list[tuple[str, str, date]] = []
    siguiente_cuit = 44_000_000
    paises = ("Chile", "Brasil", "Uruguay", "Estados Unidos", "Mexico", "España")
    especiales = (Decimal("5.00"), Decimal("12.50"), Decimal("22.50"),
                  Decimal("35.00"))
    for indice in range(cantidad):
        tipo = _TIPOS[indice % len(_TIPOS)]
        if tipo == "socio":
            tipo_doc, nro_doc = "DNI", str(30_000_000 + indice)
            nombre = faker.name()[:150]
        else:
            tipo_doc = "CUIT"
            while True:
                nro_doc = _cuit("30", siguiente_cuit)
                siguiente_cuit += 1
                if nro_doc is not None:
                    break
            nombre = faker.company()[:150]
        zona = faker.city()[:150] if tipo == "distribuidor" else None
        habilitacion = f"HAB-ATUEL-{indice + 1:08d}" if tipo == "distribuidor" else None
        pais = rng.choice(paises) if tipo == "exportador" else None
        especial = rng.choice(especiales) if rng.randrange(10) == 0 else None
        fila = (
            nombre, tipo_doc, nro_doc, faker.street_address()[:200],
            _fecha_aleatoria(rng, fecha_inicio, fecha_fin), rng.choice(localidades),
            tipo, especial, zona, habilitacion, pais,
        )
        filas.append(fila)
        if tipo == "exportador":
            exportadores.append((tipo_doc, nro_doc, fila[4]))
    return filas, exportadores


def _generar_permisos(
    rng: Any, clientes_exportadores: list[tuple[int, date]],
    fecha_fin: date, fecha_operativa: date,
) -> list[tuple]:
    """Cada exportador recibe de 1 a 3 permisos; el principal sigue vigente."""
    filas: list[tuple] = []
    inicio_reciente = fecha_fin - timedelta(days=240)
    for posicion, (cliente_id, fecha_alta) in enumerate(clientes_exportadores, start=1):
        cantidad = rng.randint(1, 3)
        for orden in range(1, cantidad + 1):
            if orden == 1:
                emision = _fecha_aleatoria(rng, max(fecha_alta, inicio_reciente), fecha_fin)
                vencimiento = max(emision + timedelta(days=730),
                                  fecha_operativa + timedelta(days=30))
            else:
                emision = _fecha_aleatoria(rng, fecha_alta, fecha_fin)
                vencimiento = emision + timedelta(days=rng.randint(365, 1095))
            filas.append((f"EXP-ATUEL-{posicion:08d}-{orden}", cliente_id,
                          emision, vencimiento))
    return filas


def _planificar_ventas(
    rng: Any, objetivo_comprobantes: int, objetivo_renglones: int,
    stock_original: dict[tuple[int, int], int],
) -> tuple[list[tuple[int, list[tuple[int, int]]]], dict[tuple[int, int], int]]:
    """Plan cerrado sin SQL; conserva PK compuesta y stock no negativo.

    Se usa copia local. Cada comprobante tiene al menos un vino, y cada vino
    aparece una sola vez dentro de ese documento. Cantidad por renglon: 1 a 3
    botellas, limitada al saldo de la pareja (sala, vino).
    """
    if objetivo_comprobantes <= 0 or objetivo_renglones < objetivo_comprobantes:
        raise ValueError("Cada comprobante debe tener al menos un renglon")
    disponibles = dict(stock_original)
    por_sala: dict[int, list[int]] = defaultdict(list)
    for (sala, vino), cantidad in sorted(disponibles.items()):
        if cantidad > 0:
            por_sala[sala].append(vino)
    salas = sorted(por_sala)
    if not salas:
        raise ValueError("ventas: no hay stock_sala positivo para generar ventas")
    if sum(disponibles.values()) < objetivo_renglones:
        raise ValueError("ventas: stock total inferior a los renglones requeridos")
    maximo_renglones = (objetivo_renglones + objetivo_comprobantes - 1) // objetivo_comprobantes
    if maximo_renglones > max(map(len, por_sala.values())):
        raise ValueError("ventas: ninguna sala tiene suficientes vinos distintos por comprobante")

    # Renglones repartidos exactamente, independientemente de la aleatoriedad.
    base, resto = divmod(objetivo_renglones, objetivo_comprobantes)
    objetivos = [base + (1 if i < resto else 0) for i in range(objetivo_comprobantes)]
    plan: list[tuple[int, list[tuple[int, int]]]] = []
    for indice, cantidad_renglones in enumerate(objetivos):
        sala_elegida = None
        opciones: list[int] = []
        # Rotacion uniforme entre salas; buscar otra sala si la elegida agota
        # sus combinaciones. No se inventan pares (sala, vino) inexistentes.
        for intento in range(len(salas)):
            sala = salas[(indice + intento) % len(salas)]
            candidatas = [vino for vino in por_sala[sala]
                          if disponibles[(sala, vino)] > 0]
            if len(candidatas) >= cantidad_renglones:
                sala_elegida, opciones = sala, candidatas
                break
        if sala_elegida is None:
            raise ValueError(
                f"ventas: stock/combinaciones insuficientes en comprobante "
                f"{indice + 1}/{objetivo_comprobantes}; no se insertan ventas incompletas"
            )
        renglones: list[tuple[int, int]] = []
        for vino in rng.sample(opciones, cantidad_renglones):
            clave = (sala_elegida, vino)
            cantidad = min(rng.randint(1, 3), disponibles[clave])
            disponibles[clave] -= cantidad
            renglones.append((vino, cantidad))
        plan.append((sala_elegida, renglones))
    return plan, disponibles


def seed(conn: Any, rng: Any, faker: Any, config: Any,
         refs: dict[str, Any]) -> dict[str, int | float]:
    """Carga las cuatro tablas con triggers/FK activos y transaccion externa."""
    t0 = perf_counter()
    localidad_ids = _lista_ids(refs, "localidad_ids")
    sala_ids = _lista_ids(refs, "sala_ids")
    vino_ids = _lista_ids(refs, "vino_ids")
    _validar_tipos(refs)
    stock_refs = refs.get("stock_sala_por_clave")
    if not isinstance(stock_refs, dict) or not stock_refs:
        raise ValueError("ventas: refs['stock_sala_por_clave'] debe ser un dict no vacio")
    salas_validas, vinos_validos = set(sala_ids), set(vino_ids)
    stock_inicial: dict[tuple[int, int], int] = {}
    for clave, cantidad in stock_refs.items():
        if (not isinstance(clave, tuple) or len(clave) != 2
                or clave[0] not in salas_validas or clave[1] not in vinos_validos):
            raise ValueError(f"ventas: pareja de stock invalida: {clave!r}")
        if not isinstance(cantidad, int) or cantidad <= 0:
            raise ValueError(f"ventas: cantidad de stock invalida en {clave!r}")
        stock_inicial[clave] = cantidad

    n_clientes = int(config.counts["cliente"])
    n_comprobantes = int(config.counts["comprobante"])
    n_renglones = int(config.counts["renglon_comprobante"])
    batch_size = int(config.batch_size)
    if min(n_clientes, n_comprobantes, n_renglones, batch_size) <= 0:
        raise ValueError("ventas: counts y batch_size deben ser positivos")
    if config.start_date > config.end_date:
        raise ValueError("ventas: fechas historicas invalidas en config")

    # Cerrar el plan de stock ANTES de insertar la primera fila. Si no hay
    # existencias suficientes, se rechaza la carga sin generar ventas parciales.
    plan, saldos_previstos = _planificar_ventas(rng, n_comprobantes, n_renglones,
                                              stock_inicial)

    with conn.cursor() as cur:
        for tabla in _TABLAS:
            cur.execute(f"SELECT COUNT(*) FROM public.{tabla}")
            if int(cur.fetchone()[0]) != 0:
                raise ValueError(f"ventas: public.{tabla} no esta vacia; usar base nueva")
        cur.execute("SELECT CURRENT_DATE")
        fecha_operativa = cur.fetchone()[0]
        fin_altas = min(config.end_date, fecha_operativa)
        if config.start_date > fin_altas:
            raise ValueError("ventas: el periodo de alta comienza despues de CURRENT_DATE")

        # Asegurar que el snapshot publicado por Logistica corresponde a la BD.
        cur.execute("SELECT id_sala, cod_vino, cantidad FROM public.stock_sala "
                    "WHERE cantidad > 0 ORDER BY id_sala, cod_vino")
        stock_db = {(int(s), int(v)): int(c) for s, v, c in cur.fetchall()}
        if stock_db != stock_inicial:
            raise ValueError("ventas: stock_sala de PostgreSQL difiere de refs de Logistica")

        # 1) CLIENTE (se recuperan IDs por su clave natural, no por posicion
        # supuesta en RETURNING, ni por la secuencia autoincremental).
        filas_clientes, docs_exportadores = _generar_clientes(
            rng, faker, n_clientes, localidad_ids, config.start_date, fin_altas
        )
        devueltos = _insertar_lotes(
            cur, "cliente", _COLUMNAS_CLIENTE, filas_clientes, batch_size,
            returning="id_cliente, tipo_doc, nro_doc"
        )
        id_por_documento = {(tipo, numero): int(ident)
                            for ident, tipo, numero in devueltos}
        if len(id_por_documento) != n_clientes:
            raise RuntimeError("ventas: no se recuperaron todos los IDs de cliente")
        cliente_ids = [id_por_documento[(fila[1], fila[2])] for fila in filas_clientes]
        exportador_ids_y_altas = [
            (id_por_documento[(tipo, nro)], alta)
            for tipo, nro, alta in docs_exportadores
        ]

        # 2) PERMISO_EXPORTACION, exclusivamente para exportadores.
        permisos = _generar_permisos(rng, exportador_ids_y_altas,
                                     fin_altas, fecha_operativa)
        _insertar_lotes(cur, "permiso_exportacion",
                        ("codigo_permiso", "id_cliente", "fecha_emision",
                         "fecha_vencimiento"), permisos, batch_size)

        # Consultar precios actuales SIN calcular descuentos ni totales.
        cur.execute("SELECT cod_vino, precio FROM public.vino ORDER BY cod_vino")
        precios = {int(cod): precio for cod, precio in cur.fetchall()
                   if int(cod) in vinos_validos}
        if len(precios) != len(vinos_validos):
            raise ValueError("ventas: faltan precios de vinos publicados por Produccion")

        # 3) COMPROBANTES y 4) RENGLONES. Para asociar sin ambiguedad cada
        # cabecera y sus vinos se reservan IDs reales con nextval, sin suponer
        # que empiezan en 1 ni que son consecutivos.
        cur.execute("SELECT pg_get_serial_sequence('public.comprobante', 'nro_comprobante')")
        secuencia = cur.fetchone()[0]
        if not secuencia:
            raise ValueError("ventas: comprobante.nro_comprobante debe tener secuencia SERIAL")
        comprobante_ids: list[int] = []
        for inicio in range(0, n_comprobantes, batch_size):
            parte = plan[inicio:inicio + batch_size]
            cur.execute("SELECT nextval(%s::regclass) FROM generate_series(1, %s)",
                        (secuencia, len(parte)))
            ids = [int(fila[0]) for fila in cur.fetchall()]
            cabeceras: list[tuple] = []
            renglones: list[tuple] = []
            for nro, (id_sala, vinos_documento) in zip(ids, parte):
                cliente = rng.choice(cliente_ids)
                # Misma fecha de las transferencias; hora reproducible dentro
                # de esa fecha. La fecha historica termina en septiembre 2026.
                hora = time(rng.randint(10, 20), rng.randint(0, 59),
                            rng.randint(0, 59))
                cabeceras.append((nro, datetime.combine(fecha_operativa, hora),
                                  cliente, id_sala))
                for vino, cantidad in vinos_documento:
                    renglones.append((nro, vino, cantidad, precios[vino], 0, 0))
            _insertar_lotes(cur, "comprobante",
                            ("nro_comprobante", "fecha", "id_cliente", "id_sala"),
                            cabeceras, batch_size)
            # Descuento y subtotal = 0 solo al insertar: el trigger BEFORE los
            # sustituye por sus valores correctos, y AFTER actualiza cabecera.
            _insertar_lotes(cur, "renglon_comprobante",
                            ("nro_comprobante", "cod_vino", "cantidad",
                             "precio_unitario", "descuento", "subtotal"),
                            renglones, batch_size)
            comprobante_ids.extend(ids)

        # Verificacion localizada de stock; la modificacion real fue hecha
        # exclusivamente por trg_renglon_comprobante.
        cur.execute("SELECT id_sala, cod_vino, cantidad FROM public.stock_sala ")
        stock_final = {(int(s), int(v)): int(c) for s, v, c in cur.fetchall()}
        if any(stock_final.get(clave) != saldo for clave, saldo in saldos_previstos.items()):
            raise RuntimeError("ventas: saldos reales no coinciden con el plan de ventas")
        if any(cantidad < 0 for cantidad in stock_final.values()):
            raise RuntimeError("ventas: se detecto stock_sala negativo")

        # No actualizar refs de Logistica: su diccionario es el snapshot previo
        # a ventas. Solo publicar IDs reales cuando la carga concluyo bien.
        refs["cliente_ids"] = cliente_ids
        refs["comprobante_ids"] = comprobante_ids
        refs["permiso_exportacion_codigos"] = [fila[0] for fila in permisos]
        return {
            "cliente": len(cliente_ids),
            "permiso_exportacion": len(permisos),
            "comprobante": len(comprobante_ids),
            "renglon_comprobante": n_renglones,
            "segundos": round(perf_counter() - t0, 2),
        }
