"""Troncos para nuevo negocio entrenados en el desarrollado 2021-2023 y medidos en el nuevo negocio emergente 2023 y 2024.
T2nb: solo filas de nuevo negocio del desarrollado. T2nbw: todas las filas con peso 5 en nuevo negocio. Base: T2b guardado (modelos/dev)."""
import sys, json, time
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
P_DEV = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.05, num_leaves=63, min_data_in_leaf=1000, feature_fraction=0.8,
             bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, max_cat_to_onehot=8, cat_smooth=50, verbose=-1, num_threads=2, seed=20261024)
P_DEVB = {"motor": dict(P_DEV, learning_rate=0.03, lambda_l2=0.0, min_data_in_leaf=300),
          "buildings": dict(P_DEV, learning_rate=0.03, lambda_l2=0.0, min_data_in_leaf=3000),
          "contents": dict(P_DEV, learning_rate=0.03, lambda_l2=10.0, min_data_in_leaf=3000)}
def ajustar(X, y, off, params, max_rounds, es=150, val=None, w=None):
    wt = None if w is None else w[~val]
    dtr = lgb.Dataset(X[~val], y[~val], init_score=off[~val], weight=wt, free_raw_data=False)
    dva = lgb.Dataset(X[val], y[val], init_score=off[val], weight=None if w is None else w[val], reference=dtr)
    b = lgb.train(params, dtr, max_rounds, valid_sets=[dva], callbacks=[lgb.early_stopping(es, verbose=False)])
    n = max(b.best_iteration, 1)
    b = lgb.train(params, lgb.Dataset(X, y, init_score=off, weight=w), n)
    return b, n
OUT = RAIZ / "nb"; OUT.mkdir(exist_ok=True)
def dev(y, m): return 4 * y / np.sqrt(m) + 4 * np.sqrt(m) - 8 * np.sqrt(y)
def kopt(y, m): return np.sum(y / np.sqrt(m)) / np.sum(np.sqrt(m))
res = {}
for linea in (sys.argv[1].split(",") if len(sys.argv) > 1 else LINEAS):
    t0 = time.time()
    em = cargar("emerging", linea, "hasta2023"); dv = cargar("developed", linea, "hasta2023"); dv = dv[dv.year.isin([2021, 2022, 2023])].reset_index(drop=True)
    cols = comunes(linea); cats = categorias_union([dv, em], cols + SOLO_EMERGENTE + MARKETING + TARIFA + MAKE)
    raw = {}
    b2 = lgb.Booster(model_file=str(TRABAJO / "modelos/dev" / f"T2b_{linea}.txt")); raw["T2b"] = b2.predict(matriz(em, cols, cats), raw_score=True)
    off = np.log(dv.exposure.values * dv.c_fila.values)
    nb = dv.new_business.values.astype(bool)
    d1 = dv[nb].reset_index(drop=True)
    bnb, n1 = ajustar(matriz(d1, cols, cats), d1.y.values, np.log(d1.exposure.values * d1.c_fila.values), P_DEVB[linea], 5000, val=d1.fold.values == 0)
    bnb.save_model(str(OUT / f"T2nb_{linea}.txt")); raw["T2nb"] = bnb.predict(matriz(em, cols, cats), raw_score=True)
    w = np.where(nb, 5.0, 1.0)
    bw, n2 = ajustar(matriz(dv, cols, cats), dv.y.values, off, P_DEVB[linea], 5000, val=dv.fold.values == 0, w=w)
    bw.save_model(str(OUT / f"T2nbw_{linea}.txt")); raw["T2nbw"] = bw.predict(matriz(em, cols, cats), raw_score=True)
    pd.DataFrame({"row_id": em.row_id.values, **{k: v for k, v in raw.items()}}).to_parquet(OUT / f"raw_{linea}.parquet", index=False)
    r = {"rondas": {"T2nb": n1, "T2nbw": n2}, "segundos": round(time.time() - t0)}
    tr = (em.conjunto == "train").values
    for anio in (2023, 2024):
        for etiqueta, msk in (("NB", em.new_business.values.astype(bool)), ("NB_anio_completo", em.new_business.values.astype(bool) & (em.exposure.values >= 0.9)), ("REN", ~em.new_business.values.astype(bool))):
            i = tr & (em.year.values == anio) & msk; y = em.y.values[i]; e = em.exposure.values[i] * em.c_fila.values[i]
            null = dev(y, np.full(i.sum(), y.mean())).sum(); m0 = e * kopt(y, e); d0 = dev(y, m0).sum()
            out = {"n": int(i.sum()), "pos": int((y > 0).sum()), "habilidad_exposicion": {}}
            mm = {}
            for k, v in raw.items():
                m = np.exp(v[i]) * e; m = m * kopt(y, m); mm[k] = m
                out["habilidad_exposicion"][k] = round(float((d0 - dev(y, m).sum()) / null), 5)
            for k in ("T2nb", "T2nbw"):
                g = np.sqrt(mm["T2b"] * mm[k]); g = g * kopt(y, g)
                out["habilidad_exposicion"][f"geo(T2b,{k})"] = round(float((d0 - dev(y, g).sum()) / null), 5)
            r[f"{anio}_{etiqueta}"] = out
    res[linea] = r; print(linea, json.dumps(r, indent=0), flush=True)
    json.dump(res, open(OUT / f"nb_backbone_{'_'.join(res)}.json", "w"), indent=1)
