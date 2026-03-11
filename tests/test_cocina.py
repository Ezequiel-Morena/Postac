"""
tests/test_cocina.py
Tests para el sistema de cocina (engine/cocina.py).
"""
import unittest
from unittest.mock import patch

from engine.personaje import Sobreviviente
from engine.cocina import cocinar_item, puede_cocinar, listar_items_cocinables


def _personaje_con_fuego() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.inventario.clear()
    p.almacen.clear()
    p.fatiga = 0
    p.fuego_activo = True
    p.combustible_restante = 200
    return p


def _personaje_sin_fuego() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.inventario.clear()
    p.almacen.clear()
    p.fatiga = 0
    p.fuego_activo = False
    p.combustible_restante = 0
    return p


class TestPuedeCocinar(unittest.TestCase):

    def test_puede_con_fuego_activo(self):
        p = _personaje_con_fuego()
        puede, _ = puede_cocinar(p)
        self.assertTrue(puede)

    def test_no_puede_sin_fuego(self):
        p = _personaje_sin_fuego()
        puede, razon = puede_cocinar(p)
        self.assertFalse(puede)
        self.assertIn("fuego", razon.lower())


class TestCocinarItem(unittest.TestCase):

    @patch("engine.cocina.random.random", return_value=0.99)
    def test_cocinar_pez_pequeno(self, _mock):
        p = _personaje_con_fuego()
        p.inventario.append({"id": "pez_pequeno", "nombre": "Pez pequeño", "cantidad": 1})
        resultado = cocinar_item(p, "pez_pequeno")
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["resultado_item"]["id"], "pez_cocido")
        # El pez crudo debe haberse consumido del inventario
        ids_inv = [i["id"] for i in p.inventario]
        self.assertNotIn("pez_pequeno", ids_inv)

    @patch("engine.cocina.random.random", return_value=0.99)
    def test_cocinar_carne_cruda(self, _mock):
        p = _personaje_con_fuego()
        p.inventario.append({"id": "carne_animal_cruda", "nombre": "Carne cruda", "cantidad": 1})
        resultado = cocinar_item(p, "carne_animal_cruda")
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["resultado_item"]["id"], "carne_asada")

    def test_cocinar_sin_fuego_falla(self):
        p = _personaje_sin_fuego()
        p.inventario.append({"id": "pez_pequeno", "nombre": "Pez pequeño", "cantidad": 1})
        resultado = cocinar_item(p, "pez_pequeno")
        self.assertFalse(resultado["exito"])
        self.assertIn("fuego", resultado["mensaje"].lower())

    @patch("engine.cocina.random.random", return_value=0.99)
    def test_cocinar_item_inexistente_falla(self, _mock):
        p = _personaje_con_fuego()
        resultado = cocinar_item(p, "item_inventado")
        self.assertFalse(resultado["exito"])

    @patch("engine.cocina.random.random", return_value=0.99)
    def test_cocinar_sin_ingrediente_falla(self, _mock):
        p = _personaje_con_fuego()
        resultado = cocinar_item(p, "pez_pequeno")
        self.assertFalse(resultado["exito"])
        self.assertIn("no tienes", resultado["mensaje"].lower())

    @patch("engine.cocina.random.random", return_value=0.99)
    def test_resultado_va_al_almacen(self, _mock):
        p = _personaje_con_fuego()
        p.inventario.append({"id": "pez_pequeno", "nombre": "Pez pequeño", "cantidad": 1})
        cocinar_item(p, "pez_pequeno")
        ids_almacen = [i["id"] for i in p.almacen]
        self.assertIn("pez_cocido", ids_almacen)

    @patch("engine.cocina.random.random", return_value=0.99)
    def test_combustible_insuficiente_falla(self, _mock):
        p = _personaje_con_fuego()
        p.combustible_restante = 1  # muy poco
        p.inventario.append({"id": "pez_pequeno", "nombre": "Pez pequeño", "cantidad": 1})
        resultado = cocinar_item(p, "pez_pequeno")
        self.assertFalse(resultado["exito"])
        self.assertIn("combustible", resultado["mensaje"].lower())

    @patch("engine.cocina.random.random", return_value=0.99)
    def test_fatiga_aumenta_al_cocinar(self, _mock):
        p = _personaje_con_fuego()
        p.fatiga = 0
        p.inventario.append({"id": "pez_pequeno", "nombre": "Pez pequeño", "cantidad": 1})
        cocinar_item(p, "pez_pequeno")
        self.assertGreater(p.fatiga, 0)


class TestListarItemsCocinables(unittest.TestCase):

    def test_lista_items_disponibles(self):
        p = _personaje_con_fuego()
        p.inventario.append({"id": "pez_pequeno", "nombre": "Pez pequeño", "cantidad": 1})
        p.inventario.append({"id": "agua_sucia", "nombre": "Agua sucia", "cantidad": 1})
        cocinables = listar_items_cocinables(p)
        self.assertIn("pez_pequeno", cocinables)
        self.assertIn("agua_sucia", cocinables)

    def test_lista_vacia_sin_items(self):
        p = _personaje_con_fuego()
        cocinables = listar_items_cocinables(p)
        self.assertEqual(cocinables, [])


if __name__ == "__main__":
    unittest.main()
