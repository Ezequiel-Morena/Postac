# ============================================================
# engine/fuego.py — Sistema de fuego y combustión
#
# El fuego es el núcleo de la supervivencia estática:
# permite cocinar, purificar agua, generar calor y luz.
# Un fuego mal gestionado se apaga o destruye el refugio.
# ============================================================

from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

# Combustibles válidos y su eficiencia calórica (minutos de fuego por unidad)
COMBUSTIBLES = {
    "madera":             30,
    "lena":               50,
    "carbon_vegetal":     90,
    "gasolina":           20,   # quema rápido, mucho calor
    "alcohol_industrial": 15,
    "piel_animal":        10,
}

# Métodos de encendido y su probabilidad base de éxito
METODOS_ENCENDIDO = {
    "encendedor": 0.90,
    "pedernal":   0.55,
    "friccion":   0.20,   # sin herramienta, puro conocimiento
}


def encender_fuego(personaje: "Sobreviviente") -> tuple[bool, str]:
    """
    Intenta encender el fuego del refugio del personaje.
    Busca herramientas de encendido en el inventario/almacén.
    Requiere combustible disponible.

    Retorna: (éxito: bool, mensaje: str)
    """
    inventario = getattr(personaje, "inventario", [])
    almacen    = getattr(personaje, "almacen", [])

    metodo, prob_base = _buscar_metodo_encendido(inventario, almacen)
    if metodo is None:
        return False, "No tienes con qué encender fuego. Necesitas un encendedor o pedernal."

    combustible = _buscar_combustible(inventario, almacen)
    if combustible is None:
        return False, "No hay combustible disponible. Necesitas madera, leña o carbón."

    skill_sup = personaje.skills.get("supervivencia", 0)
    prob_ajustada = min(0.98, prob_base + skill_sup * 0.003)

    if random.random() > prob_ajustada:
        return False, f"Intentaste encender fuego con {metodo} pero no lograste que prendiera."

    _consumir_combustible(personaje, combustible)
    duracion = COMBUSTIBLES[combustible]
    personaje.fuego_activo = True
    personaje.combustible_restante = duracion

    return True, f"🔥 Fuego encendido con {metodo}. Combustible: ~{duracion} min."


def agregar_combustible(personaje: "Sobreviviente", nombre_item: str) -> tuple[bool, str]:
    """
    Añade combustible al fuego activo.
    Retorna (éxito, mensaje).
    """
    if not getattr(personaje, "fuego_activo", False):
        return False, "No hay fuego activo. Enciéndelo primero."

    if nombre_item not in COMBUSTIBLES:
        return False, f"'{nombre_item}' no es un combustible válido."

    inventario = getattr(personaje, "inventario", [])
    almacen    = getattr(personaje, "almacen", [])
    encontrado = False
    for col in (inventario, almacen):
        for item in col:
            if isinstance(item, dict) and item.get("id") == nombre_item:
                col.remove(item)
                encontrado = True
                break
        if encontrado:
            break

    if not encontrado:
        return False, f"No tienes {nombre_item} disponible."

    ganancia = COMBUSTIBLES[nombre_item]
    personaje.combustible_restante = min(
        getattr(personaje, "combustible_restante", 0) + ganancia,
        300
    )
    return True, f"Añadiste {nombre_item} al fuego. Combustible restante: ~{personaje.combustible_restante} min."


def tick_fuego(personaje: "Sobreviviente", horas: float) -> None:
    """
    Avanza el estado del fuego según las horas transcurridas.
    Consume combustible y apaga si se agota.
    """
    if not getattr(personaje, "fuego_activo", False):
        return

    minutos_consumidos = horas * 60
    actual = getattr(personaje, "combustible_restante", 0)
    nuevo  = actual - minutos_consumidos

    if nuevo <= 0:
        personaje.fuego_activo = False
        personaje.combustible_restante = 0
    else:
        personaje.combustible_restante = nuevo


def apagar_fuego(personaje: "Sobreviviente") -> str:
    """Apaga el fuego manualmente."""
    personaje.fuego_activo = False
    personaje.combustible_restante = 0
    return "Fuego apagado."


def esta_encendido(personaje: "Sobreviviente") -> bool:
    return bool(getattr(personaje, "fuego_activo", False))


def combustible_disponible(personaje: "Sobreviviente") -> int:
    """Devuelve minutos de combustible restantes."""
    return getattr(personaje, "combustible_restante", 0)


def puede_cocinar(personaje: "Sobreviviente") -> bool:
    """El personaje puede cocinar si tiene fuego activo."""
    return esta_encendido(personaje)


# ── helpers privados ──────────────────────────────────────────

def _buscar_metodo_encendido(inventario, almacen):
    """Busca el mejor método de encendido disponible."""
    prioridad = ["encendedor", "pedernal"]
    for col in (inventario, almacen):
        for item in col:
            if isinstance(item, dict) and item.get("id") in prioridad:
                return item["id"], METODOS_ENCENDIDO[item["id"]]
    # Sin herramienta: fricción (muy baja probabilidad)
    return "friccion", METODOS_ENCENDIDO["friccion"]


def _buscar_combustible(inventario, almacen):
    """Busca el mejor combustible disponible (mayor eficiencia calórica)."""
    mejor = None
    mejor_val = 0
    for col in (inventario, almacen):
        for item in col:
            if isinstance(item, dict) and item.get("id") in COMBUSTIBLES:
                val = COMBUSTIBLES[item["id"]]
                if val > mejor_val:
                    mejor = item["id"]
                    mejor_val = val
    return mejor


def _consumir_combustible(personaje: "Sobreviviente", nombre_item: str) -> None:
    """Quita una unidad del combustible del inventario o almacén."""
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in list(col):
            if isinstance(item, dict) and item.get("id") == nombre_item:
                col.remove(item)
                return
