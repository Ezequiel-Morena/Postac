import sys
import time

from ui.hud import mostrar_estado, _mostrar_advertencias
from ui.inventory import pantalla_inventario
from ui.survivors import pantalla_supervivientes
from ui.character import pantalla_ficha, _pantalla_medicina


def bucle_principal(personaje, opciones_pendientes=None):
    from engine.save_manager  import guardar
    from engine.mundo         import generar_opciones
    from engine.input_handler import getch, es_interactivo
    from ui.tui import (
        console, tabla_zonas, shortcuts_bar, limpiar,
        COLOR_DIM, COLOR_ACCENT, COLOR_OK, COLOR_WARN,
    )
    from rich.panel import Panel
    from rich.text  import Text

    if not opciones_pendientes:
        opciones_pendientes = generar_opciones(personaje, 4)

    seleccion_zona = 0

    SHORTCUTS = {
        "I": "Inventario", "F": "Ficha", "V": "Supervivientes",
        "A": "Almacén", "C": "Acciones", "R": "Ranking",
        "G": "Guardar", "Q": "Salir", "?": "Ayuda",
    }

    while True:
        if not personaje.esta_vivo():
            procesar_muerte(personaje, "heridas de combate")
            return

        limpiar()
        mostrar_estado(personaje)
        _mostrar_advertencias(personaje)

        tz = tabla_zonas(opciones_pendientes, personaje, seleccion=seleccion_zona)
        console.print(tz)

        console.print(Panel(
            shortcuts_bar(SHORTCUTS),
            border_style=COLOR_DIM,
            padding=(0, 1),
        ))
        console.print(
            f"  [{COLOR_DIM}][↑↓] navegar zonas  [Enter] ir · [0] descansar  "
            f"[Esc] guardar+salir[/{COLOR_DIM}]"
        )

        if es_interactivo():
            k = getch()
        else:
            k = input("  > ").strip().lower()

        # ── Navegación de zonas con flechas ────────────────────
        if k == "up":
            seleccion_zona = (seleccion_zona - 1) % (len(opciones_pendientes) + 1)
            continue
        elif k == "down":
            seleccion_zona = (seleccion_zona + 1) % (len(opciones_pendientes) + 1)
            continue
        elif k == "enter":
            if seleccion_zona == len(opciones_pendientes):
                _ejecutar_descanso_interactivo(personaje, opciones_pendientes)
            elif 0 <= seleccion_zona < len(opciones_pendientes):
                _procesar_eleccion_expedicion(
                    str(seleccion_zona + 1), personaje, opciones_pendientes
                )
                seleccion_zona = 0
            continue

        # ── Esc: guardar y salir ───────────────────────────────
        elif k == "esc":
            guardar(personaje, opciones_pendientes)
            console.print(f"\n  [{COLOR_OK}]Guardado. Hasta la próxima.[/{COLOR_OK}]\n")
            sys.exit(0)

        # ── Comandos de una letra ──────────────────────────────
        elif k in ("q",):
            guardar(personaje, opciones_pendientes)
            sys.exit(0)

        elif k == "g":
            guardar(personaje, opciones_pendientes)
            console.print(f"  [{COLOR_OK}]✔ Guardado.[/{COLOR_OK}]")
            time.sleep(0.5)

        elif k == "i":
            pantalla_inventario(personaje)

        elif k == "f":
            pantalla_ficha(personaje)

        elif k == "v":
            pantalla_supervivientes(personaje)

        elif k == "m":
            _pantalla_medicina(personaje)

        elif k == "a":
            from ui.almacen import pantalla_almacen
            pantalla_almacen(personaje)

        elif k == "c":
            from ui.acciones import pantalla_acciones_refugio
            pantalla_acciones_refugio(personaje, opciones_pendientes)

        elif k == "s":
            _accion_auto_supervivencia(personaje, opciones_pendientes)

        elif k == "r":
            from ui.tui import render_leaderboard, pausa
            limpiar()
            console.print(render_leaderboard(15))
            pausa()

        elif k == "?":
            from ui.menus import _pantalla_ayuda_rapida
            _pantalla_ayuda_rapida()

        elif k == "h":
            from ui.menus import pantalla_historias
            pantalla_historias()

        elif k == "0":
            _ejecutar_descanso_interactivo(personaje, opciones_pendientes)
            seleccion_zona = 0

        elif k.isdigit():
            n = int(k)
            if 1 <= n <= len(opciones_pendientes):
                seleccion_zona = n - 1
                _procesar_eleccion_expedicion(k, personaje, opciones_pendientes)
                seleccion_zona = 0


