# ============================================================
# engine/mundo.py — Generación procedural de zonas y loot
# Lee áreas desde data/areas.py y loot desde data/loot.py
# ============================================================
import random
import copy
from data.areas import AREAS
from data.loot  import LOOT_POOLS
from data.items import ITEMS
from engine.clima import clima_actual
from engine.constants import (
    PELIGRO_MIN, PELIGRO_MAX, PELIGRO_VARIACION,
    PROB_LOOT_ALTO, PROB_RIESGO_ALTO,
    DURACION_MULT_LOOT_ALTO, DURACION_MULT_INVIERNO, DURACION_MULT_VERANO,
    DURACION_MULT_MAL_CLIMA, DISTANCIA_FACTOR_MIN, DISTANCIA_FACTOR_MAX,
    DISTANCIA_MIN_KM, LOOT_SCORE_MULT_TORMENTA, LOOT_SCORE_MULT_ALTO,
)


def generar_opciones(personaje, cantidad: int = 4) -> list[dict]:
    """Genera N opciones de expedición proceduralmente."""
    tipos = list(AREAS.keys())
    no_visitadas = [t for t in tipos if t not in personaje.areas_visitadas]
    visitadas    = [t for t in tipos if t in personaje.areas_visitadas]
    pool = (no_visitadas * 3) + visitadas
    random.shuffle(pool)

    seleccionados, vistos = [], set()
    for t in pool:
        if t not in vistos:
            seleccionados.append(t)
            vistos.add(t)
        if len(seleccionados) == cantidad:
            break

    return [_instanciar_area(key, personaje) for key in seleccionados]


def _instanciar_area(area_key: str, personaje) -> dict:
    base   = AREAS[area_key]
    clima = clima_actual(personaje.dia, personaje.hora, {"area_key": area_key, "tags": base.get("tags", [])})
    peligro = max(PELIGRO_MIN, min(PELIGRO_MAX, base["peligro"] + random.randint(-PELIGRO_VARIACION, PELIGRO_VARIACION)))
    t_min, t_max = base["tiempo_h"]
    duracion = round(random.uniform(t_min, t_max), 1)
    high_loot   = random.random() < PROB_LOOT_ALTO
    high_riesgo = random.random() < PROB_RIESGO_ALTO

    if high_riesgo: peligro = min(PELIGRO_MAX, peligro + 1)
    if high_loot:   duracion = round(duracion * DURACION_MULT_LOOT_ALTO, 1)

    # Ajustes estacionales y climáticos para exploración emergente.
    est = clima.get("estacion", "")
    clima_id = clima.get("clima_id", "templado")
    if est == "invierno":
        duracion = round(duracion * DURACION_MULT_INVIERNO, 1)
    elif est == "verano":
        duracion = round(duracion * DURACION_MULT_VERANO, 1)

    if clima_id in ("tormenta", "tormenta_radiacion", "helada"):
        peligro = min(PELIGRO_MAX, peligro + 1)
    if clima_id in ("lluvia", "niebla"):
        duracion = round(duracion * DURACION_MULT_MAL_CLIMA, 1)

    # Distancia aproximada coherente con la duración: evita '?' en la UI
    # y ayuda a una heurística de elección más legible en humano/bot.
    distancia_km = max(DISTANCIA_MIN_KM, round(duracion * random.uniform(DISTANCIA_FACTOR_MIN, DISTANCIA_FACTOR_MAX), 1))

    # Valor esperado del área según su tabla de loot, para priorizar opciones
    # sin hardcodear zonas concretas.
    escasez_factor = _factor_escasez_regional(personaje, area_key)
    loot_score = round(sum(base.get("loot_chances", {}).values()) * (LOOT_SCORE_MULT_ALTO if high_loot else 1.0), 2)
    if clima_id in ("tormenta", "tormenta_radiacion"):
        loot_score = round(loot_score * LOOT_SCORE_MULT_TORMENTA, 2)
    loot_score = round(loot_score * escasez_factor, 2)

    # Riesgo compuesto (peligro + radiación + bandera de actividad elevada).
    riesgo_score = round(peligro + base.get("radiacion", 0) * 0.6 + (0.8 if high_riesgo else 0.0), 2)

    sufijos = ["del Norte", "Central", "Sección B", "del Este",
               "en ruinas", "Zona 3", "Bloque 7", "Sector Gamma"]

    return {
        "area_key":      area_key,
        "nombre":        f"{base['nombre']} {random.choice(sufijos)}",
        "icono":         base["icono"],
        "descripcion":   base["descripcion"],
        "distancia_km":  distancia_km,
        "peligro":       peligro,
        "radiacion":     base.get("radiacion", 0) + (1 if high_riesgo else 0),
        "ya_visitada":   area_key in personaje.areas_visitadas,
        "loot_chances":  base.get("loot_chances", {}),
        "enemigos":      base.get("enemigos", ["infectado_lento"]),
        "eventos":       base.get("eventos", []),
        "estructura":    base.get("estructura", ["interior"]),
        "duracion_h":    duracion,
        "high_loot":     high_loot,
        "alto_riesgo":   high_riesgo,
        "loot_score":    loot_score,
        "riesgo_score":  riesgo_score,
        "escasez_factor": escasez_factor,
        "escasez_pct":   int(round((1.0 - escasez_factor) * 100)),
        "tags":          base.get("tags", []),
        "info_previa":   personaje.info_areas.get(area_key, {}),
        "estacion":      clima.get("estacion", ""),
        "clima":         clima.get("nombre", "Templado"),
        "clima_icono":   clima.get("icono", "[CLM]"),
        "temperatura_c": clima.get("temperatura_c", 18),
    }


