"""
tests/test_caza.py
Tests para el sistema de caza y trampas (engine/caza.py).
"""
import unittest
from unittest.mock import patch

from engine.personaje import Sobreviviente
from engine.caza import puede_cazar, cazar_activo, poner_trampa, revisar_trampas


def _personaje(**overrides) -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.inventario.clear()
    p.almacen.clear()
    p.fatiga = 0
    p.trampas_activas = []
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


class TestPuedeCazar(unittest.TestCase):

    def test_zona_forestal_permite_caza(self):
        p = _personaje()
        puede, _ = puede_cazar(p, {"tags": ["forestal"]})
        self.assertTrue(puede)

    def test_zona_campo_permite_caza(self):
        p = _personaje()
        puede, _ = puede_cazar(p, {"tags": ["campo"]})
        self.assertTrue(puede)

    def test_zona_urbano_permite_caza(self):
        p = _personaje()
        puede, _ = puede_cazar(p, {"tags": ["urbano"]})
        self.assertTrue(puede)

    def test_zona_interior_sin_tag_caza_falla(self):
        p = _personaje()
        puede, razon = puede_cazar(p, {"tags": ["interior"]})
        self.assertFalse(puede)
        self.assertIn("fauna", razon.lower())

    def test_zona_sin_tags_falla(self):
        p = _personaje()
        puede, _ = puede_cazar(p, {})
        self.assertFalse(puede)


class TestCazarActivo(unittest.TestCase):

    @patch("engine.caza.random.random", return_value=0.01)
    @patch("engine.caza.random.choices")
    def test_caza_exitosa_retorna_carne(self, mock_choices, _mock_rand):
        animal = {
            "nombre": "Conejo", "rend_carne": 2, "rend_piel": 1,
            "peligro": 0, "peso_prob": 0.40, "nivel_min": 0,
        }
        mock_choices.return_value = [animal]
        p = _personaje()
        zona = {"tags": ["forestal"]}
        resultado = cazar_activo(p, zona, horas=1.0)
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["capturas_carne"], 2)
        self.assertEqual(resultado["capturas_piel"], 1)
        self.assertEqual(resultado["animal"], "Conejo")

    def test_caza_en_zona_invalida_falla(self):
        p = _personaje()
        zona = {"tags": ["interior"]}
        resultado = cazar_activo(p, zona)
        self.assertFalse(resultado["exito"])
        self.assertIn("fauna", resultado["mensaje"].lower())

    @patch("engine.caza.random.random", return_value=0.01)
    @patch("engine.caza.random.choices")
    def test_fatiga_aumenta_tras_cazar(self, mock_choices, _mock_rand):
        animal = {
            "nombre": "Rata", "rend_carne": 1, "rend_piel": 0,
            "peligro": 0, "peso_prob": 0.60, "nivel_min": 0,
        }
        mock_choices.return_value = [animal]
        p = _personaje()
        p.fatiga = 0
        zona = {"tags": ["forestal"]}
        cazar_activo(p, zona, horas=2.0)
        self.assertGreater(p.fatiga, 0)

    def test_resultado_contiene_campos_esperados(self):
        p = _personaje()
        zona = {"tags": ["interior"]}
        resultado = cazar_activo(p, zona)
        for campo in ("exito", "capturas_carne", "capturas_piel", "mensaje", "fatiga_costo", "animal"):
            self.assertIn(campo, resultado)


class TestPonerTrampa(unittest.TestCase):

    def test_poner_trampa_exitoso(self):
        p = _personaje()
        p.inventario.append({"id": "trampa_caza", "nombre": "Trampa de lazo", "usos": 3})
        zona = {"id": "zona_bosque", "nombre": "Bosque denso", "tags": ["forestal"]}
        exito, msg = poner_trampa(p, zona)
        self.assertTrue(exito)
        self.assertEqual(len(p.trampas_activas), 1)
        self.assertEqual(p.trampas_activas[0]["zona_id"], "zona_bosque")

    def test_poner_trampa_sin_trampa_falla(self):
        p = _personaje()
        zona = {"id": "zona_bosque", "nombre": "Bosque denso", "tags": ["forestal"]}
        exito, msg = poner_trampa(p, zona)
        self.assertFalse(exito)
        self.assertIn("trampa", msg.lower())

    def test_poner_trampa_zona_invalida_falla(self):
        p = _personaje()
        p.inventario.append({"id": "trampa_caza", "nombre": "Trampa de lazo", "usos": 2})
        zona = {"id": "zona_interior", "nombre": "Interior", "tags": ["interior"]}
        exito, msg = poner_trampa(p, zona)
        self.assertFalse(exito)

    def test_trampa_gasta_uso(self):
        p = _personaje()
        p.inventario.append({"id": "trampa_caza", "nombre": "Trampa de lazo", "usos": 2})
        zona = {"id": "zona_bosque", "nombre": "Bosque", "tags": ["forestal"]}
        poner_trampa(p, zona)
        trampa_item = next((i for i in p.inventario if i.get("id") == "trampa_caza"), None)
        self.assertIsNotNone(trampa_item)
        self.assertEqual(trampa_item["usos"], 1)


class TestRevisarTrampas(unittest.TestCase):

    @patch("engine.caza.random.random", return_value=0.01)
    @patch("engine.caza.random.choices")
    def test_revisar_con_captura(self, mock_choices, _mock_rand):
        animal = {
            "nombre": "Conejo", "rend_carne": 2, "rend_piel": 1,
            "peligro": 0, "peso_prob": 0.40, "nivel_min": 0,
        }
        mock_choices.return_value = [animal]
        p = _personaje()
        p.trampas_activas = [{"zona_id": "bosque1", "zona_nombre": "Bosque", "horas_pendientes": 0}]
        zona = {"id": "bosque1", "nombre": "Bosque", "tags": ["forestal"]}
        capturas = revisar_trampas(p, zona)
        self.assertGreater(len(capturas), 0)
        self.assertEqual(p.trampas_activas, [])

    def test_revisar_sin_trampas(self):
        p = _personaje()
        zona = {"id": "bosque1", "nombre": "Bosque", "tags": ["forestal"]}
        capturas = revisar_trampas(p, zona)
        self.assertEqual(capturas, [])


if __name__ == "__main__":
    unittest.main()
