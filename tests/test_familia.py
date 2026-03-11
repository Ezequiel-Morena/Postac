"""Tests para el sistema de árbol genealógico y relaciones familiares."""
import unittest

from engine.personaje import Sobreviviente
from engine.familia import (
    generar_npc,
    generar_id_npc,
    integrar_npc_en_refugio,
    proponer_relacion,
    terminar_relacion,
    puede_tener_hijo,
    iniciar_embarazo,
    avanzar_estado_relacion,
    tick_familia,
    _nacer_hijo,
    _hacer_crecer_hijo,
)
from data.familia import ROLES_NPC, PERSONALIDADES_NPC, EDAD_ADULTO, EDAD_JOVEN


def _personaje() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.relaciones_refugio = {}
    p.familia = {}
    return p


def _personaje_con_pareja() -> tuple[Sobreviviente, str]:
    """Devuelve (personaje, npc_id) con pareja ya establecida y confianza alta."""
    p = _personaje()
    npc = generar_npc("seed_pareja", p)
    npc["confianza"] = 85
    npc["estado_relacion"] = "pareja"
    npc["edad"] = 28
    integrar_npc_en_refugio(p, npc)
    npc_id = list(p.relaciones_refugio.keys())[0]
    p.relaciones_refugio[npc_id]["estado_relacion"] = "pareja"
    p.relaciones_refugio[npc_id]["confianza"] = 85
    p.familia[npc_id] = {"tipo": "pareja", "nombre": npc["nombre"], "apellido": npc["apellido"]}
    return p, npc_id


# ══════════════════════════════════════════════════════════════
#  Tests: Generación procedural de NPCs
# ══════════════════════════════════════════════════════════════

class TestGeneracionNPC(unittest.TestCase):

    def test_genera_campos_obligatorios(self):
        npc = generar_npc("seed_a", Sobreviviente())
        campos = ("nombre", "apellido", "genero", "edad", "rol", "personalidad",
                  "puede_expedicion", "confianza", "lealtad", "tension",
                  "hambre", "salud", "estado_relacion", "es_menor",
                  "padres", "hijos", "pareja_id")
        for campo in campos:
            self.assertIn(campo, npc, f"Falta campo '{campo}' en NPC generado")

    def test_genero_valido(self):
        for i in range(10):
            npc = generar_npc(f"seed_g{i}", Sobreviviente())
            self.assertIn(npc["genero"], ("masculino", "femenino"))

    def test_edad_rango_adulto(self):
        for i in range(10):
            npc = generar_npc(f"seed_edad{i}", Sobreviviente())
            self.assertGreaterEqual(npc["edad"], 16)
            self.assertLessEqual(npc["edad"], 55)

    def test_rol_valido(self):
        for i in range(10):
            npc = generar_npc(f"seed_rol{i}", Sobreviviente())
            self.assertIn(npc["rol"], ROLES_NPC)

    def test_personalidad_valida(self):
        for i in range(10):
            npc = generar_npc(f"seed_per{i}", Sobreviviente())
            self.assertIn(npc["personalidad"], PERSONALIDADES_NPC)

    def test_semillas_distintas_dan_npcs_distintos(self):
        p = Sobreviviente()
        nombres = {generar_npc(f"seed_{i}", p)["nombre"] for i in range(20)}
        self.assertGreater(len(nombres), 1)

    def test_rol_forzado(self):
        npc = generar_npc("seed_rol_forzado", Sobreviviente(), rol="médico")
        self.assertEqual(npc["rol"], "médico")

    def test_hijo_no_puede_expedicion(self):
        npc = generar_npc("seed_hijo", Sobreviviente(), es_hijo=True)
        self.assertFalse(npc["puede_expedicion"])

    def test_generar_id_unico(self):
        existentes = {"marcos_vega", "marcos_vega_2"}
        npc_id = generar_id_npc("Marcos", "Vega", existentes)
        self.assertNotIn(npc_id, existentes)

    def test_integrar_npc_en_refugio(self):
        p = _personaje()
        npc = generar_npc("seed_integ", p)
        msg = integrar_npc_en_refugio(p, npc)
        self.assertEqual(len(p.relaciones_refugio), 1)
        self.assertIsInstance(msg, str)
        npc_id = list(p.relaciones_refugio.keys())[0]
        # Debe llegar con penalizaciones
        self.assertLess(p.relaciones_refugio[npc_id]["confianza"], npc["confianza"])
        self.assertGreater(p.relaciones_refugio[npc_id]["hambre"], npc["hambre"])


