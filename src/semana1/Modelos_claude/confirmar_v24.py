"""Confirmación en V24 de variantes elegidas en V23, con diferencia pareada y bootstrap frente a la base del ramo.

Cada variante: parámetros extra de LightGBM y/o elasticidad del capital en el offset; rondas = mejor iteración V23 x 1,15;
tres semillas; entrena 2021-2023 y evalúa 2024 sobre T0 con offset de exposición efectiva. Guarda v24 de cada variante.
Uso: python3 confirmar_v24.py <ramo> <variantes_json>
variantes_json: {"base": {"params": {}, "rounds": 350}, "monotona": {"params": {...}, "rounds": 350, "elasticidad": 0.0}}
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import WORK, d2, deviance, to_model_frame
from experimentos import features, fit, load, predict


def main():
    line, vpath = sys.argv[1], sys.argv[2]
    variants = json.loads(open(vpath).read())
    cfg = json.load(open("/home/claude/work/cfg_total.json"))[line]["params"]
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    tr = (df.year <= 2023).values
    ev = (df.year == 2024).values
    si_rel = (df["sum_insured"].values / np.median(df["sum_insured"].values[tr])) if "sum_insured" in df.columns else np.ones(len(df))
    mono = {"sum_insured": 1, "log_sum_insured": 1, "flood_zone": 1, "elevation_m": -1, "distance_to_river_km": -1}
    preds = {}
    for name, v in variants.items():
        p = dict(cfg); p.update(v.get("params", {}))
        if v.get("monotona"):
            p["monotone_constraints"] = [mono.get(f, 0) for f in feats]; p["monotone_constraints_method"] = "advanced"
        o = off * si_rel ** float(v.get("elasticidad", 0.0))
        mu = np.zeros(ev.sum())
        for s in range(3):
            b, base = fit(X[tr], y[tr], o[tr], rounds=int(round(v["rounds"] * 1.15)), early=None, params=dict(p, seed=20261017 + 101 * s))
            mu += predict(b, base, X[ev], o[ev]) / 3
        preds[name] = mu
        print(line, name, "d2_v24", round(d2(y[ev], mu), 5), flush=True)
        pd.DataFrame({"row_id": df.row_id[ev].astype(str).values, "line": line, "y": y[ev], "mu": mu}).to_parquet(WORK / f"v24_{line}_{name}.parquet", index=False)
    yb = y[ev]
    rng = np.random.default_rng(11)
    n = len(yb)
    dbase = deviance(yb, preds["base"])
    for name, mu in preds.items():
        if name == "base":
            continue
        dv = deviance(yb, mu)
        diffs = []
        for _ in range(200):
            i = rng.integers(0, n, n)
            nd = deviance(yb[i], np.full(n, yb[i].mean())).sum()
            diffs.append((dbase[i].sum() - dv[i].sum()) / nd)
        print(line, name, "menos base: media %.5f desv %.5f P(>0) %.3f" % (np.mean(diffs), np.std(diffs), np.mean(np.array(diffs) > 0)), flush=True)


if __name__ == "__main__":
    main()
