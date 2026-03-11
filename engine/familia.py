from __future__ import annotations
# ============================================================
# engine/familia.py
# Gestión del árbol genealógico, generación procedural de NPCs
# y lógica de relaciones románticas / familiares.
# ============================================================
import random
from typing import TYPE_CHECKING

from data.familia import (
    BACKSTORIES_POR_ROL, BACKSTORY_GENERICO, CONFIANZA_PARA_ESTADO,
    EDAD_ADULTO, EDAD_JOVEN, ESTADOS_RELACION, EVENTOS_FAMILIA,
    HITOS_CRECIMIENTO, NOMBRES_BEBES, PERSONALIDADES_EXPEDICION,
    PERSONALIDADES_NPC, RELACION_TIPOS, ROLES_EXPEDICION, ROLES_LOOT_EXPEDICION,
    ROLES_NPC,
)
from data.personajes import NOMBRES

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

# ── Campos base para cualquier NPC generado ───────────────────────────────────
_CAMPOS_NPC_BASE: dict = {
    "confianza":        40,
    "lealtad":          40,
    "tension":          30,
    "hambre":           50,
    "salud":            80,
    "en_expedicion":    False,
    "dias_expedicion":  0,
    "veces_peleado":    0,
    "quiere_irse":      False,
    "estado_relacion":  "desconocido",
    "es_menor":         False,
    "padres":           [],
    "hijos":            [],
    "pareja_id":        None,
    "embarazo_ticks":   0,   # 0 = no embarazada; >0 = ticks restantes hasta nacer
}

_TICKS_EMBARAZO     = 9     # Ticks de juego que dura un embarazo
_MIN_EDAD_HIJOS     = 18    # Edad mínima del personaje para tener hijos
_MAX_EDAD_HIJOS     = 45
_MIN_EDAD_ADULTO_NPC = 16   # Edad mínima de NPCs generados aleatoriamente
_MAX_EDAD_ADULTO_NPC = 55


# ══════════════════════════════════════════════════════════════
#  GENERACIÓN PROCEDURAL DE NPCs
# ══════════════════════════════════════════════════════════════

def generar_npc(
    seed: str,
    personaje: "Sobreviviente",
    rol: str | None = None,
    edad_min: int = _MIN_EDAD_ADULTO_NPC,
    edad_max: int = _MAX_EDAD_ADULTO_NPC,
    es_hijo: bool = False,
) -> dict:
    """
    Genera un NPC completamente aleatorio. No usa ningún pool fijo de NPCs:
    cada llamada con una semilla diferente produce un personaje único.

    Returns un dict con todos los campos necesarios para añadirlo a
    relaciones_refugio, incluyendo los campos familiares.
    """
    rng = random.Random(seed)

    genero    = rng.choice(("masculino", "femenino"))
    nombre    = rng.choice(NOMBRES[genero])
    apellido  = rng.choice(NOMBRES["apellidos"])
    edad      = rng.randint(edad_min, edad_max)
    rol_final = rol or rng.choice(ROLES_NPC)
    personalidad = rng.choice(PERSONALIDADES_NPC)

    pool_bs = BACKSTORIES_POR_ROL.get(rol_final, BACKSTORY_GENERICO)
    desc     = rng.choice(pool_bs)

    puede_expedicion = (
        rol_final in ROLES_EXPEDICION
        or personalidad in PERSONALIDADES_EXPEDICION
    ) and not es_hijo

    npc: dict = {
        "nombre":           nombre,
        "apellido":         apellido,
        "genero":           genero,
        "edad":             edad,
        "rol":              rol_final,
        "personalidad":     personalidad,
        "puede_expedicion": puede_expedicion,
        "desc":             desc,
        # Stats iniciales con ligera variación por personalidad
        "confianza":        max(15, min(55, 35 + rng.randint(-10, 10))),
        "lealtad":          max(20, min(55, 38 + rng.randint(-8, 12))),
        "tension":          max(10, min(55, 30 + rng.randint(-10, 15))),
        "hambre":           max(40, min(75, 55 + rng.randint(-10, 15))),
        "salud":            max(50, min(90, 75 + rng.randint(-15, 15))),
        "en_expedicion":    False,
        "dias_expedicion":  0,
        "veces_peleado":    0,
        "quiere_irse":      False,
        "estado_relacion":  "desconocido",
        "es_menor":         edad < EDAD_ADULTO,
        "padres":           [],
        "hijos":            [],
        "pareja_id":        None,
        "embarazo_ticks":   0,
    }
    return npc


