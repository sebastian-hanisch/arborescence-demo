"""Auswertung: was kostet es, die Richtung zu ignorieren, wie oft enthält der billigste Zulauf je Knoten Kreise, wie viele Kontraktionsebenen braucht Chu-Liu/Edmonds, wie viel spart die freie Wurzel?
Verfahren auf derselben Instanz: das Optimum (Chu-Liu/Edmonds), die naive Antwort "ungerichteter MST (Kruskal auf den Leitungslängen), von der Wurzel aus orientiert", gerichtetes Prim und der
Kürzeste-Wege-Baum. Kosten sind die Summe der Bogenkosten des Baums. Alles ist deterministisch: Kennzahlen laufen über 5 feste Instanzen (Seeds 100000-100004), Median mit 10./90. Perzentil.

- **Lücke** = Kosten / Optimum − 1 in Prozent (nur über Instanzen, in denen das Verfahren einen gültigen Baum liefert).
- **Ungültig** = das Verfahren liefert keinen Baum (bei "Kruskal orientiert": ein benötigter Bogen fehlt, Einbahn).
- **Schritt-1-Kreise** = Kreise unter den billigsten Zuläufen je Knoten (dann ist Schritt 1 allein kein Baum).
- **Ebenen** = Ebenen des Chu-Liu/Edmonds-Laufs (Ebene 0 = Originalgraph; jede Kontraktion fügt eine hinzu)."""

from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

import arb_algorithm as A
import arb_constants as C
import arb_scenario as S

INF = float("inf")
METHODS = ("kruskal", "prim", "spt")
METHOD_LABELS = {"kruskal": "Kruskal, orientiert", "prim": "Prim, gerichtet", "spt": "Kürzeste-Wege-Baum"}


@dataclass(frozen=True)
class Settings:
    kind: str = "map"
    n: int = C.DEFAULT_N
    k: int = C.DEFAULT_K
    alpha: float = C.DEFAULT_ALPHA
    oneway: float = C.DEFAULT_ONEWAY
    seed: int = C.DEFAULT_SEED
    root_mode: str = "depot"


@lru_cache(maxsize=256)
def instance_of(settings):
    if settings.kind == "textbook":
        return S.textbook_instance()
    if settings.kind == "nested":
        return S.nested_instance(max(3, settings.n))
    return S.generate(settings.n, settings.k, settings.alpha, settings.oneway, settings.seed)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    root: int
    opt: object                 # ArbResult für die gewählte Wurzel
    depot_opt: object           # ArbResult für das Werk (Knoten 0)
    trees: dict                 # Verfahren -> TreeResult (für die gewählte Wurzel)
    step1_cycles: list          # Kreise des billigsten Zulaufs je Knoten (Werk als Wurzel)
    root_ops: int               # Elementarschritte aller Wurzelversuche (nur bei root_mode "best")

    @property
    def arcs(self):
        return self.inst.arcs

    def tree_of(self, name):
        if name == "optimum":
            return list(self.opt.tree)
        return list(self.trees[name].tree)

    def gap(self, name):
        r = self.trees[name]
        return 100.0 * (r.cost / self.opt.cost - 1.0) if r.valid and self.opt.cost > 0 else None

    @property
    def levels(self):
        return len(self.opt.levels)

    @property
    def contractions(self):
        return self.opt.contractions

    @property
    def ops_per_arc(self):
        return self.opt.ops / max(1, self.inst.m)

    @property
    def root_gain(self):
        """Ersparnis der gewählten Wurzel gegenüber dem Werk in Prozent (0 beim Werk)."""
        return 100.0 * (1.0 - self.opt.cost / self.depot_opt.cost) if self.depot_opt.cost > 0 else 0.0


def analyse(settings):
    inst = instance_of(settings)
    depot = A.chu_liu_edmonds(inst.n, inst.arcs, inst.root)
    root, opt, root_ops = inst.root, depot, 0
    if settings.root_mode == "best":
        root, opt, root_ops = A.best_root(inst.n, inst.arcs)
    trees = {"kruskal": A.kruskal_oriented(inst.n, inst.arcs, root), "prim": A.prim_directed(inst.n, inst.arcs, root), "spt": A.shortest_path_tree(inst.n, inst.arcs, root)}
    _best, cycles, _cost = A.min_incoming(inst.n, inst.arcs, inst.root)
    return Analysis(settings, inst, root, opt, depot, trees, cycles, root_ops)


