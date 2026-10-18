import json, numpy as np, pandas as pd
from comun import WORK, d2, to_model_frame
from experimentos import features, fit, load, predict
base_cfg = json.load(open('/home/claude/work/cfg_total.json'))
variantes = {"reg_fuerte": {"num_leaves": 5, "min_data_in_leaf": 8000, "lambda_l2": 100.0, "path_smooth": 50.0, "learning_rate": 0.03, "feature_fraction": 0.8, "bagging_fraction": 0.9},
             "reg_media": {"num_leaves": 5, "min_data_in_leaf": 4000, "lambda_l2": 50.0, "path_smooth": 20.0, "learning_rate": 0.02},
             "sin_region": None}
for line in ["buildings", "contents"]:
    df = load(line); feats = features(line, df, "F0124")
    y = df["T0"].fillna(0).values; off = df["e_ef_coste"].values
    tr = df.year.isin([2021, 2022]).values; cal = ((df.year == 2023) & (df.cal_half == 0)).values; sel = ((df.year == 2023) & (df.cal_half == 1)).values
    for k, v in variantes.items():
        f2 = [f for f in feats if f != "region"] if k == "sin_region" else feats
        p = dict(base_cfg[line]["params"]); p.update(v or {})
        X = to_model_frame(df, f2)
        b, s = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=8000, early=300, params=p)
        mu = predict(b, s, X[sel], off[sel], b.best_iteration)
        print(line, k, round(d2(y[sel], mu), 5), b.best_iteration, flush=True)
        pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu}).to_parquet(WORK / f"sel_hogar_{k}_{line}.parquet", index=False)
