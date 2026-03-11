import unittest

from engine.clima import aplicar_efectos_clima, clima_actual, estacion_actual
from engine.personaje import Sobreviviente


class TestClimateSystem(unittest.TestCase):
    def test_estacion_lookup(self):
        self.assertEqual(estacion_actual(1), "primavera")
        self.assertEqual(estacion_actual(120), "verano")

    def test_climate_deterministic_for_tick_block(self):
        c1 = clima_actual(40, 8, {"area_key": "hospital"})
        c2 = clima_actual(40, 9, {"area_key": "hospital"})
        self.assertEqual(c1["clima_id"], c2["clima_id"])

    def test_heat_weather_applies_survival_pressure(self):
        p = Sobreviviente()
        p.sed = 20
        p.fatiga = 20
        clima = {
            "mods": {"sed_hora": 4, "fatiga_hora": 2, "hambre_hora": 1, "salud_tick": 0, "radiacion_hora": 0},
            "nombre": "calor_extremo",
        }
        msgs = aplicar_efectos_clima(p, 2, {"tags": ["exterior"]}, clima, en_refugio=False)
        self.assertGreaterEqual(p.sed, 28)
        self.assertGreaterEqual(p.fatiga, 24)
        self.assertTrue(any("sed" in m.lower() for m in msgs))


if __name__ == "__main__":
    unittest.main()
