# ============================================================
# engine/eventos.py — Resolución de eventos
# Lee eventos desde data/eventos.py, sin datos hardcodeados.
# ============================================================
import random
import copy
from data.eventos  import EVENTOS
from data.items    import ITEMS
from data.loot     import LOOT_POOLS
from data.skills   import SKILLS
from engine.personaje import Condicion
from engine.combate   import resolver_combate
from engine.relaciones import generar_superviviente_aleatorio, integrar_nuevo_miembro
from engine.constants import clamp


class ResultadoEvento:
    def __init__(self):
        self.tipo             = ""
        self.titulo           = ""
        self.log:             list[str]  = []
        self.items_obtenidos: list[dict] = []
        self.daño_recibido    = 0
        self.moral_cambio     = 0
        self.info_obtenida    = {}
        self.combate          = None

    def añadir(self, linea: str):
        self.log.append(linea)


# ──────────────────────────────────────────────────────────────
#  REGISTRY DE RESOLVERS — Open/Closed: agregar tipos sin
#  modificar el dispatcher. Mapea tipo_evento → función resolver.
# ──────────────────────────────────────────────────────────────

# Los tipos que comparten resolver se registran por separado para
# mantener el mapeo explícito y evitar lógica dentro del registry.
_RESOLVERS: dict = {}  # poblado después de definir las funciones


def _registrar_resolver(tipos: list[str], fn):
    """Registra una función resolver para uno o más tipos de evento."""
    for tipo in tipos:
        _RESOLVERS[tipo] = fn


# ──────────────────────────────────────────────────────────────
#  DISPATCHER PRINCIPAL
# ──────────────────────────────────────────────────────────────

def resolver_evento(personaje, evento_key: str, area: dict) -> ResultadoEvento:
    if evento_key not in EVENTOS:
        return _evento_generico(personaje, area)

    tmpl = EVENTOS[evento_key]
    resultado    = ResultadoEvento()
    resultado.tipo   = tmpl["tipo"]
    resultado.titulo = tmpl["titulo"]
    resultado.añadir(f"  📍 {tmpl['titulo'].upper()}")
    resultado.añadir(f"  {tmpl['descripcion']}")

    resolver_fn = _RESOLVERS.get(tmpl["tipo"])
    if resolver_fn:
        resolver_fn(resultado, personaje, tmpl, area)

    if resultado.moral_cambio != 0:
        personaje.moral = clamp(personaje.moral + resultado.moral_cambio)

    return resultado


# ──────────────────────────────────────────────────────────────
#  UTILIDAD — XP de skills en eventos
# ──────────────────────────────────────────────────────────────

def _dar_xp_skill(personaje, skill_key: str) -> None:
    """
    Otorga XP por usar una skill en un evento exitoso.
    La cantidad viene del campo xp_por_uso definido en data/skills.py.
    El XP se acumula y se muestra al final del tick en PROGRESO.
    """
    xp = SKILLS.get(skill_key, {}).get("xp_por_uso", 1)
    personaje.ganar_xp_skill(skill_key, xp)


# ──────────────────────────────────────────────────────────────
#  RESOLVERS POR TIPO
# ──────────────────────────────────────────────────────────────

