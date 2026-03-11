import unittest

from engine.mundo import _factor_escasez_regional
from engine.personaje import Sobreviviente


class TestRegionalScarcity(unittest.TestCase):
    def test_revisit_penalizes_regional_scarcity_factor(self):
        p = Sobreviviente()
        p.dia = 20
        p.expediciones_completadas = 6

        sin_revisita = _factor_escasez_regional(p, "hospital")
        p.areas_visitadas.append("hospital")
        con_revisita = _factor_escasez_regional(p, "hospital")

        self.assertLess(con_revisita, sin_revisita)

    def test_high_survival_skills_mitigate_scarcity(self):
        p = Sobreviviente()
        p.dia = 40
        p.expediciones_completadas = 12
        p.skills["saqueo"] = 0
        p.skills["supervivencia"] = 0
        base = _factor_escasez_regional(p, "comisaria")

        p.skills["saqueo"] = 80
        p.skills["supervivencia"] = 80
        mitigado = _factor_escasez_regional(p, "comisaria")

        self.assertGreater(mitigado, base)


if __name__ == "__main__":
    unittest.main()