# --- Sweeps ---------------------------------------------------------------------------------------------------------------------------------------


def _stats(values):
    values = [v for v in values if v is not None and not np.isnan(v) and v != INF]
    if not values:
        return float("nan"), float("nan"), float("nan")
    return float(np.median(values)), float(np.percentile(values, 10)), float(np.percentile(values, 90))


def run_config(base, seeds=C.SWEEP_SEEDS, **changes):
    s0 = replace(base, **changes)
    rows = [analyse(replace(s0, seed=seed)) for seed in seeds]
    out = {"n_runs": len(rows), "feasible_share": 100.0 * sum(r.opt.feasible for r in rows) / len(rows)}
    for name in METHODS:
        out[f"invalid_{name}"] = 100.0 * sum(not r.trees[name].valid for r in rows) / len(rows)
    for key, values in (
        *[(f"gap_{name}", [r.gap(name) for r in rows]) for name in METHODS],
        ("cost", [r.opt.cost for r in rows]),
        ("arcs", [float(r.inst.m) for r in rows]),
        ("levels", [float(r.levels) for r in rows]),
        ("contractions", [float(r.contractions) for r in rows]),
        ("ops", [float(r.opt.ops) for r in rows]),
        ("ops_per_arc", [r.ops_per_arc for r in rows]),
        ("step1_cycles", [float(len(r.step1_cycles)) for r in rows]),
        ("root_gain", [r.root_gain for r in rows]),
    ):
        out[key], out[f"{key}_lo"], out[f"{key}_hi"] = _stats(values)
    out["step1_cycle_share"] = 100.0 * sum(bool(r.step1_cycles) for r in rows) / len(rows)
    return out


SWEEP_VALUES = {"alpha": C.ALPHA_OPTIONS, "oneway": C.ONEWAY_OPTIONS, "n": C.N_SWEEP, "k": (3, 4, 6, 12, 20)}
SWEEP_LABELS = {"alpha": "Steigungsaufschlag α", "oneway": "Einbahn-Anteil q", "n": "Knoten n", "k": "Nächste Nachbarn k"}


def sweep(param, base=Settings(), values=None):
    values = SWEEP_VALUES[param] if values is None else values
    return [{"value": v, **run_config(base, **{param: v})} for v in values]


def feasibility(base, seeds=C.FEAS_SEEDS):
    """Wie oft scheitern die naiven Antworten? Über `seeds` Instanzen: Anteil, in denen "Kruskal orientiert" keinen Baum liefert, Anteil mit Kreis unter den billigsten Zuläufen, Kreise und Kontraktionen
    im Mittel und im Größten, größte Zahl von Ebenen."""
    an = [analyse(replace(base, seed=seed)) for seed in seeds]
    cyc = [len(a.step1_cycles) for a in an]
    con = [a.contractions for a in an]
    return {"n_runs": len(an), "kruskal_invalid": 100.0 * sum(not a.trees["kruskal"].valid for a in an) / len(an), "prim_invalid": 100.0 * sum(not a.trees["prim"].valid for a in an) / len(an),
            "step1_cycle_share": 100.0 * sum(c > 0 for c in cyc) / len(an), "cycles_mean": float(np.mean(cyc)), "cycles_max": int(max(cyc)), "contractions_mean": float(np.mean(con)),
            "contractions_max": int(max(con)), "levels_max": int(max(a.levels for a in an)), "cycle_len_mean": float(np.mean([len(c) for a in an for c in a.step1_cycles])) if any(cyc) else 0.0}


def nested_levels(ns=(5, 10, 20, 40, 80)):
    """Der Worst Case: Ebenen und Elementarschritte an der geschachtelten Instanz."""
    rows = []
    for n in ns:
        res = A.chu_liu_edmonds(n, S.nested_instance(n).arcs, 0)
        rows.append({"n": n, "levels": len(res.levels), "ops": res.ops, "arcs": S.nested_instance(n).m})
    return rows
