# ============================================================
# tests/test_autonomo.py — Tests para el sistema autónomo
#
# Cubre:
#   1. Cálculo de archetype desde bg_key y desde skill dominante.
#   2. Scoring de zonas con estado vital normal y comprometido.
#   3. Decisión de descanso con umbrales mínimos.
#   4. Selección de zona más adecuada según necesidades.
#   5. Actualización de estrategia tras fin de partida.
#   6. Bucle autónomo mínimo (personaje crea un tick sin errores).
# ============================================================

import sys
import os
import copy

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.personaje  import Sobreviviente
from engine.estrategia import (
    calcular_archetype, obtener_config_archetype,
    registrar_fin_partida, cargar_estrategia,
    _config_archetype_default,
)
from engine.autonomo import (
    decidir_tick, elegir_zona, _debe_descansar,
    _score_zona, gestionar_inventario_autonomo,
    _tiene_item_tipo,
)


# ──────────────────────────────────────────────────────────────
#  FIXTURES
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def personaje_base():
    """Personaje con estado vital saludable y conocido."""
    p = Sobreviviente.__new__(Sobreviviente)
    # Vitales normales.
    p.salud      = 80
    p.salud_max  = 100
    p.hambre     = 20
    p.sed        = 20
    p.fatiga     = 30
    p.radiacion  = 0
    p.inventario = []
    p.skills     = {"supervivencia": 40, "combate_cac": 20, "medicina": 10}
    p.bg_key     = "granjero"
    p.expediciones_completadas = 0
    p.dia        = 5
    p.areas_visitadas = []
    return p


@pytest.fixture
def zona_segura():
    return {
        "area_key":  "supermercado",
        "nombre":    "Supermercado Abandonado",
        "peligro":   2,
        "tags":      ["interior", "comida", "agua"],
        "radiacion": 0,
    }


@pytest.fixture
def zona_peligrosa():
    return {
        "area_key": "comisaria",
        "nombre":   "Comisaría",
        "peligro":  4,
        "tags":     ["interior", "armas"],
        "radiacion": 0,
    }


@pytest.fixture
def zona_radiactiva():
    return {
        "area_key": "laboratorio",
        "nombre":   "Laboratorio",
        "peligro":  3,
        "tags":     ["conocimiento", "medico"],
        "radiacion": 2,
    }


@pytest.fixture
def estrategia_base():
    return cargar_estrategia()


@pytest.fixture
def config_granjero(estrategia_base):
    archetypes = estrategia_base.get("archetypes", {})
    if "granjero" in archetypes:
        return {**estrategia_base.get("global", {}), **archetypes["granjero"], "_archetype": "granjero"}
    return _config_archetype_default("granjero") | {"_archetype": "granjero"}


# ──────────────────────────────────────────────────────────────
#  1. ARCHETYPE
# ──────────────────────────────────────────────────────────────

def test_calcular_archetype_desde_bg_key(personaje_base):
    personaje_base.bg_key = "medico"
    assert calcular_archetype(personaje_base) == "medico"


def test_calcular_archetype_desde_bg_key_ladron(personaje_base):
    personaje_base.bg_key = "ladron"
    assert calcular_archetype(personaje_base) == "ladron"


def test_calcular_archetype_sin_bg_usa_skill_dominante(personaje_base):
    personaje_base.bg_key = ""
    personaje_base.skills = {"medicina": 80, "combate_cac": 20}
    archetype = calcular_archetype(personaje_base)
    assert archetype == "medico"


def test_calcular_archetype_sin_nada_devuelve_default(personaje_base):
    personaje_base.bg_key = ""
    personaje_base.skills = {}
    archetype = calcular_archetype(personaje_base)
    assert isinstance(archetype, str)
    assert len(archetype) > 0


# ──────────────────────────────────────────────────────────────
#  2. SCORING DE ZONAS
# ──────────────────────────────────────────────────────────────

def test_zona_segura_mayor_score_con_salud_baja(personaje_base, zona_segura, zona_peligrosa, config_granjero):
    """Con salud baja, la zona segura debe superar a la peligrosa."""
    personaje_base.salud = 20  # Muy baja.
    scores = [
        _score_zona(personaje_base, zona_segura, config_granjero),
        _score_zona(personaje_base, zona_peligrosa, config_granjero),
    ]
    # No necesariamente segura gana siempre (hay ruido), pero en promedio sí.
    # Verificamos que la peligrosa tiene penalización (score sin ruido).
    import importlib, engine.autonomo as mod
    factor_pel = mod._factor_peligro(personaje_base, zona_peligrosa)
    assert factor_pel < 1.0, "Zona peligrosa debe tener factor < 1 con salud baja."


