"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt und jede Ebene, alle Instanztypen und Bäume, Randwerte, Würfel-Knopf, Permalink-Grenzen, Instanzwechsel, Experimente und Sweeps auf Abruf,
Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import arb_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if step != 1:
        at.select_slider(key="arb_step").set_value(step).run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m for m in at.metric if m.label.startswith(label))


def test_default_run_has_no_exception_and_shows_the_four_metrics():
    at = _run()
    _ok(at)
    assert {"Optimum", "Ebenen", "Kruskal orientiert", "Prim gerichtet"} <= {m.label for m in at.metric}
    assert _metric(at, "Optimum").value == "392.23" and _metric(at, "Ebenen").value == "7" and _metric(at, "Ebenen").delta == "23 Kontraktionen"
    assert _metric(at, "Kruskal orientiert").value == "+1.09 %" and _metric(at, "Prim gerichtet").value == "+1.09 %"


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert at.session_state["kind_select"] == p["kind"] and at.session_state["alpha_select"] == p["alpha"] and at.session_state["oneway_select"] == p["oneway"]
    assert at.session_state["root_select"] == p["root_mode"] and at.session_state["tree_select"] == p["tree"] and at.metric


@pytest.mark.parametrize("step", [1, 2, 3, 4])
def test_every_step_runs_for_every_kind(step):
    for kind in C.KINDS:
        at = _run(kind_select=kind, n_slider=12, step=step)
        _ok(at)
        assert at.get("plotly_chart") and at.session_state["arb_step"] == step


def test_level_slider_walks_through_all_levels_and_survives_an_instance_change():
    at = _run(step=3)
    _ok(at)
    assert at.slider(key="arb_level").max == 6
    for lv in (0, 3, 6):
        at.slider(key="arb_level").set_value(lv).run()
        _ok(at)
        assert any(m.value.startswith(f"**Ebene {lv} von 6:**") for m in at.markdown)
    assert any("Kein Kreis mehr" in m.value for m in at.markdown)
    at.session_state["kind_select"] = "textbook"
    at.run()
    _ok(at)
    assert at.session_state["arb_level"] <= 2


def test_textbook_walkthrough_text():
    at = _run(kind_select="textbook", step=3)
    at.slider(key="arb_level").set_value(0).run()
    _ok(at)
    text = next(m.value for m in at.markdown if m.value.startswith("**Ebene 0 von 2:**"))
    assert "5 Knoten, 8 Bögen" in text and "14.00" in text and "1 Kreis(e)" in text
    step2 = _run(kind_select="textbook", step=2)
    assert any("kein Baum" in m.value and "1 Kreis(e)" in m.value for m in step2.markdown)


@pytest.mark.parametrize("tree", C.TREES)
def test_every_tree_view_runs(tree):
    at = _run(step=4, tree_select=tree)
    _ok(at)
    assert at.get("plotly_chart") and any("Kosten" in m.value for m in at.markdown)


def test_invalid_tree_shows_a_warning_instead_of_a_tree():
    at = _run(step=4, oneway_select=0.4, tree_select="kruskal")
    _ok(at)
    assert any("liefert hier keinen Baum" in w.value and "19→5 fehlt" in w.value for w in at.warning)


@pytest.mark.parametrize("kw", [
    dict(n_slider=C.N_MIN), dict(n_slider=C.N_MAX), dict(k_select=C.K_OPTIONS[0]), dict(k_select=C.K_OPTIONS[-1]), dict(alpha_select=C.ALPHA_OPTIONS[-1]), dict(oneway_select=C.ONEWAY_OPTIONS[-1]),
    dict(root_select="best"), dict(root_select="best", kind_select="textbook"), dict(kind_select="nested", n_slider=C.N_MIN), dict(kind_select="nested", n_slider=60),
    dict(n_slider=C.N_MIN, k_select=3, oneway_select=0.6, alpha_select=3.0, root_select="best"),
])
def test_extreme_settings_run(kw):
    for step in (1, 2, 3, 4):
        _ok(_run(step=step, **kw))