def _resolver_combate_directo(r, personaje, tmpl, area=None):
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
        skill = opcion.get("skill", "sigilo")
        dif   = opcion.get("dificultad", 50)
        # Tags del área para contexto (interior, exterior)
        contexto = "interior" if area.get("interior", False) else ""
        if personaje.check_skill(skill, dif, contexto=contexto):
            _dar_xp_skill(personaje, skill)
            r.añadir("  Te ocultas perfectamente. Pasan sin verte.")
        else:
            r.añadir("  No pudiste ocultarte. ¡Te descubren!")
            resultado_c = resolver_combate(personaje, tmpl["enemigo"])
            r.combate = resultado_c
            for l in resultado_c.log:
                r.añadir(l)
            r.daño_recibido = resultado_c.daño_recibido

    elif opcion_key == "combate":
        bonus       = opcion.get("bonus_ataque", 0)
        resultado_c = resolver_combate(personaje, tmpl["enemigo"],
                                       "jugador", bonus_ataque=bonus)
        r.combate = resultado_c
        for l in resultado_c.log:
            r.añadir(l)
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

    exito    = False
    skill    = opcion.get("skill")
    stat     = opcion.get("stat")
    contexto = "interior" if area.get("interior", False) else ""

    if skill:
        exito = personaje.check_skill(skill, opcion.get("dificultad", 50),
                                      contexto=contexto)
    elif stat:
        exito = personaje.check_stat(stat, opcion.get("dificultad", 5))

    if exito:
        r.añadir("  ¡Éxito!")
        if skill:
            _dar_xp_skill(personaje, skill)
        for key in opcion.get("loot_exito", []):
            if key in ITEMS and random.random() < 0.7:
                r.items_obtenidos.append(copy.deepcopy(ITEMS[key]))
    else:
        r.añadir("  Fallaste.")
        if opcion.get("ruido_fallo") and random.random() < 0.40:
            r.añadir("  El ruido atrae a un infectado...")
            resultado_c = resolver_combate(personaje, "infectado_lento")
            r.combate = resultado_c
            for l in resultado_c.log:
                r.añadir(l)
            r.daño_recibido = resultado_c.daño_recibido


def _resolver_npc_amigable(r, personaje, tmpl, area=None):
    opciones   = tmpl.get("opciones", {})
    opcion_key = _ia_elegir_npc(personaje, opciones)
    opcion     = opciones[opcion_key]
    r.añadir(f"\n  → Decisión: {opcion['texto']}")

    costo      = opcion.get("costo", {})
    recompensa = opcion.get("recompensa", {})

    # Aplicar costos buscando por tipo en el inventario
    if costo.get("comida"):
        for nombre in ["Lata de frijoles", "Lata de atún", "Barrita energética"]:
            if personaje.remover_item(nombre):
                break
    if costo.get("agua"):
        personaje.remover_item("Botella de agua")

    r.moral_cambio = opcion.get("moral_bonus", 0) - opcion.get("moral_costo", 0)

    # Unirse al refugio si la opción lo indica y el evento lo permite.
    if opcion.get("une_al_refugio") and tmpl.get("puede_unirse"):
        seed = f"{getattr(personaje, 'partida_id', '0')}:{getattr(personaje, 'dia', 0)}:{opcion_key}"
        perfil = generar_superviviente_aleatorio(seed, personaje)
        if perfil:
            msg = integrar_nuevo_miembro(personaje, perfil)
            r.añadir(f"  {msg}")
            personaje.moral = min(100, personaje.moral + 5)

    if recompensa.get("info_zona"):
        r.info_obtenida["info_zona"] = True
        r.añadir("  Compartió información valiosa sobre la zona.")

    if recompensa.get("loot_pool"):
        pool = LOOT_POOLS.get(recompensa["loot_pool"], [])
        if random.random() < float(recompensa.get("prob", 0.5)):
            item_key = random.choice([k for k in pool if k is not None] or [None])
            if item_key and item_key in ITEMS:
                r.items_obtenidos.append(copy.deepcopy(ITEMS[item_key]))

    if opcion.get("skill") == "persuasion":
        _dar_xp_skill(personaje, "persuasion")

    for key in recompensa.get("items", []):
        if key in ITEMS:
            r.items_obtenidos.append(copy.deepcopy(ITEMS[key]))


