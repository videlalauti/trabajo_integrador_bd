#!/usr/bin/env python3
"""PROPUESTA, no reemplaza al kit aprobado sin aval de coordinación.

Comparación de conteos exactos para las 27 tablas del TP, sin conexiones a BD.
Separa requisitos de la base completa de los de la carga reducida en nube.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

TABLAS = (
    'localidad', 'sala_venta', 'empleado', 'finca', 'cepa', 'parcela',
    'bodega', 'lote_uva', 'analisis_calidad', 'vino', 'vino_cepa',
    'maridaje', 'vino_maridaje', 'tipo_cliente', 'cliente',
    'permiso_exportacion', 'comprobante', 'renglon_comprobante',
    'transportista', 'transportista_localidad', 'ingreso',
    'renglon_ingreso', 'transferencia', 'renglon_transferencia',
    'stock_sala', 'stock_deposito', 'auditoria_precio',
)
ESPERADAS = set(TABLAS)


def leer_csv(ruta: Path) -> dict[str, int]:
    resultado: dict[str, int] = {}
    with ruta.open('r', encoding='utf-8-sig', newline='') as archivo:
        lector = csv.DictReader(archivo)
        if lector.fieldnames != ['tabla', 'filas']:
            raise ValueError(f'{ruta}: encabezado obligatorio tabla,filas')
        for linea, fila in enumerate(lector, start=2):
            if None in fila or None in fila.values():
                raise ValueError(f'{ruta}:{linea}: columnas insuficientes o sobrantes')
            nombre = fila['tabla'].strip()
            cantidad = fila['filas'].strip()
            if not nombre or nombre in resultado:
                raise ValueError(f'{ruta}:{linea}: tabla vacía o repetida')
            if not re.fullmatch(r'[0-9]+', cantidad):
                raise ValueError(f'{ruta}:{linea}: conteo inválido para {nombre}')
            resultado[nombre] = int(cantidad)
    if not resultado:
        raise ValueError(f'{ruta}: CSV vacío')
    return resultado


def evaluar(origen: dict[str, int], restaurado: dict[str, int], perfil: str):
    problemas: list[str] = []
    for etiqueta, datos in [('ORIGEN', origen), ('DESTINO', restaurado)]:
        faltantes = sorted(ESPERADAS - set(datos))
        sobrantes = sorted(set(datos) - ESPERADAS)
        if faltantes:
            problemas.append(f'{etiqueta}: faltan {len(faltantes)} tablas: {", ".join(faltantes)}')
        if sobrantes:
            problemas.append(f'{etiqueta}: tablas no esperadas: {", ".join(sobrantes)}')
        vacias = sorted(k for k in ESPERADAS & set(datos) if datos[k] == 0)
        if vacias:
            problemas.append(f'{etiqueta}: tablas sin filas: {", ".join(vacias)}')
    for tabla in sorted(ESPERADAS):
        if tabla in origen and tabla in restaurado and origen[tabla] != restaurado[tabla]:
            problemas.append(f'CONTEO DISTINTO {tabla}: {origen[tabla]} != {restaurado[tabla]}')

    if set(origen) == ESPERADAS:
        if perfil == 'nube_reducida':
            if not any(v >= 10000 for v in origen.values()):
                problemas.append('NUBE REDUCIDA: ninguna tabla tiene >= 10000 filas')
        elif perfil == 'local_completa':
            if sum(v > 10000 for v in origen.values()) < 3:
                problemas.append('BASE COMPLETA: menos de 3 tablas superan 10000 filas')
            if not any(v > 100000 for v in origen.values()):
                problemas.append('BASE COMPLETA: ninguna tabla supera 100000 filas')
        else:
            raise ValueError(f'Perfil inválido: {perfil}')
    return problemas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origen', type=Path, required=True)
    parser.add_argument('--destino', type=Path, required=True)
    parser.add_argument('--perfil', choices=['nube_reducida', 'local_completa'], required=True)
    args = parser.parse_args()
    try:
        origen = leer_csv(args.origen)
        restaurado = leer_csv(args.destino)
        problemas = evaluar(origen, restaurado, args.perfil)
        print('tabla,origen,destino,resultado')
        for tabla in sorted(ESPERADAS):
            a, b = origen.get(tabla), restaurado.get(tabla)
            estado = 'OK' if a is not None and b is not None and a == b else 'FALTA_O_DIFIERE'
            print(f'{tabla},{"" if a is None else a},{"" if b is None else b},{estado}')
        if problemas:
            print('NO APROBADO:', file=sys.stderr)
            for p in problemas:
                print(' - ' + p, file=sys.stderr)
            return 1
        print(f'APROBADO: 27 tablas coincidentes, no vacías, perfil {args.perfil}')
        return 0
    except (OSError, ValueError) as error:
        print(f'NO APROBADO: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
