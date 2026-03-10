# ============================================================
# engine/input_handler.py — Manejo de input de teclado
#
# API pública principal:
#   leer_entrada(prompt, opciones_nav) — reemplaza input() en todo
#       el proyecto. Si el usuario pulsa ↑/↓ y hay opciones_nav,
#       activa el selector navegable. Si pulsa texto, lo acumula
#       normalmente. Así cualquier pantalla hereda navegación
#       sin código extra.
#
#   menu_navegable(...)  — menú standalone con limpieza de pantalla.
#   lista_navegable(...) — lista con submenú de acciones (inventario).
#   confirmar(...)       — confirmación s/N.
#   es_interactivo()     — True si hay terminal real.
#
# Compatibilidad modo bot: sin terminal, leer_entrada() equivale
# a input() estándar. Los comandos de texto nunca se rompen.
# ============================================================

import os
import sys
import select

_WINDOWS = os.name == "nt"

_R   = "\033[0m"
_VE  = "\033[92m"
_AM  = "\033[93m"
_CI  = "\033[96m"
_GR  = "\033[90m"
_NE  = "\033[1m"
_DIM = "\033[2m"


def es_interactivo() -> bool:
    """True si hay terminal real (no pipe, redirect ni modo bot)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


# ──────────────────────────────────────────────────────────────
#  LECTURA CRUDA DE TECLA
# ──────────────────────────────────────────────────────────────

def getch() -> str:
    """
    Lee una tecla sin esperar Enter.
    Retorna: 'up'|'down'|'left'|'right'|'enter'|'esc'|'backspace'|char|''
    """
    if not es_interactivo():
        return ""
    return _getch_windows() if _WINDOWS else _getch_unix()


def _getch_windows() -> str:
    import msvcrt
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):
        return {"H": "up", "P": "down", "K": "left", "M": "right"}.get(msvcrt.getwch(), "")
    if ch == "\r":              return "enter"
    if ch == "\x1b":            return "esc"
    if ch == "\x03":            raise KeyboardInterrupt
    if ch in ("\x08", "\x7f"): return "backspace"
    return ch


def _getch_unix() -> str:
    try:
        import tty, termios
    except ImportError:
        return ""
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
    except termios.error:
        return ""
    try:
        tty.setraw(fd)
        sys.stdout.flush()
        ch = os.read(fd, 1)
        if not ch:
            return ""
        if ch == b"\x1b":
            ready, _, _ = select.select([sys.stdin], [], [], 0.10)
            if ready:
                rest = os.read(fd, 8)
                if len(rest) >= 2 and rest[0:1] == b"[":
                    c = rest[1:2]
                    if c == b"A": return "up"
                    if c == b"B": return "down"
                    if c == b"C": return "right"
                    if c == b"D": return "left"
            return "esc"
        if ch in (b"\r", b"\n"):      return "enter"
        if ch == b"\x03":             raise KeyboardInterrupt
        if ch in (b"\x7f", b"\x08"): return "backspace"
        try:
            return ch.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    except KeyboardInterrupt:
        raise
    except Exception:
        return ""
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────
#  ENTRADA HÍBRIDA — reemplaza input() en todo el proyecto
# ──────────────────────────────────────────────────────────────

def leer_entrada(prompt: str = "> ",
                 opciones_nav: list[str] | None = None) -> str:
    """
    Reemplaza input() con soporte transparente de navegación.

    Comportamiento:
      ↑ / ↓      — si hay opciones_nav, abre el selector y retorna
                   el índice 1-based como string ("1", "2"...).
                   Si no hay opciones, mueve el cursor del historial
                   (no implementado: retorna "").
      Letra/núm  — la echa en pantalla y completa la línea normalmente.
      Enter      — retorna "".
      Esc        — retorna "".
      Sin tty    — equivale exactamente a input(prompt).
    """
    if not es_interactivo():
        return input(prompt)

    sys.stdout.write(prompt)
    sys.stdout.flush()

    k = getch()

    # ── Flechas → modo navegación ──────────────────────────────
    if k in ("up", "down") and opciones_nav:
        # Borrar el prompt ya impreso
        sys.stdout.write("\r" + " " * (len(prompt) + 2) + "\r")
        sys.stdout.flush()
        sel_inicial = len(opciones_nav) - 1 if k == "up" else 0
        idx = menu_navegable(
            "Seleccionar opción",
            opciones_nav,
            seleccion_inicial=sel_inicial,
            limpiar=True,
        )
        if idx >= 0:
            return str(idx + 1)
        return ""

    # ── Enter / Esc vacíos ─────────────────────────────────────
    if k in ("enter", "esc", ""):
        print()
        return ""

    # ── Tecla de texto → acumular hasta Enter ─────────────────
    if len(k) == 1 and (k.isprintable() or k.isdigit()):
        sys.stdout.write(k)
        sys.stdout.flush()
        return _completar_linea(k)

    print()
    return ""


def _completar_linea(inicial: str = "") -> str:
    """
    Lee caracteres hasta Enter, con soporte de backspace.
    Echa cada carácter en pantalla (comportamiento de readline básico).
    """
    buf = list(inicial)
    while True:
        k = getch()
        if k == "enter":
            print()
            return "".join(buf).strip()
        elif k in ("esc",):
            print()
            return ""
        elif k == "backspace":
            if buf:
                buf.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
        elif len(k) == 1 and (k.isprintable() or k == " "):
            buf.append(k)
            sys.stdout.write(k)
            sys.stdout.flush()


# ──────────────────────────────────────────────────────────────
#  MENÚ NAVEGABLE STANDALONE
# ──────────────────────────────────────────────────────────────

def menu_navegable(titulo: str,
                   opciones: list[str],
                   subtitulo: str = "",
                   seleccion_inicial: int = 0,
                   limpiar: bool = True) -> int:
    """
    Menú con ↑↓ + números directos + Enter.
    limpiar=True  → limpia pantalla (menús standalone).
    limpiar=False → sobreescribe in-place sin tocar el contenido superior.
    Retorna índice 0-based o -1 si ESC / sin terminal.
    """
    if not es_interactivo() or not opciones:
        return -1

    sel           = max(0, min(seleccion_inicial, len(opciones) - 1))
    n_lineas_menu = _altura_menu(titulo, subtitulo, opciones)
    primer_render = True

    while True:
        if limpiar:
            sys.stdout.write("\033[H\033[J")
        elif not primer_render:
            sys.stdout.write(f"\033[{n_lineas_menu}A\033[J")
        primer_render = False

        _dibujar_menu(titulo, opciones, subtitulo, sel)

        k = getch()
        if   k == "up":    sel = (sel - 1) % len(opciones)
        elif k == "down":  sel = (sel + 1) % len(opciones)
        elif k == "enter": return sel
        elif k == "esc":   return -1
        elif k.isdigit():
            n = int(k) - 1
            if 0 <= n < len(opciones):
                return n


def _altura_menu(titulo: str, subtitulo: str, opciones: list[str]) -> int:
    n = 2
    if subtitulo: n += 1
    n += 1
    n += len(opciones)
    n += 2
    return n


def _dibujar_menu(titulo, opciones, subtitulo, sel) -> None:
    ancho = max(42, len(titulo) + 6)
    lines = [f"\n{_AM}{_NE}  {titulo}{_R}"]
    if subtitulo:
        lines.append(f"  {_DIM}{subtitulo}{_R}")
    lines.append(f"  {_GR}{chr(9552) * ancho}{_R}")
    for i, op in enumerate(opciones):
        if i == sel:
            lines.append(f"  {_VE}{_NE}\u25b6  {i+1:2d}. {op}{_R}")
        else:
            lines.append(f"  {_CI}    {i+1:2d}. {op}{_R}")
    lines.append(f"\n  {_DIM}[\u2191\u2193] navegar  [Enter/N\u00fam] confirmar  [Esc] cancelar{_R}")
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


# ──────────────────────────────────────────────────────────────
#  LISTA NAVEGABLE (inventario y similares)
# ──────────────────────────────────────────────────────────────

def lista_navegable(titulo: str,
                    items: list[str],
                    acciones: list[str],
                    header: str = "") -> tuple[int, str]:
    """
    Lista navegable con ↑↓ + Enter para submenú de acciones.
    Retorna (índice_0based, accion_lowercase) o (-1, \'\').
    """
    if not es_interactivo() or not items:
        return -1, ""

    sel = 0
    while True:
        _render_lista(titulo, items, sel, header, acciones)
        k = getch()
        if   k == "up":   sel = (sel - 1) % len(items)
        elif k == "down": sel = (sel + 1) % len(items)
        elif k == "esc":  return -1, ""
        elif k == "enter":
            accion_idx = menu_navegable(
                f"Acción sobre ítem #{sel + 1}",
                acciones,
                limpiar=True,
            )
            if accion_idx >= 0:
                return sel, acciones[accion_idx].split()[0].lower()
        elif k.isdigit():
            n = int(k) - 1
            if 0 <= n < len(items):
                sel = n


def _render_lista(titulo, items, sel, header, acciones) -> None:
    sys.stdout.write("\033[H\033[J")
    lines = [f"\n{_AM}{_NE}  {titulo}{_R}"]
    if header:
        lines.append(f"  {_GR}{header}{_R}")
    lines.append(f"  {_GR}{'\u2500' * 64}{_R}")
    inicio = max(0, min(sel - 6, len(items) - 14))
    fin    = min(len(items), inicio + 14)
    for i in range(inicio, fin):
        if i == sel:
            lines.append(f"  {_VE}{_NE}\u25b6{items[i]}{_R}")
        else:
            lines.append(f"  {_CI} {items[i]}{_R}")
    if len(items) > 14:
        lines.append(f"  {_DIM}  ({len(items)} ítems en total){_R}")
    lines.append(f"  {_GR}{'\u2500' * 64}{_R}")
    acts = "  ".join(f"[{a.split()[0]}]" for a in acciones)
    lines.append(f"  {_DIM}[\u2191\u2193] navegar · [Enter] acción · {acts} · [Esc] volver{_R}")
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stdout.flush()


# ──────────────────────────────────────────────────────────────
#  CONFIRMACIÓN
# ──────────────────────────────────────────────────────────────

def confirmar(mensaje: str, default_no: bool = True) -> bool:
    """Pide s/N. Sin terminal retorna False."""
    if not es_interactivo():
        return False
    opcion = "[s/N]" if default_no else "[S/n]"
    resp   = input(f"\n  {_AM}{mensaje} {opcion}: {_R}").strip().lower()
    return resp == "s" if default_no else resp != "n"
