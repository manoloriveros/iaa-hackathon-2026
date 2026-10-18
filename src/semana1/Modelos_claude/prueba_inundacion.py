"""Hogar: Tweedie del coste sin inundación + Tweedie del coste de inundación, frente al Tweedie del total."""
import json, numpy as np, pandas as pd
from comun import PERILS, d2, to_model_frame
from experimentos import features, fit, load, predict
cfg = json.load(open('/home/claude/work/cfg_total.json'))
for line in ["buildings", "contents"]:
    df = load(line); feats = features(line, df, "F0124"); X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values; yf = df["y_flood"].fillna(0).values; ynf = y - yf
    tr = df.year.isin([2021, 2022]).values; cal = ((df.year == 2023) & (df.cal_half == 0)).values; sel = ((df.year == 2023) & (df.cal_half == 1)).values
    shares = {p: df.loc[tr, f"y_{p}"].sum() for p in PERILS[line] if p != "flood"}
    tot = sum(shares.values())
    off_nf = sum(df[f"e_ef_{p}"].values * s / tot for p, s in shares.items())
    off_f = df["e_ef_flood"].values
    p = dict(cfg[line]["params"])
    b1, s1 = fit(X[tr], ynf[tr], off_nf[tr], X[cal], ynf[cal], off_nf[cal], rounds=6000, early=200, params=dict(p))
    b2, s2 = fit(X[tr], yf[tr], off_f[tr], X[cal], yf[cal], off_f[cal], rounds=6000, early=200, params=dict(p))
    mu = predict(b1, s1, X[sel], off_nf[sel], b1.best_iteration) + predict(b2, s2, X[sel], off_f[sel], b2.best_iteration)
    print(line, "hibrido inundación", round(d2(y[sel], mu), 5), "balance", round(mu.sum() / y[sel].sum(), 4), "iter", b1.best_iteration, b2.best_iteration, flush=True)
    pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu}).to_parquet(f"/home/claude/work/sel_hib_{line}.parquet", index=False)