def generar_id_npc(nombre: str, apellido: str, existentes: set[str]) -> str:
    """Genera un ID único para un NPC a partir de su nombre y apellido."""
    base = f"{nombre.lower()}_{apellido.lower()}"
    base = base.replace(" ", "_").replace(".", "").replace("'", "")
    npc_id = base
    i = 2
    while npc_id in existentes:
        npc_id = f"{base}_{i}"
        i += 1
    return npc_id


def generar_npc_para_encuentro(seed: str, personaje: "Sobreviviente") -> dict | None:
    """
    Genera un NPC que no esté ya en el refugio (por nombre+apellido).
    Devuelve None si no hay semilla válida disponible (no debería ocurrir).
    """
    nombres_presentes = {
        f"{e.get('nombre','')}_{e.get('apellido','')}".lower()
        for e in personaje.relaciones_refugio.values()
    }
    # Intentar hasta 20 semillas diferentes para evitar colisiones.
    for i in range(20):
        npc = generar_npc(f"{seed}:{i}", personaje)
        clave = f"{npc['nombre']}_{npc['apellido']}".lower()
        if clave not in nombres_presentes:
            return npc
    return None


def integrar_npc_en_refugio(personaje: "Sobreviviente", npc: dict) -> str:
    """
    Añade un NPC generado al refugio del personaje. Asigna ID único.
    El NPC llega con penalizadores: más hambre, menos confianza, más tensión.
    Devuelve mensaje narrativo.
    """
    if not hasattr(personaje, "relaciones_refugio"):
        personaje.relaciones_refugio = {}

    npc_id = generar_id_npc(
        npc["nombre"], npc["apellido"],
        set(personaje.relaciones_refugio.keys()),
    )

    # Penalizaciones de llegada: llegó de afuera, no confía todavía
    estado = dict(npc)
    estado["confianza"] = max(10, npc.get("confianza", 35) - 15)
    estado["hambre"]    = min(80, npc.get("hambre", 50) + 20)
    estado["salud"]     = max(20, npc.get("salud", 75) - 10)
    estado["tension"]   = min(75, npc.get("tension", 30) + 15)

    personaje.relaciones_refugio[npc_id] = estado
    nombre_completo = f"{npc['nombre']} {npc['apellido']}"
    return (
        f"[Refugio] {nombre_completo} ({npc['rol']}, {npc['edad']}a) "
        f"se une al refugio. {npc.get('desc', '')}"
    )


# ══════════════════════════════════════════════════════════════
#  RELACIONES ROMÁNTICAS
# ══════════════════════════════════════════════════════════════

def estado_relacion_actual(npc_estado: dict) -> str:
    return npc_estado.get("estado_relacion", "desconocido")


def avanzar_estado_relacion(npc_id: str, personaje: "Sobreviviente") -> str | None:
    """
    Sube el estado_relacion del NPC un paso si la confianza lo permite.
    Devuelve el nuevo estado o None si no cambia.
    """
    estado = personaje.relaciones_refugio.get(npc_id)
    if not estado:
        return None

    actual   = estado_relacion_actual(estado)
    confianza = int(estado.get("confianza", 0))

    idx = ESTADOS_RELACION.index(actual) if actual in ESTADOS_RELACION else 0
    if idx >= len(ESTADOS_RELACION) - 1:
        return None

    siguiente = ESTADOS_RELACION[idx + 1]
    umbral = CONFIANZA_PARA_ESTADO.get(siguiente, 999)

    if confianza >= umbral and siguiente != "interes":
        estado["estado_relacion"] = siguiente
        return siguiente
    return None


