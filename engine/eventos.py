# ============================================================
# engine/eventos.py — Resolución de eventos
# Lee eventos desde data/eventos.py, sin datos hardcodeados.
# ============================================================
import random
import copy
from data.eventos  import EVENTOS
from data.items    import ITEMS
from data.loot     import LOOT_POOLS
from engine.personaje import Condicion
from engine.combate   import resolver_combate


class ResultadoEvento:
    def __init__(self):
        self.tipo            = ""
        self.titulo          = ""
        self.log:            list[str]  = []
        self.items_obtenidos: list[dict] = []
        self.daño_recibido   = 0
        self.moral_cambio    = 0
        self.info_obtenida   = {}
        self.combate         = None

    def añadir(self, linea: str):
        self.log.append(linea)


# ──────────────────────────────────────────────────────────────
#  DISPATCHER PRINCIPAL
# ──────────────────────────────────────────────────────────────
def resolver_evento(personaje, evento_key: str, area: dict) -> ResultadoEvento:
    if evento_key not in EVENTOS:
        return _evento_generico(personaje, area)

    tmpl = EVENTOS[evento_key]
    r    = ResultadoEvento()
    r.tipo   = tmpl["tipo"]
    r.titulo = tmpl["titulo"]
    r.añadir(f"  📍 {tmpl['titulo'].upper()}")
    r.añadir(f"  {tmpl['descripcion']}")

    t = tmpl["tipo"]

    if t == "combate":
        _resolver_combate_directo(r, personaje, tmpl)

    elif t == "combate_evadible":
        _resolver_combate_evadible(r, personaje, tmpl, area)

    elif t in ("hallazgo", "hallazgo_especial"):
        _resolver_hallazgo(r, personaje, tmpl, area)

    elif t == "interaccion":
        _resolver_interaccion(r, personaje, tmpl, area)

    elif t == "npc_amigable":
        _resolver_npc_amigable(r, personaje, tmpl)

    elif t == "npc_dilema":
        _resolver_npc_dilema(r, personaje, tmpl)

    elif t == "npc_especial":
        _resolver_npc_especial(r, personaje, tmpl)

    elif t == "peligro_ambiental":
        _resolver_peligro_ambiental(r, personaje, tmpl)

    elif t == "ambiental_forzado":
        _resolver_ambiental_forzado(r, personaje, tmpl)

    elif t == "ambiental_acumulativo":
        _resolver_ambiental_acumulativo(r, personaje, tmpl)

    elif t in ("narrativo", "narrativo_especial"):
        _resolver_narrativo(r, personaje, tmpl)

    elif t == "peligro_oculto":
        _resolver_peligro_oculto(r, personaje, tmpl)

    # Aplicar cambio de moral
    if r.moral_cambio != 0:
        personaje.moral = max(0, min(100, personaje.moral + r.moral_cambio))

    return r


# ──────────────────────────────────────────────────────────────
#  RESOLVERS POR TIPO
# ──────────────────────────────────────────────────────────────
def _resolver_combate_directo(r, personaje, tmpl):
    resultado_c = resolver_combate(personaje, tmpl["enemigo"],
                                   tmpl.get("iniciativa", "tirar"))
    r.combate = resultado_c
    for linea in resultado_c.log:
        r.añadir(linea)
    r.items_obtenidos.extend(resultado_c.loot_enemigo)
    r.daño_recibido = resultado_c.daño_recibido
    if resultado_c.derrota:
        r.tipo = "combate_derrota"


def _resolver_combate_evadible(r, personaje, tmpl, area):
    opciones   = tmpl.get("opciones", {})
    opcion_key = _ia_elegir_opcion(personaje, opciones)
    opcion     = opciones[opcion_key]
    r.añadir(f"\n  → Decisión: {opcion['texto']}")

    if opcion_key == "huida":
        r.añadir("  Te retiras silenciosamente. Evitas el enfrentamiento.")
        r.moral_cambio = opcion.get("moral_costo", -3)

    elif opcion_key == "sigilo":
        if personaje.check_skill(opcion.get("skill", "sigilo"),
                                  opcion.get("dificultad", 50)):
            r.añadir("  Te ocultas perfectamente. Pasan sin verte.")
        else:
            r.añadir("  No pudiste ocultarte. ¡Te descubren!")
            resultado_c = resolver_combate(personaje, tmpl["enemigo"])
            r.combate = resultado_c
            for l in resultado_c.log: r.añadir(l)
            r.daño_recibido = resultado_c.daño_recibido

    elif opcion_key == "combate":
        bonus = opcion.get("bonus_ataque", 0)
        resultado_c = resolver_combate(personaje, tmpl["enemigo"],
                                       "jugador", bonus_ataque=bonus)
        r.combate = resultado_c
        for l in resultado_c.log: r.añadir(l)
        r.daño_recibido = resultado_c.daño_recibido
        r.items_obtenidos.extend(resultado_c.loot_enemigo)


