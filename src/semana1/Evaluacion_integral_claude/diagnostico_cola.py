"""Dónde gana y dónde pierde la calibración de forma: cola de siniestros grandes frente al resto de la cartera.

Para cada ramo y corte (V23 selección y V24) reconstruye la mezcla S13 sin forma (S13sf) y con la forma adoptada, y mide:
- cuota de pérdida y número de filas del 0,1 % superior de la pérdida observada, y su peligro dominante,
- real sobre esperado por decil de tasa predicha (S13sf), con y sin ese 0,1 % superior,
- rejilla del exponente de la tasa a (y de la exposición b) con D² renivelado en todos los datos y sin el 0,1 % superior,
  como diferencia frente a S13sf, para ver el intercambio entre cola y resto.
Uso: python3 diagnostico_cola.py  ->  salidas/diagnostico_cola.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/claude/modelos_claude")
from comun import LINES, PERILS, WORK, d2  # noqa: E402
from mezcla3 import ftw, labels, shape_rate  # noqa: E402
from robustez import blend  # noqa: E402

OUT = Path(__file__).resolve().parent / "salidas"
SPEC = json.loads(open(WORK / "spec_s13.json").read())
FORMA = {"motor": (1.09, 0.95), "buildings": (1.08, 1.14), "contents": (1.07, 1.0)}


def d2r(y, mu):
    return d2(y, mu * ftw(y, mu))


def main():
    rep = {}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"] + [f"y_{p}" for p in PERILS[line]])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        _, bsel, b24, _ = blend(SPEC, {}, line, ysel, y24, idx25, expos)
        rep[line] = {}
        for fold, y, mu, e, idx in (("V23", ysel.values, bsel, expos[0], ysel.index), ("V24", y24.values, b24, expos[1], y24.index)):
            thr = np.quantile(y, 0.999)
            top = y > thr
            per = fe.loc[idx, [f"y_{p}" for p in PERILS[line]]].fillna(0).values
            dom = pd.Series(np.array(PERILS[line])[per[top].argmax(1)]).value_counts().to_dict()
            r = mu / e
            dec = pd.qcut(pd.Series(r).rank(method="first"), 10, labels=False).values
            ae = {}
            for k in range(10):
                m = dec == k
                ae[int(k) + 1] = {"ae": round(float(y[m].sum() / mu[m].sum()), 3), "ae_sin_top": round(float(y[m & ~top].sum() / mu[m & ~top].sum()), 3),
                                  "filas_top": int((m & top).sum())}
            # rejilla de forma alrededor de S13sf; diferencias reniveladas frente a S13sf
            base_all, base_keep = d2r(y, mu), d2r(y[~top], mu[~top])
            a0, b0 = FORMA[line]
            grid = {}
            for a in (1.0, 1.02, 1.04, 1.06, 1.08, 1.10):
                for b in sorted({1.0, b0}):
                    mm = shape_rate(mu, e, a, b)
                    grid[f"{a}:{b}"] = {"todo": round(d2r(y, mm) - base_all, 5), "sin_top": round(d2r(y[~top], mm[~top]) - base_keep, 5)}
            rep[line][fold] = {"umbral_top01": round(float(thr), 1), "filas_top": int(top.sum()), "cuota_perdida_top": round(float(y[top].sum() / y.sum()), 4),
                               "peligro_dominante_top": dom, "ae_por_decil_tasa": ae, "rejilla_forma": grid}
            print(line, fold, "top", int(top.sum()), "cuota", rep[line][fold]["cuota_perdida_top"], dom, flush=True)
            print("   AE por decil", [v["ae"] for v in ae.values()], flush=True)
            print("   AE sin top  ", [v["ae_sin_top"] for v in ae.values()], flush=True)
            print("   filas top   ", [v["filas_top"] for v in ae.values()], flush=True)
            for k, v in grid.items():
                print("   forma", k, v, flush=True)
    (OUT / "diagnostico_cola.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
