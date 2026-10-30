"""Fit production peril Poisson frequency and gamma severity on developed 2021-2024.
Use the common T2b schema, weather through 2024 and learning rate 0.08. Predict
emerging target rows and save row_id, ultimate expected counts f_<p>, severity
s_<p> and completeness cp_<p> to trabajo/pred/fsp/<line>_prod.parquet.
"""
import sys, time, json
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
from completitud import por_peligro
linea = sys.argv[1]
VENT, ANIOS, SUFX = "hasta2024", [2021, 2022, 2023, 2024], "_prod"
HIST = ["hist_pol_12m", "hist_cli_12m"]
cols = comunes(linea)
t0 = time.time()
em = cargar("emerging", linea, VENT)
dva = cargar("developed", linea, VENT)
dv = dva[dva.year.isin(ANIOS)].reset_index(drop=True); del dva
cn = pd.read_parquet(TRABAJO / f"conteos_developed_{linea}.parquet")
dv = dv.merge(cn, on="row_id", how="left")
cats = categorias_union([dv, em], cols + HIST + ["new_business", "renewal_count", "prior_claims_5y"])
Xd = matriz(dv, cols, cats); Xe = matriz(em, cols, cats); val = dv.fold.values == 0
perils = sorted(c[2:] for c in cn.columns if c.startswith("n_"))
PF = dict(objective="poisson", learning_rate=0.08, num_leaves=31, min_data_in_leaf=1000, feature_fraction=0.8, bagging_fraction=0.8,
          bagging_freq=1, lambda_l2=10.0, max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261026)
PS = dict(objective="gamma", learning_rate=0.05, num_leaves=15, min_data_in_leaf=200, feature_fraction=0.8, bagging_fraction=0.8,
          bagging_freq=1, lambda_l2=10.0, max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261026)
def fit(X, y, off, p, val, w=None, rounds=2000):
    dtr = lgb.Dataset(X[~val], y[~val], init_score=off[~val], weight=None if w is None else w[~val], free_raw_data=False)
    dvl = lgb.Dataset(X[val], y[val], init_score=off[val], weight=None if w is None else w[val], reference=dtr)
    b = lgb.train(p, dtr, rounds, valid_sets=[dvl], callbacks=[lgb.early_stopping(50, verbose=False)])
    n = max(b.best_iteration, 1); b = lgb.train(p, lgb.Dataset(X, y, init_score=off, weight=w), n); return b, n
out = pd.DataFrame({"row_id": em.row_id.values}); meta = {}
for p in perils:
    n = dv[f"n_{p}"].values.astype(float); yp = dv[f"y_{p}"].values
    cp = np.maximum(por_peligro(linea, p, dv.period_start, dv.period_end), 1e-4)
    off = np.log(dv.exposure.values * cp); b0 = float(np.log(n.sum() / np.exp(off).sum())); off = off + b0
    bf, nf = fit(Xd, n, off, PF, val)
    (TRABAJO / "modelos/fsp_prod").mkdir(parents=True, exist_ok=True)
    bf.save_model(str(TRABAJO / "modelos/fsp_prod" / f"f_{linea}_{p}.txt"))
    s = (n > 0) & (yp > 0); msev = float(yp[s].sum() / n[s].sum())
    bs, ns = fit(Xd[s].reset_index(drop=True), yp[s] / n[s], np.full(s.sum(), np.log(msev)), PS, val[s], w=n[s])
    bs.save_model(str(TRABAJO / "modelos/fsp_prod" / f"s_{linea}_{p}.txt"))
    guardar_json({"b0": b0, "msev": msev, "nf": nf, "ns": ns}, TRABAJO / "modelos/fsp_prod" / f"meta_{linea}_{p}.json")
    out[f"f_{p}"] = np.exp(bf.predict(Xe, raw_score=True) + b0) * em.exposure.values
    out[f"s_{p}"] = np.exp(bs.predict(Xe, raw_score=True) + np.log(msev))
    out[f"cp_{p}"] = por_peligro(linea, p, em.period_start, em.period_end)
    meta[p] = {"b0": b0, "rondas_f": nf, "rondas_s": ns, "n_dev": int(n.sum()), "sev_media": msev}
    print(linea, p, meta[p], round(time.time() - t0), flush=True)
(TRABAJO / "pred" / "fsp").mkdir(parents=True, exist_ok=True)
out.to_parquet(TRABAJO / "pred" / "fsp" / f"{linea}{SUFX}.parquet", index=False)
json.dump(meta, open(TRABAJO / "pred" / "fsp" / f"{linea}{SUFX}_meta.json", "w"), indent=1)
print("fin", linea, round(time.time() - t0))
