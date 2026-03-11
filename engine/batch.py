# ============================================================
# engine/batch.py — Ejecución de simulaciones en paralelo
#
# Arquitectura:
#   ┌──────────────────────────────────────────────────────┐
#   │  Pool de N workers (multiprocessing.Pool)            │
#   │  Cada worker ejecuta una simulación completa         │
#   │  y al morir envía RunResult a la cola compartida.    │
#   └────────────────────┬─────────────────────────────────┘
#                        │ multiprocessing.Queue
#   ┌────────────────────▼─────────────────────────────────┐
#   │  Proceso escritor (único que toca archivos de datos) │
#   │   - estrategias.json  ← registrar_fin_partida()      │
#   │   - leaderboard.json  ← registrar_muerte()           │
#   └──────────────────────────────────────────────────────┘
#
# Principio de diseño:
#   Los workers son read-only sobre archivos compartidos.
#   El escritor es el único proceso que escribe, lo que elimina
#   cualquier posibilidad de corrupción o race condition.
# ============================================================

from __future__ import annotations

import multiprocessing
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

# ──────────────────────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────

# Señal centinela que indica al escritor que no vendrán más resultados.
_SENTINEL = None

# Cuántos ticks máximos por día antes de forzar descanso (límite de seguridad).
_MAX_TICKS_POR_DIA = 50


# ──────────────────────────────────────────────────────────────
#  RESOLUCIÓN DE WORKERS
# ──────────────────────────────────────────────────────────────

def resolver_n_workers(valor: str | int) -> int:
    """
    Convierte el argumento de workers a un entero.
    "max" → detecta CPUs del sistema y devuelve ese número.
    Número entero → usa ese valor (mínimo 1).
    """
    if str(valor).lower() == "max":
        return max(1, os.cpu_count() or 1)
    try:
        n = int(valor)
        return max(1, n)
    except (ValueError, TypeError):
        return 1


# ──────────────────────────────────────────────────────────────
#  RESULTADO DE SIMULACIÓN (pasable entre procesos)
# ──────────────────────────────────────────────────────────────

@dataclass
class RunResult:
    """Datos serializables que el worker envía al escritor al terminar."""
    sim_id:              int
    personaje_dict:      dict         # personaje.a_dict() para el leaderboard
    causa_muerte:        str
    zonas_visitadas:     list[str]
    zona_muerte:         str | None
    dias_vividos:        int
    expediciones:        int
    nombre_completo:     str
    background:          str
    archetype:           str


# ──────────────────────────────────────────────────────────────
#  WORKER — función de nivel módulo (requerido por multiprocessing)
# ──────────────────────────────────────────────────────────────

def _worker_simulacion(args: tuple) -> None:
    """
    Ejecuta una simulación completa de forma autónoma.
    Esta función corre en un proceso separado.

    No escribe a ningún archivo compartido — solo envía RunResult a la cola.
    Captura cualquier excepción no manejada para garantizar que siempre
    se envíe un RunResult a la cola (evita que el escritor quede bloqueado).
    """
    sim_id, queue, max_dias, exportar = args
    try:
        _ejecutar_simulacion_interna(sim_id, queue, max_dias, exportar)
    except Exception as e:
        # Error inesperado: enviar resultado parcial para no bloquear el escritor.
        print(f"  [SIM {sim_id}] ⚠ Error inesperado: {e}", flush=True)
        # Intentar enviar un resultado mínimo de emergencia.
        try:
            from engine.personaje import Sobreviviente
            p = Sobreviviente.__new__(Sobreviviente)
            p.nombre   = f"SIM{sim_id}"
            p.apellido = "ERROR"
            p.dia      = 0
            p.expediciones_completadas = 0
            queue.put(RunResult(
                sim_id=sim_id,
                personaje_dict={},
                causa_muerte=f"error interno: {e}",
                zonas_visitadas=[],
                zona_muerte=None,
                dias_vividos=0,
                expediciones=0,
                nombre_completo=f"SIM {sim_id} (error)",
                background="desconocido",
                archetype="desconocido",
            ))
        except Exception:
            pass  # Si ni esto funciona, el escritor usará timeout.


