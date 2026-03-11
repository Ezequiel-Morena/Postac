# ============================================================
# engine/estrategia.py — Motor de estrategias de supervivencia
#
# Carga y guarda data/estrategias.json, que actúa como memoria
# colectiva del simulador: cada partida que termina actualiza
# los pesos de decisión del archetype correspondiente usando
# EWMA (Exponential Weighted Moving Average).
#
# No hay modelo IA detrás. El aprendizaje es estadístico:
# si una estrategia lleva sistemáticamente a más días de
# supervivencia, sus pesos se refuerzan; si lleva a muerte
# rápida, se debilitan.
# ============================================================

from __future__ import annotations

import json
import math
import random
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

_RUTA_ESTRATEGIAS = Path(__file__).parent.parent / "data" / "estrategias.json"

# Cuánto vale la última partida frente al historial acumulado.
_EWMA_ALPHA = 0.15

# Cuánto se penaliza/refuerza el peso de una zona según su aporte.
# Si la zona fue la más frecuente en expedición exitosa → +FACTOR.
# Si la zona precedió a la muerte → −FACTOR.
_PESO_AJUSTE_EXITO = 0.08
_PESO_AJUSTE_MUERTE = 0.12
_PESO_MIN = 0.05
_PESO_MAX = 5.0


# ──────────────────────────────────────────────────────────────
#  CARGA / GUARDADO
# ──────────────────────────────────────────────────────────────

def cargar_estrategia() -> dict:
    """Carga el archivo de estrategias. Si no existe, devuelve defaults."""
    if _RUTA_ESTRATEGIAS.exists():
        with open(_RUTA_ESTRATEGIAS, encoding="utf-8") as f:
            return json.load(f)
    # Fallback vacío: el módulo autonomo usará valores globales.
    return {"version": 0, "global": {}, "archetypes": {}, "historial_partidas": [], "metadata": {}}


def guardar_estrategia(estrategia: dict) -> None:
    """Guarda el archivo de estrategias de forma atómica."""
    ruta_tmp = _RUTA_ESTRATEGIAS.with_suffix(".json.tmp")
    estrategia["metadata"]["ultima_actualizacion"] = datetime.now().isoformat(timespec="seconds")
    with open(ruta_tmp, "w", encoding="utf-8") as f:
        json.dump(estrategia, f, ensure_ascii=False, indent=2)
    ruta_tmp.replace(_RUTA_ESTRATEGIAS)


def resetear_estrategia() -> str:
    """
    Elimina el archivo de estrategias aprendidas y lo reemplaza por
    una estructura vacía (sin historial, sin ajustes EWMA acumulados).

    Útil tras actualizaciones del simulador que cambian los parámetros
    de zonas, archetypes o mecánicas de juego.

    Devuelve un mensaje descriptivo del resultado.
    """
    backup = _RUTA_ESTRATEGIAS.with_suffix(".json.bak")

    if _RUTA_ESTRATEGIAS.exists():
        # Guardar backup antes de borrar, por si se arrepiente.
        import shutil
        shutil.copy2(_RUTA_ESTRATEGIAS, backup)
        _RUTA_ESTRATEGIAS.unlink()
        msg = f"Estrategia reseteada. Backup guardado en: {backup.name}"
    else:
        msg = "No existía archivo de estrategias. Nada que resetear."

    return msg


# ──────────────────────────────────────────────────────────────
#  SNAPSHOT Y DIFF DE ESTRATEGIA
# ──────────────────────────────────────────────────────────────

def snapshot_archetype(personaje: "Sobreviviente", estrategia: dict) -> dict:
    """
    Captura el estado actual de la estrategia para el archetype del personaje.
    Devuelve un dict con los valores relevantes ANTES de la actualización,
    para poder comparar después con mostrar_diff_archetype().
    """
    archetype = calcular_archetype(personaje)
    arch_cfg  = estrategia.get("archetypes", {}).get(archetype, {})
    stats     = arch_cfg.get("estadisticas", {})
    pesos     = arch_cfg.get("pesos_zonas", {})

    return {
        "archetype":     archetype,
        "runs":          stats.get("runs", 0),
        "dias_promedio": stats.get("dias_promedio", 0.0),
        "mejor_racha":   stats.get("mejor_racha", 0),
        "tasa_violenta": stats.get("tasa_muerte_violenta", 0.0),
        "tasa_inanicion": stats.get("tasa_muerte_inanicion", 0.0),
        "pesos_zonas":   dict(pesos),  # copia para no referenciar el original
    }


