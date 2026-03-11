# ============================================================
# engine/clima.py
# Motor climático: estaciones, clima diario y efectos ambientales.
# ============================================================

from __future__ import annotations

import random

from data.clima import CLIMAS, ESTACIONES
from engine.constants import clamp

# Climas que disparan riesgo de adquirir condiciones crónicas.
CLIMAS_PELIGROSOS = frozenset({"lluvia_acida", "polvo_toxico", "ventisca_polar", "granizo_acido", "tormenta_radiacion"})

# Ítems que mitigan climas peligrosos específicos.
_PROTECCIONES_CLIMA: dict[str, list[str]] = {
    "polvo_toxico":       ["Máscara de gas", "Mascarilla"],
    "lluvia_acida":       ["Impermeable", "Casco"],
    "granizo_acido":      ["Impermeable", "Casco"],
    "ventisca_polar":     ["Ropa de abrigo"],
    "tormenta_radiacion": ["Mascarilla", "Traje NBQ"],
}


def estacion_actual(dia: int) -> str:
    dia_ciclo = ((max(1, int(dia)) - 1) % 365) + 1
    for nombre, data in ESTACIONES.items():
        if dia_ciclo in data["dias"]:
            return nombre
    return "primavera"


def clima_actual(dia: int, hora: int, area: dict | None = None) -> dict:
    """Genera clima reproducible por bloque temporal para consistencia del tick."""
    est = estacion_actual(dia)
    est_data = ESTACIONES[est]

    bloque_hora = max(0, int(hora) // 6)
    area_key = (area or {}).get("area_key", "refugio")
    seed = f"{dia}:{bloque_hora}:{area_key}:{est}"
    rng = random.Random(seed)

    climas = est_data["climas"]
    total_peso = sum(int(c.get("peso", 1)) for c in climas)
    pick = rng.randint(1, max(1, total_peso))

    acumulado = 0
    clima_id = "templado"
    for c in climas:
        acumulado += int(c.get("peso", 1))
        if pick <= acumulado:
            clima_id = c["id"]
            break

    base = CLIMAS.get(clima_id, CLIMAS["templado"])
    temp_base = int(est_data.get("temp_base_c", 18))
    variacion = rng.randint(-5, 5)

    return {
        "estacion":       est,
        "clima_id":       clima_id,
        "nombre":         base.get("nombre", clima_id),
        "icono":          base.get("icono", "[CLM]"),
        "temperatura_c":  temp_base + variacion,
        "humedad_rel":    int(base.get("humedad_rel", 45)),
        "viento_kmh":     int(base.get("viento_kmh", 8)),
        "mods":           dict(base.get("mods", {})),
        "peligroso":      clima_id in CLIMAS_PELIGROSOS,
        "riesgo_condicion": base.get("riesgo_condicion"),
        "prob_condicion": float(base.get("prob_condicion", 0.0)),
    }


def aplicar_efectos_clima(
    personaje,
    horas: float,
    area: dict | None,
    clima: dict,
    en_refugio: bool = False,
) -> list[str]:
    if horas <= 0:
        return []

    mods = clima.get("mods", {}) if isinstance(clima, dict) else {}
    factor_exposicion = 0.45 if en_refugio else 1.0

    if area and not en_refugio:
        tags = set(str(t).lower() for t in area.get("tags", []))
        if "interior" in tags:
            factor_exposicion *= 0.75
        if "radiacion" in tags:
            factor_exposicion *= 1.15

    # Rasgos que reducen efectos ambientales.
    resist_mult = personaje.obtener_efecto_rasgo("resistencia_ambiental_mult", 1.0)
    factor_exposicion *= resist_mult

    delta_sed    = int(round(float(mods.get("sed_hora",    0)) * horas * factor_exposicion))
    delta_hambre = int(round(float(mods.get("hambre_hora", 0)) * horas * factor_exposicion))
    delta_fatiga = int(round(float(mods.get("fatiga_hora", 0)) * horas * factor_exposicion))
    delta_rad    = int(round(float(mods.get("radiacion_hora", 0)) * horas * factor_exposicion))

    personaje.sed      = clamp(personaje.sed      + delta_sed)
    personaje.hambre   = clamp(personaje.hambre   + delta_hambre)
    personaje.fatiga   = clamp(personaje.fatiga   + delta_fatiga)
    personaje.radiacion = clamp(personaje.radiacion + delta_rad)

    # Máscara mitiga radiación y polvo tóxico.
    if personaje.tiene_item("Mascarilla") and delta_rad > 0:
        personaje.radiacion = max(0, personaje.radiacion - max(1, int(delta_rad * 0.6)))

    # Máscara de gas mitiga polvo tóxico.
    clima_id = clima.get("clima_id", "")
    if clima_id == "polvo_toxico" and personaje.tiene_item("Máscara de gas"):
        factor_exposicion *= 0.3  # Solo para log visual

    salud_tick = int(round(float(mods.get("salud_tick", 0)) * horas * factor_exposicion))
    if salud_tick < 0:
        personaje.salud = max(0, personaje.salud + salud_tick)

    msgs: list[str] = []
    if delta_sed > 0:
        msgs.append(f"Clima: +{delta_sed} sed.")
    if delta_hambre > 0:
        msgs.append(f"Clima: +{delta_hambre} hambre.")
    if delta_fatiga > 0:
        msgs.append(f"Clima: +{delta_fatiga} fatiga.")
    if delta_rad > 0:
        msgs.append(f"Clima/entorno: +{delta_rad} radiación.")
    if salud_tick < 0:
        msgs.append(f"Exposición ambiental: {salud_tick} salud.")

    # Advertencia de clima peligroso sin equipo de protección.
    if clima.get("peligroso") and not en_refugio:
        protecciones = _PROTECCIONES_CLIMA.get(clima_id, [])
        tiene_proteccion = any(personaje.tiene_item(p) for p in protecciones)
        if not tiene_proteccion and protecciones:
            msgs.append(
                f"⚠ {clima['nombre']} sin protección adecuada: consecuencias acumulativas."
            )

    return msgs
