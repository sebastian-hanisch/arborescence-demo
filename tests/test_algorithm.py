"""Die zentrale Korrektheits-Kette: Chu-Liu/Edmonds == Brute-Force und networkx, gültige Arboreszenz, Dual-Zertifikat, Kontraktion von Hand, Symmetrie, Vergleichsverfahren, Wurzelwahl, Sonderfälle."""

import itertools
import math
import random

import networkx as nx
import pytest

import arb_algorithm as A
import arb_scenario as S
import arb_undirected as U


def _brute(n, arcs, root):
    into = [[i for i, a in enumerate(arcs) if a[1] == v and a[0] != v] for v in range(n)]
    best = math.inf
    for combo in itertools.product(*[into[v] for v in range(n) if v != root]):
        if A.is_arborescence(n, arcs, list(combo), root):
            best = min(best, sum(arcs[i][2] for i in combo))
    return best


def _networkx_cost(n, arcs, root):
    """networkx kennt keine Wurzel: virtuelle Wurzel R mit Bogen R → root (Kosten 0) und sehr teuren Bögen zu allen anderen; bei lösbarer Instanz ist das Optimum der Originalkosten gleich."""
    g = nx.DiGraph()
    g.add_nodes_from(range(n))
    for a in arcs:
        if a[0] != a[1] and a[1] != root and (not g.has_edge(a[0], a[1]) or g[a[0]][a[1]]["weight"] > a[2]):
            g.add_edge(a[0], a[1], weight=float(a[2]))
    big = 10.0 * (1 + sum(a[2] for a in arcs))
    g.add_edge("R", root, weight=0.0)
    for v in range(n):
        if v != root:
            g.add_edge("R", v, weight=big)
    t = nx.minimum_spanning_arborescence(g)
    return sum(d["weight"] for _u, _v, d in t.edges(data=True))


def _random_graph(rng, n, costs=(1, 2, 3, 5, 8, 13)):
    m = rng.randint(n - 1, n * (n - 1))
    return [(rng.randrange(n), rng.randrange(n), float(rng.choice(costs)), 1.0) for _ in range(m)]


def _fixtures():
    yield S.textbook_instance()
    yield S.nested_instance(9)
    for seed in range(4):
        yield S.generate(25, 5, 0.5, 0.0, seed)
        yield S.generate(25, 4, 1.0, 0.4, seed)


ALL = list(_fixtures())


# --- Optimalität ----------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(120))
def test_equals_brute_force_on_small_random_graphs_including_infeasible_ones(seed):
    rng = random.Random(seed)
    n = rng.randint(2, 7)
    arcs = _random_graph(rng, n)
    res = A.chu_liu_edmonds(n, arcs, 0)
    best = _brute(n, arcs, 0)
    assert res.feasible == (best < math.inf) == (len(A.reachable(n, arcs, 0)) == n)
    if res.feasible:
        assert A.is_arborescence(n, arcs, res.tree, 0) and res.cost == pytest.approx(best) and res.dual == pytest.approx(best)
    else:
        assert res.tree == [] and res.unreachable


@pytest.mark.parametrize("seed", range(200))
def test_equals_networkx_on_random_feasible_graphs(seed):
    rng = random.Random(1000 + seed)
    n = rng.randint(3, 14)
    arcs = _random_graph(rng, n, costs=tuple(range(1, 30)))
    if len(A.reachable(n, arcs, 0)) < n:
        pytest.skip("nicht lösbar")
    res = A.chu_liu_edmonds(n, arcs, 0)
    assert A.is_arborescence(n, arcs, res.tree, 0) and res.cost == pytest.approx(_networkx_cost(n, arcs, 0)) and res.dual == pytest.approx(res.cost)


@pytest.mark.parametrize("inst", ALL)
def test_generated_and_fixture_instances_are_solved_optimally_and_certified(inst):
    res = A.chu_liu_edmonds(inst.n, inst.arcs, inst.root)
    assert res.feasible and A.is_arborescence(inst.n, inst.arcs, res.tree, inst.root)
    assert res.cost == pytest.approx(_networkx_cost(inst.n, inst.arcs, inst.root)) and res.dual == pytest.approx(res.cost)
    assert sum(lv.reduction for lv in res.levels) == pytest.approx(res.dual)


