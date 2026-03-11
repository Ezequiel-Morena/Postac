# ============================================================
# engine/tick.py — Motor de tick global
#
# Cada decisión del jugador dispara un tick global que actualiza
# todos los sistemas y devuelve un ResultadoTick listo para
# ser presentado por main.py.
# ============================================================

import logging
import random
from dataclasses import dataclass, field
from pathlib     import Path

from data.items  import ITEMS
from data.skills import SKILLS
from engine.clima import aplicar_efectos_clima, clima_actual
from engine.temperatura import (
    actualizar_humedad_ropa,
    calcular_temp_corporal,
    desgastar_ropa,
    efectos_temperatura,
    evaluar_congelacion,
    impermeabilidad_total,
    temperatura_sensacion,
)
from engine.relaciones import tick_refugio
from engine.medical_system import evaluar_adquisicion_condiciones
from engine.constants import (
    HAMBRE_UMBRAL_CRITICO, SED_UMBRAL_CRITICO,
    SALUD_PCT_ALERTA_INICIO, SALUD_PCT_ABORT_EXPEDICION,
    SALUD_PCT_AUTOCONSUMO, SALUD_PCT_DESCANSO_MEDICINA,
    HAMBRE_UMBRAL_DESCANSO, SED_UMBRAL_DESCANSO,
    HAMBRE_UMBRAL_AVISO_DESCANSO, SED_UMBRAL_AVISO_DESCANSO,
    SED_UMBRAL_EMERGENCIA, HAMBRE_UMBRAL_EMERGENCIA,
    MORAL_BONUS_EXPEDICION, MORAL_BONUS_DESCANSO, MORAL_MAX,
)


@dataclass
class ResultadoTick:
    tipo:                 str       = ""
    log_terminal:         str       = ""
    log_plano:            str       = ""
    ruta_imagen:          str       = ""
    exito:                bool      = True
    personaje_vivo:       bool      = True
    causa_muerte:         str       = ""
    log_descanso:         list[str] = field(default_factory=list)
    progreso_skills:      list[str] = field(default_factory=list)
    penalizaciones_tick:  list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────
#  EXPEDICIÓN
# ──────────────────────────────────────────────────────────────

def ejecutar_expedicion(personaje, area: dict,
                         exportar_img: bool = True) -> ResultadoTick:
    from engine.bitacora  import (Bitacora, render_terminal, render_texto_plano)
    from engine.eventos   import generar_secuencia_eventos
    from engine.save_manager import siguiente_ruta_texto

    resultado = ResultadoTick(tipo="expedicion")
    resultado.penalizaciones_tick = personaje.tick_dependencias()

    bit       = Bitacora(personaje)
    clima_tick = clima_actual(personaje.dia, personaje.hora, area)

    _log_inicio_expedicion(bit, area, clima_tick, resultado.penalizaciones_tick, personaje)

    secuencia  = generar_secuencia_eventos(area, personaje)
    loot_total, exito = _procesar_secuencia_eventos(
        personaje, bit, secuencia, area, clima_tick
    )

    if exito:
        loot_total += _recolectar_loot_general(personaje, bit, area)

    _procesar_sistemas_globales(personaje, bit, area, clima_tick)
    _tick_temperatura(personaje, clima_tick, area["duracion_h"], en_refugio=False, bit=bit)
    _registrar_contadores_expedicion(personaje, area, exito)

    personaje.evaluar_rasgos_nuevos()
    resultado.progreso_skills = personaje.recoger_progreso_skills()
    bit.fin(area["nombre"], exito)

    resultado.log_terminal   = render_terminal(bit, personaje, loot_total, resultado.progreso_skills)
    resultado.log_plano      = render_texto_plano(bit, personaje, loot_total, area["nombre"], resultado.progreso_skills)
    resultado.exito          = exito
    resultado.personaje_vivo = personaje.esta_vivo()
    if not personaje.esta_vivo():
        resultado.causa_muerte = "heridas de expedición"

    from engine.save_manager import siguiente_ruta_texto
    ruta_txt = siguiente_ruta_texto(personaje.partida_id, personaje.dia)
    ruta_txt.write_text(resultado.log_plano, encoding="utf-8")
    Path("saves").mkdir(exist_ok=True)
    Path("saves/bitacora_ultima.txt").write_text(resultado.log_plano, encoding="utf-8")

    resultado.ruta_imagen = _exportar_imagen_partida(resultado.log_plano, personaje, exportar_img)
    return resultado


