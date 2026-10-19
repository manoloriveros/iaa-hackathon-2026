"""Restricciones monótonas en el LightGBM de autos (dirección actuarial esperada), comparación pareada V23 y V24.

Variables y signo: historia de siniestros y puntos de licencia (+), impagos (+), kilometraje (+), años de NCB y de
licencia (−), franquicias voluntaria y obligatoria (−, el coste es neto de franquicia). El resto sin restricción.
V23: parada temprana en la mitad de calibración y comparación en la de selección; V24: rondas V23 x 1,15, dos semillas.
Uso: python3 prueba_monotona_autos.py
"""
from __future__ import annotations

import json

import numpy as np

from comun import WORK, d2, deviance, to_model_frame
from experimentos import features, fit, load, predict

MONO = {"prior_claims_5y": 1, "f1_notificaciones_previas": 1, "f1x_notif_bodily_injury": 1, "f1x_notif_own_damage": 1, "f1x_notif_third_party_prop": 1,
        "f1x_notif_theft": 1, "f1x_notif_glass_hail": 1, "f1x_tasa_notif_previa": 1, "licence_points": 1, "missed_payments_12m": 1, "annual_mileage": 1,
        "ncb_years": -1, "years_licensed": -1, "voluntary_excess": -1, "compulsory_excess": -1}
cfg = json.load(open(WORK / "cfg_total.json"))["motor"]["params"]
df = load("motor")
feats = features("motor", df, "F01234")
X = to_model_frame(df, feats)
y = df["T0"].fillna(0).values
off = df["e_ef_coste"].values
yr = df.year.values
tr = yr <= 2022; cal = ((yr == 2023) & (df.cal_half == 0)).values; sel = ((yr == 2023) & (df.cal_half == 1)).values
tr24 = yr <= 2023; ev = yr == 2024
pr23, pr24 = {}, {}
for tag, extra in (("base", {}), ("monotona", {"monotone_constraints": [MONO.get(f, 0) for f in feats], "monotone_constraints_method": "advanced"})):
    p = dict(cfg, **extra)
    b, s = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(p))
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
    print("motor", tag, out, flush=True)
