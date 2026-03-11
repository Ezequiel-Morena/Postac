#!/usr/bin/env python3
# ============================================================
# main.py — POSTAC: Simulador de Supervivencia Post-Apocalíptica
#
# Punto de entrada CLI. Toda la lógica de presentación vive en ui/.
# ============================================================

import sys

from ui.colors import R, VE, RO, AM, CI, GR, BL, NE, DIM


_HELP_TEXT = f"""
  {AM}╔══════════════════════════════════════════════════════════════╗
  ║              POSTAC — Comandos disponibles                   ║
  ╚══════════════════════════════════════════════════════════════╝{R}

  {VE}Modo interactivo (por defecto){R}
    python main.py
      Abre el menú principal. El jugador elige expediciones.

  {VE}Modo autónomo — una sola simulación{R}
    python main.py --auto [DIAS] [--no-img]
      El simulador toma todas las decisiones solo.
      DIAS   Límite de días (0 = sin límite). Ejemplo: --auto 30
      --no-img   Omite la exportación de imagen al terminar.

  {VE}Modo autónomo — varias simulaciones en paralelo{R}
    python main.py --auto-batch <N|max> [--dias D] [--no-img]
      Ejecuta N simulaciones en paralelo usando multiprocessing.
      max    Detecta la CPU y usa todos los núcleos disponibles.
      --dias D   Límite de días por simulación.
      Ejemplos:
        python main.py --auto-batch 2 --dias 10
        python main.py --auto-batch max --no-img

  {VE}Modo loop — repite simulaciones automáticamente{R}
    python main.py --auto       --loop N [--dias D] [--no-img]
    python main.py --auto-batch --loop N [--dias D] [--no-img]
      Repite N veces la simulación elegida (--auto o --auto-batch).
      Espera 2-3 segundos entre iteraciones para liberar hilos.
      N = 0 → bucle infinito (Ctrl+C para detener).
      Ejemplos:
        python main.py --auto --loop 5 --no-img
        python main.py --auto-batch max --loop 10 --dias 5 --no-img

  {VE}Gestión de estrategias{R}
    python main.py --reset-estrategia [--forzar]
      Borra el aprendizaje acumulado en data/estrategias.json.
      Guarda un backup automático (.bak) antes de borrar.
      --forzar   Omite la confirmación interactiva.

  {VE}Otros comandos{R}
    python main.py --ranking
      Muestra la tabla de clasificación de supervivientes caídos.
    python main.py --nueva
      Crea y guarda un nuevo personaje (sin iniciar partida).
    python main.py --bot [N]
      Ejecuta N partidas en modo bot (publicación automática).
    python main.py --historias
      Lista las historias guardadas con sus imágenes.
    python main.py --help
      Muestra este mensaje.
"""


def _parsear_arg_int(args: list[str], flag: str, default: int = 0) -> int:
    """Extrae el entero que sigue a `flag` en args, o devuelve `default`."""
    try:
        i = args.index(flag)
        if i + 1 < len(args) and not args[i + 1].startswith("--"):
            return int(args[i + 1])
    except (ValueError, IndexError):
        pass
    return default


