# ============================================================
# exportador.py — Convierte la bitácora en imagen PNG estilo terminal
# ============================================================
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont


# ─────────────────────────────────────────────────────────────
#  CONFIGURACIÓN VISUAL
# ─────────────────────────────────────────────────────────────
ANCHO_IMG   = 900
MARGEN_X    = 40
MARGEN_Y    = 40
TAMANO_FONT = 16
LINE_HEIGHT = 22
COLOR_BG    = (10, 12, 10)       # negro verdoso
COLOR_TEXTO = (140, 230, 100)    # verde terminal clásico
COLOR_DIM   = (70, 120, 60)      # verde apagado (detalles secundarios)
COLOR_ROJO  = (220, 80, 80)      # alertas, combate
COLOR_CIAN  = (80, 200, 200)     # eventos
COLOR_AMARILLO = (220, 200, 80)  # resumen / títulos
COLOR_BLANCO = (200, 210, 200)   # texto normal
COLOR_SEP   = (40, 80, 40)       # separadores

# Buscar fuentes monoespaciadas disponibles en el sistema
FUENTES_CANDIDATAS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    "/usr/share/fonts/truetype/noto/NotoMono-Regular.ttf",
    "/System/Library/Fonts/Monaco.ttf",
    "C:/Windows/Fonts/consola.ttf",
]

FUENTES_BOLD_CANDIDATAS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
]


