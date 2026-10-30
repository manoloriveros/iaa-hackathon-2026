"""Inspect a line's component weights on a simplex grid with step 0.1.

Load each component once, normalize its cut-specific level and retain the chosen
shape rule. Evaluate V23 selection without a next-year factor and V24 with the
V23 factor. Report rankings by each cut, their mean, and the worst improvement
over the starting weights (maximin), alongside that starting configuration.
Usage: python rejilla_pesos.py <line> <shape a:b> <level|-> <run:selection:weight> [...]
"""
from __future__ import annotations

import itertools
import sys

import numpy as np
import pandas as pd

from comun import WORK
from mezcla3 import component, evaluate, labels, sin_referencia


def main():
    line, forma, nivel = sys.argv[1], sys.argv[2], sys.argv[3]
    a, b = (float(x) for x in forma.split(":"))
    comps_in = [c.split(":") for c in sys.argv[4:]]
    ysel, y24, idx25 = labels(line)
    raw = []
    for run, sel_name, w in comps_in:
        s, v, p = component(run, sel_name, line)
        raw.append((run, float(w), s.reindex(ysel.index).values, v.reindex(y24.index).values, p.reindex(idx25).values))
    excl = sin_referencia({"nivel": None if nivel == "-" else nivel})
    fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
    fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
    expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)

    def run_ws(ws):
        own = [(w, s, v, p) for (run, _, s, v, p), w in zip(raw, ws) if run not in excl and w > 0]
        if not own:
            own = [(1.0, s, v, p) for (run, _, s, v, p) in raw if run not in excl]
        wo = sum(o[0] for o in own)
        ref = [sum(o[0] * o[j].sum() for o in own) / wo for j in (1, 2, 3)]
        comps = [(s * ref[0] / s.sum(), v * ref[1] / v.sum(), p * ref[2] / p.sum()) for run, _, s, v, p in raw]
        r, *_ = evaluate(comps, ws, ysel.values, y24.values, 1.0, (a, b), expos)
        return r["d2_sel"], r["d2_v24_f23"]

    base = run_ws([c[1] for c in raw])
    print(line, "partida", [c[1] for c in raw], "V23 %.5f V24 %.5f" % base, flush=True)
    k = len(raw)
    rows = []
    for combo in itertools.product(range(11), repeat=k):
        if sum(combo) != 10:
            continue
        ws = [c / 10 for c in combo]
        s23, s24 = run_ws(ws)
        rows.append((ws, s23, s24))
    for nombre, key in (("V23", lambda r: r[1]), ("V24", lambda r: r[2]), ("media", lambda r: r[1] + r[2]),
                        ("la peor de las dos mejoras", lambda r: min(r[1] - base[0], r[2] - base[1]))):
        print("mejores por", nombre, flush=True)
        for ws, s23, s24 in sorted(rows, key=key, reverse=True)[:5]:
            print("   ", ws, "V23 %.5f (%+.5f)  V24 %.5f (%+.5f)" % (s23, s23 - base[0], s24, s24 - base[1]), flush=True)


if __name__ == "__main__":
    main()