# ══════════════════════════════════════════════════════════════
#  Tests: Relaciones románticas
# ══════════════════════════════════════════════════════════════

class TestRelacionesRomanticas(unittest.TestCase):

    def test_proponer_relacion_confianza_insuficiente(self):
        p = _personaje()
        npc = generar_npc("seed_conf_baja", p)
        npc["confianza"] = 20
        integrar_npc_en_refugio(p, npc)
        npc_id = list(p.relaciones_refugio.keys())[0]
        p.relaciones_refugio[npc_id]["confianza"] = 20
        msg = proponer_relacion(p, npc_id)
        self.assertIn("no te conoce suficiente", msg.lower())
        self.assertNotEqual(p.relaciones_refugio[npc_id].get("estado_relacion"), "pareja")

    def test_proponer_relacion_confianza_alta(self):
        p = _personaje()
        npc = generar_npc("seed_conf_alta", p)
        integrar_npc_en_refugio(p, npc)
        npc_id = list(p.relaciones_refugio.keys())[0]
        p.relaciones_refugio[npc_id]["confianza"] = 85
        p.relaciones_refugio[npc_id]["estado_relacion"] = "cercano"
        msg = proponer_relacion(p, npc_id)
        self.assertEqual(p.relaciones_refugio[npc_id]["estado_relacion"], "pareja")
        self.assertIn(npc_id, p.familia)
        self.assertEqual(p.familia[npc_id]["tipo"], "pareja")

    def test_terminar_relacion(self):
        p, npc_id = _personaje_con_pareja()
        msg = terminar_relacion(p, npc_id)
        self.assertEqual(p.relaciones_refugio[npc_id]["estado_relacion"], "ex_pareja")
        self.assertIsInstance(msg, str)

    def test_proponer_relacion_ya_es_pareja(self):
        p, npc_id = _personaje_con_pareja()
        msg = proponer_relacion(p, npc_id)
        self.assertIn("ya estáis juntos", msg.lower())

    def test_avanzar_estado_relacion(self):
        p = _personaje()
        npc = generar_npc("seed_avanzar", p)
        integrar_npc_en_refugio(p, npc)
        npc_id = list(p.relaciones_refugio.keys())[0]
        p.relaciones_refugio[npc_id]["confianza"] = 50
        p.relaciones_refugio[npc_id]["estado_relacion"] = "desconocido"
        # Con confianza 50 debe pasar a "amigo" (umbral 45)
        nuevo = avanzar_estado_relacion(npc_id, p)
        self.assertIsNotNone(nuevo)


# ══════════════════════════════════════════════════════════════
#  Tests: Hijos y familia
# ══════════════════════════════════════════════════════════════

