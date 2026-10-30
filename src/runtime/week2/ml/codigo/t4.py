"""T4 preregistered joint developed/emerging model with a market indicator.
Sample 35% of developed customers for computation and weight emerging rows by 5.
Stop on internal emerging validation and relevel on emerging training-fold rows.
"""
import sys, hashlib
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
from gbm import P_DEVB, interno, CONF, FASE, OUT, MOD

PESO_EM = 5.0
for l in LINEAS:
    em = cargar("emerging", l, CONF["clima"]); dv = cargar("developed", l, CONF["clima"])
    dv = dv[dv.year.isin(CONF["dev_years"])]
    h = np.array([int(hashlib.sha256(("t4|" + c).encode()).hexdigest()[:8], 16) / 2 ** 32 for c in dv.customer_id.values])
    dv = dv[h < 0.35].reset_index(drop=True)
    cols = comunes(l) + SOLO_EMERGENTE + ["market"]
    CATEGORICAS.add("market")
    cats = categorias_union([dv, em], cols)
    tr = em[(em.conjunto == "train") & em.year.isin(CONF["em_train"])].reset_index(drop=True)
    sets = [(tr[tr.fold != k], tr[tr.fold == k]) for k in range(5)] if CONF["em_eval"] is None else [(tr, em[em.year == CONF["em_eval"]].reset_index(drop=True))]
    Xd = matriz(dv, cols, cats); offd = np.log(dv.exposure.values * dv.c_fila.values)
    preds = []; rondas = []
    for a, b in sets:
        Xa = matriz(a, cols, cats); offa = np.log(a.exposure.values * a.c_fila.values)
        v = interno(a.customer_id.values)
        X = pd.concat([Xd, Xa[~v]], ignore_index=True)
        y = np.concatenate([dv.y.values, a.y.values[~v]]); off = np.concatenate([offd, offa[~v]])
        w = np.concatenate([np.ones(len(dv)), np.full((~v).sum(), PESO_EM)])
        p = dict(P_DEVB[l])
        dtr = lgb.Dataset(X, y, weight=w, init_score=off, free_raw_data=False)
        dva = lgb.Dataset(Xa[v], a.y.values[v], init_score=offa[v], reference=dtr)
        bst = lgb.train(p, dtr, 5000, valid_sets=[dva], callbacks=[lgb.early_stopping(150, verbose=False)])
        n = max(bst.best_iteration, 1); rondas.append(n)
        X2 = pd.concat([Xd, Xa], ignore_index=True)
        y2 = np.concatenate([dv.y.values, a.y.values]); off2 = np.concatenate([offd, offa])
        w2 = np.concatenate([np.ones(len(dv)), np.full(len(a), PESO_EM)])
        bst = lgb.train(p, lgb.Dataset(X2, y2, weight=w2, init_score=off2), n)
        kin = factor_tweedie(a.y.values, np.exp(bst.predict(Xa, raw_score=True) + offa))
        mu = kin * np.exp(bst.predict(matriz(b, cols, cats), raw_score=True)) * b.exposure.values
        preds.append(pd.DataFrame({"row_id": b.row_id.values, "mu": mu}))
        if CONF["em_eval"] is not None:
            (TRABAJO / "modelos" / FASE).mkdir(parents=True, exist_ok=True)
            bst.save_model(str(TRABAJO / "modelos" / FASE / f"T4_{l}.txt"))
    pd.concat(preds).to_parquet(OUT / f"T4_{l}.parquet", index=False)
    print(l, "rondas", rondas, flush=True)
