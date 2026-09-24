"""Presets: Vollständigkeit, gültige Werte, der Median der optimalen Kosten bleibt in der gemessenen Spannweite, und jedes Preset zeigt, was sein Name und sein Hilfetext sagen."""

import pytest

import arb_constants as C
import arb_evaluation as ev
import arb_presets as P


def _settings(p):
    return ev.Settings(kind=p["kind"], n=p["n"], k=p["k"], alpha=p["alpha"], oneway=p["oneway"], seed=p["seed"], root_mode=p["root_mode"])


def _analyse(name):
    return ev.analyse(_settings(C.PRESETS[name]))


def test_every_preset_has_help_and_the_map_presets_a_band():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 8
    for name, p in C.PRESETS.items():
        assert set(p) == set(P.PRESET_KEYS) and C.PRESET_HELP[name]
    assert set(C.PRESET_EXPECTED_BANDS) == {n for n, p in C.PRESETS.items() if p["kind"] == "map"}


def test_preset_values_are_valid_members_of_the_controls():
    for p in C.PRESETS.values():
        assert p["kind"] in C.KINDS and p["k"] in C.K_OPTIONS and p["alpha"] in C.ALPHA_OPTIONS and p["oneway"] in C.ONEWAY_OPTIONS and p["root_mode"] in C.ROOT_MODES and p["tree"] in C.TREES
        assert C.N_MIN <= p["n"] <= C.N_MAX and 0 <= p["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings_and_the_defaults_of_the_specs():
    p = C.PRESETS["Standardfall (Voreinstellung)"]
    assert _settings(p) == ev.Settings() and p["tree"] == C.DEFAULT_TREE
    assert all(P.SETTING_SPECS[k].default == v for k, v in (("tree_select", p["tree"]), ("alpha_select", p["alpha"]), ("k_select", p["k"]), ("root_select", p["root_mode"]), ("kind_select", p["kind"])))


@pytest.mark.parametrize("name", list(C.PRESET_EXPECTED_BANDS))
def test_map_preset_median_optimal_cost_stays_in_the_measured_band(name):
    lo, hi = C.PRESET_EXPECTED_BANDS[name]
    assert lo <= ev.run_config(_settings(C.PRESETS[name]))["cost"] <= hi


def test_standard_preset_numbers():
    a = _analyse("Standardfall (Voreinstellung)")
    assert round(a.opt.cost, 2) == 392.23 and (a.levels, a.contractions, len(a.step1_cycles)) == (7, 23, 10) and all(len(c) == 2 for c in a.step1_cycles)
    assert round(a.gap("kruskal"), 2) == 1.09 and round(a.gap("prim"), 2) == 1.09 and round(a.gap("spt"), 1) == 87.1


def test_symmetric_preset_has_no_gap_but_still_contracts():
    a = _analyse("Symmetrisch (α = 0)")
    assert round(a.opt.cost, 2) == 375.5 and a.gap("kruskal") == pytest.approx(0.0, abs=1e-9) and (a.contractions, a.levels) == (24, 7)


def test_steep_preset_gaps():
    a = _analyse("Starke Steigung (α = 3)")
    assert round(a.opt.cost, 2) == 432.72 and round(a.gap("kruskal"), 1) == 15.9 and round(a.gap("prim"), 1) == 17.9 and round(a.gap("spt"), 1) == 104.5


def test_oneway_preset_makes_kruskal_invalid():
    a = _analyse("Einbahn-Trassen (q = 0,4)")
    assert not a.trees["kruskal"].valid and a.trees["kruskal"].reason == "Bogen 19→5 fehlt (Einbahn)" and round(a.opt.cost, 2) == 410.42 and a.gap("prim") == pytest.approx(0.0, abs=1e-9)


def test_free_root_preset():
    a = _analyse("Freie Wurzel")
    assert a.root == 12 and round(a.opt.cost, 2) == 388.85 and round(a.depot_opt.cost, 2) == 392.23 and round(a.root_gain, 2) == 0.86 and a.root_ops == 59052 and a.depot_opt.ops == 1772


def test_textbook_preset_by_hand():
    a = _analyse("Lehrbuchbeispiel")
    assert a.opt.cost == 17.0 and a.opt.dual == 17.0 and [lv.reduction for lv in a.opt.levels] == [14.0, 1.0, 2.0] and round(a.gap("kruskal"), 2) == 11.76 and a.trees["kruskal"].cost == 19.0


def test_nested_preset():
    a = _analyse("Geschachtelt (Worst Case)")
    assert a.levels == 19 and a.contractions == 18 and a.opt.ops == 911 and a.opt.cost == 218.0


def test_big_preset():
    a = _analyse("Große Instanz (n = 120)")
    assert (a.inst.m, a.levels, a.contractions, a.opt.ops) == (872, 22, 105, 17209) and round(a.gap("kruskal"), 2) == 0.05 and round(a.gap("spt"), 1) == 83.5


def test_bounds_and_permalink_constants():
    assert P.bounds("n_slider") == (C.N_MIN, C.N_MAX) and P.bounds("seed_input") == (0, C.SEED_MAX)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)
    assert set(P.WIDGET_KEYS) <= set(P.SETTING_SPECS) and len(set(P.WIDGET_KEYS.values())) == len(P.WIDGET_KEYS)


def test_permalink_casters_accept_members_and_reject_everything_else():
    c = P.SETTING_SPECS
    assert c["kind_select"].caster("nested") == "nested" and c["alpha_select"].caster("0.25") == 0.25 and c["oneway_select"].caster("0.4") == 0.4 and c["tree_select"].caster("spt") == "spt"
    for key, bad in (("kind_select", "x"), ("k_select", "7"), ("alpha_select", "0.3"), ("oneway_select", "0.5"), ("root_select", "x"), ("tree_select", "mst")):
        with pytest.raises(ValueError):
            c[key].caster(bad)
