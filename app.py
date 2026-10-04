"""Gerichteter Spannbaum (Arboreszenz) – Chu-Liu/Edmonds - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Fünftes Stück der Spannbaum-Reihe der "Konzepte"-Reihe: hat eine Leitung Fließrichtung (bergauf teurer als bergab, Einbahn-Trassen), zählt jeder Bogen einzeln, und Kruskal/Prim sind nicht mehr das richtige
Werkzeug. Chu-Liu/Edmonds wählt je Knoten den billigsten Zulauf, kontrahiert entstehende Kreise, reduziert die Kosten und expandiert am Ende. Gemessen werden der Preis des Ignorierens der Richtung, die Kreise,
die Kontraktionsebenen und der Aufwand, die Einbahn-Falle und die freie Wurzel.

Lauffähig mit: streamlit run app.py
"""

from dataclasses import replace

import streamlit as st

import arb_algorithm as A
import arb_constants as C
from arb_evaluation import METHODS, SWEEP_LABELS, Settings, analyse, feasibility, nested_levels, run_config, sweep
from arb_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    store_from_widget,
    sync_query_params,
)
from arb_visualization import (
    METHOD_COLORS,
    METHOD_LABELS,
    build_first_step,
    build_gap_bars,
    build_instance,
    build_level,
    build_nested,
    build_sweep,
    build_tree,
)

