# ============================================================
# engine/autonomo.py — Motor de decisiones autónomas
#
# Implementa la heurística de supervivencia que reemplaza
# completamente la interacción del usuario. El personaje toma
# sus propias decisiones basándose en:
#   1. Su estado vital actual (hambre, sed, fatiga, salud).
#   2. La configuración de estrategia para su archetype.
#   3. Un scoring contextual de las zonas disponibles.
#   4. Ruido aleatorio calibrado para evitar comportamiento
#      determinista (simula juicio imperfecto).
#
# Principio de diseño:
#   Este módulo NO toca datos. Solo lee estado y devuelve
#   decisiones. La ejecución sigue siendo responsabilidad
#   de engine/tick.py.
# ============================================================

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from engine.constants import (
    HAMBRE_UMBRAL_CRITICO, SED_UMBRAL_CRITICO,
    SALUD_PCT_ALERTA_INICIO, SALUD_PCT_DESCANSO_MEDICINA,
    HAMBRE_UMBRAL_EMERGENCIA, SED_UMBRAL_EMERGENCIA,
)

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

# Ruido aleatorio sobre el score de zona para romper determinismo.
_RUIDO_MAX = 0.12

# Tags de zona que coinciden con necesidades del personaje.
_TAG_A_TIPO_ITEM: dict[str, str] = {
    "medico":       "medicina",
    "comida":       "comida",
    "interior":     "",
    "armas":        "arma",
    "industrial":   "material",
    "conocimiento": "libro",
    "humanitario":  "comida",
    "combustible":  "material",
}

# Penalización de peligro según estado físico del personaje.
_PENALIZACION_PELIGRO_SALUD_BAJA  = 0.6  # salud < 40%
_PENALIZACION_PELIGRO_SALUD_MEDIA = 0.85 # salud < 65%
_PENALIZACION_PELIGRO_RADIACION   = 0.7  # zona con radiación >= 2

# Umbrales de necesidad para el bonus de zona.
_HAMBRE_NECESITA_COMIDA = 50
_SED_NECESITA_AGUA      = 50
_SALUD_NECESITA_MEDICINA_PCT = 0.6


# ──────────────────────────────────────────────────────────────
#  DECISIÓN PRINCIPAL
# ──────────────────────────────────────────────────────────────

def decidir_acciones_disponibles(
    personaje: "Sobreviviente",
    opciones_zona: list[dict],
) -> list[str]:
    """
    Determina qué acciones están disponibles para el personaje
    en función de su estado y los recursos disponibles.
    """
    from engine.fuego import esta_encendido
    from engine.pesca import puede_pescar
    from engine.caza import puede_cazar
    from engine.recoleccion import puede_recolectar
    from engine.cocina import listar_items_cocinables

    acciones = []

    for zona in opciones_zona:
        if puede_pescar(personaje, zona)[0]:
            acciones.append("pescar")
            break

    for zona in opciones_zona:
        if puede_cazar(personaje, zona)[0]:
            acciones.append("cazar")
            break

    for zona in opciones_zona:
        if puede_recolectar(zona)[0]:
            acciones.append("recolectar")
            break

    if listar_items_cocinables(personaje):
        acciones.append("cocinar")

    if not esta_encendido(personaje):
        acciones.append("encender_fuego")

    acciones.append("descansar")
    return acciones


