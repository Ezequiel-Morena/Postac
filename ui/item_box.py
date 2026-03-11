"""
ui/item_box.py — Widget genérico de lista de ítems con navegación por flechas.

CajaItems encapsula:
  - Tabla rich con la fila del cursor resaltada visualmente.
  - Navegación con ↑↓ + Enter para submenú de acciones.
  - Acciones configurables por instancia (AccionItem) con condición y confirmación.
  - Agrupación visual por tipo/categoría (no afecta el cursor).
  - Comandos globales por tecla (atajos que actúan sobre el contenedor completo).

Uso:
    caja = CajaItems(
        titulo="INVENTARIO",
        obtener_items=lambda: personaje.inventario,
        acciones=[AccionItem("u", "Usar", fn_usar), ...],
        contexto=personaje,
    )
    caja.run()

Tanto el inventario personal como el almacén son instancias de CajaItems
con distintas acciones, contextos y fuentes de datos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from engine.input_handler import confirmar, es_interactivo, getch, menu_navegable
from ui.tui import (
    COLOR_ACCENT, COLOR_DANGER, COLOR_DIM, COLOR_INFO, COLOR_OK, COLOR_WARN,
    console, footer_volver, limpiar, pausa,
)

_ICONOS_TIPO: dict[str, str] = {
    "comida": "🍖", "agua": "💧", "medicina": "💊",
    "arma_fuego": "🔫", "arma_cortante": "🔪", "arma_contundente": "🪓",
    "arma_arrojadiza": "🎯", "armadura": "🛡", "casco": "⛑",
    "municion": "🔋", "herramienta": "🔧", "equipo": "🎒",
    "equipo_especial": "⚙", "material": "📦", "libro": "📚",
    "vestimenta": "👔", "misc": "🔹",
}

TIPOS_CONSUMIBLES: frozenset[str] = frozenset({
    "comida", "agua", "medicina", "medicina_fuerte", "purificacion",
})

_ORDEN_TIPOS: list[str] = [
    "comida", "agua", "medicina", "arma_fuego", "arma_cortante",
    "arma_contundente", "arma_arrojadiza", "armadura", "casco",
    "municion", "herramienta", "equipo", "equipo_especial",
    "vestimenta", "material", "libro", "misc",
]


@dataclass
class AccionItem:
    """Define una acción disponible sobre un ítem seleccionado en CajaItems."""
    clave: str                                           # etiqueta de tecla mostrada: 'u', 'm', ...
    label: str                                           # texto visible en el menú de acciones
    ejecutar: Callable[[Any, dict], None]                # fn(contexto, item) → None
    condicion: Callable[[dict], bool] = field(default=lambda _: True)
    confirmar_msg: str | None = None                     # None = sin confirmación previa


class CajaItems:
    """
    Widget reutilizable para mostrar y gestionar cualquier contenedor de ítems.

    Parámetros
    ----------
    titulo          : Texto del panel superior.
    obtener_items   : Callable que retorna list[dict] fresca en cada frame.
                      Los dicts deben tener al menos 'nombre', 'tipo', 'peso'.
    acciones        : Lista de AccionItem. Se filtran por condicion(item) antes de mostrar.
    contexto        : Objeto pasado como primer arg a cada AccionItem.ejecutar (personaje, etc.).
    info_header     : Callable opcional → str para mostrar junto al título (peso, totales, etc.).
    columnas_extra  : Lista de (nombre_col, ancho, fn(item)→str) para columnas adicionales.
    comandos_extra  : Dict tecla→callable() para atajos globales (crafteo, tomar-todo, etc.).
    hint_inferior   : Texto de ayuda que aparece sobre el footer.
    """

    def __init__(
        self,
        titulo: str,
        obtener_items: Callable[[], list[dict]],
        acciones: list[AccionItem],
        contexto: Any = None,
        info_header: Callable[[], str] | None = None,
        columnas_extra: list[tuple[str, int, Callable[[dict], str]]] | None = None,
        comandos_extra: dict[str, Callable[[], None]] | None = None,
        hint_inferior: str = "",
    ) -> None:
        self.titulo = titulo
        self.obtener_items = obtener_items
        self.acciones = acciones
        self.contexto = contexto
        self.info_header = info_header
        self.columnas_extra = columnas_extra or []
        self.comandos_extra = comandos_extra or {}
        self.hint_inferior = hint_inferior
        self._cursor = 0

    def run(self) -> None:
        """Bucle principal. Bloquea hasta que el jugador salga con Esc/Q."""
        while True:
            items = self._items_ordenados()
            n = len(items)
            self._cursor = max(0, min(self._cursor, n - 1)) if n > 0 else 0

            limpiar()
            self._dibujar(items)

            if not es_interactivo():
                return

            k = getch()

            if k == "up" and n > 0:
                self._cursor = (self._cursor - 1) % n
            elif k == "down" and n > 0:
                self._cursor = (self._cursor + 1) % n
            elif k in ("esc", "q"):
                return
            elif k == "enter" and n > 0:
                self._ejecutar_accion_menu(items[self._cursor])
            elif k in self.comandos_extra:
                self.comandos_extra[k]()

    # ── Renderizado ───────────────────────────────────────────────────────────

    def _items_ordenados(self) -> list[dict]:
        """Retorna los ítems ordenados por tipo para la agrupación visual."""
        orden = {t: i for i, t in enumerate(_ORDEN_TIPOS)}
        items = list(self.obtener_items())
        items.sort(key=lambda it: (
            orden.get(it.get("tipo", "misc"), 99),
            it.get("nombre", ""),
        ))
        return items

    def _dibujar(self, items: list[dict]) -> None:
        info = self.info_header() if self.info_header else ""
        header_txt = f"[bold {COLOR_ACCENT}]{self.titulo}[/bold {COLOR_ACCENT}]"
        if info:
            header_txt += f"  [{COLOR_DIM}]{info}[/{COLOR_DIM}]"
        console.print(Panel(header_txt, border_style=COLOR_INFO, padding=(0, 1)))

        if not items:
            console.print(f"\n  [{COLOR_DIM}](vacío)[/{COLOR_DIM}]\n")
        else:
            console.print(self._build_tabla(items))

        if self.hint_inferior:
            console.print(f"  [{COLOR_DIM}]{self.hint_inferior}[/{COLOR_DIM}]")
        console.print(f"  {footer_volver('[↑↓] navegar  [Enter] acciones')}")

    def _build_tabla(self, items: list[dict]) -> Table:
        t = Table(
            box=box.SIMPLE,
            border_style=COLOR_DIM,
            show_header=True,
            header_style=f"bold {COLOR_INFO}",
            expand=False,
        )
        t.add_column(" ", width=2)
        t.add_column("#", width=4, justify="right")
        t.add_column("Nombre", min_width=26)
        t.add_column("Cant.", width=6, justify="right")
        t.add_column("Peso", width=7, justify="right")
        t.add_column("Tipo", width=18)
        for col_nombre, col_ancho, _ in self.columnas_extra:
            t.add_column(col_nombre, width=col_ancho)

        cat_actual = ""
        for i, item in enumerate(items):
            tipo = item.get("tipo", "misc")
            if tipo != cat_actual:
                icono = _ICONOS_TIPO.get(tipo, "🔹")
                t.add_row(
                    "", "",
                    Text(f"{icono} {tipo}", style=f"bold {COLOR_ACCENT}"),
                    "", "", "",
                    *["" for _ in self.columnas_extra],
                )
                cat_actual = tipo

            es_sel = (i == self._cursor)
            row_style = "bold on grey15" if es_sel else None
            cursor_icon = Text("▶", style=f"bold {COLOR_ACCENT}") if es_sel else Text(" ")
            nombre_style = f"bold {COLOR_ACCENT}" if es_sel else COLOR_INFO
            cant = item.get("cantidad", item.get("usos", 1))
            extras = [Text(fn(item), style=COLOR_DIM) for _, _, fn in self.columnas_extra]

            t.add_row(
                cursor_icon,
                Text(str(i + 1), style=COLOR_DIM),
                Text(item.get("nombre", "?")[:28], style=nombre_style),
                Text(str(cant), style=COLOR_DIM),
                Text(f"{item.get('peso', 0):.1f}kg", style=COLOR_DIM),
                Text(f"{_ICONOS_TIPO.get(tipo, '🔹')} {tipo}", style=COLOR_DIM),
                *extras,
                style=row_style,
            )
        return t

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _ejecutar_accion_menu(self, item: dict) -> None:
        """Muestra submenú de acciones filtradas para el ítem seleccionado."""
        acciones_visibles = [a for a in self.acciones if a.condicion(item)]
        if not acciones_visibles:
            console.print(f"  [{COLOR_DIM}]Sin acciones disponibles para este ítem.[/{COLOR_DIM}]")
            pausa()
            return

        labels = [f"[{a.clave}] {a.label}" for a in acciones_visibles]
        cant = item.get("cantidad", item.get("usos", 1))
        idx = menu_navegable(
            item.get("nombre", "?"),
            labels,
            subtitulo=f"Tipo: {item.get('tipo', '?')}  ×{cant}  {item.get('peso', 0):.1f}kg",
            limpiar=True,
        )
        if idx < 0:
            return

        accion = acciones_visibles[idx]
        if accion.confirmar_msg:
            if not confirmar(accion.confirmar_msg.format(nombre=item.get("nombre", "?"))):
                return

        accion.ejecutar(self.contexto, item)
        pausa()


# ── Pantalla de inspección compartida ────────────────────────────────────────

def pantalla_inspeccion_item(item: dict, personaje: Any | None = None) -> None:
    """
    Muestra los detalles completos de un ítem.
    Si se provee personaje, muestra efectos calculados con sus rasgos/skills.
    """
    from rich.table import Table

    limpiar()
    icono = _icono_item(item)
    console.print(f"\n[bold {COLOR_ACCENT}]  {icono}  {item.get('nombre', '?')}[/bold {COLOR_ACCENT}]")
    console.print(f"  [{COLOR_DIM}]{'─' * 48}[/{COLOR_DIM}]")

    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column(width=12, style=COLOR_DIM)
    t.add_column(style=COLOR_INFO)

    cant = item.get("cantidad", item.get("usos", ""))
    peso = item.get("peso", 0)
    t.add_row("Tipo",      item.get("tipo", "—"))
    t.add_row("Peso",      f"{peso:.1f}kg" + (f"  ×{cant}" if cant else ""))
    console.print(t)

    desc = item.get("desc", "Sin descripción.")
    console.print(f"\n  [{COLOR_ACCENT}]{desc}[/{COLOR_ACCENT}]")

    # Efectos calculados si hay personaje disponible
    if personaje is not None:
        info = personaje.info_item_dict(item)
        if info.get("efectos"):
            console.print(f"\n  [{COLOR_WARN}]Efectos:[/{COLOR_WARN}]")
            for linea in info["efectos"]:
                console.print(f"    [{COLOR_OK}]{linea}[/{COLOR_OK}]")
    elif item.get("efectos"):
        console.print(f"\n  [{COLOR_WARN}]Efectos:[/{COLOR_WARN}]")
        for clave, valor in item["efectos"].items():
            if isinstance(valor, (int, float)):
                console.print(f"    [{COLOR_OK}]{clave:12} {valor:+d}[/{COLOR_OK}]")

    pausa()


def _icono_item(item: dict) -> str:
    return _ICONOS_TIPO.get(item.get("tipo", "misc"), "🔹")
