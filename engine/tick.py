# ============================================================
# engine/tick.py — Motor de tick global
#
# Cada decisión del jugador dispara un tick global que actualiza
# todos los sistemas y devuelve un ResultadoTick listo para
# ser presentado por main.py.
# ============================================================

import random
from dataclasses import dataclass, field
from pathlib     import Path

from data.items  import ITEMS
from data.skills import SKILLS


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
    from engine.bitacora  import (Bitacora, render_terminal, render_texto_plano,
                                   exportar_imagen, exportar_perfil)
    from engine.mundo     import generar_loot_area
    from engine.eventos   import resolver_evento, generar_secuencia_eventos
    from engine.combate   import resolver_combate
    from engine.save_manager import siguiente_ruta_bitacora, siguiente_ruta_texto

    resultado = ResultadoTick(tipo="expedicion")
    resultado.penalizaciones_tick = personaje.tick_dependencias()

    bit        = Bitacora(personaje)
    loot_total: list[dict] = []
    exito       = True

    bit.entrada(
        f"Salida → {area['nombre']} (peligro {area['peligro']}/5). "
        f"ETA ~{area['duracion_h']}h."
    )
    for msg in resultado.penalizaciones_tick:
        bit.entrada(msg, "critico")

    if personaje.hambre > 70: bit.estado_critico("hambre")
    if personaje.sed    > 70: bit.estado_critico("sed")
    if personaje.salud < personaje.salud_max * 0.4: bit.estado_critico("salud_baja")

    # ── Secuencia de eventos ──────────────────────────────────
    secuencia = generar_secuencia_eventos(area, personaje)
    for ev_data in secuencia:
        if not personaje.esta_vivo() or not exito:
            break
        tipo_ev = ev_data[0]
        zona    = ev_data[2]
        bit.entrada(f"Explorando: {zona.replace('_', ' ').title()}")

        if tipo_ev == "combate":
            iniciativa = ev_data[3] if len(ev_data) > 3 else "tirar"
            r_c = resolver_combate(personaje, ev_data[1], iniciativa)
            bit.log_combate(r_c)
            for item in r_c.loot_enemigo:
                if personaje.añadir_item(item):
                    loot_total.append(item)
            if r_c.derrota:
                exito = False

        elif tipo_ev == "evento":
            r_e = resolver_evento(personaje, ev_data[1], area)
            bit.log_evento(r_e)
            for item in r_e.items_obtenidos:
                if personaje.añadir_item(item):
                    loot_total.append(item)
                    personaje.items_recolectados += 1
            if r_e.info_obtenida:
                personaje.info_areas[area["area_key"]] = {
                    "conocido": True, "detalle": "Zona explorada previamente"
                }

        horas_zona = area["duracion_h"] / max(1, len(secuencia))
        personaje.pasar_tiempo(horas_zona)
        _auto_consumir(personaje, bit)

        if personaje.salud < personaje.salud_max * 0.15:
            bit.entrada("¡Salud crítica! Aborto la expedición.", "critico")
            exito = False

    # ── Loot general ─────────────────────────────────────────
    if exito:
        loot_base = generar_loot_area(area, personaje)
        bit.log_loot(loot_base)
        for item in loot_base:
            if personaje.añadir_item(item):
                loot_total.append(item)
                personaje.items_recolectados += 1

    bit.fin(area["nombre"], exito)

    if area["area_key"] not in personaje.areas_visitadas:
        personaje.areas_visitadas.append(area["area_key"])
    if exito:
        personaje.expediciones_completadas += 1
        personaje.moral = min(100, personaje.moral + 5)
    if not (6 <= personaje.hora <= 20):
        personaje.expediciones_nocturnas += 1

    personaje.evaluar_rasgos_nuevos()
    resultado.progreso_skills = personaje.recoger_progreso_skills()

    # ── Render ───────────────────────────────────────────────
    resultado.log_terminal = render_terminal(bit, personaje, loot_total,
                                              resultado.progreso_skills)
    resultado.log_plano    = render_texto_plano(bit, personaje, loot_total,
                                                 area["nombre"],
                                                 resultado.progreso_skills)
    resultado.exito        = exito
    resultado.personaje_vivo = personaje.esta_vivo()
    if not personaje.esta_vivo():
        resultado.causa_muerte = "heridas de expedición"

    # ── Guardar texto en directorio de la partida ─────────────
    ruta_txt = siguiente_ruta_texto(personaje.partida_id, personaje.dia)
    ruta_txt.write_text(resultado.log_plano, encoding="utf-8")

    # Copia de conveniencia (última bitácora siempre accesible)
    Path("saves").mkdir(exist_ok=True)
    Path("saves/bitacora_ultima.txt").write_text(resultado.log_plano, encoding="utf-8")

    # ── Imagen ───────────────────────────────────────────────
    resultado.ruta_imagen = _exportar_imagen_partida(
        resultado.log_plano, personaje, exportar_img
    )
    return resultado


# ──────────────────────────────────────────────────────────────
#  DESCANSO
# ──────────────────────────────────────────────────────────────

def ejecutar_descanso(personaje) -> ResultadoTick:
    resultado = ResultadoTick(tipo="descanso")
    resultado.penalizaciones_tick = personaje.tick_dependencias()
    log = list(resultado.penalizaciones_tick)
    log += _consumo_descanso(personaje)

    mult_rec = personaje.obtener_efecto_rasgo("recuperacion_descanso_mult", 1.0)
    rec_fat  = int(40 * mult_rec)
    personaje.fatiga = max(0, personaje.fatiga - rec_fat)
    personaje.moral  = min(100, personaje.moral + 5)
    personaje.pasar_tiempo(6)
    log.append(f"Descansaste 6 horas. Fatiga -{rec_fat}.")
    if personaje.hambre > 75: log.append("⚠ Sin comida. El hambre es crítica.")
    if personaje.sed    > 75: log.append("⚠ Sin agua. La deshidratación avanza.")

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
    if personaje.hambre > 40:
        item = _item_por_tipo(personaje, "comida")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok: msgs.append(f"Comiste: {item['nombre']}. {msg}")
    if personaje.sed > 30:
        item = _item_por_tipo(personaje, "agua")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok: msgs.append(f"Bebiste: {item['nombre']}.")
    if personaje.salud < personaje.salud_max * 0.7:
        item = _item_por_tipo(personaje, "medicina")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok: msgs.append(f"Trataste heridas: {msg}")
    return msgs


def _auto_consumir(personaje, bit) -> None:
    """Consumo de emergencia durante expedición — busca por tipo, no por nombre."""
    if personaje.sed > 85:
        item = _item_por_tipo(personaje, "agua")
        if item:
            ok, _ = personaje.usar_item(item["nombre"])
            if ok: bit.entrada("Bebiste al vuelo. No podías más.", "aviso")
    if personaje.hambre > 90:
        item = _item_por_tipo(personaje, "comida")
        if item:
            ok, _ = personaje.usar_item(item["nombre"])
            if ok: bit.entrada("Comiste algo al vuelo.", "aviso")
    if personaje.salud < personaje.salud_max * 0.30:
        item = _item_por_tipo(personaje, "medicina")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok: bit.entrada(f"Usé {item['nombre']} de emergencia. {msg}", "aviso")


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
        print(f"  [TICK] Imagen no generada: {e}")
        return ""
