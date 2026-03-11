from ui.tui import (
    console, limpiar, pausa, barra_vital,
    leer_cmd, es_salida, footer_volver,
    COLOR_OK, COLOR_WARN, COLOR_DANGER, COLOR_INFO, COLOR_DIM, COLOR_ACCENT,
)
from ui.hud import _mostrar_resumen_skills, _mostrar_todas_skills
from rich.table import Table
from rich.text  import Text
from rich       import box


def pantalla_ficha(personaje):
    from data.rasgos  import RASGOS
    from data.stats   import STATS

    limpiar()
    console.print(f"\n[bold {COLOR_ACCENT}]  FICHA — {personaje.nombre} {personaje.apellido}[/bold {COLOR_ACCENT}]")
    console.print(f"  [{COLOR_DIM}]{'─' * 56}[/{COLOR_DIM}]")

    # Stats en tabla rich dos columnas
    console.print(f"  [{COLOR_WARN}]ESTADÍSTICAS[/{COLOR_WARN}]")
    t_stats = Table(box=None, show_header=False, padding=(0, 1), expand=False)
    t_stats.add_column(width=18)
    t_stats.add_column(width=16)
    t_stats.add_column(width=3, justify="right")
    t_stats.add_column(width=18)
    t_stats.add_column(width=16)
    t_stats.add_column(width=3, justify="right")

    cols = list(personaje.stats.items())
    mid  = (len(cols) + 1) // 2
    for i in range(mid):
        k1, v1 = cols[i]
        n1     = STATS[k1].get("nombre", k1)
        if i + mid < len(cols):
            k2, v2 = cols[i + mid]
            n2     = STATS[k2].get("nombre", k2)
            t_stats.add_row(
                Text(n1, style=COLOR_INFO),
                barra_vital(v1 * 10),
                Text(str(v1), style=COLOR_DIM),
                Text(n2, style=COLOR_INFO),
                barra_vital(v2 * 10),
                Text(str(v2), style=COLOR_DIM),
            )
        else:
            t_stats.add_row(
                Text(n1, style=COLOR_INFO),
                barra_vital(v1 * 10),
                Text(str(v1), style=COLOR_DIM),
                Text(""), Text(""), Text(""),
            )
    console.print(t_stats)

    # Skills top con barra de XP
    console.print(f"\n  [{COLOR_WARN}]HABILIDADES[/{COLOR_WARN}]")
    _mostrar_resumen_skills(personaje, limite=8, incluir_xp=True)

    console.print(f"\n  [{COLOR_DIM}][v] Ver todas las skills[/{COLOR_DIM}]  {footer_volver()}")
    cmd = leer_cmd()
    if cmd == "v":
        _mostrar_todas_skills(personaje, incluir_xp=True)
        pausa()

    # Rasgos
    if personaje.rasgos:
        console.print(f"\n  [{COLOR_INFO}]RASGOS ACTIVOS[/{COLOR_INFO}]")
        for r in personaje.rasgos:
            if r in RASGOS:
                ras = RASGOS[r]
                console.print(
                    f"    {ras['icono']} [bold {COLOR_ACCENT}]{ras['nombre']:<22}[/bold {COLOR_ACCENT}]  "
                    f"[{COLOR_DIM}]{ras['descripcion']}[/{COLOR_DIM}]"
                )

    if personaje.condiciones_cronicas:
        console.print(f"\n  [{COLOR_WARN}]CONDICIONES CRÓNICAS[/{COLOR_WARN}]")
        for cc in personaje.condiciones_cronicas:
            console.print(
                f"    [{COLOR_DANGER}]• {cc.get('nombre','Condición')}[/{COLOR_DANGER}] "
                f"[{COLOR_DIM}]({cc.get('origen','origen desconocido')})[/{COLOR_DIM}]"
            )

    # Estadísticas de supervivencia
    console.print(f"\n  [{COLOR_DIM}]{'─' * 56}[/{COLOR_DIM}]")
    console.print(
        f"  [{COLOR_DIM}]Expediciones: {personaje.expediciones_completadas} | "
        f"Infectados: {personaje.infectados_eliminados} | "
        f"Bandidos: {personaje.bandidos_eliminados}[/{COLOR_DIM}]"
    )
    console.print(
        f"  [{COLOR_DIM}]Ítems recolectados: {personaje.items_recolectados} | "
        f"Condiciones graves: {personaje.veces_condicion_grave}[/{COLOR_DIM}]"
    )

    try:
        from engine.bitacora import exportar_perfil
        exportar_perfil(personaje, "saves/perfil.png")
        console.print(f"  [{COLOR_OK}]Perfil exportado → saves/perfil.png[/{COLOR_OK}]")
    except Exception:
        pass
    pausa()


