"""Auswertung: Analysis-Felder gegen unabhängige Neuberechnung, run_config/sweep, Machbarkeits-Experiment, Worst Case."""

import pytest

import arb_algorithm as A
import arb_constants as C
import arb_evaluation as ev
import arb_scenario as S

SMALL = dict(seeds=C.SWEEP_SEEDS[:2])


def test_default_settings_come_from_the_constants_and_are_members_of_the_controls():
    s = ev.Settings()
    assert (s.n, s.k, s.alpha, s.oneway, s.seed, s.kind, s.root_mode) == (C.DEFAULT_N, C.DEFAULT_K, C.DEFAULT_ALPHA, C.DEFAULT_ONEWAY, C.DEFAULT_SEED, "map", "depot")
    assert s.k in C.K_OPTIONS and s.alpha in C.ALPHA_OPTIONS and s.oneway in C.ONEWAY_OPTIONS and s.root_mode in C.ROOT_MODES and C.DEFAULT_TREE in C.TREES
    assert set(ev.SWEEP_VALUES["k"]) <= set(C.K_OPTIONS) and max(C.N_SWEEP) <= C.N_MAX and set(ev.SWEEP_VALUES) == set(ev.SWEEP_LABELS)


def test_analysis_fields_match_an_independent_recomputation():
    a = ev.analyse(ev.Settings(seed=7))
    inst = S.generate(30, 6, 0.5, 0.0, 7)
    opt = A.chu_liu_edmonds(inst.n, inst.arcs, 0)
    assert a.opt.cost == pytest.approx(opt.cost) and a.opt.tree == opt.tree and a.root == 0 and a.levels == len(opt.levels) and a.contractions == opt.contractions
    assert a.trees["kruskal"].cost == pytest.approx(A.kruskal_oriented(inst.n, inst.arcs, 0).cost) and a.trees["prim"].cost == pytest.approx(A.prim_directed(inst.n, inst.arcs, 0).cost)
    assert a.gap("kruskal") == pytest.approx(100.0 * (a.trees["kruskal"].cost / opt.cost - 1.0)) and a.gap("prim") >= 0 and a.gap("spt") > 20
    assert a.ops_per_arc == pytest.approx(opt.ops / inst.m) and len(a.step1_cycles) == len(A.min_incoming(inst.n, inst.arcs, 0)[1]) and a.root_gain == 0.0
    assert a.tree_of("optimum") == opt.tree and a.tree_of("prim") == a.trees["prim"].tree


def test_invalid_methods_have_no_gap_and_the_optimum_always_exists():
    a = ev.analyse(ev.Settings(oneway=0.4))
    assert not a.trees["kruskal"].valid and a.gap("kruskal") is None and a.opt.feasible and a.gap("prim") is not None


def test_best_root_analysis_is_never_worse_than_the_depot():
    a = ev.analyse(ev.Settings(root_mode="best"))
    assert a.root != 0 and a.opt.cost < a.depot_opt.cost and a.root_gain == pytest.approx(100.0 * (1.0 - a.opt.cost / a.depot_opt.cost)) and a.root_ops > a.depot_opt.ops
    assert ev.analyse(ev.Settings(root_mode="best", kind="textbook")).opt.cost <= 17.0


@pytest.mark.parametrize("kind", ["textbook", "nested"])
def test_fixture_kinds_are_analysed(kind):
    a = ev.analyse(ev.Settings(kind=kind, n=12))
    assert a.opt.feasible and a.inst.kind == kind
    assert (a.levels, a.contractions) == ((3, 2) if kind == "textbook" else (11, 10))


def test_run_config_keys_ranges_and_base_seed_independence():
    r = ev.run_config(ev.Settings(seed=1, n=20), **SMALL)
    assert r["n_runs"] == 2 and r["feasible_share"] == 100.0
    for key in ("gap_kruskal", "gap_prim", "gap_spt", "cost", "arcs", "levels", "contractions", "ops", "ops_per_arc", "step1_cycles", "root_gain"):
        assert r[f"{key}_lo"] <= r[key] <= r[f"{key}_hi"]
    assert r == pytest.approx(ev.run_config(ev.Settings(seed=999, n=20), **SMALL))


def test_run_config_counts_invalid_shares_and_skips_them_in_the_gaps():
    r = ev.run_config(ev.Settings(n=20, oneway=0.4), **SMALL)
    assert r["invalid_kruskal"] == 100.0 and r["invalid_prim"] == 0.0 and r["gap_kruskal"] != r["gap_kruskal"]


def test_sweep_rows_and_labels():
    rows = ev.sweep("alpha", ev.Settings(seed=0, n=20), values=(0.0, 1.0))
    assert [r["value"] for r in rows] == [0.0, 1.0] and rows[0]["gap_kruskal"] == 0.0 and rows[1]["gap_prim"] >= rows[0]["gap_prim"]
    assert [r["value"] for r in ev.sweep("oneway", ev.Settings(seed=0, n=20), values=(0.0, 0.2))] == [0.0, 0.2]


def test_feasibility_experiment_invariants():
    r = ev.feasibility(ev.Settings(n=20), seeds=C.FEAS_SEEDS[:10])
    assert r["n_runs"] == 10 and 0 <= r["kruskal_invalid"] <= 100 and r["prim_invalid"] == 0.0 and r["cycles_max"] >= r["cycles_mean"] > 0 and r["contractions_max"] >= r["contractions_mean"]
    assert r["levels_max"] >= 2 and r["cycle_len_mean"] >= 2.0
    assert ev.feasibility(ev.Settings(n=20, oneway=0.4), seeds=C.FEAS_SEEDS[:10])["kruskal_invalid"] == 100.0


def test_nested_levels_rows():
    rows = ev.nested_levels((5, 10, 20))
    assert [r["n"] for r in rows] == [5, 10, 20] and [r["levels"] for r in rows] == [4, 9, 19] and rows[2]["ops"] > 3.5 * rows[1]["ops"]
