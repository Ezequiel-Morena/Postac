# ============================================================
# ui/tui.py — Utilidades UI centralizadas con rich
#
# Reemplaza el sistema de ANSI manual con rich para output
# moderno. El input sigue usando engine/input_handler.getch().
# ============================================================

from __future__ import annotations
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from engine.input_handler import getch, es_interactivo

# Consola global con tema oscuro
console = Console(highlight=False)

# ── Paleta de colores semánticos ──────────────────────────────
COLOR_OK     = "bright_green"
COLOR_WARN   = "bright_yellow"
COLOR_DANGER = "bright_red"
COLOR_INFO   = "bright_cyan"
COLOR_DIM    = "grey50"
COLOR_ACCENT = "bright_white"

STYLE_HEADER   = f"bold {COLOR_ACCENT}"
STYLE_SELECTED = f"bold {COLOR_OK} on grey15"
STYLE_NORMAL   = COLOR_INFO

# ── Convención de salida/navegación — definida UNA vez ───────
#
# Para cambiar qué teclas significan "volver" en todo el juego,
# solo hay que editar CMDS_SALIR. Es_salida() y leer_cmd() lo
# propagan automáticamente a todas las pantallas.
#
CMDS_SALIR: frozenset[str] = frozenset({"esc", "q"})


def es_salida(cmd: str) -> bool:
    """True si el comando significa 'volver / cerrar pantalla'."""
    return cmd in CMDS_SALIR


def leer_cmd(prompt: str = "  > ") -> str:
    """
    Lector de comandos unificado para TODAS las pantallas.

    Comportamiento:
      - Con terminal real: getch() — sin necesidad de Enter.
      - Sin terminal (bot/pipe): input() clásico.
      - 'q' se normaliza a 'esc' para mantener convención única.
      - Enter vacío retorna ''.

    Si mañana cambia la convención de salida, solo se toca aquí.
    """
    if not es_interactivo():
        k = input(prompt).strip().lower()
        return "esc" if k == "q" else k
    k = getch()
    return "esc" if k == "q" else k


def footer_volver(extra: str = "") -> str:
    """
    Línea de footer estándar con [Esc] Volver.
    Usar en todas las pantallas para consistencia visual.
    """
    partes = [f"[{COLOR_DIM}][Esc/Q] Volver[/{COLOR_DIM}]"]
    if extra:
        partes.append(f"[{COLOR_DIM}]{extra}[/{COLOR_DIM}]")
    return "  ".join(partes)


def color_vital(valor: int, invertido: bool = False) -> str:
    """Color según nivel de vital. invertido=True para hambre/sed/fatiga (alto=malo)."""
    if invertido:
        if valor > 80: return COLOR_DANGER
        if valor > 55: return COLOR_WARN
        return COLOR_OK
    else:
        if valor < 25: return COLOR_DANGER
        if valor < 50: return COLOR_WARN
        return COLOR_OK


def barra_vital(valor: int, maximo: int = 100, ancho: int = 12) -> Text:
    """Barra de progreso como rich Text con bloques Unicode."""
    pct    = max(0.0, min(1.0, valor / max(1, maximo)))
    llenas = round(pct * ancho)
    col    = color_vital(int(pct * 100))
    barra  = Text()
    barra.append("█" * llenas, style=col)
    barra.append("░" * (ancho - llenas), style=COLOR_DIM)
    barra.append(f" {valor:3d}", style=col)
    return barra


def barra_invertida(valor: int, ancho: int = 12) -> Text:
    """Barra para vitales invertidos (hambre, sed, fatiga): lleno=malo."""
    nivel_bueno = 100 - valor
    return barra_vital(nivel_bueno, ancho=ancho)


def dots_peligro(nivel: int, maximo: int = 5) -> Text:
    """●●●○○ para niveles de peligro."""
    t = Text()
    for i in range(maximo):
        if i < nivel:
            col = COLOR_DANGER if nivel >= 4 else (COLOR_WARN if nivel >= 3 else COLOR_OK)
            t.append("●", style=col)
        else:
            t.append("○", style=COLOR_DIM)
    return t


def limpiar():
    """Limpia la pantalla."""
    console.clear()


def pausa(msg: str = "[ENTER para continuar]"):
    if es_interactivo():
        console.print(f"\n  [{COLOR_DIM}]{msg}[/{COLOR_DIM}]")
        getch()
    else:
        input(f"\n  {msg}")


