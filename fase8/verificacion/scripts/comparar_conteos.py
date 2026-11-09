#!/usr/bin/env python3
"""Compara conteos exactos exportados por psql --csv, sin acceso a la BD."""
import argparse
import csv
import sys
from pathlib import Path


def leer(path):
    datos = {}
    with open(path, newline="", encoding="utf-8-sig") as stream:
        lector = csv.DictReader(stream)
        if lector.fieldnames != ["tabla", "filas"]:
            raise ValueError(f"{path}: columnas requeridas tabla,filas; recibidas {lector.fieldnames}")
        for i, fila in enumerate(lector, start=2):
            nombre = fila["tabla"].strip()
            if not nombre or nombre in datos:
                raise ValueError(f"{path}:{i}: tabla vacía o repetida")
            val = int(fila["filas"])
            if val < 0:
                raise ValueError(f"{path}:{i}: conteo negativo")
            datos[nombre] = val
    if not datos:
        raise ValueError(f"{path}: sin tablas")
    return datos


def comparar(origen, destino, minimo=10000):
    a, b = leer(origen), leer(destino)
    filas = []
    errores = []
    for tabla in sorted(set(a) | set(b)):
        x, y = a.get(tabla), b.get(tabla)
        ok = x is not None and y is not None and x == y
        filas.append((tabla, x, y, "OK" if ok else "DIFERENCIA"))
        if not ok:
            errores.append(tabla)
    cumple_volumen = any(n >= minimo for n in a.values())
    if not cumple_volumen:
        errores.append(f"Ninguna tabla del origen tiene >= {minimo} filas")
    return filas, errores


def main():
    parser = argparse.ArgumentParser(description="Comparación reproducible de conteos entre origen y restauración")
    parser.add_argument("--origen", type=Path, required=True)
    parser.add_argument("--destino", type=Path, required=True)
    parser.add_argument("--minimo", type=int, default=10000, help="Mínimo de filas para una tabla (consigna: 10000)")
    args = parser.parse_args()
    try:
        if args.minimo < 1:
            raise ValueError("El mínimo debe ser positivo")
        filas, errores = comparar(args.origen, args.destino, args.minimo)
        print("tabla,origen,destino,estado")
        for tabla, x, y, estado in filas:
            print(f"{tabla},{'' if x is None else x},{'' if y is None else y},{estado}")
        if errores:
            print("NO APROBADO: " + "; ".join(errores), file=sys.stderr)
            return 1
        print("APROBADO: conteos coincidentes y volumen mínimo alcanzado")
        return 0
    except (OSError, ValueError) as exc:
        print(f"NO APROBADO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
