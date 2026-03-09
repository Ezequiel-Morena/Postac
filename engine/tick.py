# ============================================================
# engine/tick.py — Motor de tick global
#
# Un tick = una decisión del jugador (expedición o descanso).
# Responsabilidad única: ejecutar la simulación de un tick
# y devolver su resultado encapsulado en ResultadoTick.
# No imprime nada. No sabe nada de colores ni terminal.
#
# Punto de extensión para sistemas futuros:
#   Cuando lleguen clima, NPCs, familia — cada uno tendrá su
#   función tick_X() y sus resultados se agregarán al
#   ResultadoTick. main.py nunca necesitará saber de ellos.
#
#   Ejemplo futuro:
#     resultado.eventos_refugio = tick_refugio(personaje, mundo)
#     resultado.evento_clima    = tick_clima(mundo)
# ============================================================
from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from data.items import ITEMS


# ══════════════════════════════════════════════════════════════
#  RESULTADO DE TICK
# ══════════════════════════════════════════════════════════════

@dataclass
class ResultadoTick:
    """
    Encapsula todo lo que ocurrió durante un tick de simulación.

    main.py recibe este objeto y se ocupa exclusivamente de
    presentarlo al jugador. La lógica de qué pasó vive aquí;
    la lógica de cómo mostrarlo vive en main.py.
    """
    tipo: str                       # "expedicion" | "descanso"
    log_terminal: str = ""          # texto ANSI para mostrar en terminal
    log_plano: str = ""             # texto sin colores (para disco / bot)
    ruta_imagen: str = ""           # path al PNG, o "" si no se generó
    exito: bool = True              # False si la expedición fue abortada
    personaje_vivo: bool = True     # False si murió durante el tick
    causa_muerte: str = ""          # descripción de causa, "" si sobrevivió
    log_descanso: list[str] = field(default_factory=list)  # líneas del descanso


# ══════════════════════════════════════════════════════════════
#  TICK DE EXPEDICIÓN
# ══════════════════════════════════════════════════════════════

def ejecutar_expedicion(personaje, area: dict,
                         exportar_img: bool = True) -> ResultadoTick:
    """
    Ejecuta un tick completo de expedición.

    Recorre la secuencia de eventos del área, aplica combates,
    loot y efectos sobre el personaje, y devuelve un ResultadoTick
    con todo lo ocurrido.
    """
    from engine.bitacora import (Bitacora, render_terminal,
                                  render_texto_plano, exportar_imagen,
                                  exportar_perfil)
    from engine.mundo    import generar_loot_area
    from engine.eventos  import resolver_evento, generar_secuencia_eventos
    from engine.combate  import resolver_combate

    bit        = Bitacora(personaje)
    loot_total: list[dict] = []
    exito      = True

    bit.entrada(
        f"Salida → {area['nombre']} (peligro {area['peligro']}/5). "
        f"ETA ~{area['duracion_h']}h."
    )

    # Advertencias pre-expedición según el estado actual del personaje
    if personaje.hambre > 70: bit.estado_critico("hambre")
    if personaje.sed    > 70: bit.estado_critico("sed")
    if personaje.salud  < personaje.salud_max * 0.4:
        bit.estado_critico("salud_baja")

    secuencia = generar_secuencia_eventos(area, personaje)

    for ev_data in secuencia:
        if not personaje.esta_vivo() or not exito:
            break

        tipo_ev = ev_data[0]
        zona    = ev_data[2]
        bit.entrada(f"Explorando: {zona.replace('_', ' ').title()}")

        if tipo_ev == "combate":
            enemigo_key = ev_data[1]
            iniciativa  = ev_data[3] if len(ev_data) > 3 else "tirar"
            r_c = resolver_combate(personaje, enemigo_key, iniciativa)
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

        # El tiempo avanza proporcionalmente por zona recorrida
        horas_zona = area["duracion_h"] / max(1, len(secuencia))
        personaje.pasar_tiempo(horas_zona)
        _auto_consumir(personaje, bit)

        # Abortar si la salud cae a niveles incompatibles con la supervivencia
        if personaje.salud < personaje.salud_max * 0.15:
            bit.entrada("¡Salud crítica! Aborto la expedición.", "critico")
            exito = False

    # Loot general del área, sólo si la expedición se completó
    if exito:
        loot_base = generar_loot_area(area, personaje)
        bit.log_loot(loot_base)
        for item in loot_base:
            if personaje.añadir_item(item):
                loot_total.append(item)
                personaje.items_recolectados += 1

    bit.fin(area["nombre"], exito)

    # Actualizar contadores del personaje
    if area["area_key"] not in personaje.areas_visitadas:
        personaje.areas_visitadas.append(area["area_key"])
    if exito:
        personaje.expediciones_completadas += 1
        personaje.moral = min(100, personaje.moral + 5)

    # Renderizar registros
    log_term  = render_terminal(bit, personaje, loot_total)
    log_plano = render_texto_plano(bit, personaje, loot_total, area["nombre"])

    Path("saves").mkdir(exist_ok=True)
    with open("saves/bitacora_ultima.txt", "w", encoding="utf-8") as f:
        f.write(log_plano)

    ruta_img = _exportar_imagenes(log_plano, personaje, exportar_img)

    return ResultadoTick(
        tipo="expedicion",
        log_terminal=log_term,
        log_plano=log_plano,
        ruta_imagen=ruta_img,
        exito=exito,
        personaje_vivo=personaje.esta_vivo(),
        causa_muerte="heridas de expedición" if not personaje.esta_vivo() else "",
    )