def _pantalla_medicina(personaje):
    """Permite al jugador tratar condiciones crónicas con ítems médicos."""
    from engine.medical_system import intentar_tratamiento, items_tratamiento_disponibles

    while True:
        limpiar()
        condiciones = getattr(personaje, "condiciones_cronicas", [])

        console.print(f"\n[bold {COLOR_ACCENT}]  TRATAMIENTOS MÉDICOS[/bold {COLOR_ACCENT}]")
        console.print(f"  [{COLOR_DIM}]{'─' * 50}[/{COLOR_DIM}]")

        if not condiciones:
            console.print(f"\n  [{COLOR_OK}]No tienes condiciones crónicas activas.[/{COLOR_OK}]")
            pausa()
            return

        console.print(f"\n  [{COLOR_DANGER}]CONDICIONES ACTIVAS:[/{COLOR_DANGER}]")

        t_cond = Table(box=box.SIMPLE, border_style=COLOR_DIM, show_header=False)
        t_cond.add_column("#", width=4, justify="right")
        t_cond.add_column("Condición", min_width=30)
        t_cond.add_column("Sev.", width=8)
        t_cond.add_column("Origen", min_width=20)

        for i, c in enumerate(condiciones, 1):
            sev     = c.get("severidad", 1)
            sev_str = "●" * sev + "○" * (3 - min(sev, 3))
            t_cond.add_row(
                Text(str(i), style=COLOR_DIM),
                Text(c.get("nombre", "?"), style=COLOR_DANGER),
                Text(sev_str, style=COLOR_DANGER),
                Text(c.get("origen", "desconocido"), style=COLOR_DIM),
            )
        console.print(t_cond)

        items_disp = items_tratamiento_disponibles(personaje)
        if not items_disp:
            console.print(f"\n  [{COLOR_DIM}]No tienes ítems médicos. Necesitas: Botiquín, Antibióticos, etc.[/{COLOR_DIM}]")
            pausa()
            return

        console.print(f"\n  [{COLOR_OK}]ÍTEMS DISPONIBLES:[/{COLOR_OK}]")
        for j, item in enumerate(items_disp, 1):
            console.print(f"  [{COLOR_OK}][{j}][/{COLOR_OK}] {item}")

        console.print(f"\n  [{COLOR_DIM}]Escribe: [nº condición]-[nº ítem]  (ej: 1-2)[/{COLOR_DIM}]  {footer_volver()}")
        cmd = leer_cmd()

        if es_salida(cmd):
            return

        try:
            partes    = cmd.split("-")
            idx_cond  = int(partes[0]) - 1
            idx_item  = int(partes[1]) - 1
            if not (0 <= idx_cond < len(condiciones)) or not (0 <= idx_item < len(items_disp)):
                continue
            clave_cond  = condiciones[idx_cond]["clave"]
            nombre_item = items_disp[idx_item]
            resultado   = intentar_tratamiento(personaje, clave_cond, nombre_item)
            limpiar()
            col = COLOR_OK if resultado["exito"] else COLOR_DANGER
            console.print(f"\n  [{col}]{resultado['mensaje']}[/{col}]\n")
            pausa()
        except (ValueError, IndexError):
            continue
