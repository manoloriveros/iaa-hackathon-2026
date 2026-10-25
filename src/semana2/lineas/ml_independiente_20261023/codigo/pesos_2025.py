"""W01: pesos de razón de densidad (2023 DEV frente a test 2025) para el D2 ponderado a la mezcla de 2025."""
import sys
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *

ANIO = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
CLIMA = "hasta2023"
resumen = {}
salida = []
for l in LINEAS:
    em = cargar("emerging", l, CLIMA)
    cols = [c for c in comunes(l) + SOLO_EMERGENTE if c not in ("hist_pol_12m", "hist_cli_12m")]
    a = em[(em.conjunto == "train") & (em.year == ANIO)]
    b = em[em.conjunto == "test"]
    d = pd.concat([a.assign(z=0), b.assign(z=1)], ignore_index=True)
    cats = categorias_union([d], cols)
    X = matriz(d, cols, cats); z = d.z.values
    fo = pliegue(d.customer_id.values)
    p = np.zeros(len(d))
    params = dict(objective="binary", learning_rate=0.05, num_leaves=31, min_data_in_leaf=200, feature_fraction=0.8,
                  bagging_fraction=0.8, bagging_freq=1, verbose=-1, num_threads=2, seed=7)
    for k in range(5):
        m = lgb.train(params, lgb.Dataset(X[fo != k], z[fo != k]), 300)
        p[fo == k] = m.predict(X[fo == k])
    from sklearn.metrics import roc_auc_score
    auc = roc_auc_score(z, p)
    imp = pd.Series(m.feature_importance("gain"), index=cols).sort_values(ascending=False)
    pa = np.clip(p[z == 0], 1e-6, 1 - 1e-6)
    w = pa / (1 - pa) * (len(a) / len(b))
    w = np.clip(w, 0.1, 10); w = w / w.mean()
    ess = w.sum() ** 2 / (w ** 2).sum()
    resumen[l] = {"auc": round(float(auc), 4), "n_dev": int(len(a)), "n_test": int(len(b)), "ess": round(float(ess), 1),
                  "nb_dev": round(float(a.new_business.mean()), 4),
                  "nb_ponderado": round(float(np.average(a.new_business, weights=w)), 4),
                  "nb_test": round(float(b.new_business.mean()), 4),
                  "importancia_top": {k: round(float(v / imp.sum()), 4) for k, v in imp.head(8).items()}}
    salida.append(pd.DataFrame({"row_id": a.row_id.values, "w2025": w}))
    print(l, resumen[l])
suf = "dev" if ANIO == 2023 else "hold"
pd.concat(salida).to_parquet(TRABAJO / f"pesos_2025_{suf}.parquet", index=False)
guardar_json(resumen, TRABAJO / f"pesos_2025_{suf}.json")
