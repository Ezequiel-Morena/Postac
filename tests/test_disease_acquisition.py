"""Tests para el sistema de adquisición dinámica de condiciones (evaluar_adquisicion_condiciones)."""
import unittest

from engine.personaje import Sobreviviente
from engine.medical_system import (
    evaluar_adquisicion_condiciones,
    adquirir_condicion_por_consumo,
    aplicar_condiciones_cronicas_tick,
)


def _personaje_limpio() -> Sobreviviente:
    p = Sobreviviente()
    p.rasgos.clear()
    p.condiciones_cronicas = [c for c in p.condiciones_cronicas if c.get("origen") == "hereditario"]
    return p


class TestDiseaseAcquisition(unittest.TestCase):

    def test_radiation_triggers_envenenamiento(self):
        p = _personaje_limpio()
        p.radiacion = 75

        # Forzar adquisición directa (sin probabilidad aleatoria)
        msgs = adquirir_condicion_por_consumo(p, "envenenamiento_radiacion", "test")
        self.assertTrue(any(msgs), "Debe añadir condición de envenenamiento por radiación")
        claves = [c["clave"] for c in p.condiciones_cronicas]
        self.assertIn("envenenamiento_radiacion", claves)

    def test_no_duplicate_condition(self):
        p = _personaje_limpio()
        adquirir_condicion_por_consumo(p, "sepsis", "test_1")
        adquirir_condicion_por_consumo(p, "sepsis", "test_2")  # segunda vez: ignorar
        count = sum(1 for c in p.condiciones_cronicas if c["clave"] == "sepsis")
        self.assertEqual(count, 1, "No debe duplicarse la misma condición crónica")

    def test_agua_contaminada_puede_intoxicar(self):
        """Consumir agua_contaminada con prob=1 debe añadir intoxicacion_alimentaria."""
        from data.items import ITEMS
        p = _personaje_limpio()
        p.sed = 50  # sed > 0 para que el efecto se aplique
        from unittest.mock import patch
        item = dict(ITEMS["agua_contaminada"])
        item["usos"] = 2
        p.inventario.append(item)
        with patch("random.random", return_value=0.0):  # siempre menor que prob
            ok, msg = p.usar_item("Agua contaminada")
        self.assertTrue(ok, f"El ítem debe consumirse. msg={msg}")
        claves = [c["clave"] for c in p.condiciones_cronicas]
        self.assertIn("intoxicacion_alimentaria", claves)

    def test_carne_cruda_puede_intoxicar(self):
        from data.items import ITEMS
        from unittest.mock import patch
        p = _personaje_limpio()
        p.hambre = 50  # hambre > 0 para que el efecto se aplique
        item = dict(ITEMS["carne_cruda"])
        item["usos"] = 2
        p.inventario.append(item)
        with patch("random.random", return_value=0.0):
            ok, msg = p.usar_item("Carne cruda")
        self.assertTrue(ok, f"El ítem debe consumirse. msg={msg}")
        claves = [c["clave"] for c in p.condiciones_cronicas]
        self.assertIn("intoxicacion_alimentaria", claves)

    def test_condicion_causa_daño_en_tick(self):
        p = _personaje_limpio()
        adquirir_condicion_por_consumo(p, "sepsis", "test")
        salud_antes = p.salud
        aplicar_condiciones_cronicas_tick(p, horas=4.0)
        self.assertLess(p.salud, salud_antes, "Sepsis debe reducir salud por tick")

    def test_metabolismo_rapido_recupera_condicion_adquirida(self):
        """El rasgo metabolismo_rapido (recuperacion_condicion_mult=1.30) debe reducir severidad."""
        p = _personaje_limpio()
        # Añadir condición adquirida con severidad 0.5 (ya casi curada)
        p.condiciones_cronicas.append({
            "clave":     "agotamiento_profundo",
            "nombre":    "Agotamiento Profundo",
            "origen":    "fatiga_critica_sostenida",  # adquirida, no hereditaria
            "severidad": 0.5,
            "efectos":   {},
        })
        p.rasgos.append("metabolismo_rapido")
        # Con mult=1.30 y horas=6, recuperacion_tick = (1.3-1)*6*0.5 = 0.9 > 0.5 → debe removerse
        aplicar_condiciones_cronicas_tick(p, horas=6.0)
        claves = [c["clave"] for c in p.condiciones_cronicas]
        self.assertNotIn("agotamiento_profundo", claves, "Condición adquirida debe resolverse")

    def test_evaluar_condicion_no_duplica_en_multiples_ticks(self):
        p = _personaje_limpio()
        p.fatiga = 95
        evaluar_adquisicion_condiciones(p, horas=6.0, clima_id="ninguno")
        evaluar_adquisicion_condiciones(p, horas=6.0, clima_id="ninguno")
        count = sum(1 for c in p.condiciones_cronicas if c["clave"] == "agotamiento_profundo")
        self.assertLessEqual(count, 1, "No debe duplicar condición aunque se llame varias veces")


if __name__ == "__main__":
    unittest.main()