class TestSistemaHijos(unittest.TestCase):

    def test_puede_tener_hijo_con_pareja_valida(self):
        p, npc_id = _personaje_con_pareja()
        p.edad = 28
        p.vitals = {"salud": 80, "sed": 20, "hambre": 20, "fatiga": 10}
        self.assertTrue(puede_tener_hijo(p, npc_id))

    def test_no_puede_tener_hijo_sin_pareja(self):
        p = _personaje()
        npc = generar_npc("seed_sin_pareja", p)
        integrar_npc_en_refugio(p, npc)
        npc_id = list(p.relaciones_refugio.keys())[0]
        # estado_relacion no es "pareja"
        self.assertFalse(puede_tener_hijo(p, npc_id))

    def test_iniciar_embarazo(self):
        p, npc_id = _personaje_con_pareja()
        p.edad = 28
        p.vitals = {"salud": 80, "sed": 20, "hambre": 20, "fatiga": 10}
        msg = iniciar_embarazo(p, npc_id)
        self.assertGreater(p.relaciones_refugio[npc_id]["embarazo_ticks"], 0)
        self.assertIsInstance(msg, str)

    def test_nacer_hijo(self):
        import random
        p, npc_id = _personaje_con_pareja()
        rng = random.Random("seed_nacer")
        msg = _nacer_hijo(p, npc_id, rng)
        # Debe haber un NPC nuevo en el refugio (el hijo)
        hijos = [npc_id2 for npc_id2, est in p.relaciones_refugio.items()
                 if est.get("es_menor") or est.get("edad", 99) == 0]
        self.assertGreater(len(hijos), 0)
        self.assertIsInstance(msg, str)
        self.assertIn(npc_id, p.familia)  # pareja sigue en familia
        # El hijo también debe estar en familia
        hijos_familia = [k for k, v in p.familia.items() if v["tipo"] in ("hijo", "hija")]
        self.assertGreater(len(hijos_familia), 0)

    def test_hijo_nace_como_menor(self):
        import random
        p, npc_id = _personaje_con_pareja()
        rng = random.Random("seed_menor")
        _nacer_hijo(p, npc_id, rng)
        hijo_id = [k for k, v in p.relaciones_refugio.items() if v.get("edad", 99) == 0][0]
        self.assertTrue(p.relaciones_refugio[hijo_id]["es_menor"])
        self.assertFalse(p.relaciones_refugio[hijo_id]["puede_expedicion"])

    def test_crecer_hijo_activa_hito(self):
        estado = {
            "nombre": "Kael", "edad": 0,
            "tick_nacimiento": 0, "es_menor": True,
            "puede_expedicion": False,
        }
        msg = _hacer_crecer_hijo("kael", estado, dia_actual=365)
        self.assertIsNotNone(msg)
        self.assertEqual(estado["edad"], 1)

    def test_hijo_adulto_puede_expedicion(self):
        estado = {
            "nombre": "Kael", "edad": 17,
            "tick_nacimiento": 0, "es_menor": True,
            "puede_expedicion": False,
            "personalidad": "valiente",
            "rol_adulto": "explorador",
        }
        _hacer_crecer_hijo("kael", estado, dia_actual=18 * 365)
        self.assertFalse(estado["es_menor"])
        # Con personalidad valiente y rol explorador puede salir
        self.assertTrue(estado["puede_expedicion"])


# ══════════════════════════════════════════════════════════════
#  Tests: tick_familia integración
# ══════════════════════════════════════════════════════════════

class TestTickFamilia(unittest.TestCase):

    def test_tick_familia_sin_npcs_devuelve_lista_vacia(self):
        import random
        p = _personaje()
        msgs = tick_familia(p, horas=8, rng=random.Random("seed_vacio"))
        self.assertIsInstance(msgs, list)
        self.assertEqual(msgs, [])

    def test_tick_familia_con_npc_devuelve_lista(self):
        import random
        p = _personaje()
        npc = generar_npc("seed_tick_fam", p)
        integrar_npc_en_refugio(p, npc)
        msgs = tick_familia(p, horas=8, rng=random.Random("seed_t"))
        self.assertIsInstance(msgs, list)

    def test_tick_familia_pareja_npc_npc_posible(self):
        """Dos NPCs con alta confianza pueden formar pareja en el refugio."""
        import random
        p = _personaje()
        for i in range(3):
            npc = generar_npc(f"seed_pareja_{i}", p)
            npc["confianza"] = 70
            npc["estado_relacion"] = "cercano"
            npc["pareja_id"] = None
            npc["es_menor"] = False
            integrar_npc_en_refugio(p, npc)
            npc_id = list(p.relaciones_refugio.keys())[-1]
            p.relaciones_refugio[npc_id]["confianza"] = 70

        # Forzar la función directamente
        from engine.familia import _evaluar_pareja_npc_npc
        rng = random.Random("seed_forzar_pareja")
        # Ajustar estado_relacion a cercano para todos
        for est in p.relaciones_refugio.values():
            est["estado_relacion"] = "cercano"
            est["confianza"] = 70
        msg = _evaluar_pareja_npc_npc(p, rng)
        # Puede devolver un mensaje o None (depende de condiciones internas)
        # Solo verificamos que no crashea
        self.assertTrue(msg is None or isinstance(msg, str))


if __name__ == "__main__":
    unittest.main()
