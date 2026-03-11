# ============================================================
# engine/autoconsumo.py
# Motor de autoconsumo autónomo para entidades del refugio.
#
# Gestiona la satisfacción de necesidades (hambre, sed, salud)
# de jugador y NPCs. Prioriza inventario personal antes del almacén
# compartido. La personalidad de cada entidad determina cuándo consume
# y si sus dependientes son atendidos antes que ella misma.
# ============================================================

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from engine.almacen import consumir_tipo

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente


# ── Perfiles de consumo por personalidad ──────────────────────────────────────
# hambre/sed : umbral a partir del cual el NPC busca consumir (0-100).
#              Egoístas = umbral bajo (comen rápido).
#              Altruistas = umbral alto (aguantan para que otros coman).
# salud      : umbral mínimo antes de buscar medicina.
# familia    : estrategia con dependientes.
#              'hijos_primero' → protege a sus hijos activamente.
#              'equilibrado'   → cuidado normal.
#              'propio_primero' → se atiende antes que a sus hijos.

_PERFILES: dict[str, dict] = {
    # Altruistas: aguantan hambre para que quede comida para otros
    "generoso":    {"hambre": 80, "sed": 80, "salud": 35, "familia": "hijos_primero"},
    "leal":        {"hambre": 78, "sed": 78, "salud": 38, "familia": "hijos_primero"},
    "protector":   {"hambre": 82, "sed": 82, "salud": 30, "familia": "hijos_primero"},
    "empatico":    {"hambre": 75, "sed": 75, "salud": 40, "familia": "hijos_primero"},
    # Responsables: equilibrados, ligeramente protectores
    "estoico":     {"hambre": 72, "sed": 72, "salud": 42, "familia": "equilibrado"},
    "pragmatico":  {"hambre": 65, "sed": 65, "salud": 45, "familia": "equilibrado"},
    "valiente":    {"hambre": 70, "sed": 70, "salud": 40, "familia": "equilibrado"},
    "optimista":   {"hambre": 68, "sed": 68, "salud": 42, "familia": "equilibrado"},
    "melancolico": {"hambre": 70, "sed": 70, "salud": 40, "familia": "equilibrado"},
    "reservado":   {"hambre": 65, "sed": 65, "salud": 45, "familia": "equilibrado"},
    "curioso":     {"hambre": 67, "sed": 67, "salud": 44, "familia": "equilibrado"},
    # Egoístas: consumen antes de que escaseen los recursos
    "oportunista": {"hambre": 50, "sed": 50, "salud": 55, "familia": "propio_primero"},
    "hosco":       {"hambre": 55, "sed": 55, "salud": 50, "familia": "propio_primero"},
    "desconfiado": {"hambre": 52, "sed": 52, "salud": 52, "familia": "propio_primero"},
    "cauteloso":   {"hambre": 58, "sed": 58, "salud": 48, "familia": "propio_primero"},
}

_PERFIL_NEUTRO: dict = {
    "hambre": 65, "sed": 65, "salud": 45, "familia": "equilibrado",
}

# Umbrales aplicados a HIJOS según la estrategia del progenitor más protector
_UMBRALES_HIJOS: dict[str, dict] = {
    "hijos_primero": {"hambre": 50, "sed": 50, "salud": 55},
    "equilibrado":   {"hambre": 65, "sed": 65, "salud": 42},
    "propio_primero": {"hambre": 85, "sed": 85, "salud": 25},
}

# Ganancias fijas por tipo de ítem (cuando se consume directamente del almacén)
_GANANCIA_COMIDA: int = 30
_GANANCIA_AGUA: int = 30
_GANANCIA_MEDICINA: int = 25


def _perfil(personalidad: str) -> dict:
    """Devuelve el perfil de consumo para una personalidad dada."""
    return _PERFILES.get(personalidad, _PERFIL_NEUTRO)


def autoconsumo_npc(
    estado: dict,
    almacen: list[dict],
    nombre: str = "",
) -> list[str]:
    """
    Satisface las necesidades de un NPC usando el almacén compartido.
    Los umbrales de consumo dependen de su personalidad: los egoístas
    consumen antes; los altruistas aguantan para dejar recursos a otros.

    Returns:
        Lista de mensajes narrativos sobre lo que el NPC consumió.
    """
    personalidad = estado.get("personalidad", "pragmatico")
    perfil = _perfil(personalidad)
    nombre_display = nombre or estado.get("nombre", "?")
    mensajes: list[str] = []

    hambre = int(estado.get("hambre", 0))
    sed = int(estado.get("sed", 0))
    salud = int(estado.get("salud", 100))

    if hambre > perfil["hambre"]:
        consumido = consumir_tipo(almacen, "comida", 1)
        if consumido:
            estado["hambre"] = max(0, hambre - _GANANCIA_COMIDA)
            mensajes.append(f"{nombre_display} comió del almacén")

    # NPCs pueden no tener sed si el campo no existe (migración parcial)
    if sed and sed > perfil["sed"]:
        consumido = consumir_tipo(almacen, "agua", 1)
        if consumido:
            estado["sed"] = max(0, sed - _GANANCIA_AGUA)
            mensajes.append(f"{nombre_display} bebió del almacén")

    if salud < perfil["salud"]:
        consumido = consumir_tipo(almacen, "medicina", 1)
        if consumido:
            estado["salud"] = min(100, salud + _GANANCIA_MEDICINA)
            mensajes.append(f"{nombre_display} usó medicina del almacén")

    return mensajes