def _resolver_hallazgo(r, personaje, tmpl, area):
    from engine.mundo import generar_loot_area
    items = generar_loot_area(area, personaje)
    if tmpl.get("loot_bonus", 1.0) > 1.0:
        items += generar_loot_area(area, personaje)[:2]
    for key in tmpl.get("loot_extra", []):
        if key in ITEMS:
            items.append(copy.deepcopy(ITEMS[key]))
    r.items_obtenidos.extend(items)
    r.moral_cambio = tmpl.get("moral_costo", 0)
    if items:
        r.añadir(f"  Encontraste: {', '.join(i['nombre'] for i in items[:4])}")
    else:
        r.añadir("  Revisaste bien. Nada de valor esta vez.")


def _resolver_interaccion(r, personaje, tmpl, area):
    opciones   = tmpl.get("opciones", {})
    opcion_key = _ia_elegir_opcion(personaje, opciones)
    opcion     = opciones[opcion_key]
    r.añadir(f"\n  → Decisión: {opcion['texto']}")

    if opcion.get("resultado") == "nada":
        r.añadir("  Lo dejás pasar.")
        return

    exito = False
    if "skill" in opcion:
        exito = personaje.check_skill(opcion["skill"], opcion.get("dificultad", 50))
    elif "stat" in opcion:
        exito = personaje.check_stat(opcion["stat"], opcion.get("dificultad", 5))

    if exito:
        r.añadir("  ¡Éxito!")
        for key in opcion.get("loot_exito", []):
            if key in ITEMS and random.random() < 0.7:
                r.items_obtenidos.append(copy.deepcopy(ITEMS[key]))
    else:
        r.añadir("  Fallaste.")
        if opcion.get("ruido_fallo") and random.random() < 0.40:
            r.añadir("  El ruido atrae a un infectado...")
            resultado_c = resolver_combate(personaje, "infectado_lento")
            r.combate = resultado_c
            for l in resultado_c.log: r.añadir(l)
            r.daño_recibido = resultado_c.daño_recibido


def _resolver_npc_amigable(r, personaje, tmpl):
    opciones   = tmpl.get("opciones", {})
    opcion_key = _ia_elegir_npc(personaje, opciones)
    opcion     = opciones[opcion_key]
    r.añadir(f"\n  → Decisión: {opcion['texto']}")

    costo      = opcion.get("costo", {})
    recompensa = opcion.get("recompensa", {})

    # Aplicar costos (busca items por tipo aproximado)
    if costo.get("comida"):
        for nombre in ["Lata de frijoles", "Lata de atún", "Barrita energética"]:
            if personaje.remover_item(nombre):
                break
    if costo.get("agua"):
        personaje.remover_item("Botella de agua")

    r.moral_cambio = opcion.get("moral_bonus", 0) - opcion.get("moral_costo", 0)

    if recompensa.get("info_zona"):
        r.info_obtenida["info_zona"] = True
        r.añadir("  Compartió información valiosa sobre la zona.")

    loot_key = recompensa.get("loot_key")
    if loot_key and loot_key in ITEMS and random.random() < recompensa.get("prob", 1.0):
        r.items_obtenidos.append(copy.deepcopy(ITEMS[loot_key]))
        r.añadir(f"  Te entregó: {ITEMS[loot_key]['nombre']}")


def _resolver_npc_dilema(r, personaje, tmpl):
    opciones   = tmpl.get("opciones", {})
    opcion_key = _ia_elegir_npc(personaje, opciones)
    opcion     = opciones[opcion_key]
    r.añadir(f"\n  → Decisión: {opcion['texto']}")

    r.moral_cambio = opcion.get("moral_bonus", 0) - opcion.get("moral_costo", 0)

    if costo := opcion.get("costo", {}):
        if costo.get("comida"):
            for nombre in ["Lata de frijoles", "Lata de atún"]:
                if personaje.remover_item(nombre): break
        if costo.get("agua"):
            personaje.remover_item("Botella de agua")

    for loot_key in opcion.get("loot", []):
        if loot_key in ITEMS:
            r.items_obtenidos.append(copy.deepcopy(ITEMS[loot_key]))

    personaje.muertes_vistas += 1 if opcion_key == "ignorar" else 0