def header_personaje(personaje) -> Panel:
    """Panel superior con nombre, día, hora y background."""
    p = personaje
    sexo_icon = "♂" if p.genero == "Masculino" else "♀"
    bg_nombre = p.background.get("nombre", "?") if isinstance(p.background, dict) else str(p.background)

    titulo = Text()
    titulo.append(f"  {p.nombre} {p.apellido} ", style=STYLE_HEADER)
    titulo.append(f"{sexo_icon} {p.edad}a", style=COLOR_DIM)
    titulo.append("  ·  ", style=COLOR_DIM)
    titulo.append(bg_nombre, style=COLOR_INFO)
    titulo.append(f"  ·  Día {p.dia}", style=COLOR_DIM)
    titulo.append(f"  {p.hora:02d}:00 hs", style=COLOR_DIM)

    return Panel(titulo, border_style=COLOR_DIM, padding=(0, 1))


def tabla_vitales(personaje) -> Table:
    """Tabla 2×3 con todos los vitales del personaje."""
    p = personaje
    t = Table(box=None, padding=(0, 2), show_header=False, expand=True)
    t.add_column(width=4)
    t.add_column(width=16)
    t.add_column(width=4)
    t.add_column(width=16)

    salud_pct  = int(p.salud / max(1, p.salud_max) * 100)
    salud_col  = color_vital(salud_pct)
    hambre_col = color_vital(p.hambre, invertido=True)
    sed_col    = color_vital(p.sed, invertido=True)
    fatiga_col = color_vital(p.fatiga, invertido=True)
    moral_col  = color_vital(p.moral)

    t.add_row(
        f"[{salud_col}]❤[/{salud_col}]",
        barra_vital(p.salud, p.salud_max),
        f"[{hambre_col}]🍖[/{hambre_col}]",
        barra_invertida(p.hambre),
    )
    t.add_row(
        f"[{sed_col}]💧[/{sed_col}]",
        barra_invertida(p.sed),
        f"[{fatiga_col}]⚡[/{fatiga_col}]",
        barra_invertida(p.fatiga),
    )
    t.add_row(
        f"[{moral_col}]🧠[/{moral_col}]",
        barra_vital(p.moral),
        f"[grey50]☢[/grey50]" if p.radiacion > 0 else "",
        barra_vital(100 - p.radiacion) if p.radiacion > 0 else Text(""),
    )
    return t


def tabla_zonas(opciones: list[dict], personaje, seleccion: int = -1) -> Table:
    """Tabla de zonas de expedición con peligro, distancia, clima."""
    t = Table(
        box=box.SIMPLE_HEAVY,
        border_style=COLOR_DIM,
        show_header=True,
        header_style=f"bold {COLOR_INFO}",
        expand=True,
    )
    t.add_column("#", width=3, justify="right")
    t.add_column("Destino", min_width=22)
    t.add_column("Peligro", width=10, justify="center")
    t.add_column("Dist.", width=6, justify="right")
    t.add_column("Clima", width=20)

    for i, area in enumerate(opciones, 1):
        peligro  = area.get("peligro", 1)
        dist     = area.get("distancia_km", "?")
        visitada = area["area_key"] in personaje.areas_visitadas
        nombre   = area["nombre"]
        clima_ic = area.get("clima_icono", "")
        temp     = area.get("temperatura_c", "?")

        row_style = STYLE_SELECTED if (i - 1) == seleccion else STYLE_NORMAL

        num_text = Text(str(i), style=row_style)
        nom_text = Text()
        nom_text.append(nombre, style=row_style)
        if visitada:
            nom_text.append(" ✓", style=COLOR_DIM)

        t.add_row(
            num_text,
            nom_text,
            dots_peligro(peligro),
            Text(f"{dist}km", style=COLOR_DIM),
            Text(f"{clima_ic} {temp}°C", style=COLOR_DIM),
        )

    # Fila de descanso
    desc_style = STYLE_SELECTED if seleccion == len(opciones) else STYLE_NORMAL
    t.add_row(
        Text("0", style=desc_style),
        Text("Descansar en el refugio", style=desc_style),
        Text(""),
        Text(""),
        Text(""),
    )
    return t


