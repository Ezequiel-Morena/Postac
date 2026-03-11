# ============================================================
# tests/test_batch.py — Tests para el sistema de batch
# ============================================================

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.batch import resolver_n_workers, RunResult


# ──────────────────────────────────────────────────────────────
#  resolver_n_workers
# ──────────────────────────────────────────────────────────────

def test_max_devuelve_cpu_count():
    esperado = max(1, os.cpu_count() or 1)
    assert resolver_n_workers("max") == esperado


def test_max_case_insensitive():
    assert resolver_n_workers("MAX") == resolver_n_workers("max")
    assert resolver_n_workers("Max") == resolver_n_workers("max")


def test_numero_entero_como_string():
    assert resolver_n_workers("3") == 3


def test_numero_entero_directo():
    assert resolver_n_workers(2) == 2


def test_minimo_es_uno():
    assert resolver_n_workers(0)  == 1
    assert resolver_n_workers(-5) == 1


def test_valor_invalido_devuelve_uno():
    assert resolver_n_workers("xyz") == 1
    assert resolver_n_workers(None)  == 1


# ──────────────────────────────────────────────────────────────
#  RunResult
# ──────────────────────────────────────────────────────────────

def test_run_result_es_dataclass():
    r = RunResult(
        sim_id=1,
        personaje_dict={},
        causa_muerte="herida",
        zonas_visitadas=["hospital"],
        zona_muerte="hospital",
        dias_vividos=5,
        expediciones=3,
        nombre_completo="Ana García",
        background="Médico/a",
        archetype="medico",
    )
    assert r.sim_id == 1
    assert r.dias_vividos == 5
    assert r.archetype == "medico"
    assert r.zona_muerte == "hospital"


def test_run_result_sin_zona_muerte():
    r = RunResult(
        sim_id=2,
        personaje_dict={},
        causa_muerte="vejez",
        zonas_visitadas=[],
        zona_muerte=None,
        dias_vividos=100,
        expediciones=50,
        nombre_completo="Juan Pérez",
        background="Granjero/a",
        archetype="granjero",
    )
    assert r.zona_muerte is None
    assert r.zonas_visitadas == []


# ──────────────────────────────────────────────────────────────
#  Import sanity — batch module carga sin errores
# ──────────────────────────────────────────────────────────────

def test_import_batch_no_falla():
    import engine.batch as b
    assert hasattr(b, "ejecutar_batch")
    assert hasattr(b, "resolver_n_workers")
    assert hasattr(b, "_worker_simulacion")
    assert hasattr(b, "_escritor_batch")
