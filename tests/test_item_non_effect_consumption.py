import unittest

from engine.personaje import Sobreviviente


class TestItemNonEffectConsumption(unittest.TestCase):
    def test_bandage_not_consumed_when_no_effect(self):
        p = Sobreviviente()
        p.skills["medicina"] = 40
        p.salud = p.salud_max
        p.inventario.append(
            {
                "nombre": "Venda no-efecto",
                "tipo": "medicina",
                "peso": 0.1,
                "cantidad": 3,
                "efectos": {"salud": 8},
            }
        )

        ok, msg = p.usar_item("Venda no-efecto")
        qty = next(i for i in p.inventario if i.get("nombre") == "Venda no-efecto")["cantidad"]

        self.assertFalse(ok)
        self.assertIn("No hay necesidad médica", msg)
        self.assertEqual(qty, 3)


if __name__ == "__main__":
    unittest.main()
