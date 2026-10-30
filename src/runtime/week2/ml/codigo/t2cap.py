"""E06: train developed T2 with line-specific positive-row p99.9 caps."""
import sys
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
from gbm import P_DEV, ajustar, CONF, MOD, OUT, FASE

for l in LINEAS:
    em = cargar("emerging", l, CONF["clima"]); dv = cargar("developed", l, CONF["clima"])
    dv = dv[dv.year.isin(CONF["dev_years"])].reset_index(drop=True)
    cols = comunes(l); cats = categorias_union([dv, em], cols + SOLO_EMERGENTE + MARKETING + TARIFA + MAKE)
    tope = float(np.quantile(dv.y[dv.y > 0], 0.999))
    f = MOD / f"T2cap_{l}.txt"
    Xd = matriz(dv, cols, cats); offd = np.log(dv.exposure.values * dv.c_fila.values)
    if f.exists():
        b = lgb.Booster(model_file=str(f)); n = b.current_iteration()
    else:
        b, n = ajustar(Xd, np.minimum(dv.y.values, tope), offd, P_DEV, 4000, es=100, val=dv.fold.values == 0)
        b.save_model(str(f))
    r = b.predict(matriz(em, cols, cats), raw_score=True)
    em["raw"] = r
    tr = em[(em.conjunto == "train") & em.year.isin(CONF["em_train"])].reset_index(drop=True)
    sets = [(tr[tr.fold != k], tr[tr.fold == k]) for k in range(5)] if CONF["em_eval"] is None else \
        [(tr, em[em.year == CONF["em_eval"]].reset_index(drop=True))]
    preds = []
    for a, bb in sets:
        k = factor_tweedie(a.y.values, np.exp(a.raw.values) * a.exposure.values * a.c_fila.values)
        preds.append(pd.DataFrame({"row_id": bb.row_id.values, "mu": k * np.exp(bb.raw.values) * bb.exposure.values}))
    pd.concat(preds).to_parquet(OUT / f"T2cap_{l}.parquet", index=False)
    pd.DataFrame({"row_id": em.row_id.values, "raw": r}).to_parquet(OUT / f"T2capraw_{l}.parquet", index=False)
    print(l, "tope", round(tope), "rondas", n, flush=True)
