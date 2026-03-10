# ============================================================
# engine/input_handler.py — Manejo de input de teclado
#
# Provee lectura de teclas sin Enter (flechas ↑↓, Enter, ESC)
# sobre stdlib pura: termios en Unix, msvcrt en Windows.
#
# Compatibilidad con modo bot: si stdin no es una terminal real,
# menu_navegable() retorna -1 de inmediato y el flujo cae de vuelta
# al input() clásico de texto. Los comandos de texto siguen
# funcionando exactamente igual que antes.
# ============================================================

import os
import sys
import select

_WINDOWS = os.name == "nt"

# Secuencias ANSI Unix → nombre semántico
_UNIX_ESCAPES: dict[str, str] = {
    "[A":  "up",
    "[B":  "down",
    "[C":  "right",
    "[D":  "left",
    "[5~": "pgup",
    "[6~": "pgdn",
}

# Scancodes Windows (segundo byte tras 0x00 o 0xe0)
_WIN_SCANCODES: dict[str, str] = {
    "H": "up",
    "P": "down",
    "K": "left",
    "M": "right",
}

# Colores ANSI internos — no importar desde bitacora para evitar ciclos
_R   = "\033[0m"
_VE  = "\033[92m"
_AM  = "\033[93m"
_CI  = "\033[96m"
_GR  = "\033[90m"
_NE  = "\033[1m"
_DIM = "\033[2m"


def es_interactivo() -> bool:
    """True si hay una terminal real (no pipe, redirect ni modo bot)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def getch() -> str:
    """
    Lee una sola tecla sin esperar Enter.
    Retorna:
      'up' | 'down' | 'left' | 'right'  — flechas
      'enter'                            — Enter / Return
      'esc'                              — Escape
      'backspace'                        — Backspace
      cualquier carácter imprimible      — tal cual
      ''                                 — si no hay terminal interactiva
    """
    if not es_interactivo():
        return ""
    return _getch_windows() if _WINDOWS else _getch_unix()


def _getch_windows() -> str:
    import msvcrt
    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):
        return _WIN_SCANCODES.get(msvcrt.getwch(), "")
    if ch == "\r":           return "enter"
    if ch == "\x1b":         return "esc"
    if ch == "\x03":         raise KeyboardInterrupt
    if ch in ("\x08","\x7f"): return "backspace"
    return ch


def _getch_unix() -> str:
    try:
        import tty
        import termios
    except ImportError:
        return ""

    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
    except termios.error:
        return ""

    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            # Leer secuencia de escape con timeout 60 ms
            try:
                if select.select([sys.stdin], [], [], 0.06)[0]:
                    seq = ""
                    for _ in range(6):
                        c = sys.stdin.read(1)
                        seq += c
                        if c.isalpha() or c == "~":
                            break
                    return _UNIX_ESCAPES.get(seq, "esc")
            except Exception:
                pass
            return "esc"
        if ch in ("\r", "\n"): return "enter"
        if ch == "\x03":       raise KeyboardInterrupt
        if ch in ("\x7f", "\x08"): return "backspace"
        return ch
    except KeyboardInterrupt:
        raise
    except Exception:
        return ""
    finally:
        # Restaurar siempre, incluso si hubo error
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────
#  MENÚ NAVEGABLE
# ──────────────────────────────────────────────────────────────

def menu_navegable(titulo: str,
                   opciones: list[str],
                   subtitulo: str = "",
                   seleccion_inicial: int = 0,
                   limpiar: bool = True) -> int:
    """
    Menú interactivo con ↑↓ + números directos + Enter.
    Retorna índice 0-based, o -1 si ESC o sin terminal.
    """
    if not es_interactivo() or not opciones:
        return -1

    sel = max(0, min(seleccion_inicial, len(opciones) - 1))
    while True:
        _render_menu(titulo, opciones, subtitulo, sel, limpiar)
        k = getch()
        if   k == "up":    sel = (sel - 1) % len(opciones)
        elif k == "down":  sel = (sel + 1) % len(opciones)
        elif k == "enter": return sel
        elif k == "esc":   return -1
        elif k.isdigit():
            n = int(k) - 1
            if 0 <= n < len(opciones):
                return n


def _render_menu(titulo, opciones, subtitulo, sel, limpiar) -> None:
    if limpiar:
        sys.stdout.write("\033[H\033[J")
        sys.stdout.flush()
    ancho = max(40, len(titulo) + 6)
    print(f"\n{_AM}{_NE}  {titulo}{_R}")
    if subtitulo:
        print(f"  {_DIM}{subtitulo}{_R}")
    print(f"  {_GR}{'═' * ancho}{_R}")
    for i, op in enumerate(opciones):
        cursor = f"{_VE}{_NE}▶" if i == sel else f"{_CI} "
        print(f"  {cursor}  {i+1:2d}. {op}{_R}")
    print(f"\n  {_DIM}[↑↓] navegar  [Enter/Núm] confirmar  [Esc] cancelar{_R}", flush=True)


# ──────────────────────────────────────────────────────────────
#  LISTA NAVEGABLE (inventario y similares)
# ──────────────────────────────────────────────────────────────

def lista_navegable(titulo: str,
                    items: list[str],
                    acciones: list[str],
                    header: str = "") -> tuple[int, str]:
    """
    Lista navegable con ↑↓. Al presionar Enter sobre un ítem
    muestra un submenú de acciones.
    Retorna (índice_0based, nombre_accion_lowercase) o (-1, '').
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
            nombre_item = items[sel].strip().split("  ")[0]
            accion_idx  = menu_navegable(
                f"¿Qué hacer con el ítem #{sel + 1}?",
                acciones,
                limpiar=True
            )
            if accion_idx >= 0:
                return sel, acciones[accion_idx].split()[0].lower()
        elif k.isdigit():
            n = int(k) - 1
            if 0 <= n < len(items):
                sel = n


def _render_lista(titulo, items, sel, header, acciones) -> None:
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()
    print(f"\n{_AM}{_NE}  {titulo}{_R}")
    if header:
        print(f"  {_GR}{header}{_R}")
    print(f"  {_GR}{'─' * 64}{_R}")
    # Ventana deslizante de 14 ítems
    inicio = max(0, min(sel - 6, len(items) - 14))
    fin    = min(len(items), inicio + 14)
    for i in range(inicio, fin):
        cursor = f"{_VE}{_NE}▶" if i == sel else f"{_CI} "
        print(f"  {cursor}{items[i]}{_R}")
    if len(items) > 14:
        print(f"  {_DIM}  ({len(items)} ítems en total){_R}")
    print(f"  {_GR}{'─' * 64}{_R}")
    acts = "  ".join(f"[{a.split()[0]}]" for a in acciones)
    print(f"  {_DIM}[↑↓] navegar · [Enter] acción · {acts} · [Esc] volver{_R}")


# ──────────────────────────────────────────────────────────────
#  CONFIRMACIÓN
# ──────────────────────────────────────────────────────────────

def confirmar(mensaje: str, default_no: bool = True) -> bool:
    """Pide s/N. Si no hay terminal retorna False."""
    if not es_interactivo():
        return False
    opcion = "[s/N]" if default_no else "[S/n]"
    resp   = input(f"\n  {_AM}{mensaje} {opcion}: {_R}").strip().lower()
    return resp == "s" if default_no else resp != "n"
