# ============================================================
# engine/combate.py — Motor de combate por turnos
# Lee enemigos desde data/enemigos.py, sin datos hardcodeados.
# ============================================================
import random
from data.enemigos import ENEMIGOS
from data.items    import ITEMS
from data.skills   import SKILLS
from engine.personaje import Condicion
from engine.constants import (
    MAX_TURNOS_COMBATE, SALUD_PCT_HUIDA_CRITICA, TURNO_MIN_HUIDA,
    PROB_CRITICO, MULT_DAÑO_CRITICO, DIFICULTAD_GOLPE_BASE,
    DIFICULTAD_GOLPE_POR_VELOCIDAD, PROB_LOOT_ENEMIGO,
    MULT_DAÑO_EMBOSCADA, PROB_ATAQUE_ACIDO, DAÑO_EXTRA_ACIDO,
    PROB_MORDIDA_INFECTADA, DAÑO_HORDA_HUIDA_MIN, DAÑO_HORDA_HUIDA_MAX,
    DAÑO_HORDA_ATRAPADO_MIN, DAÑO_HORDA_ATRAPADO_MAX,
    DAÑO_MANOS_MIN, DAÑO_MANOS_MAX, SUERTE_MIN_CRITICO,
)


class ResultadoCombate:
    def __init__(self):
        self.victoria        = False
        self.huida           = False
        self.derrota         = False
        self.daño_recibido   = 0
        self.daño_causado    = 0
        self.turnos          = 0
        self.loot_enemigo: list[dict] = []
        self.log:          list[str]  = []
        self.enemigo_nombre  = ""

    def añadir(self, linea: str):
        self.log.append(linea)


def resolver_combate(personaje, enemigo_key: str,
                     iniciativa: str = "tirar",
                     bonus_ataque: int = 0) -> ResultadoCombate:
    """
    Simula un combate completo por turnos.
    iniciativa: 'jugador' | 'enemigo' | 'tirar'

    XP:
      - Cada golpe exitoso otorga xp_por_uso de la skill usada.
      - Al neutralizar al enemigo se suma la xp del campo 'xp' del enemigo.
      - Todo el XP se acumula vía ganar_xp_skill() y se muestra al final
        del tick en la sección PROGRESO (no inline en el combate).
    """
    resultado = ResultadoCombate()
    enemigo   = dict(ENEMIGOS[enemigo_key])
    resultado.enemigo_nombre = enemigo["nombre"]

    salud_enemigo = random.randint(*enemigo["salud"])
    resultado.añadir(f"  ▶ {enemigo['nombre']} — {enemigo['descripcion']}")

    if enemigo.get("solo_huida"):
        return _resolver_horda(resultado, personaje, enemigo)

    skill_combate, daño_base = _determinar_arma_jugador(resultado, personaje)
    iniciativa = _resolver_iniciativa(iniciativa, personaje, enemigo)

    xp_por_golpe = SKILLS.get(skill_combate, {}).get("xp_por_uso", 2)

    turno      = 0
    max_turnos = MAX_TURNOS_COMBATE

    while salud_enemigo > 0 and personaje.esta_vivo() and turno < max_turnos:
        turno += 1
        resultado.turnos = turno

        if iniciativa == "jugador" or turno > 1:
            salud_enemigo = _turno_jugador(
                resultado, personaje, enemigo, salud_enemigo,
                skill_combate, daño_base, xp_por_golpe, bonus_ataque, turno
            )

        if salud_enemigo <= 0:
            break

        _turno_enemigo(resultado, personaje, enemigo, turno, iniciativa)

        if _debe_huir(personaje, turno):
            if personaje.check_stat("destreza", 4):
                resultado.huida = True
                resultado.añadir("  ¡Salud crítica! Huyes exitosamente.")
                break
            else:
                resultado.añadir("  Intentas huir pero el enemigo te bloquea.")

    return _cerrar_combate(resultado, personaje, enemigo, skill_combate,
                           salud_enemigo, enemigo_key, turno)