def ejecutar_accion_autonoma(
    personaje: "Sobreviviente",
    accion: str,
    opciones_zona: list[dict],
) -> str:
    """
    Ejecuta una acción autónoma y retorna un log string.
    """
    import random
    from engine.fuego import encender_fuego, esta_encendido
    from engine.pesca import intentar_pesca, puede_pescar
    from engine.caza import cazar_activo, puede_cazar
    from engine.recoleccion import recolectar, puede_recolectar
    from engine.cocina import cocinar_item, listar_items_cocinables

    if accion == "encender_fuego":
        if not esta_encendido(personaje):
            _, msg = encender_fuego(personaje)
            return f"[fuego] {msg}"

    elif accion == "pescar":
        zona_agua = next(
            (z for z in opciones_zona if puede_pescar(personaje, z)[0]),
            None,
        )
        if zona_agua:
            resultado = intentar_pesca(personaje, zona_agua, horas=2.0)
            if resultado["capturas"]:
                almacen = getattr(personaje, "almacen", [])
                almacen.extend(resultado["capturas"])
                personaje.almacen = almacen
            return f"[pesca] {resultado['mensaje']}"

    elif accion == "cazar":
        zona_caza = next(
            (z for z in opciones_zona if puede_cazar(personaje, z)[0]),
            None,
        )
        if zona_caza:
            resultado = cazar_activo(personaje, zona_caza, horas=3.0)
            if resultado["exito"]:
                almacen = getattr(personaje, "almacen", [])
                for _ in range(resultado["capturas_carne"]):
                    almacen.append({"id": "carne_animal_cruda", "nombre": "Carne de animal", "cantidad": 1})
                personaje.almacen = almacen
            return f"[caza] {resultado['mensaje']}"

    elif accion == "recolectar":
        zona_rec = next(
            (z for z in opciones_zona if puede_recolectar(z)[0]),
            None,
        )
        if zona_rec:
            resultado = recolectar(personaje, zona_rec, horas=1.5)
            if resultado["items"]:
                almacen = getattr(personaje, "almacen", [])
                almacen.extend(resultado["items"])
                personaje.almacen = almacen
            return f"[recoleccion] {resultado['mensaje']}"

    elif accion == "cocinar":
        cocinables = listar_items_cocinables(personaje)
        if cocinables:
            item_a_cocinar = random.choice(cocinables)
            resultado = cocinar_item(personaje, item_a_cocinar)
            return f"[cocina] {resultado['mensaje']}"

    return f"[{accion}] Acción no disponible."


def decidir_tick(
    personaje: "Sobreviviente",
    opciones_zona: list[dict],
    config_arch: dict,
) -> tuple[str, dict | None]:
    """
    Decide si el personaje debe descansar o ir de expedición,
    y en caso de expedición, qué zona elegir.

    Devuelve:
        ("descanso", None)
        ("expedicion", area_dict)
    """
    if _debe_descansar(personaje, config_arch):
        return ("descanso", None)

    zona_elegida = elegir_zona(personaje, opciones_zona, config_arch)
    return ("expedicion", zona_elegida)



def _debe_descansar(personaje: "Sobreviviente", config: dict) -> bool:
    """
    Evalúa si el personaje debe descansar en lugar de salir.
    Usa umbrales del archetype con ajustes por situación extrema.
    """
    umbral_fat  = config.get("umbral_descanso_fatiga",    70)
    umbral_ham  = config.get("umbral_descanso_hambre",    72)
    umbral_sed  = config.get("umbral_descanso_sed",       75)
    umbral_sal  = config.get("umbral_descanso_salud_pct", 0.35)

    salud_pct = personaje.salud / max(1, personaje.salud_max)

    # Condiciones de descanso obligatorio.
    if salud_pct < umbral_sal:
        return True
    if personaje.fatiga > umbral_fat:
        return True

    # El hambre/sed extremos pueden forzar descanso si hay comida/agua en refugio.
    if personaje.hambre > umbral_ham or personaje.sed > umbral_sed:
        tiene_comida = _tiene_item_tipo(personaje, "comida")
        tiene_agua   = _tiene_item_tipo(personaje, "agua")
        if tiene_comida or tiene_agua:
            return True

    # Racha máxima de expediciones seguidas.
    max_exp = config.get("max_expediciones_seguidas", 3)
    exps_completadas = getattr(personaje, "expediciones_completadas", 0)
    dia = getattr(personaje, "dia", 1)
    # Expediciones en el último "ciclo" = completadas sin descanso.
    # Aproximación: si el día es impar y las exps son múltiplo exacto → descansar.
    if exps_completadas > 0 and exps_completadas % max_exp == 0 and dia > 1:
        # Forzar descanso cada max_exp expediciones, con probabilidad.
        if random.random() < 0.6:
            return True

    return False


