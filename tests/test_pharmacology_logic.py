import unittest

from engine.personaje import Sobreviviente


class TestPharmacologyLogic(unittest.TestCase):
    def test_high_medical_skill_blocks_repeated_same_active(self):
        p = Sobreviviente()
        p.skills["medicina"] = 80
        p.salud = max(1, p.salud_max - 30)
        med = {
            "nombre": "Morfina test",
            "tipo": "medicina_fuerte",
            "peso": 0.1,
            "cantidad": 2,
            "efectos": {"salud": 10},
            "farmacologia": {
                "principio_activo": "morfina",
                "clase": "opioide",
                "dosis": 1.2,
                "dosis_toxica": 2.0,
                "ventana_horas": 10,
                "contraindicaciones": [],
                "no_combinar_con": ["analgesico"],
            },
        }
        p.inventario.append(med)

        ok1, _ = p.usar_item("Morfina test")
        salud_post_1 = p.salud
        ok2, msg2 = p.usar_item("Morfina test")
        qty = next(i for i in p.inventario if i.get("nombre") == "Morfina test")["cantidad"]

        self.assertTrue(ok1)
        self.assertFalse(ok2)
        self.assertIn("ya hay morfina activo", msg2.lower())
        self.assertEqual(qty, 1)
        self.assertEqual(p.salud, salud_post_1)

    def test_low_medical_skill_can_overdose_on_repeat(self):
        p = Sobreviviente()
        p.skills["medicina"] = 10
        p.skills["farmacologia"] = 0
        p.rasgos.clear()  # eliminar rasgos de background para test determinista
        p.stats["resistencia"] = 1  # evitar que evaluar_rasgos_nuevos aplique metabolismo_rapido
        p.salud = max(1, p.salud_max - 30)
        med = {
            "nombre": "Morfina riesgo",
            "tipo": "medicina_fuerte",
            "peso": 0.1,
            "cantidad": 2,
            "efectos": {"salud": 10},
            "farmacologia": {
                "principio_activo": "morfina",
                "clase": "opioide",
                "dosis": 1.3,
                "dosis_toxica": 2.0,
                "ventana_horas": 10,
                "contraindicaciones": [],
                "no_combinar_con": ["analgesico"],
            },
        }
        p.inventario.append(med)

        salud_antes = p.salud
        ok1, _ = p.usar_item("Morfina riesgo")
        salud_post_1 = p.salud
        ok2, msg2 = p.usar_item("Morfina riesgo")

        self.assertTrue(ok1)
        self.assertTrue(ok2)
        self.assertIn("sobredosis", msg2.lower())
        self.assertLessEqual(p.salud, salud_post_1)
        self.assertGreaterEqual(salud_post_1, salud_antes)


if __name__ == "__main__":
    unittest.main()
