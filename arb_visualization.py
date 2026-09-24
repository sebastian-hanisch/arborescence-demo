"""Plotly-Abbildungen: gerichtete Bögen mit Pfeilspitzen, der billigste Zulauf je Knoten mit Kreisen, die Kontraktionsebenen, der gewählte Baum gegen das Optimum, Lücken-Balken, Sweeps.
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen."""

from math import atan2, degrees, hypot

import plotly.graph_objects as go
from plotly.subplots import make_subplots

TREE_COLOR = "#2F6B65"
CYCLE_COLOR = "#d62728"
DIFF_COLOR = "#ff7f0e"
MISS_COLOR = "rgba(120,120,120,0.55)"
GREY = "rgba(150,150,150,0.28)"
METHOD_COLORS = {"optimum": "#2F6B65", "kruskal": "#7b3fbf", "prim": "#4c78a8", "spt": "#e8a13a"}
METHOD_LABELS = {"optimum": "Optimum (Chu-Liu/Edmonds)", "kruskal": "Kruskal, orientiert", "prim": "Prim, gerichtet", "spt": "Kürzeste-Wege-Baum"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.1):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=legend_y), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _map_axes(fig, height=440):
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, height)


def _geometry(xy, u, v, offset):
    """Anfang und Ende eines Bogens, seitlich um `offset` versetzt (damit die beiden Richtungen eines Paars getrennt sichtbar sind) und an beiden Enden gekürzt."""
    x0, y0, x1, y1 = xy[u][0], xy[u][1], xy[v][0], xy[v][1]
    dx, dy = x1 - x0, y1 - y0
    length = hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    cut = min(0.14, 2.6 / length)
    return (x0 + dx * cut + nx * offset, y0 + dy * cut + ny * offset, x1 - dx * cut + nx * offset, y1 - dy * cut + ny * offset, degrees(atan2(dx, dy)))


def _arrows(fig, inst, arc_ids, color, width=2.5, dash="solid", name="", showlegend=False, offset=0.9, head=14, heads=True):
    if not len(arc_ids):
        return
    xs, ys, hx, hy, ang = [], [], [], [], []
    for i in arc_ids:
        u, v = inst.arcs[i][0], inst.arcs[i][1]
        x0, y0, x1, y1, a = _geometry(inst.xy, u, v, offset)
        xs += [x0, x1, None]
        ys += [y0, y1, None]
        hx.append(x0 + (x1 - x0) * 0.86)
        hy.append(y0 + (y1 - y0) * 0.86)
        ang.append(a)
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width, dash=dash), name=name, hoverinfo="skip", showlegend=showlegend))
    if heads:
        fig.add_trace(go.Scatter(x=hx, y=hy, mode="markers", marker=dict(symbol="arrow", size=head, angle=ang, angleref="up", color=color, line=dict(width=0)), hoverinfo="skip", showlegend=False))


def _points(fig, inst, colors, size=9, root=None):
    fig.add_trace(go.Scatter(x=inst.xy[:, 0], y=inst.xy[:, 1], mode="markers+text" if inst.labels is not None else "markers", text=list(inst.labels) if inst.labels is not None else None,
                             textposition="top center", marker=dict(size=size, color=colors, line=dict(width=1, color="white")), hoverinfo="skip", showlegend=False))
    if root is not None:
        fig.add_trace(go.Scatter(x=[inst.xy[root][0]], y=[inst.xy[root][1]], mode="markers", marker=dict(size=16, symbol="star", color="#2ca02c", line=dict(width=1, color="white")),
                                 name="Wurzel", hoverinfo="skip", showlegend=False))


def _height(inst):
    return 440 if inst.kind == "map" else 340


def build_instance(inst, root):
    """Alle Kandidatenbögen (bei vielen Bögen ohne Pfeilspitzen): dünn und grau."""
    fig = go.Figure()
    _arrows(fig, inst, range(inst.m), GREY, 1.1, heads=inst.m <= 60, head=7)
    _points(fig, inst, "#4c78a8", 8, root)
    return _map_axes(fig, _height(inst))


def build_first_step(inst, best, cycles, root):
    """Schritt 1 von Chu-Liu/Edmonds: der billigste Zulauf je Knoten (blau); Bögen, die einen Kreis bilden, rot."""
    in_cycle = {x for cyc in cycles for x in cyc}
    fig = go.Figure()
    _arrows(fig, inst, range(inst.m), "rgba(150,150,150,0.16)", 1.0, heads=False)
    _arrows(fig, inst, [i for v, i in best.items() if v not in in_cycle], "#4c78a8", 2.6)
    _arrows(fig, inst, [i for v, i in best.items() if v in in_cycle], CYCLE_COLOR, 3.4)
    _points(fig, inst, ["#d62728" if x in in_cycle else "#4c78a8" for x in range(inst.n)], 8, root)
    return _map_axes(fig, _height(inst))


def _palette(members, n):
    """Punktfarbe je Originalknoten nach dem Ebenen-Knoten, zu dem er gehört (Einzelknoten grau)."""
    color, idx = ["rgba(150,150,150,0.85)"] * n, 0
    for group in members:
        if len(group) > 1:
            c = f"hsl({(idx * 137) % 360},62%,45%)"
            idx += 1
            for x in group:
                color[x] = c
    return color


