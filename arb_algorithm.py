"""Minimale Arboreszenz (gerichteter Spannbaum) nach Chu-Liu/Edmonds, dazu die Vergleichsverfahren.

Gegeben: gerichtete Bögen (u, v, Kosten, Länge) und eine Wurzel. Gesucht: für jeden Knoten außer der Wurzel genau ein Zulaufbogen, sodass alle Knoten von der Wurzel aus erreichbar sind (ein Verteilbaum in
Fließrichtung), mit minimalen Gesamtkosten. Kruskal und Prim sind für UNGERICHTETE Kanten gebaut; hier zählt jeder Bogen einzeln.

**Chu-Liu/Edmonds** (Chu & Liu 1965, Edmonds 1967): 1. Für jeden Knoten den billigsten Zulaufbogen wählen und dessen Kosten von allen Bögen in diesen Knoten abziehen (Dualwert). 2. Bilden die gewählten Bögen
keinen Kreis, sind sie die Lösung. 3. Sonst jeden Kreis zu einem Superknoten **kontrahieren** (Bögen innerhalb des Kreises fallen weg) und mit den reduzierten Kosten von vorn beginnen. 4. Rückwärts **expandieren**:
der Bogen, der in den Superknoten führt, ersetzt den gewählten Kreisbogen an seinem Zielknoten. Die Summe der in allen Ebenen abgezogenen Mindestkosten ist ein Dualwert und gleich den Baumkosten (Optimalitätsbeweis).

Aufwand in **Elementarschritten**: je Ebene alle Bögen prüfen (billigster Zulauf), Zeigerschritte der Kreissuche, alle Bögen umbenennen und reduzieren. Diese einfache Umsetzung ist O(n·m); schnellere Varianten
(Tarjan 1977, Gabow u. a. 1986) sind nicht gebaut."""

import heapq
from dataclasses import dataclass, field

import arb_undirected as U

INF = float("inf")


@dataclass
class LevelInfo:
    n: int                                          # Knoten dieser Ebene
    m: int                                          # Bögen dieser Ebene
    members: list                                   # je Ebenen-Knoten die Menge der Originalknoten
    best: dict                                      # Ebenen-Knoten -> (Originalbogen des billigsten Zulaufs, seine (reduzierten) Kosten in dieser Ebene)
    cycles: list                                    # Kreise als Listen von Ebenen-Knoten
    root: int                                       # Wurzel als Ebenen-Knoten
    reduction: float = 0.0                          # Summe der abgezogenen Mindestkosten dieser Ebene


@dataclass
class ArbResult:
    tree: list                                      # Originalbogen-Indizes, je Nicht-Wurzel-Knoten einer (leer, wenn nicht lösbar)
    cost: float
    feasible: bool
    levels: list = field(default_factory=list)      # LevelInfo je Ebene (Ebene 0 = Originalgraph)
    dual: float = 0.0                               # Summe aller abgezogenen Mindest-Zulaufkosten = Baumkosten
    ops: int = 0
    unreachable: list = field(default_factory=list)  # bei nicht lösbaren Instanzen: Originalknoten ohne Zulauf in der letzten Ebene

    @property
    def contractions(self):
        return sum(len(lv.cycles) for lv in self.levels)


@dataclass
class TreeResult:
    tree: list                                      # Originalbogen-Indizes oder [] (ungültig)
    cost: float
    valid: bool
    reason: str = ""