def shortcuts_bar(shortcuts: dict[str, str]) -> Text:
    """Barra de shortcuts: [I] Inventario  [F] Ficha  ..."""
    t = Text()
    for key, desc in shortcuts.items():
        t.append(f"[{key.upper()}]", style=f"bold {COLOR_ACCENT}")
        t.append(f" {desc}  ", style=COLOR_DIM)
    return t


def menu_rich(
    titulo: str,
    opciones: list[str],
    subtextos: list[str] | None = None,
    seleccion_inicial: int = 0,
    subtitulo: str = "",
) -> int:
    """
    Menú navegable con rich + getch.
    ↑↓ navega, Enter confirma, Esc cancela (-1), números directos.
    Si no es interactivo retorna -1.
    """
    if not es_interactivo() or not opciones:
        return -1

    sel = max(0, min(seleccion_inicial, len(opciones) - 1))

    while True:
        console.clear()
        _render_menu_rich(titulo, opciones, subtextos, sel, subtitulo)

        k = getch()
        if k == "up":
            sel = (sel - 1) % len(opciones)
        elif k == "down":
            sel = (sel + 1) % len(opciones)
        elif k == "enter":
            return sel
        elif k == "esc":
            return -1
        elif k.isdigit():
            n = int(k) - 1
            if 0 <= n < len(opciones):
                return n


def _render_menu_rich(titulo, opciones, subtextos, sel, subtitulo):
    t = Table(
        box=box.ROUNDED,
        border_style=COLOR_DIM,
        show_header=False,
        padding=(0, 2),
        expand=False,
        min_width=50,
    )
    t.add_column(width=3)
    t.add_column(min_width=40)

    for i, op in enumerate(opciones):
        sub = subtextos[i] if subtextos and i < len(subtextos) else ""
        if i == sel:
            t.add_row(
                Text("▶", style=f"bold {COLOR_OK}"),
                Text(op, style=STYLE_SELECTED),
            )
            if sub:
                t.add_row(Text(""), Text(sub, style=f"italic {COLOR_DIM}"))
        else:
            t.add_row(
                Text(f"{i+1}", style=COLOR_DIM),
                Text(op, style=STYLE_NORMAL),
            )
            if sub:
                t.add_row(Text(""), Text(sub, style=f"italic {COLOR_DIM}"))

    panel = Panel(
        t,
        title=f"[bold {COLOR_ACCENT}]{titulo}[/bold {COLOR_ACCENT}]",
        subtitle=f"[{COLOR_DIM}]{subtitulo}[/{COLOR_DIM}]" if subtitulo else None,
        border_style=COLOR_INFO,
        padding=(0, 1),
    )
    console.print(panel)
    console.print(
        f"  [{COLOR_DIM}][↑↓] navegar  [Enter/Núm] confirmar  [Esc] cancelar[/{COLOR_DIM}]"
    )


# ──────────────────────────────────────────────────────────────
#  LEADERBOARD — Rendering con Rich
# ──────────────────────────────────────────────────────────────

_MEDALLAS = {0: "🥇", 1: "🥈", 2: "🥉"}


