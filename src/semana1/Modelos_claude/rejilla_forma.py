"""Rejilla de la calibración de forma (a sobre la tasa, b sobre la exposición) para una mezcla ya especificada.

Carga los componentes de cada ramo una sola vez, los reescala como mezcla3.py (con la regla de nivel indicada) y evalúa
cada par (a, b) con la función evaluate de mezcla3: D² de V23 selección sin factor y D² de V24 con el factor de V23.
La elección se hace con V23 y V24 solo confirma; se informa también la suma de ambas mejoras frente al par vigente.
Uso: python3 rejilla_forma.py <spec_json> <salida.json> [--nivel=s17] [--a=1.0,1.05,...] [--b=0.9,1.0,...]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK
from mezcla3 import component, evaluate, labels, sin_referencia

VIGENTE = {"motor": (1.09, 0.95), "buildings": (1.08, 1.14), "contents": (1.07, 1.0)}


def main():
    spec = json.loads(open(sys.argv[1]).read())
    out = sys.argv[2]
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[3:] if a.startswith("--"))
    A = [float(x) for x in opts.get("a", "1.0,1.03,1.06,1.09,1.12,1.15").split(",")]
    Bv = [float(x) for x in opts.get("b", "0.85,0.9,0.95,1.0,1.05,1.1,1.15,1.2").split(",")]
    rep = {}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        raw = []
        for run, sel_name, w in spec[line]:
            s, v, p = component(run, sel_name, line)
            raw.append((run, w, s.reindex(ysel.index).values, v.reindex(y24.index).values, p.reindex(idx25).values))
        own = [(w, s, v, p) for run, w, s, v, p in raw if run not in sin_referencia(opts)]
        wo = sum(o[0] for o in own)
        ref = [sum(o[0] * o[j].sum() for o in own) / wo for j in (1, 2, 3)]
        comps = [(s * ref[0] / s.sum(), v * ref[1] / v.sum(), p * ref[2] / p.sum()) for run, w, s, v, p in raw]
        ws = [c[2] for c in spec[line]]
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        base, *_ = evaluate(comps, ws, ysel.values, y24.values, 1.0, VIGENTE[line], expos)
        rows = []
        for a in A:
            for b in Bv:
                r, *_ = evaluate(comps, ws, ysel.values, y24.values, 1.0, (a, b), expos)
                rows.append({"a": a, "b": b, "d2_sel": round(r["d2_sel"], 5), "d2_v24": round(r["d2_v24_f23"], 5),
                             "dif_sel": round(r["d2_sel"] - base["d2_sel"], 5), "dif_v24": round(r["d2_v24_f23"] - base["d2_v24_f23"], 5)})
        best = max(rows, key=lambda x: x["d2_sel"])
        rep[line] = {"vigente": {"a": VIGENTE[line][0], "b": VIGENTE[line][1], "d2_sel": round(base["d2_sel"], 5), "d2_v24": round(base["d2_v24_f23"], 5)},
                     "mejor_v23": best, "rejilla": rows}
        print(line, "vigente", rep[line]["vigente"], "mejor V23", best, flush=True)
        top = sorted(rows, key=lambda x: -x["d2_sel"])[:6]
        for t in top:
            print("   ", t, flush=True)
    (WORK / out).write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
