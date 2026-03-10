#!/usr/bin/env python3
# ============================================================
# main.py — POSTAC: Simulador de Supervivencia Post-Apocalíptica
#
# Responsabilidades:
#   - Presentación (colores, layouts, mensajes al jugador)
#   - Input del jugador (texto + navegación por teclado)
#   - Orquestación de ticks (llama a engine/tick.py)
#
# La lógica de simulación vive en engine/. Este archivo
# NO contiene lógica de juego.
# ============================================================

import sys
import time
import os

# ── Colores ANSI ──────────────────────────────────────────────
R   = "\033[0m"
VE  = "\033[92m"
RO  = "\033[91m"
AM  = "\033[93m"
CI  = "\033[96m"
GR  = "\033[90m"
BL  = "\033[97m"
NE  = "\033[1m"
DIM = "\033[2m"

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


# ──────────────────────────────────────────────────────────────
#  HUD — ESTADO DEL PERSONAJE
# ──────────────────────────────────────────────────────────────

def mostrar_estado(personaje):
    """Panel de estado compacto."""
    p   = personaje
    sep = f"  {GR}{'─' * 60}{R}"

    def barra(v, m, w=10):
        ll = int((v / max(1, m)) * w)
        return "█" * ll + "░" * (w - ll)

    def cvital(v, inv=False):
        # inv=True: valor alto es malo (hambre, sed, fatiga)
        if inv:
            return RO if v > 80 else (AM if v > 55 else VE)
        return RO if v < 25 else (AM if v < 50 else VE)

    sexo = "♂" if p.genero == "Masculino" else "♀"
    print(sep)
    print(f"  {BL}{NE}{p.nombre} {p.apellido}{R}  "
          f"{GR}{sexo} {p.edad}a · {p.background['nombre']} · Día {p.dia} {p.hora:02d}:00hs{R}")

    cs = cvital(p.salud / p.salud_max * 100)
    print(
        f"  {cs}❤  {barra(p.salud, p.salud_max):10} {p.salud:3d}/{p.salud_max}{R}  "
        f"{cvital(p.hambre, inv=True)}🍖  {barra(100-p.hambre, 100):10} {100-p.hambre:3d}/100{R}  "
        f"{cvital(p.sed, inv=True)}💧 {barra(100-p.sed, 100):10} {100-p.sed:3d}/100{R}"
    )
    print(
        f"  {cvital(p.fatiga, inv=True)}⚡  {barra(100-p.fatiga, 100):10} {100-p.fatiga:3d}/100{R}  "
        f"{cvital(p.moral)}🧠  {barra(p.moral, 100):10} {p.moral:3d}/100{R}  "
        + (f"{RO}☢  {barra(p.radiacion, 100):10} {p.radiacion:3d}/100{R}" if p.radiacion > 0 else "")
    )

    if p.condiciones:
        iconos_sev = {1: "🟡", 2: "🟠", 3: "🔴"}
        conds = "  ".join(
            f"{iconos_sev.get(c.severidad, '·')} {c.nombre}" for c in p.condiciones
        )
        print(f"  {RO}Condiciones: {conds}{R}")

    if p.rasgos:
        from data.rasgos import RASGOS
        nombres = [RASGOS[r]["nombre"] for r in p.rasgos if r in RASGOS]
        print(f"  {CI}Rasgos: {', '.join(nombres)}{R}")

    print(sep)


# ──────────────────────────────────────────────────────────────
#  OPCIONES DE EXPEDICIÓN
# ──────────────────────────────────────────────────────────────

def mostrar_opciones(opciones: list[dict], personaje) -> str:
    lineas = [f"\n  {AM}{NE}¿A dónde vas?{R}"]
    for i, area in enumerate(opciones, 1):
        p_nivel = area.get("peligro", 1)
        barras  = "█" * p_nivel + "░" * (5 - p_nivel)
        col     = VE if p_nivel <= 1 else (AM if p_nivel <= 3 else RO)
        dist    = area.get("distancia_km", "?")
        dur     = area.get("duracion_h", "?")
        estado  = f" {GR}[visitada]{R}" if area["area_key"] in personaje.areas_visitadas else ""
        lineas.append(
            f"  {col}{NE}{i}.{R} {CI}{area['nombre']:<28}{R} "
            f"{col}[{barras}]{R} {GR}{dist}km ~{dur}h{R}{estado}"
        )
    lineas.append(f"\n  {GR}0.  Descansar en el refugio{R}")
    return "\n".join(lineas)


