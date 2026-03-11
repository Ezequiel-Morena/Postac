from ui.tui import (
    console, limpiar, pausa, barra_vital, barra_invertida,
    leer_cmd, es_salida, footer_volver,
    COLOR_OK, COLOR_WARN, COLOR_DANGER, COLOR_INFO, COLOR_DIM, COLOR_ACCENT,
)
from rich.table import Table
from rich.text  import Text
from rich.panel import Panel
from rich       import box


def pantalla_supervivientes(personaje):
    """Pantalla completa de supervivientes en el refugio con interacción."""
    from engine.familia import proponer_relacion, terminar_relacion, puede_tener_hijo, iniciar_embarazo
    from data.familia import RELACION_TIPOS, EDAD_ADULTO

    while True:
        limpiar()
        rels    = personaje.relaciones_refugio
        familia = getattr(personaje, "familia", {})

        console.print(Panel(
            f"[bold {COLOR_ACCENT}]SUPERVIVIENTES EN EL REFUGIO[/bold {COLOR_ACCENT}]",
            border_style=COLOR_INFO,
            padding=(0, 1),
        ))

        if not rels:
            console.print(f"\n  [{COLOR_DIM}]El refugio está vacío. Nadie ha llegado todavía.[/{COLOR_DIM}]")
            console.print(f"  [{COLOR_DIM}]Encuentra supervivientes durante expediciones.[/{COLOR_DIM}]")
        else:
            _imprimir_tabla_supervivientes(rels, familia)

        # ── Sección de animales ──────────────────────────────────
        animales = getattr(personaje, "animales_refugio", [])
        if animales:
            console.print(f"\n  [{COLOR_ACCENT}]ANIMALES EN EL REFUGIO[/{COLOR_ACCENT}]")
            _imprimir_tabla_animales(animales)

        console.print(f"\n  {footer_volver('[número] Interactuar')}")
        cmd = leer_cmd()

        if es_salida(cmd):
            return

        if not cmd.isdigit():
            continue
        idx = int(cmd) - 1
        lista = list(rels.items())
        if not (0 <= idx < len(lista)):
            continue

        npc_id, est = lista[idx]
        _interactuar_con_npc(personaje, npc_id, est)


def _imprimir_tabla_supervivientes(rels: dict, familia: dict) -> None:
    """Tabla con todos los supervivientes y sus vitales."""
    t = Table(
        box=box.SIMPLE_HEAVY,
        border_style=COLOR_DIM,
        show_header=True,
        header_style=f"bold {COLOR_INFO}",
        expand=True,
    )
    t.add_column("#", width=3, justify="right")
    t.add_column("Nombre", min_width=20)
    t.add_column("Rol / Edad", width=16)
    t.add_column("Salud", width=16)
    t.add_column("Sacied.", width=16)
    t.add_column("Confianza", width=16)
    t.add_column("Estado", width=14)

    for idx, (npc_id, est) in enumerate(rels.items(), 1):
        nombre   = f"{est.get('nombre', '?')} {est.get('apellido', '')}"
        rol      = est.get("rol", "?")
        edad     = est.get("edad", "?")
        salud    = int(est.get("salud", 0))
        hambre   = int(est.get("hambre", 0))
        conf     = int(est.get("confianza", 0))
        tension  = int(est.get("tension", 0))
        er       = est.get("estado_relacion", "desconocido")
        en_exp   = est.get("en_expedicion", False)
        es_menor = est.get("es_menor", False)
        vinculo  = familia.get(npc_id, {}).get("tipo", "")

        # Badge de vínculo familiar
        badge = ""
        if vinculo == "pareja":
            badge = " ❤"
        elif vinculo in ("hijo", "hija"):
            badge = f" ▸{vinculo}"
        elif vinculo in ("padre", "madre"):
            badge = f" ▸{vinculo}"

        nombre_text = Text()
        nombre_text.append(nombre, style=COLOR_ACCENT)
        if badge:
            nombre_text.append(badge, style=COLOR_WARN)
        if er not in ("desconocido", "familiar", ""):
            nombre_text.append(f" [{er}]", style=COLOR_DIM)

        rol_str = f"{rol}, {edad}a"
        if es_menor:
            rol_str = f"{rol} ({edad}a) menor"

        estado_str = Text("EN EXP.", style=COLOR_WARN) if en_exp else Text("")
        if est.get("quiere_irse"):
            estado_str = Text("¡QUIERE IRSE!", style=COLOR_DANGER)
        if tension > 60:
            estado_str = Text(f"tensión {tension}", style=COLOR_WARN)

        t.add_row(
            Text(str(idx), style=COLOR_DIM),
            nombre_text,
            Text(rol_str, style=COLOR_DIM),
            barra_vital(salud),
            barra_invertida(hambre),
            barra_vital(conf),
            estado_str,
        )

        # Embarazo
        if est.get("embarazo_ticks", 0) > 0:
            t.add_row(
                Text(""),
                Text(f"  Embarazo: ~{est['embarazo_ticks']} expediciones", style=COLOR_INFO),
                Text(""), Text(""), Text(""), Text(""), Text(""),
            )

    console.print(t)


