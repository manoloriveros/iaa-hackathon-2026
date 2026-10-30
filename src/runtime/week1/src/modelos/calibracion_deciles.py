"""Inspect observed-to-expected ratios by predicted-rate decile in V23 and V24.

Use the evaluated blend, including its V23-derived V24 level factor. Form deciles
from prediction/effective exposure and also report ratios excluding the largest
0.1% of observed losses, to show the influence of the household tail.

Usage: python calibracion_deciles.py <spec>@<shape>@<level> <output.json>
"""
import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK
from mezcla3 import labels
from robustez import blend, parse


def main():
    _, spec, forma = parse("C=" + sys.argv[1])
    rep = {}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        _, bsel, b24, _ = blend(spec, forma, line, ysel, y24, idx25, expos)
        rep[line] = {}
        for fold, y, mu, e in (("V23", ysel.values, bsel, expos[0]), ("V24", y24.values, b24, expos[1])):
            rate = mu / e
            q = np.quantile(rate, np.linspace(0, 1, 11)); dec = np.clip(np.searchsorted(q, rate, side="right") - 1, 0, 9)
            keep = y <= np.quantile(y, 0.999)
            ae = [round(float(y[dec == k].sum() / mu[dec == k].sum()), 3) for k in range(10)]
            ae_sin = [round(float(y[(dec == k) & keep].sum() / mu[(dec == k) & keep].sum()), 3) for k in range(10)]
            rep[line][fold] = {"real_sobre_esperado_por_decil": ae, "sin_0_1_por_ciento_superior": ae_sin, "total": round(float(y.sum() / mu.sum()), 4)}
            print(line, fold, "total", rep[line][fold]["total"], "deciles", ae, flush=True)
            print("   sin top 0,1 %", ae_sin, flush=True)
    (WORK / sys.argv[2]).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
