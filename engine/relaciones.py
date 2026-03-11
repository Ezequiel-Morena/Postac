# ============================================================
# engine/relaciones.py
# Simula el refugio de forma autónoma:
#   - NPCs con necesidades propias (hambre, salud, tensión).
#   - Expediciones autónomas de NPCs según su rol y estado.
#   - Dinámica de tensión grupal: NPCs pueden irse si las
#     condiciones empeoran lo suficiente.
#   - Integración de nuevos supervivientes al refugio.
# ============================================================

from __future__ import annotations

import copy
import random
from typing import TYPE_CHECKING

from data.items import ITEMS
from data.loot import LOOT_POOLS
from data.relaciones import EVENTOS_REFUGIO
from data.familia import ROLES_LOOT_EXPEDICION, PERSONALIDADES_EXPEDICION
from engine.constants import (
    NPC_PROB_EXPEDICION_BASE, NPC_TENSION_UMBRAL,
    NPC_EXPEDICION_PROB_RETORNO_BASE, NPC_EXPEDICION_PROB_RETORNO_POR_DIA,
    NPC_EXPEDICION_PROB_LESION, NPC_EXPEDICION_PROB_MUERTE, NPC_EXPEDICION_PROB_EXITO,
    NPC_EXPEDICION_BONUS_LEALTAD_ALTA, NPC_EXPEDICION_REDUCCION_LESION_LEALTAD,
    NPC_EXPEDICION_REDUCCION_MUERTE_LEALTAD, NPC_PROB_EMIGRACION,
    NPC_CONFIANZA_REACCION, SALUD_PCT_ACTIVA_MIEDO_NPC, NPC_PROB_REACCION_MIEDO,
    MORAL_UMBRAL_BAJA, NPC_PROB_ALERTA_MORAL, SALUD_PCT_REDUCE_MIEDO,
    MORAL_MINIMA_REDUCE_MIEDO, clamp,
)

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

# ── Constantes locales ───────────────────────────────────────────────────────

# Umbrales para que un NPC pueda salir de expedición.
_EXPEDICION_SALUD_MIN    = 60
_EXPEDICION_HAMBRE_MAX   = 68
_EXPEDICION_PROB_BASE    = NPC_PROB_EXPEDICION_BASE

# Tensión grupal: porcentaje del grupo en conflicto para activar alerta.
_TENSION_GRUPAL_UMBRAL   = NPC_TENSION_UMBRAL

# NPC quiere irse si confianza < este valor Y tensión > otro umbral.
_CONFIANZA_IRSE_MIN      = 22
_TENSION_IRSE_MIN        = 65

# Campos que todo NPC debe tener en su estado en save.
_CAMPOS_NPC_BASE: dict = {
    "confianza":      50,
    "lealtad":        50,
    "tension":        25,
    "miedo":          0,
    "hambre":         35,
    "salud":          90,
    "en_expedicion":  False,
    "dias_expedicion": 0,
    "veces_peleado":  0,
    "quiere_irse":    False,
}


# ── Inicialización ────────────────────────────────────────────────────────────

def estado_relaciones_refugio_base() -> dict[str, dict]:
    """El refugio arranca vacío. Los NPCs se incorporan durante el juego."""
    return {}


def _npc_estado_inicial(npc: dict) -> dict:
    """Normaliza un dict de NPC garantizando todos los campos necesarios."""
    from data.familia import ROLES_EXPEDICION
    return {
        "nombre":           npc.get("nombre", "Desconocido"),
        "apellido":         npc.get("apellido", ""),
        "genero":           npc.get("genero", "masculino"),
        "edad":             int(npc.get("edad", 30)),
        "rol":              npc.get("rol", "superviviente"),
        "personalidad":     npc.get("personalidad", "neutral"),
        "puede_expedicion": bool(npc.get("puede_expedicion", False)),
        "desc":             npc.get("desc", ""),
        "confianza":        int(npc.get("confianza", 40)),
        "lealtad":          int(npc.get("lealtad",   40)),
        "tension":          int(npc.get("tension",   30)),
        "miedo":            int(npc.get("miedo",      0)),
        "hambre":           int(npc.get("hambre",    50)),
        "salud":            int(npc.get("salud",     80)),
        "en_expedicion":    bool(npc.get("en_expedicion", False)),
        "dias_expedicion":  max(0, int(npc.get("dias_expedicion", 0))),
        "veces_peleado":    max(0, int(npc.get("veces_peleado", 0))),
        "quiere_irse":      bool(npc.get("quiere_irse", False)),
        "estado_relacion":  npc.get("estado_relacion", "desconocido"),
        "es_menor":         bool(npc.get("es_menor", False)),
        "padres":           list(npc.get("padres", [])),
        "hijos":            list(npc.get("hijos", [])),
        "pareja_id":        npc.get("pareja_id"),
        "embarazo_ticks":   int(npc.get("embarazo_ticks", 0)),
    }