# ──────────────────────────────────────────────────────────────
#  DESCANSO
# ──────────────────────────────────────────────────────────────

def ejecutar_descanso(personaje) -> ResultadoTick:
    resultado = ResultadoTick(tipo="descanso")
    resultado.penalizaciones_tick = personaje.tick_dependencias()
    log = list(resultado.penalizaciones_tick)
    log += _consumo_descanso(personaje)

    fatiga_inicial = personaje.fatiga
    mult_rec = personaje.obtener_efecto_rasgo("recuperacion_descanso_mult", 1.0)
    rec_fat  = int(40 * mult_rec)
    personaje.moral  = min(MORAL_MAX, personaje.moral + MORAL_BONUS_DESCANSO)
    clima_tick = clima_actual(personaje.dia, personaje.hora, {"area_key": "refugio", "tags": ["interior"]})
    log.append(
        f"Refugio: {clima_tick['icono']} {clima_tick['nombre']} | "
        f"{clima_tick['estacion']} | {clima_tick['temperatura_c']}°C."
    )

    # Durante el descanso siguen avanzando hambre/sed/tiempo global,
    # y luego se aplica la recuperación de fatiga para que el efecto
    # de descansar sea tangible en el estado final.
    personaje.pasar_tiempo(6)
    log += aplicar_efectos_clima(personaje, 6, {"tags": ["interior", "seguro"]}, clima_tick, en_refugio=True)
    personaje.fatiga = max(0, personaje.fatiga - rec_fat)
    log += tick_refugio(personaje, 6, contexto="descanso")

    # ── Envejecimiento ────────────────────────────────────────
    for msg_edad in personaje.tick_envejecimiento():
        log.append(msg_edad)

    # Durante el descanso también pueden adquirirse condiciones (con menor prob).
    for msg_cond in evaluar_adquisicion_condiciones(personaje, clima_tick.get("clima_id", "templado"), 6, en_refugio=True):
        log.append(msg_cond)

    # Temperatura corporal (en refugio, 6 horas)
    temp_msgs = _tick_temperatura(personaje, clima_tick, 6, en_refugio=True)
    log.extend(temp_msgs)

    delta_fatiga_real = max(0, fatiga_inicial - personaje.fatiga)
    log += personaje.recoger_log_medico()
    log.append(f"Descansaste 6 horas. Fatiga -{delta_fatiga_real} (recuperación base: {rec_fat}).")
    if personaje.hambre > HAMBRE_UMBRAL_AVISO_DESCANSO: log.append("⚠ Sin comida. El hambre es crítica.")
    if personaje.sed    > SED_UMBRAL_AVISO_DESCANSO:    log.append("⚠ Sin agua. La deshidratación avanza.")

    personaje.evaluar_rasgos_nuevos()
    resultado.progreso_skills = personaje.recoger_progreso_skills()
    resultado.log_descanso    = log
    resultado.personaje_vivo  = personaje.esta_vivo()
    if not personaje.esta_vivo():
        resultado.causa_muerte = "inanición o deshidratación en refugio"
    return resultado


# ──────────────────────────────────────────────────────────────
#  UTILIDADES INTERNAS
# ──────────────────────────────────────────────────────────────