def test_relabelled_nodes_give_the_same_cost():
    inst = S.generate(20, 5, 1.0, 0.2, 3)
    perm = list(range(inst.n))
    random.Random(2).shuffle(perm[1:])                                         # Wurzel bleibt Knoten 0
    rest = perm[1:]
    random.Random(2).shuffle(rest)
    perm = [0] + rest
    moved = [(perm[a[0]], perm[a[1]], a[2], a[3]) for a in inst.arcs]
    assert A.chu_liu_edmonds(inst.n, moved, 0).cost == pytest.approx(A.chu_liu_edmonds(inst.n, inst.arcs, 0).cost)


# --- Kontraktion von Hand -------------------------------------------------------------------------------------------------------------------------


def test_textbook_walkthrough_by_hand():
    t = S.textbook_instance()
    res = A.chu_liu_edmonds(t.n, t.arcs, 0)
    lv = res.levels
    assert [len(x.cycles) for x in lv] == [1, 1, 0] and [x.reduction for x in lv] == [14.0, 1.0, 2.0] and [x.n for x in lv] == [5, 4, 3] and [x.m for x in lv] == [8, 6, 3]
    assert [sorted(x) for x in lv[0].cycles] == [[2, 3]] and sorted(lv[1].members[lv[1].cycles[0][0]] | lv[1].members[lv[1].cycles[0][1]]) == [1, 2, 3]
    assert [t.arcs[i][:2] for i in res.tree] == [(0, 2), (2, 3), (2, 4), (3, 1)] and res.cost == 17.0 == res.dual and res.contractions == 2
    assert res.ops == 40                                                       # Ebene 0: 8 Prüfungen + 4 Zeigerschritte + 8 Umbenennungen; Ebene 1: 6 + 3 + 6; Ebene 2 (die beiden Bögen von C nach B fallen mit B→C weg): 3 + 2
    best, cycles, cost = A.min_incoming(t.n, t.arcs, 0)
    assert [sorted(c) for c in cycles] == [[2, 3]] and cost == 14.0 and not A.is_arborescence(t.n, t.arcs, list(best.values()), 0)
    assert A.kruskal_oriented(t.n, t.arcs, 0).cost == 19.0


@pytest.mark.parametrize("n", [3, 4, 8, 20, 60])
def test_nested_instance_needs_exactly_n_minus_1_levels(n):
    inst = S.nested_instance(n)
    res = A.chu_liu_edmonds(n, inst.arcs, 0)
    assert len(res.levels) == n - 1 and res.contractions == n - 2 and res.cost == pytest.approx(10.0 * n + (n - 2)) == pytest.approx(res.dual)
    assert [inst.arcs[i][:2] for i in res.tree if inst.arcs[i][0] != 0] == sorted((j + 1, j) for j in range(1, n - 1))


def test_ops_grow_quadratically_on_the_nested_worst_case():
    ops = {n: A.chu_liu_edmonds(n, S.nested_instance(n).arcs, 0).ops for n in (20, 40, 80)}
    assert 3.0 < ops[40] / ops[20] < 4.5 and 3.0 < ops[80] / ops[40] < 4.5


def test_single_level_when_the_cheapest_incoming_arcs_form_a_tree():
    arcs = [(0, 1, 1.0, 1.0), (0, 2, 4.0, 1.0), (1, 2, 2.0, 1.0), (2, 1, 9.0, 1.0)]
    res = A.chu_liu_edmonds(3, arcs, 0)
    assert len(res.levels) == 1 and res.contractions == 0 and res.cost == 3.0 == res.dual
    assert res.ops == 4 + 2                                                    # 4 Bögen geprüft + 2 Zeigerschritte


