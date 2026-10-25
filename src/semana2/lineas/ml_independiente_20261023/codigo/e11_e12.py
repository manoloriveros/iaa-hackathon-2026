"""E11 (promedio de 4 semillas de T2b) y E12 (desarrollado reponderado hacia la cartera emergente 2025).
Rondas fijas iguales a las de T2b en la fase dev. Salidas en pred/dev y pred/hold como T2bs4 y T2bw."""
import json
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
from gbm import P_DEVB

RONDAS = {"motor": 249, "buildings": 194, "contents": 169}
out = {}
for l in LINEAS:
    em = cargar("emerging", l, "hasta2023"); dv = cargar("developed", l, "hasta2023")
    dv = dv[dv.year.isin([2021, 2022, 2023])].reset_index(drop=True)
    cols = comunes(l)
    cats = categorias_union([dv, em], cols + SOLO_EMERGENTE + MARKETING + TARIFA + MAKE)
    Xd = matriz(dv, cols, cats); Xe = matriz(em, cols, cats)
    off = np.log(dv.exposure.values * dv.c_fila.values)
    # E11: cuatro semillas (la original 20261024 + tres)
    raws = []
    for s in [20261024, 11, 12, 13]:
        b = lgb.train(dict(P_DEVB[l], seed=s), lgb.Dataset(Xd, dv.y.values, init_score=off), RONDAS[l])
        raws.append(b.predict(Xe, raw_score=True))
    r_s4 = np.log(np.mean(np.exp(np.column_stack(raws)), axis=1))
    # E12: razón de densidad desarrollado -> test emergente 2025 con variables comunes sin historia
    cw = [c for c in cols if c not in ("hist_pol_12m", "hist_cli_12m")]
    te = em[em.conjunto == "test"]
    Xc = pd.concat([matriz(dv, cw, cats), matriz(te, cw, cats)], ignore_index=True)
    z = np.r_[np.zeros(len(dv)), np.ones(len(te))]
    pc = dict(objective="binary", learning_rate=0.05, num_leaves=31, min_data_in_leaf=500, feature_fraction=0.8,
              bagging_fraction=0.8, bagging_freq=1, verbose=-1, num_threads=2, seed=5)
    fo = dv.fold.values
    p = np.zeros(len(dv))
    clf = lgb.train(pc, lgb.Dataset(Xc, z), 200)
    p = clf.predict(matriz(dv, cw, cats))  # dentro de muestra: solo para pesos, no para evaluar
    w = p / (1 - p) * (len(dv) / len(te)); w = np.clip(w, 0.2, 5); w = w / w.mean()
    ess = w.sum() ** 2 / (w ** 2).sum()
    b = lgb.train(P_DEVB[l], lgb.Dataset(Xd, dv.y.values, weight=w, init_score=off), RONDAS[l])
    r_w = b.predict(Xe, raw_score=True)
    out[l] = {"ess_frac": float(ess / len(dv))}
    for nom, r in [("T2bs4", r_s4), ("T2bw", r_w)]:
        em["raw"] = r
        tr = em[(em.conjunto == "train") & (em.year == 2023)].reset_index(drop=True)
        for fase, sets in [("dev", [(tr[tr.fold != k], tr[tr.fold == k]) for k in range(5)]),
                           ("hold", [(tr, em[em.year == 2024].reset_index(drop=True))])]:
            preds = []
            for a, bb in sets:
                k = factor_tweedie(a.y.values, np.exp(a.raw.values) * a.exposure.values * a.c_fila.values)
                preds.append(pd.DataFrame({"row_id": bb.row_id.values, "mu": k * np.exp(bb.raw.values) * bb.exposure.values}))
            pd.concat(preds).to_parquet(TRABAJO / "pred" / fase / f"{nom}_{l}.parquet", index=False)
    print(l, out[l], flush=True)
guardar_json(out, ENTREGA / "e11_e12_info.json")
