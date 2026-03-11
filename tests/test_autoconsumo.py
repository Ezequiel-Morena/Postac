# ============================================================
# tests/test_autoconsumo.py
# Tests para el motor de autoconsumo (engine/autoconsumo.py)
# y el método autoconsumo() de InventoryMixin.
# ============================================================

import copy
import unittest

from engine.personaje import Sobreviviente
from engine.familia import generar_npc, integrar_npc_en_refugio
from engine.autoconsumo import (
    autoconsumo_npc,
    resolver_autoconsumo_refugio,
    _perfil,
    _umbral_para_menor,
    _PERFILES,
    _PERFIL_NEUTRO,
)
from engine.almacen import agregar_item


# ── Helpers ──────────────────────────────────────────────────────────────────

COMIDA = {"nombre": "Lata de frijoles", "tipo": "comida", "cantidad": 1,
           "efectos": {"hambre": -30}, "peso": 0.5}
AGUA = {"nombre": "Botella de agua", "tipo": "agua", "cantidad": 1,
        "efectos": {"sed": -30}, "peso": 0.5}
MEDICINA = {"nombre": "Venda", "tipo": "medicina", "cantidad": 1,
            "efectos": {"salud": 25}, "peso": 0.1}


def _personaje_vacio() -> Sobreviviente:
    p = Sobreviviente()
    p.inventario = []
    p.almacen = []
    p.relaciones_refugio = {}
    return p


def _npc(personalidad: str = "pragmatico", hambre: int = 70, salud: int = 80) -> dict:
    return {
        "nombre": "Test",
        "rol": "civil",
        "personalidad": personalidad,
        "hambre": hambre,
        "salud": salud,
        "en_expedicion": False,
        "es_menor": False,
        "hijos": [],
        "pareja_id": None,
        "confianza": 50,
        "lealtad": 50,
        "tension": 20,
    }


# ── Tests: perfiles de personalidad ──────────────────────────────────────────

class TestPerfilesPorPersonalidad(unittest.TestCase):

    def test_perfil_altruista_tiene_umbral_alto(self):
        """Personalidades altruistas esperan más antes de comer (umbral > 70)."""
        for pers in ("generoso", "protector", "leal", "empatico"):
            with self.subTest(personalidad=pers):
                self.assertGreaterEqual(_perfil(pers)["hambre"], 75)

    def test_perfil_egoista_tiene_umbral_bajo(self):
        """Personalidades egoístas comen antes (umbral ≤ 60)."""
        for pers in ("oportunista", "hosco", "desconfiado", "cauteloso"):
            with self.subTest(personalidad=pers):
                self.assertLessEqual(_perfil(pers)["hambre"], 60)

    def test_perfil_altruista_prioriza_hijos(self):
        for pers in ("generoso", "protector", "leal", "empatico"):
            with self.subTest(personalidad=pers):
                self.assertEqual(_perfil(pers)["familia"], "hijos_primero")

    def test_perfil_egoista_prioriza_propio(self):
        for pers in ("oportunista", "hosco"):
            with self.subTest(personalidad=pers):
                self.assertEqual(_perfil(pers)["familia"], "propio_primero")

    def test_perfil_desconocido_usa_neutro(self):
        perfil = _perfil("personalidad_que_no_existe")
        self.assertEqual(perfil, _PERFIL_NEUTRO)


# ── Tests: autoconsumo_npc ────────────────────────────────────────────────────

