# ============================================================
# engine/caza.py — Sistema de caza y trampas
#
# La caza activa requiere sigilo, rastreo y paciencia.
# Las trampas son pasivas: se instalan y se revisan después.
# Cada animal tiene sus propios rendimientos y riesgos.
# ============================================================

from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

# Animales cazables por zona/bioma
ANIMALES_POR_ZONA: dict[str, list[dict]] = {
    "forestal": [
        {"nombre": "Conejo",      "rend_carne": 2, "rend_piel": 1, "peligro": 0, "peso_prob": 0.40, "nivel_min": 0},
        {"nombre": "Ciervo",      "rend_carne": 8, "rend_piel": 2, "peligro": 1, "peso_prob": 0.20, "nivel_min": 20},
        {"nombre": "Jabalí",      "rend_carne": 6, "rend_piel": 1, "peligro": 3, "peso_prob": 0.15, "nivel_min": 30},
        {"nombre": "Rata grande", "rend_carne": 1, "rend_piel": 0, "peligro": 0, "peso_prob": 0.25, "nivel_min": 0},
    ],
    "urbano": [
        {"nombre": "Paloma",       "rend_carne": 1, "rend_piel": 0, "peligro": 0, "peso_prob": 0.50, "nivel_min": 0},
        {"nombre": "Rata urbana",  "rend_carne": 1, "rend_piel": 0, "peligro": 0, "peso_prob": 0.35, "nivel_min": 0},
        {"nombre": "Perro salvaje","rend_carne": 3, "rend_piel": 1, "peligro": 3, "peso_prob": 0.15, "nivel_min": 10},
    ],
    "campo": [
        {"nombre": "Conejo",  "rend_carne": 2, "rend_piel": 1, "peligro": 0, "peso_prob": 0.45, "nivel_min": 0},
        {"nombre": "Liebre",  "rend_carne": 2, "rend_piel": 1, "peligro": 0, "peso_prob": 0.35, "nivel_min": 0},
        {"nombre": "Ciervo",  "rend_carne": 8, "rend_piel": 2, "peligro": 1, "peso_prob": 0.20, "nivel_min": 25},
    ],
    "default": [
        {"nombre": "Rata",   "rend_carne": 1, "rend_piel": 0, "peligro": 0, "peso_prob": 0.60, "nivel_min": 0},
        {"nombre": "Paloma", "rend_carne": 1, "rend_piel": 0, "peligro": 0, "peso_prob": 0.40, "nivel_min": 0},
    ],
}

TAGS_ZONA_CAZA = {"forestal", "campo", "exterior", "urbano", "industrial"}
PROB_BASE_CAZA_ACTIVA = 0.30
DAÑO_BASE_ANIMAL_PELIGROSO = (5, 20)


def puede_cazar(personaje: "Sobreviviente", zona: dict) -> tuple[bool, str]:
    tags = set(zona.get("tags", []))
    if not tags.intersection(TAGS_ZONA_CAZA):
        return False, "Esta zona no tiene fauna que cazar."
    return True, ""


def cazar_activo(
    personaje: "Sobreviviente",
    zona: dict,
    horas: float = 3.0,
) -> dict:
    """
    Caza activa: acecho y captura.
    Puede resultar en ataque si el animal es peligroso.
    """
    resultado = {
        "exito": False,
        "capturas_carne": 0,
        "capturas_piel": 0,
        "xp_ganada": 0,
        "mensaje": "",
        "fatiga_costo": int(horas * 5),
        "daño_recibido": 0,
        "animal": None,
    }

    puede, razon = puede_cazar(personaje, zona)
    if not puede:
        resultado["mensaje"] = razon
        return resultado

    skill_caza   = personaje.skills.get("caza", 0)
    skill_sigilo = personaje.skills.get("sigilo", 0)

    animal = _seleccionar_animal(zona, skill_caza)
    resultado["animal"] = animal["nombre"]

    prob = min(0.80, PROB_BASE_CAZA_ACTIVA + skill_caza * 0.005 + skill_sigilo * 0.002)

    if random.random() > prob:
        if animal["peligro"] >= 2 and random.random() < 0.4:
            daño = random.randint(*DAÑO_BASE_ANIMAL_PELIGROSO)
            personaje.recibir_daño(daño)
            resultado["daño_recibido"] = daño
            resultado["mensaje"] = f"{animal['nombre']} te atacó antes de escapar. -{daño} salud."
        else:
            resultado["mensaje"] = f"El {animal['nombre']} escapó antes de que pudieras cazarlo."

        if hasattr(personaje, "ganar_xp_skill"):
            personaje.ganar_xp_skill("caza", 1)
    else:
        resultado["exito"] = True
        resultado["capturas_carne"] = animal["rend_carne"]
        resultado["capturas_piel"]  = animal["rend_piel"]
        xp = 3 + animal["peligro"]
        if hasattr(personaje, "ganar_xp_skill"):
            personaje.ganar_xp_skill("caza", xp)
        resultado["xp_ganada"] = xp
        resultado["mensaje"] = (
            f"Cazaste un {animal['nombre']}. "
            f"Obtuviste {animal['rend_carne']}x carne"
            + (f" y {animal['rend_piel']}x piel." if animal["rend_piel"] > 0 else ".")
        )

    personaje.fatiga = min(100, personaje.fatiga + resultado["fatiga_costo"])
    return resultado