def build_level(inst, res, level):
    """Ebene `level` des Laufs: Punktfarbe = Superknoten (grau = Einzelknoten), gewählte billigste Zuläufe blau, Kreise rot gestrichelt umrandet (rot)."""
    lv = res.levels[level]
    in_cycle = {x for cyc in lv.cycles for x in cyc}
    fig = go.Figure()
    _arrows(fig, inst, range(inst.m), "rgba(150,150,150,0.14)", 1.0, heads=False)
    _arrows(fig, inst, [orig for x, (orig, _c) in lv.best.items() if x not in in_cycle], "#4c78a8", 2.6)
    _arrows(fig, inst, [orig for x, (orig, _c) in lv.best.items() if x in in_cycle], CYCLE_COLOR, 3.6)
    cyc_nodes = {y for x in in_cycle for y in lv.members[x]}
    _points(fig, inst, _palette(lv.members, inst.n), 9, next(iter(lv.members[lv.root])))
    if cyc_nodes:
        fig.add_trace(go.Scatter(x=[inst.xy[y][0] for y in cyc_nodes], y=[inst.xy[y][1] for y in cyc_nodes], mode="markers", marker=dict(size=16, color="rgba(0,0,0,0)", line=dict(width=2, color=CYCLE_COLOR)),
                                 hoverinfo="skip", showlegend=False))
    return _map_axes(fig, _height(inst))


def build_tree(inst, tree, optimum, root, valid=True):
    """Der gewählte Baum: grün, wo er mit dem Optimum übereinstimmt, orange, wo er abweicht; die Optimum-Bögen, die er nicht hat, grau gestrichelt."""
    fig = go.Figure()
    _arrows(fig, inst, range(inst.m), "rgba(150,150,150,0.14)", 1.0, heads=False)
    if valid:
        same = [i for i in tree if i in set(optimum)]
        diff = [i for i in tree if i not in set(optimum)]
        missing = [i for i in optimum if i not in set(tree)]
        _arrows(fig, inst, missing, MISS_COLOR, 2.0, dash="dash", name="Optimum-Bogen fehlt", showlegend=bool(missing))
        _arrows(fig, inst, same, TREE_COLOR, 3.2, name="wie das Optimum", showlegend=True)
        _arrows(fig, inst, diff, DIFF_COLOR, 3.6, name="weicht ab", showlegend=bool(diff))
    _points(fig, inst, "#4c78a8", 8, root)
    return _map_axes(fig, _height(inst))


def build_gap_bars(costs, opt_cost):
    """Kosten je Verfahren gegen das Optimum (Lücke in Prozent); ungültige Verfahren als Text."""
    names = list(costs)
    fig = go.Figure()
    xs = [METHOD_LABELS[k] for k in names]
    ys = [0.0 if k == "optimum" else (None if costs[k] is None else 100.0 * (costs[k] / opt_cost - 1.0)) for k in names]
    fig.add_trace(go.Bar(x=xs, y=[y if y is not None else 0 for y in ys], marker_color=[METHOD_COLORS[k] for k in names],
                         text=[("ungültig" if y is None else f"{y:.2f} %") for y in ys], textposition="outside"))
    fig.update_yaxes(title_text="Mehrkosten gegen das Optimum (%)", rangemode="tozero")
    return _base(fig, 320)


def build_sweep(rows, param_label, series, y_label, log_y=False, ref_line=None, ref_label=None):
    """`series` = [(key, Name, Farbe)]: Median als Linie, 10. bis 90. Perzentil als Band (`<key>_lo`/`<key>_hi`)."""
    xs = [str(r["value"]) for r in rows]
    fig = go.Figure()
    for key, name, color in series:
        ys = [None if r[key] != r[key] else r[key] for r in rows]
        lo = [None if r.get(f"{key}_lo", r[key]) != r.get(f"{key}_lo", r[key]) else r.get(f"{key}_lo", r[key]) for r in rows]
        hi = [None if r.get(f"{key}_hi", r[key]) != r.get(f"{key}_hi", r[key]) else r.get(f"{key}_hi", r[key]) for r in rows]
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        if all(v is not None for v in lo + hi):
            fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], mode="lines", fill="toself", fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.13)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=color, width=2.5), name=name, connectgaps=False))
    if ref_line is not None:
        fig.add_hline(y=ref_line, line=dict(color="#888", dash="dash", width=1.5), annotation_text=ref_label, annotation_position="top left")
    fig.update_xaxes(title_text=param_label, type="category")
    fig.update_yaxes(title_text=y_label, type="log" if log_y else "linear")
    return _base(fig, 360, legend_y=-0.3)


def build_nested(rows):
    """Worst Case: Ebenen (Linie n - 1 gestrichelt) und Elementarschritte über n."""
    ns = [r["n"] for r in rows]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Ebenen", "Elementarschritte"), horizontal_spacing=0.12)
    fig.add_trace(go.Scatter(x=ns, y=[r["levels"] for r in rows], mode="lines+markers", line=dict(color=TREE_COLOR, width=2.5), name="Ebenen"), row=1, col=1)
    fig.add_trace(go.Scatter(x=ns, y=[n - 1 for n in ns], mode="lines", line=dict(color="#888", dash="dash", width=1.5), name="n − 1"), row=1, col=1)
    fig.add_trace(go.Scatter(x=ns, y=[r["ops"] for r in rows], mode="lines+markers", line=dict(color="#e8a13a", width=2.5), name="Schritte"), row=1, col=2)
    fig.update_xaxes(title_text="Knoten n")
    return _base(fig, 320, legend_y=-0.3)
