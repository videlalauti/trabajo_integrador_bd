import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.request import Request
from pathlib import Path

from check_public_api import RedireccionRechazada, ejecutar, solicitar, validar_base
from comparar_conteos import comparar, leer


class VerificacionesKit(unittest.TestCase):
    def test_url_https(self):
        self.assertEqual(validar_base('https://api.example.com/'), 'https://api.example.com')

    def test_no_http(self):
        with self.assertRaises(ValueError):
            validar_base('http://api.example.com')

    def test_no_credenciales_embebidas(self):
        with self.assertRaises(ValueError):
            validar_base('https://user:pass@api.example.com')

    def test_compara_conteos_iguales(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.csv', Path(d)/'b.csv'
            content='tabla,filas\ncliente,12000\nvino,25\n'
            a.write_text(content); b.write_text(content)
            filas, errores = comparar(a,b)
            self.assertEqual(errores, [])
            self.assertEqual(len(filas), 2)

    def test_detecta_conteos_distintos(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.csv', Path(d)/'b.csv'
            a.write_text('tabla,filas\ncliente,12000\n')
            b.write_text('tabla,filas\ncliente,11999\n')
            filas, errores = comparar(a,b)
            self.assertEqual(errores, ['cliente'])

    def test_detecta_tabla_faltante(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.csv', Path(d)/'b.csv'
            a.write_text('tabla,filas\ncliente,12000\nvino,5\n')
            b.write_text('tabla,filas\ncliente,12000\n')
            _, errores = comparar(a,b)
            self.assertEqual(errores, ['vino'])

    def test_volumen_insuficiente(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d)/'a.csv', Path(d)/'b.csv'
            a.write_text('tabla,filas\ncliente,9999\n')
            b.write_text('tabla,filas\ncliente,9999\n')
            _, errores = comparar(a,b)
            self.assertTrue(any('10000' in e for e in errores))

    def test_fila_duplicada(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d)/'a.csv'
            a.write_text('tabla,filas\ncliente,12000\ncliente,12000\n')
            with self.assertRaises(ValueError):
                leer(a)


class VerificacionesHTTPSyTLS(unittest.TestCase):
    """Pruebas 100% offline: sin red, API ni escritura en DB."""

    @staticmethod
    def _salud(tls_marker):
        return (200, 'application/json', {
            'estado': 'ok', 'base_datos': 'conectada', 'tls': tls_marker,
        })

    def test_tls_true_aprueba(self):
        with patch('check_public_api.solicitar', return_value=self._salud(True)):
            resultado = ejecutar('https://api.example.com', 2, 1, 0)
        self.assertEqual(resultado['status'], 'OK')
        self.assertIs(resultado['tls'], True)

    def test_tls_false_rechazado(self):
        with patch('check_public_api.solicitar', return_value=self._salud(False)):
            with self.assertRaisesRegex(RuntimeError, 'tls: true'):
                ejecutar('https://api.example.com', 2, 1, 0)

    def test_tls_ausente_rechazado(self):
        respuesta = (200, 'application/json', {'estado': 'ok', 'base_datos': 'conectada'})
        with patch('check_public_api.solicitar', return_value=respuesta):
            with self.assertRaisesRegex(RuntimeError, 'tls: true'):
                ejecutar('https://api.example.com', 2, 1, 0)

    def test_tls_texto_rechazado(self):
        with patch('check_public_api.solicitar', return_value=self._salud('true')):
            with self.assertRaisesRegex(RuntimeError, 'tls: true'):
                ejecutar('https://api.example.com', 2, 1, 0)

    def _rechazo_redireccion(self, destino):
        handler = RedireccionRechazada()
        with self.assertRaisesRegex(ValueError, 'Redireccion'):
            handler.redirect_request(
                Request('https://api.example.com/salud'), None,
                302, 'Found', {}, destino,
            )

    def test_redireccion_http_rechazada(self):
        self._rechazo_redireccion('http://api.example.com/salud')

    def test_redireccion_otro_host_rechazada(self):
        self._rechazo_redireccion('https://otro.example.com/salud')

    def test_redireccion_mismo_host_rechazada(self):
        # Política intencional: ninguna redirección es necesaria para /salud.
        self._rechazo_redireccion('https://api.example.com/salud/')

    @staticmethod
    def _simular_destino(destino):
        response = MagicMock()
        response.geturl.return_value = destino
        response.status = 200
        response.headers = {'Content-Type': 'application/json'}
        response.read.return_value = b'{"estado":"ok","base_datos":"conectada","tls":true}'
        response.__enter__.return_value = response
        opener = MagicMock()
        opener.open.return_value = response
        return opener

    def test_url_final_http_rechazada(self):
        with patch('check_public_api.build_opener', return_value=self._simular_destino('http://api.example.com/salud')):
            with self.assertRaisesRegex(ValueError, 'Destino final inesperado'):
                solicitar('https://api.example.com/salud', 2)

    def test_url_final_otro_host_rechazada(self):
        with patch('check_public_api.build_opener', return_value=self._simular_destino('https://otro.example.com/salud')):
            with self.assertRaisesRegex(ValueError, 'Destino final inesperado'):
                solicitar('https://api.example.com/salud', 2)

    def test_url_final_original_aprueba(self):
        with patch('check_public_api.build_opener', return_value=self._simular_destino('https://api.example.com/salud')):
            code, content_type, payload = solicitar('https://api.example.com/salud', 2)
        self.assertEqual(code, 200)
        self.assertEqual(content_type, 'application/json')
        self.assertIs(payload['tls'], True)


if __name__ == '__main__':
    unittest.main()