# ──────────────────────────────────────────────────────────────
#  INVENTARIO
# ──────────────────────────────────────────────────────────────

def pantalla_inventario(personaje):
    """
    Pantalla de inventario completa.

    Comandos de texto (siempre disponibles — compatible con bot/pipes):
      u <id|nombre>   — usar ítem
      d <id|nombre>   — descartar ítem
      i <id|nombre>   — inspeccionar ítem
      todo            — usa automáticamente toda la comida/agua/medicina

    Navegación interactiva (solo en terminal real):
      ↑↓ para moverse, Enter para submenú de acciones
    """
    from engine.input_handler import lista_navegable, confirmar, es_interactivo
    from engine.personaje     import _linea_item

    while True:
        cls()
        inv  = personaje.inventario
        peso = personaje.peso_actual()
        pmax = personaje.peso_max

        # ── Cabecera ────────────────────────────────────────────
        print(f"\n{AM}{NE}  ══ INVENTARIO  ({peso:.1f}/{pmax:.0f}kg) "
              f"{'█' * int(peso/pmax*20):20} ══{R}")
        print(f"  {GR}{'ID':>3}  {'':2} {'Nombre':<29} {'Cant':>5}   {'Peso':>5}{R}")
        print(f"  {GR}{'─' * 54}{R}")

        if not inv:
            print(f"  {DIM}  (vacío){R}")
        else:
            for linea in personaje.listar_inventario():
                print(f"  {CI}{linea}{R}")

        print(f"  {GR}{'─' * 54}{R}")
        print(f"\n  {AM}Comandos:{R}")
        print(f"  {GR}u <id>   usar ítem     {R}"
              f"  {GR}d <id>   descartar     {R}"
              f"  {GR}i <id>   inspeccionar{R}")
        print(f"  {GR}u <nombre>  busca por nombre parcial{R}")
        print(f"  {GR}todo     usa toda la comida/agua/medicina{R}")
        if es_interactivo() and inv:
            print(f"  {DIM}[↑↓ + Enter]  navegar visualmente{R}")
        print(f"  {GR}q / Enter   volver al juego{R}")

        from engine.input_handler import leer_entrada as _le
        cmd = _le(f"\n  {AM}> {R}").strip().lower()

        if cmd in ("q", ""):
            # Si hay terminal y hay ítems, ofrecer navegación ↑↓
            if es_interactivo() and inv and cmd == "":
                idx, accion = lista_navegable(
                    "INVENTARIO — Selecciona un ítem",
                    [l.strip() for l in personaje.listar_inventario()],
                    ["usar — consumir / equipar",
                     "descartar — tirar al suelo",
                     "inspeccionar — ver detalles"],
                    header=f"Carga {peso:.1f}/{pmax:.0f}kg"
                )
                if idx >= 0:
                    _accion_item(personaje, idx + 1, accion)
                    pausa()
                continue
            return

        if cmd == "todo":
            _usar_todo_consumible(personaje)
            pausa()
            continue

        partes = cmd.split(None, 1)
        if len(partes) < 2:
            print(f"  {RO}Uso: u 3  /  d 3  /  i 3  (número de la lista){R}")
            pausa()
            continue

        verbo, arg = partes[0], partes[1].strip()
        idx_num = _resolver_id(arg, personaje)

        if idx_num is None:
            print(f"  {RO}No encontrado: '{arg}'{R}")
            pausa()
            continue

        if verbo in ("u", "usar"):
            ok, msg = personaje.usar_item_por_id(idx_num)
            print(f"\n  {VE if ok else RO}{msg}{R}")
            pausa()

        elif verbo in ("d", "descartar", "drop"):
            item = personaje.obtener_item_por_id(idx_num)
            if item:
                if confirmar(f"¿Descartar '{item['nombre']}'? No se puede recuperar"):
                    ok, nombre = personaje.descartar_por_id(idx_num)
                    print(f"\n  {VE}Descartaste: {nombre}{R}" if ok else f"  {RO}Error{R}")
            pausa()

        elif verbo in ("i", "info", "inspeccionar"):
            _pantalla_inspeccion(personaje, idx_num)

        else:
            print(f"  {RO}Verbo desconocido: '{verbo}'. Usa u/d/i{R}")
            pausa()


