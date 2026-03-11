import unittest

from engine.personaje import Condicion, Sobreviviente


class TestMedicalModular(unittest.TestCase):
    def test_high_medical_skill_avoids_unnecessary_medicine(self):
        p = Sobreviviente()
        p.skills["medicina"] = 80
        p.salud = p.salud_max
        p.inventario.append(
            {
                "nombre": "Venda de prueba",
                "tipo": "medicina",
                "peso": 0.1,
                "cantidad": 2,
                "efectos": {"salud": 8},
            }
        )

        ok, msg = p.usar_item("Venda de prueba")
        cant = next(i for i in p.inventario if i.get("nombre") == "Venda de prueba")["cantidad"]

        self.assertFalse(ok)
        self.assertIn("No hay necesidad médica", msg)
        self.assertEqual(cant, 2)

    def test_low_medical_skill_can_consume_unnecessary_medicine(self):
        p = Sobreviviente()
        p.skills["medicina"] = 5
        p.salud = p.salud_max
        p.inventario.append(
            {
                "nombre": "Píldora de prueba",
                "tipo": "medicina_fuerte",
                "peso": 0.1,
                "cantidad": 2,
                "efectos": {"salud": 20},
            }
        )

        ok, msg = p.usar_item("Píldora de prueba")
        cant = next(i for i in p.inventario if i.get("nombre") == "Píldora de prueba")["cantidad"]

        self.assertTrue(ok)
        self.assertIn("Carga farmacológica", msg)
        self.assertEqual(cant, 1)
        self.assertGreater(p.farmaco_carga, 0)

    def test_two_handed_weapon_blocked_if_one_arm_unusable(self):
        p = Sobreviviente()
        p.inventario.append(
            {
                "nombre": "Escopeta de prueba",
                "tipo": "arma_fuego",
                "peso": 2.5,
                "daño": (20, 30),
                "manos_requeridas": 2,
            }
        )

        cond = Condicion(
            "brazo_inutilizado",
            "Brazo inutilizado",
            3,
            8,
            {"brazos_inutiles": 1, "zona_cuerpo": "brazo_derecho"},
        )
        p.añadir_condicion(cond)

        arma = next(i for i in p.inventario if i.get("nombre") == "Escopeta de prueba")
        self.assertFalse(p.puede_usar_arma(arma))
        self.assertIn("requiere", p.motivo_bloqueo_arma(arma))


if __name__ == "__main__":
    unittest.main()
