import unittest

from engine.personaje import Sobreviviente


class TestSkillsAdvanced(unittest.TestCase):
    def test_specialization_unlocks_when_level_threshold_reached(self):
        p = Sobreviviente()
        p.skills["medicina"] = 70
        p._recalcular_especialidades()

        especialidades = p.especialidades_skill("medicina")
        self.assertIn("Trauma de campo", especialidades)
        self.assertIn("Infecciosas", especialidades)

    def test_chronic_conditions_have_expected_shape(self):
        p = Sobreviviente()
        for c in p.condiciones_cronicas:
            self.assertIn("clave", c)
            self.assertIn("nombre", c)
            self.assertIn("origen", c)
            self.assertIn("severidad", c)
            self.assertIn("efectos", c)


if __name__ == "__main__":
    unittest.main()
