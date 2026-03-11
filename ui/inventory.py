"""
ui/inventory.py — Pantalla del inventario personal.

Construida como una instancia de CajaItems con acciones:
  [u] Usar / consumir  (solo comida, agua, medicina)
  [i] Inspeccionar
  [m] Mover al almacén
  [d] Descartar

Atajos globales:
  [c]    Abrir pantalla de crafteo
  [↑↓]   Navegar entre ítems
  [Enter] Abrir menú de acciones del ítem seleccionado
  [Esc/Q] Volver
"""
from __future__ import annotations

from ui.tui import (
    console, limpiar, pausa,
    leer_cmd, es_salida, footer_volver,
    COLOR_OK, COLOR_WARN, COLOR_DANGER, COLOR_INFO, COLOR_DIM, COLOR_ACCENT,
)
from ui.item_box import CajaItems, AccionItem, pantalla_inspeccion_item
from rich.table import Table
from rich.text import Text
from rich import box

from ui.item_box import TIPOS_CONSUMIBLES as _TIPOS_CONSUMIBLES


def _es_vestimenta(item: dict) -> bool:
    return item.get("tipo") == "vestimenta" and item.get("slot") in (
        "cabeza", "torso", "piernas", "pies", "manos", "capa_exterior",
    )


def pantalla_inventario(personaje) -> None:
    """Pantalla de inventario con navegación por flechas."""

    def _usar(ctx, item):
        ok, msg = ctx.usar_item(item["nombre"])
        col = COLOR_OK if ok else COLOR_DANGER
        console.print(f"\n  [{col}]{msg}[/{col}]")

    def _descartar(ctx, item):
        try:
            idx = ctx.inventario.index(item)
            ok, nombre = ctx.descartar_por_id(idx + 1)
        except ValueError:
            ok, nombre = False, "No encontrado"
        if ok:
            console.print(f"\n  [{COLOR_OK}]Descartaste: {nombre}[/{COLOR_OK}]")
        else:
            console.print(f"  [{COLOR_DANGER}]Error al descartar.[/{COLOR_DANGER}]")

    def _inspeccionar(ctx, item):
        pantalla_inspeccion_item(item, ctx)

    def _mover_almacen(ctx, item):
        from engine.almacen import depositar_al_almacen
        ok, msg = depositar_al_almacen(ctx, ctx.almacen, item["nombre"], 1)
        col = COLOR_OK if ok else COLOR_DANGER
        console.print(f"\n  [{col}]{msg}[/{col}]")

    def _equipar(ctx, item):
        slot = item.get("slot", "")
        ropa = getattr(ctx, "ropa_equipada", {})
        desplazada = ropa.get(slot)
        if desplazada:
            ctx.inventario.append(desplazada)
        ropa[slot] = dict(item)
        ctx.ropa_equipada = ropa
        try:
            ctx.inventario.remove(item)
        except ValueError:
            pass
        msg = f"Equipaste: {item.get('nombre', '?')} [{slot}]"
        if desplazada:
            msg += f"  (reemplazó: {desplazada.get('nombre', '?')})"
        console.print(f"\n  [{COLOR_OK}]{msg}[/{COLOR_OK}]")

    def _desequipar(ctx, item):
        slot = item.get("slot", "")
        ropa = getattr(ctx, "ropa_equipada", {})
        equipada = ropa.get(slot)
        if equipada and equipada.get("nombre") == item.get("nombre"):
            del ropa[slot]
            ctx.inventario.append(equipada)
            console.print(f"\n  [{COLOR_OK}]Desequipaste: {item.get('nombre', '?')}[/{COLOR_OK}]")
        else:
            console.print(f"\n  [{COLOR_DANGER}]No está equipada.[/{COLOR_DANGER}]")

    def _item_equipada(it: dict) -> bool:
        ropa = getattr(personaje, "ropa_equipada", {})
        slot = it.get("slot", "")
        eq = ropa.get(slot)
        return eq is not None and eq.get("nombre") == it.get("nombre")

    acciones = [
        AccionItem(
            "u", "Usar / consumir",
            _usar,
            condicion=lambda it: it.get("tipo") in _TIPOS_CONSUMIBLES,
        ),
        AccionItem(
            "e", "Equipar",
            _equipar,
            condicion=lambda it: _es_vestimenta(it) and not _item_equipada(it),
        ),
        AccionItem(
            "q", "Desequipar",
            _desequipar,
            condicion=lambda it: _es_vestimenta(it) and _item_equipada(it),
        ),
        AccionItem("i", "Inspeccionar", _inspeccionar),
        AccionItem("m", "Mover al almacén", _mover_almacen),
        AccionItem(
            "d", "Descartar",
            _descartar,
            confirmar_msg="¿Descartar '{nombre}'? No se puede recuperar",
        ),
    ]

    def _info_header():
        ropa = getattr(personaje, "ropa_equipada", {})
        n_eq = len(ropa)
        temp = getattr(personaje, "temp_corporal", 36.5)
        return (
            f"{personaje.peso_actual():.1f}/{personaje.peso_max:.0f}kg  "
            f"[{len(personaje.inventario)} ítems]  "
            f"🌡{temp:.1f}°C  👔{n_eq}/6 slots"
        )

    caja = CajaItems(
        titulo="INVENTARIO",
        obtener_items=lambda: list(personaje.inventario),
        acciones=acciones,
        contexto=personaje,
        info_header=_info_header,
        comandos_extra={
            "c": lambda: _pantalla_crafteo(personaje),
            "v": lambda: _pantalla_vestimenta(personaje),
        },
        hint_inferior="[c] Crafteo  [v] Vestimenta equipada",
    )
    caja.run()