def _ejecutar_loop(args: list[str], n_iteraciones: int) -> None:
    """Repite la simulación (--auto o --auto-batch) N veces con pausa entre iteraciones."""
    import time
    import random
    from ui.modos import modo_simulacion_autonoma

    es_batch  = "--auto-batch" in args
    no_img    = "--no-img" in args
    max_dias  = _parsear_arg_int(args, "--dias")

    modo_label = "auto-batch" if es_batch else "auto"
    infinito   = n_iteraciones == 0

    if es_batch:
        from engine.batch import ejecutar_batch, resolver_n_workers
        n_arg     = "max"
        try:
            i = args.index("--auto-batch")
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                n_arg = args[i + 1]
        except (ValueError, IndexError):
            pass
        n_workers = resolver_n_workers(n_arg)

    limite_txt = "∞" if infinito else str(n_iteraciones)
    print(
        f"\n  {AM}━━━ LOOP {modo_label.upper()} · {limite_txt} iteraciones"
        f"{f' · máx {max_dias}d/sim' if max_dias else ''} ━━━{R}\n"
    )

    iteracion = 0
    try:
        while infinito or iteracion < n_iteraciones:
            iteracion += 1
            print(f"  {VE}▶ Iteración {iteracion}{f'/{n_iteraciones}' if not infinito else ''}{R}")

            if es_batch:
                print(f"  CPUs detectadas: {__import__('os').cpu_count()} · Workers: {n_workers}")
                ejecutar_batch(n_workers=n_workers, max_dias=max_dias, exportar=not no_img)
            else:
                modo_simulacion_autonoma(max_dias=max_dias, exportar=not no_img)

            if infinito or iteracion < n_iteraciones:
                espera = random.uniform(2.0, 3.0)
                print(f"\n  ⏳ Pausa {espera:.1f}s antes de la siguiente iteración…\n")
                time.sleep(espera)

    except KeyboardInterrupt:
        print(f"\n\n  {GR}Loop detenido tras {iteracion} iteración(es). Hasta pronto.{R}\n")
        sys.exit(0)

    print(f"\n  {VE}✔ Loop completado: {iteracion} iteración(es).{R}\n")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        if not args:
            # Sin argumentos → menú interactivo como siempre.
            from ui.menus import menu_inicio
            from ui.game_loop import bucle_principal
            try:
                while True:
                    result = menu_inicio()
                    if result is None:
                        print(f"\n\n  {GR}Hasta pronto, superviviente.{R}\n")
                        break
                    personaje, opciones = result
                    bucle_principal(personaje, opciones)
            except KeyboardInterrupt:
                print(f"\n\n  {GR}Hasta pronto, superviviente.{R}\n")
                sys.exit(0)
        else:
            print(_HELP_TEXT)
            sys.exit(0)

    elif "--loop" in args and ("--auto" in args or "--auto-batch" in args):
        n_iter = _parsear_arg_int(args, "--loop", default=1)
        _ejecutar_loop(args, n_iter)

    elif "--auto-batch" in args:
        from engine.batch import ejecutar_batch, resolver_n_workers
        n_arg    = "max"
        max_dias = 0
        no_img   = "--no-img" in args
        try:
            i = args.index("--auto-batch")
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                n_arg = args[i + 1]
            if "--dias" in args:
                j = args.index("--dias")
                if j + 1 < len(args):
                    max_dias = int(args[j + 1])
        except (ValueError, IndexError):
            pass
        n_workers = resolver_n_workers(n_arg)
        print(f"\n  CPUs detectadas: {__import__('os').cpu_count()} · Workers: {n_workers}")
        ejecutar_batch(n_workers=n_workers, max_dias=max_dias, exportar=not no_img)

    elif "--auto" in args:
        from ui.modos import modo_simulacion_autonoma
        max_dias = _parsear_arg_int(args, "--auto")
        no_img   = "--no-img" in args
        modo_simulacion_autonoma(max_dias=max_dias, exportar=not no_img)

    elif "--bot" in args:
        from ui.modos import modo_bot
        num = -1
        try:
            i = args.index("--bot")
            if i + 1 < len(args):
                num = int(args[i + 1])
        except (ValueError, IndexError):
            pass
        modo_bot(num)

    elif "--reset-estrategia" in args:
        from engine.estrategia import resetear_estrategia
        if "--forzar" not in args:
            print(f"\n  {AM}⚠ Esto borrará todo el aprendizaje acumulado en data/estrategias.json.")
            print(f"  Se guardará un backup automático (.bak).{R}")
            resp = input(f"\n  ¿Continuar? [s/N]: ").strip().lower()
            if resp not in ("s", "si", "sí", "y", "yes"):
                print(f"  {GR}Cancelado.{R}")
                sys.exit(0)
        msg = resetear_estrategia()
        print(f"\n  {VE}✔ {msg}{R}\n")

    elif "--nueva" in args:
        from engine.personaje    import Sobreviviente
        from engine.save_manager import guardar
        p = Sobreviviente()
        guardar(p)
        print(f"Nuevo personaje: {p.nombre} {p.apellido} | {p.background['nombre']}")

    elif "--ranking" in args:
        from ui.tui import render_leaderboard_ansi
        print(render_leaderboard_ansi(20))

    elif "--historias" in args:
        from engine.save_manager import listar_historias
        for h in listar_historias():
            print(f"{h['partida_id']}: {h['num_bitacoras']} imgs, {h['tamaño_mb']}MB")

    else:
        print(f"\n  {AM}Comando desconocido. Usa --help para ver los comandos disponibles.{R}\n")
        sys.exit(1)