def mostrar_diff_archetype(snap_antes: dict, estrategia: dict) -> str:
    """
    Compara el snapshot anterior con el estado actual de la estrategia
    y devuelve un resumen formateado de los cambios producidos.
    """
    archetype = snap_antes["archetype"]
    arch_cfg  = estrategia.get("archetypes", {}).get(archetype, {})
    stats     = arch_cfg.get("estadisticas", {})
    pesos     = arch_cfg.get("pesos_zonas", {})

    lineas: list[str] = []
    lineas.append(f"  Archetype: {archetype}")

    # ── Estadísticas globales ─────────────────────────────────
    runs_a  = snap_antes["runs"]
    runs_d  = stats.get("runs", runs_a)
    dias_a  = snap_antes["dias_promedio"]
    dias_d  = stats.get("dias_promedio", dias_a)
    racha_a = snap_antes["mejor_racha"]
    racha_d = stats.get("mejor_racha", racha_a)

    lineas.append(f"  runs:          {runs_a} → {runs_d}")
    lineas.append(f"  días prom:     {dias_a:.2f} → {dias_d:.2f}  {_flecha(dias_d, dias_a)}")
    if racha_d != racha_a:
        lineas.append(f"  mejor racha:   {racha_a} → {racha_d}  ★ nuevo récord")

    # ── Pesos de zonas con cambios ────────────────────────────
    zonas_cambiadas: list[tuple[str, float, float]] = []
    todas_zonas = set(snap_antes["pesos_zonas"]) | set(pesos)
    for zona in sorted(todas_zonas):
        p_a = snap_antes["pesos_zonas"].get(zona, 1.0)
        p_d = pesos.get(zona, 1.0)
        if abs(p_d - p_a) >= 0.001:
            zonas_cambiadas.append((zona, p_a, p_d))

    if zonas_cambiadas:
        lineas.append("  pesos zonas:")
        for zona, p_a, p_d in zonas_cambiadas:
            lineas.append(f"    {zona:<28} {p_a:.4f} → {p_d:.4f}  {_flecha(p_d, p_a)}")
    else:
        lineas.append("  pesos zonas:   sin cambios")

    return "\n".join(lineas)


def _flecha(nuevo: float, viejo: float) -> str:
    """Devuelve ↑ ↓ o = según la dirección del cambio."""
    if nuevo > viejo + 0.001:
        return "↑"
    if nuevo < viejo - 0.001:
        return "↓"
    return "="

# ──────────────────────────────────────────────────────────────
#  ARCHETYPE
# ──────────────────────────────────────────────────────────────

def calcular_archetype(personaje: "Sobreviviente") -> str:
    """
    Calcula el archetype del personaje a partir de su background.
    El bg_key es el identificador primario de estrategia.
    Si el personaje tiene skills muy por encima del background base,
    el archetype puede derivar (ej: granjero con combate_cac alto → cazador).
    """
    bg_key = getattr(personaje, "bg_key", "")
    if bg_key:
        return bg_key

    # Fallback: archetype por skill dominante si no hay bg_key.
    skills = getattr(personaje, "skills", {})
    if not skills:
        return "granjero"  # Default conservador

    skill_dominante = max(skills, key=lambda k: skills[k])
    return _SKILL_A_ARCHETYPE.get(skill_dominante, "granjero")


_SKILL_A_ARCHETYPE: dict[str, str] = {
    "combate_cac":        "militar",
    "combate_distancia":  "cazador",
    "medicina":           "medico",
    "farmacologia":       "medico",
    "mecanica":           "mecanico",
    "carpinteria":        "mecanico",
    "supervivencia":      "granjero",
    "botanica":           "granjero",
    "sigilo":             "ladron",
    "saqueo":             "ladron",
    "atletismo":          "bombero",
    "cocina":             "cocinero",
    "persuasion":         "periodista",
    "liderazgo":          "docente",
    "balistica":          "militar",
}


