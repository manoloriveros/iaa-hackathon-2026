"""Diagnose variability in comparisons on random customer subsets of V23/V24.

Draw 1,000 customer subsets at 30% and 50%, retaining each candidate's own level.
Report the mean global-D2 difference, P(difference>0) and a 90% interval. These
local simulations do not reproduce Kaggle's unknown 2025 public subset.
Usage: python publico_simulado.py <output.json> <ref>=<spec>[@<shape>] <cand>=<spec>[@<shape>] [...]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK, deviance
from mezcla3 import labels
from robustez import blend, parse

B = 1000


def main():
    out_path = sys.argv[1]
    cands = [parse(a) for a in sys.argv[2:]]
    rng = np.random.default_rng(20261019)
    folds = {"V23": {"y": [], "cust": [], "pred": {c[0]: [] for c in cands}}, "V24": {"y": [], "cust": [], "pred": {c[0]: [] for c in cands}}}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "customer_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        folds["V23"]["y"].append(ysel.values); folds["V24"]["y"].append(y24.values)
        folds["V23"]["cust"].append(fe.customer_id.reindex(ysel.index).astype(str).values)
        folds["V24"]["cust"].append(fe.customer_id.reindex(y24.index).astype(str).values)
        for name, spec, forma in cands:
            _, bsel, b24, _ = blend(spec, forma, line, ysel, y24, idx25, expos)
            folds["V23"]["pred"][name].append(bsel); folds["V24"]["pred"][name].append(b24)
    rep = {}
    ref = cands[0][0]
    for fold, d in folds.items():
        y = np.concatenate(d["y"]); cu = np.concatenate(d["cust"])
        codes, inv = np.unique(cu, return_inverse=True)
        nc = len(codes)
        dev = {name: deviance(y, np.concatenate(p)) for name, p in d["pred"].items()}
        rep[fold] = {}
        for frac in (0.3, 0.5):
            res = {name: [] for name in dev if name != ref}
            pairs = [(a, b) for i, a in enumerate(dev) for b in list(dev)[i + 1:] if a != ref and b != ref]
            pres = {f"{a}-{b}": [] for a, b in pairs}
            for _ in range(B):
                keep = (rng.random(nc) < frac)[inv]
                yk = y[keep]
                null = deviance(yk, np.full_like(yk, yk.mean())).sum()
                d2k = {name: 1.0 - v[keep].sum() / null for name, v in dev.items()}
                for name in res:
                    res[name].append(d2k[name] - d2k[ref])
                for a, b in pairs:
                    pres[f"{a}-{b}"].append(d2k[a] - d2k[b])
            summ = {}
            for k, v in list({f"{n}-{ref}": res[n] for n in res}.items()) + list(pres.items()):
                v = np.array(v)
                summ[k] = {"media": round(float(v.mean()), 5), "P_mayor_que_0": round(float((v > 0).mean()), 3),
                           "ic90": [round(float(np.quantile(v, 0.05)), 5), round(float(np.quantile(v, 0.95)), 5)]}
                print(fold, f"{int(frac * 100)} %", k, summ[k], flush=True)
            rep[fold][f"{int(frac * 100)}%"] = summ
    (WORK / out_path).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
