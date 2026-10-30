"""E07: choose developed-market model settings using developed internal validation."""
import sys, itertools, time
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
from gbm import P_DEV, CONF, MOD, OUT, FASE

res = {}
for l in LINEAS:
    em = cargar("emerging", l, CONF["clima"]); dv = cargar("developed", l, CONF["clima"])
    dv = dv[dv.year.isin(CONF["dev_years"])].reset_index(drop=True)
    cols = comunes(l); cats = categorias_union([dv, em], cols + SOLO_EMERGENTE + MARKETING + TARIFA + MAKE)
    X = matriz(dv, cols, cats); y = dv.y.values; off = np.log(dv.exposure.values * dv.c_fila.values)
    va = dv.fold.values == 0
    dtr = lgb.Dataset(X[~va], y[~va], init_score=off[~va], free_raw_data=False)
    dva = lgb.Dataset(X[va], y[va], init_score=off[va], reference=dtr)
    filas = []
    for l2, md in itertools.product([0.0, 10.0], [300, 1000, 3000]):
        t0 = time.time()
        p = dict(P_DEV, learning_rate=0.03, lambda_l2=l2, min_data_in_leaf=md)
        b = lgb.train(p, dtr, 5000, valid_sets=[dva], callbacks=[lgb.early_stopping(150, verbose=False)])
        mu = np.exp(b.predict(X[va], raw_score=True, num_iteration=b.best_iteration) + off[va])
        k = factor_tweedie(y[~va], np.exp(b.predict(X[~va], raw_score=True, num_iteration=b.best_iteration) + off[~va]))
        dev_v = desviacion(y[va], mu * k).sum()
        filas.append({"lambda_l2": l2, "min_data": md, "rondas": b.best_iteration, "k_entren": k,
                      "D2_val": d2(y[va], mu * k), "s": round(time.time() - t0)})
        print(l, filas[-1], flush=True)
    res[l] = filas
    guardar_json(res, OUT / "T2_rejilla.json")
