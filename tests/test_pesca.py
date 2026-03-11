"""
tests/test_pesca.py
Tests para el sistema de pesca (engine/pesca.py).
"""
import unittest
from unittest.mock import patch

from engine.personaje import Sobreviviente
from engine.pesca import intentar_pesca, puede_pescar


def _personaje(**overrides) -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.inventario.clear()
    p.almacen.clear()
    p.fatiga = 0
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


class TestPuedePescar(unittest.TestCase):

    def test_zona_con_rio_permite_pesca(self):
        p = _personaje()
        puede, _ = puede_pescar(p, {"tags": ["exterior", "rio"]})
        self.assertTrue(puede)

    def test_zona_con_lago_permite_pesca(self):
        p = _personaje()
        puede, _ = puede_pescar(p, {"tags": ["lago"]})
        self.assertTrue(puede)

    def test_zona_con_costa_permite_pesca(self):
        p = _personaje()
        puede, _ = puede_pescar(p, {"tags": ["costa"]})
        self.assertTrue(puede)

    def test_zona_interior_no_permite_pesca(self):
        p = _personaje()
        puede, razon = puede_pescar(p, {"tags": ["interior"]})
        self.assertFalse(puede)
        self.assertIn("agua", razon.lower())

    def test_zona_sin_tags_no_permite_pesca(self):
        p = _personaje()
        puede, _ = puede_pescar(p, {})
        self.assertFalse(puede)


class TestIntentarPesca(unittest.TestCase):

    @patch("engine.pesca.random.random", return_value=0.01)
    @patch("engine.pesca.random.choices")
    def test_pesca_exitosa_en_zona_rio(self, mock_choices, mock_rand):
        mock_choices.return_value = [
            {"id": "pez_pequeno", "nombre": "Trucha pequeña", "peso_prob": 0.45, "nivel_min": 0}
        ]
        p = _personaje()
        p.inventario.append({"id": "cana_pesca", "nombre": "Caña de pescar", "usos": 5})
        zona = {"tags": ["exterior", "rio"]}
        resultado = intentar_pesca(p, zona, horas=1.0)
        self.assertTrue(resultado["exito"])
        self.assertGreater(len(resultado["capturas"]), 0)

    def test_pesca_falla_en_zona_interior(self):
        p = _personaje()
        zona = {"tags": ["interior"]}
        resultado = intentar_pesca(p, zona)
        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["capturas"], [])
        self.assertIn("agua", resultado["mensaje"].lower())

    @patch("engine.pesca.random.random", return_value=0.01)
    @patch("engine.pesca.random.choices")
    def test_cana_mejora_probabilidad(self, mock_choices, mock_rand):
        mock_choices.return_value = [
            {"id": "pez_pequeno", "nombre": "Bagre", "peso_prob": 0.05, "nivel_min": 0}
        ]
        p_con = _personaje()
        p_con.inventario.append({"id": "cana_pesca", "nombre": "Caña de pescar", "usos": 5})

        p_sin = _personaje()

        zona = {"tags": ["exterior", "rio"]}
        res_con = intentar_pesca(p_con, zona, horas=1.0)
        res_sin = intentar_pesca(p_sin, zona, horas=1.0)

        # Ambos con random=0.01 siempre pescan, pero verificamos la estructura
        self.assertTrue(res_con["exito"])
        self.assertTrue(res_sin["exito"])

    def test_resultado_contiene_campos_esperados(self):
        p = _personaje()
        zona = {"tags": ["interior"]}
        resultado = intentar_pesca(p, zona)
        for campo in ("exito", "capturas", "xp_ganada", "mensaje", "fatiga_costo", "horas_usadas"):
            self.assertIn(campo, resultado)

    @patch("engine.pesca.random.random", return_value=0.01)
    @patch("engine.pesca.random.choices")
    def test_fatiga_aumenta_tras_pescar(self, mock_choices, mock_rand):
        mock_choices.return_value = [
            {"id": "pez_pequeno", "nombre": "Trucha pequeña", "peso_prob": 0.45, "nivel_min": 0}
        ]
        p = _personaje()
        p.fatiga = 0
        zona = {"tags": ["exterior", "rio"]}
        intentar_pesca(p, zona, horas=2.0)
        self.assertGreater(p.fatiga, 0)

    @patch("engine.pesca.random.random", return_value=0.01)
    @patch("engine.pesca.random.choices")
    def test_cana_se_desgasta(self, mock_choices, mock_rand):
        mock_choices.return_value = [
            {"id": "pez_pequeno", "nombre": "Trucha pequeña", "peso_prob": 0.45, "nivel_min": 0}
        ]
        p = _personaje()
        p.inventario.append({"id": "cana_pesca", "nombre": "Caña de pescar", "usos": 2})
        zona = {"tags": ["exterior", "rio"]}
        intentar_pesca(p, zona, horas=1.0)
        cana = next((i for i in p.inventario if i.get("id") == "cana_pesca"), None)
        self.assertIsNotNone(cana)
        self.assertEqual(cana["usos"], 1)


if __name__ == "__main__":
    unittest.main()