def _resolver_id(arg: str, personaje) -> int | None:
    """Resuelve un argumento de comando: número o nombre parcial → ID 1-based."""
    if arg.isdigit():
        n = int(arg)
        return n if 1 <= n <= len(personaje.inventario) else None
    # Búsqueda por nombre parcial (case insensitive)
    for i, it in enumerate(personaje.inventario, 1):
        if arg in it.get("nombre", "").lower():
            return i
    return None


def _accion_item(personaje, idx_1: int, accion: str):
    from engine.input_handler import confirmar
    accion = accion.lower()
    if "usar" in accion:
        ok, msg = personaje.usar_item_por_id(idx_1)
        print(f"\n  {VE if ok else RO}{msg}{R}")
    elif "descartar" in accion:
        item = personaje.obtener_item_por_id(idx_1)
        if item and confirmar(f"¿Descartar '{item['nombre']}'?"):
            ok, nombre = personaje.descartar_por_id(idx_1)
            print(f"\n  {VE}Descartaste: {nombre}{R}" if ok else f"  {RO}Error{R}")
    elif "inspeccionar" in accion:
        _pantalla_inspeccion(personaje, idx_1)


def _pantalla_inspeccion(personaje, idx_1: int):
    info = personaje.info_item(idx_1)
    if not info:
        print(f"  {RO}ID inválido{R}"); pausa(); return

    cls()
    sep = "─" * 52
    print(f"\n{AM}{NE}  {info['icono']}  {info['nombre']}{R}")
    print(f"  {GR}{sep}{R}")
    print(f"  {GR}Tipo: {info['tipo']:<20} Peso: {info['peso']:.1f}kg   {info['qty_str']}{R}")
    print(f"\n  {BL}{info['desc']}{R}")
    if info["efectos"]:
        print(f"\n  {AM}Efectos:{R}")
        for linea in info["efectos"]:
            print(f"  {VE}{linea}{R}")
    print(f"\n  {GR}{sep}{R}")
    if info["usable"]:
        print(f"  {GR}[u] Usar ahora   [Enter] Volver{R}")
        cmd = input(f"  {AM}> {R}").strip().lower()
        if cmd == "u":
            ok, msg = personaje.usar_item_por_id(idx_1)
            print(f"\n  {VE if ok else RO}{msg}{R}")
    pausa()


def _usar_todo_consumible(personaje):
    """Consume automáticamente toda la comida, agua y medicina disponible."""
    usados = []
    for it in list(personaje.inventario):
        if it.get("tipo") in ("comida", "agua", "medicina"):
            ok, msg = personaje.usar_item(it["nombre"])
            if ok:
                usados.append(f"  {CI}{it['nombre']}{R}: {GR}{msg}{R}")
    if usados:
        print(f"\n  {VE}Usado:{R}")
        for u in usados:
            print(u)
    else:
        print(f"  {GR}Sin consumibles disponibles.{R}")


# ──────────────────────────────────────────────────────────────
#  GESTIÓN DE HISTORIAS
# ──────────────────────────────────────────────────────────────

