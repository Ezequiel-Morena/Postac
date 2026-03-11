"""Tests para engine/temperatura.py — motor de temperatura corporal."""
import pytest
from engine.temperatura import (
    aislamiento_efectivo,
    calcular_temp_corporal,
    efectos_temperatura,
    evaluar_congelacion,
    actualizar_humedad_ropa,
    desgastar_ropa,
    impermeabilidad_total,
    temperatura_sensacion,
    TEMP_CORPORAL_NORMAL,
    HIPOTERMIA_LEVE,
    HIPERTERMIA_LEVE,
)
from data.vestimenta import PRENDAS


# ── Helpers ───────────────────────────────────────────────────

def _prenda(key: str) -> dict:
    """Devuelve una copia de la prenda con durabilidad actual."""
    import copy
    p = copy.deepcopy(PRENDAS[key])
    p["durabilidad"] = p.get("durabilidad_max", 100)
    return p


def _ropa_completa() -> dict:
    """Conjunto completo de ropa de abrigo."""
    return {
        "cabeza": _prenda("gorro_lana"),
        "torso": _prenda("jersey_lana"),
        "piernas": _prenda("pantalon_cuero"),
        "pies": _prenda("botas_cuero"),
        "manos": _prenda("guantes_cuero"),
        "capa_exterior": _prenda("abrigo_invierno"),
    }


# ── temperatura_sensacion ────────────────────────────────────

class TestTemperaturaSensacion:
    def test_sin_viento_sin_humedad(self):
        """Sin factores extra, temperatura sensación ≈ temperatura ambiente."""
        ts = temperatura_sensacion(20.0, 0, 40)
        assert abs(ts - 20.0) < 2.0

    def test_wind_chill_bajo_cero(self):
        """El viento a temperaturas bajas reduce la sensación térmica."""
        ts = temperatura_sensacion(-5.0, 30, 50)
        assert ts < -5.0

    def test_heat_index_calor(self):
        """Alta humedad con calor eleva la sensación térmica."""
        ts = temperatura_sensacion(35.0, 5, 80)
        assert ts > 35.0


# ── aislamiento_efectivo ─────────────────────────────────────

class TestAislamientoEfectivo:
    def test_sin_ropa(self):
        assert aislamiento_efectivo({}, 0.0, True) == 0.0

    def test_con_ropa_seca(self):
        ropa = _ropa_completa()
        aisl = aislamiento_efectivo(ropa, 0.0, True)
        assert aisl > 30.0  # un conjunto completo aísla significativamente

    def test_ropa_mojada_reduce_aislamiento(self):
        ropa = _ropa_completa()
        aisl_seca = aislamiento_efectivo(ropa, 0.0, True)
        aisl_mojada = aislamiento_efectivo(ropa, 80.0, True)
        assert aisl_mojada < aisl_seca

    def test_lana_resiste_humedad(self):
        """La lana pierde menos aislamiento al mojarse que el algodón."""
        gorro_lana = {"cabeza": _prenda("gorro_lana")}
        camiseta = {"torso": _prenda("camiseta_algodon")}
        aisl_lana_seca = aislamiento_efectivo(gorro_lana, 0.0, True)
        aisl_lana_mojada = aislamiento_efectivo(gorro_lana, 100.0, True)
        aisl_algodon_seca = aislamiento_efectivo(camiseta, 0.0, True)
        aisl_algodon_mojada = aislamiento_efectivo(camiseta, 100.0, True)
        ratio_lana = aisl_lana_mojada / max(aisl_lana_seca, 0.01)
        ratio_algodon = aisl_algodon_mojada / max(aisl_algodon_seca, 0.01)
        assert ratio_lana > ratio_algodon


# ── calcular_temp_corporal ───────────────────────────────────

class TestCalcularTempCorporal:
    def test_normal_en_refugio(self):
        """En refugio con temperatura moderada, la temp corporal se mantiene estable."""
        nueva, msgs = calcular_temp_corporal(
            temp_actual=36.5, temp_ambiente=20.0, viento_kmh=5,
            humedad_rel=40, ropa_equipada=_ropa_completa(), humedad_ropa=0.0,
            fuego_activo=False, en_refugio=True, horas=6,
        )
        assert abs(nueva - TEMP_CORPORAL_NORMAL) < 2.0

    def test_hipotermia_exterior_frio_sin_ropa(self):
        """Sin ropa en frío extremo, la temperatura corporal cae."""
        nueva, msgs = calcular_temp_corporal(
            temp_actual=36.5, temp_ambiente=-15.0, viento_kmh=25,
            humedad_rel=60, ropa_equipada={}, humedad_ropa=0.0,
            fuego_activo=False, en_refugio=False, horas=4,
        )
        assert nueva < HIPOTERMIA_LEVE

    def test_ropa_protege_del_frio(self):
        """Con ropa adecuada, la caída de temp es menor."""
        ropa = _ropa_completa()
        temp_sin, _ = calcular_temp_corporal(
            temp_actual=36.5, temp_ambiente=-5.0, viento_kmh=15,
            humedad_rel=50, ropa_equipada={}, humedad_ropa=0.0,
            fuego_activo=False, en_refugio=False, horas=3,
        )
        temp_con, _ = calcular_temp_corporal(
            temp_actual=36.5, temp_ambiente=-5.0, viento_kmh=15,
            humedad_rel=50, ropa_equipada=ropa, humedad_ropa=0.0,
            fuego_activo=False, en_refugio=False, horas=3,
        )
        assert temp_con > temp_sin

    def test_fuego_calienta(self):
        """El fuego activo sube la temperatura efectiva."""
        temp_sin, _ = calcular_temp_corporal(
            temp_actual=36.5, temp_ambiente=5.0, viento_kmh=10,
            humedad_rel=50, ropa_equipada={}, humedad_ropa=0.0,
            fuego_activo=False, en_refugio=True, horas=3,
        )
        temp_con, _ = calcular_temp_corporal(
            temp_actual=36.5, temp_ambiente=5.0, viento_kmh=10,
            humedad_rel=50, ropa_equipada={}, humedad_ropa=0.0,
            fuego_activo=True, en_refugio=True, horas=3,
        )
        assert temp_con > temp_sin

    def test_hipertermia_calor_extremo(self):
        """En calor extremo prolongado, la temperatura corporal sube."""
        nueva, msgs = calcular_temp_corporal(
            temp_actual=37.5, temp_ambiente=48.0, viento_kmh=5,
            humedad_rel=70, ropa_equipada={}, humedad_ropa=0.0,
            fuego_activo=False, en_refugio=False, horas=6,
        )
        assert nueva > HIPERTERMIA_LEVE


