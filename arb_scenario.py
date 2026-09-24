"""Die Instanz dieser Demo: ein Verteilnetz mit Fließrichtung. n Standorte liegen auf einer Karte mit Höhenfeld; Knoten 0 ist das Werk (die Wurzel). Ein Bogen u → v ist ein Rohr in Fließrichtung; er kostet
Länge + α · max(0, h(v) − h(u)): bergauf wird Pumpenergie fällig (Steigungsaufschlag α), bergab nicht. Mit α = 0 sind die Kosten symmetrisch. Kandidaten sind die k nächsten Nachbarn je Knoten (beide
Richtungen als getrennte Bögen); mit dem Einbahn-Anteil q hat jedes Knotenpaar mit Wahrscheinlichkeit q nur EINE zufällige Richtung. Damit alle Instanzen lösbar sind, wird die Erreichbarkeit von der Wurzel
durch Wiederherstellen entfernter Gegenrichtungen garantiert.

Bögen sind Tupel (u, v, Kosten, Länge), sortiert nach (u, v). Zwei Fixtures: ein Lehrbuchbeispiel (5 Knoten, zwei Kontraktionen von Hand nachvollziehbar) und eine geschachtelte Instanz, an der Chu-Liu/Edmonds
n − 1 Ebenen braucht."""

from dataclasses import dataclass
from math import cos, pi, sin

import numpy as np

import arb_constants as C

INSTANCE_KINDS = C.KINDS


@dataclass(frozen=True)
class Instance:
    xy: np.ndarray                 # (n, 2)
    arcs: tuple                    # ((u, v, Kosten, Länge), ...) sortiert nach (u, v)
    root: int = 0
    kind: str = "map"
    heights: object = None         # Höhe je Knoten (Karte) oder None
    alpha: float = 0.0
    oneway: float = 0.0
    seed: int = 0
    labels: object = None

    @property
    def n(self):
        return len(self.xy)

    @property
    def m(self):
        return len(self.arcs)


def _height(xy, rng):
    centers = rng.uniform(0.0, C.AREA, size=(C.HILLS, 2))
    amp = rng.uniform(*C.HILL_AMPLITUDE, size=C.HILLS)
    d2 = ((xy[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    return (amp[None, :] * np.exp(-d2 / (2.0 * C.HILL_SIGMA ** 2))).sum(axis=1)


def _candidate_pairs(n, k, dist):
    if k >= n - 1:
        return {(u, v) for u in range(n) for v in range(u + 1, n)}
    pairs = set()
    order = np.argsort(dist + np.diag(np.full(n, np.inf)), axis=1, kind="stable")
    for u in range(n):
        for v in order[u, :k]:
            pairs.add((min(u, int(v)), max(u, int(v))))
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in pairs:
        parent[find(u)] = find(v)
    while len({find(x) for x in range(n)}) > 1:
        best = None
        for u in range(n):
            for v in range(u + 1, n):
                if find(u) != find(v) and (best is None or (dist[u, v], u, v) < best):
                    best = (dist[u, v], u, v)
        _, u, v = best
        pairs.add((u, v))
        parent[find(u)] = find(v)
    return pairs


def generate(n=C.DEFAULT_N, k=C.DEFAULT_K, alpha=C.DEFAULT_ALPHA, oneway=C.DEFAULT_ONEWAY, seed=C.DEFAULT_SEED):
    """Werk + n - 1 weitere Standorte (insgesamt n Knoten); Knoten 0 ist die Wurzel."""
    n = int(n)
    rng = np.random.default_rng([int(seed), 606])
    xy = np.vstack([np.array([C.DEPOT_XY]), rng.uniform(0.0, C.AREA, size=(n - 1, 2))])
    h = _height(xy, rng)
    diff = xy[:, None, :] - xy[None, :, :]
    dist = np.hypot(diff[:, :, 0], diff[:, :, 1])
    pairs = sorted(_candidate_pairs(n, int(k), dist))
    arcs = {}
    removed = []
    for u, v in pairs:
        both = [(u, v), (v, u)]
        if oneway > 0 and rng.random() < oneway:
            drop = both[int(rng.integers(2))]
            removed.append(drop)
            both.remove(drop)
        for a, b in both:
            arcs[(a, b)] = (a, b, float(dist[a, b] + alpha * max(0.0, h[b] - h[a])), float(dist[a, b]))
    while True:                                                                  # Erreichbarkeit von der Wurzel wiederherstellen
        seen, todo = {0}, [0]
        out = {}
        for a, b in arcs:
            out.setdefault(a, []).append(b)
        while todo:
            x = todo.pop()
            for y in out.get(x, []):
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
        if len(seen) == n:
            break
        fix = min((dist[a, b], a, b) for a, b in removed if a in seen and b not in seen)
        _, a, b = fix
        removed.remove((a, b))
        arcs[(a, b)] = (a, b, float(dist[a, b] + alpha * max(0.0, h[b] - h[a])), float(dist[a, b]))
    return Instance(xy, tuple(arcs[key] for key in sorted(arcs)), 0, "map", h, float(alpha), float(oneway), int(seed))


# --- Handgebaute Fixtures -----------------------------------------------------------------------------------------------------------------------

TEXTBOOK_XY = [(8.0, 50.0), (72.0, 18.0), (40.0, 50.0), (72.0, 82.0), (95.0, 50.0)]
# (von, nach, Kosten, Länge) - Länge = die billigere der beiden Richtungen, wie sie ein "ungerichteter" Planer ansetzen würde
TEXTBOOK_ARCS = [(0, 2, 5.0, 5.0), (1, 2, 3.0, 3.0), (2, 1, 5.0, 3.0), (3, 1, 3.0, 3.0), (2, 3, 8.0, 2.0), (3, 2, 2.0, 2.0), (2, 4, 1.0, 1.0), (4, 2, 8.0, 1.0)]


def textbook_instance():
    """Fünf Knoten A bis E (Wurzel A), acht Bögen. Optimum 17: A→C (5), C→D (8), D→B (3), C→E (1). Der billigste Zulauf je Knoten enthält den Kreis C↔D; nach der Kontraktion entsteht der Kreis {C, D} ↔ B.
    Der von A aus orientierte ungerichtete MST (C–E, C–D, B–C, A–C) kostet 19."""
    return Instance(np.array(TEXTBOOK_XY), tuple(sorted(TEXTBOOK_ARCS)), 0, "textbook", labels=("A", "B", "C", "D", "E"))


def nested_instance(n):
    """Worst Case für die Zahl der Kontraktionsebenen: Knoten 1 bis n - 1 auf einer Linie, Bogen i → i + 1 kostet 2, i + 1 → i kostet 1, die Wurzel erreicht nur den letzten Knoten (teuer). Jede Ebene
    kontrahiert genau ein Zweier-Kreis: n - 1 Ebenen. Optimum: Wurzel → n − 1, dann jeder Bogen abwärts (i + 1 → i, Kosten 1)."""
    if n < 3:
        raise ValueError("mindestens drei Knoten")
    big = 10.0 * n
    arcs = [(0, n - 1, big, big)]
    for i in range(1, n - 1):
        arcs.append((i, i + 1, 2.0, 1.0))
        arcs.append((i + 1, i, 1.0, 1.0))
    ang = [pi * (0.15 + 0.7 * (i / max(1, n - 1))) for i in range(n)]
    xy = np.array([(50.0 + 40.0 * cos(a), 15.0 + 70.0 * sin(a)) for a in ang])
    xy[0] = (8.0, 50.0)
    return Instance(xy, tuple(sorted(arcs)), 0, "nested")
