"""Diagnóstico (sin uso en entregas): subconjuntos pequeños de F3 en hogar.

F3 completo empeoró edificios y contenidos en V23 (0,1098 y 0,0774 frente a 0,1120 y 0,0848), probablemente por las
categóricas de alta cardinalidad (correo, campaña, sucursal, aseguradora previa, ocupación). Aquí se prueban solo
variables de riesgo clásicas del cliente. Incluir alguna en una entrega exige autorización del participante, porque la
autorización vigente de F3 es solo para autos.
V23: parada temprana en la mitad de calibración, comparación en la de selección; V24: rondas V23 x 1,15, tres semillas,
diferencia pareada con bootstrap frente a la base del ramo.
Uso: python3 prueba_f3_hogar.py [ramos]
"""
from __future__ import annotations

import json
import sys

import numpy as np

from comun import d2, deviance, to_model_frame
from experimentos import features, fit, load, predict

cfg = json.load(open("/home/claude/work/cfg_total.json"))
SUBSETS = {"base": [], "S1": ["prior_claims_5y", "credit_band", "missed_payments_12m"],
           "S2": ["prior_claims_5y", "credit_band", "missed_payments_12m", "household_size", "years_at_address", "marital_status", "licence_points"]}
if "--solo_s0" in sys.argv:
    # prior_claims_5y es la única columna de F3 con disponibilidad resuelta (declarada antes de incorporarse, D76)
    SUBSETS = {"base": [], "S0": ["prior_claims_5y"]}
lines = sys.argv[1].split(",") if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else ["buildings", "contents"]
for line in lines:
    df = load(line)
    base_feats = features(line, df, "F0124")
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    yr = df.year.values
    tr = yr <= 2022; cal = ((yr == 2023) & (df.cal_half == 0)).values; sel = ((yr == 2023) & (df.cal_half == 1)).values
    tr24 = yr <= 2023; ev = yr == 2024
    p = dict(cfg[line]["params"])
    preds24, preds23 = {}, {}
    for tag, extra in SUBSETS.items():
        feats = base_feats + [c for c in extra if c in df.columns]
        X = to_model_frame(df, feats)
        b, s = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(p))
        best = b.best_iteration
        preds23[tag] = predict(b, s, X[sel], off[sel], best)
        mu = np.zeros(ev.sum())
        for k in range(3):
            b2, s2 = fit(X[tr24], y[tr24], off[tr24], rounds=int(round(best * 1.15)), early=None, params=dict(p, seed=20261017 + 101 * k))
            mu += predict(b2, s2, X[ev], off[ev]) / 3
        preds24[tag] = mu
        print(line, tag, "best", best, "V23", round(d2(y[sel], preds23[tag]), 5), "V24", round(d2(y[ev], mu), 5), flush=True)
    rng = np.random.default_rng(5)
    for tag in SUBSETS:
        if tag == "base":
            continue
        for fold, yy, pr in (("V23", y[sel], preds23), ("V24", y[ev], preds24)):
            db, dv = deviance(yy, pr["base"]), deviance(yy, pr[tag])
            n = len(yy); out = []
            for _ in range(200):
                i = rng.integers(0, n, n)
                out.append((db[i].sum() - dv[i].sum()) / deviance(yy[i], np.full(n, yy[i].mean())).sum())
            print(line, tag, fold, "menos base %.5f desv %.5f P(>0) %.2f" % (np.mean(out), np.std(out), np.mean(np.array(out) > 0)), flush=True)
