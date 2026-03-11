import sys
import time

from ui.tui import (
    console, limpiar, pausa, menu_rich,
    COLOR_OK, COLOR_WARN, COLOR_DANGER, COLOR_INFO, COLOR_DIM, COLOR_ACCENT,
)
from ui.hud import _mostrar_resumen_skills, _mostrar_todas_skills
from ui.colors import LOGO


def menu_inicio():
    """Returns (personaje, opciones_pendientes) or None if user chose to exit."""
    from engine.save_manager  import hay_guardado, info_guardado, borrar_guardado, cargar, eco_del_pasado
    from engine.input_handler import es_interactivo

    limpiar()
    console.print(LOGO)

    eco = eco_del_pasado()
    if eco:
        console.print(f"  [{COLOR_DIM}]{eco}[/{COLOR_DIM}]\n")

    info      = info_guardado() if hay_guardado() else None
    subtitulo = ""
    if info:
        subtitulo = (
            f"Partida activa: {info['nombre']}  —  Día {info['dia']} | "
            f"{info['expediciones']} expediciones"
        )

    opciones_menu = []
    if info:
        opciones_menu.append("Continuar partida")
    opciones_menu += [
        "Nueva partida",
        "Ranking de caídos",
        "Gestión de historias",
        "Salir",
    ]

    if es_interactivo():
        idx = menu_rich("MENÚ PRINCIPAL", opciones_menu, subtitulo=subtitulo)
        if idx == -1:
            idx = len(opciones_menu) - 1
        eleccion = opciones_menu[idx]
    else:
        for i, op in enumerate(opciones_menu, 1):
            print(f"  {i}. {op}")
        try:
            eleccion = opciones_menu[int(input("\n  > ").strip()) - 1]
        except (ValueError, IndexError):
            eleccion = "Salir"

    if eleccion == "Continuar partida":
        personaje, opciones = cargar()
        if personaje:
            return (personaje, opciones)
        else:
            console.print(f"  [{COLOR_DANGER}]Error al cargar la partida.[/{COLOR_DANGER}]")
            pausa()
            return menu_inicio()

    elif eleccion == "Nueva partida":
        if info:
            from engine.input_handler import confirmar
            if not confirmar("¿Borrar la partida actual y empezar de nuevo?"):
                return menu_inicio()
            borrar_guardado()
        personaje = pantalla_creacion()
        if personaje:
            from engine.save_manager import guardar
            guardar(personaje)
            return (personaje, None)
        else:
            return menu_inicio()

    elif eleccion == "Ranking de caídos":
        from ui.tui import render_leaderboard
        limpiar()
        console.print(render_leaderboard(15))
        pausa()
        return menu_inicio()

    elif eleccion == "Gestión de historias":
        pantalla_historias()
        return menu_inicio()

    elif eleccion == "Salir":
        console.print(f"\n  [{COLOR_DIM}]Que la suerte te acompañe, superviviente.[/{COLOR_DIM}]\n")
        return None


