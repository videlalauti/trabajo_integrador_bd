"""Simula respuestas REST: NO crea comprobantes ni mueve stock real."""
import pytest
from ejecutar_demo import preflight, ejecutar

class APISimulada:
    def __init__(self):
        self.sala = 14
        self.vino = 5
        self.cliente = 2
        self.stock_sala = 12
        self.stock_deposito = 20
        self.comprobantes = 100
        self.renglones = 250
        self.transferencias = 3
        self.estado_transferencia = None
        self.solicitudes = []

    def estado(self):
        return {
            "comprobantes": self.comprobantes, "renglones": self.renglones,
            "stock_sala": self.stock_sala, "stock_deposito": self.stock_deposito,
            "transferencias": self.transferencias,
        }

    def pedir(self, metodo, ruta, payload=None):
        self.solicitudes.append((metodo, ruta))
        if metodo == "GET" and ruta == "/demo/identidad":
            return 200, {"modo": "aislado", "proyecto_ref": "LOCAL"}
        if metodo == "GET" and ruta == "/demo/candidatos":
            return 200, {
                "disponible": True, "id_cliente": self.cliente,
                "id_sala": self.sala, "cod_vino": self.vino,
                "stock_sala": self.stock_sala, "stock_deposito": self.stock_deposito,
            }
        if metodo == "GET" and ruta.startswith("/demo/estado?"):
            return 200, self.estado()
        if metodo == "POST" and ruta == "/comprobantes":
            cantidad = payload["renglones"][0]["cantidad"]
            if cantidad > self.stock_sala:
                return 409, {"error": {"codigo": "P0001", "mensaje": "RN-09: stock insuficiente"}}
            self.comprobantes += 1
            self.renglones += 1
            self.stock_sala -= cantidad
            return 201, {"nro_comprobante": 101}
        if metodo == "POST" and ruta == "/transferencias":
            self.transferencias += 1
            self.estado_transferencia = "en_confeccion"
            return 201, {"nro_solicitud": 4, "estado": self.estado_transferencia}
        if metodo == "POST" and ruta == "/transferencias/4/renglones":
            return 201, {"nro_solicitud": 4, "estado": self.estado_transferencia}
        if metodo == "POST" and ruta == "/transferencias/4/terminar":
            self.estado_transferencia = "terminado"
            return 200, {"nro_solicitud": 4, "estado": self.estado_transferencia}
        if metodo == "POST" and ruta == "/transferencias/4/procesar":
            self.estado_transferencia = "procesado"
            self.stock_deposito -= 1
            self.stock_sala += 1
            return 200, {"nro_solicitud": 4, "estado": self.estado_transferencia}
        raise AssertionError(f"Ruta no prevista: {metodo} {ruta}")

def test_preflight_es_100_por_ciento_lectura():
    api = APISimulada()
    candidatos, antes = preflight(api, "", True)
    assert candidatos["id_cliente"] == 2
    assert antes["stock_sala"] == 12
    assert all(m == "GET" for m, ruta in api.solicitudes)

def test_venta_rollback_transferencia_y_balance():
    api = APISimulada()
    candidatos, antes = preflight(api, "", True)
    ejecutar(api, candidatos, antes)
    assert api.comprobantes == 101
    assert api.renglones == 251
    assert api.transferencias == 4
    assert api.stock_sala == 12  # -1 venta, +1 transferencia
    assert api.stock_deposito == 19
    assert api.solicitudes.count(("POST", "/comprobantes")) == 2

def test_detiene_si_no_hay_409_de_rn09():
    class Fallida(APISimulada):
        def pedir(self, metodo, ruta, payload=None):
            if metodo == "POST" and ruta == "/comprobantes" and payload["renglones"][0]["cantidad"] > self.stock_sala:
                return 200, {"mensaje": "falso exito"}
            return super().pedir(metodo, ruta, payload)
    api = Fallida()
    candidatos, antes = preflight(api, "", True)
    with pytest.raises(RuntimeError, match="HTTP 409"):
        ejecutar(api, candidatos, antes)