# ──────────────────────────────────────────────────────────────
#  SCORING Y SELECCIÓN DE ZONA
# ──────────────────────────────────────────────────────────────

def elegir_zona(
    personaje: "Sobreviviente",
    opciones_zona: list[dict],
    config_arch: dict,
) -> dict:
    """
    Puntúa cada zona disponible y elige la mejor con ruido aleatorio.
    El ruido evita comportamiento 100% determinista.
    """
    if not opciones_zona:
        return opciones_zona[0] if opciones_zona else {}

    scores = [
        _score_zona(personaje, zona, config_arch)
        for zona in opciones_zona
    ]
    # Softmax ligero para elegir con probabilidad proporcional al score.
    zona_elegida = _elegir_por_softmax(opciones_zona, scores)
    return zona_elegida


def _score_zona(
    personaje: "Sobreviviente",
    zona: dict,
    config: dict,
) -> float:
    """
    Calcula un score para una zona según:
    1. Peso base del archetype para esa zona.
    2. Bonus contextual por necesidades actuales del personaje.
    3. Bonus por afinidad de skills con los tags de la zona.
    4. Penalización por peligro relativo a la capacidad de combate.
    5. Penalización por radiación si el personaje tiene mucha ya.
    6. Ruido aleatorio.
    """
    area_key = zona.get("area_key", "")
    pesos_zonas = config.get("pesos_zonas", {})
    score = pesos_zonas.get(area_key, 1.0)

    # ── Bonus por necesidades vitales ─────────────────────────
    score += _bonus_necesidades(personaje, zona)

    # ── Bonus por afinidad de skills ──────────────────────────
    score += _bonus_skills(personaje, zona)

    # ── Penalización por peligro ──────────────────────────────
    score *= _factor_peligro(personaje, zona)

    # ── Penalización por radiación ────────────────────────────
    score *= _factor_radiacion(personaje, zona)

    # ── Ruido aleatorio calibrado ─────────────────────────────
    ruido = config.get("ruido_decision", _RUIDO_MAX)
    score *= random.uniform(1.0 - ruido, 1.0 + ruido)

    return max(0.001, score)


def _bonus_necesidades(personaje: "Sobreviviente", zona: dict) -> float:
    """Bonus si la zona tiene recursos que el personaje necesita ahora."""
    bonus = 0.0
    tags  = zona.get("tags", [])

    if personaje.hambre > _HAMBRE_NECESITA_COMIDA and "comida" in tags:
        bonus += 0.5 * (personaje.hambre / 100)

    if personaje.sed > _SED_NECESITA_AGUA and "agua" in tags:
        bonus += 0.4 * (personaje.sed / 100)

    salud_pct = personaje.salud / max(1, personaje.salud_max)
    if salud_pct < _SALUD_NECESITA_MEDICINA_PCT and "medico" in tags:
        bonus += 0.6 * (1 - salud_pct)

    return bonus


def _bonus_skills(personaje: "Sobreviviente", zona: dict) -> float:
    """Bonus cuando los tags de la zona coinciden con las skills fuertes del personaje."""
    tags   = zona.get("tags", [])
    skills = getattr(personaje, "skills", {})
    bonus  = 0.0

    # Mapa tag → skill que lo aprovecha mejor.
    tag_skill_map: dict[str, str] = {
        "medico":      "medicina",
        "armas":       "combate_cac",
        "industrial":  "mecanica",
        "conocimiento": "liderazgo",
        "comida":      "botanica",
        "peligroso":   "supervivencia",
        "exterior":    "supervivencia",
        "interior":    "sigilo",
        "humanitario": "persuasion",
    }

    for tag in tags:
        skill_rel = tag_skill_map.get(tag)
        if skill_rel and skill_rel in skills:
            nivel = skills[skill_rel]
            # Bonus proporcional al nivel de skill (máximo +0.5 a nivel 100).
            bonus += 0.005 * nivel

    return bonus


