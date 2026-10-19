"""Rejilla corta de regularización por ramo (hogar con las siete variables de cliente F3 de D80; autos con F01234).

La potencia de forma 1,10 que mejora edificios en V23 y V24 indica predicciones demasiado concentradas, señal de
regularización excesiva. Se prueban configuraciones menos restrictivas frente a la vigente: V23 con parada temprana en
la mitad de calibración y comparación en la de selección; V24 con rondas V23 x 1,15 y dos semillas; diferencia pareada.
Uso: python3 rejilla_hogar.py <ramo>
"""
from __future__ import annotations

import json
import sys

import numpy as np

from comun import WORK, d2, deviance, to_model_frame
from experimentos import features, fit, load, predict

line = sys.argv[1]
cfg = json.load(open(WORK / "cfg_hogar_s2.json"))[line]
base = dict(cfg["params"])
VAR = {"buildings": {"base": {}, "l9": {"num_leaves": 9}, "md1000": {"min_data_in_leaf": 1000}, "l15_ff06": {"num_leaves": 15, "feature_fraction": 0.6},
                     "sin_l2": {"lambda_l2": 0.0}, "lr01": {"learning_rate": 0.01}},
       "contents": {"base": {}, "md2000": {"min_data_in_leaf": 2000}, "l11": {"num_leaves": 11}, "l5": {"num_leaves": 5}, "sin_l2": {"lambda_l2": 0.0}},
       "motor": {"base": {}, "md1000": {"min_data_in_leaf": 1000}, "md1000_lr01": {"min_data_in_leaf": 1000, "learning_rate": 0.01}, "ff08": {"feature_fraction": 0.8}}}[line]
df = load(line)
feats = features(line, df, "F01234" if line == "motor" else "F0124") + [c for c in cfg.get("add", []) if c in df.columns]
X = to_model_frame(df, feats)
y = df["T0"].fillna(0).values
off = df["e_ef_coste"].values
yr = df.year.values
tr = yr <= 2022; cal = ((yr == 2023) & (df.cal_half == 0)).values; sel = ((yr == 2023) & (df.cal_half == 1)).values
tr24 = yr <= 2023; ev = yr == 2024
pr23, pr24 = {}, {}
for tag, extra in VAR.items():
    p = dict(base, **extra)
    b, s = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=8000, early=200, params=dict(p))
    best = b.best_iteration
    pr23[tag] = predict(b, s, X[sel], off[sel], best)
    mu = np.zeros(ev.sum())
    for k in range(2):
        b2, s2 = fit(X[tr24], y[tr24], off[tr24], rounds=int(round(best * 1.15)), early=None, params=dict(p, seed=20261017 + 101 * k))
        mu += predict(b2, s2, X[ev], off[ev]) / 2
    pr24[tag] = mu
    out = {"best": best, "V23": round(d2(y[sel], pr23[tag]), 5), "V24": round(d2(y[ev], mu), 5)}
    if tag != "base":
        for fold, yy, pr in (("V23", y[sel], pr23), ("V24", y[ev], pr24)):
            out[f"dif_{fold}"] = round(float((deviance(yy, pr["base"]).sum() - deviance(yy, pr[tag]).sum()) / deviance(yy, np.full(len(yy), yy.mean())).sum()), 5)
    print(line, tag, out, flush=True)
