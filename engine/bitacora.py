# ============================================================
# engine/bitacora.py — Bitácora narrativa y exportación PNG
# ============================================================
import os
import random
import textwrap
from pathlib import Path


# ── Colores ANSI ──────────────────────────────────────────────
R   = "\033[0m"
VE  = "\033[92m"
RO  = "\033[91m"
AM  = "\033[93m"
CI  = "\033[96m"
GR  = "\033[90m"
BL  = "\033[97m"
NE  = "\033[1m"

COLOR_TIPO = {
    "normal":          BL,
    "combate":         RO,
    "combate_detalle": "\033[38;5;203m",
    "evento":          CI,
    "evento_especial": AM,
    "evento_detalle":  GR,
    "loot":            VE,
    "loot_vacio":      GR,
    "aviso":           AM,
    "critico":         "\033[38;5;196m",
    "fin":             "\033[38;5;82m",
}


class Bitacora:
    def __init__(self, personaje):
        self.personaje   = personaje
        self.entradas:   list[dict] = []
        self.hora_actual = personaje.hora
        self.dia         = personaje.dia

    def _hora_str(self) -> str:
        h = self.hora_actual % 24
        return f"{h:02d}:{random.randint(0,5)}{random.randint(0,9)}"

    def _tick_hora(self, minutos: int = 30):
        self.hora_actual = (self.hora_actual + minutos // 60) % 24

    def entrada(self, texto: str, tipo: str = "normal"):
        self.entradas.append({"hora": self._hora_str(), "texto": texto, "tipo": tipo})
        self._tick_hora(random.randint(15, 45))

    def log_combate(self, resultado):
        self.entrada(f"COMBATE — {resultado.enemigo_nombre}", "combate")
        for linea in resultado.log:
            if linea.strip():
                self.entradas.append({"hora": "    ", "texto": linea.strip(),
                                       "tipo": "combate_detalle"})

    def log_evento(self, resultado):
        tipo = ("evento_especial"
                if resultado.tipo in ("hallazgo_especial", "npc_dilema")
                else "evento")
        self.entrada(resultado.titulo, tipo)
        for linea in resultado.log:
            if linea.strip() and "📍" not in linea:
                self.entradas.append({"hora": "    ", "texto": linea.strip(),
                                       "tipo": "evento_detalle"})

    def log_loot(self, items: list[dict]):
        if not items:
            self.entrada("Registrando... Nada de valor esta vez.", "loot_vacio")
            return
        nombres = [i["nombre"] for i in items]
        if len(nombres) == 1:
            self.entrada(f"Encontrado: {nombres[0]}", "loot")
        elif len(nombres) <= 3:
            self.entrada(f"Encontrado: {', '.join(nombres)}", "loot")
        else:
            self.entrada(f"Buena cosecha: {', '.join(nombres[:3])} "
                          f"y {len(nombres)-3} más.", "loot")

    def estado_critico(self, tipo: str):
        msgs = {
            "salud_baja": "Estoy en mal estado. Necesito curarme pronto.",
            "hambre":     "El hambre empieza a nublar el juicio.",
            "sed":        "La sed se vuelve desesperante.",
            "radiacion":  "Noto síntomas raros. Debo salir de aquí.",
            "moral_baja": "Es difícil encontrar razones para seguir.",
        }
        if tipo in msgs:
            self.entrada(msgs[tipo], "critico")

    def fin(self, area_nombre: str, exito: bool):
        frases_ok = [
            f"Regreso al refugio. Expedición a {area_nombre} completada.",
            f"De vuelta. {area_nombre} no fue fácil, pero salí vivo/a.",
        ]
        frases_fail = [
            f"Aborté la expedición a {area_nombre}. No valía el riesgo.",
            f"Salida forzada de {area_nombre}. Suerte que escapé.",
        ]
        self.entrada(random.choice(frases_ok if exito else frases_fail), "fin")


# ──────────────────────────────────────────────────────────────
#  RENDERIZADO TERMINAL
# ──────────────────────────────────────────────────────────────
def render_terminal(bitacora: Bitacora, personaje,
                    loot_total: list[dict]) -> str:
    from data.rasgos import RASGOS
    lineas = []
    sep = "═" * 62

    lineas.append(f"\n{VE}{NE}{sep}")
    lineas.append(f"  BITÁCORA — DÍA {bitacora.dia}")
    lineas.append(f"  {personaje.nombre} {personaje.apellido} | "
                   f"{personaje.background['nombre']}")
    lineas.append(sep + R)

    for e in bitacora.entradas:
        hora  = e["hora"]
        texto = e["texto"]
        tipo  = e.get("tipo", "normal")
        col   = COLOR_TIPO.get(tipo, BL)
        if tipo in ("combate_detalle", "evento_detalle"):
            lineas.append(f"{GR}       {texto}{R}")
        else:
            lineas.append(f"{col}  [{hora}] {texto}{R}")

    lineas.append(f"\n{AM}{NE}{'─'*62}")
    lineas.append("  RESUMEN")
    lineas.append("─" * 62 + R)

    p = personaje
    def barra(v, m, w=12):
        ll = int((v / max(1, m)) * w)
        return f"[{'█'*ll}{'░'*(w-ll)}]"

    sp  = p.salud / p.salud_max * 100
    cs  = VE if sp >= 60 else (AM if sp >= 30 else RO)
    lineas.append(f"  Salud     {cs}{barra(p.salud,p.salud_max)} "
                   f"{p.salud}/{p.salud_max}{R}")
    ch  = VE if p.hambre < 50 else (AM if p.hambre < 75 else RO)
    lineas.append(f"  Hambre    {ch}{barra(100-p.hambre,100)} {p.hambre}/100{R}")
    cs2 = VE if p.sed < 50 else (AM if p.sed < 75 else RO)
    lineas.append(f"  Sed       {cs2}{barra(100-p.sed,100)} {p.sed}/100{R}")
    cf  = VE if p.fatiga < 50 else (AM if p.fatiga < 75 else RO)
    lineas.append(f"  Fatiga    {cf}{barra(100-p.fatiga,100)} {p.fatiga}/100{R}")
    cm  = VE if p.moral >= 60 else (AM if p.moral >= 30 else RO)
    lineas.append(f"  Moral     {cm}{barra(p.moral,100)} {p.moral}/100{R}")
    if p.radiacion > 0:
        lineas.append(f"  Radiación {RO}{barra(p.radiacion,100)} "
                       f"{p.radiacion}/100 ☢{R}")

    if loot_total:
        lineas.append(f"\n{VE}  Objetos recolectados ({len(loot_total)}):{R}")
        for item in loot_total:
            cant = f" x{item.get('cantidad','')}" if item.get("cantidad",1)>1 else ""
            lineas.append(f"    + {item['nombre']}{cant}")

    if p.condiciones:
        lineas.append(f"\n{RO}  ⚕ Condiciones activas:{R}")
        for c in p.condiciones:
            lineas.append(f"    • {c}")

    if p.rasgos:
        nombres = [RASGOS[r]["nombre"] for r in p.rasgos if r in RASGOS]
        lineas.append(f"\n{CI}  Rasgos: {', '.join(nombres)}{R}")

    lineas.append(f"{AM}{NE}{'═'*62}{R}\n")
    return "\n".join(lineas)


# ──────────────────────────────────────────────────────────────
#  TEXTO PLANO (para imagen)
# ──────────────────────────────────────────────────────────────
def render_texto_plano(bitacora: Bitacora, personaje,
                        loot_total: list[dict], area_nombre: str) -> str:
    from data.rasgos import RASGOS
    lineas = []
    sep = "=" * 56

    lineas += [sep, f"  BITÁCORA — DÍA {bitacora.dia}",
               f"  {personaje.nombre} {personaje.apellido} | "
               f"{personaje.background['nombre']}",
               f"  Expedición: {area_nombre}", sep, ""]

    for e in bitacora.entradas:
        hora  = e["hora"]
        texto = e["texto"]
        tipo  = e.get("tipo", "normal")
        if tipo in ("combate_detalle", "evento_detalle"):
            lineas.append(f"       {texto}")
        else:
            lineas.append(f"  [{hora}] {texto}")

    lineas += ["", "-"*56, "  ESTADO FINAL", "-"*56]
    p = personaje
    lineas.append(f"  Salud:   {p.salud}/{p.salud_max}  ({p.estado_salud_texto()})")
    lineas.append(f"  Hambre:  {p.hambre}/100{'  ¡CRÍTICO!' if p.hambre>80 else ''}")
    lineas.append(f"  Sed:     {p.sed}/100{'  ¡CRÍTICO!' if p.sed>80 else ''}")
    lineas.append(f"  Fatiga:  {p.fatiga}/100")
    lineas.append(f"  Moral:   {p.moral}/100")
    if p.radiacion > 0:
        lineas.append(f"  Radiación: {p.radiacion}/100 ☢")

    if loot_total:
        lineas += ["", f"  Objetos obtenidos: {len(loot_total)}"]
        for item in loot_total[:8]:
            cant = f" x{item.get('cantidad','')}" if item.get("cantidad",1)>1 else ""
            lineas.append(f"    + {item['nombre']}{cant}")
        if len(loot_total) > 8:
            lineas.append(f"    ...y {len(loot_total)-8} más.")

    if p.condiciones:
        lineas += ["", "  Condiciones:"]
        for c in p.condiciones:
            lineas.append(f"    • {c}")

    if p.rasgos:
        nombres = [RASGOS[r]["nombre"] for r in p.rasgos if r in RASGOS]
        lineas += ["", f"  Rasgos activos: {', '.join(nombres)}"]

    lineas += ["", sep,
               f"  Expediciones: {p.expediciones_completadas}  "
               f"Infectados: {p.infectados_eliminados}  "
               f"Bandidos: {p.bandidos_eliminados}", sep]

    return "\n".join(lineas)


# ──────────────────────────────────────────────────────────────
#  EXPORTAR PNG
# ──────────────────────────────────────────────────────────────
_FUENTES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    "/System/Library/Fonts/Monaco.ttf",
    "C:/Windows/Fonts/consola.ttf",
]
_FUENTES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
]