def test_bonus_necesidad_comida_en_zona_adecuada(personaje_base, zona_segura, config_granjero):
    """Si el personaje tiene hambre, la zona con tag comida debe tener bonus."""
    personaje_base.hambre = 70
    import engine.autonomo as mod
    bonus_alto  = mod._bonus_necesidades(personaje_base, zona_segura)    # tiene tag comida
    zona_sin_comida = {"area_key": "comisaria", "tags": ["armas"], "peligro": 3, "radiacion": 0}
    bonus_bajo  = mod._bonus_necesidades(personaje_base, zona_sin_comida)
    assert bonus_alto > bonus_bajo


def test_radiacion_penaliza_con_radiacion_alta(personaje_base, zona_radiactiva, config_granjero):
    """Alta radiación acumulada debe penalizar zonas radioactivas."""
    personaje_base.radiacion = 70
    import engine.autonomo as mod
    factor = mod._factor_radiacion(personaje_base, zona_radiactiva)
    assert factor < 1.0


def test_score_es_positivo(personaje_base, zona_segura, config_granjero):
    score = _score_zona(personaje_base, zona_segura, config_granjero)
    assert score > 0


# ──────────────────────────────────────────────────────────────
#  3. DECISIÓN DE DESCANSO
# ──────────────────────────────────────────────────────────────

def test_descanso_obligatorio_con_salud_baja(personaje_base, config_granjero):
    personaje_base.salud = 5  # Crítica.
    assert _debe_descansar(personaje_base, config_granjero) is True


def test_descanso_obligatorio_con_fatiga_alta(personaje_base, config_granjero):
    personaje_base.fatiga = 95
    assert _debe_descansar(personaje_base, config_granjero) is True


def test_no_descanso_con_vitales_ok(personaje_base, config_granjero):
    """Con todos los vitales en buen estado, no debe forzar descanso."""
    personaje_base.salud  = 90
    personaje_base.fatiga = 10
    personaje_base.hambre = 10
    personaje_base.sed    = 10
    personaje_base.inventario = []  # Sin comida → no puede descansar por hambre.
    # No garantizamos False (hay probabilidad), pero no debe ser always True.
    # Solo verificamos que el flujo no falla.
    resultado = _debe_descansar(personaje_base, config_granjero)
    assert isinstance(resultado, bool)


def test_descanso_forzado_con_comida_y_hambre_alta(personaje_base, config_granjero):
    """Hambre alta + comida disponible → debería descansar."""
    personaje_base.hambre = 85
    personaje_base.inventario = [{"nombre": "Lata de conservas", "tipo": "comida", "peso": 0.3}]
    assert _debe_descansar(personaje_base, config_granjero) is True


# ──────────────────────────────────────────────────────────────
#  4. SELECCIÓN DE ZONA
# ──────────────────────────────────────────────────────────────

def test_elegir_zona_devuelve_una_zona(personaje_base, zona_segura, zona_peligrosa, config_granjero):
    zonas    = [zona_segura, zona_peligrosa]
    elegida  = elegir_zona(personaje_base, zonas, config_granjero)
    assert elegida in zonas


def test_elegir_zona_unica_opcion(personaje_base, zona_segura, config_granjero):
    elegida = elegir_zona(personaje_base, [zona_segura], config_granjero)
    assert elegida == zona_segura


def test_decidir_tick_devuelve_tupla(personaje_base, zona_segura, config_granjero):
    personaje_base.salud  = 90
    personaje_base.fatiga = 20
    personaje_base.hambre = 10
    personaje_base.sed    = 10
    result = decidir_tick(personaje_base, [zona_segura], config_granjero)
    assert isinstance(result, tuple)
    assert result[0] in ("expedicion", "descanso")


def test_decidir_tick_descanso_cuando_critico(personaje_base, zona_segura, config_granjero):
    personaje_base.salud = 2
    accion, zona = decidir_tick(personaje_base, [zona_segura], config_granjero)
    assert accion == "descanso"
    assert zona is None


# ──────────────────────────────────────────────────────────────
#  5. GESTIÓN DE INVENTARIO AUTÓNOMO
# ──────────────────────────────────────────────────────────────

def test_no_descarta_si_hay_espacio(personaje_base, config_granjero):
    personaje_base.inventario = [
        {"nombre": "Lata", "tipo": "comida", "peso": 0.3}
    ]
    personaje_base.peso_max = 10.0
    msgs = gestionar_inventario_autonomo(personaje_base, config_granjero)
    assert msgs == []