# ──────────────────────────────────────────────────────────────
#  HELPERS INTERNOS
# ──────────────────────────────────────────────────────────────

def _resolver_horda(resultado: ResultadoCombate, personaje, enemigo: dict) -> ResultadoCombate:
    """Hordas no combatibles: sólo se puede huir, con daño variable."""
    resultado.añadir("  ¡Una HORDA! Imposible combatirla. Debes huir.")
    if personaje.check_stat("destreza", 5):
        daño = personaje.recibir_daño(random.randint(DAÑO_HORDA_HUIDA_MIN, DAÑO_HORDA_HUIDA_MAX))
        resultado.daño_recibido = daño
        resultado.huida = True
        resultado.añadir(f"  Huiste con dificultad. -{daño} hp.")
    else:
        daño = personaje.recibir_daño(random.randint(DAÑO_HORDA_ATRAPADO_MIN, DAÑO_HORDA_ATRAPADO_MAX))
        resultado.daño_recibido = daño
        resultado.huida = True
        resultado.añadir(f"  La horda te atrapó un momento. -{daño} hp.")
    return resultado


def _determinar_arma_jugador(resultado: ResultadoCombate, personaje) -> tuple[str, tuple]:
    """Detecta el arma equipada y devuelve (skill_combate, rango_daño)."""
    arma = personaje.arma_equipada()
    if arma:
        daño_base     = arma.get("daño", (3, 7))
        skill_combate = ("combate_distancia" if arma.get("tipo") == "arma_fuego"
                          else "combate_cac")
        resultado.añadir(
            f"  (Arma activa: {arma.get('nombre', 'Arma')} "
            f"{daño_base[0]}-{daño_base[1]})"
        )
    else:
        daño_base     = (DAÑO_MANOS_MIN, DAÑO_MANOS_MAX)
        skill_combate = "combate_cac"
        resultado.añadir("  (Sin arma equipada. Combate a manos limpias.)")
        bloqueada = personaje.mejor_arma_bloqueada()
        if bloqueada:
            resultado.añadir(f"  ({personaje.motivo_bloqueo_arma(bloqueada)})")
    return skill_combate, daño_base


def _resolver_iniciativa(iniciativa: str, personaje, enemigo: dict) -> str:
    """Resuelve quién actúa primero si la iniciativa no está fijada."""
    if iniciativa != "tirar":
        return iniciativa
    velocidad_enemigo = enemigo.get("velocidad", 2)
    gana_jugador = (
        personaje.stats["destreza"] + random.randint(1, 6)
        > velocidad_enemigo + random.randint(1, 6)
    )
    return "jugador" if gana_jugador else "enemigo"


def _turno_jugador(
    resultado: ResultadoCombate,
    personaje,
    enemigo: dict,
    salud_enemigo: int,
    skill_combate: str,
    daño_base: tuple,
    xp_por_golpe: int,
    bonus_ataque: int,
    turno: int,
) -> int:
    """Ejecuta el ataque del jugador. Devuelve la salud restante del enemigo."""
    dificultad = (
        DIFICULTAD_GOLPE_BASE
        + enemigo.get("velocidad", 2) * DIFICULTAD_GOLPE_POR_VELOCIDAD
        - bonus_ataque
    )
    if not personaje.check_skill(skill_combate, dificultad):
        resultado.añadir(f"  T{turno} Tu ataque falla.")
        return salud_enemigo

    personaje.ganar_xp_skill(skill_combate, xp_por_golpe)

    daño  = random.randint(*daño_base)
    daño += personaje.bonus_sinergia_arma(personaje.arma_equipada())

    mult_rasgo = personaje.obtener_efecto_rasgo("daño_cac_mult", 1.0)
    if skill_combate == "combate_cac":
        daño = int(daño * mult_rasgo)

    # Golpe crítico — sólo posible con suerte alta.
    if personaje.stats["suerte"] >= SUERTE_MIN_CRITICO and random.random() < PROB_CRITICO:
        daño = int(daño * MULT_DAÑO_CRITICO)
        resultado.añadir(f"  T{turno} ★ CRÍTICO → {enemigo['nombre']}: -{daño} hp")
    else:
        resultado.añadir(f"  T{turno} Atacas al {enemigo['nombre']}: -{daño} hp")

    resultado.daño_causado += daño
    return salud_enemigo - daño