# --- Symmetrie -----------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(12))
def test_symmetric_costs_give_the_undirected_mst_and_kruskal_oriented_is_exact(seed):
    inst = S.generate(30, 6, 0.0, 0.0, seed)
    edges = tuple(sorted({(min(a[0], a[1]), max(a[0], a[1]), a[3]) for a in inst.arcs}))
    mst = U.kruskal(inst.n, edges).cost
    opt = A.chu_liu_edmonds(inst.n, inst.arcs, 0)
    assert opt.cost == pytest.approx(mst) and A.kruskal_oriented(inst.n, inst.arcs, 0).cost == pytest.approx(opt.cost) and opt.contractions >= 1


def test_direction_matters_once_alpha_is_positive():
    gaps = []
    for seed in range(20):
        inst = S.generate(30, 6, 2.0, 0.0, seed)
        opt = A.chu_liu_edmonds(inst.n, inst.arcs, 0).cost
        k = A.kruskal_oriented(inst.n, inst.arcs, 0)
        assert k.valid and k.cost >= opt - 1e-9
        gaps.append(k.cost - opt)
    assert max(gaps) > 1.0


# --- Vergleichsverfahren -------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("inst", ALL)
def test_prim_and_shortest_path_tree_are_valid_but_never_cheaper(inst):
    opt = A.chu_liu_edmonds(inst.n, inst.arcs, inst.root).cost
    for f in (A.prim_directed, A.shortest_path_tree):
        r = f(inst.n, inst.arcs, inst.root)
        assert r.valid and A.is_arborescence(inst.n, inst.arcs, r.tree, inst.root) and r.cost >= opt - 1e-9 and r.cost == pytest.approx(sum(inst.arcs[i][2] for i in r.tree))
    k = A.kruskal_oriented(inst.n, inst.arcs, inst.root)
    assert (not k.valid) or (A.is_arborescence(inst.n, inst.arcs, k.tree, inst.root) and k.cost >= opt - 1e-9)


def test_kruskal_oriented_is_invalid_exactly_when_a_needed_direction_is_missing():
    arcs = [(0, 1, 1.0, 1.0), (2, 1, 1.0, 1.0), (0, 2, 5.0, 5.0)]
    k = A.kruskal_oriented(3, arcs, 0)
    assert not k.valid and "fehlt" in k.reason and k.tree == []
    opt = A.chu_liu_edmonds(3, arcs, 0)
    assert opt.cost == 6.0 and [arcs[i][:2] for i in opt.tree] == [(0, 1), (0, 2)]
    ok = A.kruskal_oriented(3, arcs + [(1, 2, 1.0, 1.0)], 0)
    assert ok.valid and ok.cost == 2.0


def test_min_incoming_has_cycles_exactly_when_it_is_not_a_tree():
    for inst in ALL:
        best, cycles, cost = A.min_incoming(inst.n, inst.arcs, inst.root)
        assert (not cycles) == A.is_arborescence(inst.n, inst.arcs, list(best.values()), inst.root)
        assert cost == pytest.approx(A.chu_liu_edmonds(inst.n, inst.arcs, inst.root).levels[0].reduction)


def test_heuristics_report_infeasible_instances_as_invalid():
    arcs = [(0, 1, 1.0, 1.0), (2, 1, 1.0, 1.0)]
    assert not A.prim_directed(3, arcs, 0).valid and not A.shortest_path_tree(3, arcs, 0).valid and not A.kruskal_oriented(3, arcs, 0).valid


def test_shortest_path_tree_minimises_every_single_path_not_the_total():
    arcs = [(0, 1, 1.0, 1.0), (0, 2, 3.0, 1.0), (1, 2, 1.0, 1.0), (2, 3, 1.0, 1.0), (0, 3, 3.5, 1.0), (1, 3, 5.0, 1.0)]
    spt, opt = A.shortest_path_tree(4, arcs, 0), A.chu_liu_edmonds(4, arcs, 0)
    assert sorted(arcs[i][:2] for i in spt.tree) == [(0, 1), (1, 2), (2, 3)] and spt.cost == 3.0 == opt.cost
    line = [(0, 1, 2.0, 1.0), (0, 2, 3.0, 1.0), (1, 2, 2.0, 1.0)]
    assert A.shortest_path_tree(3, line, 0).cost == 5.0 and A.chu_liu_edmonds(3, line, 0).cost == 4.0                  # Weg zu 2: direkt 3 statt über 1 für 4, aber 1 → 2 kostet nur 2