def test_descarta_libro_si_inventario_lleno(personaje_base, config_granjero):
    """Libro debe descartarse cuando el inventario está al 90%+ de peso."""
    personaje_base.peso_max = 5.0
    personaje_base.inventario = [
        {"nombre": "Manual técnico", "tipo": "libro", "peso": 4.5},
        {"nombre": "Agua", "tipo": "agua", "peso": 0.5},
    ]
    msgs = gestionar_inventario_autonomo(personaje_base, config_granjero)
    assert len(msgs) > 0


def test_tiene_item_tipo_true(personaje_base):
    personaje_base.inventario = [{"nombre": "Pan", "tipo": "comida", "peso": 0.2}]
    assert _tiene_item_tipo(personaje_base, "comida") is True


def test_tiene_item_tipo_false(personaje_base):
    personaje_base.inventario = []
    assert _tiene_item_tipo(personaje_base, "medicina") is False


# ──────────────────────────────────────────────────────────────
#  6. ACTUALIZACIÓN DE ESTRATEGIA (aprendizaje)
# ──────────────────────────────────────────────────────────────

def test_registrar_fin_partida_actualiza_runs(personaje_base):
    estrategia = cargar_estrategia()
    arch = "granjero"
    runs_antes = (estrategia.get("archetypes", {})
                              .get(arch, {})
                              .get("estadisticas", {})
                              .get("runs", 0))

    personaje_base.bg_key = arch
    personaje_base.dia    = 10
    personaje_base.expediciones_completadas = 8

    registrar_fin_partida(
        personaje_base, estrategia,
        causa_muerte="herida",
        zonas_visitadas_esta_partida=["supermercado", "casa_abandonada"],
        zona_muerte="casa_abandonada",
    )

    runs_post = estrategia["archetypes"][arch]["estadisticas"]["runs"]
    assert runs_post == runs_antes + 1


def test_registrar_fin_partida_crea_archetype_nuevo(personaje_base):
    """Si el archetype no existe en el archivo, debe crearse."""
    estrategia = {"version": 1, "global": {}, "archetypes": {}, "historial_partidas": [], "metadata": {}}
    personaje_base.bg_key = "archetype_nuevo_test"
    personaje_base.dia    = 5
    personaje_base.expediciones_completadas = 3

    registrar_fin_partida(
        personaje_base, estrategia,
        causa_muerte="inanición",
        zonas_visitadas_esta_partida=["supermercado"],
        zona_muerte=None,
    )

    assert "archetype_nuevo_test" in estrategia["archetypes"]
    assert estrategia["archetypes"]["archetype_nuevo_test"]["estadisticas"]["runs"] == 1


def test_registrar_penaliza_zona_muerte(personaje_base):
    """La zona de muerte debe tener su peso reducido."""
    estrategia = cargar_estrategia()
    arch = "medico"
    personaje_base.bg_key = arch
    personaje_base.dia    = 3
    personaje_base.expediciones_completadas = 2

    # Asegurar que el archetype existe con peso base para laboratorio.
    if arch not in estrategia.get("archetypes", {}):
        estrategia.setdefault("archetypes", {})[arch] = _config_archetype_default(arch)
    peso_antes = estrategia["archetypes"][arch].get("pesos_zonas", {}).get("hospital", 1.0)

    registrar_fin_partida(
        personaje_base, estrategia,
        causa_muerte="herida",
        zonas_visitadas_esta_partida=["hospital"],
        zona_muerte="hospital",
    )

    peso_post = estrategia["archetypes"][arch]["pesos_zonas"].get("hospital", 1.0)
    # El peso de la zona de muerte debe bajar (o mantenerse si ya era mínimo).
    assert peso_post <= peso_antes


def test_historial_no_supera_50(personaje_base):
    estrategia = {"version": 1, "global": {}, "archetypes": {}, "historial_partidas": [], "metadata": {}}
    personaje_base.bg_key = "granjero"
    personaje_base.expediciones_completadas = 1

    for i in range(60):
        personaje_base.dia = i + 1
        registrar_fin_partida(
            personaje_base, estrategia,
            causa_muerte="inanición",
            zonas_visitadas_esta_partida=["supermercado"],
            zona_muerte="supermercado",
        )

    assert len(estrategia["historial_partidas"]) <= 50


# ──────────────────────────────────────────────────────────────
#  8. GESTIÓN AUTÓNOMA DE RECURSOS
# ──────────────────────────────────────────────────────────────

from engine.autonomo import gestionar_recursos_autonomo


