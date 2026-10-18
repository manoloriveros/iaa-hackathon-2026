"""XGBoost Tweedie (hist) con el mismo contrato: offset por base_margin, tope de autos con recargo, F3 solo en autos.

V23: parada temprana en la mitad de calibración, comparación en la de selección; con --v24 entrena además 2021-2023
con las rondas de V23 x 1,15 y evalúa 2024; con --prod entrena 2021-2024 (x 1,3) y predice 2025.
Uso: python3 xgb_experimento.py <nombre> <ramo> [--v24] [--prod] [--semillas=2]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd
import xgboost as xgb

from comun import WORK, d2, to_model_frame
from experimentos import features, load

CAPS = {"motor": 15000.0}
PARAMS = {"objective": "reg:tweedie", "tweedie_variance_power": 1.5, "eta": 0.03, "max_depth": 4, "min_child_weight": 50, "subsample": 0.8,
          "colsample_bytree": 0.6, "lambda": 20.0, "alpha": 0.0, "tree_method": "hist", "max_cat_to_onehot": 8, "max_bin": 256, "nthread": 2}


def run_fit(X, y, off, cap, rounds, seed, Xv=None, yv=None, offv=None, early=None):
    yt = np.minimum(y, cap) if cap else y
    loading = y.sum() / yt.sum() if cap else 1.0
    base = float(np.log(yt.sum() / off.sum()))
    d = xgb.DMatrix(X, label=yt, base_margin=np.log(off) + base, enable_categorical=True)
    evals = []
    if Xv is not None:
        yvt = np.minimum(yv, cap) if cap else yv
        evals = [(xgb.DMatrix(Xv, label=yvt, base_margin=np.log(offv) + base, enable_categorical=True), "cal")]
    b = xgb.train(dict(PARAMS, seed=seed), d, num_boost_round=rounds, evals=evals, early_stopping_rounds=early, verbose_eval=False)
    return b, base, loading


def pred(b, base, loading, X, off, iters=None):
    d = xgb.DMatrix(X, base_margin=np.log(off) + base, enable_categorical=True)
    rng = (0, iters) if iters else (0, 0)
    return b.predict(d, iteration_range=rng) * loading


def main():
    name, line = sys.argv[1], sys.argv[2]
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[3:] if a.startswith("--"))
    seeds = int(opts.get("semillas", 2))
    t = time.time()
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    expo = df["exposure"].values
    cap = CAPS.get(line)
    tr = df.year.isin([2021, 2022]).values; cal = ((df.year == 2023) & (df.cal_half == 0)).values; sel = ((df.year == 2023) & (df.cal_half == 1)).values
    b, base, ld = run_fit(X[tr], y[tr], off[tr], cap, 6000, 20261017, X[cal], y[cal], off[cal], early=200)
    best = b.best_iteration + 1
    mu = pred(b, base, ld, X[sel], off[sel], best)
    res = {"line": line, "best": best, "d2_sel": round(d2(y[sel], mu), 5)}
    print(name, res, flush=True)
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    if "v24" in opts:
        tr24 = (df.year <= 2023).values; ev24 = (df.year == 2024).values
        m24 = np.zeros(ev24.sum())
        for s in range(seeds):
            b2, base2, ld2 = run_fit(X[tr24], y[tr24], off[tr24], cap, int(best * 1.15), 20261017 + 101 * s)
            m24 += pred(b2, base2, ld2, X[ev24], off[ev24]) / seeds
        res["d2_v24"] = round(d2(y[ev24], m24), 5)
        pd.DataFrame({"row_id": df.row_id[ev24].astype(str).values, "line": line, "y": y[ev24], "mu": m24}).to_parquet(out / "v24.parquet", index=False)
        print(name, res, flush=True)
    if "prod" in opts:
        trp = (df.year <= 2024).values; te = (df.year == 2025).values
        m25 = np.zeros(te.sum())
        for s in range(seeds):
            b3, base3, ld3 = run_fit(X[trp], y[trp], off[trp], cap, int(best * 1.3), 20261017 + 101 * s)
            m25 += pred(b3, base3, ld3, X[te], expo[te]) / seeds
        res["pred_2025_total_CU"] = round(float(m25.sum()), 2)
        pd.DataFrame({"row_id": df.row_id[te].astype(str).values, "line": line, "prediction": m25}).to_parquet(out / "prediccion_2025.parquet", index=False)
    res["secs"] = round(time.time() - t)
    (out / "resumen.json").write_text(json.dumps(res, indent=1))
    print(name, res, flush=True)


if __name__ == "__main__":
    main()
