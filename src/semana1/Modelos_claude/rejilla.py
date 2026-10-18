"""Rejilla de hiperparámetros en V23 (parada en la mitad de calibración, comparación en la de selección).

Carga cada ramo una vez, ajusta cada configuración, guarda las predicciones de la mitad de selección y calcula el D²
global por configuración. También prueba dos calibraciones estimadas en la mitad de calibración: balance (suma) y el
factor que minimiza la desviación Tweedie con p=1,5, sum(y/sqrt(m))/sum(sqrt(m)).
Uso: python3 rejilla.py <nombre> <conjunto>
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from comun import LINES, WORK, d2, to_model_frame
from experimentos import fit, features, load, predict

L7 = {"learning_rate": 0.02, "num_leaves": 7, "min_data_in_leaf": 2000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16}
CONFIGS = {
    "l7": dict(L7),
    "l7_p13": dict(L7, tweedie_variance_power=1.3),
    "l7_p14": dict(L7, tweedie_variance_power=1.4),
    "l5": dict(L7, num_leaves=5),
    "l7_ff06": dict(L7, feature_fraction=0.6),
    "l7_md4000": dict(L7, min_data_in_leaf=4000),
    "l7_cap": dict(L7, cap=300000.0),
    "base": {},
    "lento_15": {"learning_rate": 0.02, "num_leaves": 15, "min_data_in_leaf": 1000},
    "lento_15_cat": {"learning_rate": 0.02, "num_leaves": 15, "min_data_in_leaf": 1000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16},
    "lento_31_cat": {"learning_rate": 0.02, "num_leaves": 31, "min_data_in_leaf": 2000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16, "feature_fraction": 0.6},
    "lento_7_cat": {"learning_rate": 0.02, "num_leaves": 7, "min_data_in_leaf": 2000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16},
    "lento_15_cat_p16": {"learning_rate": 0.02, "num_leaves": 15, "min_data_in_leaf": 1000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16, "tweedie_variance_power": 1.6},
    "lento_15_cat_p13": {"learning_rate": 0.02, "num_leaves": 15, "min_data_in_leaf": 1000, "cat_smooth": 200, "cat_l2": 50, "min_data_per_group": 1000, "max_cat_threshold": 16, "tweedie_variance_power": 1.3},
}


def main():
    name, set_name = sys.argv[1], sys.argv[2]
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else list(CONFIGS)
    drop = set(sys.argv[4].split(",")) if len(sys.argv) > 4 else set()
    store = {k: {"y": [], "mu": [], "mu_bal": [], "mu_tw": []} for k in only}
    report = {}
    for line in LINES:
        df = load(line)
        feats = [f for f in features(line, df, set_name) if f not in drop]
        X = to_model_frame(df, feats)
        tr = df.year.isin([2021, 2022]).values
        cal = ((df.year == 2023) & (df.cal_half == 0)).values
        sel = ((df.year == 2023) & (df.cal_half == 1)).values
        y = df["T0"].fillna(0).values
        off = df["e_ef_coste"].values
        for k in only:
            t = time.time()
            booster, base = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], params=dict(CONFIGS[k]), rounds=6000, early=200)
            best = booster.best_iteration or booster.current_iteration()
            mu_cal = predict(booster, base, X[cal], off[cal], best)
            mu_sel = predict(booster, base, X[sel], off[sel], best)
            f_bal = y[cal].sum() / mu_cal.sum()
            f_tw = (y[cal] / np.sqrt(mu_cal)).sum() / np.sqrt(mu_cal).sum()
            r = {"best": best, "d2_sel": round(d2(y[sel], mu_sel), 5), "d2_sel_bal": round(d2(y[sel], mu_sel * f_bal), 5), "d2_sel_tw": round(d2(y[sel], mu_sel * f_tw), 5),
                 "f_bal": round(float(f_bal), 4), "f_tw": round(float(f_tw), 4), "balance_sel": round(float(mu_sel.sum() / y[sel].sum()), 4), "secs": round(time.time() - t)}
            report.setdefault(k, {})[line] = r
            store[k]["y"].append(y[sel]); store[k]["mu"].append(mu_sel); store[k]["mu_bal"].append(mu_sel * f_bal); store[k]["mu_tw"].append(mu_sel * f_tw)
            print(set_name, k, line, r, flush=True)
    for k in only:
        yy = np.concatenate(store[k]["y"])
        report[k]["global"] = {"d2_sel": round(d2(yy, np.concatenate(store[k]["mu"])), 5), "d2_sel_bal": round(d2(yy, np.concatenate(store[k]["mu_bal"])), 5),
                               "d2_sel_tw": round(d2(yy, np.concatenate(store[k]["mu_tw"])), 5)}
        print("== ", k, report[k]["global"], flush=True)
    (WORK / f"grid_{name}.json").write_text(json.dumps(report, indent=1, default=float))


if __name__ == "__main__":
    main()
