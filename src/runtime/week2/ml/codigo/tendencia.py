"""Estimate developed-market annual trend and apply the exposure-weighted time shift.
Exclude year and history features. Fit log-linear observed/expected trends using
completeness-adjusted labels and expected-cost weights. HOLD uses developed
2021-2023 and the 2023-to-2024 shift; production uses 2021-2024 and the shift
from emerging 2023-2024 to 2025.
Usage: python tendencia.py <phase>
"""
import sys
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
from gbm import P_DEVB, ajustar, CONF, FASE, MOD, OUT

res = {}
for l in LINEAS:
    dv = cargar("developed", l, CONF["clima"]); dv = dv[dv.year.isin(CONF["dev_years"])].reset_index(drop=True)
    em = cargar("emerging", l, CONF["clima"])
    cols = [c for c in comunes(l) if c not in ("hist_pol_12m", "hist_cli_12m")]
    cats = categorias_union([dv, em], cols)
    X = matriz(dv, cols, cats); off = np.log(dv.exposure.values * dv.c_fila.values)
    b, n = ajustar(X, dv.y.values, off, P_DEVB[l], 5000, es=150, val=dv.fold.values == 0)
    mu = np.exp(b.predict(X, raw_score=True) + off)
    g = pd.DataFrame({"year": dv.year, "y": dv.y, "m": mu}).groupby("year").sum()
    g["ae"] = g.y / g.m
    x = g.index.values.astype(float); w = g.m.values
    A = np.vstack([np.ones_like(x), x - x.mean()]).T
    beta = np.linalg.lstsq(A * np.sqrt(w)[:, None], np.log(g.ae.values) * np.sqrt(w), rcond=None)[0]
    tau = float(np.exp(beta[1]))
    # Time shift between exposure-weighted mean coverage dates in training and target.
    def fecha_media(d):
        mid = d.period_start + (d.period_end - d.period_start) / 2
        anio = mid.dt.year + (mid.dt.dayofyear - 0.5) / 365.25
        return float(np.average(anio, weights=d.exposure))
    tr = em[(em.conjunto == "train") & em.year.isin(CONF["em_train"])]
    ob = em[em.year == CONF["em_eval"]]
    dt = fecha_media(ob) - fecha_media(tr)
    res[l] = {"ae_por_anio": g.ae.round(4).to_dict(), "tau_anual": tau, "dt": dt, "factor": tau ** dt, "rondas": n}
    print(l, res[l], flush=True)
guardar_json(res, OUT / "tendencia.json")