def pantalla_creacion():
    from engine.personaje     import Sobreviviente
    from engine.input_handler import es_interactivo
    from data.rasgos          import RASGOS
    from data.stats           import STATS

    limpiar()
    console.print(f"\n[{COLOR_WARN}]  GENERANDO NUEVO SUPERVIVIENTE...[/{COLOR_WARN}]\n")
    time.sleep(0.3)

    personaje = Sobreviviente()

    limpiar()
    sexo = "♂" if personaje.genero == "Masculino" else "♀"
    console.print(f"\n[bold {COLOR_ACCENT}]  NUEVO SUPERVIVIENTE[/bold {COLOR_ACCENT}]")
    console.print(f"  [{COLOR_DIM}]{'─' * 56}[/{COLOR_DIM}]")
    console.print(
        f"  [bold {COLOR_ACCENT}]{personaje.nombre} {personaje.apellido}[/bold {COLOR_ACCENT}]  "
        f"[{COLOR_DIM}]{sexo}  {personaje.edad} años[/{COLOR_DIM}]"
    )
    console.print(f"  [{COLOR_INFO}]{personaje.background['nombre']}[/{COLOR_INFO}]")
    console.print(f"  [{COLOR_DIM}]{personaje.background.get('descripcion', '')}[/{COLOR_DIM}]\n")

    # Stats en tabla rich
    from rich.table import Table
    from rich.text  import Text
    from ui.tui import barra_vital

    t_stats = Table(box=None, show_header=False, padding=(0, 1), expand=False)
    t_stats.add_column(width=18)
    t_stats.add_column(width=16)
    t_stats.add_column(width=3, justify="right")
    t_stats.add_column(width=18)
    t_stats.add_column(width=16)
    t_stats.add_column(width=3, justify="right")

    console.print(f"  [{COLOR_WARN}]ESTADÍSTICAS[/{COLOR_WARN}]")
    items_stats = list(personaje.stats.items())
    mitad       = (len(items_stats) + 1) // 2
    for i in range(mitad):
        k1, v1 = items_stats[i]
        n1     = STATS[k1].get("nombre", k1)
        if i + mitad < len(items_stats):
            k2, v2 = items_stats[i + mitad]
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

    # Skills
    console.print(f"\n  [{COLOR_WARN}]HABILIDADES[/{COLOR_WARN}]")
    _mostrar_resumen_skills(personaje, limite=6, incluir_xp=False)

    if es_interactivo():
        from ui.tui import leer_cmd, footer_volver
        console.print(f"\n  [{COLOR_DIM}][v] ver todas las skills[/{COLOR_DIM}]  {footer_volver()}")
        cmd = leer_cmd()
        if cmd == "v":
            _mostrar_todas_skills(personaje, incluir_xp=False)
            pausa()

    # Rasgos iniciales
    if personaje.rasgos:
        console.print(f"\n  [{COLOR_INFO}]RASGOS INICIALES[/{COLOR_INFO}]")
        for r in personaje.rasgos:
            if r in RASGOS:
                ras = RASGOS[r]
                console.print(
                    f"    {ras['icono']} [bold {COLOR_ACCENT}]{ras['nombre']}[/bold {COLOR_ACCENT}]: "
                    f"[{COLOR_DIM}]{ras['descripcion']}[/{COLOR_DIM}]"
                )

    # Inventario inicial
    console.print(f"\n  [{COLOR_OK}]EQUIPO INICIAL[/{COLOR_OK}]")
    for linea in personaje.listar_inventario():
        console.print(f"  [{COLOR_DIM}]{linea}[/{COLOR_DIM}]")

    console.print(f"\n  [{COLOR_DIM}]ID de partida: {personaje.partida_id}[/{COLOR_DIM}]")

    idx = menu_rich(
        "¿Aceptar este superviviente?",
        ["Sí, empezar con este personaje", "No, generar otro diferente"],
    )
    acepta = (idx == 0)

    return personaje if acepta else pantalla_creacion()


def pantalla_historias():
    """Menú de gestión de historias guardadas con navegación por teclado."""
    from engine.save_manager import (
        listar_historias, eliminar_bitacoras_historia,
        eliminar_entrada_leaderboard, eliminar_historia_completa,
        eliminar_todas_las_historias
    )
    from engine.input_handler import confirmar

    while True:
        limpiar()
        historias = listar_historias()

        console.print(f"\n[bold {COLOR_ACCENT}]  GESTIÓN DE HISTORIAS[/bold {COLOR_ACCENT}]")
        console.print(f"  [{COLOR_DIM}]Ubicación: saves/historias/[/{COLOR_DIM}]\n")

        if not historias:
            console.print(f"  [{COLOR_DIM}]No hay historias guardadas.[/{COLOR_DIM}]\n")
            opciones_globales = ["← Volver"]
        else:
            from rich.table import Table
            from rich.text import Text
            t = Table(border_style=COLOR_DIM, show_header=True,
                      header_style=f"bold {COLOR_INFO}")
            t.add_column("N", width=4, justify="right")
            t.add_column("Partida ID", min_width=36)
            t.add_column("Imgs", width=5, justify="right")
            t.add_column("MB", width=7, justify="right")
            for i, h in enumerate(historias, 1):
                t.add_row(
                    Text(str(i), style=COLOR_DIM),
                    Text(h["partida_id"][:35], style=COLOR_INFO),
                    Text(str(h["num_bitacoras"]), style=COLOR_DIM),
                    Text(f"{h['tamaño_mb']:.1f}", style=COLOR_DIM),
                )
            console.print(t)

            opciones_globales = [
                f"📂 Seleccionar historia ({len(historias)} disponibles)",
                "🧹 Borrar TODAS las bitácoras (conservar ranking)",
                "💀 Borrar TODO (bitácoras + ranking)",
                "← Volver",
            ]

        idx = menu_rich("GESTIÓN DE HISTORIAS", opciones_globales)

        if idx == -1 or opciones_globales[idx].startswith("←"):
            return

        if not historias:
            continue

        if idx == 0:
            _seleccionar_historia(historias, confirmar)
        elif idx == 1:
            if confirmar("¿Borrar TODAS las bitácoras? El ranking se conserva"):
                msg = eliminar_todas_las_historias(incluir_leaderboard=False)
                console.print(f"\n  [{COLOR_OK}]{msg}[/{COLOR_OK}]")
                pausa()
        elif idx == 2:
            if confirmar("¿Borrar TODO? Bitácoras Y ranking completo. Sin vuelta atrás"):
                msg = eliminar_todas_las_historias(incluir_leaderboard=True)
                console.print(f"\n  [{COLOR_OK}]{msg}[/{COLOR_OK}]")
                pausa()


