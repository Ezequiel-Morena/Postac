# ============================================================
# engine/pesca.py — Sistema de pesca
#
# La pesca es una actividad de bajo riesgo pero alta paciencia.
# Requiere herramienta, acceso al agua y tiempo.
# El rendimiento depende de la habilidad, la suerte y la zona.
# ============================================================

from __future__ import annotations
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

# Catálogo de peces por tipo de zona
PECES_POR_ZONA: dict[str, list[dict]] = {
    "rio": [
        {"id": "pez_pequeno", "nombre": "Trucha pequeña",  "peso_prob": 0.45, "nivel_min": 0},
        {"id": "pez_mediano", "nombre": "Trucha grande",   "peso_prob": 0.30, "nivel_min": 15},
        {"id": "pez_mediano", "nombre": "Pejerrey",        "peso_prob": 0.20, "nivel_min": 10},
        {"id": "pez_pequeno", "nombre": "Bagre",           "peso_prob": 0.05, "nivel_min": 0},
    ],
    "lago": [
        {"id": "pez_pequeno", "nombre": "Carpa pequeña",   "peso_prob": 0.40, "nivel_min": 0},
        {"id": "pez_mediano", "nombre": "Carpa grande",    "peso_prob": 0.25, "nivel_min": 20},
        {"id": "pez_mediano", "nombre": "Lucio",           "peso_prob": 0.20, "nivel_min": 30},
        {"id": "pez_pequeno", "nombre": "Pez gato",        "peso_prob": 0.15, "nivel_min": 0},
    ],
    "costa": [
        {"id": "pez_mediano", "nombre": "Corvina",         "peso_prob": 0.30, "nivel_min": 10},
        {"id": "pez_pequeno", "nombre": "Pejerrey de mar", "peso_prob": 0.40, "nivel_min": 0},
        {"id": "pez_mediano", "nombre": "Lenguado",        "peso_prob": 0.15, "nivel_min": 25},
        {"id": "pez_pequeno", "nombre": "Anchoa",          "peso_prob": 0.15, "nivel_min": 0},
    ],
    "default": [
        {"id": "pez_pequeno", "nombre": "Pez pequeño",    "peso_prob": 0.60, "nivel_min": 0},
        {"id": "pez_mediano", "nombre": "Pez mediano",    "peso_prob": 0.40, "nivel_min": 20},
    ],
}

# Tags de zona que habilitan la pesca
TAGS_ZONA_PESCA = {"agua", "rio", "lago", "costa", "puerto"}

# Probabilidad base de captura por hora de pesca
PROB_BASE_CAPTURA_POR_HORA = 0.25
# Bonus de caña vs sin herramienta
BONUS_CANA = 0.20
# Pesca a mano solo en zonas poco profundas
PESCA_MANO_TAGS = {"rio", "poza"}


def puede_pescar(personaje: "Sobreviviente", zona: dict) -> tuple[bool, str]:
    """
    Verifica si el personaje puede pescar en la zona dada.
    Retorna (puede: bool, razon: str).
    """
    tags = set(zona.get("tags", []))
    if not tags.intersection(TAGS_ZONA_PESCA):
        return False, "Esta zona no tiene acceso a agua para pescar."
    return True, ""


def intentar_pesca(
    personaje: "Sobreviviente",
    zona: dict,
    horas: float = 2.0,
) -> dict:
    """
    Resuelve una sesión de pesca.

    Retorna dict con:
        - exito: bool
        - capturas: list[dict]  (ítems obtenidos)
        - xp_ganada: int
        - mensaje: str
        - fatiga_costo: int
        - horas_usadas: float
    """
    resultado = {
        "exito": False,
        "capturas": [],
        "xp_ganada": 0,
        "mensaje": "",
        "fatiga_costo": int(horas * 3),
        "horas_usadas": horas,
    }

    puede, razon = puede_pescar(personaje, zona)
    if not puede:
        resultado["mensaje"] = razon
        return resultado

    skill_pesca = personaje.skills.get("pesca", 0)
    tiene_cana  = _tiene_herramienta_pesca(personaje)
    tags        = set(zona.get("tags", []))

    prob_por_hora = PROB_BASE_CAPTURA_POR_HORA
    if tiene_cana:
        prob_por_hora += BONUS_CANA
    elif not tags.intersection(PESCA_MANO_TAGS):
        prob_por_hora *= 0.3  # muy difícil sin herramienta en zona profunda

    prob_por_hora = min(0.85, prob_por_hora + skill_pesca * 0.004)

    intentos = max(1, int(horas))
    capturas = []

    for _ in range(intentos):
        if random.random() < prob_por_hora:
            pez = _seleccionar_pez(zona, skill_pesca)
            if pez:
                capturas.append(pez)

    xp_base = 3 if capturas else 1
    if hasattr(personaje, "ganar_xp_skill"):
        personaje.ganar_xp_skill("pesca", xp_base)
    resultado["xp_ganada"] = xp_base

    if tiene_cana:
        _desgastar_herramienta_pesca(personaje)

    if capturas:
        resultado["exito"]    = True
        resultado["capturas"] = capturas
        nombres = ", ".join(c.get("nombre", c.get("id", "?")) for c in capturas)
        resultado["mensaje"]  = f"Pescaste {len(capturas)} pez/peces: {nombres}."
    else:
        resultado["mensaje"]  = f"Pasaste {horas:.0f}h pescando pero no hubo suerte."

    personaje.fatiga = min(100, personaje.fatiga + resultado["fatiga_costo"])

    return resultado


# ── helpers privados ──────────────────────────────────────────

def _tiene_herramienta_pesca(personaje: "Sobreviviente") -> bool:
    herramientas = {"cana_pesca", "red_pesca", "arpon"}
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in col:
            if isinstance(item, dict) and item.get("id") in herramientas:
                return True
    return False


def _desgastar_herramienta_pesca(personaje: "Sobreviviente") -> None:
    for col in (getattr(personaje, "inventario", []), getattr(personaje, "almacen", [])):
        for item in col:
            if isinstance(item, dict) and item.get("id") == "cana_pesca":
                usos = item.get("usos", 1)
                if usos <= 1:
                    col.remove(item)
                else:
                    item["usos"] = usos - 1
                return


def _seleccionar_pez(zona: dict, skill_pesca: int) -> dict | None:
    tags = set(zona.get("tags", []))
    tipo = "default"
    for t in ("rio", "lago", "costa"):
        if t in tags:
            tipo = t
            break

    pool = PECES_POR_ZONA.get(tipo, PECES_POR_ZONA["default"])
    disponibles = [p for p in pool if skill_pesca >= p["nivel_min"]]
    if not disponibles:
        disponibles = pool  # fallback

    pesos = [p["peso_prob"] for p in disponibles]
    elegido = random.choices(disponibles, weights=pesos, k=1)[0]
    return {"id": elegido["id"], "nombre": elegido["nombre"], "cantidad": 1}
