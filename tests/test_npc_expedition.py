"""Tests para el sistema de expediciones autónomas de NPCs."""
import unittest

from engine.personaje import Sobreviviente
from engine.relaciones import (
    estado_relaciones_refugio_base,
    tick_refugio,
    generar_superviviente_aleatorio,
    integrar_nuevo_miembro,
    _npc_puede_salir,
)
from engine.familia import generar_npc, integrar_npc_en_refugio


def _personaje() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.relaciones_refugio = {}
    return p


def _personaje_con_npc() -> Sobreviviente:
    p = _personaje()
    npc = generar_npc("seed_exp_test", p)
    integrar_npc_en_refugio(p, npc)
    return p


class TestNPCExpeditionFields(unittest.TestCase):
    """Los campos de autonomía deben existir en NPCs generados."""

    def test_refugio_base_vacio(self):
        estado = estado_relaciones_refugio_base()
        self.assertEqual(estado, {})

    def test_npc_generado_tiene_campos_autonomia(self):
        npc = generar_npc("seed_autonomia", Sobreviviente())
        campos = ("en_expedicion", "dias_expedicion", "veces_peleado", "quiere_irse")
        for campo in campos:
            self.assertIn(campo, npc, f"NPC generado falta campo '{campo}'")

    def test_npc_generado_tiene_puede_expedicion(self):
        """Roles de exploración deben generar NPCs con puede_expedicion=True."""
        from data.familia import ROLES_EXPEDICION
        found = False
        for i in range(20):
            npc = generar_npc(f"seed_exp_{i}", Sobreviviente(), rol="cazador")
            if npc.get("puede_expedicion"):
                found = True
                break
        self.assertTrue(found, "Un cazador debe tener puede_expedicion=True")


class TestNPCPuedeExpedicion(unittest.TestCase):

    def _npc_apto(self) -> dict:
        return {
            "nombre": "Tester", "apellido": "X",
            "salud": 80, "hambre": 50,
            "en_expedicion": False, "dias_expedicion": 0,
            "veces_peleado": 0, "quiere_irse": False,
            "confianza": 60, "personalidad": "valiente",
            "puede_expedicion": True,
        }

    def test_npc_enfermo_no_puede_salir(self):
        p = _personaje()
        npc = self._npc_apto()
        npc["salud"] = 30
        self.assertFalse(_npc_puede_salir(npc, p))

    def test_npc_con_hambre_critica_no_puede_salir(self):
        p = _personaje()
        npc = self._npc_apto()
        npc["hambre"] = 85
        self.assertFalse(_npc_puede_salir(npc, p))

    def test_npc_en_expedicion_no_puede_salir(self):
        p = _personaje()
        npc = self._npc_apto()
        npc["en_expedicion"] = True
        self.assertFalse(_npc_puede_salir(npc, p))

    def test_npc_sano_puede_salir(self):
        p = _personaje()
        npc = self._npc_apto()
        self.assertTrue(_npc_puede_salir(npc, p))


class TestGenerarSupervivienteAleatorio(unittest.TestCase):

    def test_genera_npc_valido(self):
        p = _personaje()
        npc = generar_superviviente_aleatorio("seed_test_001", p)
        self.assertIsNotNone(npc)
        self.assertIn("nombre", npc)
        self.assertIn("rol", npc)

    def test_genera_npcs_variados(self):
        p = _personaje()
        nombres = {
            generar_superviviente_aleatorio(f"s{i}", p)["nombre"]
            for i in range(15)
        }
        self.assertGreater(len(nombres), 1)

    def test_genera_npc_aunque_haya_colision_de_nombre(self):
        """El sistema de IDs (nombre_apellido + sufijo) permite siempre generar un NPC único."""
        p = _personaje()
        # Agregar muchos NPCs — el generador debe seguir funcionando con IDs únicos
        from engine.familia import integrar_npc_en_refugio
        for i in range(20):
            npc = generar_superviviente_aleatorio(f"seed_col_{i}", p)
            if npc:
                integrar_npc_en_refugio(p, npc)
        resultado = generar_superviviente_aleatorio("seed_final", p)
        self.assertIsNotNone(resultado)
        self.assertIn("nombre", resultado)


class TestIntegrarNuevoMiembro(unittest.TestCase):

    def test_integrar_npc_aparece_en_refugio(self):
        p = _personaje()
        npc = generar_npc("seed_integrar", p)
        msg = integrar_nuevo_miembro(p, npc)
        self.assertEqual(len(p.relaciones_refugio), 1)
        self.assertIsInstance(msg, str)

    def test_nuevo_miembro_llega_con_confianza_baja(self):
        p = _personaje()
        npc = generar_npc("seed_conf_baja", p)
        # Forzar confianza alta en el NPC generado para verificar la penalización
        npc["confianza"] = 60
        integrar_nuevo_miembro(p, npc)
        npc_id = list(p.relaciones_refugio.keys())[0]
        self.assertLess(p.relaciones_refugio[npc_id]["confianza"], 60)

    def test_nuevo_miembro_llega_hambriento(self):
        p = _personaje()
        npc = generar_npc("seed_hambre", p)
        npc["hambre"] = 40
        integrar_nuevo_miembro(p, npc)
        npc_id = list(p.relaciones_refugio.keys())[0]
        self.assertGreater(p.relaciones_refugio[npc_id]["hambre"], 40)


class TestTickConExpedicion(unittest.TestCase):

    def test_tick_con_npc_en_expedicion(self):
        p = _personaje_con_npc()
        primer_npc = list(p.relaciones_refugio.keys())[0]
        p.relaciones_refugio[primer_npc]["en_expedicion"] = True
        p.relaciones_refugio[primer_npc]["dias_expedicion"] = 3
        msgs = tick_refugio(p, horas=8)
        self.assertIsInstance(msgs, list)

    def test_tick_refugio_vacio_no_falla(self):
        p = _personaje()
        msgs = tick_refugio(p, horas=6)
        self.assertIsInstance(msgs, list)
        self.assertEqual(msgs, [])


if __name__ == "__main__":
    unittest.main()



def _personaje() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.relaciones_refugio = estado_relaciones_refugio_base()
    return p


if __name__ == "__main__":
    unittest.main()
