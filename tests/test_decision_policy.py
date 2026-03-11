import unittest

from engine.decision_support import AutoSupervivenciaPolicy, aplicar_auto_supervivencia
from engine.personaje import Sobreviviente


class TestDecisionPolicy(unittest.TestCase):
    def test_custom_policy_disables_medical_attempts(self):
        p = Sobreviviente()
        p.salud = max(1, int(p.salud_max * 0.20))
        p.inventario.append(
            {
                "nombre": "Botiquin policy",
                "tipo": "medicina",
                "peso": 0.1,
                "cantidad": 1,
                "efectos": {"salud": 12},
            }
        )

        policy = AutoSupervivenciaPolicy(max_intentos_emergencia=0)
        acciones = aplicar_auto_supervivencia(p, policy=policy)

        self.assertEqual(acciones, [])
        self.assertIsNotNone(p.obtener_item("Botiquin policy"))

    def test_custom_policy_can_force_water_consumption(self):
        p = Sobreviviente()
        p.sed = 20
        p.inventario.append(
            {
                "nombre": "Cantimplora test",
                "tipo": "agua",
                "peso": 0.2,
                "cantidad": 1,
                "efectos": {"sed": -20},
            }
        )

        policy = AutoSupervivenciaPolicy(sed_min=10)
        acciones = aplicar_auto_supervivencia(p, policy=policy)

        self.assertTrue(any("Bebiste Cantimplora test" in a for a in acciones))


if __name__ == "__main__":
    unittest.main()
