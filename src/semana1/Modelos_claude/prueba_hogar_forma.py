"""Hogar: formas alternativas para efectos suaves (capital, elevación, zona de inundación) en V23.

Variantes: árboles con hojas lineales (linear_tree), restricciones monótonas (capital creciente, zona de inundación
creciente, elevación y distancia al río decrecientes) y elasticidad del capital en el offset (log(e) + b*log(SI/SI_medio)).
Compara con el modelo vigente en la mitad de selección y guarda las predicciones.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from comun import WORK, d2, to_model_frame
from experimentos import features, fit, load, predict

cfg = json.load(open("/home/claude/work/cfg_total.json"))
for line in ["buildings", "contents"]:
    df = load(line)
    feats = features(line, df, "F0124")
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    tr = df.year.isin([2021, 2022]).values
    cal = ((df.year == 2023) & (df.cal_half == 0)).values
    sel = ((df.year == 2023) & (df.cal_half == 1)).values
    si = df["sum_insured"].values.astype(float)
    si_rel = si / np.median(si[tr])
    mono = {"sum_insured": 1, "log_sum_insured": 1, "flood_zone": 1, "elevation_m": -1, "distance_to_river_km": -1}
    variants = {
        "linear_tree": ({"linear_tree": True, "linear_lambda": 1.0}, off),
        "monotona": ({"monotone_constraints": [mono.get(f, 0) for f in feats], "monotone_constraints_method": "advanced"}, off),
        "elasticidad_03": ({}, off * si_rel ** 0.3),
        "elasticidad_05": ({}, off * si_rel ** 0.5),
    }
    for k, (extra, o) in variants.items():
        p = dict(cfg[line]["params"]); p.update(extra)
        try:
            b, s = fit(X[tr], y[tr], o[tr], X[cal], y[cal], o[cal], rounds=6000, early=200, params=p)
            mu = predict(b, s, X[sel], o[sel], b.best_iteration)
            print(line, k, round(d2(y[sel], mu), 5), b.best_iteration, flush=True)
            pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu}).to_parquet(WORK / f"sel_forma_{k}_{line}.parquet", index=False)
        except Exception as exc:  # una variante que LightGBM no admita no detiene las demás
            print(line, k, "error", exc, flush=True)
