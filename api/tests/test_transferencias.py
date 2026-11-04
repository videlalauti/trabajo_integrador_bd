"""Pruebas de integracion de /transferencias (Antonio).

Negativas por reglas de la base: procesar sin stock suficiente (P0001 -> 409
sin cambios a medias), procesar dos veces (P0001 -> 409) y procesar en
confeccion (P0001 -> 409).
"""
from datetime import date, timedelta

from tests.apoyo_antonio import CANTIDAD_IMPOSIBLE, SALA, VINO_DE_LA_BODEGA
from tests.apoyo_antonio import client  # noqa: F401  (fixture protegido)


def _crear_transferencia(client) -> dict:
    r = client.post("/transferencias", json={"id_sala": SALA})
    assert r.status_code == 201, r.text
    return r.json()


def _preparar_terminada(client, cantidad: int) -> int:
    nro = _crear_transferencia(client)["nro_solicitud"]
    r = client.post(f"/transferencias/{nro}/renglones", json={"cod_vino": VINO_DE_LA_BODEGA, "cantidad": cantidad})
    assert r.status_code == 201, r.text
    r = client.post(f"/transferencias/{nro}/terminar")
    assert r.status_code == 200, r.text
    return nro


def test_crear_transferencia_con_fecha_actual(client):
    t = _crear_transferencia(client)
    assert t["estado"] == "en_confeccion"
    # La fecha la fija el trigger (RN-11). Tolerancia de un dia por zona horaria.
    fecha = date.fromisoformat(t["fecha_confeccion"])
    assert abs(fecha - date.today()) <= timedelta(days=1)


def test_circuito_completo_mueve_stock_deposito_a_sala(client):
    nro = _preparar_terminada(client, 7)
    antes = client.get(f"/transferencias/{nro}").json()["renglones"][0]

    r = client.post(f"/transferencias/{nro}/procesar")
    assert r.status_code == 200, r.text
    despues = r.json()
    assert despues["estado"] == "procesado"
    renglon = despues["renglones"][0]
    # Los movimientos los hace sp_procesar_transferencia; la API solo los lee.
    assert renglon["stock_deposito"] == antes["stock_deposito"] - 7
    assert renglon["stock_sala"] == antes["stock_sala"] + 7


def test_procesar_sin_stock_suficiente_no_deja_cambios(client):
    nro = _preparar_terminada(client, CANTIDAD_IMPOSIBLE)
    antes = client.get(f"/transferencias/{nro}").json()

    r = client.post(f"/transferencias/{nro}/procesar")
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "P0001"
    assert "stock insuficiente" in r.json()["error"]["mensaje"]

    # ROLLBACK completo: estado y stocks iguales que antes.
    despues = client.get(f"/transferencias/{nro}").json()
    assert despues["estado"] == "terminado"
    assert despues["renglones"] == antes["renglones"]


def test_procesar_dos_veces_es_rechazado(client):
    nro = _preparar_terminada(client, 1)
    assert client.post(f"/transferencias/{nro}/procesar").status_code == 200

    r = client.post(f"/transferencias/{nro}/procesar")
    assert r.status_code == 409
    assert "ya fue procesada" in r.json()["error"]["mensaje"]


def test_procesar_en_confeccion_es_rechazado(client):
    nro = _crear_transferencia(client)["nro_solicitud"]
    client.post(f"/transferencias/{nro}/renglones", json={"cod_vino": VINO_DE_LA_BODEGA, "cantidad": 1})

    r = client.post(f"/transferencias/{nro}/procesar")
    assert r.status_code == 409
    assert client.get(f"/transferencias/{nro}").json()["estado"] == "en_confeccion"
