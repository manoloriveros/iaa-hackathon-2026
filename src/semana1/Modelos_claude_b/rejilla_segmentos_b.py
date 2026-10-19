"""Pesos de mezcla por segmento (obra nueva frente a renovación, periodo corto frente a completo): ¿aporta algo que los
componentes pesen distinto según el tipo de fila?

Para un ramo, toma los componentes de la especificación, elige en V23 selección los pesos (rejilla de 0,1) que minimizan
la devianza dentro de cada segmento, y mide en V24 (y en V23) el D² completo y el cuerpo (sin el 0,5 % superior,
renivelado) de la mezcla por segmentos frente a la mezcla con los pesos globales de la especificación. La forma del ramo
se aplica igual en los dos casos. El nivel sigue la regla s17.
Uso: python3 rejilla_segmentos_b.py <ramo> <spec_json> [--forma=a:b] [--segmento=new_business|periodo_corto|ambos]
"""
from __future__ import annotations

import itertools
import json
import os as _os
import sys
from pathlib import Path as _Path

import numpy as np
import pandas as pd

_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
sys.path.insert(0, str(_Path(__file__).resolve().parent))
import nivel_b  # noqa: E402
from comun import WORK, d2, deviance  # noqa: E402
from mezcla3 import component, ftw, labels, shape_rate  # noqa: E402


def rt(y, v, q=0.995):
    keep = y <= np.quantile(y, q)
    return d2(y[keep], v[keep] * ftw(y[keep], v[keep]))


def main():
    line, spec_path = sys.argv[1:3]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[3:] if a.startswith("--"))
    forma = tuple(float(x) for x in opts.get("forma", "1:1").split(":"))
    segvar = opts.get("segmento", "ambos")
    spec = json.load(open(spec_path))
    nivel_b.clasificar({line: [c[0] for c in spec[line]]})
    nivel_b.aplicar()
    excl = nivel_b.mezcla3.sin_referencia({"nivel": "s17"})
    ysel, y24, idx25 = labels(line)
    fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "new_business", "periodo_corto", "exposure"])
    fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
    esel, e24 = fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values
    raw = []
    for run, sel_name, w in spec[line]:
        s, v, p = component(run, sel_name, line)
        raw.append((run, w, s.reindex(ysel.index).values, v.reindex(y24.index).values))
    own = [r for r in raw if r[0] not in excl]
    wo = sum(r[1] for r in own)
    ref_tot = [sum(r[1] * r[j].sum() for r in own) / wo for j in (2, 3)]
    S = np.column_stack([r[2] * ref_tot[0] / r[2].sum() for r in raw]); V = np.column_stack([r[3] * ref_tot[1] / r[3].sum() for r in raw])
    y1, y2 = ysel.values, y24.values
    k = len(raw)
    grid = [np.array(c) / 10 for c in itertools.product(range(11), repeat=k) if sum(c) == 10]
    w0 = np.array([r[1] for r in raw], float); w0 = w0 / w0.sum()

    def seg(df_idx, var):
        nb = fe.new_business.reindex(df_idx).astype(float).fillna(0).values > 0.5
        pc = fe.periodo_corto.reindex(df_idx).astype(float).fillna(0).values > 0.5
        if var == "new_business":
            return nb.astype(int)
        if var == "periodo_corto":
            return pc.astype(int)
        return nb.astype(int) * 2 + pc.astype(int)

    for var in (["new_business", "periodo_corto", "ambos"] if segvar == "ambos" else [segvar]):
        g1, g2 = seg(ysel.index, var), seg(y24.index, var)
        pesos = {}
        for gval in np.unique(g1):
            m = g1 == gval
            best = min(grid, key=lambda w: deviance(y1[m], shape_rate(S[m] @ w, esel[m], *forma)).sum())
            pesos[int(gval)] = best
        # mezcla por segmentos y mezcla global, misma forma
        bs = np.zeros(len(y1)); b4 = np.zeros(len(y2))
        for gval, w in pesos.items():
            bs[g1 == gval] = (S[g1 == gval] @ w); b4[g2 == gval] = (V[g2 == gval] @ w)
        bs, b4 = shape_rate(bs, esel, *forma), shape_rate(b4, e24, *forma)
        gs, g4 = shape_rate(S @ w0, esel, *forma), shape_rate(V @ w0, e24, *forma)
        f23s, f23g = ftw(y1, bs), ftw(y1, gs)
        res = {"segmento": var, "pesos_por_segmento": {str(g): list(np.round(w, 2)) for g, w in pesos.items()},
               "filas_v24_por_segmento": {str(g): int((g2 == g).sum()) for g in np.unique(g2)},
               "d2_v23": [round(d2(y1, gs), 5), round(d2(y1, bs), 5)], "d2_v24": [round(d2(y2, g4 * f23g), 5), round(d2(y2, b4 * f23s), 5)],
               "rt995_v23": [round(rt(y1, gs), 5), round(rt(y1, bs), 5)], "rt995_v24": [round(rt(y2, g4), 5), round(rt(y2, b4), 5)]}
        print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
