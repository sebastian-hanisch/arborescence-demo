"""Jede Zahl, die App-Text und README nennen, wird hier über die echten Auswertungsfunktionen (ev.run_config / ev.sweep / ev.feasibility / ev.nested_levels) belegt - nie über ein Ad-hoc-Skript.
Bogenkosten sind Gleitkommazahlen, Kennzahlen daher auf Rundungsstellen verglichen; Schrittzahlen und Ebenen sind ganzzahlig."""

from dataclasses import replace
from functools import lru_cache

import pytest

import arb_constants as C
import arb_evaluation as ev

BASE = ev.Settings(seed=0)


@lru_cache(maxsize=None)
def _cfg(**kw):
    return ev.run_config(replace(BASE, **kw))


@lru_cache(maxsize=None)
def _sweep(param, **kw):
    return ev.sweep(param, replace(BASE, **kw))


@lru_cache(maxsize=None)
def _feas(**kw):
    return ev.feasibility(replace(BASE, **kw))


def _col(rows, key, digits=2):
    return [round(r[key], digits) for r in rows]


def test_default_case_medians_over_five_instances():
    r = _cfg()
    assert round(r["cost"], 2) == 379.87 and round(r["gap_kruskal"], 2) == 0.18 and round(r["gap_prim"], 2) == 0.0 and round(r["gap_spt"], 1) == 69.6
    assert (r["levels"], r["contractions"], r["ops"]) == (8.0, 19.0, 2397.0) and r["feasible_share"] == 100.0


def test_price_of_ignoring_the_direction_over_alpha():
    rows = _sweep("alpha")
    assert [r["value"] for r in rows] == [0.0, 0.25, 0.5, 1.0, 2.0, 3.0]
    assert _col(rows, "gap_kruskal") == [0.0, 0.0, 0.18, 1.38, 3.73, 5.79] and _col(rows, "gap_prim") == [0.0, 0.0, 0.0, 0.84, 5.65, 11.6] and _col(rows, "gap_spt", 1) == [67.9, 69.3, 69.6, 71.4, 79.7, 86.7]
    assert all(r["invalid_kruskal"] == r["invalid_prim"] == r["invalid_spt"] == 0.0 for r in rows)


def test_symmetric_costs_make_the_kruskal_tree_exactly_optimal_but_chu_liu_still_contracts():
    r = _cfg(alpha=0.0)
    assert r["gap_kruskal"] == pytest.approx(0.0, abs=1e-9) and r["gap_prim"] == pytest.approx(0.0, abs=1e-9) and r["contractions"] >= 15
    assert round(_feas(alpha=0.0)["contractions_mean"], 1) == 22.0


def test_one_way_pipes_break_the_naive_answer():
    rows = _sweep("oneway")
    assert [r["value"] for r in rows] == [0.0, 0.1, 0.2, 0.4, 0.6] and [r["invalid_kruskal"] for r in rows] == [0.0, 80.0, 100.0, 100.0, 100.0]
    assert _col(rows, "gap_prim") == [0.0, 0.12, 1.46, 3.92, 6.32] and all(r["invalid_prim"] == 0.0 and r["feasible_share"] == 100.0 for r in rows) and _col(rows, "arcs", 0) == [228, 216, 208, 184, 163]
    assert _feas(oneway=0.4)["kruskal_invalid"] == 100.0 and _feas(oneway=0.4)["prim_invalid"] == 0.0


def test_cheapest_incoming_arcs_always_contain_cycles_of_length_two():
    f = _feas()
    assert f["step1_cycle_share"] == 100.0 and round(f["cycles_mean"], 1) == 8.1 and f["cycles_max"] == 11 and f["cycle_len_mean"] == 2.0
    assert round(f["contractions_mean"], 1) == 20.8 and f["contractions_max"] == 28 and f["levels_max"] == 18 and f["kruskal_invalid"] == 0.0


def test_levels_and_effort_grow_with_n():
    rows = _sweep("n")
    assert [r["value"] for r in rows] == [10, 20, 40, 80, 120] and _col(rows, "levels", 0) == [4, 6, 10, 18, 17] and _col(rows, "contractions", 0) == [5, 12, 27, 65, 97]
    assert _col(rows, "ops_per_arc", 1) == [5.9, 9.3, 12.3, 20.5, 18.9]


def test_worst_case_needs_n_minus_1_levels_and_quadratic_effort():
    rows = ev.nested_levels()
    assert [r["n"] for r in rows] == [5, 10, 20, 40, 80] and [r["levels"] for r in rows] == [4, 9, 19, 39, 79] and [r["ops"] for r in rows] == [41, 206, 911, 3821, 15641]


def test_free_root_saves_about_one_and_a_half_percent():
    r = _cfg(root_mode="best")
    assert round(r["root_gain"], 2) == 1.69 and r["root_gain_lo"] >= 0.0 and r["root_gain_lo"] <= r["root_gain"] <= r["root_gain_hi"]
    assert _cfg()["root_gain"] == 0.0


def test_free_root_matters_more_with_steep_slopes():
    gains = {a: _cfg(alpha=a, root_mode="best")["root_gain"] for a in (0.0, 0.5, 3.0)}
    assert round(gains[3.0], 2) == 8.6 and gains[0.0] < gains[0.5] < gains[3.0] and round(gains[0.5], 2) == 1.69
