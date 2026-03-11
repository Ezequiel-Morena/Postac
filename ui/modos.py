from ui.colors import R, VE, RO, AM, CI, GR, BL, NE, DIM, cls, pausa, LOGO
from ui.game_loop import bucle_principal


def modo_simulacion_autonoma(max_dias: int = 0, exportar: bool = True):
    """
    Modo 100% autónomo: crea un personaje nuevo y simula su vida completa
    sin ninguna interacción del usuario.

    El simulador decide en cada tick si descansar o ir de expedición,
    y qué zona elegir, usando engine/autonomo.py junto con la estrategia
    aprendida en data/estrategias.json.

    Parámetros:
        max_dias   : Límite de días simulados (0 = sin límite, hasta la muerte).
        exportar   : Si True, exporta imágenes PNG de la bitácora.
    """
    from engine.save_manager import registrar_muerte, guardar, borrar_guardado
    from engine.mundo        import generar_opciones
    from engine.personaje    import Sobreviviente
    from engine.tick         import ejecutar_expedicion, ejecutar_descanso
    from engine.estrategia   import (
        cargar_estrategia, guardar_estrategia,
        obtener_config_archetype, registrar_fin_partida,
        snapshot_archetype, mostrar_diff_archetype,
    )
    from engine.autonomo import (
        decidir_tick, gestionar_inventario_autonomo, gestionar_recursos_autonomo,
        gestionar_recursos_almacen, cargar_mochila_desde_almacen,
        decidir_acciones_disponibles, ejecutar_accion_autonoma,
    )
    from engine.fuego import esta_encendido

    cls()
    print(LOGO)
    print(f"  {AM}{NE}MODO SIMULACIÓN AUTÓNOMA{R}")
    print(f"  {GR}El simulador controla todas las decisiones.{R}\n")

    personaje  = Sobreviviente()
    estrategia = cargar_estrategia()
    config     = obtener_config_archetype(personaje, estrategia)

    print(f"  {VE}► {personaje.nombre} {personaje.apellido} — {personaje.background['nombre']}{R}")
    print(f"  {GR}Archetype: {config.get('_archetype', '?')} · Iniciando...{R}\n")

    # Capturar estado de estrategia ANTES de la simulación.
    snap_antes = snapshot_archetype(personaje, estrategia)

    opciones       = generar_opciones(personaje, 4)
    zonas_hist: list[str] = []
    zona_muerte: str | None = None

    while personaje.esta_vivo():
        if max_dias > 0 and personaje.dia > max_dias:
            break

        # 1. Consumir recursos según estado vital (comida, agua, medicina, etc.)
        for msg in gestionar_recursos_autonomo(personaje):
            print(f"  {GR}{msg}{R}")

        # 2. Gestión de inventario (descartar si está lleno).
        for msg in gestionar_inventario_autonomo(personaje, config):
            print(f"  {GR}{msg}{R}")

        # 3. Acciones autónomas previas a la decisión principal:
        #    encender fuego si hay combustible, cocinar si hay materiales.
        acciones_disponibles = decidir_acciones_disponibles(personaje, opciones)
        sin_fuego   = not esta_encendido(personaje)
        hay_comida  = any(
            isinstance(i, dict) and i.get("tipo") == "comida"
            for i in getattr(personaje, "almacen", [])
        )
        hambre_alta = personaje.hambre < 40

        if sin_fuego and "encender_fuego" in acciones_disponibles:
            log = ejecutar_accion_autonoma(personaje, "encender_fuego", opciones)
            print(f"  {GR}{log}{R}")

        if "cocinar" in acciones_disponibles and esta_encendido(personaje):
            log = ejecutar_accion_autonoma(personaje, "cocinar", opciones)
            print(f"  {GR}{log}{R}")

        # Si hay hambre crítica y no hay comida, intentar conseguirla
        if hambre_alta and not hay_comida:
            for accion_comida in ("pescar", "recolectar", "cazar"):
                if accion_comida in acciones_disponibles:
                    log = ejecutar_accion_autonoma(personaje, accion_comida, opciones)
                    print(f"  {GR}{log}{R}")
                    break

        accion, zona = decidir_tick(personaje, opciones, config)

        if accion == "descanso":
            for msg in gestionar_recursos_almacen(personaje):
                print(f"  {GR}{msg}{R}")
            resultado = ejecutar_descanso(personaje)
            _imprimir_resumen_tick(personaje, resultado, "descanso", None)
        else:
            for msg in cargar_mochila_desde_almacen(personaje):
                print(f"  {GR}{msg}{R}")
            resultado   = ejecutar_expedicion(personaje, zona, exportar_img=exportar)
            zona_key    = zona.get("area_key", zona.get("nombre", ""))
            zonas_hist.append(zona_key)
            if not resultado.personaje_vivo:
                zona_muerte = zona_key
            _imprimir_resumen_tick(personaje, resultado, "expedicion", zona)

        if not personaje.esta_vivo():
            break

        # Rota opciones de zona y refresca configuración (puede evolucionar).
        opciones = generar_opciones(personaje, 4)
        config   = obtener_config_archetype(personaje, estrategia)

    # ── Fin de la partida ─────────────────────────────────────
    causa = getattr(resultado, "causa_muerte", "simulación completa") or "simulación completa"
    registrar_fin_partida(personaje, estrategia, causa, zonas_hist, zona_muerte)
    guardar_estrategia(estrategia)

    from engine.save_manager import registrar_muerte, borrar_guardado
    pos = registrar_muerte(personaje, causa)
    borrar_guardado()

    print(f"\n  {RO}{NE}{'═' * 52}")
    print(f"  {personaje.nombre} {personaje.apellido} HA CAÍDO")
    print(f"  {'═' * 52}{R}")
    print(f"  {GR}Días:         {personaje.dia}")
    print(f"  Expediciones: {personaje.expediciones_completadas}")
    print(f"  Causa:        {causa}")
    print(f"  Ranking:      #{pos}{R}\n")

    # ── Diff de estrategia: antes → después ──────────────────
    print(f"  {AM}{'─' * 52}")
    print(f"  CAMBIOS EN ESTRATEGIA")
    print(f"  {'─' * 52}{R}")
    print(f"{GR}{mostrar_diff_archetype(snap_antes, estrategia)}{R}\n")


def _imprimir_resumen_tick(personaje, resultado, tipo: str, zona):
    """Imprime un resumen compacto del tick para el modo autónomo."""
    icono  = "🏕" if tipo == "descanso" else "🧭"
    destino = zona["nombre"] if zona else "refugio"
    dia_str = f"Día {personaje.dia:3d}"

    # Estado vital resumido.
    sal_pct = int(personaje.salud / max(1, personaje.salud_max) * 100)
    col_sal = RO if sal_pct < 30 else (AM if sal_pct < 60 else VE)
    vitales = (f"{col_sal}❤{sal_pct}%{R} "
               f"{AM}🍖{100 - personaje.hambre}%{R} "
               f"{CI}💧{100 - personaje.sed}%{R}")

    exito_str = ""
    if tipo == "expedicion":
        exito_str = f" {VE}✓{R}" if resultado.exito else f" {RO}✗{R}"

    print(f"  {GR}{dia_str}{R}  {icono} {destino:<22}{exito_str}  {vitales}")

    # Alerta de muerte o daño grave.
    if not resultado.personaje_vivo:
        print(f"  {RO}⚠ {resultado.causa_muerte}{R}")


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
    return max(
        candidatas,
        key=lambda a: (a.get("loot_score", 0.0) - a.get("riesgo_score", a.get("peligro", 1) * 0.7))
    )