def pantalla_historias():
    """
    Menú de gestión de historias guardadas.

    Opciones por historia:
      b <N>  — borra solo las bitácoras (libera disco), ranking intacto
      r <N>  — quita la entrada del ranking, bitácoras intactas
      x <N>  — elimina todo (bitácoras + ranking)

    Opciones globales:
      limpio  — borra TODAS las bitácoras de todas las partidas
      reset   — borra TODO (bitácoras + ranking completo)
    """
    from engine.save_manager import (
        listar_historias, eliminar_bitacoras_historia,
        eliminar_entrada_leaderboard, eliminar_historia_completa,
        eliminar_todas_las_historias
    )
    from engine.input_handler import confirmar

    while True:
        cls()
        historias = listar_historias()

        print(f"\n{AM}{NE}  ══ GESTIÓN DE HISTORIAS ══════════════════════════{R}")
        print(f"  {GR}Ubicación: saves/historias/{R}\n")

        if not historias:
            print(f"  {DIM}  No hay historias guardadas.{R}\n")
        else:
            print(f"  {GR}{'N':>3}  {'Partida ID':<36} {'Imgs':>5} {'MB':>6}{R}")
            print(f"  {GR}{'─' * 54}{R}")
            for i, h in enumerate(historias, 1):
                print(f"  {CI}{i:3d}  {h['partida_id'][:35]:<36}{R} "
                      f"{GR}{h['num_bitacoras']:>4}   {h['tamaño_mb']:>5.1f}{R}")
            print(f"  {GR}{'─' * 54}{R}")

        print(f"\n  {AM}Comandos por historia (N = número de la lista):{R}")
        print(f"  {GR}b <N>    borrar bitácoras (libera disco, ranking intacto){R}")
        print(f"  {GR}r <N>    quitar del ranking (bitácoras intactas){R}")
        print(f"  {GR}x <N>    eliminar TODO de esa partida{R}")
        print(f"\n  {AM}Comandos globales:{R}")
        print(f"  {GR}limpio   borrar TODAS las bitácoras (ranking se conserva){R}")
        print(f"  {GR}reset    borrar TODO — bitácoras + ranking completo{R}")
        print(f"  {GR}q / Enter   volver{R}")

        from engine.input_handler import leer_entrada as _le
        cmd = _le(f"\n  {AM}> {R}").strip().lower()

        if cmd in ("q", ""):
            return

        if cmd == "limpio":
            if confirmar("¿Borrar TODAS las bitácoras? El ranking se conserva"):
                msg = eliminar_todas_las_historias(incluir_leaderboard=False)
                print(f"\n  {VE}{msg}{R}")
                pausa()
            continue

        if cmd == "reset":
            if confirmar(
                "¿Borrar TODO? Bitácoras Y ranking completo. Sin vuelta atrás",
                default_no=True
            ):
                msg = eliminar_todas_las_historias(incluir_leaderboard=True)
                print(f"\n  {VE}{msg}{R}")
                pausa()
            continue

        partes = cmd.split(None, 1)
        if len(partes) < 2 or not partes[1].isdigit():
            print(f"  {RO}Uso: b 3   r 3   x 3  (número de la lista){R}")
            pausa()
            continue

        verbo   = partes[0]
        idx_num = int(partes[1]) - 1

        if not (0 <= idx_num < len(historias)):
            print(f"  {RO}Número fuera de rango (1–{len(historias)}){R}")
            pausa()
            continue

        pid = historias[idx_num]["partida_id"]

        if verbo == "b":
            if confirmar(f"¿Borrar bitácoras de '{pid[:32]}'? El ranking queda"):
                ok, msg = eliminar_bitacoras_historia(pid)
                print(f"\n  {VE if ok else RO}{msg}{R}")
                pausa()

        elif verbo == "r":
            if confirmar(f"¿Quitar '{pid[:32]}' del ranking?"):
                ok, msg = eliminar_entrada_leaderboard(pid)
                print(f"\n  {VE if ok else RO}{msg}{R}")
                pausa()

        elif verbo == "x":
            if confirmar(f"¿Eliminar TODO de '{pid[:32]}'? (bitácoras + ranking)"):
                ok, msg = eliminar_historia_completa(pid)
                print(f"\n  {VE if ok else RO}{msg}{R}")
                pausa()

        else:
            print(f"  {RO}Verbo desconocido: '{verbo}'.  Usa b / r / x{R}")
            pausa()


# ──────────────────────────────────────────────────────────────
#  MENÚ DE INICIO
# ──────────────────────────────────────────────────────────────

