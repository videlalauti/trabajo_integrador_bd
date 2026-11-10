"""Solo datos ficticios en memoria: nunca abre conexiones ni toca nube."""
import tempfile
import unittest
from pathlib import Path

from comparar_conteos_estricto import TABLAS, evaluar, leer_csv


def inventar(**valores):
    conjunto = {t: 1 for t in TABLAS}
    conjunto.update(valores)
    return conjunto


class PruebasEstricto(unittest.TestCase):
    def test_27_y_perfil_reducido_ok(self):
        a = inventar(cliente=10000)
        self.assertEqual(evaluar(a, a.copy(), 'nube_reducida'), [])

    def test_27_y_perfil_completo_ok(self):
        a = inventar(cliente=20000, comprobante=150000, renglon_comprobante=500000)
        self.assertEqual(evaluar(a, a.copy(), 'local_completa'), [])

    def test_detecta_csv_de_tres_tablas_aunque_coincidan(self):
        a = {'cliente': 12000, 'comprobante': 3000, 'vino': 25}
        self.assertTrue(any('faltan 24' in p for p in evaluar(a, a.copy(), 'nube_reducida')))

    def test_detecta_diferencia(self):
        a = inventar(cliente=10000)
        b = a.copy(); b['cliente'] -= 1
        self.assertTrue(any('CONTEO DISTINTO cliente' in p for p in evaluar(a, b, 'nube_reducida')))

    def test_detecta_tabla_vacia(self):
        a = inventar(cliente=10000, vino=0)
        self.assertTrue(any('tablas sin filas: vino' in p for p in evaluar(a, a, 'nube_reducida')))

    def test_rechaza_perfil_reducido_insuficiente(self):
        a = inventar(cliente=9999)
        self.assertTrue(any('>= 10000' in p for p in evaluar(a, a, 'nube_reducida')))

    def test_rechaza_perfil_completo_insuficiente(self):
        a = inventar(cliente=10000, comprobante=100000, renglon_comprobante=20000)
        errores = evaluar(a, a, 'local_completa')
        self.assertTrue(any('menos de 3' in p for p in errores))
        self.assertTrue(any('ninguna tabla supera 100000' in p for p in errores))

    def test_rechaza_duplicados_csv(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / 'conteos.csv'
            ruta.write_text('tabla,filas\ncliente,10000\ncliente,10000\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                leer_csv(ruta)

    def test_rechaza_columnas_extra_csv(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / 'conteos.csv'
            ruta.write_text('tabla,filas\ncliente,10000,EXTRA\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                leer_csv(ruta)


if __name__ == '__main__':
    unittest.main()
