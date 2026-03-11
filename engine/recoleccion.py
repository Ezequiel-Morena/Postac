# ============================================================
# engine/recoleccion.py — Recolección de plantas y recursos
#
# El forrajeo es la forma más accesible de conseguir comida
# sin herramientas. Pero la identificación errónea puede matar.
# También permite recolectar leña, agua de lluvia y plantas medicinales.
# ============================================================

from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

# Recursos recolectables por tipo de zona
RECURSOS_POR_ZONA: dict[str, list[dict]] = {
    "forestal": [
        {"id": "hongo_comestible", "nombre": "Hongo comestible", "peso_prob": 0.30, "nivel_botanica": 10, "riesgo_error": 0.05},
        {"id": "hierba_medicinal", "nombre": "Hierba medicinal", "peso_prob": 0.25, "nivel_botanica": 15, "riesgo_error": 0.02},
        {"id": "lena",             "nombre": "Leña seca",        "peso_prob": 0.35, "nivel_botanica": 0,  "riesgo_error": 0.00},
        {"id": "carbon_vegetal",   "nombre": "Carbón vegetal",   "peso_prob": 0.10, "nivel_botanica": 5,  "riesgo_error": 0.00},
    ],
    "campo": [
        {"id": "hierba_medicinal", "nombre": "Hierba medicinal",   "peso_prob": 0.35, "nivel_botanica": 10, "riesgo_error": 0.02},
        {"id": "hongo_comestible", "nombre": "Hongo comestible",   "peso_prob": 0.20, "nivel_botanica": 20, "riesgo_error": 0.08},
        {"id": "semillas_tomate",  "nombre": "Semillas silvestres","peso_prob": 0.15, "nivel_botanica": 5,  "riesgo_error": 0.00},
        {"id": "lena",             "nombre": "Leña",               "peso_prob": 0.30, "nivel_botanica": 0,  "riesgo_error": 0.00},
    ],
    "exterior": [
        {"id": "lena",             "nombre": "Leña",             "peso_prob": 0.50, "nivel_botanica": 0,  "riesgo_error": 0.00},
        {"id": "hierba_medicinal", "nombre": "Hierba medicinal", "peso_prob": 0.30, "nivel_botanica": 20, "riesgo_error": 0.04},
        {"id": "hongo_comestible", "nombre": "Hongo comestible", "peso_prob": 0.20, "nivel_botanica": 25, "riesgo_error": 0.10},
    ],
    "default": [
        {"id": "lena",             "nombre": "Leña",             "peso_prob": 0.70, "nivel_botanica": 0,  "riesgo_error": 0.00},
        {"id": "hierba_medicinal", "nombre": "Hierba medicinal", "peso_prob": 0.30, "nivel_botanica": 25, "riesgo_error": 0.05},
    ],
}

TAGS_ZONA_RECOLECCION = {"forestal", "campo", "exterior", "parque", "jardín"}
PROB_BASE_ENCONTRAR   = 0.55


def puede_recolectar(zona: dict) -> tuple[bool, str]:
    tags = set(zona.get("tags", []))
    if not tags.intersection(TAGS_ZONA_RECOLECCION) and "exterior" not in tags:
        return False, "Esta zona no tiene vegetación que recolectar."
    return True, ""


def recolectar(
    personaje: "Sobreviviente",
    zona: dict,
    horas: float = 1.5,
) -> dict:
    """
    Sesión de recolección y forrajeo en una zona.

    Retorna dict con:
        - exito: bool
        - items: list[dict]
        - xp_ganada: int
        - intoxicacion: bool
        - mensaje: str
        - fatiga_costo: int
    """
    resultado = {
        "exito": False,
        "items": [],
        "xp_ganada": 0,
        "intoxicacion": False,
        "mensaje": "",
        "fatiga_costo": int(horas * 4),
    }

    puede, razon = puede_recolectar(zona)
    if not puede:
        resultado["mensaje"] = razon
        return resultado

    skill_botanica = personaje.skills.get("botanica", 0)
    tags = set(zona.get("tags", []))

    tipo = "default"
    for t in ("forestal", "campo", "exterior"):
        if t in tags:
            tipo = t
            break

    pool = RECURSOS_POR_ZONA.get(tipo, RECURSOS_POR_ZONA["default"])
    intentos = max(1, int(horas * 1.5))

    items_encontrados = []
    intoxicacion = False

    for _ in range(intentos):
        if random.random() > PROB_BASE_ENCONTRAR:
            continue

        disponibles = [r for r in pool if skill_botanica >= r["nivel_botanica"]]
        if not disponibles:
            disponibles = [r for r in pool if r["nivel_botanica"] == 0]
        if not disponibles:
            continue

        pesos = [r["peso_prob"] for r in disponibles]
        elegido = random.choices(disponibles, weights=pesos, k=1)[0]

        # Riesgo de identificación errónea con plantas desconocidas
        riesgo_efectivo = max(0.0, elegido["riesgo_error"] - skill_botanica * 0.001)
        if elegido["riesgo_error"] > 0 and random.random() < riesgo_efectivo:
            intoxicacion = True
            if hasattr(personaje, "agregar_condicion"):
                personaje.agregar_condicion("intoxicacion_alimentaria")
        else:
            items_encontrados.append({
                "id": elegido["id"],
                "nombre": elegido["nombre"],
                "cantidad": 1,
            })

    if items_encontrados:
        if hasattr(personaje, "ganar_xp_skill"):
            personaje.ganar_xp_skill("botanica", 2)
        resultado["xp_ganada"] = 2

    personaje.fatiga = min(100, personaje.fatiga + resultado["fatiga_costo"])

    if items_encontrados:
        resultado["exito"] = True
        resultado["items"] = items_encontrados
        nombres = ", ".join(f"{i['nombre']}×{i['cantidad']}" for i in items_encontrados)
        resultado["mensaje"] = f"Recolectaste: {nombres}."
    elif intoxicacion:
        resultado["mensaje"] = "Recogiste algo que parecía comestible pero no lo era. Te sientes mal."
    else:
        resultado["mensaje"] = f"Pasaste {horas:.0f}h buscando pero no encontraste nada útil."

    resultado["intoxicacion"] = intoxicacion
    return resultado