def menu_inicio():
    from engine.save_manager  import hay_guardado, info_guardado, borrar_guardado, cargar, mostrar_leaderboard
    from engine.input_handler import menu_navegable, leer_entrada, es_interactivo

    cls()
    print(LOGO)

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
        idx = menu_navegable("MENÚ PRINCIPAL", opciones_menu, subtitulo=subtitulo)
        if idx == -1:
            idx = len(opciones_menu) - 1   # ESC → Salir
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
            bucle_principal(personaje, opciones)
        else:
            print(f"  {RO}Error al cargar la partida.{R}")
            pausa()
            menu_inicio()

    elif eleccion == "Nueva partida":
        if info:
            from engine.input_handler import confirmar
            if not confirmar("¿Borrar la partida actual y empezar de nuevo?"):
                menu_inicio()
                return
            borrar_guardado()
        personaje = pantalla_creacion()
        if personaje:
            from engine.save_manager import guardar
            guardar(personaje)
            bucle_principal(personaje)
        else:
            menu_inicio()

    elif eleccion == "Ranking de caídos":
        cls()
        print(mostrar_leaderboard(15))
        pausa()
        menu_inicio()

    elif eleccion == "Gestión de historias":
        pantalla_historias()
        menu_inicio()

    elif eleccion == "Salir":
        print(f"\n  {GR}Que la suerte te acompañe, superviviente.{R}\n")
        sys.exit(0)


# ──────────────────────────────────────────────────────────────
#  CREACIÓN DE PERSONAJE
# ──────────────────────────────────────────────────────────────

