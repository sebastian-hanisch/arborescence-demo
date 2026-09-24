import numpy as np
import pytest

import arb_algorithm as A
import arb_constants as C
import arb_scenario as S


@pytest.mark.parametrize("n", [5, 30, 90])
@pytest.mark.parametrize("k", [3, 6, 1000])
def test_generated_instance_shape_and_canonical_arcs(n, k):
    inst = S.generate(n, k, 0.5, 0.0, 3)
    assert inst.n == n and tuple(inst.xy[0]) == C.DEPOT_XY and inst.root == 0 and inst.kind == "map"
    assert list(inst.arcs) == sorted(inst.arcs, key=lambda a: (a[0], a[1])) and len({(a[0], a[1]) for a in inst.arcs}) == inst.m
    assert all(a[0] != a[1] and a[3] > 0 and a[2] >= a[3] - 1e-12 for a in inst.arcs) and inst.xy.min() >= 0 and inst.xy.max() <= C.AREA
    if k >= n - 1:
        assert inst.m == n * (n - 1)


def test_generation_is_deterministic_and_seed_dependent():
    a, b, c = S.generate(30, 6, 0.5, 0.2, 4), S.generate(30, 6, 0.5, 0.2, 4), S.generate(30, 6, 0.5, 0.2, 5)
    assert a.arcs == b.arcs and np.array_equal(a.xy, b.xy) and a.arcs != c.arcs


def test_costs_are_length_plus_alpha_times_the_climb():
    inst = S.generate(40, 6, 1.5, 0.0, 7)
    h = inst.heights
    assert (h >= 0).all() and h.max() > 5
    for u, v, cost, length in inst.arcs:
        assert length == pytest.approx(float(np.hypot(*(inst.xy[u] - inst.xy[v]))))
        assert cost == pytest.approx(length + 1.5 * max(0.0, h[v] - h[u]))


def test_zero_alpha_gives_symmetric_costs_and_positive_alpha_makes_uphill_more_expensive():
    flat = S.generate(30, 6, 0.0, 0.0, 2)
    lookup = {(a[0], a[1]): a[2] for a in flat.arcs}
    assert all(lookup[(v, u)] == pytest.approx(c) for (u, v), c in lookup.items())
    rough = S.generate(30, 6, 2.0, 0.0, 2)
    up = [(a[2] - a[3]) for a in rough.arcs if rough.heights[a[1]] > rough.heights[a[0]]]
    down = [(a[2] - a[3]) for a in rough.arcs if rough.heights[a[1]] < rough.heights[a[0]]]
    assert min(up) > 0 and all(d == pytest.approx(0.0) for d in down)


def test_without_oneway_every_arc_has_its_reverse_and_with_oneway_some_do_not():
    both = S.generate(40, 6, 0.5, 0.0, 3)
    keys = {(a[0], a[1]) for a in both.arcs}
    assert all((v, u) in keys for u, v in keys)
    some = S.generate(40, 6, 0.5, 0.6, 3)
    keys2 = {(a[0], a[1]) for a in some.arcs}
    assert any((v, u) not in keys2 for u, v in keys2) and some.m < both.m


@pytest.mark.parametrize("oneway", C.ONEWAY_OPTIONS)
@pytest.mark.parametrize("k", [3, 6])
def test_every_generated_instance_is_solvable_from_the_root(oneway, k):
    for seed in range(10):
        inst = S.generate(40, k, 0.5, oneway, seed)
        assert len(A.reachable(inst.n, inst.arcs, 0)) == inst.n


def test_textbook_fixture():
    t = S.textbook_instance()
    assert t.n == 5 and t.m == 8 and t.labels == ("A", "B", "C", "D", "E") and t.root == 0 and t.kind == "textbook"
    assert list(t.arcs) == sorted(t.arcs) and len(A.reachable(5, t.arcs, 0)) == 5


@pytest.mark.parametrize("n", [3, 5, 12, 40])
def test_nested_fixture(n):
    inst = S.nested_instance(n)
    assert inst.n == n and inst.m == 1 + 2 * (n - 2) and inst.kind == "nested" and len(A.reachable(n, inst.arcs, 0)) == n
    assert {(a[0], a[1]) for a in inst.arcs} >= {(0, n - 1)}


def test_nested_needs_three_nodes():
    with pytest.raises(ValueError):
        S.nested_instance(2)
