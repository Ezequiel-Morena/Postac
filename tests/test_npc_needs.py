"""Tests para el sistema de necesidades autónomas de NPCs (relaciones)."""
import random
import unittest

from engine.personaje import Sobreviviente
from engine.relaciones import tick_refugio, estado_relaciones_refugio_base
from engine.familia import generar_npc, integrar_npc_en_refugio


def _personaje_con_npc() -> Sobreviviente:
    """Personaje con un NPC generado proceduralmente."""
    p = Sobreviviente()
    p.rasgos.clear()
    p.relaciones_refugio = {}
    npc = generar_npc("seed_test_npc", p)
    integrar_npc_en_refugio(p, npc)
    return p


class TestNPCNeeds(unittest.TestCase):

    def test_refugio_base_vacio(self):
        """El refugio base debe estar vacío: los NPCs se generan proceduralmente."""
        estado = estado_relaciones_refugio_base()
        self.assertEqual(estado, {}, "estado_relaciones_refugio_base() debe devolver {}")

    def test_npc_generado_tiene_personalidad(self):
        npc = generar_npc("seed_pers", Sobreviviente())
        self.assertIn("personalidad", npc)
        self.assertIsInstance(npc["personalidad"], str)

    def test_npc_generado_tiene_campos_vitales(self):
        npc = generar_npc("seed_vitales", Sobreviviente())
        for campo in ("hambre", "salud", "confianza", "lealtad", "tension"):
            self.assertIn(campo, npc, f"NPC generado falta campo '{campo}'")
            self.assertGreaterEqual(npc[campo], 0)
            self.assertLessEqual(npc[campo], 100)

    def test_tick_refugio_returns_list(self):
        p = _personaje_con_npc()
        msgs = tick_refugio(p, horas=6.0)
        self.assertIsInstance(msgs, list)

    def test_npc_hambre_increases_over_time(self):
        """El hambre de un NPC debe aumentar en cada tick cuando no hay comida."""
        old_state = random.getstate()
        random.seed(777)
        p = _personaje_con_npc()
        # partida_id fijo para que el rng interno de tick_refugio sea determinista
        # (partida_id incluye datetime.now(), haciéndolo no-reproducible).
        p.partida_id = "test_hambre_deterministic"
        p.inventario = []
        p.almacen = []
        npc_key = next(iter(p.relaciones_refugio))
        npc = p.relaciones_refugio[npc_key]
        npc["hambre"] = 0
        npc["en_expedicion"] = False
        npc["puede_expedicion"] = False
        npc["salud"] = 100
        # Ejecutar varios ticks: incluso si un evento reduce hambre un tick,
        # la tendencia sin comida siempre es al alza.
        for _ in range(3):
            p.dia += 1
            tick_refugio(p, horas=6.0)
        random.setstate(old_state)
        hambre_despues = npc.get("hambre", 0)
        self.assertGreater(hambre_despues, 0,
                           "El hambre de los NPCs debe subir con el tiempo sin comida")

    def test_critical_hunger_reported(self):
        """Si un NPC llega a hambre >= 90, tick_refugio debe avisar."""
        p = _personaje_con_npc()
        p.inventario = []  # Sin comida para que no auto-consuma
        for npc_estado in p.relaciones_refugio.values():
            npc_estado["hambre"] = 92
            npc_estado["en_expedicion"] = False
        # Fijar semilla para evitar que un evento de scavenging alimente al NPC
        import random
        rng_state = random.getstate()
        random.seed(42)
        msgs = tick_refugio(p, horas=1.0)
        random.setstate(rng_state)
        # Verificar que al menos un NPC sigue con hambre alta o generó alerta
        hay_alerta = any(
            "sin comer" in m.lower() or "hambre" in m.lower() or "crítica" in m.lower()
            for m in msgs
        )
        self.assertTrue(hay_alerta, f"Debe notificar hambre crítica. Msgs: {msgs}")


if __name__ == "__main__":
    unittest.main()