def pantalla_creacion():
    from engine.personaje    import Sobreviviente
    from engine.input_handler import menu_navegable, leer_entrada, es_interactivo
    from data.rasgos          import RASGOS
    from data.stats           import STATS
    from data.skills          import SKILLS

    cls()
    print(f"\n{AM}{NE}  GENERANDO NUEVO SUPERVIVIENTE...{R}\n")
    time.sleep(0.3)

    personaje = Sobreviviente()

    cls()
    sexo = "♂" if personaje.genero == "Masculino" else "♀"
    print(f"\n{AM}{NE}  NUEVO SUPERVIVIENTE{R}")
    print(f"  {GR}{'─' * 56}{R}")
    print(f"  {BL}{NE}{personaje.nombre} {personaje.apellido}{R}  "
          f"{GR}{sexo}  {personaje.edad} años{R}")
    print(f"  {CI}{NE}{personaje.background['nombre']}{R}")
    print(f"  {GR}{personaje.background.get('descripcion', '')}{R}\n")

    # Stats en dos columnas
    print(f"  {AM}ESTADÍSTICAS{R}")
    items_stats = list(personaje.stats.items())
    mitad       = (len(items_stats) + 1) // 2
    for i in range(mitad):
        k1, v1 = items_stats[i]
        n1     = STATS[k1].get("nombre", k1)
        b1     = "█" * v1 + "░" * (10 - v1)
        if i + mitad < len(items_stats):
            k2, v2 = items_stats[i + mitad]
            n2     = STATS[k2].get("nombre", k2)
            b2     = "█" * v2 + "░" * (10 - v2)
            print(f"    {CI}{n1:<16}{R}[{b1}]{v1:2d}    {CI}{n2:<16}{R}[{b2}]{v2:2d}")
        else:
            print(f"    {CI}{n1:<16}{R}[{b1}]{v1:2d}")

    # Skills
    print(f"\n  {AM}HABILIDADES{R}")
    for sk, val in personaje.skills.items():
        defn  = SKILLS[sk]
        nivel = "█" * (val // 10) + "░" * (10 - val // 10)
        print(f"    {defn['icono']} {defn['nombre']:<22} [{nivel}] {val:3d}")

    # Rasgos iniciales
    if personaje.rasgos:
        print(f"\n  {CI}RASGOS INICIALES{R}")
        for r in personaje.rasgos:
            if r in RASGOS:
                ras = RASGOS[r]
                print(f"    {ras['icono']} {NE}{ras['nombre']}{R}: {GR}{ras['descripcion']}{R}")

    # Inventario inicial
    print(f"\n  {VE}EQUIPO INICIAL{R}")
    for linea in personaje.listar_inventario():
        print(f"  {GR}{linea}{R}")

    print(f"\n  {DIM}ID de partida: {personaje.partida_id}{R}")

    if es_interactivo():
        idx = menu_navegable(
            "¿Aceptar este superviviente?",
            ["Sí, empezar con este personaje", "No, generar otro diferente"],
            limpiar=False
        )
        acepta = (idx == 0)
    else:
        resp   = input(f"\n  {AM}¿Aceptar? [s/N]: {R}").strip().lower()
        acepta = (resp == "s")

    return personaje if acepta else pantalla_creacion()


# ──────────────────────────────────────────────────────────────
#  FICHA DE PERSONAJE
# ──────────────────────────────────────────────────────────────

def pantalla_ficha(personaje):
    from data.rasgos  import RASGOS
    from data.stats   import STATS
    from data.skills  import SKILLS

    cls()
    sep = "─" * 56
    print(f"\n{AM}{NE}  FICHA — {personaje.nombre} {personaje.apellido}{R}")
    print(f"  {GR}{sep}{R}")

    # Stats en dos columnas
    print(f"  {AM}ESTADÍSTICAS{R}")
    cols = list(personaje.stats.items())
    mid  = (len(cols) + 1) // 2
    for i in range(mid):
        k1, v1 = cols[i]
        n1     = STATS[k1].get("nombre", k1)
        b1     = "█" * v1 + "░" * (10 - v1)
        if i + mid < len(cols):
            k2, v2 = cols[i + mid]
            n2     = STATS[k2].get("nombre", k2)
            b2     = "█" * v2 + "░" * (10 - v2)
            print(f"    {CI}{n1:<16}{R}[{b1}]{v1:2d}    {CI}{n2:<16}{R}[{b2}]{v2:2d}")
        else:
            print(f"    {CI}{n1:<16}{R}[{b1}]{v1:2d}")

    # Skills con barra de XP
    print(f"\n  {AM}HABILIDADES{R}")
    for sk, val in personaje.skills.items():
        defn    = SKILLS[sk]
        xp      = personaje.skills_xp.get(sk, 0)
        xp_need = defn.get("xp_base", 10) + (val // 10) * defn.get("xp_incremento", 5)
        blen    = int((xp / max(1, xp_need)) * 12)
        bxp     = "█" * blen + "░" * (12 - blen)
        print(f"    {defn['icono']} {defn['nombre']:<22} {val:3d}  "
              f"{GR}xp:[{bxp}] {xp}/{xp_need}{R}")

    # Rasgos
    if personaje.rasgos:
        print(f"\n  {CI}RASGOS ACTIVOS{R}")
        for r in personaje.rasgos:
            if r in RASGOS:
                ras = RASGOS[r]
                print(f"    {ras['icono']} {NE}{ras['nombre']:<22}{R}  {GR}{ras['descripcion']}{R}")

    # Estadísticas de supervivencia
    print(f"\n  {GR}{'─' * 56}{R}")
    print(f"  {GR}Expediciones: {personaje.expediciones_completadas} | "
          f"Infectados: {personaje.infectados_eliminados} | "
          f"Bandidos: {personaje.bandidos_eliminados}{R}")
    print(f"  {GR}Ítems recolectados: {personaje.items_recolectados} | "
          f"Condiciones graves: {personaje.veces_condicion_grave}{R}")

    try:
        from engine.bitacora import exportar_perfil
        exportar_perfil(personaje, "saves/perfil.png")
        print(f"  {VE}Perfil exportado → saves/perfil.png{R}")
    except Exception:
        pass
    pausa()


# ──────────────────────────────────────────────────────────────
#  BUCLE PRINCIPAL DE JUEGO
# ──────────────────────────────────────────────────────────────

def bucle_principal(personaje, opciones_pendientes=None):
    from engine.save_manager  import guardar
    from engine.mundo         import generar_opciones
    from engine.tick          import ejecutar_expedicion, ejecutar_descanso
    from engine.input_handler import menu_navegable, leer_entrada, es_interactivo

    if not opciones_pendientes:
        opciones_pendientes = generar_opciones(personaje, 4)

    while True:
        if not personaje.esta_vivo():
            procesar_muerte(personaje, "heridas de combate")
            return

        cls()
        print(LOGO)
        mostrar_estado(personaje)
        print(mostrar_opciones(opciones_pendientes, personaje))
        _mostrar_advertencias(personaje)

        print(f"\n  {AM}[i] Inventario  [f] Ficha  [r] Ranking  "
              f"[h] Historias  [g] Guardar  [q] Salir{R}")
        if es_interactivo():
            print(f"  {DIM}[↑↓] navegar expediciones  [Enter] confirmar  [letra] comando{R}")

        _opciones_nav = (
            [f"{a['nombre']}  peligro {a['peligro']}/5  ~{a['duracion_h']}h"
             for a in opciones_pendientes]
            + ["Descansar en el refugio"]
        )
        cmd = leer_entrada(f"\n  {AM}> {R}", opciones_nav=_opciones_nav).strip().lower()

        # ── Comandos de interfaz ───────────────────────────────
        if cmd == "q":
            guardar(personaje, opciones_pendientes)
            print(f"\n  {VE}Guardado. Hasta la próxima.{R}\n")
            sys.exit(0)

        elif cmd == "g":
            guardar(personaje, opciones_pendientes)
            print(f"  {VE}✔ Guardado.{R}")
            time.sleep(0.7)

        elif cmd == "i":
            pantalla_inventario(personaje)

        elif cmd == "f":
            pantalla_ficha(personaje)

        elif cmd == "r":
            from engine.save_manager import mostrar_leaderboard
            cls()
            print(mostrar_leaderboard(15))
            pausa()

        elif cmd == "h":
            pantalla_historias()

        elif cmd == "0":
            _ejecutar_descanso_interactivo(personaje, opciones_pendientes)

        elif cmd == str(len(opciones_pendientes) + 1):
            # leer_entrada retornó el índice del ítem "Descansar" en opciones_nav
            _ejecutar_descanso_interactivo(personaje, opciones_pendientes)

        elif cmd == "":
            pass   # Enter sin selección: redibujar pantalla

        else:
            _procesar_eleccion_expedicion(cmd, personaje, opciones_pendientes)


def _ejecutar_descanso_interactivo(personaje, opciones):
    from engine.save_manager import guardar
    from engine.tick         import ejecutar_descanso
    cls()
    print(f"\n{VE}{NE}  DESCANSO EN REFUGIO{R}\n")
    resultado = ejecutar_descanso(personaje)
    for linea in resultado.log_descanso:
        print(f"  {GR}{linea}{R}")
    if resultado.progreso_skills:
        print(f"\n  {VE}{NE}↑ PROGRESO DE HABILIDADES{R}")
        for msg in resultado.progreso_skills:
            print(f"  {VE}  {msg}{R}")
    if resultado.penalizaciones_tick:
        for msg in resultado.penalizaciones_tick:
            print(f"  {RO}  {msg}{R}")
    guardar(personaje, opciones)
    pausa()


def _procesar_eleccion_expedicion(cmd: str, personaje, opciones: list):
    if not cmd.isdigit():
        return
    _lanzar_expedicion(cmd, personaje, opciones)


def _lanzar_expedicion(cmd: str, personaje, opciones: list):
    from engine.save_manager import guardar
    from engine.mundo        import generar_opciones
    from engine.tick         import ejecutar_expedicion

    idx = int(cmd) - 1
    if not (0 <= idx < len(opciones)):
        return

    area = opciones[idx]
    cls()
    print(f"\n{VE}{NE}  EXPEDICIÓN → {area['nombre']}{R}")
    print(f"  {GR}Peligro: {area['peligro']}/5 | ~{area['duracion_h']}h | {area.get('distancia_km','?')}km{R}\n")
    time.sleep(0.4)

    resultado = ejecutar_expedicion(personaje, area, exportar_img=True)
    print(resultado.log_terminal)

    if resultado.ruta_imagen:
        print(f"  {VE}📷  {resultado.ruta_imagen}{R}")

    nuevas = generar_opciones(personaje, 4)
    guardar(personaje, nuevas, hacer_backup=True)

    if not personaje.esta_vivo():
        pausa()
        procesar_muerte(personaje, resultado.causa_muerte or "expedición fatal")
        return

    opciones.clear()
    opciones.extend(nuevas)
    pausa()


def _mostrar_advertencias(personaje):
    if personaje.hambre > 80:
        print(f"  {RO}⚠  HAMBRE CRÍTICA — necesitas comer{R}")
    if personaje.sed > 80:
        print(f"  {RO}⚠  SED CRÍTICA — necesitas agua{R}")
    if personaje.salud < personaje.salud_max * 0.25:
        print(f"  {RO}⚠  SALUD CRÍTICA — al borde de la muerte{R}")
    if personaje.fatiga > 85:
        print(f"  {AM}⚠  Agotamiento extremo — descansa{R}")


# ──────────────────────────────────────────────────────────────
#  MUERTE
# ──────────────────────────────────────────────────────────────

def procesar_muerte(personaje, causa: str = "desconocida"):
    from engine.save_manager import registrar_muerte, mostrar_leaderboard, borrar_guardado
    cls()
    print(f"\n{RO}{NE}  {'═' * 52}")
    print(f"  {personaje.nombre} {personaje.apellido} HA CAÍDO")
    print(f"  {'═' * 52}{R}\n")
    print(f"  {GR}Sobrevivió    {personaje.dia} días")
    print(f"  Expediciones  {personaje.expediciones_completadas}")
    print(f"  Infectados    {personaje.infectados_eliminados}")
    print(f"  Bandidos      {personaje.bandidos_eliminados}")
    print(f"  Causa         {causa}{R}\n")
    pos = registrar_muerte(personaje, causa)
    print(f"  {AM}{NE}Posición en el ranking: #{pos}{R}")
    print(mostrar_leaderboard(10))
    borrar_guardado()
    pausa("  [ENTER para volver al menú]")
    menu_inicio()


# ──────────────────────────────────────────────────────────────
#  MODO BOT
# ──────────────────────────────────────────────────────────────

def modo_bot(num_opcion: int = -1):
    from engine.save_manager import cargar, guardar, registrar_muerte, borrar_guardado
    from engine.mundo        import generar_opciones
    from engine.personaje    import Sobreviviente
    from engine.tick         import ejecutar_expedicion

    print("[BOT] Iniciando ciclo automático...")
    personaje, opciones = cargar()
    if not personaje:
        print("[BOT] Sin guardado — generando personaje nuevo...")
        personaje = Sobreviviente()
    if not opciones:
        opciones = generar_opciones(personaje, 4)

    area = (opciones[num_opcion] if 0 <= num_opcion < len(opciones)
            else _bot_elegir(personaje, opciones))
    print(f"[BOT] → {area['nombre']} (peligro {area['peligro']})")

    resultado = ejecutar_expedicion(personaje, area, exportar_img=True)
    print(resultado.log_terminal)
    if resultado.ruta_imagen:
        print(f"[BOT] Imagen: {resultado.ruta_imagen}")

    nuevas = generar_opciones(personaje, 4)
    guardar(personaje, nuevas, hacer_backup=True)
    print("[BOT] Estado guardado.")

    if not personaje.esta_vivo():
        pos = registrar_muerte(personaje, "expedición fatal")
        borrar_guardado()
        print(f"[BOT] Personaje muerto. Ranking #{pos}.")


def _bot_elegir(personaje, opciones: list) -> dict:
    """Heurística: zona moderada salvo con salud baja (entonces la más segura)."""
    if personaje.salud / personaje.salud_max < 0.4:
        return min(opciones, key=lambda a: a["peligro"])
    candidatas = [a for a in opciones if a["peligro"] <= 3] or opciones
    return max(candidatas, key=lambda a: a.get("loot_promedio", a["peligro"]))


# ──────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--bot" in args:
        num = -1
        try:
            i = args.index("--bot")
            if i + 1 < len(args):
                num = int(args[i + 1])
        except (ValueError, IndexError):
            pass
        modo_bot(num)

    elif "--nueva" in args:
        from engine.personaje    import Sobreviviente
        from engine.save_manager import guardar
        p = Sobreviviente()
        guardar(p)
        print(f"Nuevo personaje: {p.nombre} {p.apellido} | {p.background['nombre']}")

    elif "--ranking" in args:
        from engine.save_manager import mostrar_leaderboard
        print(mostrar_leaderboard(20))

    elif "--historias" in args:
        from engine.save_manager import listar_historias
        for h in listar_historias():
            print(f"{h['partida_id']}: {h['num_bitacoras']} imgs, {h['tamaño_mb']}MB")

    else:
        try:
            menu_inicio()
        except KeyboardInterrupt:
            print(f"\n\n  {GR}Hasta pronto, superviviente.{R}\n")
            sys.exit(0)