def _resolver_npc_dilema(r, personaje, tmpl, area=None):
    opciones   = tmpl.get("opciones", {})
    opcion_key = _ia_elegir_npc(personaje, opciones)
    opcion     = opciones[opcion_key]
    r.añadir(f"\n  → Decisión: {opcion['texto']}")

    costo = opcion.get("costo", {})

    # Costos.
    if costo.get("comida"):
        for nombre in ["Lata de frijoles", "Lata de atún", "Barrita energética"]:
            if personaje.remover_item(nombre):
                break
    if costo.get("agua"):
        personaje.remover_item("Botella de agua")
    if costo.get("medicina"):
        for nombre in ["Botiquín", "Antiséptico", "Venda"]:
            if personaje.remover_item(nombre):
                break

    r.moral_cambio = opcion.get("moral_bonus", 0) - opcion.get("moral_costo", 0)

    # Unirse al refugio.
    if opcion.get("une_al_refugio") and tmpl.get("puede_unirse"):
        seed = f"{getattr(personaje, 'partida_id', '0')}:{getattr(personaje, 'dia', 0)}:{opcion_key}"
        perfil = generar_superviviente_aleatorio(seed, personaje)
        if perfil:
            msg = integrar_nuevo_miembro(personaje, perfil)
            r.añadir(f"  {msg}")
            personaje.moral = min(100, personaje.moral + 5)

    if opcion.get("combate_forzado"):
        resultado_c = resolver_combate(personaje, tmpl.get("enemigo", "bandido"))
        r.combate = resultado_c
        for l in resultado_c.log:
            r.añadir(l)
        r.daño_recibido = resultado_c.daño_recibido
        r.items_obtenidos.extend(resultado_c.loot_enemigo)

    for key in opcion.get("recompensa_items", []):
        if key in ITEMS:
            r.items_obtenidos.append(copy.deepcopy(ITEMS[key]))


def _resolver_npc_especial(r, personaje, tmpl, area=None):
    """Comerciante u otro NPC único — lógica de intercambio básica."""
    r.añadir("  El encuentro fue breve pero quizás útil.")
    for key in tmpl.get("items_disponibles", [])[:2]:
        if key in ITEMS and random.random() < 0.3:
            r.items_obtenidos.append(copy.deepcopy(ITEMS[key]))


def _resolver_peligro_ambiental(r, personaje, tmpl, area=None):
    dif    = tmpl.get("dificultad", 4)
    stat   = tmpl.get("stat_check", "destreza")
    evita  = personaje.check_stat(stat, dif)

    if evita:
        r.añadir("  Reaccionas a tiempo. Sin daño.")
    else:
        rango_daño = tmpl.get("daño", (5, 15))
        real = personaje.recibir_daño(random.randint(*rango_daño))
        r.daño_recibido = real
        r.añadir(f"  Sin tiempo de reaccionar. -{real} hp.")
        _aplicar_condicion_desde_template(r, personaje, tmpl)


def _resolver_peligro_oculto(r, personaje, tmpl, area=None):
    dif   = tmpl.get("percepcion_evitar", 5)
    evita = personaje.check_stat("percepcion", dif)

    if evita:
        r.añadir("  Tu percepción te alerta a tiempo. Rodeas la trampa.")
    else:
        rango_daño = tmpl.get("daño", (5, 15))
        real = personaje.recibir_daño(random.randint(*rango_daño))
        r.daño_recibido = real
        r.añadir(f"  ¡Trampa activada! -{real} hp.")
        _aplicar_condicion_desde_template(r, personaje, tmpl)


def _aplicar_condicion_desde_template(r, personaje, tmpl) -> None:
    """Aplica una condición configurada por datos para peligros/eventos."""
    if not tmpl.get("condicion_aplica"):
        return

    prob = float(tmpl.get("condicion_prob", 1.0))
    if random.random() > max(0.0, min(1.0, prob)):
        return

    clave = tmpl.get("condicion_clave", tmpl.get("condicion_aplica", "herida_generica"))
    nombre = tmpl.get("condicion_nombre", clave.replace("_", " ").title())
    severidad = int(tmpl.get("condicion_severidad", 2))
    duracion = int(tmpl.get("condicion_duracion", 8))
    efectos = dict(tmpl.get("condicion_efectos", {"stats_global": -1}))
    descripcion = tmpl.get("condicion_descripcion", "")

    c = Condicion(clave, nombre, severidad, duracion, efectos, descripcion)
    personaje.añadir_condicion(c)

    msg = tmpl.get("condicion_mensaje")
    if msg:
        r.añadir(msg)
    else:
        r.añadir(f"  Sufres condición: {nombre}.")