def _ejecutar_descanso_interactivo(personaje, opciones):
    from engine.save_manager import guardar
    from engine.tick         import ejecutar_descanso
    from ui.tui import console, limpiar, pausa, COLOR_OK, COLOR_WARN, COLOR_DANGER, COLOR_DIM, COLOR_INFO

    salud_antes  = personaje.salud
    hambre_antes = personaje.hambre
    sed_antes    = personaje.sed
    fatiga_antes = personaje.fatiga

    limpiar()
    console.print(f"\n  [{COLOR_OK}]DESCANSO EN REFUGIO[/{COLOR_OK}]\n")
    resultado = ejecutar_descanso(personaje)

    almacen = getattr(personaje, "almacen", [])
    from engine.almacen import consumir_tipo
    if personaje.sed < 70:
        items = consumir_tipo(almacen, "agua", 1)
        if items:
            personaje.sed = min(100, personaje.sed + 35)
    if personaje.hambre < 70:
        items = consumir_tipo(almacen, "comida", 1)
        if items:
            personaje.hambre = min(100, personaje.hambre + 35)

    console.print(
        f"  [{COLOR_INFO}]Estado:[/{COLOR_INFO}] "
        f"Salud {salud_antes}→{personaje.salud} | "
        f"Hambre {hambre_antes}→{personaje.hambre} | "
        f"Sed {sed_antes}→{personaje.sed} | "
        f"Fatiga {fatiga_antes}→{personaje.fatiga}"
    )

    for linea in resultado.log_descanso:
        console.print(f"  [{COLOR_DIM}]{linea}[/{COLOR_DIM}]")

    if resultado.progreso_skills:
        console.print(f"\n  [{COLOR_OK}]↑ PROGRESO DE HABILIDADES[/{COLOR_OK}]")
        for msg in resultado.progreso_skills:
            console.print(f"  [{COLOR_OK}]  {msg}[/{COLOR_OK}]")

    if resultado.penalizaciones_tick:
        for msg in resultado.penalizaciones_tick:
            console.print(f"  [{COLOR_DANGER}]  {msg}[/{COLOR_DANGER}]")

    guardar(personaje, opciones)
    pausa()


def _procesar_eleccion_expedicion(cmd: str, personaje, opciones: list):
    if not cmd.isdigit():
        return
    _lanzar_expedicion(cmd, personaje, opciones)