def _consumo_descanso(personaje) -> list[str]:
    msgs = []
    _consumir_si_umbral(
        personaje, msgs,
        tipo="comida",
        condicion=personaje.hambre > HAMBRE_UMBRAL_DESCANSO,
        plantilla="Comiste: {nombre}. {detalle}",
    )
    _consumir_si_umbral(
        personaje, msgs,
        tipo="agua",
        condicion=personaje.sed > SED_UMBRAL_DESCANSO,
        plantilla="Bebiste: {nombre}.",
    )
    _consumir_si_umbral(
        personaje, msgs,
        tipo="medicina",
        condicion=personaje.salud < personaje.salud_max * SALUD_PCT_DESCANSO_MEDICINA,
        plantilla="Trataste heridas: {detalle}",
    )
    return msgs


def _auto_consumir(personaje, bit) -> None:
    """Consumo de emergencia durante expedición — busca por tipo, no por nombre."""
    if _consumir_si_umbral(personaje, [], tipo="agua",
                           condicion=personaje.sed > SED_UMBRAL_EMERGENCIA):
        bit.entrada("Bebiste al vuelo. No podías más.", "aviso")
    if _consumir_si_umbral(personaje, [], tipo="comida",
                           condicion=personaje.hambre > HAMBRE_UMBRAL_EMERGENCIA):
        bit.entrada("Comiste algo al vuelo.", "aviso")

    detalle_med = _consumir_si_umbral(
        personaje, [],
        tipo="medicina",
        condicion=personaje.salud < personaje.salud_max * SALUD_PCT_AUTOCONSUMO,
        devolver_detalle=True,
    )
    if isinstance(detalle_med, str):
        bit.entrada(detalle_med, "aviso")


def _item_por_tipo(personaje, tipo: str) -> dict | None:
    return next(
        (i for i in personaje.inventario if _tipo_funcional(i) == tipo),
        None
    )


def _tipo_funcional(item: dict) -> str:
    t = item.get("tipo", "")
    if t:
        return t
    nombre = item.get("nombre", "")
    for defn in ITEMS.values():
        if defn.get("nombre") == nombre:
            return defn.get("tipo", "")
    return ""


def _exportar_imagen_partida(log_plano: str, personaje, exportar: bool) -> str:
    if not exportar:
        return ""
    from engine.bitacora      import exportar_imagen, exportar_perfil
    from engine.save_manager  import siguiente_ruta_bitacora
    ruta = siguiente_ruta_bitacora(personaje.partida_id, personaje.dia)
    try:
        resultado = exportar_imagen(log_plano, str(ruta))
        exportar_perfil(personaje, "saves/perfil.png")
        return resultado
    except Exception as e:
        logging.getLogger(__name__).warning("Imagen no generada: %s", e)
        return ""


def _consumir_si_umbral(
    personaje,
    mensajes: list[str],
    *,
    tipo: str,
    condicion: bool,
    plantilla: str = "",
    devolver_detalle: bool = False,
):
    if not condicion:
        return False

    item = _item_por_tipo(personaje, tipo)
    if not item:
        return False

    ok, detalle = personaje.usar_item(item["nombre"])
    if not ok:
        return False

    if plantilla:
        mensajes.append(plantilla.format(nombre=item["nombre"], detalle=detalle))

    if devolver_detalle:
        return f"Usé {item['nombre']} de emergencia. {detalle}"

    return True


# ──────────────────────────────────────────────────────────────
#  HELPERS DE EXPEDICIÓN (extraídos de ejecutar_expedicion para
#  mantener la función orquestadora en ~35 líneas)
# ──────────────────────────────────────────────────────────────

def _log_inicio_expedicion(bit, area: dict, clima_tick: dict,
                            penalizaciones: list[str], personaje) -> None:
    """Registra el encabezado de la expedición en la bitácora."""
    bit.entrada(
        f"Salida → {area['nombre']} (peligro {area['peligro']}/5). "
        f"ETA ~{area['duracion_h']}h."
    )
    bit.entrada(
        f"Entorno: {clima_tick['icono']} {clima_tick['nombre']} | "
        f"{clima_tick['estacion']} | {clima_tick['temperatura_c']}°C.",
        "aviso",
    )
    for msg in penalizaciones:
        bit.entrada(msg, "critico")

    if personaje.hambre > HAMBRE_UMBRAL_CRITICO:
        bit.estado_critico("hambre")
    if personaje.sed > SED_UMBRAL_CRITICO:
        bit.estado_critico("sed")
    if personaje.salud < personaje.salud_max * SALUD_PCT_ALERTA_INICIO:
        bit.estado_critico("salud_baja")


