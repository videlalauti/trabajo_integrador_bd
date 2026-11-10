"""Integración REAL con PostgreSQL 17 DESCARTABLE de GitHub Actions.

No usar contra Supabase ni producción. Se ejecuta con
DB_HOST=127.0.0.1, DB_NAME=bodegas_fase8_demo_local, FASE8_DEMO_LOCAL=1.
"""
import os

from fastapi.testclient import TestClient

from app.demo_main import app


def test_web_con_postgres17_real():
    assert os.environ["DB_HOST"] == "127.0.0.1"
    assert os.environ["DB_NAME"] == "bodegas_fase8_demo_local"
    assert os.environ["FASE8_DEMO_LOCAL"] == "1"
    assert os.environ["FASE8_EVAL_ENABLED"] == "1"
    clave = os.environ["FASE8_EVAL_PASSWORD"]

    # HTTPS virtual sin conexión externa: TestClient usa el lifespan real y PostgreSQL local.
    with TestClient(app, base_url="https://testserver") as cliente:
        assert cliente.get("/demo/sesion").status_code == 401
        assert cliente.post("/comprobantes", json={}).status_code == 401

        login = cliente.post("/demo/acceso", json={"clave": clave})
        assert login.status_code == 200
        csrf = login.json()["csrf"]
        headers = {"X-CSRF-Token": csrf}
        assert cliente.get("/demo/sesion").status_code == 200
        assert cliente.get("/demo/identidad").json()["modo"] == "aislado"

        # Los datos vienen de PostgreSQL (no de fixtures interceptadas).
        assert cliente.get("/vinos?page=1&page_size=20").status_code == 200
        assert cliente.get("/clientes?page=1&page_size=20").status_code == 200
        assert cliente.get("/bodegas").status_code == 200
        assert cliente.get("/cepas").status_code == 200
        assert cliente.get("/maridajes").status_code == 200
        assert cliente.get("/salas").status_code == 200
        assert cliente.get("/demo/localidades").status_code == 200
        assert cliente.get("/demo/transportistas").status_code == 200

        # Evitar escritura sin CSRF incluso dentro de sesión.
        assert cliente.post("/comprobantes", json={}).status_code == 403
        candidatos_respuesta = cliente.get("/demo/candidatos")
        assert candidatos_respuesta.status_code == 200
        candidato = candidatos_respuesta.json()
        assert candidato["disponible"] is True
        vino, sala, id_cliente = (
            candidato["cod_vino"], candidato["id_sala"], candidato["id_cliente"]
        )
        url_estado = f"/demo/estado?id_sala={sala}&cod_vino={vino}"
        previo = cliente.get(url_estado).json()

        # Venta real y cálculo de importes/stock por los triggers PostgreSQL.
        venta = {
            "id_cliente": id_cliente, "id_sala": sala,
            "renglones": [{"cod_vino": vino, "cantidad": 1}],
        }
        res = cliente.post("/comprobantes", json=venta, headers=headers)
        assert res.status_code == 201, res.text
        assert res.json()["total"] is not None
        despues = cliente.get(url_estado).json()
        assert despues["comprobantes"] == previo["comprobantes"] + 1
        assert despues["stock_sala"] == previo["stock_sala"] - 1

        # RN-09 real: el rollback impide pérdida de stock o filas adicionales.
        venta["renglones"][0]["cantidad"] = despues["stock_sala"] + 1
        res = cliente.post("/comprobantes", json=venta, headers=headers)
        assert res.status_code == 409, res.text
        assert cliente.get(url_estado).json() == despues

        # Transferencia por los cuatro POST reales de la API.
        res = cliente.post("/transferencias", json={"id_sala": sala}, headers=headers)
        assert res.status_code == 201, res.text
        nro = res.json()["nro_solicitud"]
        res = cliente.post(
            f"/transferencias/{nro}/renglones",
            json={"cod_vino": vino, "cantidad": 1}, headers=headers,
        )
        assert res.status_code in (200, 201), res.text
        assert cliente.post(
            f"/transferencias/{nro}/terminar", headers=headers,
        ).status_code == 200
        res = cliente.post(f"/transferencias/{nro}/procesar", headers=headers)
        assert res.status_code == 200, res.text
        final = cliente.get(url_estado).json()
        assert final["transferencias"] == previo["transferencias"] + 1
        assert final["stock_sala"] == previo["stock_sala"]
        assert final["stock_deposito"] == previo["stock_deposito"] - 1

        # Los cinco reportes obligatorios ejecutan consultas reales.
        for ruta in (
            "/reportes/top-vinos", "/reportes/ventas-por-sala",
            f"/reportes/vinos-sin-stock?id_sala={sala}",
            "/reportes/transportista-activo",
            f"/reportes/trazabilidad/{vino}",
        ):
            respuesta = cliente.get(ruta)
            assert respuesta.status_code == 200, (ruta, respuesta.text)

        # Cierre de sesión real en el cliente.
        assert cliente.post("/demo/salir", headers=headers).status_code == 200
        assert cliente.get("/demo/sesion").status_code == 401
