import unittest

from engine.personaje import Sobreviviente
from engine.decision_support import aplicar_auto_supervivencia


class TestSurvivalAIBehavior(unittest.TestCase):
    def test_critical_health_forces_survival_treatment(self):
        p = Sobreviviente()
        p.salud = max(1, int(p.salud_max * 0.20))
        p.skills["medicina"] = 90
        p.skills["farmacologia"] = 90
        p.historial_farmacos = [
            {
                "principio_activo": "morfina",
                "clase": "opioide",
                "dosis": 1.0,
                "hora_abs": float(p.dia * 24 + p.hora),
                "ventana_horas": 8,
            }
        ]

        p.inventario.append(
            {
                "nombre": "Morfina rescate",
                "tipo": "medicina_fuerte",
                "peso": 0.1,
                "cantidad": 2,
                "efectos": {"salud": 18},
                "farmacologia": {
                    "principio_activo": "morfina",
                    "clase": "opioide",
                    "dosis": 1.2,
                    "dosis_toxica": 2.0,
                    "ventana_horas": 8,
                    "no_combinar_con": ["analgesico"],
                },
            }
        )

        salud_antes = p.salud
        acciones = aplicar_auto_supervivencia(p)

        self.assertTrue(any("Tratamiento" in a for a in acciones))
        self.assertGreater(p.salud, salud_antes)

    def test_initial_skills_are_not_legendary_by_default(self):
        p = Sobreviviente()
        self.assertLessEqual(max(p.skills.values()), 80)


if __name__ == "__main__":
    unittest.main()
