"""
ui/almacen.py — Pantalla del almacén del refugio.

Construida como una instancia de CajaItems con acciones:
  [u] Usar directamente (solo consumibles)
  [t] Tomar al inventario personal
  [i] Inspeccionar

Atajos globales:
  [a]    Agarrar todo de un tipo (abre submenú)
  [↑↓]   Navegar entre ítems
  [Enter] Abrir menú de acciones del ítem seleccionado
  [Esc/Q] Volver
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ui.tui import (
    console, limpiar, pausa,
    COLOR_OK, COLOR_WARN, COLOR_DANGER, COLOR_INFO, COLOR_DIM, COLOR_ACCENT,
)
from ui.item_box import CajaItems, AccionItem, pantalla_inspeccion_item

if TYPE_CHECKING:
    from engine.personaje import Sobreviviente

from ui.item_box import TIPOS_CONSUMIBLES as _TIPOS_CONSUMIBLES


def pantalla_almacen(personaje: "Sobreviviente") -> None:
    """Pantalla del almacén con navegación por flechas."""
    from engine.almacen import (
        listar_items, transferir_al_inventario, cantidad_total_tipo,
        quitar_item, agregar_item,
    )

    def _usar_desde_almacen(ctx, item):
        """Extrae 1 unidad del almacén, aplica sus efectos y la consume."""
        nombre = item["nombre"]
        extraido = quitar_item(ctx.almacen, nombre, 1)
        if extraido is None:
            console.print(f"  [{COLOR_DANGER}]No se pudo sacar del almacén.[/{COLOR_DANGER}]")
            return
        if not ctx.añadir_item(extraido):
            agregar_item(ctx.almacen, extraido)
            console.print(f"  [{COLOR_DANGER}]No cabe en la mochila para usarlo.[/{COLOR_DANGER}]")
            return
        ok, msg = ctx.usar_item(nombre)
        col = COLOR_OK if ok else COLOR_DANGER
        console.print(f"\n  [{col}]{msg}[/{col}]")

    def _equipar_desde_almacen(ctx, item):
        """Intenta llevar un arma al inventario para equiparla en combate."""
        nombre = item["nombre"]
        ok, msg = transferir_al_inventario(ctx.almacen, ctx, nombre, 1)
        if ok:
            console.print(
                f"\n  [{COLOR_OK}]✔ {nombre} guardada en tu mochila. "
                f"Se equipará automáticamente en combate.[/{COLOR_OK}]"
            )
        else:
            console.print(
                f"\n  [{COLOR_WARN}]No cabe en la mochila: {msg}[/{COLOR_WARN}]"
            )

    def _tomar_inventario(ctx, item):
        ok, msg = transferir_al_inventario(ctx.almacen, ctx, item["nombre"], 1)
        col = COLOR_OK if ok else COLOR_DANGER
        console.print(f"\n  [{col}]{msg}[/{col}]")

    def _inspeccionar(ctx, item):
        pantalla_inspeccion_item(item, ctx)

    acciones = [
        AccionItem(
            "u", "Usar directamente",
            _usar_desde_almacen,
            condicion=lambda it: it.get("tipo") in _TIPOS_CONSUMIBLES,
        ),
        AccionItem(
            "e", "Equipar (llevar a mochila)",
            _equipar_desde_almacen,
            condicion=lambda it: it.get("tipo", "").startswith("arma"),
        ),
        AccionItem("t", "Tomar al inventario", _tomar_inventario),
        AccionItem("i", "Inspeccionar",         _inspeccionar),
    ]

    def _agarrar_todo_tipo():
        """Submenú para tomar todos los ítems de un tipo al inventario."""
        from engine.input_handler import menu_navegable
        almacen = personaje.almacen
        tipos_disponibles = sorted({it.get("tipo", "misc") for it in almacen})
        if not tipos_disponibles:
            console.print(f"  [{COLOR_DIM}]El almacén está vacío.[/{COLOR_DIM}]")
            pausa()
            return

        idx = menu_navegable(
            "Tomar todo el tipo:",
            tipos_disponibles + ["↩ Cancelar"],
            limpiar=True,
        )
        if idx < 0 or idx == len(tipos_disponibles):
            return

        tipo_sel = tipos_disponibles[idx]
        items_tipo = [it for it in listar_items(almacen) if it.get("tipo") == tipo_sel]
        tomados = 0
        for it in items_tipo:
            ok, _ = transferir_al_inventario(almacen, personaje, it["nombre"], it.get("cantidad", 1))
            if ok:
                tomados += 1
        console.print(f"\n  [{COLOR_OK}]✔ Tomaste {tomados} ítems de tipo '{tipo_sel}'.[/{COLOR_OK}]")
        pausa()

    caja = CajaItems(
        titulo="ALMACÉN DEL REFUGIO",
        obtener_items=lambda: listar_items(personaje.almacen),
        acciones=acciones,
        contexto=personaje,
        info_header=lambda: (
            f"🍖 {cantidad_total_tipo(personaje.almacen, 'comida')}u  "
            f"💧 {cantidad_total_tipo(personaje.almacen, 'agua')}u  "
            f"📦 {len(personaje.almacen)} tipos"
        ),
        comandos_extra={"a": _agarrar_todo_tipo},
        hint_inferior="[a] Agarrar todo de un tipo",
    )
    caja.run()