# ══════════════════════════════════════════════════════════════
#  TICK DE DESCANSO
# ══════════════════════════════════════════════════════════════

# Umbrales que disparan el consumo automático de recursos
_UMBRAL_HAMBRE       = 30     # hambre > N → buscar comida
_UMBRAL_SED          = 30     # sed > N → buscar agua
_UMBRAL_CURAR        = 0.70   # salud < N% del máximo → usar medicina
_HORAS_DESCANSO      = 6


def ejecutar_descanso(personaje) -> ResultadoTick:
    """
    Ejecuta un tick de descanso en el refugio.

    Consume recursos por tipo (data-driven), nunca por nombre
    hardcodeado. Cualquier ítem con tipo "comida", "agua" o
    "medicina" añadido en el futuro funcionará automáticamente.
    """
    log: list[str] = []

    # Comer si hay necesidad y hay comida disponible
    if personaje.hambre > _UMBRAL_HAMBRE:
        item = _buscar_item_por_tipo(personaje, "comida")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok:
                log.append(f"  Comiste: {item['nombre']}. {msg}")

    # Beber si hay necesidad y hay agua disponible
    if personaje.sed > _UMBRAL_SED:
        item = _buscar_item_por_tipo(personaje, "agua")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok:
                log.append(f"  Bebiste: {item['nombre']}. {msg}")

    # Curar heridas si hay medicina disponible
    if personaje.salud < personaje.salud_max * _UMBRAL_CURAR:
        item = _buscar_item_por_tipo(personaje, "medicina")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok:
                log.append(f"  Trataste heridas con {item['nombre']}: {msg}")

    # Recuperar fatiga; el rasgo "pesadillas" reduce esta recuperación
    mult_descanso = personaje.obtener_efecto_rasgo(
        "recuperacion_descanso_mult", 1.0
    )
    recuperacion = int(40 * mult_descanso)
    personaje.fatiga = max(0, personaje.fatiga - recuperacion)
    personaje.moral  = min(100, personaje.moral + 5)
    personaje.pasar_tiempo(_HORAS_DESCANSO)

    log.append(f"  Descansaste {_HORAS_DESCANSO} horas.")

    if personaje.hambre > 75:
        log.append("  ⚠ Sin comida. El hambre es crítica.")
    if personaje.sed > 75:
        log.append("  ⚠ Sin agua. La deshidratación avanza.")

    return ResultadoTick(
        tipo="descanso",
        log_descanso=log,
        exito=True,
        personaje_vivo=personaje.esta_vivo(),
        causa_muerte=(
            "inanición o deshidratación" if not personaje.esta_vivo() else ""
        ),
    )


# ══════════════════════════════════════════════════════════════
#  HELPERS PRIVADOS
# ══════════════════════════════════════════════════════════════

def _buscar_item_por_tipo(personaje, tipo: str) -> dict | None:
    """
    Devuelve el primer ítem del inventario que coincida con el tipo dado.

    El tipo se lee directamente del ítem si está presente, o se infiere
    desde ITEMS por nombre para ítems que no lo traen explícito.
    Nunca busca por nombre hardcodeado.
    """
    for item in personaje.inventario:
        tipo_item = item.get("tipo") or _inferir_tipo_por_nombre(item["nombre"])
        if tipo_item == tipo:
            return item
    return None


def _inferir_tipo_por_nombre(nombre: str) -> str:
    """
    Busca el tipo de un ítem en el catálogo ITEMS usando su nombre.
    Fallback para ítems del inventario que no tienen el campo 'tipo'.
    """
    for defn in ITEMS.values():
        if defn.get("nombre") == nombre:
            return defn.get("tipo", "")
    return ""


def _auto_consumir(personaje, bit) -> None:
    """
    Consumo de emergencia durante expedición.

    Se ejecuta al final de cada zona recorrida. Busca por tipo
    para que nuevos ítems de comida/agua/medicina funcionen
    sin modificar esta función.
    """
    if personaje.sed > 85:
        item = _buscar_item_por_tipo(personaje, "agua")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok:
                bit.entrada(f"Bebiste {item['nombre']} al vuelo.", "aviso")

    if personaje.hambre > 90:
        item = _buscar_item_por_tipo(personaje, "comida")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok:
                bit.entrada(f"Comiste {item['nombre']} al vuelo.", "aviso")

    if personaje.salud < personaje.salud_max * 0.30:
        item = _buscar_item_por_tipo(personaje, "medicina")
        if item:
            ok, msg = personaje.usar_item(item["nombre"])
            if ok:
                bit.entrada(
                    f"Usé {item['nombre']} de emergencia. {msg}", "aviso"
                )


def _exportar_imagenes(log_plano: str, personaje,
                        exportar_img: bool) -> str:
    """
    Exporta la bitácora y el perfil como PNG.
    Devuelve la ruta de la imagen generada, o "" si falló o no se pidió.
    """
    if not exportar_img:
        return ""

    from engine.bitacora import exportar_imagen, exportar_perfil

    nombre_img = f"saves/bitacora_dia{personaje.dia}.png"
    try:
        ruta = exportar_imagen(log_plano, nombre_img)
        exportar_perfil(personaje, "saves/perfil.png")
        return ruta
    except Exception:
        return ""
