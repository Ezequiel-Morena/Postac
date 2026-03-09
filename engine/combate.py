# ============================================================
# engine/combate.py — Motor de combate por turnos
# Lee enemigos desde data/enemigos.py, sin datos hardcodeados.
# ============================================================
import random
from data.enemigos import ENEMIGOS
from data.items    import ITEMS
from engine.personaje import Condicion


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
    """
    r   = ResultadoCombate()
    ene = dict(ENEMIGOS[enemigo_key])
    r.enemigo_nombre = ene["nombre"]

    salud_ene = random.randint(*ene["salud"])
    r.añadir(f"  ▶ {ene['nombre']} — {ene['descripcion']}")

    # ── HORDA: solo huida ─────────────────────────────────────
    if ene.get("solo_huida"):
        r.añadir("  ¡Una HORDA! Imposible combatirla. Debes huir.")
        if personaje.check_stat("destreza", 5):
            r.daño_recibido = personaje.recibir_daño(random.randint(5, 15))
            r.huida = True
            r.añadir(f"  Huiste con dificultad. -{r.daño_recibido} hp.")
        else:
            r.daño_recibido = personaje.recibir_daño(random.randint(25, 50))
            r.huida = True
            r.añadir(f"  La horda te atrapó un momento. -{r.daño_recibido} hp.")
        return r

    # ── ARMA DEL JUGADOR ──────────────────────────────────────
    arma = personaje.arma_equipada()
    if arma:
        daño_base    = arma.get("daño", (3, 7))
        skill_combate = ("combate_distancia" if arma.get("tipo") == "arma_fuego"
                          else "combate_cac")
    else:
        daño_base    = (2, 5)
        skill_combate = "combate_cac"
        r.añadir("  (Sin arma equipada. Combate a manos limpias.)")

    # ── INICIATIVA ────────────────────────────────────────────
    if iniciativa == "tirar":
        vel_ene = ene.get("velocidad", 2)
        iniciativa = ("jugador"
                      if personaje.stats["destreza"] + random.randint(1, 6)
                         > vel_ene + random.randint(1, 6)
                      else "enemigo")

    turno      = 0
    max_turnos = 12

    while salud_ene > 0 and personaje.esta_vivo() and turno < max_turnos:
        turno += 1
        r.turnos = turno

        # ── TURNO DEL JUGADOR ─────────────────────────────────
        if iniciativa == "jugador" or turno > 1:
            dif_golpe = 40 + ene.get("velocidad", 2) * 5
            if personaje.check_skill(skill_combate, dif_golpe - bonus_ataque):
                dmg = random.randint(*daño_base)
                # Rasgo golpe_brutal
                mult = personaje.obtener_efecto_rasgo("daño_cac_mult", 1.0)
                if skill_combate == "combate_cac":
                    dmg = int(dmg * mult)
                # Crítico
                if personaje.stats["suerte"] >= 8 and random.random() < 0.15:
                    dmg = int(dmg * 1.8)
                    r.añadir(f"  T{turno} ★ CRÍTICO → {ene['nombre']}: -{dmg} hp")
                else:
                    r.añadir(f"  T{turno} Atacas al {ene['nombre']}: -{dmg} hp")
                salud_ene -= dmg
                r.daño_causado += dmg
            else:
                r.añadir(f"  T{turno} Tu ataque falla.")

            if salud_ene <= 0:
                break

        # ── TURNO DEL ENEMIGO ─────────────────────────────────
        vel         = ene.get("velocidad", 2)
        dif_esquive = 3 + vel
        # Rasgo esquivador
        dif_esquive += personaje.obtener_efecto_rasgo("dificultad_esquive", 0)

        if not personaje.check_stat("destreza", dif_esquive):
            dmg_ene = random.randint(*ene["daño"])

            # Habilidades especiales del enemigo
            habs = ene.get("habilidades", [])
            if "emboscada" in habs and turno == 1 and iniciativa == "enemigo":
                dmg_ene = int(dmg_ene * 1.5)
                r.añadir(f"  T{turno} ¡EMBOSCADA! {ene['nombre']}: -{dmg_ene} hp")
            elif "salpicadura_acida" in habs and random.random() < 0.3:
                dmg_ene += 8
                r.añadir(f"  T{turno} {ene['nombre']} escupe ácido: -{dmg_ene} hp ⚗")
            else:
                r.añadir(f"  T{turno} {ene['nombre']} te golpea: -{dmg_ene} hp")

            real = personaje.recibir_daño(dmg_ene)
            r.daño_recibido += real

            # Condición por mordida
            if "mordida_infectada" in habs and random.random() < 0.30:
                c = Condicion("infeccion_leve", "Infección leve", 1, 5,
                              {"daño_por_turno": 2})
                personaje.añadir_condicion(c)
                r.añadir("  ¡La mordida parece infectada!")
        else:
            r.añadir(f"  T{turno} Esquivas el ataque del {ene['nombre']}.")

        # ── HUIDA AUTOMÁTICA si salud crítica ─────────────────
        if personaje.salud < personaje.salud_max * 0.25 and turno >= 2:
            if personaje.check_stat("destreza", 4):
                r.huida = True
                r.añadir("  ¡Salud crítica! Huyes exitosamente.")
                break
            else:
                r.añadir("  Intentas huir pero el enemigo te bloquea.")

    # ── RESULTADO FINAL ───────────────────────────────────────
    if salud_ene <= 0:
        r.victoria = True
        r.añadir(f"  ✔ {ene['nombre']} neutralizado en {turno} turnos.")
        # Loot del enemigo
        for loot_key in ene.get("loot", []):
            if loot_key and loot_key in ITEMS and random.random() < 0.60:
                r.loot_enemigo.append(dict(ITEMS[loot_key]))
        # XP en skill
        xp = ene.get("xp", 10)
        mejora = max(1, xp // 15)
        personaje.skills[skill_combate] = min(
            100, personaje.skills[skill_combate] + mejora)
        # Contadores
        if "infectado" in enemigo_key:
            personaje.infectados_eliminados += 1
        elif "bandido" in enemigo_key:
            personaje.bandidos_eliminados += 1

    elif not r.huida:
        r.derrota = True
        r.añadir("  ✖ Has sido derrotado/a.")

    personaje.evaluar_rasgos_nuevos()
    return r