def normalizar_relaciones_guardadas(relaciones: dict | None) -> dict[str, dict]:
    """
    Normaliza relaciones cargadas desde save: garantiza que cada NPC
    tenga todos los campos requeridos. NO añade NPCs nuevos.
    """
    if not isinstance(relaciones, dict):
        return {}
    normalizado = {}
    for npc_id, data in relaciones.items():
        if not isinstance(data, dict):
            continue
        normalizado[npc_id] = _npc_estado_inicial(data)
    return normalizado


# ── Tick principal ────────────────────────────────────────────────────────────

def tick_refugio(personaje: "Sobreviviente", horas: float, contexto: str = "") -> list[str]:
    """
    Simula todo lo que ocurre en el refugio mientras el personaje está fuera
    o descansa. Autónomo: el jugador no interviene en ninguna decisión aquí.
    """
    from engine.familia import tick_familia

    if horas <= 0:
        return []

    if not hasattr(personaje, "relaciones_refugio"):
        personaje.relaciones_refugio = {}

    # Garantizar campos nuevos en NPCs existentes (compatibilidad con saves viejos)
    _CAMPOS_NUEVOS = {
        "apellido": "", "genero": "masculino", "edad": 30, "desc": "",
        "estado_relacion": "desconocido", "es_menor": False,
        "padres": [], "hijos": [], "pareja_id": None, "embarazo_ticks": 0,
    }
    for estado in personaje.relaciones_refugio.values():
        for campo, default in {**_CAMPOS_NPC_BASE, **_CAMPOS_NUEVOS}.items():
            if campo not in estado:
                estado[campo] = default

    seed = f"{personaje.partida_id}:{personaje.dia}:{personaje.hora}:{contexto}"
    rng = random.Random(seed)
    mensajes: list[str] = []

    npcs_presentes = [
        npc_id for npc_id, est in personaje.relaciones_refugio.items()
        if not est.get("en_expedicion", False)
    ]
    npcs_en_exped = [
        npc_id for npc_id, est in personaje.relaciones_refugio.items()
        if est.get("en_expedicion", False)
    ]

    # ── 1. Resolver retorno de NPCs en expedición ─────────────────────────────
    for npc_id in npcs_en_exped:
        msgs = _resolver_retorno_npc(personaje, npc_id, horas, rng)
        mensajes.extend(msgs)

    # ── 2. Tick de necesidades autónomas de NPCs presentes ────────────────────
    for npc_id in npcs_presentes:
        estado = personaje.relaciones_refugio[npc_id]
        _tick_necesidades_npc(estado, horas, rng, personaje)

    # ── 3. Decidir nuevas expediciones de NPCs ────────────────────────────────
    for npc_id in npcs_presentes:
        estado = personaje.relaciones_refugio[npc_id]
        if _npc_puede_salir(estado, personaje):
            prob = _EXPEDICION_PROB_BASE
            if estado.get("rol") in ("exploradora", "explorador", "exsoldado", "cazador", "soldado", "guardia", "cartógrafo"):
                prob += 0.10
            if estado.get("tension", 0) > 50 and estado.get("personalidad") in ("valiente", "hosco"):
                prob += 0.10
            if rng.random() < prob:
                msgs = _lanzar_expedicion_npc(personaje, npc_id, estado, rng)
                mensajes.extend(msgs)
                npcs_presentes = [n for n in npcs_presentes if n != npc_id]

    # ── 4. Eventos sociales de NPCs presentes ────────────────────────────────
    bloques = max(1, int(round(horas / 3)))
    if npcs_presentes:
        for _ in range(bloques):
            npc_id = rng.choice(npcs_presentes)
            estado = personaje.relaciones_refugio[npc_id]
            evento = _elegir_evento(estado, personaje, rng)
            _aplicar_efectos(personaje, estado, evento)
            mensajes.append(
                f"[Refugio] {estado['nombre']} ({estado['rol']}) {evento['nombre']}."
            )
            item_ref = evento.get("item_ref")
            if isinstance(item_ref, str) and item_ref in ITEMS:
                item = copy.deepcopy(ITEMS[item_ref])
                if personaje.añadir_item(item):
                    mensajes[-1] += f" Recurso obtenido: {item.get('nombre', item_ref)}."

    # ── 5. Tensión grupal y partidas ─────────────────────────────────────────
    mensajes.extend(_evaluar_tension_grupal(personaje, rng))

    # ── 6. Sistema familiar (relaciones, hijos, parejas NPC-NPC) ─────────────
    mensajes.extend(tick_familia(personaje, horas, rng))

    # ── 7. Tick de animales domésticos ───────────────────────────────────────
    from engine.animales import tick_animales
    mensajes.extend(tick_animales(personaje, horas, rng))

    # ── 8. Reacciones emocionales ─────────────────────────────────────────────
    mensajes.extend(evaluar_reacciones_emocionales(personaje, rng))

    # ── 9. Alertas de estado crítico ─────────────────────────────────────────
    mensajes.extend(_generar_alertas(personaje))

    return mensajes