def _turno_enemigo(
    resultado: ResultadoCombate,
    personaje,
    enemigo: dict,
    turno: int,
    iniciativa: str,
) -> None:
    """Ejecuta el ataque del enemigo contra el jugador."""
    velocidad   = enemigo.get("velocidad", 2)
    dif_esquive = 3 + velocidad
    dif_esquive += personaje.obtener_efecto_rasgo("dificultad_esquive", 0)

    if personaje.check_stat("destreza", dif_esquive):
        resultado.añadir(f"  T{turno} Esquivas el ataque del {enemigo['nombre']}.")
        return

    daño_enemigo = random.randint(*enemigo["daño"])
    habilidades  = enemigo.get("habilidades", [])

    if "emboscada" in habilidades and turno == 1 and iniciativa == "enemigo":
        daño_enemigo = int(daño_enemigo * MULT_DAÑO_EMBOSCADA)
        resultado.añadir(f"  T{turno} ¡EMBOSCADA! {enemigo['nombre']}: -{daño_enemigo} hp")
    elif "salpicadura_acida" in habilidades and random.random() < PROB_ATAQUE_ACIDO:
        daño_enemigo += DAÑO_EXTRA_ACIDO
        resultado.añadir(f"  T{turno} {enemigo['nombre']} escupe ácido: -{daño_enemigo} hp ⚗")
    else:
        resultado.añadir(f"  T{turno} {enemigo['nombre']} te golpea: -{daño_enemigo} hp")

    daño_real = personaje.recibir_daño(daño_enemigo)
    resultado.daño_recibido += daño_real

    if "mordida_infectada" in habilidades and random.random() < PROB_MORDIDA_INFECTADA:
        condicion = Condicion("infeccion_leve", "Infección leve", 1, 5,
                              {"daño_por_turno": 2})
        personaje.añadir_condicion(condicion)
        resultado.añadir("  ¡La mordida parece infectada!")


def _debe_huir(personaje, turno: int) -> bool:
    """Devuelve True si el personaje está en estado crítico y puede intentar huir."""
    return (
        personaje.salud < personaje.salud_max * SALUD_PCT_HUIDA_CRITICA
        and turno >= TURNO_MIN_HUIDA
    )


def _cerrar_combate(
    resultado: ResultadoCombate,
    personaje,
    enemigo: dict,
    skill_combate: str,
    salud_enemigo: int,
    enemigo_key: str,
    turno: int,
) -> ResultadoCombate:
    """Determina el resultado final y registra contadores y loot."""
    if salud_enemigo <= 0:
        resultado.victoria = True
        resultado.añadir(f"  ✔ {enemigo['nombre']} neutralizado en {turno} turnos.")
        for loot_key in enemigo.get("loot", []):
            if loot_key and loot_key in ITEMS and random.random() < PROB_LOOT_ENEMIGO:
                resultado.loot_enemigo.append(dict(ITEMS[loot_key]))
        personaje.ganar_xp_skill(skill_combate, enemigo.get("xp", 10))
        if "infectado" in enemigo_key:
            personaje.infectados_eliminados += 1
        elif "bandido" in enemigo_key:
            personaje.bandidos_eliminados += 1
    elif not resultado.huida:
        resultado.derrota = True
        resultado.añadir("  ✖ Has sido derrotado/a.")

    personaje.evaluar_rasgos_nuevos()
    return resultado
