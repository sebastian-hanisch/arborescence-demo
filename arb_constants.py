"""Konstanten der Arboreszenz-Demo: Instanz-Geometrie, Regler, gemessene Werte, Presets."""
AREA = 100.0
DEPOT_XY = (15.0, 50.0)
N_MIN, N_MAX, DEFAULT_N, N_STEP = 5, 120, 30, 1
K_OPTIONS = (3, 4, 6, 8, 12, 20)
DEFAULT_K = 6
ALPHA_OPTIONS = (0.0, 0.25, 0.5, 1.0, 2.0, 3.0)
DEFAULT_ALPHA = 0.5
ONEWAY_OPTIONS = (0.0, 0.1, 0.2, 0.4, 0.6)
DEFAULT_ONEWAY = 0.0
HILLS = 3
HILL_SIGMA = 25.0
HILL_AMPLITUDE = (10.0, 30.0)
SEED_MAX = 999999
DEFAULT_SEED = 35
KINDS = ("map", "textbook", "nested")
KIND_LABELS = {"map": "Karte (Standorte mit Höhenfeld)", "textbook": "Lehrbuchbeispiel (5 Knoten)", "nested": "Geschachtelt (Worst Case)"}
ROOT_MODES = ("depot", "best")
ROOT_LABELS = {"depot": "Werk (Knoten 0)", "best": "beste Wurzel"}
TREES = ("optimum", "kruskal", "prim", "spt")
TREE_LABELS = {"optimum": "Optimum (Chu-Liu/Edmonds)", "kruskal": "Kruskal, orientiert", "prim": "Prim, gerichtet", "spt": "Kürzeste-Wege-Baum"}
DEFAULT_TREE = "optimum"
SWEEP_SEEDS = tuple(range(100000, 100005))
FEAS_SEEDS = tuple(range(200000, 200050))
N_SWEEP = (10, 20, 40, 80, 120)

# --- Gemessene Werte (MEDIAN über 5 feste Instanzen, Seeds 100000-100004; 30 Knoten, k = 6 nächste Nachbarn, Steigungsaufschlag α = 0.5, keine Einbahnen, Wurzel = Werk; 2026-09-24, alle Werte über
# --- ev.run_config/ev.sweep/ev.feasibility/ev.nested_levels nachgerechnet, s. tests/test_claims.py). Kosten = Summe der Bogenkosten des Baums; Lücke = Kosten / Optimum - 1. Alles ist deterministisch. ---
# OPTIMALITÄT: Chu-Liu/Edmonds stimmt auf 120 zufälligen Kleingraphen (auch nicht lösbaren) mit Brute-Force und auf 200 zufälligen Graphen mit networkx überein; der Dualwert (Summe der abgezogenen
#   Mindest-Zulaufkosten aller Ebenen) ist auf jeder Instanz gleich den Baumkosten.
# PREIS DES IGNORIERENS DER RICHTUNG (naive Antwort: ungerichteter MST auf den Leitungslängen, von der Wurzel aus orientiert): Lücke bei α = 0/0.25/0.5/1/2/3: 0.00/0.00/0.18/1.38/3.73/5.79 %; gerichtetes
#   Prim 0.00/0.00/0.00/0.84/5.65/11.6 %; Kürzeste-Wege-Baum 67.9/69.3/69.6/71.4/79.7/86.7 %. Bei α = 0 (symmetrisch) ist der Kruskal-Baum exakt optimal - Chu-Liu/Edmonds kontrahiert dort trotzdem
#   (im Mittel 22.0 Kreise). Der Kürzeste-Wege-Baum minimiert jeden einzelnen Weg, nicht die Summe der Bogenkosten.
# EINBAHNEN (Anteil q der Knotenpaare mit nur einer Richtung, 0/0.1/0.2/0.4/0.6): "Kruskal orientiert" liefert keinen gültigen Baum in 0/80/100/100/100 % der Instanzen (ein benötigter Bogen fehlt);
#   gerichtetes Prim ist immer gültig, aber 0.00/0.12/1.46/3.92/6.32 % teurer als das Optimum. Über 50 Instanzen bei q = 0.4: Kruskal in 100 % ungültig.
# KREISE: der billigste Zulauf je Knoten enthält in 100 % der Instanzen mindestens einen Kreis (50 Instanzen: im Mittel 8.1, höchstens 11), und jeder dieser Kreise hat die Länge 2 (zwei Nachbarn wählen
#   einander); Kontraktionen im Mittel 20.8 (höchstens 28), höchstens 18 Ebenen bei n = 30.
# EBENEN UND AUFWAND: die Zahl der Ebenen wächst mit n (Erwartung "kaum" widerlegt): n = 10/20/40/80/120 gibt 4/6/10/18/17 Ebenen, 5/12/27/65/97 Kontraktionen und 5.9/9.3/12.3/20.5/18.9 Elementarschritte
#   je Bogen. Worst Case (geschachtelte Instanz): n = 5/10/20/40/80 braucht genau n - 1 Ebenen und 41/206/911/3821/15641 Schritte (quadratisch).
# FREIE WURZEL: die beste Wurzel spart im Median 1.69 % gegenüber dem Werk (n = 30, α = 0.5); bei α = 3 sind es 8.60 %, bei α = 0 nichts (symmetrisch).

