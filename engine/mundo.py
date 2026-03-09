# ============================================================
# engine/mundo.py — Generación procedural de zonas y loot
# Lee áreas desde data/areas.py y loot desde data/loot.py
# ============================================================
import random
import copy
from data.areas import AREAS
from data.loot  import LOOT_POOLS
from data.items import ITEMS

RESET   = "\033[0m"
VERDE   = "\033[92m"
AMARILLO = "\033[93m"
ROJO    = "\033[91m"
CIAN    = "\033[96m"
GRIS    = "\033[90m"
NEGRITA = "\033[1m"

PELIGRO_TEXTO = {1: "MUY BAJO", 2: "BAJO", 3: "MEDIO", 4: "ALTO", 5: "EXTREMO"}
PELIGRO_COLOR = {1: VERDE, 2: AMARILLO, 3: AMARILLO, 4: ROJO, 5: ROJO}


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
    peligro = max(1, min(5, base["peligro"] + random.randint(-1, 1)))
    t_min, t_max = base["tiempo_h"]
    duracion = round(random.uniform(t_min, t_max), 1)
    high_loot   = random.random() < 0.25
    high_riesgo = random.random() < 0.20

    if high_riesgo: peligro = min(5, peligro + 1)
    if high_loot:   duracion = round(duracion * 1.2, 1)

    sufijos = ["del Norte", "Central", "Sección B", "del Este",
               "en ruinas", "Zona 3", "Bloque 7", "Sector Gamma"]

    return {
        "area_key":      area_key,
        "nombre":        f"{base['nombre']} {random.choice(sufijos)}",
        "icono":         base["icono"],
        "descripcion":   base["descripcion"],
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
        "tags":          base.get("tags", []),
        "info_previa":   personaje.info_areas.get(area_key, {}),
    }


def generar_loot_area(area: dict, personaje) -> list[dict]:
    """Genera loot según la tabla del área y los stats del personaje."""
    items_encontrados = []
    mult = personaje.multiplicador_loot()

    for pool_key, prob_base in area.get("loot_chances", {}).items():
        if random.random() > min(0.95, prob_base * mult):
            continue
        if pool_key not in LOOT_POOLS:
            continue
        item_key = random.choice(LOOT_POOLS[pool_key])
        if not item_key or item_key not in ITEMS:
            continue
        item = copy.deepcopy(ITEMS[item_key])
        if "cantidad" in item:
            item["cantidad"] = max(1, int(item["cantidad"] * random.uniform(0.8, mult)))
        if "durabilidad" in item:
            item["durabilidad"] = random.randint(30, 100)
        items_encontrados.append(item)

    return items_encontrados


def mostrar_opciones(opciones: list[dict], personaje) -> str:
    lineas = [
        "\n┌────────────────────────────────────────────────────",
        "│  ZONAS DE EXPEDICIÓN DISPONIBLES",
        "├────────────────────────────────────────────────────",
    ]
    for i, area in enumerate(opciones, 1):
        peligro = area["peligro"]
        col     = PELIGRO_COLOR.get(peligro, RESET)
        ptxt    = PELIGRO_TEXTO.get(peligro, "?")
        revisit = f" {GRIS}[REVISITAR]{RESET}" if area["ya_visitada"] else f" {VERDE}[NUEVA]{RESET}"
        loot_h  = f"  {AMARILLO}◆ INDICIOS DE BUENA COSECHA{RESET}" if area["high_loot"] else ""
        riesgo_h = f"  {ROJO}⚠ ACTIVIDAD ELEVADA{RESET}" if area["alto_riesgo"] else ""
        rad_txt  = f"  {ROJO}☢ RAD:{area['radiacion']}{RESET}" if area["radiacion"] > 0 else ""
        desc_short = area["descripcion"][:72] + "..."

        lineas += [
            "│",
            f"│  [{i}] {area['icono']} {CIAN}{area['nombre']}{RESET}{revisit}",
            f"│      Peligro: {col}{ptxt}{RESET}{loot_h}{riesgo_h}{rad_txt}",
            f"│      Tiempo estimado: ~{area['duracion_h']}h",
            f"│      {GRIS}{desc_short}{RESET}",
        ]
        if area["info_previa"].get("conocido"):
            det = area["info_previa"].get("detalle", "Zona conocida")
            lineas.append(f"│      {AMARILLO}► {det}{RESET}")

    lineas += [
        "│",
        f"│  [0] {AMARILLO}Descansar en el refugio{RESET}",
        "└────────────────────────────────────────────────────",
    ]
    return "\n".join(lineas)
