import unittest

from engine.personaje import Sobreviviente


class TestCraftingSystem(unittest.TestCase):
    def test_can_craft_improvised_bandage(self):
        p = Sobreviviente()
        p.skills["supervivencia"] = 40
        p.inventario = [
            {"nombre": "Tiras de tela", "tipo": "material", "cantidad": 2, "peso": 0.1},
            {"nombre": "Alcohol industrial", "tipo": "material_especial", "cantidad": 1, "peso": 0.5},
        ]

        ok, msg = p.craftear("venda_improvisada")

        self.assertTrue(ok)
        self.assertIn("Crafteaste", msg)
        self.assertIsNotNone(p.obtener_item("Venda"))

    def test_reject_craft_when_missing_materials(self):
        p = Sobreviviente()
        p.skills["supervivencia"] = 40
        p.inventario = []

        ok, msg = p.craftear("venda_improvisada")

        self.assertFalse(ok)
        self.assertIn("Faltan materiales", msg)


if __name__ == "__main__":
    unittest.main()