# ── Expediciones de NPCs ──────────────────────────────────────────────────────

# Bonus por rol para elegir zona de expedición NPC.
_ROL_ZONA_BONUS: dict[str, dict[str, float]] = {
    "soldado":     {"comisaria": 2.0, "laboratorio": 1.5, "fabrica": 1.3},
    "exsoldado":   {"comisaria": 2.0, "laboratorio": 1.5, "estadio": 1.2},
    "cazador":     {"reserva_forestal": 2.5, "puerto_seco": 1.5, "gasolinera": 1.2},
    "exploradora": {"biblioteca": 1.8, "hospital": 1.5, "casa_abandonada": 1.3},
    "guardia":     {"comisaria": 1.8, "fabrica": 1.5, "gasolinera": 1.2},
    "medico":      {"hospital": 2.5, "farmacia": 2.0, "laboratorio": 1.5},
    "mecanico":    {"fabrica": 2.0, "gasolinera": 1.8, "puerto_seco": 1.3},
    "cocinero":    {"supermercado": 2.0, "reserva_forestal": 1.5, "casa_abandonada": 1.2},
    "granjero":    {"reserva_forestal": 2.5, "supermercado": 1.5, "casa_abandonada": 1.2},
}

def _elegir_zona_npc(estado: dict, rng: random.Random) -> str:
    """Elige una zona para la expedición del NPC según su rol y salud."""
    from data.areas import AREAS
    rol     = estado.get("rol", "")
    bonuses = _ROL_ZONA_BONUS.get(rol, {})
    salud   = int(estado.get("salud", 80))
    pesos   = []
    area_keys = list(AREAS.keys())
    for key in area_keys:
        area = AREAS[key]
        peso = 1.0
        # Evitar zonas peligrosas si el NPC está herido.
        peligro = area.get("peligro", 3)
        if salud < 50 and peligro > 3:
            peso *= 0.3
        peso *= bonuses.get(key, 1.0)
        pesos.append(max(0.01, peso))
    total = sum(pesos)
    r     = rng.random() * total
    acum  = 0.0
    for key, peso in zip(area_keys, pesos):
        acum += peso
        if r <= acum:
            return AREAS[key].get("nombre", key)
    return AREAS[area_keys[-1]].get("nombre", area_keys[-1])


def _npc_puede_salir(estado: dict, personaje: "Sobreviviente") -> bool:
    """Determina si un NPC está en condiciones de salir a expedición."""
    if not estado.get("puede_expedicion", False):
        return False
    if estado.get("en_expedicion", False):
        return False
    if estado.get("quiere_irse", False):
        return False
    if int(estado.get("salud", 0)) < _EXPEDICION_SALUD_MIN:
        return False
    if int(estado.get("hambre", 0)) > _EXPEDICION_HAMBRE_MAX:
        return False
    return True