# --- Wurzelwahl ----------------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(6))
def test_best_root_is_the_minimum_over_all_roots_and_matches_the_virtual_root_trick(seed):
    inst = S.generate(14, 6, 1.5, 0.0, seed)
    root, res, ops = A.best_root(inst.n, inst.arcs)
    costs = {r: A.chu_liu_edmonds(inst.n, inst.arcs, r).cost for r in range(inst.n)}
    assert res.cost == pytest.approx(min(costs.values())) and costs[root] == pytest.approx(res.cost) and root == min(r for r, c in costs.items() if c == pytest.approx(min(costs.values()))) and ops > 0
    big = 10.0 * (1 + sum(a[2] for a in inst.arcs))
    virtual = list(inst.arcs) + [(inst.n, v, big, big) for v in range(inst.n)]
    assert A.chu_liu_edmonds(inst.n + 1, virtual, inst.n).cost == pytest.approx(big + res.cost)


def test_best_root_skips_roots_that_cannot_reach_everybody():
    arcs = [(0, 1, 1.0, 1.0), (1, 2, 1.0, 1.0), (2, 0, 1.0, 1.0)]
    assert A.best_root(3, arcs)[0] == 0
    chain = [(0, 1, 1.0, 1.0), (1, 2, 1.0, 1.0)]
    root, res, _ops = A.best_root(3, chain)
    assert root == 0 and res.cost == 2.0
    assert A.best_root(3, [(0, 1, 1.0, 1.0), (2, 1, 1.0, 1.0)]) [0] is None


# --- Sonderfälle ---------------------------------------------------------------------------------------------------------------------------------


def test_tiny_and_degenerate_inputs():
    one = A.chu_liu_edmonds(1, [], 0)
    assert one.feasible and one.tree == [] and one.cost == 0.0
    two = A.chu_liu_edmonds(2, [(0, 1, 4.0, 1.0), (1, 0, 1.0, 1.0)], 0)
    assert two.tree == [0] and two.cost == 4.0
    assert not A.chu_liu_edmonds(3, [(1, 0, 1.0, 1.0), (1, 2, 1.0, 1.0), (2, 1, 1.0, 1.0)], 0).feasible


def test_parallel_arcs_self_loops_and_arcs_into_the_root_are_handled():
    arcs = [(0, 1, 5.0, 1.0), (0, 1, 2.0, 1.0), (1, 1, 0.1, 1.0), (1, 0, 0.1, 1.0), (1, 2, 3.0, 1.0)]
    res = A.chu_liu_edmonds(3, arcs, 0)
    assert sorted(res.tree) == [1, 4] and res.cost == 5.0


def test_all_equal_costs_terminate_and_give_a_valid_tree():
    n = 12
    arcs = [(u, v, 1.0, 1.0) for u in range(n) for v in range(n) if u != v]
    res = A.chu_liu_edmonds(n, arcs, 0)
    assert A.is_arborescence(n, arcs, res.tree, 0) and res.cost == n - 1 == res.dual


def test_chain_and_star():
    chain = [(i, i + 1, float(i + 1), 1.0) for i in range(9)]
    assert A.chu_liu_edmonds(10, chain, 0).cost == sum(range(1, 10))
    star = [(0, i, 2.0, 1.0) for i in range(1, 8)] + [(i, 0, 1.0, 1.0) for i in range(1, 8)]
    assert A.chu_liu_edmonds(8, star, 0).cost == 14.0


def test_results_are_deterministic():
    inst = S.generate(40, 6, 1.0, 0.2, 9)
    a, b = A.chu_liu_edmonds(inst.n, inst.arcs, 0), A.chu_liu_edmonds(inst.n, inst.arcs, 0)
    assert a.tree == b.tree and a.ops == b.ops and [lv.cycles for lv in a.levels] == [lv.cycles for lv in b.levels]