def _resolver_npc_especial(r, personaje, tmpl):
    r.añadir("  El comerciante revisa su mercancía...")
    inv = tmpl.get("inventario_comerciante", [])
    # Por ahora ofrece un item aleatorio gratuitamente (si tiene moral alta)
    if inv and personaje.moral > 60:
        key = random.choice(inv)
        if key in ITEMS:
            r.items_obtenidos.append(copy.deepcopy(ITEMS[key]))
            r.añadir(f"  'Toma esto. Parece que lo necesitás.' → {ITEMS[key]['nombre']}")
    else:
        r.añadir("  No tenías nada para intercambiar. Se despide y sigue su camino.")


def _resolver_peligro_ambiental(r, personaje, tmpl):
    opciones = tmpl.get("opciones", {})
    if not opciones:
        daño  = tmpl.get("daño", (5, 15))
        real  = personaje.recibir_daño(random.randint(*daño))
        r.daño_recibido = real
        r.añadir(f"  No pudiste evitarlo. -{real} hp.")
        return

    opcion_key = _ia_elegir_opcion(personaje, opciones)
    opcion     = opciones[opcion_key]
    r.añadir(f"\n  → Decisión: {opcion['texto']}")

    if "daño" in opcion:  # atravesar llamas, etc.
        real = personaje.recibir_daño(random.randint(*opcion["daño"]))
        r.daño_recibido = real
        r.añadir(f"  Doloroso pero superado. -{real} hp.")
        return

    exito = False
    if "stat" in opcion:
        exito = personaje.check_stat(opcion["stat"], opcion.get("dificultad", 5))
    elif "skill" in opcion:
        exito = personaje.check_skill(opcion["skill"], opcion.get("dificultad", 50))
    else:
        exito = True

    if not exito and "fallo_daño" in opcion:
        real = personaje.recibir_daño(random.randint(*opcion["fallo_daño"]))
        r.daño_recibido = real
        r.añadir(f"  Algo salió mal. -{real} hp.")
    elif exito:
        r.añadir("  Superado sin problemas.")

    personaje.fatiga = min(100, personaje.fatiga + opcion.get("fatiga_costo", 0))


def _resolver_ambiental_forzado(r, personaje, tmpl):
    prot_item = tmpl.get("proteccion_item", "")
    tiene_prot = personaje.tiene_item(prot_item) if prot_item else False

    if tiene_prot:
        r.añadir(f"  Tu {prot_item} te protege de lo peor.")
        if tmpl.get("consume_proteccion"):
            personaje.usar_item(prot_item)
    else:
        daño = tmpl.get("daño_sin_proteccion", 10)
        real = personaje.recibir_daño(daño)
        r.daño_recibido = real
        r.añadir(f"  Sin protección. -{real} hp.")


def _resolver_ambiental_acumulativo(r, personaje, tmpl):
    prot_item = tmpl.get("proteccion_item", "")
    tiene_prot = personaje.tiene_item(prot_item) if prot_item else False

    rad = (tmpl.get("radiacion_protegido", 5)
           if tiene_prot else tmpl.get("radiacion_normal", 15))
    personaje.radiacion = min(100, personaje.radiacion + rad)
    r.añadir(f"  +{rad} radiación absorbida. Total: {personaje.radiacion}/100 ☢")


def _resolver_narrativo(r, personaje, tmpl):
    r.moral_cambio = tmpl.get("moral_bonus", 0) - tmpl.get("moral_costo", 0)
    if tmpl.get("info_zona"):
        r.info_obtenida["info_zona"] = True
    for key in tmpl.get("loot", []):
        if key in ITEMS:
            r.items_obtenidos.append(copy.deepcopy(ITEMS[key]))