def _lanzar_expedicion(cmd: str, personaje, opciones: list):
    from engine.save_manager  import guardar
    from engine.mundo         import generar_opciones
    from engine.tick          import ejecutar_expedicion
    from engine.input_handler import confirmar, es_interactivo
    from engine.decision_support import (
        confirmar_salida_expedicion,
        diagnosticar_supervivencia,
    )
    from ui.tui import console, limpiar, pausa, COLOR_OK, COLOR_WARN, COLOR_INFO, COLOR_DIM

    idx = int(cmd) - 1
    if not (0 <= idx < len(opciones)):
        return

    area = opciones[idx]

    if es_interactivo():
        diag = diagnosticar_supervivencia(personaje)
        console.print(f"\n  [{COLOR_WARN}]Confirmación táctica[/{COLOR_WARN}]")
        console.print(
            f"  [{COLOR_INFO}]Zona: {area['nombre']} | Peligro {area['peligro']}/5 | "
            f"~{area.get('duracion_h','?')}h[/{COLOR_INFO}]"
        )
        console.print(
            f"  [{COLOR_INFO}]Estado: {diag.nivel.upper()} — {diag.recomendacion}[/{COLOR_INFO}]"
        )

    if not confirmar_salida_expedicion(personaje, area, es_interactivo, confirmar):
        return

    limpiar()
    console.print(f"\n  [{COLOR_OK}]EXPEDICIÓN → {area['nombre']}[/{COLOR_OK}]")
    console.print(
        f"  [{COLOR_DIM}]Peligro: {area['peligro']}/5 | ~{area['duracion_h']}h | "
        f"{area.get('distancia_km','?')}km[/{COLOR_DIM}]\n"
    )
    time.sleep(0.4)

    resultado = ejecutar_expedicion(personaje, area, exportar_img=True)
    console.print(resultado.log_terminal)

    if resultado.ruta_imagen:
        console.print(f"  [{COLOR_OK}]📷  {resultado.ruta_imagen}[/{COLOR_OK}]")

    nuevas = generar_opciones(personaje, 4)
    guardar(personaje, nuevas, hacer_backup=True)

    if not personaje.esta_vivo():
        pausa()
        procesar_muerte(personaje, resultado.causa_muerte or "expedición fatal")
        return

    opciones.clear()
    opciones.extend(nuevas)
    pausa()


def _accion_auto_supervivencia(personaje, opciones_pendientes):
    from engine.save_manager import guardar
    from engine.decision_support import aplicar_auto_supervivencia
    from ui.tui import console, limpiar, pausa, COLOR_OK, COLOR_WARN, COLOR_DIM

    limpiar()
    console.print(f"\n  [{COLOR_WARN}]AUTO-SUPERVIVENCIA[/{COLOR_WARN}]\n")
    acciones = aplicar_auto_supervivencia(personaje)

    if acciones:
        for a in acciones:
            console.print(f"  [{COLOR_OK}]✔ {a}[/{COLOR_OK}]")
        guardar(personaje, opciones_pendientes)
        console.print(f"\n  [{COLOR_DIM}]Estado actualizado y guardado.[/{COLOR_DIM}]")
    else:
        console.print(f"  [{COLOR_DIM}]No se encontró consumo útil para el estado actual.[/{COLOR_DIM}]")
    pausa()


def procesar_muerte(personaje, causa: str = "desconocida"):
    from engine.save_manager import registrar_muerte, borrar_guardado
    from ui.tui import console, limpiar, pausa, render_leaderboard, COLOR_DANGER, COLOR_WARN, COLOR_DIM

    limpiar()
    console.print(f"\n[bold {COLOR_DANGER}]  {'═' * 52}[/bold {COLOR_DANGER}]")
    console.print(f"[bold {COLOR_DANGER}]  {personaje.nombre} {personaje.apellido} HA CAÍDO[/bold {COLOR_DANGER}]")
    console.print(f"[bold {COLOR_DANGER}]  {'═' * 52}[/bold {COLOR_DANGER}]\n")

    console.print(f"  [{COLOR_DIM}]Sobrevivió    {personaje.dia} días[/{COLOR_DIM}]")
    console.print(f"  [{COLOR_DIM}]Expediciones  {personaje.expediciones_completadas}[/{COLOR_DIM}]")
    console.print(f"  [{COLOR_DIM}]Infectados    {personaje.infectados_eliminados}[/{COLOR_DIM}]")
    console.print(f"  [{COLOR_DIM}]Bandidos      {personaje.bandidos_eliminados}[/{COLOR_DIM}]")
    console.print(f"  [{COLOR_DIM}]Causa         {causa}[/{COLOR_DIM}]\n")

    pos = registrar_muerte(personaje, causa)
    console.print(f"  [{COLOR_WARN}]Posición en el ranking: #{pos}[/{COLOR_WARN}]")
    console.print(render_leaderboard(10))
    borrar_guardado()
    pausa("  [ENTER para volver al menú]")

    from ui.menus import menu_inicio
    result = menu_inicio()
    if result is None:
        sys.exit(0)
    personaje_nuevo, opciones = result
    bucle_principal(personaje_nuevo, opciones)
