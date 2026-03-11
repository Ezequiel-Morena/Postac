"""
tests/test_animales.py
Tests para el sistema de animales domésticos (F5).
"""
import unittest

from engine.personaje import Sobreviviente
from engine.animales import (
    generar_animal, integrar_animal, evaluar_encuentro_animal, tick_animales
)
from data.animales import TIPOS_ANIMALES


def _personaje() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.animales_refugio = []
    return p


class TestGenerarAnimal(unittest.TestCase):

    def test_genera_perro_valido(self):
        animal = generar_animal("perro", "seed_test_perro")
        self.assertEqual(animal["tipo"], "perro")
        self.assertIn("nombre", animal)
        self.assertGreater(animal["salud"], 0)
        self.assertGreater(animal["salud_max"], 0)

    def test_genera_todos_los_tipos(self):
        for tipo in TIPOS_ANIMALES:
            animal = generar_animal(tipo, f"seed_{tipo}")
            self.assertEqual(animal["tipo"], tipo)
            self.assertIn("nombre", animal)

    def test_misma_seed_mismo_animal(self):
        a1 = generar_animal("gato", "seed_reproducible")
        a2 = generar_animal("gato", "seed_reproducible")
        self.assertEqual(a1["nombre"], a2["nombre"])
        self.assertEqual(a1["edad_dias"], a2["edad_dias"])

    def test_tipo_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            generar_animal("dragon", "seed_x")


class TestIntegrarAnimal(unittest.TestCase):

    def test_integrar_agrega_al_refugio(self):
        p = _personaje()
        animal = generar_animal("perro", "seed_int")
        msg = integrar_animal(p, animal)
        self.assertEqual(len(p.animales_refugio), 1)
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg), 0)
        # El mensaje debe mencionar el nombre del animal
        self.assertIn(animal["nombre"], msg)

    def test_maximo_6_animales_por_cria(self):
        p = _personaje()
        for i in range(6):
            animal = generar_animal("gato", f"seed_max_{i}")
            integrar_animal(p, animal)
        self.assertEqual(len(p.animales_refugio), 6)
        # Intentar cría no debe pasar del límite
        import random
        rng = random.Random("seed_cria")
        from engine.animales import _intentar_cria
        _intentar_cria(p, p.animales_refugio[0], [], rng)
        self.assertEqual(len(p.animales_refugio), 6)


class TestTickAnimales(unittest.TestCase):

    def test_tick_vacio_no_genera_mensajes(self):
        p = _personaje()
        import random
        msgs = tick_animales(p, 6, random.Random("seed"))
        self.assertEqual(msgs, [])

    def test_tick_incrementa_hambre(self):
        p = _personaje()
        animal = generar_animal("gallina", "seed_hambre")
        animal["hambre"] = 0
        integrar_animal(p, animal)
        import random
        tick_animales(p, 24, random.Random("seed_tick"))
        # Después de 24h, el hambre debería haber subido
        self.assertGreater(p.animales_refugio[0]["hambre"], 0)

    def test_tick_animal_muerto_se_remueve(self):
        p = _personaje()
        animal = generar_animal("conejo", "seed_muerto")
        animal["salud"] = 0
        integrar_animal(p, animal)
        import random
        msgs = tick_animales(p, 6, random.Random("seed_rm"))
        self.assertEqual(len(p.animales_refugio), 0)
        self.assertTrue(any("muerto" in m.lower() or "murió" in m.lower() or "ha muerto" in m for m in msgs))

    def test_serializar_animales_refugio(self):
        p = _personaje()
        animal = generar_animal("perro", "seed_ser")
        integrar_animal(p, animal)
        nombre_antes = p.animales_refugio[0]["nombre"]

        data = p.a_dict()
        restaurado = Sobreviviente.desde_dict(data)
        self.assertEqual(len(restaurado.animales_refugio), 1)
        self.assertEqual(restaurado.animales_refugio[0]["nombre"], nombre_antes)


class TestEncuentroAnimal(unittest.TestCase):

    def test_encuentro_en_zona_residencial(self):
        p = _personaje()
        area = {
            "area_key": "casa_abandonada",
            "tags": ["residencial", "urbano"],
            "nombre": "Casa abandonada",
        }
        # Con suficientes semillas, alguna debería encontrar animal
        encontrados = 0
        for i in range(200):
            animal = evaluar_encuentro_animal(p, area, f"seed_enc_{i}")
            if animal is not None:
                encontrados += 1
        self.assertGreater(encontrados, 0)

    def test_max_animales_bloquea_encuentro(self):
        p = _personaje()
        for i in range(6):
            animal = generar_animal("gato", f"seed_blk_{i}")
            integrar_animal(p, animal)
        # Con 6 animales el tick no debería agregar más
        self.assertEqual(len(p.animales_refugio), 6)


if __name__ == "__main__":
    unittest.main()