def _factor_peligro(personaje: "Sobreviviente", zona: dict) -> float:
    """Penaliza zonas peligrosas cuando el personaje está débil o mal armado."""
    peligro   = zona.get("peligro", 1)
    salud_pct = personaje.salud / max(1, personaje.salud_max)

    if peligro <= 2:
        return 1.0  # Zonas seguras, sin penalización.

    # Evaluar capacidad de combate.
    skills     = getattr(personaje, "skills", {})
    combate    = max(skills.get("combate_cac", 0), skills.get("combate_distancia", 0))
    tiene_arma = personaje.arma_equipada() is not None

    capacidad_combate = combate / 100.0
    if tiene_arma:
        capacidad_combate = min(1.0, capacidad_combate + 0.25)

    # A mayor peligro y menor salud/combate, mayor penalización.
    factor_base = 1.0 - (peligro - 2) * 0.08
    factor_salud = 1.0
    if salud_pct < SALUD_PCT_ALERTA_INICIO:
        factor_salud = _PENALIZACION_PELIGRO_SALUD_BAJA
    elif salud_pct < 0.65:
        factor_salud = _PENALIZACION_PELIGRO_SALUD_MEDIA

    factor_combate = 0.7 + 0.3 * capacidad_combate

    return max(0.1, factor_base * factor_salud * factor_combate)


def _factor_radiacion(personaje: "Sobreviviente", zona: dict) -> float:
    """Penaliza zonas radioactivas si el personaje ya tiene mucha radiación."""
    radiacion_zona = zona.get("radiacion", 0)
    if radiacion_zona < 1:
        return 1.0

    radiacion_actual = getattr(personaje, "radiacion", 0)
    # Si ya tiene más del 60% de radiación, evitar zonas radioactivas.
    if radiacion_actual > 60:
        return _PENALIZACION_PELIGRO_RADIACION
    if radiacion_actual > 40:
        return 0.85

    return 1.0 - radiacion_zona * 0.05  # Penalización moderada.


def _elegir_por_softmax(opciones: list[dict], scores: list[float]) -> dict:
    """
    Selecciona una opción usando distribución de probabilidad proporcional
    a los scores. Esto permite cierta variabilidad sin perder preferencia
    por la mejor opción.
    """
    total = sum(scores)
    if total <= 0:
        return random.choice(opciones)

    probs = [s / total for s in scores]
    rand = random.random()
    acum = 0.0
    for zona, prob in zip(opciones, probs):
        acum += prob
        if rand <= acum:
            return zona
    return opciones[-1]


# ──────────────────────────────────────────────────────────────
#  GESTIÓN AUTÓNOMA DE RECURSOS (consumo de ítems)
# ──────────────────────────────────────────────────────────────

# Umbrales a partir de los cuales el personaje decide consumir un ítem.
# Ordenados de emergencia → preventivo para cada vital.
_UMBRAL_COMER    = 45   # hambre > 45 → buscar comida
_UMBRAL_BEBER    = 40   # sed > 40 → buscar agua
_UMBRAL_MEDICINA = 0.60 # salud < 60% → usar botiquín/medicina
_UMBRAL_RADIACION = 35  # radiacion > 35 → usar antirradiación
_UMBRAL_FATIGA_ESTIMULANTE = 75  # fatiga > 75 → considerar estimulante

# Tipos de ítem y qué vital afectan (prioridad de búsqueda en inventario).
_TIPOS_POR_VITAL: dict[str, list[str]] = {
    "hambre":    ["comida"],
    "sed":       ["agua"],
    "salud":     ["botiquin", "medicina", "medicina_fuerte", "farmaco"],
    "radiacion": ["antirradiacion", "farmaco"],
    "fatiga":    ["estimulante", "farmaco"],
    "condicion": ["medicina", "medicina_fuerte", "farmaco", "antibiotico"],
}