# ── Crafteo ───────────────────────────────────────────────────────────────────

def _pantalla_crafteo(personaje) -> None:
    limpiar()
    console.print(f"\n[bold {COLOR_ACCENT}]  CRAFTEO DE SUPERVIVENCIA[/bold {COLOR_ACCENT}]")

    recetas = personaje.recetas_disponibles()
    if not recetas:
        console.print(f"  [{COLOR_DIM}]No hay recetas cargadas.[/{COLOR_DIM}]")
        pausa()
        return

    t = Table(
        box=box.SIMPLE, border_style=COLOR_DIM,
        show_header=True, header_style=f"bold {COLOR_INFO}",
    )
    t.add_column("ID", width=18)
    t.add_column("Nombre", min_width=20)
    t.add_column("Estado", width=24)
    t.add_column("Desc.", min_width=30)

    for r in recetas:
        estado_txt = (
            Text("LISTA", style=f"bold {COLOR_OK}")
            if r["puede"]
            else Text("FALTAN MATERIALES", style=COLOR_WARN)
        )
        desc = r["desc"]
        if r["faltantes"]:
            desc += f"  [Faltan: {', '.join(r['faltantes'])}]"
        t.add_row(r["id"], r["nombre"], estado_txt, Text(desc, style=COLOR_DIM))

    console.print(t)
    console.print(f"  [{COLOR_DIM}]ID receta a craftear[/{COLOR_DIM}]  {footer_volver()}")
    cmd = leer_cmd()
    if es_salida(cmd) or not cmd:
        return
    ok, msg = personaje.craftear(cmd)
    col = COLOR_OK if ok else COLOR_DANGER
    console.print(f"\n  [{col}]{msg}[/{col}]")
    pausa()


# ── Vestimenta equipada ───────────────────────────────────────────────────────

def _pantalla_vestimenta(personaje) -> None:
    """Muestra la ropa equipada en cada slot con sus propiedades."""
    from data.vestimenta import ICONOS_SLOT, NOMBRES_SLOT, SLOTS_ROPA

    limpiar()
    console.print(f"\n[bold {COLOR_ACCENT}]  👔 VESTIMENTA EQUIPADA[/bold {COLOR_ACCENT}]")

    ropa = getattr(personaje, "ropa_equipada", {})
    temp = getattr(personaje, "temp_corporal", 36.5)
    humedad = getattr(personaje, "humedad_ropa", 0.0)

    console.print(f"  [bold]🌡 Temp. corporal:[/bold] {temp:.1f}°C  "
                  f"[bold]💦 Humedad ropa:[/bold] {humedad:.0f}%\n")

    t = Table(
        box=box.ROUNDED, border_style=COLOR_DIM,
        show_header=True, header_style=f"bold {COLOR_INFO}",
    )
    t.add_column("Slot", width=16)
    t.add_column("Prenda", min_width=22)
    t.add_column("Frío", width=6, justify="right")
    t.add_column("Calor", width=6, justify="right")
    t.add_column("Imperm.", width=8, justify="right")
    t.add_column("Defensa", width=8, justify="right")
    t.add_column("Durab.", width=10, justify="right")

    for slot in SLOTS_ROPA:
        icono = ICONOS_SLOT.get(slot, "")
        nombre_slot = NOMBRES_SLOT.get(slot, slot)
        prenda = ropa.get(slot)
        if prenda:
            dur_max = prenda.get("durabilidad_max", 100)
            dur_act = prenda.get("durabilidad", dur_max)
            dur_pct = int(100 * dur_act / max(dur_max, 1))
            dur_style = COLOR_OK if dur_pct > 50 else (COLOR_WARN if dur_pct > 20 else COLOR_DANGER)
            t.add_row(
                f"{icono} {nombre_slot}",
                Text(prenda.get("nombre", "?"), style=f"bold {COLOR_OK}"),
                str(prenda.get("aislamiento_frio", 0)),
                str(prenda.get("aislamiento_calor", 0)),
                f"{prenda.get('impermeabilidad', 0)}%",
                str(prenda.get("defensa", 0)),
                Text(f"{dur_act}/{dur_max} ({dur_pct}%)", style=dur_style),
            )
        else:
            t.add_row(
                f"{icono} {nombre_slot}",
                Text("— vacío —", style=COLOR_DIM),
                "—", "—", "—", "—", "—",
            )

    console.print(t)
    pausa()