# ── efectos_temperatura ──────────────────────────────────────

class TestEfectosTemperatura:
    def test_normal_sin_efectos(self):
        efx = efectos_temperatura(36.5, 3)
        assert not efx or all(v == 0 for v in efx.values())

    def test_hipotermia_dano(self):
        efx = efectos_temperatura(33.0, 3)
        assert efx.get("salud", 0) < 0

    def test_hipertermia_sed(self):
        efx = efectos_temperatura(40.0, 3)
        assert efx.get("sed", 0) > 0 or efx.get("salud", 0) < 0


# ── actualizar_humedad_ropa ──────────────────────────────────

class TestHumedadRopa:
    def test_lluvia_aumenta_humedad(self):
        h = actualizar_humedad_ropa(0.0, "lluvia", 30, False, False, 3)
        assert h > 0

    def test_refugio_seca_ropa(self):
        h = actualizar_humedad_ropa(80.0, "templado", 50, True, False, 6)
        assert h < 80.0

    def test_fuego_seca_mas_rapido(self):
        h_sin = actualizar_humedad_ropa(80.0, "templado", 50, True, False, 6)
        h_con = actualizar_humedad_ropa(80.0, "templado", 50, True, True, 6)
        assert h_con <= h_sin


# ── desgastar_ropa ───────────────────────────────────────────

class TestDesgastarRopa:
    def test_desgaste_reduce_durabilidad(self):
        ropa = _ropa_completa()
        dur_antes = sum(p.get("durabilidad", p.get("durabilidad_max", 100))
                        for p in ropa.values())
        desgastar_ropa(ropa, 6, True, "templado")
        dur_despues = sum(p.get("durabilidad", p.get("durabilidad_max", 100))
                         for p in ropa.values())
        assert dur_despues < dur_antes

    def test_ropa_rota_se_elimina(self):
        ropa = {"cabeza": _prenda("gorro_lana")}
        ropa["cabeza"]["durabilidad"] = 1
        desgastar_ropa(ropa, 100, True, "lluvia_acida")
        # Prenda destruida se reemplaza por dict vacío
        cabeza = ropa.get("cabeza", {})
        assert not cabeza or cabeza.get("durabilidad", 1) <= 0


# ── evaluar_congelacion ──────────────────────────────────────

class TestCongelacion:
    def test_sin_frio_no_congela(self):
        horas_exp, msgs = evaluar_congelacion(10.0, _ropa_completa(), 3, 0.0)
        assert horas_exp == 0.0
        assert not msgs

    def test_frio_sin_proteccion_acumula(self):
        horas_exp, msgs = evaluar_congelacion(-10.0, {}, 3, 0.0)
        assert horas_exp > 0.0

    def test_proteccion_extremidades_reduce(self):
        horas_sin, _ = evaluar_congelacion(-10.0, {}, 3, 0.0)
        ropa = {"manos": _prenda("guantes_cuero"), "pies": _prenda("botas_cuero")}
        horas_con, _ = evaluar_congelacion(-10.0, ropa, 3, 0.0)
        assert horas_con <= horas_sin


# ── impermeabilidad_total ────────────────────────────────────

class TestImpermeabilidad:
    def test_sin_ropa(self):
        assert impermeabilidad_total({}) == 0.0

    def test_con_poncho(self):
        ropa = {"capa_exterior": _prenda("impermeable")}
        imp = impermeabilidad_total(ropa)
        assert imp > 20.0

    def test_ropa_completa_alta(self):
        ropa = _ropa_completa()
        imp = impermeabilidad_total(ropa)
        assert imp > 0.0


# ── Integración de vestimenta en ITEMS ───────────────────────

class TestVestimentaEnItems:
    def test_prendas_registradas_en_items(self):
        from data.items import ITEMS
        for key in PRENDAS:
            assert key in ITEMS, f"Prenda '{key}' no registrada en ITEMS"
            # chaleco_cuero ya existía como armadura; el resto son vestimenta
            assert ITEMS[key]["tipo"] in ("vestimenta", "armadura")

    def test_prenda_tiene_slot(self):
        from data.items import ITEMS
        for key in PRENDAS:
            assert "slot" in ITEMS[key]