def _procesar_secuencia_eventos(personaje, bit, secuencia: list,
                                 area: dict, clima_tick: dict) -> tuple[list[dict], bool]:
    """
    Itera la secuencia de eventos de la expedición.
    Devuelve (loot_total, exito).
    """
    from engine.eventos import resolver_evento
    from engine.combate import resolver_combate

    loot_total: list[dict] = []
    exito = True
    horas_por_segmento = area["duracion_h"] / max(1, len(secuencia))

    for ev_data in secuencia:
        if not personaje.esta_vivo() or not exito:
            break

        tipo_ev = ev_data[0]
        zona    = ev_data[2]
        bit.entrada(f"Explorando: {zona.replace('_', ' ').title()}")

        if tipo_ev == "combate":
            iniciativa = ev_data[3] if len(ev_data) > 3 else "tirar"
            resultado_c = resolver_combate(personaje, ev_data[1], iniciativa)
            bit.log_combate(resultado_c)
            from engine.almacen import agregar_item as _almacen_add
            for item in resultado_c.loot_enemigo:
                _almacen_add(personaje.almacen, item)
                loot_total.append(item)
            if resultado_c.derrota:
                exito = False

        elif tipo_ev == "evento":
            resultado_e = resolver_evento(personaje, ev_data[1], area)
            bit.log_evento(resultado_e)
            from engine.almacen import agregar_item as _almacen_add
            for item in resultado_e.items_obtenidos:
                _almacen_add(personaje.almacen, item)
                loot_total.append(item)
                personaje.items_recolectados += 1
            if resultado_e.info_obtenida:
                personaje.info_areas[area["area_key"]] = {
                    "conocido": True, "detalle": "Zona explorada previamente"
                }

        personaje.pasar_tiempo(horas_por_segmento)
        for msg in aplicar_efectos_clima(personaje, horas_por_segmento, area, clima_tick, en_refugio=False):
            bit.entrada(msg, "aviso")
        for msg in personaje.recoger_log_medico():
            bit.entrada(msg, "aviso")
        _auto_consumir(personaje, bit)

        if personaje.salud < personaje.salud_max * SALUD_PCT_ABORT_EXPEDICION:
            bit.entrada("¡Salud crítica! Aborto la expedición.", "critico")
            exito = False

    return loot_total, exito


def _recolectar_loot_general(personaje, bit, area: dict) -> list[dict]:
    """Genera y registra el loot base del área — va directo al almacén del refugio."""
    from engine.mundo import generar_loot_area
    from engine.almacen import agregar_item as _almacen_add
    loot: list[dict] = []
    loot_base = generar_loot_area(area, personaje)
    bit.log_loot(loot_base)
    for item in loot_base:
        _almacen_add(personaje.almacen, item)
        loot.append(item)
        personaje.items_recolectados += 1
    return loot


def _procesar_sistemas_globales(personaje, bit, area: dict, clima_tick: dict) -> None:
    """Actualiza refugio, animales, envejecimiento y condiciones al final del tick."""
    from engine.animales import evaluar_encuentro_animal, integrar_animal
    from engine.constants import MAX_ANIMALES_REFUGIO

    for evento_refugio in tick_refugio(personaje, area["duracion_h"], contexto="expedicion"):
        bit.entrada(evento_refugio, "aviso")

    animal = evaluar_encuentro_animal(personaje, area, f"{personaje.dia}:{personaje.hora}")
    if animal and len(personaje.animales_refugio) < MAX_ANIMALES_REFUGIO:
        bit.entrada(integrar_animal(personaje, animal), "aviso")

    for msg in personaje.tick_envejecimiento():
        tipo = "aviso" if "🎂" in msg else "critico"
        bit.entrada(msg, tipo)

    clima_id = clima_tick.get("clima_id", "templado")
    for msg in evaluar_adquisicion_condiciones(personaje, clima_id, area["duracion_h"], en_refugio=False):
        bit.entrada(msg, "critico")