def _resolver_peligro_oculto(r, personaje, tmpl):
    dif   = tmpl.get("percepcion_evitar", 5)
    evita = personaje.check_stat("percepcion", dif)

    if evita:
        r.añadir("  Tu percepción te alerta a tiempo. Rodeas la trampa.")
    else:
        real = personaje.recibir_daño(random.randint(*tmpl["daño"]))
        r.daño_recibido = real
        r.añadir(f"  ¡Trampa activada! -{real} hp.")
        if tmpl.get("condicion_aplica"):
            c = Condicion("herida_pierna", "Herida en pierna", 2, 8,
                          {"stats_global": -1})
            personaje.añadir_condicion(c)
            r.añadir("  Tu pierna queda lastimada (-1 a todas las stats).")


def _evento_generico(personaje, area: dict) -> ResultadoEvento:
    r = ResultadoEvento()
    r.titulo = "Zona tranquila"
    r.tipo   = "narrativo"
    r.añadir("  La zona está en silencio. Exploras con cuidado.")
    from engine.mundo import generar_loot_area
    for item in generar_loot_area(area, personaje)[:2]:
        r.items_obtenidos.append(item)
    return r


# ──────────────────────────────────────────────────────────────
#  IA HEURÍSTICA
# ──────────────────────────────────────────────────────────────
def _ia_elegir_opcion(personaje, opciones: dict) -> str:
    puntajes = {}
    for key, opcion in opciones.items():
        p = 50
        if opcion.get("resultado") == "nada":       p -= 20
        if "daño" in opcion and personaje.salud < personaje.salud_max * 0.4:
            p -= 35
        if key == "sigilo":
            p += personaje.skills.get("sigilo", 20) // 5
            if personaje.salud < personaje.salud_max * 0.5: p += 20
        if key == "combate":
            if personaje.arma_equipada():            p += 15
            if personaje.salud < personaje.salud_max * 0.4: p -= 30
        if key == "huida":
            if personaje.salud < personaje.salud_max * 0.35: p += 45
        if key in ("cuidadoso", "buscar_ruta"):      p += 10
        if key == "ignorar" and personaje.fatiga > 70: p += 10
        p += random.randint(-8, 8)
        puntajes[key] = p
    return max(puntajes, key=puntajes.get)


def _ia_elegir_npc(personaje, opciones: dict) -> str:
    puntajes = {}
    for key, opcion in opciones.items():
        p = 50
        costo     = opcion.get("costo", {})
        moral_bon = opcion.get("moral_bonus", 0)
        moral_cos = opcion.get("moral_costo", 0)

        if costo.get("comida"):
            tiene = any(i.get("tipo") == "comida" for i in personaje.inventario)
            if not tiene: p -= 40
        if costo.get("agua"):
            tiene = any(i.get("tipo") == "agua" for i in personaje.inventario)
            if not tiene: p -= 40

        if personaje.moral < 40:
            p += moral_bon * 2
        else:
            p += moral_bon
        p -= moral_cos
        if key == "ignorar" and personaje.moral < 30: p -= 20
        p += random.randint(-5, 5)
        puntajes[key] = p
    return max(puntajes, key=puntajes.get)


# ──────────────────────────────────────────────────────────────
#  GENERADOR DE SECUENCIA DE EVENTOS
# ──────────────────────────────────────────────────────────────
def generar_secuencia_eventos(area: dict, personaje) -> list[tuple]:
    """
    Genera la secuencia de eventos de una expedición.
    Retorna lista de tuplas (tipo, clave, zona).
    """
    estructura = area.get("estructura", ["interior"])
    peligro    = area["peligro"]
    enemigos   = area.get("enemigos", ["infectado_lento"])
    eventos_area = area.get("eventos", [])

    secuencia = []
    for zona in estructura:
        prob_combate = 0.10 + peligro * 0.08
        prob_evento  = 0.25
        tirada       = random.random()

        if tirada < prob_combate:
            enemigo = random.choice(enemigos)
            tipo_ini = "enemigo" if not personaje.check_stat("percepcion", 4) else "tirar"
            secuencia.append(("combate", enemigo, zona, tipo_ini))

        elif tirada < prob_combate + prob_evento:
            if eventos_area and random.random() < 0.6:
                ev_key = random.choice(eventos_area)
            else:
                ev_key = random.choice([
                    "cadaver_con_loot", "trampa_cazador", "piso_inestable",
                    "diario_anterior", "mensaje_radio", "sobreviviente_amigable"
                ])
            secuencia.append(("evento", ev_key, zona))

    if not secuencia:
        secuencia.append(("evento", "cadaver_con_loot", estructura[0]))

    return secuencia