def proponer_relacion(personaje: "Sobreviviente", npc_id: str) -> str:
    """
    El jugador inicia una relación romántica con un NPC.
    Devuelve mensaje con el resultado.
    """
    estado = personaje.relaciones_refugio.get(npc_id)
    if not estado:
        return "Esa persona ya no está en el refugio."

    nombre = estado.get("nombre", "Alguien")
    confianza = int(estado.get("confianza", 0))
    actual = estado_relacion_actual(estado)

    if actual == "pareja":
        return f"Ya estáis juntos, {nombre} y tú."

    if actual in ("ex_pareja",):
        return f"{nombre} no quiere volver a eso. La herida aún está abierta."

    if confianza < CONFIANZA_PARA_ESTADO["cercano"]:
        return (
            f"{nombre} aprecia la honestidad, pero no te conoce suficiente. "
            f"Necesitas más tiempo juntos. (Confianza: {confianza}/65)"
        )

    if confianza >= CONFIANZA_PARA_ESTADO["pareja"]:
        # Aceptación directa con alta confianza
        _establecer_pareja(personaje, npc_id)
        personaje.moral = min(100, personaje.moral + 15)
        return (
            f"{nombre} te mira un momento en silencio. Luego asiente. "
            f"No necesita más palabras."
        )
    else:
        # Aceptación tentativa
        estado["estado_relacion"] = "interes"
        estado["confianza"] = min(100, confianza + 5)
        personaje.moral = min(100, personaje.moral + 8)
        return (
            f"{nombre} no dice que no. Dice que necesita tiempo. "
            f"Algo ha cambiado entre vosotros."
        )


def _establecer_pareja(personaje: "Sobreviviente", npc_id: str) -> None:
    """Formaliza la relación de pareja entre el jugador y el NPC."""
    estado = personaje.relaciones_refugio[npc_id]
    estado["estado_relacion"] = "pareja"
    estado["confianza"] = min(100, int(estado.get("confianza", 50)) + 10)

    # Registrar en el árbol familiar del personaje
    if not hasattr(personaje, "familia"):
        personaje.familia = {}
    personaje.familia[npc_id] = {
        "tipo":    "pareja",
        "nombre":  estado.get("nombre", ""),
        "apellido": estado.get("apellido", ""),
    }


def terminar_relacion(personaje: "Sobreviviente", npc_id: str) -> str:
    """Termina la relación romántica con un NPC."""
    estado = personaje.relaciones_refugio.get(npc_id)
    if not estado:
        return "Esa persona ya no está en el refugio."

    nombre = estado.get("nombre", "Alguien")
    estado["estado_relacion"] = "ex_pareja"
    estado["tension"] = min(100, int(estado.get("tension", 30)) + 20)
    estado["confianza"] = max(0, int(estado.get("confianza", 50)) - 20)
    personaje.moral = max(0, personaje.moral - 10)

    if hasattr(personaje, "familia") and npc_id in personaje.familia:
        personaje.familia[npc_id]["tipo"] = "ex_pareja"

    return f"La ruptura con {nombre} deja un hueco que el refugio no puede llenar."


# ══════════════════════════════════════════════════════════════
#  SISTEMA DE HIJOS
# ══════════════════════════════════════════════════════════════

def puede_tener_hijo(personaje: "Sobreviviente", npc_id: str) -> bool:
    """Comprueba si el jugador y el NPC pueden concebir un hijo ahora."""
    estado = personaje.relaciones_refugio.get(npc_id)
    if not estado:
        return False
    if estado.get("estado_relacion") != "pareja":
        return False
    if estado.get("embarazo_ticks", 0) > 0:
        return False  # Ya hay embarazo en curso
    edad_jugador = getattr(personaje, "edad", 0)
    if not (_MIN_EDAD_HIJOS <= edad_jugador <= _MAX_EDAD_HIJOS):
        return False
    edad_pareja = int(estado.get("edad", 0))
    if not (_MIN_EDAD_HIJOS <= edad_pareja <= _MAX_EDAD_HIJOS):
        return False
    if int(personaje.vitals.get("salud", 100)) < 30:
        return False
    return True