def _lanzar_expedicion_npc(
    personaje: "Sobreviviente",
    npc_id: str,
    estado: dict,
    rng: random.Random,
) -> list[str]:
    """Marca al NPC como en expedición, elige zona según rol, y lo retira del refugio."""
    estado["en_expedicion"]   = True
    estado["dias_expedicion"] = 0
    zona_elegida = _elegir_zona_npc(estado, rng)
    estado["zona_actual"] = zona_elegida
    nombre = estado.get("nombre", npc_id)
    rol    = estado.get("rol", "")
    return [f"[Refugio] {nombre} ({rol}) salió hacia {zona_elegida}."]


def _resolver_retorno_npc(
    personaje: "Sobreviviente",
    npc_id: str,
    horas: float,
    rng: random.Random,
) -> list[str]:
    """Resuelve el regreso de un NPC que estaba en expedición."""
    estado  = personaje.relaciones_refugio[npc_id]
    nombre  = estado.get("nombre", npc_id)
    rol     = estado.get("rol", "")
    msgs: list[str] = []

    dias = int(estado.get("dias_expedicion", 0)) + max(1, int(horas // 6))
    estado["dias_expedicion"] = dias

    # Probabilidad de retorno sube con los días: 50% día 1, 80% día 2, 100% día 3+.
    prob_retorno = min(1.0, NPC_EXPEDICION_PROB_RETORNO_BASE + (dias - 1) * NPC_EXPEDICION_PROB_RETORNO_POR_DIA)
    if rng.random() > prob_retorno:
        return []  # Aún no vuelve.

    # ── Retornó: calcular resultado ──────────────────────────────────────────
    estado["en_expedicion"]   = False
    estado["dias_expedicion"] = 0

    prob_lesion  = NPC_EXPEDICION_PROB_LESION
    prob_muerte  = NPC_EXPEDICION_PROB_MUERTE
    prob_exito   = NPC_EXPEDICION_PROB_EXITO

    # Los roles combativos y de exploración tienen mejores probabilidades.
    if rol in ("exsoldado", "soldado", "cazador"):
        prob_lesion -= NPC_EXPEDICION_REDUCCION_LESION_LEALTAD
        prob_muerte -= NPC_EXPEDICION_REDUCCION_MUERTE_LEALTAD
    elif rol in ("exploradora", "guardia"):
        prob_exito  += NPC_EXPEDICION_BONUS_LEALTAD_ALTA

    # Tirada de resultado.
    tirada = rng.random()

    if tirada < prob_muerte:
        # NPC no regresó con vida.
        del personaje.relaciones_refugio[npc_id]
        personaje.moral = max(0, personaje.moral - 15)
        msgs.append(
            f"[Refugio] ✝ {nombre} ({rol}) no ha regresado. "
            "Quizás fue presa de algo en las ruinas. El grupo llora su ausencia."
        )
        return msgs

    if tirada < prob_muerte + prob_lesion:
        # Volvió herido.
        daño = rng.randint(20, 40)
        estado["salud"] = clamp(int(estado.get("salud", 90)) - daño)
        personaje.moral = max(0, personaje.moral - 5)
        msgs.append(
            f"[Refugio] {nombre} ({rol}) regresó malherido/a "
            f"(-{daño} salud). Necesita descanso."
        )
    else:
        zona_str = estado.get("zona_actual", "")
        zona_info = f" desde {zona_str}" if zona_str else ""
        msgs.append(
            f"[Refugio] {nombre} ({rol}) regresó{zona_info}."
        )

    # Loot traído si la expedición fue exitosa — va al almacén compartido.
    if rng.random() < prob_exito:
        loot_pool_key = _rol_a_loot_pool(rol, rng)
        pool = LOOT_POOLS.get(loot_pool_key, [])
        item_key = rng.choice([k for k in pool if k is not None] or [None])
        if item_key and item_key in ITEMS:
            item = copy.deepcopy(ITEMS[item_key])
            from engine.almacen import agregar_item as _almacen_add
            _almacen_add(personaje.almacen, item)
            msgs[-1] += f" Trajo al almacén: {item.get('nombre', item_key)}."
            estado["confianza"] = clamp(int(estado.get("confianza", 50)) + 4)
            estado["lealtad"]   = clamp(int(estado.get("lealtad",   50)) + 3)
            personaje.moral     = min(100, personaje.moral + 3)

    # Gasta hambre en la expedición.
    estado["hambre"] = clamp(int(estado.get("hambre", 35)) + rng.randint(10, 25))

    return msgs


def _rol_a_loot_pool(rol: str, rng: random.Random) -> str:
    pools = ROLES_LOOT_EXPEDICION.get(rol, ["comida_escasa", "herramientas"])
    return rng.choice(pools)


# ── Nuevos supervivientes ─────────────────────────────────────────────────────

def generar_superviviente_aleatorio(seed: str, personaje: "Sobreviviente") -> dict | None:
    """
    Genera un NPC proceduralmente para un encuentro de expedición.
    Delega a engine.familia para garantizar coherencia.
    """
    from engine.familia import generar_npc_para_encuentro
    return generar_npc_para_encuentro(seed, personaje)


def integrar_nuevo_miembro(personaje: "Sobreviviente", perfil: dict) -> str:
    """
    Añade un superviviente (generado proceduralmente) al refugio.
    Delega a engine.familia que gestiona IDs y penalizaciones de llegada.
    """
    from engine.familia import integrar_npc_en_refugio
    if not hasattr(personaje, "relaciones_refugio"):
        personaje.relaciones_refugio = {}
    return integrar_npc_en_refugio(personaje, perfil)


# ── Tensión grupal y partidas ─────────────────────────────────────────────────

def _evaluar_tension_grupal(personaje: "Sobreviviente", rng: random.Random) -> list[str]:
    """
    Evalúa si la situación grupal está deteriorada y si algún NPC quiere irse.
    Los NPCs con quiere_irse=True pueden abandonar el refugio en este tick.
    """
    msgs: list[str] = []
    relaciones = personaje.relaciones_refugio
    npcs = list(relaciones.keys())
    if not npcs:
        return msgs

    # Tensión grupal: fracción de NPCs con tensión >= 60.
    n_en_tension = sum(1 for npc_id in npcs if int(relaciones[npc_id].get("tension", 0)) >= 60)
    fraccion_tension = n_en_tension / len(npcs)

    if fraccion_tension >= _TENSION_GRUPAL_UMBRAL:
        personaje.moral = max(0, personaje.moral - 3)
        msgs.append(
            f"[Refugio] ⚠ La tensión afecta a más de la mitad del grupo. "
            "El ambiente es irrespirable."
        )

    a_irse: list[str] = []
    for npc_id in npcs:
        estado = relaciones[npc_id]
        confianza = int(estado.get("confianza", 50))
        tension   = int(estado.get("tension",   25))
        nombre    = estado.get("nombre", npc_id)
        rol       = estado.get("rol", "")

        # Activar bandera "quiere_irse" si condiciones lo justifican.
        queria_irse = bool(estado.get("quiere_irse", False))
        quiere_irse_ahora = (
            confianza < _CONFIANZA_IRSE_MIN
            and tension > _TENSION_IRSE_MIN
        ) or (
            int(estado.get("veces_peleado", 0)) >= 3
            and confianza < 35
        )

        if quiere_irse_ahora and not queria_irse:
            estado["quiere_irse"] = True
            msgs.append(
                f"[Refugio] ⚠ {nombre} ({rol}) está pensando en abandonar el grupo. "
                "La situación entre ellos y el resto se ha vuelto insostenible."
            )
        elif queria_irse and quiere_irse_ahora:
            # Ya quería irse y las condiciones siguen sin mejorar → se va.
            if rng.random() < NPC_PROB_EMIGRACION:
                a_irse.append(npc_id)
        elif queria_irse and not quiere_irse_ahora:
            # Las condiciones mejoraron: ya no quiere irse.
            estado["quiere_irse"] = False
            msgs.append(
                f"[Refugio] {nombre} parece haber reconsiderado. "
                "Por ahora, se queda."
            )

    for npc_id in a_irse:
        estado = relaciones[npc_id]
        nombre = estado.get("nombre", npc_id)
        rol    = estado.get("rol", "")
        del relaciones[npc_id]
        personaje.moral = max(0, personaje.moral - 10)
        msgs.append(
            f"[Refugio] {nombre} ({rol}) ha abandonado el grupo. "
            "Empacó en silencio y se fue al amanecer."
        )

    return msgs


# ── Eventos sociales ──────────────────────────────────────────────────────────

def _elegir_evento(estado: dict, personaje: "Sobreviviente", rng: random.Random) -> dict:
    tension      = int(estado.get("tension",      25))
    confianza    = int(estado.get("confianza",     50))
    hambre       = int(estado.get("hambre",        35))
    salud        = int(estado.get("salud",         90))
    personalidad = str(estado.get("personalidad",  ""))

    bolsa: list[tuple[dict, int]] = []
    for evento in EVENTOS_REFUGIO:
        peso   = int(evento.get("peso", 1))
        ev_id  = evento.get("id", "")

        if ev_id == "disputa_interna" and tension > 40:
            peso += 8
        if ev_id == "conflicto_violento":
            if tension < int(evento.get("requiere_tension_min", 999)):
                peso = 0
            else:
                peso += 12
        if ev_id == "apoyo_emocional" and confianza > 60:
            peso += 6
        if ev_id == "busqueda_exitosa" and confianza > 50:
            peso += 4
        if ev_id == "enfermedad_leve" and (hambre > 65 or salud < 60):
            peso += 6
        if ev_id == "hallazgo_valioso":
            reqs = evento.get("requiere_personalidad", [])
            if reqs and personalidad not in reqs:
                peso = max(1, peso - 4)
        if ev_id == "traicion_pequena":
            reqs = evento.get("requiere_personalidad", [])
            if reqs and personalidad not in reqs:
                peso = 1
            elif tension < int(evento.get("requiere_tension_min", 999)):
                peso = 0
        if ev_id in ("confesion_miedo", "relato_pasado", "recuerdo_compartido"):
            if confianza < int(evento.get("requiere_confianza_min", 0)):
                peso = 1
        if ev_id == "mediacion_conflicto":
            reqs = evento.get("requiere_personalidad", [])
            if reqs and personalidad not in reqs:
                peso = 1
        if ev_id == "baja_moral_colectiva" and tension < 40:
            peso = 1
        if ev_id == "amago_de_irse" and tension < int(evento.get("requiere_tension_min", 999)):
            peso = 0
        if ev_id == "cuidado_a_enfermo":
            reqs = evento.get("requiere_personalidad", [])
            if reqs and personalidad not in reqs:
                peso = 1

        bolsa.append((evento, max(0, peso)))

    bolsa = [(e, p) for e, p in bolsa if p > 0]
    if not bolsa:
        return EVENTOS_REFUGIO[-1]

    total = sum(p for _, p in bolsa)
    pick  = rng.randint(1, max(1, total))
    acumulado = 0
    for evento, peso in bolsa:
        acumulado += peso
        if pick <= acumulado:
            return evento
    return bolsa[-1][0]


def _aplicar_efectos(personaje: "Sobreviviente", estado: dict, evento: dict) -> None:
    efectos = evento.get("efectos", {}) if isinstance(evento, dict) else {}

    personaje.moral = clamp(personaje.moral + int(efectos.get("moral", 0)))
    estado["confianza"] = clamp(int(estado.get("confianza", 50)) + int(efectos.get("confianza", 0)))
    estado["lealtad"]   = clamp(int(estado.get("lealtad",   50)) + int(efectos.get("lealtad",   0)))
    estado["tension"]   = clamp(int(estado.get("tension",   25)) + int(efectos.get("tension",   0)))

    if "salud_npc" in efectos:
        estado["salud"]  = clamp(int(estado.get("salud",  90)) + int(efectos["salud_npc"]))
    if "hambre_npc" in efectos:
        estado["hambre"] = clamp(int(estado.get("hambre", 35)) + int(efectos["hambre_npc"]))

    # Registro de conflictos violentos.
    if evento.get("id") == "conflicto_violento":
        estado["veces_peleado"] = int(estado.get("veces_peleado", 0)) + 1


# ── Necesidades autónomas ─────────────────────────────────────────────────────

def _tick_necesidades_npc(estado: dict, horas: float, rng: random.Random, personaje: "Sobreviviente | None" = None) -> None:
    """Avanza hambre y salud del NPC de forma autónoma. Consume del almacén si está disponible."""
    subida_hambre = int(round(rng.uniform(3, 8) * (horas / 6.0)))
    estado["hambre"] = clamp(int(estado.get("hambre", 35)) + subida_hambre)

    # Si hay almacén disponible, el NPC intenta comer y curarse.
    if personaje is not None and not estado.get("en_expedicion"):
        almacen = getattr(personaje, "almacen", [])
        if int(estado.get("hambre", 0)) > 65:
            from engine.almacen import consumir_tipo
            comida = consumir_tipo(almacen, "comida", 1)
            if comida:
                estado["hambre"] = max(0, int(estado.get("hambre", 100)) - 30)
        if int(estado.get("salud", 100)) < 50:
            from engine.almacen import consumir_tipo
            medicina = consumir_tipo(almacen, "medicina", 1)
            if medicina:
                estado["salud"] = clamp(int(estado.get("salud", 50)) + 25)

    if int(estado.get("hambre", 0)) >= 85:
        estado["salud"] = clamp(int(estado.get("salud", 90)) - max(1, int(horas)))
    elif int(estado.get("tension", 0)) >= 70:
        if rng.random() < 0.20:
            estado["salud"] = clamp(int(estado.get("salud", 90)) - 1)

    if int(estado.get("hambre", 0)) < 50 and int(estado.get("tension", 0)) < 35:
        recuperacion = max(1, int(horas * 0.5))
        estado["salud"] = clamp(int(estado.get("salud", 90)) + recuperacion)


# ── Alertas ───────────────────────────────────────────────────────────────────

def _generar_alertas(personaje: "Sobreviviente") -> list[str]:
    msgs: list[str] = []
    for npc_id, estado in personaje.relaciones_refugio.items():
        if bool(estado.get("en_expedicion", False)):
            continue
        salud  = int(estado.get("salud",  100))
        hambre = int(estado.get("hambre",   0))
        nombre = estado.get("nombre", npc_id)
        if salud <= 30:
            msgs.append(
                f"[Refugio] ⚠ {nombre} está gravemente herido/enfermo. "
                "Necesita atención médica urgente."
            )
        if hambre >= 80:
            msgs.append(
                f"[Refugio] {nombre} lleva tiempo sin comer. "
                "La moral del grupo sufre."
            )
            personaje.moral = max(0, personaje.moral - 2)
    return msgs


def evaluar_reacciones_emocionales(personaje: "Sobreviviente", rng: random.Random) -> list[str]:
    """
    Evalúa si los NPCs reaccionan emocionalmente al estado del personaje.
    Los NPCs con alta confianza/pareja se preocupan cuando el personaje está mal.
    El miedo aumenta ante situaciones críticas del grupo.
    """
    msgs: list[str] = []
    salud_pct = personaje.salud / max(1, personaje.salud_max)

    for npc_id, estado in personaje.relaciones_refugio.items():
        if estado.get("en_expedicion"):
            continue
        confianza = int(estado.get("confianza", 0))
        nombre = estado.get("nombre", npc_id)
        er = estado.get("estado_relacion", "desconocido")

        # Reacción ante salud crítica del personaje
        if salud_pct < SALUD_PCT_ACTIVA_MIEDO_NPC and confianza > NPC_CONFIANZA_REACCION and rng.random() < NPC_PROB_REACCION_MIEDO:
            estado["miedo"] = min(100, estado.get("miedo", 0) + 10)
            estado["tension"] = min(100, estado.get("tension", 0) + 5)
            if er == "pareja":
                msgs.append(
                    f"[Refugio] {nombre} está destrozado/a viendo tu estado. "
                    "El miedo a perderte es palpable."
                )
            elif confianza > 70:
                msgs.append(
                    f"[Refugio] {nombre} te observa con preocupación. "
                    "Tu estado los afecta a todos."
                )

        # Miedo ante moral colectiva muy baja
        if personaje.moral < MORAL_UMBRAL_BAJA and rng.random() < NPC_PROB_ALERTA_MORAL:
            estado["miedo"] = min(100, estado.get("miedo", 0) + 8)

        # El miedo se reduce si el personaje está bien y hay confianza
        if salud_pct > SALUD_PCT_REDUCE_MIEDO and personaje.moral > MORAL_MINIMA_REDUCE_MIEDO and estado.get("miedo", 0) > 0:
            estado["miedo"] = max(0, estado["miedo"] - 5)

    return msgs

