# ============================================================
# engine/save_manager.py
#
# Sistema de guardado con:
#   - Versiones y migraciones automáticas
#   - Escritura atómica (nunca corrompida)
#   - Backups automáticos rotativos (últimos 5)
#   - Tabla de clasificación persistente
#   - Detección de campos nuevos por actualizaciones
# ============================================================

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

# ── Versión actual del formato de guardado ─────────────────────
# Incrementar cuando el esquema del personaje cambie de forma
# incompatible (nuevos campos obligatorios, renombrados, etc.)
SAVE_VERSION = 4

# ── Rutas ──────────────────────────────────────────────────────
DIR_SAVES        = Path("saves")
DIR_BACKUPS      = DIR_SAVES / "backups"
FILE_CURRENT     = DIR_SAVES / "current.json"
FILE_LEADERBOARD = DIR_SAVES / "leaderboard.json"
MAX_BACKUPS      = 5
MAX_LEADERBOARD  = 20


# ══════════════════════════════════════════════════════════════
#  GUARDADO Y CARGA DEL PERSONAJE
# ══════════════════════════════════════════════════════════════

def guardar(personaje, opciones_pendientes: list = None,
            hacer_backup: bool = False) -> bool:
    """
    Guarda el estado completo del personaje.
    Usa escritura atómica: escribe a un archivo temporal
    y solo lo renombra al destino final cuando está completo.
    """
    _asegurar_directorios()

    data = {
        "save_version":        SAVE_VERSION,
        "timestamp":           datetime.now().isoformat(),
        "personaje":           personaje.a_dict(),
        "opciones_pendientes": opciones_pendientes or [],
    }

    if hacer_backup:
        _rotar_backup()

    return _escribir_atomico(FILE_CURRENT, data)


def cargar() -> tuple:
    """
    Carga el personaje guardado.
    Retorna (personaje, opciones_pendientes) o (None, []) si no hay guardado.
    Aplica migraciones automáticas si el save es de una versión anterior.
    """
    from engine.personaje import Sobreviviente

    if not FILE_CURRENT.exists():
        return None, []

    try:
        with open(FILE_CURRENT, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"  [SAVE] Guardado corrupto: {e}")
        print(f"  [SAVE] Intentando recuperar desde backup...")
        data = _recuperar_desde_backup()
        if data is None:
            print(f"  [SAVE] No hay backups disponibles. Partida perdida.")
            return None, []

    version_guardada = data.get("save_version", 1)
    if version_guardada < SAVE_VERSION:
        data = _migrar(data, version_guardada)
        _escribir_atomico(FILE_CURRENT, data)

    try:
        personaje = Sobreviviente.desde_dict(data["personaje"])
        opciones  = data.get("opciones_pendientes", [])
        return personaje, opciones
    except Exception as e:
        print(f"  [SAVE] Error reconstruyendo personaje: {e}")
        return None, []


def hay_guardado() -> bool:
    return FILE_CURRENT.exists()


def info_guardado() -> dict | None:
    """Retorna metadatos del guardado sin cargar el personaje completo."""
    if not FILE_CURRENT.exists():
        return None
    try:
        with open(FILE_CURRENT, "r", encoding="utf-8") as f:
            data = json.load(f)
        p  = data.get("personaje", {})
        ts = data.get("timestamp", "")
        return {
            "nombre":       f"{p.get('nombre','')} {p.get('apellido','')}",
            "background":   p.get("bg_key", "?"),
            "dia":          p.get("dia", 1),
            "salud":        p.get("salud", 0),
            "salud_max":    p.get("salud_max", 100),
            "expediciones": p.get("expediciones_completadas", 0),
            "timestamp":    ts,
            "save_version": data.get("save_version", 1),
        }
    except Exception:
        return None


def borrar_guardado():
    """Borra el guardado actual (al iniciar nueva partida)."""
    if FILE_CURRENT.exists():
        _rotar_backup()
        FILE_CURRENT.unlink()


# ══════════════════════════════════════════════════════════════
#  MIGRACIONES
# ══════════════════════════════════════════════════════════════
#
# Cómo agregar una migración nueva:
#   1. Incrementar SAVE_VERSION al inicio de este archivo
#   2. Añadir un bloque "if version_actual < N" en _migrar()
#   3. Describir qué cambió en el comentario
#
# ──────────────────────────────────────────────────────────────