def obtener_config_archetype(personaje: "Sobreviviente", estrategia: dict) -> dict:
    """
    Devuelve la configuración de estrategia para el archetype del personaje.
    Usa _config_archetype_default como base y sobreescribe con los valores
    aprendidos del archivo, garantizando que el resultado siempre esté completo.
    """
    archetype  = calcular_archetype(personaje)
    global_cfg = estrategia.get("global", {})
    arch_cfg   = estrategia.get("archetypes", {}).get(archetype, {})

    # Base garantizada con todos los campos requeridos.
    base = _config_archetype_default(archetype)

    # Fusión en orden de precedencia: default → global → archetype aprendido.
    config = {**base, **global_cfg, **arch_cfg}
    config["_archetype"] = archetype
    return config


# ──────────────────────────────────────────────────────────────
#  ACTUALIZACIÓN POST-PARTIDA (aprendizaje)
# ──────────────────────────────────────────────────────────────

def registrar_fin_partida(
    personaje: "Sobreviviente",
    estrategia: dict,
    causa_muerte: str,
    zonas_visitadas_esta_partida: list[str],
    zona_muerte: str | None,
) -> None:
    """
    Actualiza el archivo de estrategias tras la muerte del personaje.

    Mecanismo:
    - Actualiza días promedio (EWMA).
    - Penaliza el peso de la zona donde murió el personaje.
    - Refuerza los pesos de las zonas que se visitaron frecuentemente
      en partidas largas (correlación positiva días↔zona).
    - Registra la partida en historial para análisis posterior.
    """
    archetype = calcular_archetype(personaje)
    dias_vividos = getattr(personaje, "dia", 1)

    # Asegurar que el archetype existe en el dict.
    if archetype not in estrategia.get("archetypes", {}):
        estrategia.setdefault("archetypes", {})[archetype] = _config_archetype_default(archetype)

    arch_cfg   = estrategia["archetypes"][archetype]
    stats      = arch_cfg.setdefault("estadisticas", {})
    pesos      = arch_cfg.setdefault("pesos_zonas", {})

    # ── EWMA de días promedio ─────────────────────────────────
    runs_prev       = stats.get("runs", 0)
    dias_prev       = stats.get("dias_promedio", dias_vividos)
    stats["dias_promedio"] = round(
        _ewma(dias_prev, dias_vividos, _EWMA_ALPHA), 2
    )
    stats["runs"] = runs_prev + 1
    stats["mejor_racha"] = max(stats.get("mejor_racha", 0), dias_vividos)

    # ── Tasa de tipo de muerte ────────────────────────────────
    es_violenta  = "herida" in causa_muerte or "combate" in causa_muerte or "infeccion" in causa_muerte
    es_inanicion = "inanición" in causa_muerte or "deshidrat" in causa_muerte
    _actualizar_tasa(stats, "tasa_muerte_violenta",  1.0 if es_violenta else 0.0)
    _actualizar_tasa(stats, "tasa_muerte_inanicion", 1.0 if es_inanicion else 0.0)

    # ── Expediciones por día ──────────────────────────────────
    exps = getattr(personaje, "expediciones_completadas", 0)
    exp_por_dia = exps / max(1, dias_vividos)
    _actualizar_tasa(stats, "expediciones_por_dia", exp_por_dia)

    # ── Ajuste de pesos de zonas ──────────────────────────────
    _ajustar_pesos_zonas(pesos, zonas_visitadas_esta_partida, zona_muerte, dias_vividos, stats)

    # ── Metadatos globales ────────────────────────────────────
    meta = estrategia.setdefault("metadata", {})
    meta["total_runs"] = meta.get("total_runs", 0) + 1
    meta["total_dias_simulados"] = meta.get("total_dias_simulados", 0) + dias_vividos

    # ── Historial resumido (últimas 50 partidas) ──────────────
    historial = estrategia.setdefault("historial_partidas", [])
    historial.append({
        "ts":       datetime.now().isoformat(timespec="seconds"),
        "archetype": archetype,
        "dias":     dias_vividos,
        "causa":    causa_muerte,
        "zonas":    zonas_visitadas_esta_partida[-10:],  # últimas 10 zonas
    })
    if len(historial) > 50:
        estrategia["historial_partidas"] = historial[-50:]


