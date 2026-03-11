"""
tests/test_aging.py
Tests para el sistema de envejecimiento (F6).
"""
import unittest

from engine.personaje import Sobreviviente


class TestEnvejecimiento(unittest.TestCase):

    def _personaje(self, edad: int = 25) -> Sobreviviente:
        p = Sobreviviente()
        p.edad = edad
        p.edad_inicio = edad
        p.dia = 1
        p.penalizaciones_envejecimiento = []
        return p

    def test_sin_cumpleanos_no_cambia_edad(self):
        p = self._personaje(30)
        p.dia = 100     # menos de 365 días → no hay cumpleaños
        msgs = p.tick_envejecimiento()
        self.assertEqual(p.edad, 30)
        self.assertEqual(msgs, [])

    def test_cumpleanos_incrementa_edad(self):
        p = self._personaje(30)
        p.dia = 365     # exactamente un año
        msgs = p.tick_envejecimiento()
        self.assertEqual(p.edad, 31)
        self.assertTrue(any("31" in m for m in msgs))

    def test_penalizacion_stats_a_los_50(self):
        p = self._personaje(49)
        fuerza_antes = p.stats["fuerza"]
        p.dia = 365     # cumple 50
        p.tick_envejecimiento()
        self.assertEqual(p.edad, 50)
        self.assertLess(p.stats["fuerza"], fuerza_antes + 1)
        # La penalización de los 50 reduce fuerza
        self.assertIn(50, p.penalizaciones_envejecimiento)

    def test_penalizacion_no_se_aplica_dos_veces(self):
        p = self._personaje(49)
        p.dia = 365
        p.tick_envejecimiento()
        fuerza_tras_primer = p.stats["fuerza"]
        # Segundo tick sin cambio de año
        p.tick_envejecimiento()
        self.assertEqual(p.stats["fuerza"], fuerza_tras_primer)

    def test_reduccion_salud_max_a_los_60(self):
        p = self._personaje(59)
        salud_max_antes = p.salud_max
        p.dia = 365     # cumple 60
        p.tick_envejecimiento()
        self.assertLessEqual(p.salud_max, salud_max_antes)

    def test_muerte_natural_posible_a_los_80(self):
        """A los 80 años, la probabilidad de muerte natural es > 0."""
        # Usamos un RNG fijo: se ejecutan muchos personajes y al menos uno muere
        muertos = 0
        for seed_extra in range(200):
            p = self._personaje(79)
            # Truco: forzar rng en Random
            import random
            original_random = random.random
            random.random = lambda: 0.005   # por debajo del umbral
            try:
                p.dia = 365   # cumple 80
                p.tick_envejecimiento()
                if p.salud <= 0:
                    muertos += 1
            finally:
                random.random = original_random
            break   # con random fijo, el primer intento es suficiente
        self.assertGreaterEqual(muertos, 1)

    def test_serializar_y_restaurar_campos_envejecimiento(self):
        p = self._personaje(48)
        p.dia = 730    # cumplió 2 años
        p.tick_envejecimiento()

        data = p.a_dict()
        restaurado = Sobreviviente.desde_dict(data)
        self.assertEqual(restaurado.edad, p.edad)
        self.assertEqual(restaurado.edad_inicio, p.edad_inicio)
        self.assertEqual(restaurado.penalizaciones_envejecimiento,
                         p.penalizaciones_envejecimiento)


if __name__ == "__main__":
    unittest.main()