def render_leaderboard(limite: int = 10) -> Panel:
    """Renderiza el leaderboard como un Panel Rich."""
    from engine.save_manager import obtener_leaderboard

    tabla_data = obtener_leaderboard()
    if not tabla_data:
        return Panel(
            f"[{COLOR_DIM}]No hay entradas en el ranking aún.[/{COLOR_DIM}]",
            title=f"[bold {COLOR_ACCENT}]RANKING DE CAÍDOS[/bold {COLOR_ACCENT}]",
            border_style=COLOR_DIM,
        )

    t = Table(
        box=box.SIMPLE_HEAVY,
        border_style=COLOR_DIM,
        show_header=True,
        header_style=f"bold {COLOR_INFO}",
        expand=True,
        padding=(0, 1),
    )
    t.add_column("#", width=4, justify="right")
    t.add_column("Nombre", min_width=20)
    t.add_column("Trasfondo", min_width=16)
    t.add_column("Edad", width=5, justify="right")
    t.add_column("Días", width=5, justify="right")
    t.add_column("Pts", width=6, justify="right")

    for i, e in enumerate(tabla_data[:limite]):
        med = _MEDALLAS.get(i, f"{i+1}.")
        if i == 0:
            style = f"bold {COLOR_WARN}"
        elif i < 3:
            style = COLOR_OK
        elif i < 5:
            style = COLOR_INFO
        else:
            style = COLOR_DIM

        nombre = e.get("nombre", "?")[:21]
        bg = e.get("background", "?")[:17]
        edad = f"{e.get('edad_final', '?')}a"
        dias = f"{e.get('dias', 0)}d"
        pts = str(e.get("puntuacion", 0))

        t.add_row(
            Text(med, style=style),
            Text(nombre, style=style),
            Text(bg, style=COLOR_DIM),
            Text(edad, style=COLOR_DIM),
            Text(dias, style=style),
            Text(pts, style=style),
        )

        # Línea de causa + fecha
        causa = e.get("causa_muerte", "?")[:35]
        fecha = e.get("fecha", "")
        t.add_row(
            Text(""), Text(""), Text(""),
            Text(""),
            Text(f"↳ {causa}", style=COLOR_DIM, overflow="ellipsis"),
            Text(fecha, style=COLOR_DIM),
        )

        # Línea de legado
        bits: list[str] = []
        if e.get("tuvo_pareja"):
            bits.append("❤ pareja")
        if e.get("tuvo_hijos"):
            bits.append("▸ hijos")
        if e.get("animales_count"):
            bits.append(f"🐾×{e['animales_count']}")
        if e.get("mejor_skill"):
            bits.append(f"★ {e['mejor_skill']}")
        if e.get("condiciones_al_morir"):
            bits.append(f"⚕ {', '.join(e['condiciones_al_morir'][:2])}")
        if bits:
            t.add_row(
                Text(""), Text(""), Text(""),
                Text(""),
                Text(" · ".join(bits), style=COLOR_DIM),
                Text(""),
            )

    return Panel(
        t,
        title=f"[bold {COLOR_ACCENT}]TABLA DE CLASIFICACIÓN — SUPERVIVIENTES CAÍDOS[/bold {COLOR_ACCENT}]",
        border_style=COLOR_WARN,
        padding=(0, 1),
    )


def render_leaderboard_ansi(limite: int = 10) -> str:
    """Versión ANSI del leaderboard para CLI sin Rich (--ranking, modo autónomo)."""
    from engine.save_manager import obtener_leaderboard

    tabla_data = obtener_leaderboard()
    if not tabla_data:
        return "\n  (No hay entradas en el ranking aún.)\n"

    AM = "\033[93m"; VE = "\033[92m"; CI = "\033[96m"
    GR = "\033[90m"; NE = "\033[1m"; R = "\033[0m"
    medallas = {1: "🥇", 2: "🥈", 3: "🥉"}

    lineas = [
        f"\n{AM}{NE}{'═' * 65}",
        f"  TABLA DE CLASIFICACIÓN — SUPERVIVIENTES CAÍDOS",
        f"{'─' * 65}{R}",
        f"  {'#':<3} {'Nombre':<22} {'Trasfondo':<18} {'Edad':>4} {'Días':>5} {'Pts':>6}",
        f"{GR}{'─' * 65}{R}",
    ]
    for i, e in enumerate(tabla_data[:limite], 1):
        med = medallas.get(i, f" {i}.")
        col = f"{AM}{NE}" if i == 1 else (VE if i <= 3 else (CI if i <= 5 else R))
        edad_str = f"{e.get('edad_final', '?')}a"
        lineas.append(
            f"  {col}{med:<3} {e['nombre'][:21]:<22} {e['background'][:17]:<18}"
            f" {edad_str:>4} {e['dias']:>5}d {e['puntuacion']:>6}{R}"
        )
        causa = e.get("causa_muerte", "?")[:30]
        fecha = e.get("fecha", "")
        lineas.append(f"       {GR}↳ {causa} — {fecha}{R}")
        bits: list[str] = []
        if e.get("tuvo_pareja"):
            bits.append("❤ pareja")
        if e.get("tuvo_hijos"):
            bits.append("▸ hijos")
        if e.get("animales_count"):
            bits.append(f"🐾×{e['animales_count']}")
        if e.get("mejor_skill"):
            bits.append(f"★ {e['mejor_skill']}")
        if e.get("condiciones_al_morir"):
            bits.append(f"⚕ {', '.join(e['condiciones_al_morir'][:2])}")
        if bits:
            lineas.append(f"       {GR}   {' · '.join(bits)}{R}")
    lineas.append(f"{AM}{'═' * 65}{R}\n")
    return "\n".join(lineas)
