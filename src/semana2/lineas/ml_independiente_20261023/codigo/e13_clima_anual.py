"""E13: T2b con el clima del propio año de la póliza (exploratorio)."""
import numpy as np, pandas as pd, lightgbm as lgb
from comun import *
from variables import *
from gbm import P_DEVB
RONDAS = {"motor": 249, "buildings": 194, "contents": 169}
VARS = ["hail_days", "wind_exposure_index", "freezing_days", "dry_summer_index", "wildfire_index", "rainfall_mm", "mean_temperature_c"]
w = {m: pd.read_parquet(DATOS / m / "weather.parquet").rename(columns={v: "w_" + v for v in VARS}) for m in ["developed", "emerging"]}
for l in LINEAS:
    em = cargar("emerging", l, "hasta2023"); dv = cargar("developed", l, "hasta2023")
    dv = dv[dv.year.isin([2021, 2022, 2023])].reset_index(drop=True)
    dv = dv.merge(w["developed"], left_on=["address_id", "year"], right_on=["address_id", "year"], how="left")
    em = em.merge(w["emerging"], left_on=["address_id", "year"], right_on=["address_id", "year"], how="left")
    cols = [c for c in comunes(l) if not c.startswith("clima_")] + ["w_" + v for v in VARS]
    cats = categorias_union([dv, em], cols)
    off = np.log(dv.exposure.values * dv.c_fila.values)
    b = lgb.train(P_DEVB[l], lgb.Dataset(matriz(dv, cols, cats), dv.y.values, init_score=off), RONDAS[l])
    em["raw"] = b.predict(matriz(em, cols, cats), raw_score=True)
    tr = em[(em.conjunto == "train") & (em.year == 2023)].reset_index(drop=True)
    for fase, sets in [("dev", [(tr[tr.fold != k], tr[tr.fold == k]) for k in range(5)]), ("hold", [(tr, em[em.year == 2024].reset_index(drop=True))])]:
        preds = []
        for a, bb in sets:
            k = factor_tweedie(a.y.values, np.exp(a.raw.values) * a.exposure.values * a.c_fila.values)
            preds.append(pd.DataFrame({"row_id": bb.row_id.values, "mu": k * np.exp(bb.raw.values) * bb.exposure.values}))
        pd.concat(preds).to_parquet(TRABAJO / "pred" / fase / f"T2bclima_{l}.parquet", index=False)
    imp = pd.Series(b.feature_importance("gain"), index=cols); imp = imp / imp.sum()
    print(l, "ganancia clima del año", round(float(imp[[c for c in cols if c.startswith("w_")]].sum()), 3), flush=True)
