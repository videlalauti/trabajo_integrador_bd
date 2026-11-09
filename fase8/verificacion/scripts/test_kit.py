import tempfile
import unittest
from pathlib import Path

from check_public_api import validar_base
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


if __name__ == '__main__':
    unittest.main()
