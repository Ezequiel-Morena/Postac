# ============================================================
# engine/cocina.py — Sistema de cocción y preparación de comida
#
# Cocinar transforma alimentos crudos en versiones más nutritivas
# y seguras. Requiere fuego activo. La habilidad de cocina
# mejora la calidad del resultado y reduce el desperdicio.
# ============================================================

from __future__ import annotations
import random
from typing import TYPE_CHECKING

from engine.fuego import esta_encendido, tick_fuego, combustible_disponible

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

# Mapa de transformación: item_crudo -> item_cocido
RECETAS_COCCION: dict[str, dict] = {
    "pez_pequeno": {
        "resultado": "pez_cocido",
        "nombre_resultado": "Pez cocido",
        "horas": 0.5,
        "combustible_min": 20,
    },
    "pez_mediano": {
        "resultado": "pez_cocido",
        "nombre_resultado": "Pez cocido (grande)",
        "horas": 0.75,
        "combustible_min": 30,
    },
    "carne_animal_cruda": {
        "resultado": "carne_asada",
        "nombre_resultado": "Carne asada",
        "horas": 1.0,
        "combustible_min": 40,
    },
    "agua_sucia": {
        "resultado": "agua_hervida",
        "nombre_resultado": "Agua hervida",
        "horas": 0.5,
        "combustible_min": 15,
    },
    "agua_contaminada": {
        "resultado": "agua_hervida",
        "nombre_resultado": "Agua hervida",
        "horas": 0.5,
        "combustible_min": 15,
    },
    "hongo_comestible": {
        "resultado": "hongo_comestible",
        "nombre_resultado": "Hongo cocido",
        "horas": 0.3,
        "combustible_min": 10,
    },
}

RECETAS_COMPUESTAS: dict[str, dict] = {
    "caldo_huesos": {
        "ingredientes": {"carne_animal_cruda": 1, "agua_sucia": 1},
        "resultado": "caldo_huesos",
        "nombre_resultado": "Caldo de huesos",
        "horas": 2.0,
        "combustible_min": 80,
        "desc": "Nutritivo y reconstituyente. Vale la espera.",
    },
}


def puede_cocinar(personaje: "Sobreviviente") -> tuple[bool, str]:
    if not esta_encendido(personaje):
        return False, "Necesitas fuego activo para cocinar."
    return True, ""


def cocinar_item(personaje: "Sobreviviente", item_id: str) -> dict:
    """
    Cocina un ítem crudo disponible en inventario o almacén.
    Retorna dict con: exito, resultado_item, mensaje, horas_usadas, xp_ganada.
    """
    resultado = {
        "exito": False,
        "resultado_item": None,
        "mensaje": "",
        "horas_usadas": 0,
        "xp_ganada": 0,
    }

    puede, razon = puede_cocinar(personaje)
    if not puede:
        resultado["mensaje"] = razon
        return resultado

    if item_id not in RECETAS_COCCION:
        resultado["mensaje"] = f"No sabes cómo cocinar '{item_id}'."
        return resultado

    receta = RECETAS_COCCION[item_id]

    if combustible_disponible(personaje) < receta["combustible_min"]:
        resultado["mensaje"] = (
            f"El fuego no tiene suficiente combustible. "
            f"Necesitas al menos {receta['combustible_min']} min de fuego."
        )
        return resultado

    if not _consumir_item(personaje, item_id):
        resultado["mensaje"] = f"No tienes '{item_id}' disponible para cocinar."
        return resultado

    tick_fuego(personaje, receta["horas"])

    skill_cocina = personaje.skills.get("cocina", 0)
    item_resultado = {
        "id": receta["resultado"],
        "nombre": receta["nombre_resultado"],
        "cantidad": 1,
    }

    # Skill alta puede producir doble porción ocasionalmente
    if skill_cocina > 60 and random.random() < 0.3:
        item_resultado["cantidad"] = 2
        resultado["mensaje"] = f"🍳 ¡Doble porción! Cocinaste 2x {receta['nombre_resultado']}."
    else:
        resultado["mensaje"] = f"🍳 Cocinaste: {receta['nombre_resultado']}."

    almacen = getattr(personaje, "almacen", [])
    almacen.append(item_resultado)
    personaje.almacen = almacen

    if hasattr(personaje, "ganar_xp_skill"):
        personaje.ganar_xp_skill("cocina", 2)
    resultado["xp_ganada"] = 2

    resultado["exito"] = True
    resultado["resultado_item"] = item_resultado
    resultado["horas_usadas"] = receta["horas"]

    personaje.fatiga = min(100, personaje.fatiga + 2)

    return resultado


def purificar_agua(personaje: "Sobreviviente") -> dict:
    """Alias conveniente para hervir agua_sucia."""
    # Intenta con agua_sucia primero, luego agua_contaminada
    for tipo_agua in ("agua_sucia", "agua_contaminada"):
        if _tiene_item(personaje, tipo_agua):
            return cocinar_item(personaje, tipo_agua)
    return {
        "exito": False,
        "resultado_item": None,
        "mensaje": "No tienes agua que purificar.",
        "horas_usadas": 0,
        "xp_ganada": 0,
    }


def listar_items_cocinables(personaje: "Sobreviviente") -> list[str]:
    """Devuelve IDs de ítems cocinables disponibles en inventario o almacén."""
    cocinables = []
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in col:
            if isinstance(item, dict) and item.get("id") in RECETAS_COCCION:
                item_id = item["id"]
                if item_id not in cocinables:
                    cocinables.append(item_id)
    return cocinables


# ── helpers privados ──────────────────────────────────────────

def _consumir_item(personaje: "Sobreviviente", item_id: str) -> bool:
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in list(col):
            if isinstance(item, dict) and item.get("id") == item_id:
                col.remove(item)
                return True
    return False


def _tiene_item(personaje: "Sobreviviente", item_id: str) -> bool:
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in col:
            if isinstance(item, dict) and item.get("id") == item_id:
                return True
    return False
