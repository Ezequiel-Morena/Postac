import unittest

from engine.personaje import Sobreviviente
from engine.tick import ejecutar_descanso


class TestRestFatigueRecovery(unittest.TestCase):
    def test_rest_reduces_fatigue_significantly(self):
        p = Sobreviviente()
        p.inventario = []
        p.fatiga = 94
        p.hambre = 20
        p.sed = 20

        resultado = ejecutar_descanso(p)

        self.assertLessEqual(p.fatiga, 65)
        self.assertTrue(any("Fatiga -" in linea for linea in resultado.log_descanso))


if __name__ == "__main__":
    unittest.main()