def gestionar_recursos_autonomo(personaje: "Sobreviviente") -> list[str]:
    """
    Evalúa el estado vital del personaje y consume ítems del inventario
    cuando algún parámetro supera los umbrales de alerta.

    Orden de prioridad:
      1. Sed extrema (mata rápido)
      2. Hambre extrema
      3. Heridas graves (salud baja)
      4. Condiciones activas (infección, hemorragia, etc.)
      5. Radiación elevada
      6. Hambre/sed moderados (preventivo)
      7. Salud moderadamente baja
      8. Fatiga alta (estimulantes, solo si no quedan opciones de descanso)

    Devuelve lista de mensajes de log para mostrar en la consola.
    """
    msgs: list[str] = []

    # 1 — Sed extrema: prioridad absoluta.
    if personaje.sed >= SED_UMBRAL_EMERGENCIA:
        msgs += _consumir_para_vital(personaje, "sed", tipos=["agua"])

    # 2 — Hambre extrema.
    if personaje.hambre >= HAMBRE_UMBRAL_EMERGENCIA:
        msgs += _consumir_para_vital(personaje, "hambre", tipos=["comida"])

    # 3 — Heridas graves: usar medicina cuanto antes.
    salud_pct = personaje.salud / max(1, personaje.salud_max)
    if salud_pct < _UMBRAL_MEDICINA:
        msgs += _consumir_para_vital(
            personaje, "salud",
            tipos=["botiquin", "medicina", "medicina_fuerte"],
        )

    # 4 — Condiciones activas: tratar con el ítem adecuado.
    for condicion in list(personaje.condiciones):
        msgs += _tratar_condicion(personaje, condicion)

    # 5 — Radiación elevada.
    if personaje.radiacion > _UMBRAL_RADIACION:
        msgs += _consumir_para_vital(
            personaje, "radiacion",
            tipos=["antirradiacion", "farmaco"],
            efecto_clave="radiacion",
            efecto_negativo=True,
        )

    # 6 — Hambre/sed moderados (consumo preventivo).
    if personaje.hambre > _UMBRAL_COMER:
        msgs += _consumir_para_vital(personaje, "hambre", tipos=["comida"])

    if personaje.sed > _UMBRAL_BEBER:
        msgs += _consumir_para_vital(personaje, "sed", tipos=["agua"])

    # 7 — Salud moderadamente baja (uso de medicina menor).
    if salud_pct < SALUD_PCT_DESCANSO_MEDICINA and salud_pct >= _UMBRAL_MEDICINA:
        msgs += _consumir_para_vital(
            personaje, "salud",
            tipos=["medicina", "botiquin"],
        )

    # 8 — Fatiga alta: estimulante solo si hay expedición pendiente
    #     y no hay comida que pudiera ayudar.
    if personaje.fatiga > _UMBRAL_FATIGA_ESTIMULANTE:
        msgs += _consumir_para_vital(
            personaje, "fatiga",
            tipos=["estimulante"],
            efecto_clave="fatiga",
            efecto_negativo=True,
        )

    return msgs


def _consumir_para_vital(
    personaje: "Sobreviviente",
    vital: str,
    tipos: list[str],
    efecto_clave: str | None = None,
    efecto_negativo: bool = False,
) -> list[str]:
    """
    Busca en el inventario el mejor ítem para el vital indicado y lo usa.
    Solo consume un ítem por llamada para no sobremeditar.

    Parámetros:
        vital          : nombre del vital que se quiere mejorar
        tipos          : tipos de ítem a buscar (en orden de preferencia)
        efecto_clave   : si None, infiere desde el vital
        efecto_negativo: True si el efecto beneficioso es un número negativo
                         (ej: hambre=-30 reduce hambre, radiacion=-20 reduce rad)
    """
    clave = efecto_clave or vital
    item  = _mejor_item_para(personaje, tipos, clave, efecto_negativo)
    if not item:
        return []

    ok, msg = personaje.usar_item(item["nombre"], forzar_supervivencia=True)
    if ok:
        return [f"[Auto] {item['nombre']} → {msg}"]
    return []


