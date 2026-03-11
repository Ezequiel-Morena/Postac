import unittest

from engine.mundo import _contexto_area, _score_item_contextual
from data.items import ITEMS


class TestContextualLoot(unittest.TestCase):
    def test_hospital_prefers_medicine_over_weapons(self):
        area = {"area_key": "hospital", "nombre": "Hospital", "tags": ["medico", "interior"]}
        ctx = _contexto_area(area)

        score_med = _score_item_contextual(ITEMS["botiquin"], ctx)
        score_arma = _score_item_contextual(ITEMS["escopeta"], ctx)
        self.assertGreater(score_med, score_arma)

    def test_comisaria_prefers_weapons_over_food(self):
        area = {"area_key": "comisaria", "nombre": "Comisaría", "tags": ["armas", "interior"]}
        ctx = _contexto_area(area)

        score_arma = _score_item_contextual(ITEMS["pistola_9mm"], ctx)
        score_food = _score_item_contextual(ITEMS["lata_frijoles"], ctx)
        self.assertGreater(score_arma, score_food)


if __name__ == "__main__":
    unittest.main()
