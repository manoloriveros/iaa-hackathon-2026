"""Rejilla de pesos en el símplex (pasos de 0,1) con la peor de cuatro mejoras: V23 y V24, con todas las filas y sin el 0,1 %
superior de T0 del ramo (el mismo recorte que robustez.py, sin renivelar).

Igual que rejilla_pesos.py en todo lo demás: carga los componentes una vez, aplica la regla de nivel indicada y la forma del
ramo, y evalúa cada combinación con evaluate de mezcla3 (V23 selección sin factor; V24 con el factor de V23). Informa las
mejores combinaciones por la peor de las cuatro mejoras frente a la partida, y también por la peor de las dos de siempre.
Preinscrito en el foro (CLA-20261018-016) antes de calcular.
Uso: python3 rejilla_robusta.py <ramo> <forma a:b> <nivel|-> <corrida:sel:peso_partida> [...]
"""
from __future__ import annotations

import itertools
import sys

import numpy as np
import pandas as pd

from comun import WORK, d2
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
    y23, y4 = ysel.values, y24.values
    k23 = y23 <= np.quantile(y23, 0.999); k24 = y4 <= np.quantile(y4, 0.999)

    def run_ws(ws):
        own = [(w, s, v, p) for (run, _, s, v, p), w in zip(raw, ws) if run not in excl and w > 0]
        if not own:
            own = [(1.0, s, v, p) for (run, _, s, v, p) in raw if run not in excl]
        wo = sum(o[0] for o in own)
        ref = [sum(o[0] * o[j].sum() for o in own) / wo for j in (1, 2, 3)]
        comps = [(s * ref[0] / s.sum(), v * ref[1] / v.sum(), p * ref[2] / p.sum()) for run, _, s, v, p in raw]
        r, bsel, b24, _ = evaluate(comps, ws, y23, y4, 1.0, (a, b), expos)
        return (r["d2_sel"], r["d2_v24_f23"], d2(y23[k23], bsel[k23]), d2(y4[k24], b24[k24]))

    base = run_ws([c[1] for c in raw])
    print(line, "partida", [c[1] for c in raw], "V23 %.5f V24 %.5f | sin top V23 %.5f V24 %.5f" % base, flush=True)
    rows = []
    for combo in itertools.product(range(11), repeat=len(raw)):
        if sum(combo) != 10:
            continue
        ws = [c / 10 for c in combo]
        rows.append((ws, run_ws(ws)))
    for nombre, key in (("la peor de las cuatro mejoras", lambda r: min(x - y for x, y in zip(r[1], base))),
                        ("la peor de las dos mejoras (completo)", lambda r: min(r[1][0] - base[0], r[1][1] - base[1]))):
        print("mejores por", nombre, flush=True)
        for ws, m in sorted(rows, key=key, reverse=True)[:5]:
            print("   ", ws, " ".join("%+.5f" % (x - y) for x, y in zip(m, base)), flush=True)


if __name__ == "__main__":
    main()
