import unittest

from engine.personaje import Sobreviviente
from engine.relaciones import tick_refugio
from engine.familia import generar_npc, integrar_npc_en_refugio


def _personaje_con_npcs() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.relaciones_refugio = {}
    for i in range(3):
        npc = generar_npc(f"seed_refugio_{i}", p)
        integrar_npc_en_refugio(p, npc)
    return p


class TestRefugioRelaciones(unittest.TestCase):

    def test_tick_refugio_vacio_no_genera_eventos(self):
        """Un refugio vacío no genera eventos (nadie para generar nada)."""
        p = Sobreviviente()
        p.relaciones_refugio = {}
        eventos = tick_refugio(p, 6, contexto="descanso")
        self.assertIsInstance(eventos, list)
        self.assertEqual(eventos, [])

    def test_tick_refugio_con_npcs_genera_eventos(self):
        p = _personaje_con_npcs()
        eventos = tick_refugio(p, 6, contexto="descanso")
        self.assertGreaterEqual(len(eventos), 1)
        for estado in p.relaciones_refugio.values():
            self.assertGreaterEqual(int(estado["confianza"]), 0)
            self.assertLessEqual(int(estado["confianza"]), 100)

    def test_relaciones_refugio_persist_through_serialization(self):
        """Los NPCs generados deben persistir en serialización."""
        p = _personaje_con_npcs()
        npc_id = list(p.relaciones_refugio.keys())[0]
        p.relaciones_refugio[npc_id]["confianza"] = 77

        data = p.a_dict()
        restaurado = Sobreviviente.desde_dict(data)

        self.assertIn(npc_id, restaurado.relaciones_refugio)
        self.assertEqual(int(restaurado.relaciones_refugio[npc_id]["confianza"]), 77)

    def test_familia_persiste_serialization(self):
        """El árbol familiar debe persistir en serialización."""
        p = Sobreviviente()
        p.familia = {"npc_test": {"tipo": "pareja", "nombre": "Ana", "apellido": "Cruz"}}
        data = p.a_dict()
        restaurado = Sobreviviente.desde_dict(data)
        self.assertIn("npc_test", restaurado.familia)
        self.assertEqual(restaurado.familia["npc_test"]["tipo"], "pareja")


if __name__ == "__main__":
    unittest.main()