def _autoconsumo_menor(
    estado: dict,
    almacen: list[dict],
    umbral: dict,
) -> list[str]:
    """Autoconsumo para un menor con umbrales ajustados por la protección parental."""
    nombre = estado.get("nombre", "?")
    mensajes: list[str] = []

    hambre = int(estado.get("hambre", 0))
    salud = int(estado.get("salud", 100))

    if hambre > umbral["hambre"]:
        consumido = consumir_tipo(almacen, "comida", 1)
        if consumido:
            estado["hambre"] = max(0, hambre - _GANANCIA_COMIDA)
            mensajes.append(f"{nombre} (menor) comió del almacén")

    if salud < umbral["salud"]:
        consumido = consumir_tipo(almacen, "medicina", 1)
        if consumido:
            estado["salud"] = min(100, salud + _GANANCIA_MEDICINA)
            mensajes.append(f"{nombre} (menor) recibió medicina del almacén")

    return mensajes


def _umbral_para_menor(
    menor_id: str,
    npcs_presentes: dict[str, dict],
) -> dict:
    """
    Calcula los umbrales de consumo para un menor según el perfil del
    progenitor más protector presente en el refugio.

    Un padre 'protector' baja los umbrales de sus hijos (los alimenta antes).
    Un padre 'oportunista' los sube (los atiende solo en crisis extrema).
    """
    orden = {"hijos_primero": 0, "equilibrado": 1, "propio_primero": 2}
    mejor = "equilibrado"

    for _, estado_padre in npcs_presentes.items():
        if menor_id not in estado_padre.get("hijos", []):
            continue
        pers = estado_padre.get("personalidad", "pragmatico")
        estrategia_padre = _perfil(pers)["familia"]
        if orden[estrategia_padre] < orden[mejor]:
            mejor = estrategia_padre

    return _UMBRALES_HIJOS[mejor]


def resolver_autoconsumo_refugio(
    personaje: "Sobreviviente",
    rng: random.Random,
) -> list[str]:
    """
    Resuelve el autoconsumo de todos los habitantes del refugio en un tick.

    Orden de procesamiento (refleja dinámicas sociales reales):
      1. Menores/dependientes — siempre se atienden primero.
      2. Adultos con estrategia 'hijos_primero' o 'equilibrado'.
      3. Adultos con estrategia 'propio_primero' (egoístas).

    El jugador NO se incluye aquí: su autoconsumo durante el tick es solo
    en situación crítica (umbral 90). Para consumo activo usa autoconsumo()
    en InventoryMixin.
    """
    mensajes: list[str] = []
    almacen = getattr(personaje, "almacen", [])

    # Solo NPCs presentes en el refugio
    npcs_presentes: dict[str, dict] = {
        npc_id: estado
        for npc_id, estado in personaje.relaciones_refugio.items()
        if not estado.get("en_expedicion", False)
    }

    menores = [
        (nid, est) for nid, est in npcs_presentes.items()
        if est.get("es_menor", False)
    ]
    adultos = [
        (nid, est) for nid, est in npcs_presentes.items()
        if not est.get("es_menor", False)
    ]

    # Separar adultos por estrategia familiar
    protectores = [
        (nid, est) for nid, est in adultos
        if _perfil(est.get("personalidad", ""))["familia"] != "propio_primero"
    ]
    egoistas = [
        (nid, est) for nid, est in adultos
        if _perfil(est.get("personalidad", ""))["familia"] == "propio_primero"
    ]

    # Paso 1: Menores primero
    for menor_id, estado in menores:
        umbral = _umbral_para_menor(menor_id, npcs_presentes)
        mensajes += _autoconsumo_menor(estado, almacen, umbral)

    # Paso 2: Adultos protectores/equilibrados
    for _, estado in protectores:
        mensajes += autoconsumo_npc(estado, almacen)

    # Paso 3: Adultos egoístas (lo que quede)
    for _, estado in egoistas:
        mensajes += autoconsumo_npc(estado, almacen)

    return mensajes
