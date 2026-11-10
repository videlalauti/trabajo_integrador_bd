#!/usr/bin/env python3
"""Prueba de negocios Etapas 8/9 SOLO sobre API de ensayo aislada.

Por defecto ejecuta solo GET. El modo --ejecutar escribe UNA venta valida,
prueba RN-09 y procesa UNA transferencia, con mediciones antes/despues.
No imprime bearer tokens ni DB_PASSWORD.
"""
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

PROD = "https://bodegas-atuel-api.onrender.com"
PROD_REF = "sjfyocokehaubuwwbhnw"


class SinRedirecciones(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Redireccion no permitida en la API de ensayo")


def validar_destino(base: str, local: bool) -> str:
    u = urlsplit(base.rstrip("/"))
    if u.username or u.password or u.query or u.fragment or u.path not in ("", "/"):
        raise ValueError("La URL debe ser un origen sin rutas ni credenciales")
    if local:
        if u.scheme != "http" or u.hostname not in ("127.0.0.1", "localhost"):
            raise ValueError("Ensayo local exige http://127.0.0.1:<puerto>")
    else:
        if (u.scheme != "https" or u.hostname == urlsplit(PROD).hostname
                or not (u.hostname or "").endswith(".onrender.com")
                or not any(tag in (u.hostname or "") for tag in ("demo", "ensayo"))):
            raise ValueError("Se exige URL HTTPS de servicio Render DEMO independiente")
        if u.port not in (None, 443):
            raise ValueError("HTTPS demo no debe usar un puerto no estandar")
    if not u.netloc:
        raise ValueError("Falta URL de demostracion")
    return base.rstrip("/")


class ClienteDemo:
    def __init__(self, base: str, token: str):
        self.base, self.token = base, token
        self.opener = build_opener(SinRedirecciones())

    def pedir(self, metodo: str, ruta: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(
            self.base + ruta, method=metodo, data=data,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with self.opener.open(req, timeout=95) as res:
                if urlsplit(res.geturl()).netloc != urlsplit(self.base).netloc:
                    raise RuntimeError("La API redirigio a otro host")
                return res.status, json.loads(res.read(2_000_000))
        except HTTPError as error:
            raw = error.read(2_000_000)
            try:
                respuesta = json.loads(raw)
            except (ValueError, UnicodeError):
                respuesta = {"error": {"codigo": "RESPUESTA_NO_JSON"}}
            return error.code, respuesta
        except URLError as exc:
            raise RuntimeError("No se pudo contactar el servicio de demostracion") from exc


def exigir(condicion, mensaje):
    if not condicion:
        raise RuntimeError(mensaje)


def preflight(api: ClienteDemo, ref: str, local: bool):
    code, identidad = api.pedir("GET", "/demo/identidad")
    exigir(code == 200 and identidad.get("modo") == "aislado", "La API no acredita modo aislado")
    esperado = "LOCAL" if local else ref
    exigir(identidad.get("proyecto_ref") == esperado, "El proyecto demo no coincide")
    exigir(esperado != PROD_REF, "STOP: proyecto FULL prohibido")

    code, candidatos = api.pedir("GET", "/demo/candidatos")
    exigir(code == 200 and candidatos.get("disponible"), "No hay cliente/sala/vino ficticios aptos")
    sala, vino = candidatos["id_sala"], candidatos["cod_vino"]
    code, estado = api.pedir("GET", "/demo/estado?" + urlencode({"id_sala": sala, "cod_vino": vino}))
    exigir(code == 200, "No se pudo leer el estado inicial")
    exigir(estado["stock_sala"] >= 2 and estado["stock_deposito"] >= 2,
           "Stock insuficiente para ensayo controlado")
    print("PRECHECK OK: modo aislado, token valido, datos de prueba disponibles")
    print(f"Identificadores ficticios: cliente={candidatos['id_cliente']}, sala={sala}, vino={vino}")
    print("Estado inicial:", json.dumps(estado, sort_keys=True))
    return candidatos, estado


def ejecutar(api: ClienteDemo, candidato: dict, previo: dict):
    cliente, sala, vino = (candidato[k] for k in ("id_cliente", "id_sala", "cod_vino"))
    ruta_estado = "/demo/estado?" + urlencode({"id_sala": sala, "cod_vino": vino})

    venta = {
        "id_cliente": cliente, "id_sala": sala,
        "renglones": [{"cod_vino": vino, "cantidad": 1}],
    }
    code, resultado = api.pedir("POST", "/comprobantes", venta)
    exigir(code == 201 and resultado.get("nro_comprobante"), "Venta valida no generada")
    code, despues_venta = api.pedir("GET", ruta_estado)
    exigir(code == 200
           and despues_venta["comprobantes"] == previo["comprobantes"] + 1
           and despues_venta["renglones"] == previo["renglones"] + 1
           and despues_venta["stock_sala"] == previo["stock_sala"] - 1,
           "La venta no conserva los invariantes de conteos y stock")
    print(f"VENTA OK: comprobante={resultado['nro_comprobante']}, stock -1")

    # RN-09: cantidad justo por encima del stock observado.
    venta["renglones"][0]["cantidad"] = despues_venta["stock_sala"] + 1
    code, rechazo = api.pedir("POST", "/comprobantes", venta)
    err = rechazo.get("error", {})
    mensaje = str(err.get("mensaje", ""))
    exigir(code == 409 and err.get("codigo") == "P0001"
           and ("stock" in mensaje.lower() or "rn-09" in mensaje.lower()),
           "No se obtuvo HTTP 409/P0001 atribuible a RN-09")
    code, despues_rechazo = api.pedir("GET", ruta_estado)
    exigir(code == 200 and despues_rechazo == despues_venta,
           "STOP: RN-09 no preservo comprobantes/renglones/stock")
    print("RN-09 OK: 409/P0001 y rollback completo")

    code, t = api.pedir("POST", "/transferencias", {"id_sala": sala})
    exigir(code == 201 and t.get("estado") == "en_confeccion", "No se creo transferencia")
    nro = t["nro_solicitud"]
    code, _ = api.pedir("POST", f"/transferencias/{nro}/renglones",
                         {"cod_vino": vino, "cantidad": 1})
    exigir(code == 201, "No se pudo agregar renglon")
    code, t = api.pedir("POST", f"/transferencias/{nro}/terminar")
    exigir(code == 200 and t.get("estado") == "terminado", "No se pudo terminar")
    code, antes_proc = api.pedir("GET", ruta_estado)
    exigir(code == 200, "No se pudo leer stock antes de procesar")
    code, t = api.pedir("POST", f"/transferencias/{nro}/procesar")
    exigir(code == 200 and t.get("estado") == "procesado", "No se proceso")
    code, despues_proc = api.pedir("GET", ruta_estado)
    exigir(code == 200
           and despues_proc["stock_deposito"] == antes_proc["stock_deposito"] - 1
           and despues_proc["stock_sala"] == antes_proc["stock_sala"] + 1,
           "La transferencia no conservo el movimiento de stock")
    print(f"TRANSFERENCIA OK: nro={nro}, deposito -1, sala +1")
    print("RESULTADO 3/3: SOLO entorno aislado, nunca FULL")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ejecutar", action="store_true")
    parser.add_argument("--confirmar-demo", default="")
    args = parser.parse_args()
    local = os.getenv("FASE8_DEMO_LOCAL", "") == "1"
    base = validar_destino(os.getenv("FASE8_DEMO_URL", ""), local)
    token = os.getenv("FASE8_DEMO_TOKEN", "")
    if len(token) < 48:
        raise ValueError("Falta token privado largo de demo")
    ref = os.getenv("FASE8_DEMO_PROJECT_REF", "")
    if not local and (not ref or ref == PROD_REF):
        raise ValueError("Falta el identificador del proyecto demo independiente")
    api = ClienteDemo(base, token)
    candidatos, estado = preflight(api, ref, local)
    if not args.ejecutar:
        print("DRY RUN: solo lecturas. Para ensayar usar --ejecutar --confirmar-demo SOLO_BASE_DESCARTABLE")
        return 0
    if args.confirmar_demo != "SOLO_BASE_DESCARTABLE":
        raise ValueError("Falta confirmacion exacta para escrituras aisladas")
    ejecutar(api, candidatos, estado)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(f"STOP SEGURO: {exc}", file=sys.stderr)
        raise SystemExit(1)