def _imprimir_tabla_animales(animales: list) -> None:
    """Tabla de animales en el refugio."""
    t = Table(
        box=box.SIMPLE,
        border_style=COLOR_DIM,
        show_header=True,
        header_style=f"bold {COLOR_INFO}",
    )
    t.add_column("Animal", min_width=16)
    t.add_column("Tipo", width=12)
    t.add_column("Salud", width=16)
    t.add_column("Saciedad", width=16)

    for animal in animales:
        from data.animales import TIPOS_ANIMALES
        defn      = TIPOS_ANIMALES.get(animal.get("tipo", ""), {})
        icono     = defn.get("icono", "🐾")
        nombre_a  = animal.get("nombre", "?")
        sal_a     = int(animal.get("salud", 0))
        sal_max_a = int(animal.get("salud_max", 100))
        ham_a     = int(animal.get("hambre", 0))
        tipo_str  = animal.get("tipo", "animal").capitalize()

        t.add_row(
            f"{icono} {nombre_a}",
            Text(tipo_str, style=COLOR_DIM),
            barra_vital(sal_a, sal_max_a),
            barra_invertida(ham_a),
        )

    console.print(t)


def _interactuar_con_npc(personaje, npc_id: str, est: dict):
    """Submenú de interacción con un NPC específico."""
    from engine.familia import (
        proponer_relacion, terminar_relacion, puede_tener_hijo,
        iniciar_embarazo, estado_relacion_actual,
    )

    nombre = est.get("nombre", "?")
    er     = estado_relacion_actual(est)

    opciones: list[tuple[str, str]] = []

    if er not in ("pareja",) and not est.get("es_menor", False):
        if er in ("cercano", "interes"):
            opciones.append(("r", "Proponer relación"))
        elif er == "ex_pareja":
            opciones.append(("r", "Intentar retomar la relación"))
        elif er in ("amigo", "conocido"):
            opciones.append(("r", "Declarar interés"))

    if er == "pareja":
        opciones.append(("x", "Terminar la relación"))
        if puede_tener_hijo(personaje, npc_id):
            opciones.append(("h", "Hablar de tener un hijo"))

    opciones.append(("q", "Volver"))

    limpiar()
    console.print(f"\n[bold {COLOR_ACCENT}]  {nombre}[/bold {COLOR_ACCENT}]"
                  f"  [{COLOR_DIM}]{est.get('rol','?')}, {est.get('edad','?')}a[/{COLOR_DIM}]")
    console.print(f"  [{COLOR_DIM}]{est.get('desc','')}[/{COLOR_DIM}]")
    console.print(
        f"\n  [{COLOR_INFO}]Confianza: {est.get('confianza',0)}  "
        f"Relación: {er}  Tensión: {est.get('tension',0)}[/{COLOR_INFO}]\n"
    )

    for key, texto in opciones:
        console.print(f"  [{COLOR_ACCENT}][{key}][/{COLOR_ACCENT}] {texto}")

    cmd = leer_cmd()

    if cmd == "r" and not est.get("es_menor", False):
        msg = proponer_relacion(personaje, npc_id)
        console.print(f"\n  [{COLOR_INFO}]{msg}[/{COLOR_INFO}]")
        pausa()

    elif cmd == "x" and er == "pareja":
        msg = terminar_relacion(personaje, npc_id)
        console.print(f"\n  [{COLOR_DANGER}]{msg}[/{COLOR_DANGER}]")
        pausa()

    elif cmd == "h" and er == "pareja" and puede_tener_hijo(personaje, npc_id):
        msg = iniciar_embarazo(personaje, npc_id)
        console.print(f"\n  [{COLOR_INFO}]{msg}[/{COLOR_INFO}]")
        pausa()