def generar_loot_area(area: dict, personaje) -> list[dict]:
    """Genera loot según la tabla del área y los stats del personaje."""
    items_encontrados = []
    mult = personaje.multiplicador_loot()
    contexto_area = _contexto_area(area)
    escasez_factor = _factor_escasez_regional(personaje, area.get("area_key", ""))

    for pool_key, prob_base in area.get("loot_chances", {}).items():
        if random.random() > min(0.95, prob_base * mult * escasez_factor):
            continue
        if pool_key not in LOOT_POOLS:
            continue

        item_key = _elegir_item_contextual(LOOT_POOLS[pool_key], area, contexto_area)
        if not item_key or item_key not in ITEMS:
            continue
        item = copy.deepcopy(ITEMS[item_key])
        if "cantidad" in item:
            item["cantidad"] = max(1, int(item["cantidad"] * random.uniform(0.8, mult)))
        if "durabilidad" in item:
            item["durabilidad"] = random.randint(30, 100)
        items_encontrados.append(item)

    return items_encontrados


def _factor_escasez_regional(personaje, area_key: str) -> float:
    """
    Escasez emergente sin estado adicional persistente.
    Sube con el paso de dias y expediciones, y penaliza revisitas.
    """
    revisit_penalty = 0.08 if area_key in getattr(personaje, "areas_visitadas", []) else 0.0
    presion_global = personaje.expediciones_completadas * 0.015 + personaje.dia * 0.002
    mitigacion = (personaje.skills.get("saqueo", 0) + personaje.skills.get("supervivencia", 0)) * 0.0015
    factor = 1.0 - min(0.45, presion_global + revisit_penalty) + min(0.12, mitigacion)
    return max(0.55, min(1.05, round(factor, 3)))


def _contexto_area(area: dict) -> set[str]:
    tags = {str(t).lower() for t in area.get("tags", [])}
    key = str(area.get("area_key", "")).lower()
    nombre = str(area.get("nombre", "")).lower()

    for token in (key, nombre):
        if "hospital" in token or "farmacia" in token or "lab" in token:
            tags.add("medico")
        if "comis" in token or "polic" in token or "armer" in token:
            tags.add("armas")
        if "casa" in token:
            tags.add("residencial")
            tags.add("civil")
        if "super" in token:
            tags.add("civil")
            tags.add("comida")
        if "fabrica" in token:
            tags.add("industrial")
        if "biblioteca" in token:
            tags.add("conocimiento")
        if "gasolinera" in token:
            tags.add("combustible")
        if "estadio" in token:
            tags.add("civil")
            tags.add("humanitario")
    return tags


def _score_item_contextual(item_def: dict, contexto_area: set[str]) -> int:
    tipo = item_def.get("tipo", "")
    score = 0

    if "medico" in contexto_area:
        if tipo.startswith("medicina"):
            score += 4
        if tipo.startswith("arma"):
            score -= 2
    if "armas" in contexto_area:
        if tipo.startswith("arma") or tipo == "municion":
            score += 4
    if "residencial" in contexto_area or "civil" in contexto_area:
        if tipo in ("comida", "agua", "herramienta", "material", "libro", "misc"):
            score += 3
        if tipo in ("medicina_fuerte", "arma_rara"):
            score -= 2
    if "industrial" in contexto_area:
        if tipo in ("herramienta", "material", "combustible"):
            score += 3
    if "conocimiento" in contexto_area and tipo == "libro":
        score += 4
    if "combustible" in contexto_area and tipo == "combustible":
        score += 4

    # Ajuste opcional data-driven por item
    for c in item_def.get("loot_contexts", []):
        if c in contexto_area:
            score += 2

    return score


def _elegir_item_contextual(pool: list, area: dict, contexto_area: set[str]) -> str | None:
    candidatos = [k for k in pool if k]
    if not candidatos:
        return None

    mejor_key = None
    mejor_score = -999
    random.shuffle(candidatos)
    for key in candidatos[:12]:
        item_def = ITEMS.get(key, {})
        score = _score_item_contextual(item_def, contexto_area)
        if score > mejor_score:
            mejor_score = score
            mejor_key = key

    # Si todo puntúa muy mal, respetar posibilidad de no encontrar nada contextual.
    if mejor_score < -1:
        return None
    return mejor_key