def _seleccionar_historia(historias: list[dict], confirmar) -> None:
    """Submenú: elegir una historia y luego qué hacer con ella."""
    from engine.save_manager import (
        eliminar_bitacoras_historia,
        eliminar_entrada_leaderboard,
        eliminar_historia_completa,
    )

    nombres = [
        f"{h['partida_id'][:35]}  ({h['num_bitacoras']} imgs, {h['tamaño_mb']:.1f} MB)"
        for h in historias
    ]
    nombres.append("← Volver")

    idx = menu_rich("Seleccionar historia", nombres)
    if idx == -1 or idx == len(historias):
        return

    h = historias[idx]
    pid = h["partida_id"]
    pid_short = pid[:32]

    acciones = [
        "🗑 Borrar bitácoras (conservar ranking)",
        "📊 Quitar del ranking (conservar bitácoras)",
        "💀 Eliminar TODO (bitácoras + ranking)",
        "← Volver",
    ]
    accion_idx = menu_rich(f"Acciones — {pid_short}", acciones)
    if accion_idx == -1 or accion_idx == 3:
        return

    if accion_idx == 0:
        if confirmar(f"¿Borrar bitácoras de '{pid_short}'?"):
            ok, msg = eliminar_bitacoras_historia(pid)
            col = COLOR_OK if ok else COLOR_DANGER
            console.print(f"\n  [{col}]{msg}[/{col}]")
            pausa()
    elif accion_idx == 1:
        if confirmar(f"¿Quitar '{pid_short}' del ranking?"):
            ok, msg = eliminar_entrada_leaderboard(pid)
            col = COLOR_OK if ok else COLOR_DANGER
            console.print(f"\n  [{col}]{msg}[/{col}]")
            pausa()
    elif accion_idx == 2:
        if confirmar(f"¿Eliminar TODO de '{pid_short}'? (bitácoras + ranking)"):
            ok, msg = eliminar_historia_completa(pid)
            col = COLOR_OK if ok else COLOR_DANGER
            console.print(f"\n  [{col}]{msg}[/{col}]")
            pausa()


def _pantalla_ayuda_rapida():
    limpiar()
    console.print(f"\n[bold {COLOR_ACCENT}]  AYUDA RÁPIDA[/bold {COLOR_ACCENT}]")
    console.print(f"  [{COLOR_DIM}]{'─' * 54}[/{COLOR_DIM}]")
    console.print(f"  [{COLOR_INFO}]Decisiones de tick:[/{COLOR_INFO}]")
    console.print(f"  [{COLOR_DIM}]1..N expedición | 0 descanso | flechas ↑↓ navegar | Enter confirmar[/{COLOR_DIM}]")
    console.print(f"\n  [{COLOR_INFO}]Comandos útiles:[/{COLOR_INFO}]")
    console.print(f"  [{COLOR_DIM}][a] almacén  [s] auto-supervivencia  [i] inventario  [f] ficha  [g] guardar[/{COLOR_DIM}]")
    console.print(f"  [{COLOR_DIM}][Esc] guardar y salir[/{COLOR_DIM}]")
    console.print(f"\n  [{COLOR_INFO}]Criterio práctico:[/{COLOR_INFO}]")
    console.print(f"  [{COLOR_DIM}]Si salud <35%, sed >80 o fatiga >85, descansar suele ser mejor que arriesgar.[/{COLOR_DIM}]")
    pausa()