def _ejecutar_simulacion_interna(sim_id: int, queue, max_dias: int, exportar: bool) -> None:
    """Lógica real de la simulación, separada del manejo de errores."""

    # Importaciones dentro del worker para evitar problemas de fork.
    from engine.mundo       import generar_opciones
    from engine.personaje   import Sobreviviente
    from engine.tick        import ejecutar_expedicion, ejecutar_descanso
    from engine.estrategia  import cargar_estrategia, obtener_config_archetype
    from engine.autonomo    import (
        decidir_tick,
        gestionar_recursos_autonomo,
        gestionar_inventario_autonomo,
    )

    personaje  = Sobreviviente()
    estrategia = cargar_estrategia()   # Lectura — sin conflicto.
    config     = obtener_config_archetype(personaje, estrategia)

    archetype = config.get("_archetype", "desconocido")
    nombre    = f"{personaje.nombre} {personaje.apellido}"
    print(f"  [SIM {sim_id}] ► {nombre} ({archetype})", flush=True)

    opciones        = generar_opciones(personaje, 4)
    zonas_hist: list[str] = []
    zona_muerte: str | None = None
    resultado = None
    ticks_dia_actual = 0
    dia_anterior     = personaje.dia

    while personaje.esta_vivo():
        if max_dias > 0 and personaje.dia > max_dias:
            break

        # Resetear contador por día nuevo.
        if personaje.dia != dia_anterior:
            ticks_dia_actual = 0
            dia_anterior     = personaje.dia

        # Límite de seguridad: forzar descanso si hay demasiados ticks en un día.
        if ticks_dia_actual >= _MAX_TICKS_POR_DIA:
            resultado = ejecutar_descanso(personaje)
            ticks_dia_actual = 0
            continue

        gestionar_recursos_autonomo(personaje)
        gestionar_inventario_autonomo(personaje, config)

        accion, zona = decidir_tick(personaje, opciones, config)

        if accion == "descanso":
            resultado = ejecutar_descanso(personaje)
        else:
            resultado = ejecutar_expedicion(personaje, zona, exportar_img=exportar)
            zona_key  = zona.get("area_key", zona.get("nombre", ""))
            zonas_hist.append(zona_key)
            if not resultado.personaje_vivo:
                zona_muerte = zona_key

        ticks_dia_actual += 1

        if not personaje.esta_vivo():
            break

        opciones = generar_opciones(personaje, 4)
        config   = obtener_config_archetype(personaje, estrategia)

    causa = (getattr(resultado, "causa_muerte", "") or "simulación completa") if resultado else "desconocida"

    run = RunResult(
        sim_id          = sim_id,
        personaje_dict  = personaje.a_dict(),
        causa_muerte    = causa,
        zonas_visitadas = zonas_hist,
        zona_muerte     = zona_muerte,
        dias_vividos    = personaje.dia,
        expediciones    = personaje.expediciones_completadas,
        nombre_completo = nombre,
        background      = personaje.background.get("nombre", ""),
        archetype       = archetype,
    )
    queue.put(run)


# ──────────────────────────────────────────────────────────────
#  ESCRITOR — proceso único que toca archivos compartidos
# ──────────────────────────────────────────────────────────────

def _escritor_batch(queue: Any, total_sims: int) -> None:
    """
    Proceso dedicado a escribir en archivos compartidos.
    Escucha la cola hasta recibir `total_sims` resultados,
    luego guarda la estrategia final y termina.
    """
    from engine.estrategia  import (
        cargar_estrategia, guardar_estrategia, registrar_fin_partida,
        snapshot_archetype, mostrar_diff_archetype,
    )
    from engine.save_manager import registrar_muerte
    from engine.personaje    import Sobreviviente

    estrategia = cargar_estrategia()
    recibidos  = 0

    while recibidos < total_sims:
        try:
            run: RunResult = queue.get(timeout=300)  # 5 min por sim como máximo.
        except Exception:
            break

        if run is _SENTINEL:
            break

        try:
            personaje = Sobreviviente.desde_dict(run.personaje_dict)

            # Capturar estado ANTES de actualizar.
            snap = snapshot_archetype(personaje, estrategia)

            registrar_fin_partida(
                personaje,
                estrategia,
                run.causa_muerte,
                run.zonas_visitadas,
                run.zona_muerte,
            )

            pos = registrar_muerte(personaje, run.causa_muerte)

            print(
                f"  [SIM {run.sim_id}] ✓ {run.nombre_completo} "
                f"({run.background}) — {run.dias_vividos}d "
                f"{run.expediciones} exps — {run.causa_muerte} "
                f"— Ranking #{pos}",
                flush=True,
            )
            # Mostrar diff de estrategia para esta sim.
            print(mostrar_diff_archetype(snap, estrategia), flush=True)

        except Exception as e:
            print(f"  [SIM {run.sim_id}] ⚠ Error procesando resultado: {e}", flush=True)

        recibidos += 1

    guardar_estrategia(estrategia)
    print(f"\n  ✔ Estrategia guardada ({recibidos}/{total_sims} partidas procesadas).", flush=True)


# ──────────────────────────────────────────────────────────────
#  ORQUESTADOR PRINCIPAL
# ──────────────────────────────────────────────────────────────

def ejecutar_batch(
    n_workers: int,
    max_dias:  int  = 0,
    exportar:  bool = False,
) -> None:
    """
    Lanza `n_workers` simulaciones en paralelo.
    Cada worker ejecuta una simulación completa (hasta la muerte).

    Parámetros:
        n_workers : número de procesos paralelos (usa resolver_n_workers).
        max_dias  : días máximos por simulación (0 = sin límite).
        exportar  : si True, exporta imágenes PNG (lento, no recomendado en batch).
    """
    total_sims = n_workers

    print(f"\n  ┌{'─' * 52}┐")
    print(f"  │ BATCH: {total_sims} simulaciones · {n_workers} workers paralelos{' ' * max(0, 40 - len(str(total_sims)) - len(str(n_workers)))}│")
    if max_dias:
        print(f"  │ Límite por sim: {max_dias} días{' ' * max(0, 36 - len(str(max_dias)))}│")
    print(f"  └{'─' * 52}┘\n")

    # Cola compartida entre workers y escritor.
    manager = multiprocessing.Manager()
    queue   = manager.Queue()

    # Proceso escritor: arranca primero, escucha la cola.
    escritor = multiprocessing.Process(
        target=_escritor_batch,
        args=(queue, total_sims),
        daemon=False,
    )
    escritor.start()

    # Pool de workers.
    args_workers = [
        (sim_id, queue, max_dias, exportar)
        for sim_id in range(1, total_sims + 1)
    ]

    with multiprocessing.Pool(processes=n_workers) as pool:
        pool.map(_worker_simulacion, args_workers)

    # Esperar a que el escritor termine de procesar todos los resultados.
    escritor.join()
