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

    acciones = [
        AccionItem(
            "u", "Usar / consumir",
            _usar,
            condicion=lambda it: it.get("tipo") in _TIPOS_CONSUMIBLES,
        ),
        AccionItem("i", "Inspeccionar", _inspeccionar),
        AccionItem("m", "Mover al almacén", _mover_almacen),
        AccionItem(
            "d", "Descartar",
            _descartar,
            confirmar_msg="¿Descartar '{nombre}'? No se puede recuperar",
        ),
    ]

    caja = CajaItems(
        titulo="INVENTARIO",
        obtener_items=lambda: list(personaje.inventario),
        acciones=acciones,
        contexto=personaje,
        info_header=lambda: (
            f"{personaje.peso_actual():.1f}/{personaje.peso_max:.0f}kg  "
            f"[{len(personaje.inventario)} ítems]"
        ),
        comandos_extra={"c": lambda: _pantalla_crafteo(personaje)},
        hint_inferior="[c] Recetas de crafteo",
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
