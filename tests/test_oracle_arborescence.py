"""Orakel-Tests gegen networkx: beliebige Wurzel (nicht nur Knoten 0), Gleichstände und Nullkosten,
Kürzeste-Wege-Baum (Distanzen = Dijkstra), beste Wurzel (Minimum über alle Wurzeln), ungerichteter
Kruskal/Prim (alle drei Prim-Varianten) gegen den networkx-MST."""
import random

import networkx as nx
import pytest

import arb_algorithm as A
import arb_undirected as U


def _graph(rng, n, root):
    costs = rng.choice([(1, 2), (1, 2, 3), tuple(range(1, 20)), (0, 1, 5)])
    arcs = [(rng.randrange(n), rng.randrange(n), float(rng.choice(costs)), 1.0) for _ in range(rng.randint(n - 1, 3 * n))]
    rest = [v for v in range(n) if v != root]
    rng.shuffle(rest)
    order = [root] + rest
    for i in range(1, n):                                  # erreichbar von der Wurzel
        arcs.append((order[rng.randrange(i)], order[i], float(rng.choice(costs)), 1.0))
    rng.shuffle(arcs)
    return arcs


def _nx_cost(n, arcs, root):
    g = nx.DiGraph()
    g.add_nodes_from(range(n))
    for a in arcs:
        if a[0] != a[1] and a[1] != root and (not g.has_edge(a[0], a[1]) or g[a[0]][a[1]]["weight"] > a[2]):
            g.add_edge(a[0], a[1], weight=a[2])
    g.add_edge("R", root, weight=0.0)
    big = 10.0 * (1 + sum(a[2] for a in arcs))
    for v in range(n):
        if v != root:
            g.add_edge("R", v, weight=big)
    return sum(d["weight"] for _u, _v, d in nx.minimum_spanning_arborescence(g).edges(data=True))


def test_any_root_ties_and_zero_costs_match_networkx_and_dual_certificate():
    rng = random.Random(77)
    for _ in range(80):
        n = rng.randint(2, 18)
        root = rng.randrange(n)
        arcs = _graph(rng, n, root)
        res = A.chu_liu_edmonds(n, arcs, root)
        assert res.feasible and A.is_arborescence(n, arcs, res.tree, root)
        ref = _nx_cost(n, arcs, root)
        assert res.cost == pytest.approx(ref) and res.dual == pytest.approx(ref)
        for fn in (A.kruskal_oriented, A.prim_directed, A.shortest_path_tree):
            r = fn(n, arcs, root)
            if r.valid:
                assert A.is_arborescence(n, arcs, r.tree, root) and r.cost >= ref - 1e-9


def test_shortest_path_tree_distances_equal_dijkstra():
    rng = random.Random(5)
    for _ in range(40):
        n = rng.randint(2, 15)
        root = rng.randrange(n)
        arcs = _graph(rng, n, root)
        g = nx.DiGraph()
        for a in arcs:
            if a[0] != a[1] and a[1] != root and (not g.has_edge(a[0], a[1]) or g[a[0]][a[1]]["weight"] > a[2]):
                g.add_edge(a[0], a[1], weight=a[2])
        dist = nx.single_source_dijkstra_path_length(g, root)
        tree = A.shortest_path_tree(n, arcs, root).tree
        parent = {arcs[i][1]: (arcs[i][0], arcs[i][2]) for i in tree}
        for v in range(n):
            total, x = 0.0, v
            while x != root:
                x, c = parent[x][0], parent[x][1]
                total += c
            assert total == pytest.approx(dist[v])


def test_best_root_is_the_cheapest_root_with_smallest_index_on_ties():
    rng = random.Random(9)
    for _ in range(40):
        n = rng.randint(3, 8)
        arcs = _graph(rng, n, rng.randrange(n))
        costs = {r: _nx_cost(n, arcs, r) for r in range(n) if len(A.reachable(n, arcs, r)) == n}
        root, res, _ops = A.best_root(n, arcs)
        best = min(costs.values())
        assert res.cost == pytest.approx(best)
        assert root == min(r for r, c in costs.items() if c == pytest.approx(best))


def test_undirected_kruskal_and_all_prim_variants_match_networkx_mst():
    rng = random.Random(3)
    for _ in range(60):
        n = rng.randint(2, 20)
        edges = [(rng.randrange(n), rng.randrange(n), float(rng.randint(1, 10))) for _ in range(rng.randint(n - 1, 3 * n))]
        edges = tuple(e for e in edges if e[0] != e[1])
        g = nx.Graph()
        g.add_nodes_from(range(n))
        for u, v, w in edges:
            if not g.has_edge(u, v) or g[u][v]["weight"] > w:
                g.add_edge(u, v, weight=w)
        k = U.kruskal(n, edges)
        assert k.connected == nx.is_connected(g)
        if not k.connected:
            continue
        ref = sum(d["weight"] for _u, _v, d in nx.minimum_spanning_edges(g, data=True))
        assert k.cost == pytest.approx(ref)
        for variant in U.VARIANTS:
            p = U.prim(n, edges, variant=variant, start=rng.randrange(n))
            assert p.connected and p.cost == pytest.approx(ref)
