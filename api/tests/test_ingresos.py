"""Pruebas de integracion de /ingresos (Antonio).

Negativas por reglas de la base: procesar en confeccion (P0001 -> 409),
renglon en ingreso terminado (RN-12, P0001 -> 409), terminar sin renglones
(P0001 -> 409) y cantidad 0 (CHECK 23514 -> 422).
"""
from tests.apoyo_antonio import CUIT_BODEGA, TRANSPORTISTA, VINO_DE_LA_BODEGA
from tests.apoyo_antonio import client  # noqa: F401  (fixture protegido)


def _crear_ingreso(client) -> dict:
    r = client.post("/ingresos", json={"cod_transporte": TRANSPORTISTA, "cuit_bodega": CUIT_BODEGA})
    assert r.status_code == 201, r.text
    return r.json()


def test_crear_ingreso_queda_en_confeccion(client):
    ingreso = _crear_ingreso(client)
    assert ingreso["estado"] == "en_confeccion"   # DEFAULT de la base (RN-10)
    assert ingreso["renglones"] == []


def test_circuito_completo_suma_stock_del_deposito(client):
    ingreso = _crear_ingreso(client)
    cod = ingreso["cod_ingreso"]

    r = client.post(f"/ingresos/{cod}/renglones", json={"cod_vino": VINO_DE_LA_BODEGA, "cantidad": 120})
    assert r.status_code == 201, r.text
    stock_antes = r.json()["renglones"][0]["stock_deposito"]

    r = client.post(f"/ingresos/{cod}/terminar")
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "terminado"
    assert r.json()["renglones"][0]["stock_deposito"] == stock_antes  # terminar no toca stock

    r = client.post(f"/ingresos/{cod}/procesar")
    assert r.status_code == 200, r.text
    detalle = r.json()
    assert detalle["estado"] == "procesado"
    # El stock lo suma sp_procesar_ingreso; la API solo lo lee.
    assert detalle["renglones"][0]["stock_deposito"] == stock_antes + 120


def test_procesar_en_confeccion_es_rechazado(client):
    cod = _crear_ingreso(client)["cod_ingreso"]
    client.post(f"/ingresos/{cod}/renglones", json={"cod_vino": VINO_DE_LA_BODEGA, "cantidad": 10})

    r = client.post(f"/ingresos/{cod}/procesar")
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "P0001"
    assert "confeccion" in r.json()["error"]["mensaje"]
    # Rollback: el ingreso sigue en confeccion.
    assert client.get(f"/ingresos/{cod}").json()["estado"] == "en_confeccion"


def test_renglon_en_ingreso_terminado_es_rechazado(client):
    cod = _crear_ingreso(client)["cod_ingreso"]
    client.post(f"/ingresos/{cod}/renglones", json={"cod_vino": VINO_DE_LA_BODEGA, "cantidad": 10})
    client.post(f"/ingresos/{cod}/terminar")

    r = client.post(f"/ingresos/{cod}/renglones", json={"cod_vino": VINO_DE_LA_BODEGA + 1, "cantidad": 5})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "P0001"
    assert "RN-12" in r.json()["error"]["mensaje"]
    assert len(client.get(f"/ingresos/{cod}").json()["renglones"]) == 1


def test_terminar_sin_renglones_es_rechazado(client):
    cod = _crear_ingreso(client)["cod_ingreso"]
    r = client.post(f"/ingresos/{cod}/terminar")
    assert r.status_code == 409
    assert "no tiene renglones" in r.json()["error"]["mensaje"]


def test_cantidad_cero_viola_check(client):
    cod = _crear_ingreso(client)["cod_ingreso"]
    r = client.post(f"/ingresos/{cod}/renglones", json={"cod_vino": VINO_DE_LA_BODEGA, "cantidad": 0})
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "23514"


def test_ingreso_inexistente_devuelve_404(client):
    r = client.post("/ingresos/999999999/procesar")
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "NO_ENCONTRADO"
