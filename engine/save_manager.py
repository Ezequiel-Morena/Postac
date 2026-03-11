# ============================================================
# engine/save_manager.py
#
# Sistema de guardado con:
#   - Versiones y migraciones automáticas
#   - Escritura atómica (nunca corrompida)
#   - Backups rotativos (últimos 5)
#   - Tabla de clasificación persistente
#   - Bitácoras por partida en saves/historias/<partida_id>/
#   - Gestión de historias: listar, eliminar bitácoras, eliminar del ranking
# ============================================================

import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SAVE_VERSION = 17

DIR_SAVES        = Path("saves")
DIR_BACKUPS      = DIR_SAVES / "backups"
DIR_HISTORIAS    = DIR_SAVES / "historias"
FILE_CURRENT     = DIR_SAVES / "current.json"
FILE_LEADERBOARD = DIR_SAVES / "leaderboard.json"
MAX_BACKUPS      = 5
MAX_LEADERBOARD  = 20


# ══════════════════════════════════════════════════════════════
#  GUARDADO Y CARGA
# ══════════════════════════════════════════════════════════════

def guardar(personaje, opciones_pendientes: list = None,
            hacer_backup: bool = False) -> bool:
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
    from engine.personaje import Sobreviviente
    if not FILE_CURRENT.exists():
        return None, []
    try:
        with open(FILE_CURRENT, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Guardado corrupto: %s", e)
        data = _recuperar_desde_backup()
        if data is None:
            logger.error("Sin backups disponibles. Partida perdida.")
            return None, []

    version = data.get("save_version", 1)
    if version < SAVE_VERSION:
        data = _migrar(data, version)
        _escribir_atomico(FILE_CURRENT, data)

    try:
        return Sobreviviente.desde_dict(data["personaje"]), data.get("opciones_pendientes", [])
    except Exception as e:
        logger.error("Error reconstruyendo personaje: %s", e)
        return None, []


def hay_guardado() -> bool:
    return FILE_CURRENT.exists()


def info_guardado() -> dict | None:
    if not FILE_CURRENT.exists():
        return None
    try:
        with open(FILE_CURRENT, "r", encoding="utf-8") as f:
            data = json.load(f)
        p  = data.get("personaje", {})
        return {
            "nombre":       f"{p.get('nombre','')} {p.get('apellido','')}",
            "background":   p.get("bg_key", "?"),
            "dia":          p.get("dia", 1),
            "salud":        p.get("salud", 0),
            "salud_max":    p.get("salud_max", 100),
            "expediciones": p.get("expediciones_completadas", 0),
            "timestamp":    data.get("timestamp", ""),
            "save_version": data.get("save_version", 1),
            "partida_id":   p.get("partida_id", ""),
        }
    except Exception:
        return None


def borrar_guardado() -> None:
    if FILE_CURRENT.exists():
        _rotar_backup()
        FILE_CURRENT.unlink()


# ══════════════════════════════════════════════════════════════
#  BITÁCORAS POR PARTIDA
# ══════════════════════════════════════════════════════════════

def directorio_historia(partida_id: str) -> Path:
    """Retorna (y crea si no existe) el directorio de bitácoras de una partida."""
    d = DIR_HISTORIAS / partida_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def siguiente_ruta_bitacora(partida_id: str, dia: int) -> Path:
    """
    Calcula la ruta para la próxima bitácora del día N de una partida.
    Si ya existe bitacora_dia3_exp1.png, retorna bitacora_dia3_exp2.png.
    Nunca sobreescribe.
    """
    d       = directorio_historia(partida_id)
    prefijo = f"bitacora_dia{dia}_exp"
    n       = 1
    while (d / f"{prefijo}{n}.png").exists():
        n += 1
    return d / f"{prefijo}{n}.png"


def siguiente_ruta_texto(partida_id: str, dia: int) -> Path:
    """Igual que siguiente_ruta_bitacora pero para .txt."""
    d       = directorio_historia(partida_id)
    prefijo = f"bitacora_dia{dia}_exp"
    n       = 1
    while (d / f"{prefijo}{n}.txt").exists():
        n += 1
    return d / f"{prefijo}{n}.txt"


# ══════════════════════════════════════════════════════════════
#  GESTIÓN DE HISTORIAS
# ══════════════════════════════════════════════════════════════

def listar_historias() -> list[dict]:
    """
    Lista todas las historias guardadas (directorios en saves/historias/).
    Retorna lista de dicts con metadatos básicos, ordenada por reciente primero.
    """
    if not DIR_HISTORIAS.exists():
        return []
    historias = []
    for d in sorted(DIR_HISTORIAS.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        pngs = list(d.glob("*.png"))
        txts = list(d.glob("*.txt"))
        historias.append({
            "partida_id":   d.name,
            "directorio":   d,
            "num_bitacoras": len(pngs),
            "num_textos":    len(txts),
            "tamaño_mb":     round(sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1024 / 1024, 2),
        })
    return historias


def listar_historias_leaderboard() -> list[dict]:
    """Lista entradas del leaderboard con sus partida_id (para cruzar con historias)."""
    tabla = _cargar_leaderboard()
    return [{"partida_id": e.get("partida_id", ""), "nombre": e.get("nombre", ""), "dias": e.get("dias", 0)}
            for e in tabla if e.get("partida_id")]


def eliminar_bitacoras_historia(partida_id: str) -> tuple[bool, str]:
    """
    Elimina SOLO las imágenes y textos de la historia (libera espacio de disco).
    El registro del leaderboard se mantiene intacto.
    """
    d = DIR_HISTORIAS / partida_id
    if not d.exists():
        return False, f"No se encontró la historia '{partida_id}'"
    shutil.rmtree(d)
    return True, f"Bitácoras de '{partida_id}' eliminadas."


def eliminar_entrada_leaderboard(partida_id: str) -> tuple[bool, str]:
    """
    Elimina SOLO la entrada del leaderboard correspondiente a esa partida.
    Las bitácoras se mantienen.
    """
    tabla = _cargar_leaderboard()
    antes = len(tabla)
    tabla = [e for e in tabla if e.get("partida_id") != partida_id]
    if len(tabla) == antes:
        return False, "No se encontró esa partida en el ranking."
    _escribir_atomico(FILE_LEADERBOARD, tabla)
    return True, "Entrada eliminada del ranking."


def eliminar_historia_completa(partida_id: str) -> tuple[bool, str]:
    """
    Elimina TANTO las bitácoras como la entrada del leaderboard.
    Operación de limpieza total.
    """
    ok1, msg1 = eliminar_bitacoras_historia(partida_id)
    ok2, msg2 = eliminar_entrada_leaderboard(partida_id)
    return True, f"{msg1}  {msg2}"


def eliminar_todas_las_historias(incluir_leaderboard: bool = False) -> str:
    """
    Elimina TODAS las bitácoras de todas las partidas.
    Si incluir_leaderboard=True también vacía el leaderboard.
    """
    if DIR_HISTORIAS.exists():
        shutil.rmtree(DIR_HISTORIAS)
    DIR_HISTORIAS.mkdir(parents=True, exist_ok=True)
    if incluir_leaderboard:
        _escribir_atomico(FILE_LEADERBOARD, [])
        return "Todas las bitácoras y el ranking han sido eliminados."
    return "Todas las bitácoras eliminadas. El ranking se mantiene."


# ══════════════════════════════════════════════════════════════
#  MIGRACIONES
# ══════════════════════════════════════════════════════════════

def _migrar(data: dict, version_actual: int) -> dict:
    p = data.get("personaje", {})
    cambios = []

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
            if p.get("bg_key") in rasgo_por_bg:
                p["rasgos"].append(rasgo_por_bg[p["bg_key"]])
            cambios.append("rasgos inferidos")
        if "rasgos_en_progreso" not in p:
            p["rasgos_en_progreso"] = {}
            cambios.append("rasgos_en_progreso")

    if version_actual < 3:
        for campo, default in [("muertes_vistas", 0), ("expediciones_nocturnas", 0), ("usos_morfina", 0)]:
            if campo not in p:
                p[campo] = default
                cambios.append(campo)

    if version_actual < 4:
        if "skills_xp" not in p:
            p["skills_xp"] = {k: 0 for k in p.get("skills", {})}
            cambios.append("skills_xp")
        for campo, default in [("libros_leidos", 0), ("veces_condicion_grave", 0)]:
            if campo not in p:
                p[campo] = default
                cambios.append(campo)

    if version_actual < 5:
        # partida_id: generar uno retroactivo para saves antiguos
        if "partida_id" not in p:
            from engine.personaje import _generar_partida_id
            p["partida_id"] = _generar_partida_id(
                p.get("nombre", "survivor"), p.get("apellido", "unknown")
            )
            cambios.append("partida_id generado")

    if version_actual < 6:
        from engine.medical_system import estado_cuerpo_base
        if "cuerpo" not in p:
            p["cuerpo"] = estado_cuerpo_base()
            cambios.append("cuerpo")
        if "farmaco_carga" not in p:
            p["farmaco_carga"] = 0.0
            cambios.append("farmaco_carga")

    if version_actual < 7:
        if "historial_farmacos" not in p:
            p["historial_farmacos"] = []
            cambios.append("historial_farmacos")

    if version_actual < 8:
        if "especialidades_desbloqueadas" not in p:
            p["especialidades_desbloqueadas"] = {k: [] for k in p.get("skills", {})}
            cambios.append("especialidades_desbloqueadas")
        if "condiciones_cronicas" not in p:
            p["condiciones_cronicas"] = []
            cambios.append("condiciones_cronicas")

    if version_actual < 9:
        if "relaciones_refugio" not in p:
            from engine.relaciones import estado_relaciones_refugio_base

            p["relaciones_refugio"] = estado_relaciones_refugio_base()
            cambios.append("relaciones_refugio")

    if version_actual < 10:
        # v10: NPCs con hambre y salud; nuevos NPCs (elena, viktor) añadidos.
        from engine.relaciones import estado_relaciones_refugio_base, REFUGIO_NPCS
        base = estado_relaciones_refugio_base()
        rels = p.get("relaciones_refugio", {})
        for npc_id, npc_base in base.items():
            if npc_id not in rels:
                rels[npc_id] = dict(npc_base)
                cambios.append(f"npc_nuevo:{npc_id}")
            else:
                for campo in ("hambre", "salud"):
                    if campo not in rels[npc_id]:
                        rels[npc_id][campo] = npc_base.get(campo, 50)
        p["relaciones_refugio"] = rels

    if version_actual < 11:
        # v11: campos de autonomía NPC.
        _CAMPOS_NPC_V11 = {
            "en_expedicion": False, "dias_expedicion": 0,
            "veces_peleado": 0, "quiere_irse": False,
        }
        rels = p.get("relaciones_refugio", {})
        for npc_estado in rels.values():
            for campo, valor in _CAMPOS_NPC_V11.items():
                if campo not in npc_estado:
                    npc_estado[campo] = valor
            if "personalidad" not in npc_estado:
                npc_estado["personalidad"] = "neutral"
            if "puede_expedicion" not in npc_estado:
                npc_estado["puede_expedicion"] = False
        p["relaciones_refugio"] = rels
        cambios.append("npc_autonomia_v11")

    if version_actual < 12:
        # v12: árbol genealógico + campos familiares en NPCs.
        _CAMPOS_NPC_V12 = {
            "apellido": "", "genero": "masculino", "edad": 30, "desc": "",
            "estado_relacion": "desconocido", "es_menor": False,
            "padres": [], "hijos": [], "pareja_id": None, "embarazo_ticks": 0,
        }
        rels = p.get("relaciones_refugio", {})
        for npc_estado in rels.values():
            for campo, valor in _CAMPOS_NPC_V12.items():
                if campo not in npc_estado:
                    npc_estado[campo] = valor
        p["relaciones_refugio"] = rels
        if "familia" not in p:
            p["familia"] = {}
        cambios.append("arbol_genealogico_v12")

    if version_actual < 13:
        # v13: animales_refugio, edad_inicio, penalizaciones_envejecimiento, miedo NPC.
        if "animales_refugio" not in p:
            p["animales_refugio"] = []
        if "edad_inicio" not in p:
            p["edad_inicio"] = p.get("edad", 25)
        if "penalizaciones_envejecimiento" not in p:
            p["penalizaciones_envejecimiento"] = []
        rels = p.get("relaciones_refugio", {})
        for npc_estado in rels.values():
            if "miedo" not in npc_estado:
                npc_estado["miedo"] = 0
        p["relaciones_refugio"] = rels
        cambios.append("envejecimiento_animales_miedo_v13")

    if version_actual < 14:
        if "almacen" not in p:
            p["almacen"] = []
        cambios.append("almacen_refugio_v14")

    if version_actual < 15:
        # v14 → v15: campos de fuego y trampas
        p.setdefault("fuego_activo", False)
        p.setdefault("combustible_restante", 0)
        p.setdefault("temperatura_refugio", 18.0)
        p.setdefault("trampas_activas", [])
        cambios.append("fuego_trampas_v15")

    if version_actual < 16:
        # v15 → v16: sistema de temperatura corporal y vestimenta
        p.setdefault("temp_corporal", 36.5)
        p.setdefault("ropa_equipada", {})
        p.setdefault("humedad_ropa", 0.0)
        p.setdefault("horas_exposicion_frio", 0.0)
        cambios.append("temperatura_vestimenta_v16")

    if version_actual < 17:
        # v16 → v17: ejes emocionales (amor/respeto/resentimiento) por NPC.
        # Los valores se inicializan desde confianza/tensión existentes para
        # que los NPCs ya conocidos tengan valores coherentes con la historia.
        for npc_estado in p.get("relaciones_refugio", {}).values():
            if not isinstance(npc_estado, dict):
                continue
            confianza = int(npc_estado.get("confianza", 40))
            tension   = int(npc_estado.get("tension",   30))
            npc_estado.setdefault("amor",         min(100, int(confianza * 0.8)))
            npc_estado.setdefault("respeto",      min(100, int(confianza * 0.7)))
            npc_estado.setdefault("resentimiento", max(0, int(tension * 0.3 - confianza * 0.1)))
        cambios.append("ejes_emocionales_v17")

    if cambios:
        logger.info("Migración v%d→%d: %s", version_actual, SAVE_VERSION, ", ".join(cambios))
    data["personaje"]    = p
    data["save_version"] = SAVE_VERSION
    return data


# ══════════════════════════════════════════════════════════════
#  TABLA DE CLASIFICACIÓN
# ══════════════════════════════════════════════════════════════

def registrar_muerte(personaje, causa: str = "desconocida") -> int:
    _asegurar_directorios()
    tabla = _cargar_leaderboard()

    # Estadísticas de familia
    rels = getattr(personaje, "relaciones_refugio", {})
    familia_count = len(rels)
    animales_count = len(getattr(personaje, "animales_refugio", []))
    tuvo_pareja = any(
        v.get("tipo") == "pareja"
        for v in getattr(personaje, "familia", {}).values()
    )
    tuvo_hijos = any(
        v.get("tipo") in ("hijo", "hija")
        for v in getattr(personaje, "familia", {}).values()
    )

    # Mejor skill
    skills = getattr(personaje, "skills", {})
    mejor_skill = max(skills, key=skills.get) if skills else ""

    # Condiciones crónicas al morir
    condiciones_al_morir = [
        c.get("nombre", c.get("clave", "?"))
        for c in getattr(personaje, "condiciones_cronicas", [])
    ]

    entrada = {
        "partida_id":        personaje.partida_id,
        "nombre":            f"{personaje.nombre} {personaje.apellido}",
        "genero":            personaje.genero,
        "background":        personaje.background["nombre"],
        "dias":              personaje.dia,
        "hora":              personaje.hora,
        "expediciones":      personaje.expediciones_completadas,
        "infectados":        personaje.infectados_eliminados,
        "bandidos":          personaje.bandidos_eliminados,
        "items":             personaje.items_recolectados,
        "rasgos":            personaje.rasgos,
        "causa_muerte":      causa,
        "fecha":             datetime.now().strftime("%Y-%m-%d"),
        "puntuacion":        _calcular_puntuacion(personaje),
        # Campos de legado enriquecido
        "edad_final":        getattr(personaje, "edad", "?"),
        "familia_count":     familia_count,
        "animales_count":    animales_count,
        "tuvo_pareja":       tuvo_pareja,
        "tuvo_hijos":        tuvo_hijos,
        "mejor_skill":       mejor_skill,
        "condiciones_al_morir": condiciones_al_morir,
    }
    tabla.append(entrada)
    tabla.sort(key=lambda e: (e["dias"], e["puntuacion"]), reverse=True)
    tabla = tabla[:MAX_LEADERBOARD]
    _escribir_atomico(FILE_LEADERBOARD, tabla)
    return _posicion(entrada, tabla)


def obtener_leaderboard() -> list[dict]:
    return _cargar_leaderboard()


def eco_del_pasado() -> str:
    """
    Retorna un mensaje narrativo breve que referencia a un personaje caído previo.
    Destinado a mostrarse al iniciar una nueva partida si hay entradas en el leaderboard.
    Retorna '' si no hay entradas.
    """
    tabla = _cargar_leaderboard()
    if not tabla:
        return ""

    import random
    entrada = random.choice(tabla[:min(5, len(tabla))])
    nombre = entrada.get("nombre", "Alguien")
    dias   = entrada.get("dias", 0)
    causa  = entrada.get("causa_muerte", "causas desconocidas")
    bg     = entrada.get("background", "superviviente")

    frases = [
        f"Las paredes de este mundo recuerdan a {nombre}, {bg.lower()} que vivió {dias} días antes de caer por {causa}.",
        f"Hace tiempo, {nombre} caminó por estas ruinas. Duró {dias} días. Murió por {causa}.",
        f"En algún lugar, hay un rastro de {nombre}. {dias} días de supervivencia y luego... {causa}.",
        f"Este mundo vio a {nombre} luchar {dias} días. Al final, {causa} puso fin a su historia.",
    ]
    return random.choice(frases)


def _calcular_puntuacion(personaje) -> int:
    pts  = personaje.dia * 100
    pts += personaje.expediciones_completadas * 50
    pts += personaje.infectados_eliminados    * 10
    pts += personaje.bandidos_eliminados      * 20
    pts += personaje.items_recolectados       * 5
    pts += len(personaje.areas_visitadas)     * 30
    pts += len(personaje.rasgos)              * 25
    pts += sum(personaje.skills.values()) // 10
    return pts


def _posicion(entrada: dict, tabla: list) -> int:
    for i, e in enumerate(tabla, 1):
        if (e["nombre"] == entrada["nombre"]
                and e.get("fecha") == entrada.get("fecha")
                and e["puntuacion"] == entrada["puntuacion"]):
            return i
    return len(tabla)


# ══════════════════════════════════════════════════════════════
#  BACKUPS
# ══════════════════════════════════════════════════════════════

def _rotar_backup() -> None:
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
    for bk in sorted(DIR_BACKUPS.glob("backup_*.json"), reverse=True):
        try:
            with open(bk, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Recuperado desde %s", bk.name)
            return data
        except Exception:
            continue
    return None


# ══════════════════════════════════════════════════════════════
#  UTILIDADES
# ══════════════════════════════════════════════════════════════

def _asegurar_directorios() -> None:
    DIR_SAVES.mkdir(exist_ok=True)
    DIR_BACKUPS.mkdir(exist_ok=True)
    DIR_HISTORIAS.mkdir(exist_ok=True)


def _escribir_atomico(ruta: Path, data) -> bool:
    tmp = ruta.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(ruta)
        return True
    except Exception as e:
        logger.error("Error al guardar: %s", e)
        if tmp.exists():
            tmp.unlink()
        return False


def _cargar_leaderboard() -> list:
    if not FILE_LEADERBOARD.exists():
        return []
    try:
        with open(FILE_LEADERBOARD, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