def iniciar_embarazo(personaje: "Sobreviviente", npc_id: str) -> str:
    """Inicia un embarazo entre el jugador y el NPC."""
    estado = personaje.relaciones_refugio[npc_id]
    estado["embarazo_ticks"] = _TICKS_EMBARAZO
    nombre = estado.get("nombre", "tu pareja")
    return f"[Familia] {nombre} está embarazada. Quedan ~{_TICKS_EMBARAZO} expediciones."


def _nacer_hijo(
    personaje: "Sobreviviente",
    npc_id_padre: str,
    rng: random.Random,
) -> str:
    """
    Crea un hijo como NPC en el refugio, vinculado a ambos padres.
    Devuelve el mensaje de nacimiento.
    """
    if not hasattr(personaje, "familia"):
        personaje.familia = {}

    genero  = rng.choice(("masculino", "femenino"))
    nombre  = rng.choice(NOMBRES_BEBES[genero])
    padre_estado = personaje.relaciones_refugio.get(npc_id_padre, {})
    apellido = padre_estado.get("apellido", getattr(personaje, "apellido", ""))

    # El hijo es un NPC especial con edad 0
    hijo_seed = f"hijo:{personaje.partida_id}:{personaje.dia}:{nombre}"
    hijo_id = generar_id_npc(nombre, apellido, set(personaje.relaciones_refugio.keys()))

    tipo_vinculo = "hijo" if genero == "masculino" else "hija"

    personaje.relaciones_refugio[hijo_id] = {
        "nombre":           nombre,
        "apellido":         apellido,
        "genero":           genero,
        "edad":             0,
        "rol":              "niño" if genero == "masculino" else "niña",
        "personalidad":     rng.choice(PERSONALIDADES_NPC),
        "puede_expedicion": False,
        "desc":             "Nacido en el refugio.",
        "confianza":        100,
        "lealtad":          100,
        "tension":          10,
        "hambre":           30,
        "salud":            85,
        "en_expedicion":    False,
        "dias_expedicion":  0,
        "veces_peleado":    0,
        "quiere_irse":      False,
        "estado_relacion":  "familiar",
        "es_menor":         True,
        "padres":           [npc_id_padre],  # El jugador es el otro padre implícito
        "hijos":            [],
        "pareja_id":        None,
        "embarazo_ticks":   0,
        "tick_nacimiento":  getattr(personaje, "dia", 0),
    }

    # Vincular hijo en árbol familiar
    personaje.familia[hijo_id] = {
        "tipo":    tipo_vinculo,
        "nombre":  nombre,
        "apellido": apellido,
    }

    # Añadir hijo a la lista del otro padre
    if npc_id_padre in personaje.relaciones_refugio:
        personaje.relaciones_refugio[npc_id_padre].setdefault("hijos", []).append(hijo_id)

    # Limpiar embarazo
    if npc_id_padre in personaje.relaciones_refugio:
        personaje.relaciones_refugio[npc_id_padre]["embarazo_ticks"] = 0

    personaje.moral = min(100, personaje.moral + 20)
    return (
        f"[Familia] {nombre} ha llegado al mundo. "
        f"Sus primeros lloros llenan el refugio de algo que hace tiempo no se sentía."
    )


