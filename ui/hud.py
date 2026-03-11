# ============================================================
# ui/hud.py — HUD principal del personaje con rich
# ============================================================

from rich.panel import Panel
from rich.table import Table
from rich.text  import Text
from rich       import box

from ui.tui import (
    console, header_personaje, tabla_vitales,
    COLOR_OK, COLOR_WARN, COLOR_DANGER,
    COLOR_INFO, COLOR_DIM, COLOR_ACCENT, STYLE_HEADER,
    barra_vital,
)


def mostrar_estado(personaje):
    """Imprime el HUD completo del personaje usando rich."""
    from engine.clima import clima_actual

    p = personaje

    vitales = tabla_vitales(personaje)

    info_lines = []
    arma = p.arma_equipada()
    if arma:
        dmin, dmax = arma.get("daño", (1, 3))
        info_lines.append(
            f"[{COLOR_INFO}]Arma:[/{COLOR_INFO}] {arma.get('nombre','?')} "
            f"[{COLOR_DIM}]({dmin}-{dmax} dmg)[/{COLOR_DIM}]  "
            f"[{COLOR_INFO}]DEF:[/{COLOR_INFO}] {p.defensa_total()}"
        )
    else:
        bloq = p.mejor_arma_bloqueada()
        if bloq:
            motivo = p.motivo_bloqueo_arma(bloq)
            info_lines.append(f"[{COLOR_WARN}]{motivo}[/{COLOR_WARN}]")
        else:
            info_lines.append(f"[{COLOR_DIM}]Arma: puños  DEF: {p.defensa_total()}[/{COLOR_DIM}]")

    if p.condiciones:
        iconos = {1: "🟡", 2: "🟠", 3: "🔴"}
        conds = "  ".join(f"{iconos.get(c.severidad,'·')} {c.nombre}" for c in p.condiciones)
        info_lines.append(f"[{COLOR_DANGER}]{conds}[/{COLOR_DANGER}]")

    c = clima_actual(p.dia, p.hora, {"area_key": "refugio", "tags": ["interior"]})
    info_lines.append(
        f"[{COLOR_DIM}]{c['icono']} {c['nombre']} · {c['estacion']} · {c['temperatura_c']}°C[/{COLOR_DIM}]"
    )

    from engine.fuego import esta_encendido, combustible_disponible
    if esta_encendido(p):
        mins = int(combustible_disponible(p))
        info_lines.append(f"[{COLOR_OK}]🔥 Fuego activo ~{mins} min[/{COLOR_OK}]")

    if p.rasgos:
        from data.rasgos import RASGOS
        nombres = [RASGOS[r]["nombre"] for r in p.rasgos if r in RASGOS]
        info_lines.append(f"[{COLOR_INFO}]Rasgos: {', '.join(nombres)}[/{COLOR_INFO}]")

    layout = Table(box=None, padding=(0, 2), show_header=False, expand=True)
    layout.add_column(ratio=1)
    layout.add_column(ratio=1)

    info_text = Text.from_markup("\n".join(info_lines))
    layout.add_row(vitales, info_text)

    p_header = header_personaje(personaje)

    console.print(p_header)
    console.print(Panel(layout, border_style=COLOR_DIM, padding=(0, 1)))


def mostrar_opciones(opciones: list[dict], personaje) -> str:
    """Retorna string vacío — la tabla de zonas se imprime en game_loop."""
    return ""


def _mostrar_advertencias(personaje):
    """Advertencias críticas con rich."""
    from engine.decision_support import generar_alertas_supervivencia

    color_map = {
        "info":     COLOR_OK,
        "warning":  COLOR_WARN,
        "critical": COLOR_DANGER,
    }

    for nivel, msg in generar_alertas_supervivencia(personaje):
        col  = color_map.get(nivel, COLOR_DIM)
        pref = "▸" if nivel == "info" else "⚠"
        console.print(f"  [{col}]{pref} {msg}[/{col}]")


# ── Funciones de skills ─────────────────────────────────────

def _skills_ordenadas(personaje) -> list[tuple[str, int]]:
    return sorted(personaje.skills.items(), key=lambda kv: kv[1], reverse=True)


def _mostrar_resumen_skills(personaje, limite: int = 8, incluir_xp: bool = False) -> None:
    from data.skills import SKILLS

    t = Table(box=box.SIMPLE, border_style=COLOR_DIM, show_header=True,
              header_style=f"bold {COLOR_INFO}")
    t.add_column("Skill", min_width=20)
    t.add_column("Nv.", width=5, justify="right")
    t.add_column("Progreso", width=16)
    if incluir_xp:
        t.add_column("XP", width=10, justify="right")
    t.add_column("Cat.", width=12)

    for sk, val in _skills_ordenadas(personaje)[:limite]:
        info    = SKILLS.get(sk, {})
        nombre  = info.get("nombre", sk)
        icono   = info.get("icono", "")
        cat     = info.get("categoria", "")
        maestria = personaje.nivel_maestria_skill(sk)

        row = [
            f"{icono} {nombre}",
            Text(str(val), style=COLOR_OK if val >= 50 else COLOR_DIM),
            barra_vital(val),
        ]
        if incluir_xp:
            xp_cur = personaje.skills_xp.get(sk, 0)
            xp_req = personaje.xp_necesaria_skill(sk)
            row.append(Text(f"{xp_cur}/{xp_req}", style=COLOR_DIM))
        row.append(Text(f"{cat} {maestria}", style=COLOR_DIM))
        t.add_row(*row)

    console.print(t)


def _mostrar_todas_skills(personaje, incluir_xp: bool = False) -> None:
    _mostrar_resumen_skills(personaje, limite=9999, incluir_xp=incluir_xp)