def _migrar(data: dict, version_actual: int) -> dict:
    """
    Aplica todas las migraciones necesarias en cadena
    desde version_actual hasta SAVE_VERSION.
    """
    p      = data.get("personaje", {})
    cambios = []

    # ── v1 → v2: Se agregó sistema de rasgos ─────────────────
    if version_actual < 2:
        if "rasgos" not in p:
            p["rasgos"] = []
            rasgo_por_bg = {
                "medico":     "instinto_medico",
                "mecanico":   "ingenio_mecanico",
                "militar":    "disciplina_combate",
                "granjero":   "hijo_de_la_tierra",
                "cientifico": "mente_analitica",
                "ladron":     "dedos_ligeros",
            }
            bg_key = p.get("bg_key", "")
            if bg_key in rasgo_por_bg:
                p["rasgos"].append(rasgo_por_bg[bg_key])
            cambios.append("rasgos de background inferidos")

        if "rasgos_en_progreso" not in p:
            p["rasgos_en_progreso"] = {}
            cambios.append("rasgos_en_progreso inicializado")

    # ── v2 → v3: Se agregaron nuevos contadores ───────────────
    if version_actual < 3:
        for campo, default in [
            ("muertes_vistas",         0),
            ("expediciones_nocturnas", 0),
            ("usos_morfina",           0),
        ]:
            if campo not in p:
                p[campo] = default
                cambios.append(f"contador '{campo}' inicializado en {default}")

    # ── v3 → v4: Sistema de XP de skills ─────────────────────
    if version_actual < 4:
        # Pool de XP acumulada por skill
        if "skills_xp" not in p:
            skills_existentes = p.get("skills", {})
            p["skills_xp"] = {k: 0 for k in skills_existentes}
            cambios.append("skills_xp inicializado en 0 para todas las skills")

        # Contadores nuevos para rasgos
        for campo, default in [
            ("libros_leidos",         0),
            ("veces_condicion_grave", 0),
        ]:
            if campo not in p:
                p[campo] = default
                cambios.append(f"contador '{campo}' inicializado en {default}")

    # ── v4 → v5: EJEMPLO para el futuro ──────────────────────
    # if version_actual < 5:
    #     if "nueva_stat" not in p.get("stats", {}):
    #         p["stats"]["nueva_stat"] = 3
    #         cambios.append("stat 'nueva_stat' inicializada en 3")

    if cambios:
        print(f"  [SAVE] Migración v{version_actual}→v{SAVE_VERSION}: "
              f"{', '.join(cambios)}")

    data["personaje"]    = p
    data["save_version"] = SAVE_VERSION
    return data


# ══════════════════════════════════════════════════════════════
#  UTILIDADES INTERNAS
# ══════════════════════════════════════════════════════════════