# ──────────────────────────────────────────────────────────────
#  HELPERS PRIVADOS
# ──────────────────────────────────────────────────────────────

def _ewma(valor_previo: float, nuevo_valor: float, alpha: float) -> float:
    """Exponential Weighted Moving Average."""
    return alpha * nuevo_valor + (1 - alpha) * valor_previo


def _actualizar_tasa(stats: dict, clave: str, nuevo_valor: float) -> None:
    """Actualiza una tasa con EWMA."""
    prev = stats.get(clave, nuevo_valor)
    stats[clave] = round(_ewma(prev, nuevo_valor, _EWMA_ALPHA), 4)


def _ajustar_pesos_zonas(
    pesos: dict,
    zonas_visitadas: list[str],
    zona_muerte: str | None,
    dias_vividos: int,
    stats: dict,
) -> None:
    """
    Ajusta los pesos de zonas según el rendimiento de la partida.

    Lógica:
    - Partidas largas (sobre la media) → reforzar zonas frecuentes.
    - Partidas cortas (bajo la media) → penalizar zona de muerte.
    - La magnitud del ajuste escala con la desviación respecto a la media.
    """
    if not zonas_visitadas:
        return

    dias_promedio = stats.get("dias_promedio", dias_vividos)
    # Ratio de rendimiento: >1 = mejor que la media, <1 = peor.
    ratio = dias_vividos / max(1, dias_promedio)

    frecuencia: dict[str, int] = {}
    for zona in zonas_visitadas:
        frecuencia[zona] = frecuencia.get(zona, 0) + 1

    for zona, freq in frecuencia.items():
        peso_actual = pesos.get(zona, 1.0)
        # La zona de muerte nunca se refuerza — siempre se penaliza abajo.
        es_zona_muerte = (zona == zona_muerte)
        if ratio >= 1.0 and not es_zona_muerte:
            # Partida exitosa: reforzar zonas visitadas frecuentemente.
            ajuste = _PESO_AJUSTE_EXITO * math.log1p(freq) * (ratio - 1.0 + 0.5)
            pesos[zona] = round(min(_PESO_MAX, peso_actual + ajuste), 4)
        elif not es_zona_muerte:
            # Partida corta: penalizar ligeramente zonas visitadas.
            ajuste = _PESO_AJUSTE_EXITO * 0.3 * (1.0 - ratio)
            pesos[zona] = round(max(_PESO_MIN, peso_actual - ajuste), 4)

    # Penalización directa para la zona donde murió (señal negativa fuerte).
    if zona_muerte and zona_muerte in pesos:
        pesos[zona_muerte] = round(
            max(_PESO_MIN, pesos[zona_muerte] - _PESO_AJUSTE_MUERTE),
            4
        )
        stats["zona_mas_letal"] = zona_muerte

    # Zona más exitosa = la más frecuente en partidas largas.
    if ratio >= 1.2 and zonas_visitadas:
        stats["zona_mas_exitosa"] = max(frecuencia, key=lambda z: frecuencia[z])


def _config_archetype_default(archetype: str) -> dict:
    """Genera configuración por defecto para un archetype nuevo."""
    return {
        "_descripcion": f"Archetype derivado automáticamente: {archetype}",
        "pesos_zonas": {zona: 1.0 for zona in [
            "hospital", "supermercado", "comisaria", "farmacia",
            "casa_abandonada", "fabrica", "biblioteca", "laboratorio",
            "gasolinera", "estadio", "puerto_seco", "reserva_forestal"
        ]},
        "umbral_descanso_fatiga": 70,
        "umbral_descanso_hambre": 70,
        "umbral_descanso_sed": 73,
        "umbral_descanso_salud_pct": 0.35,
        "max_expediciones_seguidas": 3,
        "prioridad_inventario": ["agua", "comida", "medicina"],
        "habilidad_dominante": archetype,
        "estadisticas": {
            "runs": 0,
            "dias_promedio": 0.0,
            "mejor_racha": 0,
            "tasa_muerte_violenta": 0.0,
            "tasa_muerte_inanicion": 0.0,
            "expediciones_por_dia": 0.0,
            "zona_mas_exitosa": "",
            "zona_mas_letal": "",
        }
    }