def poner_trampa(personaje: "Sobreviviente", zona: dict) -> tuple[bool, str]:
    """
    Instala una trampa de lazo. Se verifica en el próximo tick.
    """
    if not _tiene_trampa(personaje):
        return False, "No tienes trampas disponibles. Necesitas una trampa de lazo."

    puede, razon = puede_cazar(personaje, zona)
    if not puede:
        return False, razon

    trampas = getattr(personaje, "trampas_activas", [])
    trampas.append({
        "zona_id": zona.get("id", "desconocida"),
        "zona_nombre": zona.get("nombre", "?"),
        "horas_pendientes": 24,
    })
    personaje.trampas_activas = trampas

    _gastar_trampa(personaje)

    return True, f"Trampa instalada en {zona.get('nombre', 'la zona')}. Vuelve en 24h para revisarla."


def revisar_trampas(personaje: "Sobreviviente", zona: dict) -> list[dict]:
    """
    Revisa las trampas instaladas en una zona. Devuelve lista de capturas.
    """
    trampas = getattr(personaje, "trampas_activas", [])
    zona_id = zona.get("id", "desconocida")
    capturas = []
    trampas_restantes = []

    for trampa in trampas:
        if trampa.get("zona_id") == zona_id:
            skill_caza = personaje.skills.get("caza", 0)
            prob = min(0.60, 0.25 + skill_caza * 0.004)
            if random.random() < prob:
                animal = _seleccionar_animal(zona, skill_caza)
                if animal["rend_carne"] > 0:
                    capturas.append({
                        "id": "carne_animal_cruda",
                        "nombre": "Carne de animal",
                        "cantidad": animal["rend_carne"],
                    })
                if animal["rend_piel"] > 0:
                    capturas.append({
                        "id": "piel_animal",
                        "nombre": "Piel de animal",
                        "cantidad": animal["rend_piel"],
                    })
        else:
            trampas_restantes.append(trampa)

    personaje.trampas_activas = trampas_restantes
    return capturas


# ── helpers privados ──────────────────────────────────────────

def _seleccionar_animal(zona: dict, skill_caza: int) -> dict:
    tags = set(zona.get("tags", []))
    tipo = "default"
    for t in ("forestal", "campo", "urbano"):
        if t in tags:
            tipo = t
            break

    pool = ANIMALES_POR_ZONA.get(tipo, ANIMALES_POR_ZONA["default"])
    disponibles = [a for a in pool if skill_caza >= a["nivel_min"]]
    if not disponibles:
        disponibles = pool

    pesos = [a["peso_prob"] for a in disponibles]
    return random.choices(disponibles, weights=pesos, k=1)[0]


def _tiene_trampa(personaje: "Sobreviviente") -> bool:
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in col:
            if isinstance(item, dict) and item.get("id") == "trampa_caza":
                return True
    return False


def _gastar_trampa(personaje: "Sobreviviente") -> None:
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in list(col):
            if isinstance(item, dict) and item.get("id") == "trampa_caza":
                usos = item.get("usos", 1)
                if usos <= 1:
                    col.remove(item)
                else:
                    item["usos"] = usos - 1
                return