def _registrar_contadores_expedicion(personaje, area: dict, exito: bool) -> None:
    """Actualiza contadores de partida y moral al finalizar la expedición."""
    if area["area_key"] not in personaje.areas_visitadas:
        personaje.areas_visitadas.append(area["area_key"])
    if exito:
        personaje.expediciones_completadas += 1
        personaje.moral = min(MORAL_MAX, personaje.moral + MORAL_BONUS_EXPEDICION)
    if not (6 <= personaje.hora <= 20):
        personaje.expediciones_nocturnas += 1


# ── SISTEMA DE TEMPERATURA ──────────────────────────────────

def _tick_temperatura(personaje, clima_tick: dict, horas: float,
                      en_refugio: bool, bit=None) -> list[str]:
    """Procesa temperatura corporal, humedad de ropa, desgaste y congelación.

    Se invoca tanto en expedición como en descanso.
    """
    from engine.constants import clamp

    msgs: list[str] = []
    clima_id = clima_tick.get("clima_id", "templado")
    temp_amb = float(clima_tick.get("temperatura_c", 18))
    viento = float(clima_tick.get("viento_kmh", 8))
    humedad = float(clima_tick.get("humedad_rel", 45))

    ropa = getattr(personaje, "ropa_equipada", {})

    # 1. Actualizar humedad de la ropa
    imp = impermeabilidad_total(ropa)
    personaje.humedad_ropa = actualizar_humedad_ropa(
        getattr(personaje, "humedad_ropa", 0.0),
        clima_id, imp, en_refugio,
        getattr(personaje, "fuego_activo", False),
        horas,
    )

    # 2. Calcular temperatura corporal
    mult_resist = personaje.obtener_efecto_rasgo("resistencia_termica_mult", 1.0)
    nueva_temp, temp_msgs = calcular_temp_corporal(
        temp_actual=getattr(personaje, "temp_corporal", 36.5),
        temp_ambiente=temp_amb,
        viento_kmh=viento,
        humedad_rel=humedad,
        ropa_equipada=ropa,
        humedad_ropa=personaje.humedad_ropa,
        fuego_activo=getattr(personaje, "fuego_activo", False),
        en_refugio=en_refugio,
        horas=horas,
        mult_resistencia=mult_resist,
    )
    personaje.temp_corporal = nueva_temp
    msgs.extend(temp_msgs)

    # 3. Aplicar efectos de temperatura sobre stats
    efx = efectos_temperatura(personaje.temp_corporal, horas)
    if efx:
        for stat, delta in efx.items():
            if stat == "salud":
                personaje.salud = max(0, personaje.salud + delta)
            elif stat == "fatiga":
                personaje.fatiga = clamp(personaje.fatiga + delta)
            elif stat == "hambre":
                personaje.hambre = clamp(personaje.hambre + delta)
            elif stat == "sed":
                personaje.sed = clamp(personaje.sed + delta)
            elif stat == "moral":
                personaje.moral = clamp(personaje.moral + delta)

    # 4. Evaluar congelación en extremidades
    t_sens = temperatura_sensacion(temp_amb, viento, humedad)
    personaje.horas_exposicion_frio, frost_msgs = evaluar_congelacion(
        t_sens, ropa,
        horas,
        getattr(personaje, "horas_exposicion_frio", 0.0),
    )
    msgs.extend(frost_msgs)

    # 5. Desgaste de ropa
    desgaste_msgs = desgastar_ropa(ropa, horas, not en_refugio, clima_id)
    msgs.extend(desgaste_msgs)

    # Registrar en bitácora si existe
    if bit:
        for m in msgs:
            tipo = "critico" if "☠" in m or "severa" in m else "aviso"
            bit.entrada(m, tipo)

    return msgs
