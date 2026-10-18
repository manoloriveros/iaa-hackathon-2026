"""Potencia Tweedie de entrenamiento distinta de la de evaluación (1,5) con la configuración vigente del ramo.

Con colas pesadas la varianza real puede crecer más rápido que mu^1,5; entrenar con la potencia más cercana a la real da
estimaciones de la media más eficientes aunque la métrica use 1,5. V23 (parada temprana en calibración, comparación en
selección) y V24 (rondas V23 x 1,15, dos semillas), siempre evaluando con potencia 1,5.
Uso: python3 prueba_potencia.py <ramo> <potencias separadas por coma>
"""
from __future__ import annotations

import json
import sys

import numpy as np

from comun import d2, to_model_frame
from experimentos import features, fit, load, predict

line = sys.argv[1]
powers = [float(x) for x in sys.argv[2].split(",")]
cfg = json.load(open("/home/claude/work/cfg_total.json"))[line]["params"]
df = load(line)
feats = features(line, df, "F01234" if line == "motor" else "F0124")
X = to_model_frame(df, feats)
y = df["T0"].fillna(0).values
off = df["e_ef_coste"].values
yr = df.year.values
tr = yr <= 2022; cal = ((yr == 2023) & (df.cal_half == 0)).values; sel = ((yr == 2023) & (df.cal_half == 1)).values
tr24 = yr <= 2023; ev = yr == 2024
for pw in powers:
    p = dict(cfg, tweedie_variance_power=pw)
    b, s = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(p))
    best = b.best_iteration
    m23 = predict(b, s, X[sel], off[sel], best)
    mu = np.zeros(ev.sum())
    for k in range(2):
        b2, s2 = fit(X[tr24], y[tr24], off[tr24], rounds=int(round(best * 1.15)), early=None, params=dict(p, seed=20261017 + 101 * k))
        mu += predict(b2, s2, X[ev], off[ev]) / 2
    print(line, "p", pw, "best", best, "V23", round(d2(y[sel], m23), 5), "V24", round(d2(y[ev], mu), 5), flush=True)