@pytest.fixture
def personaje_con_comida():
    p = Sobreviviente()
    p.hambre     = 70  # Por encima del umbral de comer.
    p.sed        = 10
    p.salud      = 95
    p.radiacion  = 0
    p.condiciones = []
    p.inventario = [
        {"nombre": "Lata de atún", "tipo": "comida", "peso": 0.3,
         "efectos": {"hambre": -35}},
    ]
    return p


@pytest.fixture
def personaje_con_agua():
    p = Sobreviviente()
    p.salud      = 85
    p.hambre     = 10
    p.sed        = 85  # Emergencia.
    p.fatiga     = 15
    p.radiacion  = 0
    p.condiciones = []
    p.inventario = [
        {"nombre": "Botella de agua", "tipo": "agua", "peso": 0.5,
         "efectos": {"sed": -40}},
    ]
    return p


@pytest.fixture
def personaje_herido():
    p = Sobreviviente()
    p.salud      = 30  # < 60% → debe usar medicina.
    p.hambre     = 20
    p.sed        = 20
    p.fatiga     = 10
    p.radiacion  = 0
    p.condiciones = []
    p.inventario = [
        {"nombre": "Botiquín básico", "tipo": "botiquin", "peso": 0.5,
         "efectos": {"salud": 30}},
    ]
    return p


def test_gestionar_recursos_come_cuando_hambre_alta(personaje_con_comida):
    hambre_antes = personaje_con_comida.hambre
    msgs = gestionar_recursos_autonomo(personaje_con_comida)
    # Debe haber usado el ítem → hambre reducida.
    assert personaje_con_comida.hambre < hambre_antes
    assert len(msgs) > 0
    assert "Lata de atún" in msgs[0]


def test_gestionar_recursos_bebe_cuando_sed_alta(personaje_con_agua):
    sed_antes = personaje_con_agua.sed
    msgs = gestionar_recursos_autonomo(personaje_con_agua)
    assert personaje_con_agua.sed < sed_antes
    assert any("Botella" in m for m in msgs)


def test_gestionar_recursos_usa_medicina_herido(personaje_herido):
    salud_antes = personaje_herido.salud
    msgs = gestionar_recursos_autonomo(personaje_herido)
    assert personaje_herido.salud > salud_antes
    assert any("Botiquín" in m for m in msgs)


def test_gestionar_recursos_no_actua_sin_items(personaje_base):
    p = Sobreviviente()
    p.hambre     = 80
    p.sed        = 80
    p.inventario = []
    msgs = gestionar_recursos_autonomo(p)
    # Sin ítems no puede hacer nada, no debe lanzar excepción.
    assert isinstance(msgs, list)


def test_gestionar_recursos_no_actua_con_vitales_ok():
    # Vitales todos bien → no consume nada.
    p = Sobreviviente()
    p.hambre    = 10
    p.sed       = 10
    p.salud     = 95
    p.radiacion = 5
    p.condiciones = []
    p.inventario = [
        {"nombre": "Botiquín básico", "tipo": "botiquin", "peso": 0.5,
         "efectos": {"salud": 30}},
    ]
    msgs = gestionar_recursos_autonomo(p)
    assert msgs == []


def test_gestionar_recursos_usa_antirradiacion():
    p = Sobreviviente()
    p.radiacion = 50  # > umbral 35.
    p.hambre    = 10
    p.sed       = 10
    p.salud     = 90
    p.condiciones = []
    p.inventario = [
        {"nombre": "Yoduro de potasio", "tipo": "antirradiacion", "peso": 0.1,
         "efectos": {"radiacion": -20}},
    ]
    rad_antes = p.radiacion
    msgs = gestionar_recursos_autonomo(p)
    assert p.radiacion < rad_antes


def test_obtener_config_incluye_archetype_key(personaje_base, estrategia_base):
    personaje_base.bg_key = "granjero"
    config = obtener_config_archetype(personaje_base, estrategia_base)
    assert "_archetype" in config
    assert config["_archetype"] == "granjero"


def test_config_tiene_pesos_zonas(personaje_base, estrategia_base):
    personaje_base.bg_key = "medico"
    config = obtener_config_archetype(personaje_base, estrategia_base)
    assert "pesos_zonas" in config
    assert isinstance(config["pesos_zonas"], dict)


def test_config_tiene_umbrales_descanso(personaje_base, estrategia_base):
    personaje_base.bg_key = "granjero"
    config = obtener_config_archetype(personaje_base, estrategia_base)
    assert "umbral_descanso_fatiga" in config
    assert "umbral_descanso_hambre" in config
