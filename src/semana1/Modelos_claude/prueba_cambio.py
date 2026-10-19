"""Comparación pareada: configuración vigente frente a la misma con variables de cambio respecto del periodo anterior.

Base: autos F01234; hogar F0124 más las siete variables de cliente F3 (D80). Variables nuevas de cambio_<ramo>.parquet
(variables_cambio.py), sin las constantes. V23: parada temprana en la mitad de calibración y comparación en la de
selección; V24: rondas V23 x 1,15 con tres semillas; bootstrap de la diferencia pareada.
Uso: python3 prueba_cambio.py [ramos] [--sin_prima] [--archivo=cambio|fin]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import WORK, d2, deviance, to_model_frame
from experimentos import features, fit, load, predict

cfg = json.load(open(WORK / "cfg_hogar_s2.json"))
lines = sys.argv[1].split(",") if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else ["motor", "buildings", "contents"]
for line in lines:
    df = load(line)
    pref = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--archivo=")), "cambio")
    cb = pd.read_parquet(WORK / f"{pref}_{line}.parquet")
    df["row_id_s"] = df.row_id.astype(str)
    df = df.merge(cb.rename(columns={"row_id": "row_id_s"}), on="row_id_s", how="left", validate="one_to_one")
    new = [c for c in cb.columns if c != "row_id" and df[c].nunique(dropna=True) > 1]
    if "--sin_prima" in sys.argv:
        new = [c for c in new if c != "cb_cambio_prima"]
    base = features(line, df, "F01234" if line == "motor" else "F0124")
    base += [c for c in cfg[line].get("add", []) if c not in base]
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    yr = df.year.values
    tr = yr <= 2022; cal = ((yr == 2023) & (df.cal_half == 0)).values; sel = ((yr == 2023) & (df.cal_half == 1)).values
    tr24 = yr <= 2023; ev = yr == 2024
    p = dict(cfg[line]["params"])
    pr23, pr24 = {}, {}
    for tag, feats in (("base", base), ("cambio", base + new)):
        X = to_model_frame(df, feats)
        b, s = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(p))
        best = b.best_iteration
        pr23[tag] = predict(b, s, X[sel], off[sel], best)
        mu = np.zeros(ev.sum())
        for k in range(3):
            b2, s2 = fit(X[tr24], y[tr24], off[tr24], rounds=int(round(best * 1.15)), early=None, params=dict(p, seed=20261017 + 101 * k))
            mu += predict(b2, s2, X[ev], off[ev]) / 3
        pr24[tag] = mu
        imp = pd.Series(b2.feature_importance("gain"), index=feats)
        print(line, tag, "best", best, "V23", round(d2(y[sel], pr23[tag]), 5), "V24", round(d2(y[ev], mu), 5),
              {c: round(float(imp[c] / imp.sum()), 4) for c in new} if tag == "cambio" else "", flush=True)
    rng = np.random.default_rng(7)
    for fold, yy, pr in (("V23", y[sel], pr23), ("V24", y[ev], pr24)):
        db, dv = deviance(yy, pr["base"]), deviance(yy, pr["cambio"])
        n = len(yy); out = []
        for _ in range(200):
            i = rng.integers(0, n, n)
            out.append((db[i].sum() - dv[i].sum()) / deviance(yy[i], np.full(n, yy[i].mean())).sum())
        print(line, fold, "cambio menos base %.5f desv %.5f P(>0) %.2f" % (np.mean(out), np.std(out), np.mean(np.array(out) > 0)), flush=True)