def _mejor_item_para(
    personaje: "Sobreviviente",
    tipos: list[str],
    efecto_clave: str,
    efecto_negativo: bool,
) -> dict | None:
    """
    Devuelve el ítem del inventario con mayor efecto sobre el vital buscado.
    En caso de empate, prefiere el de menor peso (conservar capacidad de carga).
    """
    candidatos: list[tuple[float, dict]] = []

    for item in getattr(personaje, "inventario", []):
        if item.get("tipo", "") not in tipos:
            continue
        efectos = item.get("efectos", {})
        if efecto_clave not in efectos:
            # Para medicina genérica con "salud", aceptar cualquier ítem de tipo medicina.
            if efecto_clave == "salud" and item.get("tipo") in ("botiquin", "medicina", "medicina_fuerte"):
                valor = efectos.get("salud", 10)  # Valor estimado si no especifica.
            else:
                continue
        else:
            valor = efectos[efecto_clave]

        # Normaliza: queremos el mayor efecto beneficioso absoluto.
        magnitud = abs(valor) if efecto_negativo else valor
        candidatos.append((magnitud, item))

    if not candidatos:
        return None

    # Mayor magnitud de efecto; desempate por menor peso.
    return max(candidatos, key=lambda x: (x[0], -x[1].get("peso", 0)))[1]


def _tratar_condicion(personaje: "Sobreviviente", condicion) -> list[str]:
    """
    Busca en el inventario un ítem que trate la condición activa.
    Solo trata condiciones de severidad >= 2 para no malgastar medicina menor.
    """
    if getattr(condicion, "severidad", 0) < 2:
        return []

    clave_condicion = getattr(condicion, "clave", "")
    if not clave_condicion:
        return []

    # Buscar ítem con `condicion_remove` que coincida.
    for item in getattr(personaje, "inventario", []):
        efectos = item.get("efectos", {})
        if efectos.get("condicion_remove") == clave_condicion:
            ok, msg = personaje.usar_item(item["nombre"], forzar_supervivencia=True)
            if ok:
                return [f"[Auto] {item['nombre']} → tratando {clave_condicion}"]
            break

    # Fallback: medicina fuerte para condiciones graves (severidad >= 3).
    if getattr(condicion, "severidad", 0) >= 3:
        for item in getattr(personaje, "inventario", []):
            if item.get("tipo") in ("medicina_fuerte", "botiquin"):
                ok, msg = personaje.usar_item(item["nombre"], forzar_supervivencia=True)
                if ok:
                    return [f"[Auto] {item['nombre']} → emergencia médica ({clave_condicion})"]
                break

    return []


# ──────────────────────────────────────────────────────────────
#  GESTIÓN AUTÓNOMA DE INVENTARIO
# ──────────────────────────────────────────────────────────────

def gestionar_inventario_autonomo(personaje: "Sobreviviente", config: dict) -> list[str]:
    """
    Descarta ítems de bajo valor cuando el inventario está lleno.
    Prioriza conservar los tipos de ítem que el archetype necesita más.
    Devuelve mensajes de log.
    """
    msgs: list[str] = []
    if personaje.peso_actual() < personaje.peso_max * 0.85:
        return msgs  # Aún hay espacio, no descartar nada.

    prioridad = config.get("prioridad_inventario", ["agua", "comida", "medicina"])

    # Ítems candidatos a descartar (los de menor prioridad).
    candidatos_descarte = _items_baja_prioridad(personaje, prioridad)
    if candidatos_descarte:
        item_descartar = candidatos_descarte[0]
        nombre = item_descartar.get("nombre", "ítem")
        if personaje.remover_item(nombre):
            msgs.append(f"[Auto] Descartado {nombre} para liberar espacio.")

    return msgs


