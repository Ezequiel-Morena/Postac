import unittest

from engine.personaje import Sobreviviente


class TestInventoryFilterNormalization(unittest.TestCase):
    def test_alias_arma_maps_to_armas(self):
        p = Sobreviviente()
        p.inventario.append(
            {
                "nombre": "Machete alias",
                "tipo": "arma_cortante",
                "peso": 1.2,
                "daño": (4, 8),
            }
        )

        filtro = p.normalizar_filtro_inventario("arma")
        filas = p.inventario_filtrado_ordenado(filtro=filtro, orden="id")

        self.assertEqual(filtro, "armas")
        self.assertTrue(any(it.get("nombre") == "Machete alias" for _, it, _ in filas))

    def test_unknown_filter_returns_none(self):
        p = Sobreviviente()
        self.assertIsNone(p.normalizar_filtro_inventario("nada_que_ver"))


if __name__ == "__main__":
    unittest.main()
