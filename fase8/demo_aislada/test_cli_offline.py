"""Comprobaciones URL del ejecutor, sin red."""
import pytest
from ejecutar_demo import validar_destino

@pytest.mark.parametrize("url", [
    "https://bodegas-atuel-api.onrender.com",
    "https://bodegas-del-atuel.vercel.app",
    "http://bodegas-demo.onrender.com",
    "https://example.org",
    "https://user:pass@bodegas-demo.onrender.com",
    "https://bodegas-demo.onrender.com/comprobantes",
    "https://bodegas-demo.onrender.com?token=abc",
])
def test_bloquea_destinos_inseguros(url):
    with pytest.raises(ValueError):
        validar_destino(url, False)

def test_acepta_servicio_demo_https():
    assert validar_destino("https://bodegas-demo.onrender.com", False) == "https://bodegas-demo.onrender.com"
    assert validar_destino("https://bodegas-ensayo.onrender.com/", False) == "https://bodegas-ensayo.onrender.com"

def test_solo_loopback_para_local():
    assert validar_destino("http://127.0.0.1:8002", True) == "http://127.0.0.1:8002"
    with pytest.raises(ValueError):
        validar_destino("http://192.168.1.10:8002", True)