PRESETS = {
    "Standardfall (Voreinstellung)": {"kind": "map", "n": 30, "k": 6, "alpha": 0.5, "oneway": 0.0, "seed": 35, "root_mode": "depot", "tree": "optimum"},
    "Symmetrisch (α = 0)": {"kind": "map", "n": 30, "k": 6, "alpha": 0.0, "oneway": 0.0, "seed": 35, "root_mode": "depot", "tree": "kruskal"},
    "Starke Steigung (α = 3)": {"kind": "map", "n": 30, "k": 6, "alpha": 3.0, "oneway": 0.0, "seed": 35, "root_mode": "depot", "tree": "prim"},
    "Einbahn-Trassen (q = 0,4)": {"kind": "map", "n": 30, "k": 6, "alpha": 0.5, "oneway": 0.4, "seed": 35, "root_mode": "depot", "tree": "kruskal"},
    "Freie Wurzel": {"kind": "map", "n": 30, "k": 6, "alpha": 0.5, "oneway": 0.0, "seed": 35, "root_mode": "best", "tree": "optimum"},
    "Lehrbuchbeispiel": {"kind": "textbook", "n": 30, "k": 6, "alpha": 0.5, "oneway": 0.0, "seed": 35, "root_mode": "depot", "tree": "kruskal"},
    "Geschachtelt (Worst Case)": {"kind": "nested", "n": 20, "k": 6, "alpha": 0.5, "oneway": 0.0, "seed": 35, "root_mode": "depot", "tree": "optimum"},
    "Große Instanz (n = 120)": {"kind": "map", "n": 120, "k": 6, "alpha": 0.5, "oneway": 0.0, "seed": 35, "root_mode": "depot", "tree": "optimum"},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "30 Knoten, k = 6, Seed 35, α = 0.5: das Optimum kostet 392.23 und braucht 7 Ebenen mit 23 Kontraktionen (der billigste Zulauf je Knoten enthält 10 Zweier-Kreise). Der orientierte Kruskal-Baum ist 1.09 % teurer, Prim gerichtet ebenfalls 1.09 %, der Kürzeste-Wege-Baum 87.1 %.",
    "Symmetrisch (α = 0)": "Ohne Steigungsaufschlag sind die Kosten symmetrisch: der orientierte Kruskal-Baum ist exakt optimal (375.50, Lücke 0). Chu-Liu/Edmonds kontrahiert trotzdem 24 Kreise in 7 Ebenen - das Ergebnis ist der ungerichtete MST, aber der Weg dorthin braucht die Kontraktion.",
    "Starke Steigung (α = 3)": "Bergauf kostet dreimal die Höhendifferenz extra: das Optimum kostet 432.72; der orientierte Kruskal-Baum ist 15.9 % teurer, Prim gerichtet 17.9 %, der Kürzeste-Wege-Baum 104.5 %. Je stärker die Richtung zählt, desto mehr verliert man, wenn man sie ignoriert.",
    "Einbahn-Trassen (q = 0,4)": "40 % der Knotenpaare haben nur eine Richtung. Der ungerichtete MST lässt sich nicht mehr orientieren (Bogen 19→5 fehlt): \"Kruskal orientiert\" liefert keinen Baum. Chu-Liu/Edmonds findet das Optimum (410.42); Prim gerichtet ist gültig und hier ebenfalls optimal.",
    "Freie Wurzel": "Statt des Werks (Knoten 0) die beste Wurzel: Knoten 12 gibt 388.85 statt 392.23 (0.86 % billiger). Dazu läuft Chu-Liu/Edmonds für jede der 30 möglichen Wurzeln: 59 052 Elementarschritte gegen 1772 für das Werk allein.",
    "Lehrbuchbeispiel": "Fünf Knoten A bis E, acht Bögen. Der billigste Zulauf je Knoten enthält den Kreis C↔D (Kosten 14 abgezogen), die Kontraktion erzeugt den Kreis {C, D}↔B (1 abgezogen), dann bleibt A→{B, C, D} (2). Optimum 17 = 14 + 1 + 2 (Dualwert); der orientierte ungerichtete MST kostet 19.",
    "Geschachtelt (Worst Case)": "Eine Linie, an der jede Kontraktion genau einen Zweier-Kreis schließt: n = 20 braucht 19 Ebenen und 911 Schritte (bei n = 80: 79 Ebenen, 15 641 Schritte, quadratisch). Die einfachen Verfahren finden hier dasselbe Optimum (218) - es geht um den Aufwand.",
    "Große Instanz (n = 120)": "120 Knoten, 872 Bögen: 22 Ebenen mit 105 Kontraktionen, 17 209 Elementarschritte; der orientierte Kruskal-Baum ist nur 0.05 % teurer, der Kürzeste-Wege-Baum 83.5 %.",
}
# Beobachtete Spannweite des MEDIANS der optimalen Kosten über die 5 festen Instanzen (mit Sicherheitsabstand); nur Karten-Presets.
PRESET_EXPECTED_BANDS = {
    "Standardfall (Voreinstellung)": (350.0, 410.0),
    "Symmetrisch (α = 0)": (335.0, 395.0),
    "Starke Steigung (α = 3)": (400.0, 470.0),
    "Einbahn-Trassen (q = 0,4)": (390.0, 460.0),
    "Freie Wurzel": (345.0, 405.0),
    "Große Instanz (n = 120)": (710.0, 830.0),
}