st.set_page_config(page_title="Gerichteter Spannbaum – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(param, base):
    return sweep(param, base)


@st.cache_data(show_spinner=False)
def _feasibility(base):
    return feasibility(base)


@st.cache_data(show_spinner=False)
def _nested():
    return nested_levels()


@st.cache_data(show_spinner=False)
def _root_gain(base):
    return run_config(base)


def de(number):
    return f"{number:,}".replace(",", ".")


def pct(x):
    return "ungültig" if x is None else f"+{x:.2f} %"


st.title("🌳 Gerichteter Spannbaum – die Arboreszenz")
st.markdown(
    """
**Fünftes Stück der Spannbaum-Reihe.** Bisher waren alle Kosten symmetrisch. Hat eine Leitung **Fließrichtung** - bergauf wird Pumpenergie fällig, bergab nicht, manche Trassen sind Einbahnen -, dann zählt jeder
**Bogen** einzeln: gesucht ist der billigste **Verteilbaum ab einer Wurzel** (dem Werk), in dem jeder andere Standort genau **einen Zulauf** hat und alle vom Werk aus erreichbar sind - eine **minimale Arboreszenz**.
Kruskal und Prim sind für ungerichtete Kanten gebaut und liefern hier nicht mehr das Optimum, Kruskal oft gar keinen Baum.

Der richtige Algorithmus ist **Chu-Liu/Edmonds**: je Knoten den billigsten Zulauf wählen; bilden diese Zuläufe **Kreise**, den Kreis zu einem Superknoten **kontrahieren**, die Kosten der Bögen in ihn um den Kreisbogen
senken und von vorn beginnen; am Ende rückwärts expandieren. Hier wird gemessen, **was das Ignorieren der Richtung kostet**, wie oft und wie tief die Kontraktion nötig ist, was **Einbahn-Trassen** anrichten und was
die **freie Wurzel** spart. Aufwand in Elementarschritten, nicht in Laufzeit.
"""
)
st.caption(
    "Setzt auf [kruskal-demo](https://github.com/sebastian-hanisch/kruskal-demo) und [prim-demo](https://github.com/sebastian-hanisch/prim-demo) auf (Kruskal läuft als die naive Antwort mit). "
    "Weitere Stücke der Reihe (alle gebaut): [constrained-mst-demo](https://github.com/sebastian-hanisch/constrained-mst-demo) (Bottleneck-/Grad-/Hop-beschränkt), [cmst-demo](https://github.com/sebastian-hanisch/cmst-demo) (Kapazitierter MST), [steiner-tree-demo](https://github.com/sebastian-hanisch/steiner-tree-demo), [pcst-demo](https://github.com/sebastian-hanisch/pcst-demo) (Prize-Collecting Steiner-Baum), [mst-sensitivity-demo](https://github.com/sebastian-hanisch/mst-sensitivity-demo), [random-spanning-tree-demo](https://github.com/sebastian-hanisch/random-spanning-tree-demo)."
)

with st.expander("So funktioniert Chu-Liu/Edmonds", expanded=True):
    st.markdown(
        """
1. **Billigster Zulauf:** für jeden Knoten außer der Wurzel den billigsten eingehenden Bogen wählen und dessen Kosten von allen Bögen in diesen Knoten abziehen (die Summe der Abzüge ist ein **Dualwert**).
2. **Kein Kreis:** dann bilden die gewählten Bögen schon den Baum - fertig.
3. **Kreise kontrahieren:** jeden Kreis zu einem Superknoten zusammenfassen (Bögen innerhalb fallen weg) und mit den reduzierten Kosten bei 1 beginnen - eine neue **Ebene**.
4. **Expandieren:** rückwärts durch die Ebenen: der Bogen, der in einen Superknoten führt, ersetzt den gewählten Kreisbogen an seinem Zielknoten. Die Summe aller Abzüge ist gleich den Baumkosten: das beweist die Optimalität.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:4], preset_names[4:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

ss = st.session_state
with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                    help="Lehrbuchbeispiel: 5 Knoten, 8 Bögen, zwei Kontraktionen von Hand nachzuvollziehen. Geschachtelt: an dieser Linie braucht der Algorithmus n − 1 Ebenen.")
    if kind in ("map", "nested"):
        n = st.slider("Knoten n", *bounds("n_slider"), value=int(ss["n_slider"]), key="n_widget", on_change=store_from_widget, args=("n_slider",),
                      help="Die Zahl der Ebenen wächst mit n (n = 10/20/40/80/120: 4/6/10/18/17); an der geschachtelten Instanz sind es genau n − 1.")
    else:
        n = C.DEFAULT_N
    if kind == "map":
        k = st.select_slider("Kandidaten: nächste Nachbarn k", options=list(C.K_OPTIONS), value=int(ss["k_select"]), key="k_widget", on_change=store_from_widget, args=("k_select",),
                             help="Je Knoten die k nächsten Nachbarn als Kandidaten, jeweils in beide Richtungen.")
        alpha = st.select_slider("Steigungsaufschlag α", options=list(C.ALPHA_OPTIONS), value=float(ss["alpha_select"]), key="alpha_widget", on_change=store_from_widget, args=("alpha_select",),
                                 format_func=lambda v: "0 (symmetrisch)" if v == 0 else f"{v:g}",
                                 help="Kosten eines Bogens = Länge + α x Höhenunterschied bergauf. Bei α = 0 ist der orientierte Kruskal-Baum exakt optimal; mit α wächst die Lücke (0.18 % bei 0.5, 5.79 % bei 3).")
        oneway = st.select_slider("Einbahn-Anteil q", options=list(C.ONEWAY_OPTIONS), value=float(ss["oneway_select"]), key="oneway_widget", on_change=store_from_widget, args=("oneway_select",),
                                  format_func=lambda v: f"{v:.0%}", help="Anteil der Knotenpaare mit nur einer Richtung. Ab 10 % lässt sich der ungerichtete MST meist nicht mehr orientieren (Kruskal ungültig).")
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        k, alpha, oneway, seed = C.DEFAULT_K, C.DEFAULT_ALPHA, C.DEFAULT_ONEWAY, C.DEFAULT_SEED
    root_mode = st.radio("Wurzel", options=list(C.ROOT_MODES), format_func=lambda v: C.ROOT_LABELS[v], key="root_select",
                         help="Werk = Knoten 0. \"Beste Wurzel\": Chu-Liu/Edmonds für jede mögliche Wurzel, die billigste gewinnt (im Median 1.69 % billiger als das Werk).")

sync_query_params({"kind_select": kind, "n_slider": int(ss["n_slider"]), "k_select": int(ss["k_select"]), "alpha_select": float(ss["alpha_select"]), "oneway_select": float(ss["oneway_select"]),
                   "seed_input": int(ss["seed_input"]), "root_select": root_mode, "tree_select": ss["tree_select"]})

settings = Settings(kind, int(n), int(k), float(alpha), float(oneway), int(seed), root_mode)
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst, opt, root = a.inst, a.opt, a.root
L = a.levels

# --- In Aktion ---------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Chu-Liu/Edmonds in Aktion")
STEP_LABELS = {1: "1 · Instanz", 2: "2 · Billigster Zulauf", 3: "3 · Kontraktion", 4: "4 · Ergebnis"}
step = st.select_slider("Schritt", options=list(STEP_LABELS), key="arb_step", format_func=lambda s: STEP_LABELS[s])
names = inst.labels

if step == 1:
    st.markdown(f"**{inst.n} Knoten**, **{inst.m} Bögen** (Fließrichtung); Wurzel ist " + (f"Knoten {names[root]}" if names else f"Knoten {root}") + " (⭐). Gesucht: für jeden anderen Knoten genau ein Zulauf, alle vom Werk erreichbar.")
    st.plotly_chart(build_instance(inst, root), width="stretch", key="s1_map")
elif step == 2:
    best, cycles, cost1 = A.min_incoming(inst.n, inst.arcs, inst.root)
    if cycles:
        sizes = ", ".join(str(len(c)) for c in cycles[:12]) + (" ..." if len(cycles) > 12 else "")
        st.markdown(f"**Der billigste Zulauf je Knoten kostet zusammen {cost1:.2f} und ist kein Baum:** die gewählten Bögen bilden **{len(cycles)} Kreis(e)** (Längen {sizes}), rot markiert. Zwei Knoten, die einander als "
                    "billigsten Zulauf wählen, sind vom Rest abgeschnitten - deshalb reicht Schritt 1 nicht.")
    else:
        st.markdown(f"**Der billigste Zulauf je Knoten kostet zusammen {cost1:.2f} und bildet schon einen Baum** (kein Kreis): das ist das Optimum.")
    st.plotly_chart(build_first_step(inst, best, cycles, inst.root), width="stretch", key="s2_map")
    st.caption("Blau: der billigste Zulauf je Knoten; rot: Bögen, die einen Kreis bilden. Bei Wurzelwahl \"beste Wurzel\" zeigt dieser Schritt das Werk als Wurzel.")
elif step == 3:
    if "arb_level" in ss:
        ss["arb_level"] = min(max(0, int(ss["arb_level"])), L - 1)
    level = st.slider("Ebene", 0, max(1, L - 1), key="arb_level", help="Ebene 0 = Originalgraph; jede Kontraktion fügt eine Ebene hinzu.") if L > 1 else 0
    level = min(level, L - 1)
    lv = opt.levels[level]
    done = sum(x.reduction for x in opt.levels[: level + 1])
    line = f"**Ebene {level} von {L - 1}:** {lv.n} Knoten, {lv.m} Bögen; der billigste Zulauf je Knoten senkt die Kosten um {lv.reduction:.2f} (bis hier {done:.2f} von {opt.dual:.2f})."
    if lv.cycles:
        line += f" **{len(lv.cycles)} Kreis(e)** (rot umrandet) werden zu Superknoten kontrahiert."
    else:
        line += " **Kein Kreis mehr:** die gewählten Zuläufe bilden einen Baum - danach wird rückwärts expandiert."
    st.markdown(line)
    st.plotly_chart(build_level(inst, opt, level), width="stretch", key=f"s3_map_{level}")
    st.caption("Punktfarbe = Superknoten (gleiche Farbe: schon zusammengefasst), grau = Einzelknoten. Blau: billigster Zulauf je Ebenen-Knoten, rot: Kreis.")
else:
    tree_name = st.radio("Baum zeigen", options=list(C.TREES), format_func=lambda v: C.TREE_LABELS[v], key="tree_widget", horizontal=True, index=list(C.TREES).index(ss["tree_select"]),
                         on_change=store_from_widget, args=("tree_select",),
                         help="Grün: wie das Optimum, orange: weicht ab, grau gestrichelt: Optimum-Bogen fehlt. Kruskal orientiert = ungerichteter MST auf den Leitungslängen, von der Wurzel aus orientiert.")
    shown = a.tree_of(tree_name) if tree_name == "optimum" or a.trees[tree_name].valid else []
    valid = tree_name == "optimum" or a.trees[tree_name].valid
    st.plotly_chart(build_tree(inst, shown, a.tree_of("optimum"), root, valid), width="stretch", key=f"s4_map_{tree_name}")
    if tree_name == "optimum":
        st.markdown(f"**Optimum:** Kosten **{opt.cost:.2f}** = Dualwert {opt.dual:.2f} (Summe aller Abzüge über {L} Ebenen) - Baum und Zertifikat stimmen überein.")
    elif valid:
        r = a.trees[tree_name]
        st.markdown(f"**{METHOD_LABELS[tree_name]}:** ein gültiger Baum mit Kosten {r.cost:.2f}, **{a.gap(tree_name):.2f} % teurer** als das Optimum ({opt.cost:.2f}); {len([i for i in shown if i not in set(a.tree_of('optimum'))])} Bögen weichen ab.")
    else:
        st.warning(f"**{METHOD_LABELS[tree_name]} liefert hier keinen Baum:** {a.trees[tree_name].reason}. Das Optimum ({opt.cost:.2f}) findet Chu-Liu/Edmonds trotzdem.")
    st.plotly_chart(build_gap_bars({"optimum": opt.cost, **{m: (a.trees[m].cost if a.trees[m].valid else None) for m in METHODS}}, opt.cost), width="stretch", key="gap_bars")
    st.caption("Mehrkosten gegen das Optimum. Der Kürzeste-Wege-Baum minimiert jeden einzelnen Weg vom Werk, nicht die Summe der Bogenkosten.")

st.markdown("---")

# --- Aufwand -----------------------------------------------------------------------------------------------------------------------------------

st.markdown("## ⚙️ Was kostet die Richtung?")
st.caption(
    "**Elementarschritte:** je Ebene alle Bögen prüfen (billigster Zulauf), Zeigerschritte der Kreissuche, alle Bögen umbenennen und reduzieren. Diese einfache Umsetzung ist O(n·m); schnellere Varianten (Tarjan, Gabow "
    "u. a.) sind nicht gebaut. Ein Näherungsmaß, **keine Laufzeitmessung**. Die Heuristiken werden hier nur nach Kosten verglichen."
)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Optimum", f"{opt.cost:.2f}", delta=f"Wurzel {names[root] if names else root}", delta_color="off")
m2.metric("Ebenen", str(L), delta=f"{a.contractions} Kontraktionen", delta_color="off")
m3.metric("Kruskal orientiert", pct(a.gap("kruskal")), delta="gegen Optimum", delta_color="off")
m4.metric("Prim gerichtet", pct(a.gap("prim")), delta="gegen Optimum", delta_color="off")
st.caption(f"{de(opt.ops)} Elementarschritte für {inst.m} Bögen ({a.ops_per_arc:.1f} je Bogen); der Kürzeste-Wege-Baum ist {pct(a.gap('spt'))} teurer. Der Dualwert {opt.dual:.2f} ist gleich den Baumkosten.")
if root_mode == "best":
    st.caption(f"Beste Wurzel: Knoten {names[root] if names else root} - {a.root_gain:.2f} % billiger als das Werk ({a.depot_opt.cost:.2f}); {de(a.root_ops)} Elementarschritte über alle Wurzelversuche.")

st.markdown("---")

# --- Experimente auf Abruf ---------------------------------------------------------------------------------------------------------------------

base = replace(settings, seed=0)
if kind == "map":
    st.subheader("🎲 Wie oft scheitern die naiven Antworten?")
    st.caption("50 Instanzen mit den Einstellungen der Seitenleiste (nur der Seed wechselt): Anteil ohne gültigen Baum, Kreise unter den billigsten Zuläufen, Kontraktionen.")
    if st.button("Machbarkeits-Experiment über 50 Instanzen", key="feas_start"):
        ss["feas_done"] = ss.get("feas_done", set()) | {base}
    if base in ss.get("feas_done", set()):
        with st.spinner("Rechne..."):
            res = _feasibility(base)
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Kruskal ungültig", f"{res['kruskal_invalid']:.0f} %", delta=f"Prim: {res['prim_invalid']:.0f} %", delta_color="off")
        f2.metric("Schritt 1 mit Kreis", f"{res['step1_cycle_share']:.0f} %", delta=f"Länge {res['cycle_len_mean']:.1f}", delta_color="off")
        f3.metric("Kreise (Schritt 1)", f"{res['cycles_mean']:.1f}", delta=f"max. {res['cycles_max']}", delta_color="off")
        f4.metric("Kontraktionen", f"{res['contractions_mean']:.1f}", delta=f"max. {res['contractions_max']}", delta_color="off")
        st.caption(f"Über {res['n_runs']} Instanzen; höchstens {res['levels_max']} Ebenen. Kruskal ist ungültig, wenn ein benötigter Bogen in der Fließrichtung fehlt; Schritt 1 enthält fast immer Kreise der Länge 2.")
    st.markdown("---")

    st.subheader("🌐 Die beste Wurzel")
    st.caption("Chu-Liu/Edmonds für jeden möglichen Standort als Wurzel: wie viel billiger ist der beste gegenüber dem Werk? (5 feste Instanzen, Einstellungen der Seitenleiste)")
    if st.button("Freie Wurzel über 5 feste Instanzen berechnen", key="root_start"):
        ss["root_done"] = ss.get("root_done", set()) | {replace(base, root_mode="best")}
    if replace(base, root_mode="best") in ss.get("root_done", set()):
        with st.spinner("Rechne..."):
            rr = _root_gain(replace(base, root_mode="best"))
        r1, r2 = st.columns(2)
        r1.metric("Ersparnis (Median)", f"{rr['root_gain']:.2f} %", delta=f"Band {rr['root_gain_lo']:.2f}–{rr['root_gain_hi']:.2f} %", delta_color="off")
        r2.metric("Optimale Kosten", f"{rr['cost']:.1f}", delta="beste Wurzel", delta_color="off")
    st.markdown("---")

    st.subheader("📐 Sweeps")
    sweep_param = st.selectbox("Welcher Regler soll durchgefahren werden?", list(SWEEP_LABELS), format_func=lambda v: SWEEP_LABELS[v], key="sweep_select")
    metric = st.radio("Kennzahl", options=["gap", "invalid", "levels", "ops"], format_func=lambda v: {"gap": "Mehrkosten der Verfahren", "invalid": "Anteil ungültig", "levels": "Ebenen und Kontraktionen", "ops": "Schritte je Bogen"}[v],
                      key="sweep_metric", horizontal=True)
    if st.button("Sweep über 5 feste Instanzen berechnen (kann einige Sekunden dauern)", key="sweep_start"):
        ss["sweep_done"] = ss.get("sweep_done", set()) | {(sweep_param, base)}
    if (sweep_param, base) in ss.get("sweep_done", set()):
        with st.spinner("Rechne den Sweep über 5 feste Instanzen..."):
            rows_s = _sweep(sweep_param, base)
        label = SWEEP_LABELS[sweep_param]
        if metric == "gap":
            st.plotly_chart(build_sweep(rows_s, label, [(f"gap_{m}", METHOD_LABELS[m], METHOD_COLORS[m]) for m in METHODS], "Mehrkosten gegen das Optimum (%)"), width="stretch", key="sweep_gap")
        elif metric == "invalid":
            st.plotly_chart(build_sweep(rows_s, label, [(f"invalid_{m}", METHOD_LABELS[m], METHOD_COLORS[m]) for m in METHODS], "Instanzen ohne gültigen Baum (%)"), width="stretch", key="sweep_invalid")
        elif metric == "levels":
            st.plotly_chart(build_sweep(rows_s, label, [("levels", "Ebenen", "#2F6B65"), ("contractions", "Kontraktionen", "#e8a13a")], "Anzahl"), width="stretch", key="sweep_levels")
        else:
            st.plotly_chart(build_sweep(rows_s, label, [("ops_per_arc", "Elementarschritte je Bogen", "#2F6B65")], "Schritte je Bogen"), width="stretch", key="sweep_ops")
        st.caption("Median über 5 feste Instanzen (Seeds 100000–100004), Band = 10. bis 90. Perzentil; bei den Mehrkosten nur über Instanzen mit gültigem Baum. Die übrigen Regler stehen wie in der Seitenleiste.")
    st.markdown("---")

st.subheader("🧱 Der Worst Case")
st.caption("An der geschachtelten Instanz kontrahiert jede Ebene genau einen Zweier-Kreis: n − 1 Ebenen, quadratisch viele Schritte.")
if st.button("Worst Case für n = 5 bis 80 berechnen", key="nested_start"):
    ss["nested_done"] = True
if ss.get("nested_done"):
    rows_n = _nested()
    st.plotly_chart(build_nested(rows_n), width="stretch", key="nested")
    st.caption("n = " + ", ".join(str(r["n"]) for r in rows_n) + ": Ebenen " + ", ".join(str(r["levels"]) for r in rows_n) + " (immer n − 1); Elementarschritte " + ", ".join(de(r["ops"]) for r in rows_n) + ".")
st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Richtung ist ein Detail** | Bei kleinem Aufschlag ja (α = 0.5: orientierter Kruskal-Baum nur 0.18 % teurer), bei starker Steigung nein (α = 3: 5.79 %, gerichtetes Prim 11.6 %, Kürzeste-Wege-Baum 86.7 %). Mit Einbahn-Trassen gibt es den ungerichteten Baum in Fließrichtung oft gar nicht (q = 0.1: in 80 % der Instanzen ungültig, ab q = 0.2 in 100 %). | - |
| **Der billigste Zulauf je Knoten reicht** | Er enthält in allen 50 Testinstanzen Kreise (im Mittel 8.1, alle der Länge 2); erst die Kontraktion löst sie auf. | - |
| **Wenige Ebenen** | Die Ebenen wachsen mit n (n = 10/20/40/80/120: 4/6/10/18/17) und im Worst Case auf n − 1 mit quadratisch vielen Schritten (n = 80: 15 641). Diese Umsetzung ist O(n·m). | Tarjan 1977, Gabow u. a. 1986 (nicht gebaut) |
| **Elementarschritte sind Laufzeit** | Nein. Sie zählen Bogenprüfungen und Zeigerschritte einheitlich, ignorieren aber, was sie in einer Sprache kosten. Die Heuristiken werden nur nach Kosten verglichen. | Laufzeitmessung an echten Netzen (nicht gebaut) |
| **Die Wurzel steht fest** | Mit freier Wurzel spart der beste Standort im Median 1.69 % (n = 30, α = 0.5), bei α = 3 sogar 8.60 %, bei α = 0 nichts (symmetrisch); dafür läuft der Algorithmus n-mal. Ein Wald ohne feste Wurzel (Branching) ist nicht gebaut. | Minimum Branching (nicht gebaut) |
| **Synthetisches Modell** | Steigungsaufschlag und Einbahnen sind ein Modell (Punkte im Quadrat, drei Gauß-Hügel, k nächste Nachbarn); keine Kapazitäten, keine echten Rohrnetze. | Echte Trassen (nicht gebaut); Kapazitierter MST: cmst-demo |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** Gegeben ein gerichteter Graph $G = (V, A)$ mit Kosten $c_a$ und eine Wurzel $r$. Gesucht ist $T \subseteq A$ mit $|T| = |V| - 1$, in dem jeder Knoten $v \ne r$ genau einen Zulaufbogen hat und alle
Knoten von $r$ aus erreichbar sind, mit minimalem $\sum_{a \in T} c_a$.

**Kontraktion.** Sei $m_v = \min_{(u,v) \in A} c_{uv}$. Ersetzt man $c_{uv}$ durch $c_{uv} - m_v$, ändern sich alle Arboreszenzen um dieselbe Konstante $\sum_v m_v$, und mindestens ein Zulauf je Knoten kostet 0. Bilden die
Nullbögen einen Kreis $C$, ist in einer optimalen Lösung genau ein Bogen in $C$ nicht gewählt: man kontrahiert $C$ zu einem Knoten, löst das kleinere Problem und expandiert. Die Summe aller abgezogenen $m_v$ über alle
Ebenen ist ein Dualwert und gleich den Kosten der Lösung.

**Symmetrischer Fall.** Gilt $c_{uv} = c_{vu}$, ist jede Arboreszenz ein orientierter Spannbaum, und der minimale Spannbaum, von der Wurzel aus orientiert, ist optimal: die Lücke der naiven Antwort ist genau 0.

**Aufwand.** Jede Ebene kostet $O(m)$, es gibt höchstens $n - 1$ Ebenen: $O(nm)$. Mit besseren Datenstrukturen (Tarjan 1977: $O(m \log n)$; Gabow, Galil, Spencer & Tarjan 1986: $O(n \log n + m)$) geht es schneller.

**Literatur.** Chu, Y. J., & Liu, T. H. (1965). *On the shortest arborescence of a directed graph.* Scientia Sinica 14, 1396-1400. Edmonds, J. (1967). *Optimum branchings.* Journal of Research of the National Bureau
of Standards 71B, 233-240. Tarjan, R. E. (1977). *Finding optimum branchings.* Networks 7(1), 25-35. Gabow, H. N., Galil, Z., Spencer, T., & Tarjan, R. E. (1986). *Efficient algorithms for finding minimum spanning trees in
undirected and directed graphs.* Combinatorica 6(2), 109-122.

Implementiert in `arb_algorithm.py` (`chu_liu_edmonds`, Vergleichsverfahren), `arb_scenario.py` (Instanzen), `arb_evaluation.py` (Kennzahlen, Sweeps, Experimente).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Spannbäume: vom Kruskal bis zum Zufallsbaum](https://sebastianhanisch.net/konzepte-spannbaum.html)."
)