def _resolver_ambiental_forzado(r, personaje, tmpl, area=None):
    prot_item  = tmpl.get("proteccion_item", "")
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


def _resolver_ambiental_acumulativo(r, personaje, tmpl, area=None):
    prot_item  = tmpl.get("proteccion_item", "")
    tiene_prot = personaje.tiene_item(prot_item) if prot_item else False

    rad = (tmpl.get("radiacion_protegido", 5)
           if tiene_prot else tmpl.get("radiacion_normal", 15))
    personaje.radiacion = min(100, personaje.radiacion + rad)
    r.añadir(f"  +{rad} radiación absorbida. Total: {personaje.radiacion}/100 ☢")


def _resolver_narrativo(r, personaje, tmpl, area=None):
    r.moral_cambio = tmpl.get("moral_bonus", 0) - tmpl.get("moral_costo", 0)
    if tmpl.get("info_zona"):
        r.info_obtenida["info_zona"] = True
    for key in tmpl.get("loot", []):
        if key in ITEMS:
            r.items_obtenidos.append(copy.deepcopy(ITEMS[key]))


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
#  IA HEURÍSTICA — TOMA DE DECISIONES AUTÓNOMA
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
        p         = 50
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
    from data.areas import AREAS
    secuencia = []
    area_def  = AREAS.get(area.get("area_key", ""), area)
    zonas     = area_def.get("zonas", ["entrada", "interior", "salida"])
    eventos_pool = area_def.get("eventos", [])
    enemigos_pool = area_def.get("enemigos", [])

    for zona in zonas:
        # Probabilidad de evento o combate por zona
        if random.random() < area.get("peligro", 2) / 10:
            if enemigos_pool and random.random() < 0.5:
                key = random.choice(enemigos_pool)
                secuencia.append(("combate", key, zona, "tirar"))
            elif eventos_pool:
                key = random.choice(eventos_pool)
                secuencia.append(("evento", key, zona))
        else:
            # Evento narrativo / hallazgo menor con baja probabilidad
            if eventos_pool and random.random() < 0.4:
                key = random.choice(eventos_pool)
                secuencia.append(("evento", key, zona))

    return secuencia


# ──────────────────────────────────────────────────────────────
#  REGISTRO TARDÍO — las funciones deben estar definidas antes
#  de registrarlas; este bloque va siempre al final del módulo.
#  Para añadir un tipo nuevo: definir su función _resolver_X()
#  y añadir _registrar_resolver(["nuevo_tipo"], _resolver_X)
#  sin tocar resolver_evento().
# ──────────────────────────────────────────────────────────────

_registrar_resolver(["combate"],                          _resolver_combate_directo)
_registrar_resolver(["combate_evadible"],                 _resolver_combate_evadible)
_registrar_resolver(["hallazgo", "hallazgo_especial"],    _resolver_hallazgo)
_registrar_resolver(["interaccion"],                      _resolver_interaccion)
_registrar_resolver(["npc_amigable"],                     _resolver_npc_amigable)
_registrar_resolver(["npc_dilema"],                       _resolver_npc_dilema)
_registrar_resolver(["npc_especial"],                     _resolver_npc_especial)
_registrar_resolver(["peligro_ambiental"],                _resolver_peligro_ambiental)
_registrar_resolver(["ambiental_forzado"],                _resolver_ambiental_forzado)
_registrar_resolver(["ambiental_acumulativo"],            _resolver_ambiental_acumulativo)
_registrar_resolver(["narrativo", "narrativo_especial"],  _resolver_narrativo)
_registrar_resolver(["peligro_oculto"],                   _resolver_peligro_oculto)
