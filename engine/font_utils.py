# ============================================================
# engine/font_utils.py — Utilidades compartidas para carga de fuentes
# ============================================================
from __future__ import annotations

import os


def cargar_fuente(candidatas: list[str], size: int):
    """Busca la primera fuente disponible de la lista y la carga al tamaño dado.

    Si ninguna candidata existe o falla al cargar, devuelve la fuente
    por defecto de Pillow.
    """
    from PIL import ImageFont

    for ruta in candidatas:
        if os.path.exists(ruta):
            try:
                return ImageFont.truetype(ruta, size)
            except Exception:
                continue
    return ImageFont.load_default()
