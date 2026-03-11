# ============================================================
# tests/test_emociones.py
# Tests para el sistema de ejes emocionales:
#   calidad_vinculo, procesar_duelo_npc, _aplicar_efectos con
#   amor/respeto/resentimiento, alertas de resentimiento alto,
#   condición quiere_irse por resentimiento acumulado.
# ============================================================

import copy
import unittest

from engine.personaje import Sobreviviente
from engine.familia import generar_npc, integrar_npc_en_refugio
from engine.relaciones import (
    calidad_vinculo,
    procesar_duelo_npc,
    _aplicar_efectos,
    _generar_alertas,
    _evaluar_tension_grupal,
    evaluar_reacciones_emocionales,
    _npc_estado_inicial,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _crear_personaje() -> Sobreviviente:
    p = Sobreviviente.__new__(Sobreviviente)
    p.nombre         = "Test"
    p.salud          = 80
    p.salud_max      = 100
    p.moral          = 60
    p.inventario     = []
    p.almacen        = []
    p.relaciones_refugio = {}
    p.animales_refugio   = []
    p.familia            = {}
    p.partida_id         = "test"
    p.dia                = 1
    p.hora               = 8
    return p


def _npc_con_ejes(amor=50, respeto=50, resentimiento=0, **kwargs) -> dict:
    base = {
        "nombre": "NPC", "rol": "superviviente", "personalidad": "neutro",
        "confianza": 50, "lealtad": 40, "tension": 25, "miedo": 0,
        "hambre": 35, "salud": 80, "en_expedicion": False, "dias_expedicion": 0,
        "veces_peleado": 0, "quiere_irse": False, "estado_relacion": "desconocido",
        "es_menor": False, "padres": [], "hijos": [], "pareja_id": None, "embarazo_ticks": 0,
        "amor": amor, "respeto": respeto, "resentimiento": resentimiento,
    }
    base.update(kwargs)
    return base


# ══════════════════════════════════════════════════════════════
#  calidad_vinculo
# ══════════════════════════════════════════════════════════════

class TestCalidadVinculo(unittest.TestCase):

    def test_vinculo_perfecto(self):
        estado = _npc_con_ejes(amor=100, respeto=100, resentimiento=0)
        self.assertEqual(calidad_vinculo(estado), 100)

    def test_vinculo_neutro(self):
        estado = _npc_con_ejes(amor=50, respeto=50, resentimiento=0)
        self.assertEqual(calidad_vinculo(estado), 50)

    def test_resentimiento_degrada(self):
        sin_resen = _npc_con_ejes(amor=80, respeto=80, resentimiento=0)
        con_resen = _npc_con_ejes(amor=80, respeto=80, resentimiento=60)
        self.assertGreater(calidad_vinculo(sin_resen), calidad_vinculo(con_resen))

    def test_resentimiento_maximo_baja_calidad(self):
        estado = _npc_con_ejes(amor=0, respeto=0, resentimiento=100)
        self.assertEqual(calidad_vinculo(estado), 0)

    def test_clamp_minimo_cero(self):
        # Mucho resentimiento no puede dar valor negativo
        estado = _npc_con_ejes(amor=10, respeto=10, resentimiento=100)
        self.assertGreaterEqual(calidad_vinculo(estado), 0)

    def test_defaults_sin_ejes(self):
        # Estado sin ejes emocionales debe usar defaults (50/50/0)
        estado = {"confianza": 60}
        self.assertEqual(calidad_vinculo(estado), 50)


# ══════════════════════════════════════════════════════════════
#  procesar_duelo_npc
# ══════════════════════════════════════════════════════════════

class TestProcesarDuelo(unittest.TestCase):

    def test_duelo_pareja_siempre_genera_mensaje(self):
        p = _crear_personaje()
        msgs = procesar_duelo_npc(p, "Ana", era_pareja=True, calidad=80)
        self.assertTrue(any("pareja" in m or "💔" in m for m in msgs))

    def test_duelo_vinculo_alto_genera_mensaje(self):
        p = _crear_personaje()
        msgs = procesar_duelo_npc(p, "Luis", era_pareja=False, calidad=85)
        self.assertTrue(len(msgs) > 0)

    def test_duelo_vinculo_medio_sin_mensaje_extra(self):
        # Calidad 40-74: sin mensaje extra (el mensaje estándar es suficiente)
        p = _crear_personaje()
        msgs = procesar_duelo_npc(p, "Luis", era_pareja=False, calidad=55)
        self.assertEqual(msgs, [])

    def test_duelo_vinculo_bajo_genera_mensaje_especial(self):
        p = _crear_personaje()
        msgs = procesar_duelo_npc(p, "Tóxico", era_pareja=False, calidad=15)
        self.assertTrue(len(msgs) > 0)

    def test_duelo_no_modifica_moral(self):
        # procesar_duelo no debe tocar moral (eso lo hace el código que llama)
        p = _crear_personaje()
        moral_antes = p.moral
        procesar_duelo_npc(p, "Alguien", era_pareja=False, calidad=90)
        self.assertEqual(p.moral, moral_antes)


# ══════════════════════════════════════════════════════════════
#  _aplicar_efectos con ejes emocionales
# ══════════════════════════════════════════════════════════════

class TestAplicarEfectosEmocionales(unittest.TestCase):

    def _personaje(self):
        return _crear_personaje()

    def test_evento_positivo_sube_amor_respeto(self):
        p = self._personaje()
        estado = _npc_con_ejes(amor=50, respeto=50, resentimiento=10)
        evento = {"id": "apoyo_emocional", "nombre": "x",
                  "efectos": {"amor": 10, "respeto": 5, "resentimiento": -5}}
        _aplicar_efectos(p, estado, evento)
        self.assertEqual(estado["amor"], 60)
        self.assertEqual(estado["respeto"], 55)
        self.assertEqual(estado["resentimiento"], 5)

    def test_evento_negativo_sube_resentimiento(self):
        p = self._personaje()
        estado = _npc_con_ejes(amor=50, respeto=50, resentimiento=0)
        evento = {"id": "traicion_pequena", "nombre": "x",
                  "efectos": {"amor": -12, "respeto": -15, "resentimiento": 18}}
        _aplicar_efectos(p, estado, evento)
        self.assertEqual(estado["amor"], 38)
        self.assertEqual(estado["respeto"], 35)
        self.assertEqual(estado["resentimiento"], 18)

    def test_clamp_amor_no_supera_100(self):
        p = self._personaje()
        estado = _npc_con_ejes(amor=98, respeto=50)
        evento = {"id": "x", "efectos": {"amor": 10}}
        _aplicar_efectos(p, estado, evento)
        self.assertEqual(estado["amor"], 100)

    def test_clamp_resentimiento_no_baja_de_0(self):
        p = self._personaje()
        estado = _npc_con_ejes(resentimiento=2)
        evento = {"id": "x", "efectos": {"resentimiento": -20}}
        _aplicar_efectos(p, estado, evento)
        self.assertEqual(estado["resentimiento"], 0)

    def test_evento_sin_ejes_no_modifica(self):
        p = self._personaje()
        estado = _npc_con_ejes(amor=50, respeto=50, resentimiento=5)
        evento = {"id": "dia_rutinario_sin_ejes", "efectos": {"moral": 1}}
        _aplicar_efectos(p, estado, evento)
        # Sin claves de ejes en efectos, no deben cambiar
        self.assertEqual(estado["amor"], 50)
        self.assertEqual(estado["respeto"], 50)
        self.assertEqual(estado["resentimiento"], 5)


# ══════════════════════════════════════════════════════════════
#  _generar_alertas: alerta de resentimiento
# ══════════════════════════════════════════════════════════════

class TestAlertaResentimiento(unittest.TestCase):

    def test_resentimiento_alto_genera_alerta(self):
        p = _crear_personaje()
        npc_id = "npc1"
        p.relaciones_refugio[npc_id] = _npc_con_ejes(resentimiento=75, nombre="Carlos")
        msgs = _generar_alertas(p)
        self.assertTrue(any("resentimiento" in m.lower() for m in msgs))

    def test_resentimiento_alto_baja_moral(self):
        p = _crear_personaje()
        p.moral = 60
        p.relaciones_refugio["npc1"] = _npc_con_ejes(resentimiento=80, nombre="Carlos")
        _generar_alertas(p)
        self.assertLess(p.moral, 60)

    def test_resentimiento_bajo_no_genera_alerta(self):
        p = _crear_personaje()
        p.relaciones_refugio["npc1"] = _npc_con_ejes(resentimiento=30, nombre="Elena")
        msgs = _generar_alertas(p)
        self.assertFalse(any("resentimiento" in m.lower() for m in msgs))

    def test_npc_en_expedicion_no_genera_alerta(self):
        p = _crear_personaje()
        p.relaciones_refugio["npc1"] = _npc_con_ejes(
            resentimiento=90, nombre="Ausente", en_expedicion=True
        )
        msgs = _generar_alertas(p)
        self.assertEqual(msgs, [])


# ══════════════════════════════════════════════════════════════
#  _evaluar_tension_grupal: quiere_irse por resentimiento
# ══════════════════════════════════════════════════════════════

class TestQiereIrseResentimiento(unittest.TestCase):

    def test_resentimiento_alto_activa_quiere_irse(self):
        import random as rnd_module
        p = _crear_personaje()
        p.relaciones_refugio["npc1"] = _npc_con_ejes(
            resentimiento=80, confianza=45, tension=20,
            nombre="Rebelde", rol="superviviente",
            veces_peleado=0,
        )
        rng = rnd_module.Random(42)
        _evaluar_tension_grupal(p, rng)
        estado = p.relaciones_refugio.get("npc1")
        # Puede que se haya ido (None) o tenga quiere_irse=True
        if estado is not None:
            self.assertTrue(estado.get("quiere_irse", False))

    def test_resentimiento_bajo_no_activa_quiere_irse(self):
        import random as rnd_module
        p = _crear_personaje()
        p.relaciones_refugio["npc1"] = _npc_con_ejes(
            resentimiento=20, confianza=60, tension=20,
            nombre="Amigable", rol="superviviente",
            veces_peleado=0,
        )
        rng = rnd_module.Random(42)
        _evaluar_tension_grupal(p, rng)
        estado = p.relaciones_refugio.get("npc1")
        if estado is not None:
            self.assertFalse(estado.get("quiere_irse", False))


# ══════════════════════════════════════════════════════════════
#  evaluar_reacciones_emocionales: resentimiento genera frialdad
# ══════════════════════════════════════════════════════════════

class TestReaccionesEmocionales(unittest.TestCase):

    def test_resentimiento_alto_puede_subir_tension(self):
        import random as rnd_module
        p = _crear_personaje()
        p.relaciones_refugio["npc1"] = _npc_con_ejes(
            resentimiento=80, confianza=40, tension=20, nombre="Frío"
        )
        # Forzar que rng.random() devuelva < 0.30 en la condición de frialdad
        rng = rnd_module.Random(1)
        msgs_o_tension = []
        # Ejecutar varias veces para asegurar que al menos alguna dispara el efecto
        for seed in range(20):
            p2 = _crear_personaje()
            p2.relaciones_refugio["npc1"] = _npc_con_ejes(
                resentimiento=80, confianza=40, tension=20, nombre="Frío"
            )
            r = rnd_module.Random(seed)
            msgs = evaluar_reacciones_emocionales(p2, r)
            if any("resentimiento" in m.lower() or "fría" in m.lower() for m in msgs):
                msgs_o_tension.append(True)
        self.assertTrue(len(msgs_o_tension) > 0, "Debería generar mensaje de frialdad con resentimiento alto")

    def test_resentimiento_bajo_no_genera_frialdad(self):
        import random as rnd_module
        p = _crear_personaje()
        p.relaciones_refugio["npc1"] = _npc_con_ejes(
            resentimiento=10, confianza=60, tension=20, nombre="Amigable"
        )
        rng = rnd_module.Random(42)
        msgs = evaluar_reacciones_emocionales(p, rng)
        self.assertFalse(any("fría" in m.lower() for m in msgs))


# ══════════════════════════════════════════════════════════════
#  _npc_estado_inicial: incluye ejes emocionales
# ══════════════════════════════════════════════════════════════

class TestNpcEstadoInicialEjes(unittest.TestCase):

    def test_incluye_amor_respeto_resentimiento(self):
        npc = {"nombre": "Test", "amor": 70, "respeto": 80, "resentimiento": 15}
        estado = _npc_estado_inicial(npc)
        self.assertEqual(estado["amor"], 70)
        self.assertEqual(estado["respeto"], 80)
        self.assertEqual(estado["resentimiento"], 15)

    def test_defaults_cuando_faltan(self):
        estado = _npc_estado_inicial({"nombre": "Nuevo"})
        self.assertEqual(estado["amor"], 50)
        self.assertEqual(estado["respeto"], 50)
        self.assertEqual(estado["resentimiento"], 0)

    def test_clamp_en_inicializacion(self):
        npc = {"nombre": "Extremo", "amor": 999, "respeto": -10, "resentimiento": 200}
        estado = _npc_estado_inicial(npc)
        self.assertEqual(estado["amor"], 100)
        self.assertEqual(estado["respeto"], 0)
        self.assertEqual(estado["resentimiento"], 100)


# ══════════════════════════════════════════════════════════════
#  generar_npc: incluye ejes emocionales
# ══════════════════════════════════════════════════════════════

class TestGenerarNpcEjes(unittest.TestCase):

    def test_npc_generado_tiene_ejes(self):
        p = _crear_personaje()
        npc = generar_npc("seed_test", p)
        self.assertIn("amor", npc)
        self.assertIn("respeto", npc)
        self.assertIn("resentimiento", npc)

    def test_npc_generado_valores_base(self):
        p = _crear_personaje()
        npc = generar_npc("seed_test", p)
        self.assertEqual(npc["amor"], 50)
        self.assertEqual(npc["respeto"], 50)
        self.assertEqual(npc["resentimiento"], 0)


# ══════════════════════════════════════════════════════════════
#  Integración: EVENTOS_REFUGIO con deltas emocionales
# ══════════════════════════════════════════════════════════════

class TestEventosConEjes(unittest.TestCase):

    def test_todos_los_eventos_tienen_ejes(self):
        from data.relaciones import EVENTOS_REFUGIO
        for evento in EVENTOS_REFUGIO:
            efectos = evento.get("efectos", {})
            self.assertIn("amor", efectos, f"Falta 'amor' en evento {evento['id']}")
            self.assertIn("respeto", efectos, f"Falta 'respeto' en evento {evento['id']}")
            self.assertIn("resentimiento", efectos, f"Falta 'resentimiento' en evento {evento['id']}")

    def test_eventos_positivos_suben_amor_respeto(self):
        from data.relaciones import EVENTOS_REFUGIO
        eventos_positivos = {"apoyo_emocional", "rescate_npc", "recuerdo_compartido", "cuidado_a_enfermo"}
        for evento in EVENTOS_REFUGIO:
            if evento["id"] in eventos_positivos:
                efectos = evento["efectos"]
                self.assertGreater(efectos["amor"], 0, f"{evento['id']}: amor debería subir")
                self.assertGreater(efectos["respeto"], 0, f"{evento['id']}: respeto debería subir")

    def test_eventos_negativos_suben_resentimiento(self):
        from data.relaciones import EVENTOS_REFUGIO
        eventos_negativos = {"traicion_pequena", "conflicto_violento", "amago_de_irse"}
        for evento in EVENTOS_REFUGIO:
            if evento["id"] in eventos_negativos:
                efectos = evento["efectos"]
                self.assertGreater(efectos["resentimiento"], 0, f"{evento['id']}: resentimiento debería subir")
                self.assertLess(efectos["amor"], 0, f"{evento['id']}: amor debería bajar")


if __name__ == "__main__":
    unittest.main()