def _hacer_crecer_hijo(npc_id: str, estado: dict, dia_actual: int) -> str | None:
    """
    Actualiza la edad del hijo y dispara hitos de crecimiento.
    Un año de juego = ~365 días. Se llama cada tick.
    Devuelve mensaje de hito o None.
    """
    dia_nac  = estado.get("tick_nacimiento", 0)
    dias_vivo = dia_actual - dia_nac
    edad_nueva = max(0, dias_vivo // 365)
    edad_vieja = int(estado.get("edad", 0))

    if edad_nueva <= edad_vieja:
        return None

    estado["edad"] = edad_nueva
    nombre = estado.get("nombre", "")

    # Actualizar capacidades según edad
    if edad_nueva >= EDAD_ADULTO:
        estado["es_menor"]         = False
        estado["puede_expedicion"] = (
            estado.get("personalidad", "") in PERSONALIDADES_EXPEDICION
            or estado.get("rol", "") in ROLES_EXPEDICION
        )
        estado["rol"] = estado.get("rol_adulto", "explorador")
    elif edad_nueva >= EDAD_JOVEN:
        estado["es_menor"] = True  # Sigue siendo menor pero puede ayudar

    # Hito de esta edad exacta
    hito = HITOS_CRECIMIENTO.get(edad_nueva)
    if hito:
        return f"[Familia] {nombre} ({edad_nueva}a) — {hito}"
    return None


# ══════════════════════════════════════════════════════════════
#  RELACIONES NPC ↔ NPC
# ══════════════════════════════════════════════════════════════

def _evaluar_pareja_npc_npc(
    personaje: "Sobreviviente",
    rng: random.Random,
) -> str | None:
    """
    Evalúa si dos NPCs del refugio podrían formar pareja.
    Condiciones: mismas condiciones de confianza que el jugador,
    los dos sin pareja, sin ser parientes directos.
    Devuelve mensaje narrativo o None.
    """
    ids = [
        npc_id for npc_id, est in personaje.relaciones_refugio.items()
        if not est.get("es_menor", False)
        and est.get("pareja_id") is None
        and est.get("confianza", 0) >= CONFIANZA_PARA_ESTADO["cercano"]
        and est.get("estado_relacion", "") not in ("pareja", "ex_pareja")
    ]
    if len(ids) < 2:
        return None

    rng.shuffle(ids)
    a_id, b_id = ids[0], ids[1]
    a, b = personaje.relaciones_refugio[a_id], personaje.relaciones_refugio[b_id]

    # No parientes directos
    if a_id in b.get("hijos", []) or b_id in a.get("hijos", []):
        return None
    if a_id in b.get("padres", []) or b_id in a.get("padres", []):
        return None

    a["pareja_id"] = b_id
    b["pareja_id"] = a_id
    a["confianza"] = min(100, int(a.get("confianza", 50)) + 8)
    b["confianza"] = min(100, int(b.get("confianza", 50)) + 8)

    return (
        f"[Refugio] {a['nombre']} y {b['nombre']} parecen haber encontrado "
        f"algo el uno en el otro. El refugio lo nota."
    )


def _evaluar_embarazo_npc_npc(
    personaje: "Sobreviviente",
    rng: random.Random,
) -> str | None:
    """Evalúa si una pareja NPC-NPC puede concebir y dispara el embarazo."""
    for npc_id, estado in personaje.relaciones_refugio.items():
        pareja_id = estado.get("pareja_id")
        if not pareja_id or pareja_id not in personaje.relaciones_refugio:
            continue
        pareja = personaje.relaciones_refugio[pareja_id]
        if estado.get("embarazo_ticks", 0) > 0:
            continue
        edad_a = int(estado.get("edad", 0))
        edad_b = int(pareja.get("edad", 0))
        if not (_MIN_EDAD_HIJOS <= edad_a <= _MAX_EDAD_HIJOS):
            continue
        if not (_MIN_EDAD_HIJOS <= edad_b <= _MAX_EDAD_HIJOS):
            continue
        if int(estado.get("salud", 100)) < 40 or int(pareja.get("salud", 100)) < 40:
            continue
        if rng.random() < 0.015:  # ~1.5% por tick
            estado["embarazo_ticks"] = _TICKS_EMBARAZO
            return (
                f"[Refugio] {estado['nombre']} y {pareja['nombre']} "
                f"esperan un hijo. La vida sigue adelante."
            )
    return None


def _resolver_nacimiento_npc_npc(
    personaje: "Sobreviviente",
    rng: random.Random,
) -> str | None:
    """Resuelve el nacimiento de un hijo de pareja NPC-NPC."""
    for npc_id, estado in list(personaje.relaciones_refugio.items()):
        if estado.get("embarazo_ticks", 0) <= 0:
            continue
        estado["embarazo_ticks"] -= 1
        if estado["embarazo_ticks"] > 0:
            continue

        # Nacer
        pareja_id = estado.get("pareja_id")
        genero   = rng.choice(("masculino", "femenino"))
        nombre   = rng.choice(NOMBRES_BEBES[genero])
        apellido = estado.get("apellido", "")
        hijo_id  = generar_id_npc(nombre, apellido, set(personaje.relaciones_refugio.keys()))

        personaje.relaciones_refugio[hijo_id] = {
            "nombre":           nombre,
            "apellido":         apellido,
            "genero":           genero,
            "edad":             0,
            "rol":              "niño" if genero == "masculino" else "niña",
            "personalidad":     rng.choice(PERSONALIDADES_NPC),
            "puede_expedicion": False,
            "desc":             f"Hijo/a de {estado['nombre']}.",
            "confianza":        80,
            "lealtad":          80,
            "tension":          10,
            "hambre":           30,
            "salud":            85,
            "en_expedicion":    False,
            "dias_expedicion":  0,
            "veces_peleado":    0,
            "quiere_irse":      False,
            "estado_relacion":  "familiar",
            "es_menor":         True,
            "padres":           [npc_id, pareja_id] if pareja_id else [npc_id],
            "hijos":            [],
            "pareja_id":        None,
            "embarazo_ticks":   0,
            "tick_nacimiento":  getattr(personaje, "dia", 0),
        }
        estado.setdefault("hijos", []).append(hijo_id)
        if pareja_id and pareja_id in personaje.relaciones_refugio:
            personaje.relaciones_refugio[pareja_id].setdefault("hijos", []).append(hijo_id)

        personaje.moral = min(100, personaje.moral + 8)
        return (
            f"[Refugio] {nombre} nace en el refugio. "
            f"Hijo/a de {estado['nombre']}."
        )
    return None


# ══════════════════════════════════════════════════════════════
#  TICK FAMILIA (llamado desde tick_refugio)
# ══════════════════════════════════════════════════════════════

def tick_familia(
    personaje: "Sobreviviente",
    horas: float,
    rng: random.Random,
) -> list[str]:
    """
    Avanza todos los sistemas familiares en un tick:
      - Crecimiento de hijos
      - Progresión automática de relaciones románticas
      - Embarazos y nacimientos (jugador y NPC-NPC)
      - Formación de nuevas parejas entre NPCs
    Devuelve lista de mensajes narrativos.
    """
    mensajes: list[str] = []
    dia_actual = getattr(personaje, "dia", 0)

    for npc_id, estado in list(personaje.relaciones_refugio.items()):

        # ── Crecer hijos ───────────────────────────────────────────────────────
        if estado.get("es_menor") or estado.get("edad", 99) < EDAD_ADULTO:
            if "tick_nacimiento" in estado:
                msg = _hacer_crecer_hijo(npc_id, estado, dia_actual)
                if msg:
                    mensajes.append(msg)

        # ── Embarazo jugador ───────────────────────────────────────────────────
        ticks_emb = int(estado.get("embarazo_ticks", 0))
        if ticks_emb > 0 and estado.get("pareja_id") is None:
            # Esta es la pareja del jugador con embarazo activo
            estado["embarazo_ticks"] = ticks_emb - 1
            if estado["embarazo_ticks"] == 0:
                msg = _nacer_hijo(personaje, npc_id, rng)
                mensajes.append(msg)

        # ── Progresión automática de estado_relacion ───────────────────────────
        nuevo_estado = avanzar_estado_relacion(npc_id, personaje)
        if nuevo_estado == "interes":
            # El simulador propone la relación vía evento
            nombre = estado.get("nombre", "Alguien")
            mensajes.append(
                f"[Relación] {nombre} parece sentir algo por ti. "
                f"Puedes responder en el menú de supervivientes [v]."
            )
        elif nuevo_estado == "pareja" and npc_id not in getattr(personaje, "familia", {}):
            # Formalizar vínculo que ya tenía confianza suficiente
            _establecer_pareja(personaje, npc_id)

    # ── Parejas NPC-NPC ────────────────────────────────────────────────────────
    if rng.random() < 0.12:
        msg = _evaluar_pareja_npc_npc(personaje, rng)
        if msg:
            mensajes.append(msg)

    # ── Embarazos y nacimientos NPC-NPC ────────────────────────────────────────
    msg_emb = _evaluar_embarazo_npc_npc(personaje, rng)
    if msg_emb:
        mensajes.append(msg_emb)

    msg_nac = _resolver_nacimiento_npc_npc(personaje, rng)
    if msg_nac:
        mensajes.append(msg_nac)

    return mensajes
