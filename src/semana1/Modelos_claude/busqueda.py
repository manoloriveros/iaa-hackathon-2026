"""Búsqueda aleatoria acotada de hiperparámetros LightGBM por ramo en V23 (parada en calibración, comparación en selección).

Se fija la semilla de la búsqueda; cada configuración se registra con su D² de selección. Para controlar el
sobreajuste a la mitad de selección, el elegido se confirma después en V24 con diferencias pareadas frente a la
configuración vigente. Uso: python3 busqueda.py <nombre> <ramo> <n_config>
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

from comun import WORK, d2, to_model_frame
from experimentos import features, fit, load, predict


def main():
    name, line, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    base_cfg = json.load(open("/home/claude/work/cfg_total.json"))[line]["params"]
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    X = to_model_frame(df, feats)
    tr = df.year.isin([2021, 2022]).values
    cal = ((df.year == 2023) & (df.cal_half == 0)).values
    sel = ((df.year == 2023) & (df.cal_half == 1)).values
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    rng = np.random.default_rng(2026)
    res = []
    configs = [dict(base_cfg)]
    for _ in range(n - 1):
        c = dict(base_cfg)
        c.update({"num_leaves": int(rng.choice([4, 5, 7, 10, 15])), "min_data_in_leaf": int(rng.choice([500, 1000, 2000, 4000, 8000])),
                  "feature_fraction": float(rng.choice([0.4, 0.5, 0.6, 0.8])), "bagging_fraction": float(rng.choice([0.6, 0.8, 0.9])),
                  "lambda_l2": float(rng.choice([1, 10, 50, 100])), "learning_rate": float(rng.choice([0.01, 0.02, 0.03])),
                  "extra_trees": bool(rng.choice([False, True])), "path_smooth": float(rng.choice([0, 10, 50])),
                  "tweedie_variance_power": float(rng.choice([1.4, 1.5, 1.6]))})
        configs.append(c)
    for i, c in enumerate(configs):
        t = time.time()
        b, base = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=8000, early=300, params=dict(c))
        mu = predict(b, base, X[sel], off[sel], b.best_iteration)
        r = {"i": i, "d2_sel": round(d2(y[sel], mu), 5), "best": b.best_iteration, "secs": round(time.time() - t),
             "cfg": {k: c[k] for k in ["num_leaves", "min_data_in_leaf", "feature_fraction", "bagging_fraction", "lambda_l2", "learning_rate", "tweedie_variance_power"] if k in c} | {k: c.get(k) for k in ["extra_trees", "path_smooth"]}}
        res.append(r)
        print(r, flush=True)
        (WORK / f"busqueda_{name}_{line}.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