def _cargar_fuente(candidatas: list[str], size: int) -> ImageFont.FreeTypeFont:
    for ruta in candidatas:
        if os.path.exists(ruta):
            try:
                return ImageFont.truetype(ruta, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _obtener_color_linea(linea: str) -> tuple:
    """Determina el color según el contenido de la línea."""
    if any(k in linea for k in ["BITÁCORA", "RESUMEN", "===", "DÍA", "Día", "---"]):
        return COLOR_AMARILLO
    if any(k in linea for k in ["COMBATE", "INFECTADO", "BANDIDO", "JAURÍA",
                                  "✖", "daño", "hp", "golpea", "¡EMBOSCADA"]):
        return COLOR_ROJO
    if any(k in linea for k in ["Encontrado:", "Encontraste", "+", "Buena cosecha",
                                  "obtenidos", "LOOT", "Objetos"]):
        return COLOR_TEXTO
    if any(k in linea for k in ["📍", "EVENTO", "Encontraste", "Descubriste",
                                  "sobreviviente", "Sobreviviente"]):
        return COLOR_CIAN
    if any(k in linea for k in ["Salud", "Hambre", "Sed", "Fatiga", "Moral",
                                  "Radiación", "Estado", "Expediciones"]):
        return COLOR_AMARILLO
    if any(k in linea for k in ["¡CRITICO", "Agonizante", "☢", "Condiciones"]):
        return COLOR_ROJO
    if linea.strip().startswith(("•", "✔", "✖", "→", "►", "▶")):
        return COLOR_CIAN
    if linea.strip() == "" or all(c in ("=", "-", "─", "═") for c in linea.strip()):
        return COLOR_SEP
    return COLOR_BLANCO


def exportar_bitacora_imagen(texto_plano: str,
                              ruta_salida: str = "bitacora.png",
                              titulo_extra: str = "") -> str:
    """
    Convierte el texto de la bitácora en una imagen PNG estilo terminal verde.
    Retorna la ruta del archivo generado.
    """
    font      = _cargar_fuente(FUENTES_CANDIDATAS, TAMANO_FONT)
    font_bold = _cargar_fuente(FUENTES_BOLD_CANDIDATAS, TAMANO_FONT + 1)

    # Dividir texto en líneas y hacer wrap
    lineas_raw = texto_plano.split("\n")
    lineas_finales = []
    max_chars = (ANCHO_IMG - MARGEN_X * 2) // (TAMANO_FONT // 2 + 2)

    for linea in lineas_raw:
        if len(linea) <= max_chars:
            lineas_finales.append(linea)
        else:
            # Wrap preservando la indentación
            indent = len(linea) - len(linea.lstrip())
            indent_str = " " * indent
            wrapped = textwrap.wrap(linea.strip(), max_chars - indent)
            for i, w in enumerate(wrapped):
                if i == 0:
                    lineas_finales.append(indent_str + w)
                else:
                    lineas_finales.append(indent_str + "    " + w)

    # Calcular altura necesaria
    alto_total = MARGEN_Y * 2 + len(lineas_finales) * LINE_HEIGHT + 60

    # Crear imagen
    img = Image.new("RGB", (ANCHO_IMG, alto_total), color=COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Borde sutil
    draw.rectangle([2, 2, ANCHO_IMG - 3, alto_total - 3],
                   outline=(30, 60, 30), width=2)

    # Píxeles de "escaneado" (ruido de terminal antiguo)
    import random
    for _ in range(500):
        x = random.randint(0, ANCHO_IMG - 1)
        y = random.randint(0, alto_total - 1)
        draw.point((x, y), fill=(15, 25, 15))

    # Líneas de scanline sutiles
    for y in range(0, alto_total, 4):
        draw.line([(0, y), (ANCHO_IMG, y)], fill=(0, 0, 0, 20), width=1)

    # Watermark / firma
    draw.text((ANCHO_IMG - 160, alto_total - 22),
              "DIARIO APOCALIPSIS v1.0",
              fill=(30, 60, 30), font=font)

    # Escribir líneas
    y_pos = MARGEN_Y
    for linea in lineas_finales:
        color = _obtener_color_linea(linea)

        # Negrita para títulos
        es_titulo = any(k in linea for k in ["BITÁCORA", "RESUMEN", "===",
                                               "ESTADO FINAL", "---", "COMBATE —"])
        f = font_bold if es_titulo else font

        draw.text((MARGEN_X, y_pos), linea, fill=color, font=f)
        y_pos += LINE_HEIGHT

    img.save(ruta_salida, "PNG", optimize=True)
    return ruta_salida


def exportar_resumen_personaje(personaje, ruta_salida: str = "perfil.png") -> str:
    """
    Genera una imagen de la ficha del personaje (para publicar junto con el diario).
    """
    font      = _cargar_fuente(FUENTES_CANDIDATAS, 17)
    font_bold = _cargar_fuente(FUENTES_BOLD_CANDIDATAS, 19)
    font_sm   = _cargar_fuente(FUENTES_CANDIDATAS, 14)

    ancho, alto = 700, 500
    img = Image.new("RGB", (ancho, alto), color=COLOR_BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, ancho-3, alto-3], outline=(40, 90, 40), width=2)

    y = 30
    sexo = "♂" if personaje.genero == "Masculino" else "♀"

    def write(texto, color=COLOR_TEXTO, bold=False, indent=0):
        nonlocal y
        f = font_bold if bold else font
        draw.text((30 + indent, y), texto, fill=color, font=f)
        y += 26

    write("═" * 50, COLOR_SEP)
    write(f"  FICHA DE SUPERVIVIENTE", COLOR_AMARILLO, bold=True)
    write("═" * 50, COLOR_SEP)
    write(f"  {personaje.nombre} {personaje.apellido}  {sexo}  {personaje.edad} años", COLOR_BLANCO, bold=True)
    write(f"  {personaje.background['nombre']}", COLOR_CIAN)
    write(f"  Día {personaje.dia} — {personaje.hora:02d}:00hs  "
          f"| Exp.: {personaje.expediciones_completadas}", COLOR_DIM)
    write("─" * 50, COLOR_SEP)

    # Stats
    write("  ESTADÍSTICAS", COLOR_AMARILLO, bold=True)
    stat_names = {"fuerza": "FUE", "destreza": "DES", "resistencia": "RES",
                  "percepcion": "PER", "inteligencia": "INT", "suerte": "SRT"}
    row = "  " + "   ".join(f"{abbr}:{personaje.stats[k]:2d}"
                              for k, abbr in stat_names.items())
    write(row, COLOR_TEXTO)

    write("─" * 50, COLOR_SEP)
    write("  VITALES", COLOR_AMARILLO, bold=True)

    def barra_img(valor, maximo=100, ancho=15):
        llenos = int((valor / max(1, maximo)) * ancho)
        return f"[{'█'*llenos}{'░'*(ancho-llenos)}] {valor}/{maximo}"

    col_salud = COLOR_TEXTO if personaje.salud > 50 else (COLOR_AMARILLO if personaje.salud > 25 else COLOR_ROJO)
    write(f"  Salud    {barra_img(personaje.salud, personaje.salud_max)}", col_salud)
    write(f"  Hambre   {barra_img(100-personaje.hambre)}",
          COLOR_ROJO if personaje.hambre > 70 else COLOR_TEXTO)
    write(f"  Sed      {barra_img(100-personaje.sed)}",
          COLOR_ROJO if personaje.sed > 70 else COLOR_TEXTO)
    write(f"  Moral    {barra_img(personaje.moral)}",
          COLOR_ROJO if personaje.moral < 30 else COLOR_TEXTO)

    write("─" * 50, COLOR_SEP)
    write("  INVENTARIO  "
          f"({personaje.peso_actual():.1f}/{personaje.peso_max}kg)", COLOR_AMARILLO, bold=True)

    for item in personaje.inventario[:8]:
        cant = f" x{item.get('cantidad','')}" if item.get('cantidad',1)>1 else ""
        write(f"    {item['nombre']}{cant}", COLOR_TEXTO, indent=0)

    if len(personaje.inventario) > 8:
        write(f"    ...y {len(personaje.inventario)-8} objetos más.", COLOR_DIM)

    write("═" * 50, COLOR_SEP)

    img.save(ruta_salida, "PNG", optimize=True)
    return ruta_salida
