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


def _ajustar_ejes(estado: dict, **deltas) -> None:
    """Aplica deltas con clamp 0-100 a campos del NPC. Solo campos numéricos conocidos."""
    _defaults = {
        "confianza": 50, "lealtad": 50, "tension": 25, "miedo": 0,
        "amor": 50, "respeto": 50, "resentimiento": 0,
    }
    for campo, delta in deltas.items():
        actual = int(estado.get(campo, _defaults.get(campo, 0)))
        estado[campo] = max(0, min(100, actual + delta))


def _interactuar_con_npc(personaje, npc_id: str, est: dict):
    """Submenú de interacción social y relaciones con un NPC específico."""
    from engine.familia import (
        proponer_relacion, terminar_relacion, puede_tener_hijo,
        iniciar_embarazo, estado_relacion_actual,
    )
    from engine.relaciones import calidad_vinculo
    from engine.input_handler import menu_navegable
    from engine.almacen import agregar_item, quitar_item
    import copy as _copy

    nombre = est.get("nombre", "?")

    while True:
        er      = estado_relacion_actual(est)
        amor    = int(est.get("amor",          50))
        respeto = int(est.get("respeto",       50))
        resen   = int(est.get("resentimiento",  0))
        calidad = calidad_vinculo(est)

        limpiar()
        console.print(
            f"\n[bold {COLOR_ACCENT}]  {nombre}[/bold {COLOR_ACCENT}]"
            f"  [{COLOR_DIM}]{est.get('rol','?')}, {est.get('edad','?')}a[/{COLOR_DIM}]"
        )
        console.print(f"  [{COLOR_DIM}]{est.get('desc','')}[/{COLOR_DIM}]")
        console.print(
            f"\n  [{COLOR_INFO}]Confianza: {est.get('confianza',0)}"
            f"  Tensión: {est.get('tension',0)}"
            f"  Relación: {er}"
            f"  Vínculo: {calidad}/100[/{COLOR_INFO}]"
        )
        console.print(
            f"  [{COLOR_DIM}]Amor: {amor}  Respeto: {respeto}  Resentimiento: {resen}[/{COLOR_DIM}]\n"
        )

        # ── Opciones disponibles ─────────────────────────────────────────────
        opciones: list[tuple[str, str]] = [
            ("h", "Hablar"),
            ("b", "Bromear"),
            ("e", "Elogiar"),
            ("g", "Regalar algo del inventario"),
        ]

        if est.get("miedo", 0) > 40:
            opciones.append(("c", "Consolar"))

        opciones.append(("p", "Pelear / discutir"))

        # ── Opciones de relación ─────────────────────────────────────────────
        if not est.get("es_menor", False):
            if er == "pareja":
                opciones.append(("x", "Terminar la relación"))
                if puede_tener_hijo(personaje, npc_id):
                    opciones.append(("j", "Hablar de tener un hijo"))
            elif er in ("cercano", "interes"):
                opciones.append(("r", "Proponer relación"))
            elif er == "ex_pareja":
                opciones.append(("r", "Intentar retomar la relación"))
            elif er in ("amigo", "conocido"):
                opciones.append(("r", "Declarar interés"))

        opciones.append(("q", "Volver"))

        for key, texto in opciones:
            console.print(f"  [{COLOR_ACCENT}][{key}][/{COLOR_ACCENT}] {texto}")

        cmd = leer_cmd()

        if cmd == "q" or es_salida(cmd):
            return

        # ── Hablar ───────────────────────────────────────────────────────────
        elif cmd == "h":
            _ajustar_ejes(est, confianza=3, amor=2, tension=-2)
            console.print(
                f"\n  [{COLOR_OK}]Pasaste un rato hablando con {nombre}. "
                f"La distancia entre vosotros se redujo un poco.[/{COLOR_OK}]"
            )
            pausa()

        # ── Bromear ──────────────────────────────────────────────────────────
        elif cmd == "b":
            if int(est.get("confianza", 0)) < 30:
                console.print(
                    f"\n  [{COLOR_WARN}]{nombre} no te conoce lo suficiente "
                    f"para ese tipo de humor.[/{COLOR_WARN}]"
                )
            elif resen > 50:
                # El resentimiento hace que la broma salga mal
                _ajustar_ejes(est, resentimiento=5, tension=5, amor=-3)
                console.print(
                    f"\n  [{COLOR_WARN}]El intento de humor salió mal. "
                    f"{nombre} lo tomó como una burla.[/{COLOR_WARN}]"
                )
            else:
                _ajustar_ejes(est, amor=5, tension=-5, resentimiento=-3)
                personaje.moral = min(100, personaje.moral + 1)
                console.print(
                    f"\n  [{COLOR_OK}]Le hiciste reír. "
                    f"El ambiente del refugio se alivió un poco.[/{COLOR_OK}]"
                )
            pausa()

        # ── Elogiar ──────────────────────────────────────────────────────────
        elif cmd == "e":
            if int(est.get("confianza", 0)) < 25:
                console.print(
                    f"\n  [{COLOR_WARN}]Necesitas conocer mejor a {nombre} "
                    f"para que un elogio tenga peso real.[/{COLOR_WARN}]"
                )
            else:
                _ajustar_ejes(est, respeto=8, amor=4, resentimiento=-5)
                console.print(
                    f"\n  [{COLOR_OK}]Reconociste el esfuerzo de {nombre}. "
                    f"Lo notó.[/{COLOR_OK}]"
                )
            pausa()

        # ── Regalar ──────────────────────────────────────────────────────────
        elif cmd == "g":
            if not personaje.inventario:
                console.print(
                    f"\n  [{COLOR_WARN}]No tienes nada en el inventario "
                    f"para regalar.[/{COLOR_WARN}]"
                )
                pausa()
            else:
                nombres_inv = [
                    f"{it['nombre']}"
                    + (f" (x{it['cantidad']})" if it.get("cantidad", 1) > 1 else "")
                    for it in personaje.inventario
                ] + ["↩ Cancelar"]
                idx = menu_navegable(f"¿Qué regalarle a {nombre}?", nombres_inv, limpiar=True)
                if 0 <= idx < len(personaje.inventario):
                    item_regalo  = personaje.inventario[idx]
                    nombre_item  = item_regalo.get("nombre", "?")
                    # Quitar 1 unidad del inventario
                    extraido = quitar_item(personaje.inventario, nombre_item, 1)
                    if extraido:
                        agregar_item(personaje.almacen, extraido)
                        personalidad = est.get("personalidad", "")
                        if personalidad in ("generoso", "empatico", "leal", "protector"):
                            _ajustar_ejes(est, amor=15, confianza=10, respeto=6)
                            reaccion = "Lo recibió con gratitud genuina."
                        elif personalidad in ("oportunista", "hosco", "desconfiado"):
                            _ajustar_ejes(est, amor=6, confianza=5, respeto=3)
                            reaccion = "Lo aceptó sin decir mucho, pero lo recordará."
                        else:
                            _ajustar_ejes(est, amor=10, confianza=8, respeto=5)
                            reaccion = "Agradeció el gesto."
                        console.print(
                            f"\n  [{COLOR_OK}]Le regalaste {nombre_item}. "
                            f"{nombre}: {reaccion}[/{COLOR_OK}]"
                        )
                        pausa()

        # ── Consolar ─────────────────────────────────────────────────────────
        elif cmd == "c" and est.get("miedo", 0) > 40:
            _ajustar_ejes(est, amor=8, tension=-5)
            est["miedo"] = max(0, int(est.get("miedo", 0)) - 15)
            console.print(
                f"\n  [{COLOR_OK}]Intentaste calmar a {nombre}. "
                f"Tus palabras llegaron.[/{COLOR_OK}]"
            )
            pausa()

        # ── Pelear / discutir ─────────────────────────────────────────────────
        elif cmd == "p":
            _ajustar_ejes(est, tension=15, amor=-8, respeto=-6, resentimiento=12)
            est["veces_peleado"] = int(est.get("veces_peleado", 0)) + 1
            console.print(
                f"\n  [{COLOR_DANGER}]La discusión con {nombre} escaló rápidamente. "
                f"Nadie salió bien parado.[/{COLOR_DANGER}]"
            )
            pausa()

        # ── Proponer / retomar relación ───────────────────────────────────────
        elif cmd == "r" and not est.get("es_menor", False):
            msg = proponer_relacion(personaje, npc_id)
            console.print(f"\n  [{COLOR_INFO}]{msg}[/{COLOR_INFO}]")
            pausa()

        # ── Terminar relación ─────────────────────────────────────────────────
        elif cmd == "x" and er == "pareja":
            msg = terminar_relacion(personaje, npc_id)
            console.print(f"\n  [{COLOR_DANGER}]{msg}[/{COLOR_DANGER}]")
            pausa()
            return  # Volver a la lista tras romper la relación

        # ── Tener un hijo ─────────────────────────────────────────────────────
        elif cmd == "j" and er == "pareja" and puede_tener_hijo(personaje, npc_id):
            msg = iniciar_embarazo(personaje, npc_id)
            console.print(f"\n  [{COLOR_INFO}]{msg}[/{COLOR_INFO}]")
            pausa()