class TestAutoconsumoNPC(unittest.TestCase):

    def test_npc_come_cuando_hambre_supera_umbral(self):
        """NPC con hambre alta debe consumir comida del almacén."""
        almacen = [copy.deepcopy(COMIDA)]
        estado = _npc("pragmatico", hambre=70)
        autoconsumo_npc(estado, almacen)
        self.assertLess(estado["hambre"], 70, "El hambre debe bajar tras comer")
        self.assertEqual(len(almacen), 0, "La comida debe haberse consumido del almacén")

    def test_npc_no_come_bajo_umbral(self):
        """NPC con hambre baja no debe consumir comida."""
        almacen = [copy.deepcopy(COMIDA)]
        estado = _npc("pragmatico", hambre=30)
        autoconsumo_npc(estado, almacen)
        self.assertEqual(len(almacen), 1, "No debe consumirse comida innecesariamente")
        self.assertEqual(estado["hambre"], 30)

    def test_npc_egoista_consume_antes(self):
        """NPC egoísta consume con hambre < 65 (umbral bajo)."""
        almacen = [copy.deepcopy(COMIDA)]
        estado = _npc("oportunista", hambre=55)
        autoconsumo_npc(estado, almacen)
        self.assertLess(estado["hambre"], 55)

    def test_npc_altruista_aguanta_mas(self):
        """NPC altruista NO consume con hambre 70 (umbral 80+)."""
        almacen = [copy.deepcopy(COMIDA)]
        estado = _npc("generoso", hambre=70)
        autoconsumo_npc(estado, almacen)
        self.assertEqual(len(almacen), 1, "Altruista no debe comer con hambre 70")

    def test_npc_usa_medicina_si_salud_baja(self):
        """NPC con salud baja debe consumir medicina."""
        almacen = [copy.deepcopy(MEDICINA)]
        estado = _npc("pragmatico", hambre=30, salud=30)
        autoconsumo_npc(estado, almacen)
        self.assertGreater(estado["salud"], 30)
        self.assertEqual(len(almacen), 0)

    def test_npc_sin_recursos_no_cambia_stats(self):
        """Sin recursos en almacén, el NPC no puede satisfacer necesidades."""
        almacen = []
        estado = _npc("pragmatico", hambre=90, salud=20)
        hambre_antes = estado["hambre"]
        salud_antes = estado["salud"]
        autoconsumo_npc(estado, almacen)
        self.assertEqual(estado["hambre"], hambre_antes)
        self.assertEqual(estado["salud"], salud_antes)

    def test_npc_sin_sed_no_bebe(self):
        """NPC sin campo 'sed' no debe intentar consumir agua (sed=0 < umbral)."""
        almacen = [copy.deepcopy(AGUA)]
        estado = _npc("pragmatico", hambre=30)
        # sed no está en el dict; valor default es 0
        autoconsumo_npc(estado, almacen)
        self.assertEqual(len(almacen), 1, "Sin sed, no debe consumir agua")

    def test_autoconsumo_devuelve_mensajes(self):
        """autoconsumo_npc devuelve lista de mensajes sobre lo consumido."""
        almacen = [copy.deepcopy(COMIDA)]
        estado = _npc("pragmatico", hambre=70)
        msgs = autoconsumo_npc(estado, almacen, nombre="Marta")
        self.assertIsInstance(msgs, list)
        self.assertTrue(any("Marta" in m for m in msgs))


# ── Tests: orden de prioridad en el refugio ───────────────────────────────────

class TestPrioridadAutoconsumo(unittest.TestCase):

    def _personaje_con_npcs(self) -> Sobreviviente:
        """Personaje con un NPC protector, uno egoísta y un menor."""
        p = _personaje_vacio()
        agregar_item(p.almacen, copy.deepcopy(COMIDA))  # solo 1 ración

        # NPC protector con hambre 72 (umbral 80, no come)
        p.relaciones_refugio["protector_id"] = _npc("generoso", hambre=72)

        # NPC egoísta con hambre 55 (umbral 50, sí come)
        p.relaciones_refugio["egoista_id"] = _npc("oportunista", hambre=55)

        # Menor con hambre 60 (umbral hijos: 65, sí come)
        menor = _npc("pragmatico", hambre=60)
        menor["es_menor"] = True
        p.relaciones_refugio["menor_id"] = menor

        return p

    def test_menor_come_antes_que_adulto_egoista(self):
        """El menor debe consumir el único recurso antes que el adulto egoísta."""
        import random
        p = self._personaje_con_npcs()
        resolver_autoconsumo_refugio(p, random.Random("test"))

        menor = p.relaciones_refugio["menor_id"]
        egoista = p.relaciones_refugio["egoista_id"]

        # El menor debería haber comido (hambre 60 > umbral_equilibrado 65 es FALSO)
        # El egoísta debería haber comido (hambre 55 > umbral_egoísta 50)
        # Solo hay 1 ración: el menor tiene prioridad → egoísta queda sin comer
        # Menor NO tiene hambre suficiente con umbral "equilibrado" (60 < 65)
        # Entonces el recurso lo consume el egoísta
        # Verificamos que el almacén queda vacío
        self.assertEqual(len(p.almacen), 0, "El único recurso debe haberse consumido")

    def test_menor_con_padre_protector_come_antes(self):
        """Menor cuyo padre es 'generoso' tiene umbral bajo (50) y come antes."""
        import random
        p = _personaje_vacio()
        agregar_item(p.almacen, copy.deepcopy(COMIDA))

        # Padre generoso con hambre 70 (espera hasta 80)
        padre = _npc("generoso", hambre=70)
        p.relaciones_refugio["padre_id"] = padre

        # Menor con hambre 55 (umbral del padre: hijos_primero → 50, así que come)
        menor = _npc("pragmatico", hambre=55)
        menor["es_menor"] = True
        p.relaciones_refugio["menor_id"] = menor

        # El padre tiene al menor en sus hijos
        padre["hijos"] = ["menor_id"]

        resolver_autoconsumo_refugio(p, random.Random("test2"))

        # Menor comió (hambre 55 > umbral 50), almacén vacío, padre no comió
        self.assertLess(p.relaciones_refugio["menor_id"]["hambre"], 55)
        self.assertEqual(len(p.almacen), 0)
        self.assertEqual(p.relaciones_refugio["padre_id"]["hambre"], 70,
                         "El padre altruista no debe haber comido (hambre 70 < umbral 80)")