def reachable(n, arcs, root):
    """Von der Wurzel aus erreichbare Knoten (Breitensuche)."""
    out = [[] for _ in range(n)]
    for a in arcs:
        out[a[0]].append(a[1])
    seen = {root}
    stack = [root]
    while stack:
        u = stack.pop()
        for v in out[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def _find_cycles(cur_n, parent, root):
    """Kreise im Graphen der gewählten Zuläufe (Zeiger v -> Ausgangsknoten `parent[v]`). Gibt (Kreise, Zeigerschritte) zurück."""
    state = [0] * cur_n                             # 0 unbesucht, 1 auf dem aktuellen Weg, 2 fertig
    cycles, steps = [], 0
    for start in range(cur_n):
        if state[start]:
            continue
        path, v = [], start
        while v != root and state[v] == 0:
            state[v] = 1
            path.append(v)
            v = parent[v]
            steps += 1
        if v != root and state[v] == 1:
            cycles.append(path[path.index(v):])
        for x in path:
            state[x] = 2
    return cycles, steps


def chu_liu_edmonds(n, arcs, root):
    """`arcs` = Sequenz (u, v, Kosten, ...); der Index in der Sequenz ist der Originalbogen. Bögen in die Wurzel und Schleifen werden ignoriert."""
    res = ArbResult([], 0.0, True)
    if n <= 1:
        return res
    cur = [(a[0], a[1], float(a[2]), i) for i, a in enumerate(arcs) if a[0] != a[1] and a[1] != root]
    cur_n, cur_root = n, root
    members = [frozenset({x}) for x in range(n)]
    stack = []                                       # je Kontraktion: (billigste Zuläufe, Kreise, Umbenennung, Superknoten, Knoten der Ebene, Mitglieder der Ebene)
    while True:
        best = {}
        for u, v, c, orig in cur:
            res.ops += 1
            if v not in best or c < best[v][0]:
                best[v] = (c, u, orig)
        missing = [x for x in range(cur_n) if x != cur_root and x not in best]
        if missing:
            res.feasible = False
            res.unreachable = sorted({y for x in missing for y in members[x]})
            res.levels.append(LevelInfo(cur_n, len(cur), members, {}, [], cur_root))
            return res
        reduction = sum(b[0] for b in best.values())
        res.dual += reduction
        cycles, walk = _find_cycles(cur_n, {x: b[1] for x, b in best.items()}, cur_root)
        res.ops += walk
        res.levels.append(LevelInfo(cur_n, len(cur), members, {x: (b[2], b[0]) for x, b in best.items()}, cycles, cur_root, reduction))
        if not cycles:
            sel = {x: b[2] for x, b in best.items()}
            break
        in_cycle = {x: ci for ci, cyc in enumerate(cycles) for x in cyc}
        mapping, new_members = {}, []
        for x in range(cur_n):
            if x not in in_cycle:
                mapping[x] = len(new_members)
                new_members.append(members[x])
        super_id = []
        for cyc in cycles:
            super_id.append(len(new_members))
            new_members.append(frozenset().union(*(members[x] for x in cyc)))
            for x in cyc:
                mapping[x] = super_id[-1]
        nxt = []
        for u, v, c, orig in cur:
            res.ops += 1
            if mapping[u] != mapping[v]:
                nxt.append((mapping[u], mapping[v], c - best[v][0], orig))
        stack.append((best, cycles, mapping, super_id, cur_n, members))
        cur, cur_n, cur_root, members = nxt, len(new_members), mapping[cur_root], new_members
    for best, cycles, mapping, super_id, old_n, old_members in reversed(stack):
        new_sel, sel = sel, {}
        in_cycle = {x for cyc in cycles for x in cyc}
        for x in range(old_n):
            if x not in in_cycle and mapping[x] in new_sel:
                sel[x] = new_sel[mapping[x]]
        for cyc, s in zip(cycles, super_id):
            entering = new_sel[s]
            target = arcs[entering][1]
            entry = next(w for w in cyc if target in old_members[w])
            for w in cyc:
                sel[w] = entering if w == entry else best[w][2]
    res.tree = sorted(sel.values())
    res.cost = sum(float(arcs[i][2]) for i in res.tree)
    return res


# --- Referenzen und Vergleichsverfahren ---------------------------------------------------------------------------------------------------------


def is_arborescence(n, arcs, tree, root):
    """n - 1 Bögen, jeder Nicht-Wurzel-Knoten genau ein Zulauf, kein Zulauf in die Wurzel, alle Knoten von der Wurzel aus über diese Bögen erreichbar."""
    if len(tree) != n - 1 or len(set(tree)) != n - 1:
        return False
    into = {}
    for i in tree:
        v = arcs[i][1]
        if v == root or v in into:
            return False
        into[v] = i
    return len(reachable(n, [arcs[i] for i in tree], root)) == n


def min_incoming(n, arcs, root):
    """Schritt 1 von Chu-Liu/Edmonds allein: der billigste Zulauf je Knoten. Gibt (Bogenindex je Knoten, Kreise, Kosten) zurück; ohne Kreise ist das schon die Lösung, sonst kein Baum.
    Ein Knoten ohne Zulauf fehlt im Ergebnis."""
    best = {}
    for i, a in enumerate(arcs):
        if a[0] != a[1] and a[1] != root and (a[1] not in best or float(a[2]) < float(arcs[best[a[1]]][2])):
            best[a[1]] = i
    cycles, _ = _find_cycles(n, {v: arcs[i][0] for v, i in best.items()}, root) if len(best) == n - 1 else ([], 0)
    return best, cycles, sum(float(arcs[i][2]) for i in best.values())


def kruskal_oriented(n, arcs, root):
    """Die naive Antwort: ungerichteten MST auf den Leitungslängen (Kruskal), dann von der Wurzel aus orientieren und je Kante den billigsten passenden Bogen nehmen.
    Ungültig (`valid=False`), wenn ein benötigter Bogen in dieser Richtung nicht existiert (Einbahn) oder die Knoten nicht zusammenhängen."""
    pairs = {}
    for a in arcs:
        if a[0] != a[1]:
            key = (min(a[0], a[1]), max(a[0], a[1]))
            pairs[key] = min(pairs.get(key, INF), float(a[3]))
    edges = tuple((u, v, w) for (u, v), w in sorted(pairs.items()))
    kr = U.kruskal(n, edges)
    if not kr.connected:
        return TreeResult([], INF, False, "nicht zusammenhängend")
    adj = [[] for _ in range(n)]
    for i in kr.tree:
        u, v, _w = edges[i]
        adj[u].append(v)
        adj[v].append(u)
    cheapest = {}
    for i, a in enumerate(arcs):
        if a[0] != a[1] and ((a[0], a[1]) not in cheapest or float(a[2]) < float(arcs[cheapest[(a[0], a[1])]][2])):
            cheapest[(a[0], a[1])] = i
    tree, seen, todo = [], {root}, [root]
    while todo:
        p = todo.pop()
        for c in adj[p]:
            if c in seen:
                continue
            seen.add(c)
            if (p, c) not in cheapest:
                return TreeResult([], INF, False, f"Bogen {p}→{c} fehlt (Einbahn)")
            tree.append(cheapest[(p, c)])
            todo.append(c)
    return TreeResult(sorted(tree), sum(float(arcs[i][2]) for i in tree), True)


def prim_directed(n, arcs, root):
    """Gerichtetes Prim: vom Baum aus immer den billigsten Bogen zu einem noch nicht angeschlossenen Knoten nehmen (gierig, ohne Rückblick)."""
    out = [[] for _ in range(n)]
    for i, a in enumerate(arcs):
        if a[0] != a[1] and a[1] != root:
            out[a[0]].append((float(a[2]), i, a[1]))
    seen, tree, heap = {root}, [], list(out[root])
    heapq.heapify(heap)
    while heap and len(seen) < n:
        c, i, v = heapq.heappop(heap)
        if v in seen:
            continue
        seen.add(v)
        tree.append(i)
        for item in out[v]:
            if item[2] not in seen:
                heapq.heappush(heap, item)
    if len(seen) < n:
        return TreeResult([], INF, False, "nicht erreichbar")
    return TreeResult(sorted(tree), sum(float(arcs[i][2]) for i in tree), True)


def shortest_path_tree(n, arcs, root):
    """Dijkstra ab der Wurzel: minimiert jeden EINZELNEN Weg zur Wurzel, nicht die Summe der Bogenkosten des Baums."""
    out = [[] for _ in range(n)]
    for i, a in enumerate(arcs):
        if a[0] != a[1] and a[1] != root:
            out[a[0]].append((float(a[2]), i, a[1]))
    dist, parent_arc = {root: 0.0}, {}
    heap = [(0.0, root, -1)]
    done = set()
    while heap:
        d, u, via = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        if via >= 0:
            parent_arc[u] = via
        for c, i, v in out[u]:
            if v not in done and d + c < dist.get(v, INF):
                dist[v] = d + c
                heapq.heappush(heap, (d + c, v, i))
    if len(done) < n:
        return TreeResult([], INF, False, "nicht erreichbar")
    tree = sorted(parent_arc.values())
    return TreeResult(tree, sum(float(arcs[i][2]) for i in tree), True)


def best_root(n, arcs):
    """Wurzel mit der billigsten Arboreszenz (alle Wurzeln probiert, bei Gleichstand die kleinste): (Wurzel, ArbResult, Elementarschritte über alle Wurzeln). Wurzeln, von denen nicht alle Knoten erreichbar
    sind, scheiden aus; gibt (None, None, ops) zurück, wenn keine Wurzel geht."""
    best, ops = (None, None), 0
    for r in range(n):
        if len(reachable(n, arcs, r)) < n:
            continue
        res = chu_liu_edmonds(n, arcs, r)
        ops += res.ops
        if best[0] is None or res.cost < best[1].cost:
            best = (r, res)
    return best[0], best[1], ops
