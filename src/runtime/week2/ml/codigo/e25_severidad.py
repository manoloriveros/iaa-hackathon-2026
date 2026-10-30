"""E25: select gamma-severity grid settings on developed 2021-2023 inner fold 0.
Write validation deviance and the chosen setting per line under trabajo/modelos/dev.
Do not inspect developed 2024 or emerging data.
Usage: python e25_severidad.py [<lines>]
"""
import sys, json, itertools, time
import numpy as np, lightgbm as lgb
from comun import *
from variables import *

SEMILLA = 20261024
REJILLA = list(itertools.product([7, 15, 31, 63], [50, 200, 1000], [1.0, 10.0, 100.0]))


def dev_gamma(y, mu, w):
    return float(np.sum(w * 2 * (-np.log(y / mu) + (y - mu) / mu)) / np.sum(w))


def correr(linea):
    t0 = time.time()
    em = cargar("emerging", linea, "hasta2023"); dv = cargar("developed", linea, "hasta2023")
    dv = dv[dv.year.isin([2021, 2022, 2023])].reset_index(drop=True)
    cols = comunes(linea); cats = categorias_union([dv, em], cols + SOLO_EMERGENTE + MARKETING + TARIFA + MAKE)
    s = (dv.n_sin.values > 0) & (dv.y.values > 0)
    X = matriz(dv, cols, cats)[s].reset_index(drop=True)
    n = dv.n_sin.values[s].astype(float); ysev = dv.y.values[s] / n
    val = (dv.fold.values == 0)[s]
    msev = float(dv.y.values[s].sum() / n.sum())
    off = np.full(len(ysev), np.log(msev))
    filas = []
    for hojas, mind, l2 in REJILLA:
        p = dict(objective="gamma", learning_rate=0.03, num_leaves=hojas, min_data_in_leaf=mind, lambda_l2=l2,
                 feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, max_cat_to_onehot=8, cat_smooth=50,
                 verbose=-1, num_threads=2, seed=SEMILLA)
        dtr = lgb.Dataset(X[~val], ysev[~val], init_score=off[~val], weight=n[~val], free_raw_data=False)
        dva = lgb.Dataset(X[val], ysev[val], init_score=off[val], weight=n[val], reference=dtr)
        b = lgb.train(p, dtr, 3000, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])
        mu = np.exp(b.predict(X[val], raw_score=True, num_iteration=b.best_iteration) + off[val])
        filas.append({"num_leaves": hojas, "min_data_in_leaf": mind, "lambda_l2": l2, "rondas": int(b.best_iteration),
                      "desv_val": dev_gamma(ysev[val], mu, n[val])})
    base = dev_gamma(ysev[val], np.full(val.sum(), np.average(ysev[~val], weights=n[~val])), n[val])
    mejor = min(filas, key=lambda r: r["desv_val"])
    actual = [r for r in filas if (r["num_leaves"], r["min_data_in_leaf"], r["lambda_l2"]) == (31, 200, 10.0)][0]
    guardar_json({"linea": linea, "filas_val": int(val.sum()), "siniestros_val": float(n[val].sum()), "desv_constante": base,
                  "rejilla": filas, "elegida": mejor, "FS_actual": actual, "s": round(time.time() - t0)},
                 TRABAJO / "modelos" / "dev" / f"e25_rejilla_{linea}.json")
    print(linea, "constante %.5f" % base, "FS actual", actual, "elegida", mejor, round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    for l in (sys.argv[1].split(",") if len(sys.argv) > 1 else LINEAS):
        correr(l)