def _cargar_fuente(candidatas, size):
    from PIL import ImageFont
    for ruta in candidatas:
        if os.path.exists(ruta):
            try:
                return ImageFont.truetype(ruta, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _color_linea(linea: str) -> tuple:
    if any(k in linea for k in ["BITÁCORA", "RESUMEN", "===", "DÍA", "---"]):
        return (220, 200, 80)
    if any(k in linea for k in ["COMBATE", "INFECTADO", "BANDIDO", "✖",
                                  "daño", "hp", "golpea", "EMBOSCADA"]):
        return (220, 80, 80)
    if any(k in linea for k in ["Encontrado:", "Buena cosecha", "+", "obtenidos"]):
        return (140, 230, 100)
    if any(k in linea for k in ["📍", "EVENTO", "Encontraste", "Descubriste"]):
        return (80, 200, 200)
    if any(k in linea for k in ["Salud", "Hambre", "Sed", "Fatiga", "Moral",
                                  "Radiación", "Expediciones", "ESTADO"]):
        return (220, 200, 80)
    if any(k in linea for k in ["CRÍTICO", "Agonizante", "☢", "Condiciones"]):
        return (220, 80, 80)
    if linea.strip() == "" or all(c in "=-─═" for c in linea.strip() if c != " "):
        return (40, 80, 40)
    return (200, 210, 200)


def exportar_imagen(texto_plano: str, ruta_salida: str) -> str:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return ""

    font      = _cargar_fuente(_FUENTES, 16)
    font_bold = _cargar_fuente(_FUENTES_BOLD, 17)

    ANCHO = 900; MX = 40; MY = 40; LH = 22
    max_chars = (ANCHO - MX * 2) // 9

    lineas_raw = texto_plano.split("\n")
    lineas: list[str] = []
    for raw in lineas_raw:
        if len(raw) <= max_chars:
            lineas.append(raw)
        else:
            indent = len(raw) - len(raw.lstrip())
            for i, w in enumerate(textwrap.wrap(raw.strip(), max_chars - indent)):
                lineas.append(" " * indent + ("    " if i > 0 else "") + w)

    alto  = MY * 2 + len(lineas) * LH + 60
    img   = Image.new("RGB", (ANCHO, alto), color=(10, 12, 10))
    draw  = ImageDraw.Draw(img)
    draw.rectangle([2, 2, ANCHO-3, alto-3], outline=(30, 60, 30), width=2)

    # Ruido de terminal
    import random as _r
    for _ in range(400):
        draw.point((_r.randint(0,ANCHO-1), _r.randint(0,alto-1)), fill=(15,25,15))

    draw.text((ANCHO-165, alto-20), "DIARIO APOCALIPSIS v2.0",
              fill=(30, 60, 30), font=font)

    y = MY
    for linea in lineas:
        col  = _color_linea(linea)
        bold = any(k in linea for k in ["BITÁCORA", "RESUMEN", "ESTADO FINAL",
                                          "COMBATE —", "==="])
        draw.text((MX, y), linea, fill=col, font=font_bold if bold else font)
        y += LH

    img.save(ruta_salida, "PNG", optimize=True)
    return ruta_salida


def exportar_perfil(personaje, ruta_salida: str) -> str:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return ""
    from data.rasgos import RASGOS
    from data.stats  import STATS
    from data.skills import SKILLS

    font      = _cargar_fuente(_FUENTES, 17)
    font_bold = _cargar_fuente(_FUENTES_BOLD, 19)
    font_sm   = _cargar_fuente(_FUENTES, 14)

    W, H = 700, 560
    img  = Image.new("RGB", (W, H), color=(10, 12, 10))
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, W-3, H-3], outline=(40, 90, 40), width=2)

    y = 28
    def wr(texto, color=(140,230,100), bold=False, indent=0):
        nonlocal y
        draw.text((28+indent, y), texto, fill=color, font=font_bold if bold else font)
        y += 26

    sexo = "♂" if personaje.genero == "Masculino" else "♀"
    wr("═"*52, (40,80,40))
    wr("  FICHA DE SUPERVIVIENTE", (220,200,80), bold=True)
    wr("═"*52, (40,80,40))
    wr(f"  {personaje.nombre} {personaje.apellido}  {sexo}  {personaje.edad} años",
       (200,210,200), bold=True)
    wr(f"  {personaje.background['nombre']}", (80,200,200))
    wr(f"  Día {personaje.dia} — {personaje.hora:02d}:00hs  "
       f"| Exp: {personaje.expediciones_completadas}", (100,130,100))
    wr("─"*52, (40,80,40))

    wr("  ESTADÍSTICAS", (220,200,80), bold=True)
    fila = "  " + "   ".join(
        f"{STATS[k]['abrev']}:{personaje.stats[k]:2d}"
        for k in STATS
    )
    wr(fila, (140,230,100))

    wr("─"*52, (40,80,40))
    wr("  VITALES", (220,200,80), bold=True)

    def barra_img(v, m=100, w=15):
        ll = int((v/max(1,m))*w)
        return f"[{'█'*ll}{'░'*(w-ll)}] {v}/{m}"

    cs = (140,230,100) if personaje.salud > 50 else ((220,200,80) if personaje.salud > 25 else (220,80,80))
    wr(f"  Salud   {barra_img(personaje.salud, personaje.salud_max)}", cs)
    wr(f"  Hambre  {barra_img(100-personaje.hambre)}",
       (220,80,80) if personaje.hambre>70 else (140,230,100))
    wr(f"  Sed     {barra_img(100-personaje.sed)}",
       (220,80,80) if personaje.sed>70 else (140,230,100))
    wr(f"  Moral   {barra_img(personaje.moral)}",
       (220,80,80) if personaje.moral<30 else (140,230,100))

    wr("─"*52, (40,80,40))
    wr(f"  INVENTARIO  ({personaje.peso_actual():.1f}/{personaje.peso_max}kg)",
       (220,200,80), bold=True)
    for item in personaje.inventario[:7]:
        cant = f" x{item.get('cantidad','')}" if item.get("cantidad",1)>1 else ""
        draw.text((40, y), f"    {item['nombre']}{cant}", fill=(140,230,100), font=font_sm)
        y += 22
    if len(personaje.inventario) > 7:
        draw.text((40, y), f"    ...y {len(personaje.inventario)-7} más.",
                  fill=(100,130,100), font=font_sm)
        y += 22

    if personaje.rasgos:
        y += 4
        draw.text((28, y), "─"*52, fill=(40,80,40), font=font); y+=22
        draw.text((28, y), "  RASGOS", fill=(220,200,80), font=font_bold); y+=26
        nombres = [RASGOS[r]["nombre"] for r in personaje.rasgos if r in RASGOS]
        draw.text((28, y), "  " + ", ".join(nombres), fill=(80,200,200), font=font_sm)
        y += 22

    wr("═"*52, (40,80,40))
    img.save(ruta_salida, "PNG", optimize=True)
    return ruta_salida


import textwrap  # necesario para exportar_imagen