def _items_baja_prioridad(personaje: "Sobreviviente", prioridad: list[str]) -> list[dict]:
    """
    Devuelve ítems ordenados de menor a mayor prioridad estratégica.
    Los ítems de tipo 'libro' duplicados, materiales excesivos, etc.
    """
    inventario = getattr(personaje, "inventario", [])
    candidatos = []

    for item in inventario:
        tipo = item.get("tipo", "")
        # Nunca descartar comida, agua ni medicina básica.
        if tipo in ("comida", "agua", "medicina", "farmaco"):
            continue
        # Descartar libros ya leídos si el inventario está lleno.
        if tipo == "libro":
            candidatos.insert(0, item)  # Alta prioridad de descarte.
        elif tipo in ("material_basico",):
            candidatos.append(item)
        elif tipo not in prioridad:
            candidatos.append(item)

    return candidatos


# ──────────────────────────────────────────────────────────────
#  GESTIÓN AUTÓNOMA DEL ALMACÉN DEL REFUGIO
# ──────────────────────────────────────────────────────────────

def gestionar_recursos_almacen(personaje: "Sobreviviente") -> list[str]:
    """
    Durante el descanso en el refugio, consume directamente del almacén
    según necesidades vitales. Más agresivo que gestionar_recursos_autonomo
    porque no requiere tener el ítem en la mochila.
    """
    from engine.almacen import consumir_tipo
    msgs: list[str] = []
    almacen = getattr(personaje, "almacen", [])

    def _consumir(tipo: str, umbral: int, stat_attr: str, mejora: int, etiqueta: str) -> None:
        if getattr(personaje, stat_attr, 100) < umbral:
            items = consumir_tipo(almacen, tipo, 1)
            for item in items:
                nuevo_val = min(100, getattr(personaje, stat_attr) + mejora)
                setattr(personaje, stat_attr, nuevo_val)
                msgs.append(f"[Refugio/Auto] {item['nombre']} → {etiqueta}")

    _consumir("agua",    70, "sed",    35, "Sed reducida")
    _consumir("comida",  70, "hambre", 35, "Hambre reducida")

    if personaje.salud < 60:
        items = consumir_tipo(almacen, "medicina", 1)
        for item in items:
            personaje.salud = min(personaje.salud_max, personaje.salud + 25)
            msgs.append(f"[Refugio/Auto] {item['nombre']} → Salud recuperada")

    return msgs


def cargar_mochila_desde_almacen(personaje: "Sobreviviente") -> list[str]:
    """
    Antes de una expedición, carga la mochila con ítems del almacén
    según las necesidades vitales actuales. Solo toma lo que cabe.
    """
    from engine.almacen import transferir_al_inventario, cantidad_total_tipo
    almacen = getattr(personaje, "almacen", [])
    msgs: list[str] = []

    cargas: list[tuple[str, int]] = []
    if personaje.sed < 60:
        cargas.append(("agua",     max(1, (60 - personaje.sed)    // 20)))
    if personaje.hambre < 60:
        cargas.append(("comida",   max(1, (60 - personaje.hambre) // 20)))
    if personaje.salud < 70:
        cargas.append(("medicina", 1))
    if personaje.radiacion > 30:
        cargas.append(("antirad",  1))

    for tipo, cantidad in cargas:
        items_disponibles = [it for it in almacen if it.get("tipo") == tipo]
        for item in items_disponibles[:cantidad]:
            ok, msg = transferir_al_inventario(almacen, personaje, item["nombre"], 1)
            if ok:
                msgs.append(msg)

    return msgs


# ──────────────────────────────────────────────────────────────
#  UTILIDADES
# ──────────────────────────────────────────────────────────────

def _tiene_item_tipo(personaje: "Sobreviviente", tipo: str) -> bool:
    """Verifica si el personaje tiene algún ítem del tipo indicado en mochila o almacén."""
    en_mochila = any(
        item.get("tipo") == tipo
        for item in getattr(personaje, "inventario", [])
    )
    if en_mochila:
        return True
    almacen = getattr(personaje, "almacen", [])
    return any(it.get("tipo") == tipo for it in almacen)
