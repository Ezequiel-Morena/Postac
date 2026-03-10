import os

from engine.constants import (
    ANSI_RESET as R,
    ANSI_VERDE as VE,
    ANSI_ROJO as RO,
    ANSI_AMARILLO as AM,
    ANSI_CYAN as CI,
    ANSI_GRIS as GR,
    ANSI_BLANCO as BL,
    ANSI_NEGRITA as NE,
    ANSI_DIM as DIM,
)

LOGO = f"""
{VE}{NE}
  ██████╗  ██████╗ ███████╗████████╗ █████╗  ██████╗
  ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝
  ██████╔╝██║   ██║███████╗   ██║   ███████║██║
  ██╔═══╝ ██║   ██║╚════██║   ██║   ██╔══██║██║
  ██║     ╚██████╔╝███████║   ██║   ██║  ██║╚██████╗
  ╚═╝      ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝
{GR}  Simulador de Supervivencia Post-Apocalíptica{R}
"""


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def pausa(msg: str = "  [ENTER para continuar]"):
    input(f"\n{GR}{msg}{R}")


def _barra_corta(valor: int, largo: int = 8) -> str:
    """Barra de progreso compacta para la pantalla de supervivientes."""
    valor = max(0, min(100, valor))  # clamp inline — no depende de engine
    llenas = round(valor / 100 * largo)
    return f"{VE}{'█' * llenas}{'░' * (largo - llenas)}{R}"

# Alias de compatibilidad para módulos aún no migrados a rich
from ui.tui import console, limpiar as cls_rich, pausa as pausa_rich  # noqa: F401
