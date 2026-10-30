"""Fit CatBoost Tweedie under the same exposure contract as LightGBM in V23.

Use effective exposure, the motor cap with a uniform surcharge and motor F3
features. Stop on the calibration half and compare on the selection half.
Save sel_<name>.parquet for the frozen blending workflow.

Usage: python cat_experimento.py <name> [<lines>] [--depth=6] [--lr=0.05] [--f3s2]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from comun import LINES, WORK, d2
from experimentos import features, load

CAPS = {"motor": 15000.0}
# The seven approved household customer features are enabled only with --f3s2 (D80).
F3S2 = ["prior_claims_5y", "credit_band", "missed_payments_12m", "household_size", "years_at_address", "marital_status", "licence_points"]


def frame(df, feats):
    X = df[feats].copy()
    cats = []
    for c in X.columns:
        s = X[c]
        if pd.api.types.is_bool_dtype(s.dtype):
            X[c] = s.astype("float32")
        elif pd.api.types.is_numeric_dtype(s.dtype):
            X[c] = s.astype("float64")
        else:
            if pd.api.types.infer_dtype(s, skipna=True) == "boolean":
                X[c] = s.map({True: 1.0, False: 0.0}).astype("float32")
            else:
                X[c] = s.astype(str).fillna("nan")
                cats.append(c)
    return X, cats


def main():
    name = sys.argv[1]
    lines = sys.argv[2].split(",") if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else LINES
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[2:] if a.startswith("--"))
    depth, lr = int(opts.get("depth", 6)), float(opts.get("lr", 0.05))
    power = float(opts.get("p", 1.5))
    if "cap" in opts:
        CAPS["motor"] = float(opts["cap"])
    rep, frames = {}, []
    for line in lines:
        t = time.time()
        df = load(line)
        feats = features(line, df, "F01234" if line == "motor" else "F0124")
        if line != "motor" and "f3s2" in opts:
            feats += [c for c in F3S2 if c in df.columns and c not in feats]
        X, cats = frame(df, feats)
        tr = df.year.isin([2021, 2022]).values
        cal = ((df.year == 2023) & (df.cal_half == 0)).values
        sel = ((df.year == 2023) & (df.cal_half == 1)).values
        y = df["T0"].fillna(0).values
        off = df["e_ef_coste"].values
        cap = CAPS.get(line)
        yt = np.minimum(y, cap) if cap else y
        loading = y[tr].sum() / yt[tr].sum() if cap else 1.0
        base = float(np.log(yt[tr].sum() / off[tr].sum()))
        ptr = Pool(X[tr], yt[tr], cat_features=cats, baseline=np.log(off[tr]) + base)
        pcal = Pool(X[cal], yt[cal], cat_features=cats, baseline=np.log(off[cal]) + base)
        m = CatBoostRegressor(loss_function=f"Tweedie:variance_power={power}", iterations=4000, learning_rate=lr, depth=depth, l2_leaf_reg=10,
                              od_type="Iter", od_wait=200, thread_count=2, random_seed=20261017, verbose=0, boost_from_average=False,
                              one_hot_max_size=8, use_best_model=True)
        m.fit(ptr, eval_set=pcal)
        raw = m.predict(Pool(X[sel], cat_features=cats), prediction_type="RawFormulaVal")
        mu = np.exp(raw + np.log(off[sel]) + base) * loading
        rep[line] = {"d2_sel": round(d2(y[sel], mu), 5), "best": int(m.get_best_iteration()), "balance_sel": round(float(mu.sum() / y[sel].sum()), 4), "secs": round(time.time() - t)}
        print(name, line, rep[line], flush=True)
        frames.append(pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu}))
    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(WORK / f"sel_{name}.parquet", index=False)
    if len(lines) == 3:
        rep["global"] = round(d2(out.y, out.mu), 5)
        print("== ", name, "global", rep["global"], flush=True)
    (WORK / f"eval_{name}.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
