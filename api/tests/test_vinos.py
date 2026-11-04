
"""Pruebas automatizadas de validación del módulo de vinos."""

import pytest
from pydantic import ValidationError

from app.schemas.vinos import VinoCrear


@pytest.fixture
def datos_vino():
    """Datos válidos de ejemplo, sin conexión a PostgreSQL."""
    return {
        "nombre": "Vino de prueba",
        "tipo": "tinto",
        "anada": 2025,
        "volumen_ml": 750,
        "graduacion": "13.50",
        "precio": "15000",
        "cuit_bodega": "30999000300",
        "cepas": [{"id_cepa": 21, "porcentaje": 100}],
        "maridajes": [1],
    }


def test_crear_vino_valido(datos_vino):
    vino = VinoCrear.model_validate(datos_vino)
    assert vino.nombre == "Vino de prueba"
    assert vino.cuit_bodega == "30999000300"


def test_rechazar_precio_negativo(datos_vino):
    datos_vino["precio"] = -500

    with pytest.raises(ValidationError):
        VinoCrear.model_validate(datos_vino)


def test_rechazar_cuit_con_letras(datos_vino):
    datos_vino["cuit_bodega"] = "123ABC"

    with pytest.raises(ValidationError):
        VinoCrear.model_validate(datos_vino)


def test_rechazar_cuit_demasiado_largo(datos_vino):
    datos_vino["cuit_bodega"] = "123456789012"

    with pytest.raises(ValidationError):
        VinoCrear.model_validate(datos_vino)


def test_rechazar_vino_sin_cepas(datos_vino):
    datos_vino["cepas"] = []

    with pytest.raises(ValidationError):
        VinoCrear.model_validate(datos_vino)


def test_rechazar_porcentaje_cepa_mayor_100(datos_vino):
    datos_vino["cepas"] = [
        {"id_cepa": 21, "porcentaje": 110}
    ]

    with pytest.raises(ValidationError):
        VinoCrear.model_validate(datos_vino)


def test_rechazar_tipo_vino_invalido(datos_vino):
    datos_vino["tipo"] = "cerveza"

    with pytest.raises(ValidationError):
        VinoCrear.model_validate(datos_vino)