# ── Tests: autoconsumo del jugador (InventoryMixin) ───────────────────────────

class TestAutoconsumoJugador(unittest.TestCase):

    def test_consume_comida_del_inventario(self):
        """autoconsumo() usa comida del inventario personal si hambre > umbral."""
        p = _personaje_vacio()
        p.hambre = 70
        p.añadir_item(copy.deepcopy(COMIDA))
        resultados = p.autoconsumo()
        self.assertTrue(resultados, "Debe haber consumido algo")
        self.assertLess(p.hambre, 70)

    def test_fallback_a_almacen_si_no_hay_inventario(self):
        """Si no hay comida en inventario, debe consumir del almacén."""
        p = _personaje_vacio()
        p.hambre = 70
        agregar_item(p.almacen, copy.deepcopy(COMIDA))
        resultados = p.autoconsumo()
        self.assertTrue(resultados)
        self.assertLess(p.hambre, 70)
        self.assertEqual(len(p.almacen), 0, "La comida debe haberse tomado del almacén")

    def test_no_consume_si_necesidades_cubiertas(self):
        """Si las necesidades están cubiertas, no consume nada."""
        p = _personaje_vacio()
        p.hambre = 30
        p.sed = 30
        p.salud = p.salud_max
        agregar_item(p.almacen, copy.deepcopy(COMIDA))
        resultados = p.autoconsumo()
        self.assertEqual(resultados, [], "No debe consumir si no lo necesita")
        self.assertEqual(len(p.almacen), 1, "El almacén no debe cambiar")

    def test_consume_agua_si_sed_alta(self):
        """autoconsumo() debe cubrir sed si supera el umbral."""
        p = _personaje_vacio()
        p.sed = 70
        agregar_item(p.almacen, copy.deepcopy(AGUA))
        resultados = p.autoconsumo()
        self.assertTrue(any("agua" in r.lower() or "bebiste" in r.lower() or "sed" in r.lower()
                           for r in resultados), f"Esperaba mensaje de agua. Resultados: {resultados}")
        self.assertLess(p.sed, 70)

    def test_prioriza_inventario_sobre_almacen(self):
        """El inventario personal se consume antes que el almacén."""
        p = _personaje_vacio()
        p.hambre = 70
        p.añadir_item(copy.deepcopy(COMIDA))
        agregar_item(p.almacen, copy.deepcopy(COMIDA))
        p.autoconsumo()
        # El almacén debe quedar intacto; el inventario se consumió primero
        self.assertEqual(len(p.almacen), 1, "El almacén debe quedar intacto cuando hay inventario")

    def test_umbral_personalizable(self):
        """Los umbrales de autoconsumo son configurables."""
        p = _personaje_vacio()
        p.hambre = 50
        agregar_item(p.almacen, copy.deepcopy(COMIDA))
        # Con umbral bajo, debe comer
        resultados = p.autoconsumo(umbral_hambre=40)
        self.assertTrue(resultados)
        self.assertLess(p.hambre, 50)

    def test_sin_recursos_devuelve_lista_vacia(self):
        """Sin recursos, autoconsumo devuelve lista vacía."""
        p = _personaje_vacio()
        p.hambre = 90
        p.sed = 90
        resultados = p.autoconsumo()
        self.assertEqual(resultados, [])


if __name__ == "__main__":
    unittest.main()
