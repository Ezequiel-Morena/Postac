"""Tests para los nuevos climas peligrosos (lluvia ácida, polvo tóxico, etc.)."""
import unittest

from data.clima import CLIMAS, ESTACIONES
from engine.clima import clima_actual, CLIMAS_PELIGROSOS, _PROTECCIONES_CLIMA


NUEVOS_CLIMAS_PELIGROSOS = ["lluvia_acida", "polvo_toxico", "ventisca_polar", "granizo_acido"]


class TestNewClimates(unittest.TestCase):

    def test_nuevos_climas_presentes_en_data(self):
        for clave in NUEVOS_CLIMAS_PELIGROSOS:
            self.assertIn(clave, CLIMAS, f"Clima '{clave}' debe estar en data/clima.py")

    def test_climas_peligrosos_tienen_riesgo_condicion(self):
        for clave in NUEVOS_CLIMAS_PELIGROSOS:
            clima = CLIMAS[clave]
            self.assertIn("riesgo_condicion", clima,
                          f"Clima '{clave}' debe tener campo riesgo_condicion")
            self.assertIn("prob_condicion", clima,
                          f"Clima '{clave}' debe tener campo prob_condicion")
            self.assertGreater(clima["prob_condicion"], 0.0)

    def test_climas_peligrosos_en_frozenset_engine(self):
        for clave in NUEVOS_CLIMAS_PELIGROSOS:
            self.assertIn(clave, CLIMAS_PELIGROSOS,
                          f"Clima '{clave}' debe estar en CLIMAS_PELIGROSOS del engine")

    def test_protecciones_definidas_para_climas_peligrosos(self):
        for clave in NUEVOS_CLIMAS_PELIGROSOS:
            self.assertIn(clave, _PROTECCIONES_CLIMA,
                          f"Debe haber protecciones definidas para '{clave}'")
            self.assertIsInstance(_PROTECCIONES_CLIMA[clave], (list, set, frozenset))

    def test_climas_presentes_en_todas_las_estaciones(self):
        """Los nuevos climas deben poder aparecer en al menos una estación."""
        todos_los_climas_en_estaciones = set()
        for estacion_data in ESTACIONES.values():
            for c in estacion_data.get("climas", []):
                todos_los_climas_en_estaciones.add(c["id"])
        for clave in NUEVOS_CLIMAS_PELIGROSOS:
            self.assertIn(clave, todos_los_climas_en_estaciones,
                          f"Clima '{clave}' no aparece en ninguna estación")

    def test_clima_actual_retorna_campos_peligroso(self):
        """clima_actual() con un clima peligroso debe retornar peligroso=True."""
        # Usar dia=100 (verano) donde polvo_toxico/lluvia_acida pueden aparecer
        # Forzamos el clima via seeding directo: buscamos un día donde aparezca lluvia_acida
        from data.clima import ESTACIONES, CLIMAS
        encontrado = None
        for dia in range(1, 91):  # primavera, lluvia_acida tiene peso 8
            resultado = clima_actual(dia=dia, hora=0)
            if resultado["clima_id"] == "lluvia_acida":
                encontrado = resultado
                break
        if encontrado is None:
            self.skipTest("No se encontró lluvia_acida en primavera con estos seeds")
        self.assertTrue(encontrado["peligroso"])
        self.assertIn("riesgo_condicion", encontrado)

    def test_clima_seguro_peligroso_false(self):
        # Buscamos un día con clima templado (no peligroso)
        for dia in range(1, 91):
            resultado = clima_actual(dia=dia, hora=0)
            if resultado["clima_id"] == "templado":
                self.assertFalse(resultado.get("peligroso", False))
                return
        self.skipTest("No se encontró clima templado en primavera con estos seeds")

    def test_tormenta_radiacion_tiene_riesgo_condicion(self):
        """tormenta_radiacion debe tener riesgo_condicion tras la expansión."""
        self.assertIn("riesgo_condicion", CLIMAS.get("tormenta_radiacion", {}))


if __name__ == "__main__":
    unittest.main()
