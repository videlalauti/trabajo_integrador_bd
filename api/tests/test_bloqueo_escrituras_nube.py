"""Pruebas locales sin PostgreSQL ni red: no tocan Supabase."""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.bloqueo_escrituras_nube import BloqueoEscriturasNube


@pytest.fixture
def prueba(monkeypatch):
    app = FastAPI()
    app.add_middleware(BloqueoEscriturasNube)
    efectos = []
    @app.api_route('/{ruta:path}', methods=['GET','HEAD','OPTIONS','POST','PUT','PATCH','DELETE','TRACE'])
    async def recurso(request: Request):
        efectos.append((request.method,request.url.path))
        return {'ok':True}
    return TestClient(app),efectos


@pytest.mark.parametrize('metodo',['POST','PUT','PATCH','DELETE','TRACE'])
def test_remoto_bloquea_todos_los_metodos_mutantes(monkeypatch, prueba, metodo):
    monkeypatch.setenv('DB_HOST','aws-1-us-west-2.pooler.supabase.com')
    cliente,efectos=prueba
    r=cliente.request(metodo,'/vinos')
    assert r.status_code==403
    assert r.json()['error']['codigo']=='ESCRITURA_NUBE_BLOQUEADA'
    assert r.headers['cache-control']=='no-store'
    assert efectos==[]


@pytest.mark.parametrize('ruta',['/salud','/vinos','/vinos/1','/salas','/bodegas','/cepas','/maridajes','/reportes/top-vinos'])
def test_remoto_publica_solo_get_revisados(monkeypatch,prueba,ruta):
    monkeypatch.setenv('DB_HOST','aws-1-us-west-2.pooler.supabase.com')
    cliente,efectos=prueba
    r=cliente.get(ruta)
    assert r.status_code==200
    assert efectos==[('GET',ruta)]


@pytest.mark.parametrize('ruta',['/clientes','/clientes/1','/comprobantes/1','/ingresos/1','/transferencias/1','/reportes/ventas-por-sala','/reportes/vinos-sin-stock','/reportes/trazabilidad/1','/docs','/openapi.json','/vinos/1/otra','/vinos/0','/api/clientes'])
def test_remoto_bloquea_toda_lectura_no_publica(monkeypatch,prueba,ruta):
    monkeypatch.setenv('DB_HOST','aws-1-us-west-2.pooler.supabase.com')
    cliente,efectos=prueba
    r=cliente.get(ruta)
    assert r.status_code==403
    assert r.json()['error']['codigo']=='LECTURA_NO_PUBLICA'
    assert efectos==[]


def test_remoto_permite_preflight_no_muta(monkeypatch,prueba):
    monkeypatch.setenv('DB_HOST','aws-1-us-west-2.pooler.supabase.com')
    cliente,efectos=prueba
    assert cliente.options('/vinos').status_code==200
    assert efectos==[('OPTIONS','/vinos')]


def test_local_no_cambia_semantica(monkeypatch,prueba):
    monkeypatch.setenv('DB_HOST','localhost')
    cliente,efectos=prueba
    assert cliente.post('/vinos').status_code==200
    assert efectos==[('POST','/vinos')]


def test_remoto_no_se_desactiva_con_env(monkeypatch,prueba):
    monkeypatch.setenv('DB_HOST','aws-1-us-west-2.pooler.supabase.com')
    monkeypatch.setenv('API_SOLO_LECTURA','false')
    cliente,efectos=prueba
    assert cliente.delete('/clientes/1').status_code==403
    assert efectos==[]