def _escribir_atomico(ruta: Path, data) -> bool:
    """
    Escritura atómica: escribe a un .tmp y renombra solo cuando está completo.
    Si el proceso muere a mitad, el archivo original permanece intacto.
    """
    ruta_tmp = ruta.with_suffix(".tmp")
    try:
        with open(ruta_tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        ruta_tmp.replace(ruta)
        return True
    except Exception as e:
        print(f"  [SAVE] Error al guardar: {e}")
        if ruta_tmp.exists():
            ruta_tmp.unlink()
        return False


def _cargar_leaderboard() -> list:
    if not FILE_LEADERBOARD.exists():
        return []
    try:
        with open(FILE_LEADERBOARD, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _asegurar_directorios():
    DIR_SAVES.mkdir(exist_ok=True)
    DIR_BACKUPS.mkdir(exist_ok=True)


# ══════════════════════════════════════════════════════════════
#  BACKUPS
# ══════════════════════════════════════════════════════════════

def _rotar_backup():
    """Crea un backup del guardado actual. Mantiene solo los últimos MAX_BACKUPS."""
    if not FILE_CURRENT.exists():
        return
    _asegurar_directorios()

    ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DIR_BACKUPS / f"backup_{ts}.json"
    shutil.copy2(FILE_CURRENT, backup)

    backups = sorted(DIR_BACKUPS.glob("backup_*.json"))
    while len(backups) > MAX_BACKUPS:
        backups.pop(0).unlink()


def _recuperar_desde_backup() -> dict | None:
    if not DIR_BACKUPS.exists():
        return None
    backups = sorted(DIR_BACKUPS.glob("backup_*.json"), reverse=True)
    for backup in backups:
        try:
            with open(backup, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  [SAVE] Recuperado desde: {backup.name}")
            return data
        except Exception:
            continue
    return None


def listar_backups() -> list[dict]:
    if not DIR_BACKUPS.exists():
        return []
    resultado = []
    for backup in sorted(DIR_BACKUPS.glob("backup_*.json"), reverse=True):
        try:
            with open(backup, "r", encoding="utf-8") as f:
                data = json.load(f)
            p = data.get("personaje", {})
            resultado.append({
                "archivo":   backup.name,
                "timestamp": data.get("timestamp", "?"),
                "nombre":    f"{p.get('nombre','')} {p.get('apellido','')}",
                "dia":       p.get("dia", 1),
                "version":   data.get("save_version", 1),
            })
        except Exception:
            pass
    return resultado


def restaurar_backup(nombre_archivo: str) -> bool:
    ruta = DIR_BACKUPS / nombre_archivo
    if not ruta.exists():
        return False
    shutil.copy2(ruta, FILE_CURRENT)
    return True


# ══════════════════════════════════════════════════════════════
#  TABLA DE CLASIFICACIÓN
# ══════════════════════════════════════════════════════════════

def registrar_muerte(personaje, causa: str = "desconocida") -> int:
    """
    Registra al personaje en la tabla de clasificación al morir.
    Retorna su posición en el ranking.
    """
    _asegurar_directorios()
    tabla = _cargar_leaderboard()

    entrada = {
        "nombre":       f"{personaje.nombre} {personaje.apellido}",
        "genero":       personaje.genero,
        "background":   personaje.background["nombre"],
        "dias":         personaje.dia,
        "hora":         personaje.hora,
        "expediciones": personaje.expediciones_completadas,
        "infectados":   personaje.infectados_eliminados,
        "bandidos":     personaje.bandidos_eliminados,
        "items":        personaje.items_recolectados,
        "rasgos":       personaje.rasgos,
        "causa_muerte": causa,
        "fecha":        datetime.now().strftime("%Y-%m-%d"),
        "puntuacion":   _calcular_puntuacion(personaje),
    }

    tabla.append(entrada)
    tabla.sort(key=lambda e: (e["dias"], e["puntuacion"]), reverse=True)
    tabla = tabla[:MAX_LEADERBOARD]

    _escribir_atomico(FILE_LEADERBOARD, tabla)
    return _posicion_en_ranking(entrada, tabla)


def obtener_leaderboard() -> list[dict]:
    return _cargar_leaderboard()


def mostrar_leaderboard(limite: int = 10) -> str:
    tabla = _cargar_leaderboard()
    if not tabla:
        return "\n  (No hay entradas en el ranking aún.)\n"

    AMARILLO = "\033[93m"
    VERDE    = "\033[92m"
    CIAN     = "\033[96m"
    GRIS     = "\033[90m"
    RESET    = "\033[0m"
    NEGRITA  = "\033[1m"

    medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
    lineas = [
        f"\n{AMARILLO}{NEGRITA}{'═'*65}",
        f"  TABLA DE CLASIFICACIÓN — SUPERVIVIENTES CAÍDOS",
        f"{'─'*65}{RESET}",
        f"  {'#':<3} {'Nombre':<22} {'Trasfondo':<22} {'Días':>5} {'Exp':>4} {'Pts':>6}",
        f"{GRIS}{'─'*65}{RESET}",
    ]

    for i, entrada in enumerate(tabla[:limite], 1):
        medalla = medallas.get(i, f" {i}.")
        nombre  = entrada["nombre"][:21]
        bg      = entrada["background"][:21]
        dias    = entrada["dias"]
        exp     = entrada["expediciones"]
        pts     = entrada["puntuacion"]
        causa   = entrada.get("causa_muerte", "?")[:25]
        fecha   = entrada.get("fecha", "")

        if i == 1:   col = f"{AMARILLO}{NEGRITA}"
        elif i <= 3: col = VERDE
        elif i <= 5: col = CIAN
        else:        col = RESET

        lineas.append(
            f"  {col}{medalla:<3} {nombre:<22} {bg:<22} "
            f"{dias:>5}d {exp:>3}x {pts:>6}{RESET}"
        )
        lineas.append(f"       {GRIS}↳ {causa} — {fecha}{RESET}")

    lineas.append(f"{AMARILLO}{'═'*65}{RESET}\n")
    return "\n".join(lineas)


def _calcular_puntuacion(personaje) -> int:
    """Fórmula ponderada que premia longevidad, exploración y combate."""
    pts  = personaje.dia * 100
    pts += personaje.expediciones_completadas * 50
    pts += personaje.infectados_eliminados    * 10
    pts += personaje.bandidos_eliminados      * 20
    pts += personaje.items_recolectados       * 5
    pts += len(personaje.areas_visitadas)     * 30
    pts += len(personaje.rasgos)              * 25
    # Bonus por skills desarrolladas (suma de todos los niveles)
    pts += sum(personaje.skills.values()) // 10
    return pts


def _posicion_en_ranking(entrada: dict, tabla: list) -> int:
    for i, e in enumerate(tabla, 1):
        if (e["nombre"]     == entrada["nombre"]
                and e["fecha"]  == entrada["fecha"]
                and e["puntuacion"] == entrada["puntuacion"]):
            return i
    return len(tabla)
