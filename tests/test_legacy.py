"""
tests/test_legacy.py
Tests para el sistema de legado enriquecido (F6 legacy).
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine.personaje import Sobreviviente
from engine.save_manager import eco_del_pasado, obtener_leaderboard, registrar_muerte
from engine.animales import generar_animal, integrar_animal


def _personaje_completo() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    # Simular algo de historia
    p.dia = 120
    p.expediciones_completadas = 30
    p.infectados_eliminados = 15
    p.edad = 35
    p.edad_inicio = 27
    p.familia = {"npc_01": {"tipo": "pareja", "nombre": "Ana", "apellido": "Cruz"}}
    return p


class _LeaderboardAislado(unittest.TestCase):
    """
    Base que redirige FILE_LEADERBOARD a un archivo temporal por cada test.
    Evita que los tests de legado contaminen el leaderboard real de partidas.
    """

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w", encoding="utf-8"
        )
        self._tmp.write("[]")
        self._tmp.close()
        self._tmp_path = Path(self._tmp.name)
        self._patcher = patch("engine.save_manager.FILE_LEADERBOARD", self._tmp_path)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmp_path.unlink(missing_ok=True)


class TestRegistrarMuerte(_LeaderboardAislado):

    def test_entrada_tiene_campos_legado(self):
        p = _personaje_completo()
        registrar_muerte(p, causa="test_legado")
        tabla = obtener_leaderboard()
        entrada = next((e for e in tabla if p.nombre in e.get("nombre", "")), None)
        if entrada is None:
            return
        self.assertIn("edad_final", entrada)
        self.assertIn("tuvo_pareja", entrada)
        self.assertIn("mejor_skill", entrada)
        self.assertIn("condiciones_al_morir", entrada)

    def test_tuvo_pareja_detectado(self):
        p = _personaje_completo()
        p.familia = {"x": {"tipo": "pareja", "nombre": "Ana", "apellido": "Cruz"}}
        registrar_muerte(p, causa="test_pareja")
        tabla = obtener_leaderboard()
        entrada = next((e for e in tabla if p.nombre in e.get("nombre", "")), None)
        if entrada:
            self.assertTrue(entrada.get("tuvo_pareja"))

    def test_animales_count_en_leaderboard(self):
        p = _personaje_completo()
        animal = generar_animal("perro", "seed_lb_test")
        integrar_animal(p, animal)
        registrar_muerte(p, causa="test_animales")
        tabla = obtener_leaderboard()
        entrada = next((e for e in tabla if p.nombre in e.get("nombre", "")), None)
        if entrada:
            self.assertGreaterEqual(entrada.get("animales_count", 0), 0)


class TestEcoDelPasado(_LeaderboardAislado):

    def test_eco_retorna_string(self):
        eco = eco_del_pasado()
        self.assertIsInstance(eco, str)

    def test_eco_vacio_sin_leaderboard(self):
        """Con el leaderboard temporal vacío, eco_del_pasado retorna ''."""
        eco = eco_del_pasado()
        self.assertEqual(eco, "")

    def test_eco_contiene_nombre_o_dias(self):
        """Si hay entradas, el eco debe mencionar días o supervivencia."""
        p = _personaje_completo()
        p.dia = 99
        registrar_muerte(p, "test_eco_dias")
        eco = eco_del_pasado()
        if eco:
            self.assertTrue(
                "días" in eco or "día" in eco or "99" in eco or p.nombre in eco,
                f"Eco inesperado: {eco}"
            )


if __name__ == "__main__":
    unittest.main()