def test_dice_button_changes_the_seed():
    at = _run()
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(n="9999", k="7", alpha="0.3", oneway="0.5", root="x", tree="mst", kind="nope").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert ss["n_slider"] == C.N_MAX and (ss["k_select"], ss["alpha_select"], ss["oneway_select"]) == (C.DEFAULT_K, C.DEFAULT_ALPHA, C.DEFAULT_ONEWAY)
    assert (ss["root_select"], ss["tree_select"], ss["kind_select"]) == ("depot", C.DEFAULT_TREE, "map")


def test_permalink_accepts_valid_values():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(kind="map", n="50", k="12", alpha="2.0", oneway="0.2", root="best", tree="prim", seed="7").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["n_slider"], ss["k_select"], ss["alpha_select"], ss["oneway_select"], ss["root_select"], ss["tree_select"], ss["seed_input"]) == (50, 12, 2.0, 0.2, "best", "prim", 7)


def test_sidebar_shows_only_the_controls_that_matter():
    plain = _run()
    assert all(any(w.key == key for w in group) for key, group in (("n_widget", plain.slider), ("k_widget", plain.select_slider), ("alpha_widget", plain.select_slider), ("oneway_widget", plain.select_slider)))
    assert any(n.key == "seed_widget" for n in plain.number_input)
    nested = _run(kind_select="nested")
    assert any(s.key == "n_widget" for s in nested.slider) and not any(s.key == "k_widget" for s in nested.select_slider) and not any(n.key == "seed_widget" for n in nested.number_input)
    textbook = _run(kind_select="textbook")
    assert not any(s.key == "n_widget" for s in textbook.slider) and not any(s.key == "alpha_widget" for s in textbook.select_slider)
    for at in (plain, nested, textbook):
        assert any(r.key == "root_select" for r in at.radio)


def test_changing_the_instance_while_on_step_three_does_not_crash():
    at = _run(step=3)
    _ok(at)
    at.session_state["n_slider"] = C.N_MIN
    at.run()
    _ok(at)
    at.session_state["kind_select"] = "nested"
    at.run()
    _ok(at)


def test_feasibility_experiment_runs_on_demand():
    at = _run(n_slider=30, oneway_select=0.4)
    next(b for b in at.button if b.key == "feas_start").click().run()
    _ok(at)
    assert _metric(at, "Kruskal ungültig").value == "100 %" and _metric(at, "Kruskal ungültig").delta == "Prim: 0 %" and _metric(at, "Schritt 1 mit Kreis").value.endswith("%")


def test_free_root_experiment_runs_on_demand():
    at = _run(n_slider=20)
    next(b for b in at.button if b.key == "root_start").click().run()
    _ok(at)
    assert _metric(at, "Ersparnis").value.endswith("%") and _metric(at, "Optimale Kosten").delta == "beste Wurzel"


def test_worst_case_experiment_runs_on_demand_for_every_instance_kind():
    for kind in ("map", "textbook", "nested"):
        at = _run(kind_select=kind)
        next(b for b in at.button if b.key == "nested_start").click().run()
        _ok(at)
        assert any("Ebenen 4, 9, 19, 39, 79 (immer n − 1)" in c.value for c in at.caption)


@pytest.mark.parametrize("param", ["alpha", "oneway", "n", "k"])
@pytest.mark.parametrize("metric", ["gap", "invalid", "levels", "ops"])
def test_sweeps_run_on_demand_for_every_metric(param, metric):
    at = _run(n_slider=15, sweep_metric=metric)
    at.selectbox(key="sweep_select").set_value(param).run()
    next(b for b in at.button if b.key == "sweep_start").click().run()
    _ok(at)
    assert at.get("plotly_chart")


def test_no_map_experiments_for_the_fixtures():
    for kind in ("textbook", "nested"):
        at = _run(kind_select=kind)
        assert not any(b.key in ("feas_start", "root_start", "sweep_start") for b in at.button)


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Chu, Y. J., & Liu, T. H. (1965)" in m.value and "Edmonds, J. (1967)" in m.value for m in at.markdown)
