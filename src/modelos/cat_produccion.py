"""CatBoost Tweedie de producción para un ramo: V24 (entrena 2021-2023, evalúa 2024) y 2025 (entrena 2021-2024).

Mismo contrato que cat_experimento.py: offset log(e_ef_coste), tope y recargo uniforme en autos, F3 solo en autos.
Iteraciones = mejor iteración de V23 x 1,15 (V24) y x 1,3 (producción). Escribe WORK/<nombre>/v24.parquet,
prediccion_2025.parquet y resumen.json, con el formato de produccion.py.
Uso: python3 cat_produccion.py <nombre> <ramo> <iter_v23> [--semillas=2] [--semilla_inicial=0] [--depth=6] [--lr=0.05] [--drop=a,b]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from cat_experimento import CAPS, frame
from comun import WORK, d2
from experimentos import features, load


def main():
    name, line, it = sys.argv[1], sys.argv[2], int(sys.argv[3])
    opts = dict(a[2:].split("=", 1) for a in sys.argv[4:] if a.startswith("--"))
    seeds, depth, lr = int(opts.get("semillas", 2)), int(opts.get("depth", 6)), float(opts.get("lr", 0.05))
    s0 = int(opts.get("semilla_inicial", 0))  # para añadir semillas nuevas a una corrida previa sin repetir las ya usadas
    drop = set(opts["drop"].split(",")) if opts.get("drop") else set()
    t = time.time()
    df = load(line)
    feats = [f for f in features(line, df, "F01234" if line == "motor" else "F0124") if f not in drop]
    X, cats = frame(df, feats)
    for c in cats:  # categorías compactas en lugar de cadenas de Python: misma información, mucha menos memoria
        X[c] = X[c].astype("category")
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    expo = df["exposure"].values
    years = df["year"].values
    row_ids = df["row_id"].astype(str).values
    del df
    import gc
    gc.collect()
    cap = CAPS.get(line)
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    res = {"line": line, "iter_v23": it, "seeds": seeds, "depth": depth, "lr": lr, "drop": sorted(drop)}
    tasks = (("v24", years <= 2023, years == 2024, off, 1.15), ("2025", years <= 2024, years == 2025, expo, 1.3))
    if opts.get("solo2025"):
        tasks = tasks[1:]
    for tag, trm, evm, offe, mult in tasks:
        yt = np.minimum(y, cap) if cap else y
        loading = y[trm].sum() / yt[trm].sum() if cap else 1.0
        base = float(np.log(yt[trm].sum() / off[trm].sum()))
        ptr = Pool(X[trm], yt[trm], cat_features=cats, baseline=np.log(off[trm]) + base)
        pev = Pool(X[evm], cat_features=cats)
        mu = np.zeros(evm.sum())
        for s in range(s0, s0 + seeds):
            m = CatBoostRegressor(loss_function="Tweedie:variance_power=1.5", iterations=int(round(it * mult)), learning_rate=lr, depth=depth,
                                  l2_leaf_reg=10, thread_count=2, random_seed=20261017 + 101 * s, verbose=0, boost_from_average=False, one_hot_max_size=8)
            m.fit(ptr)
            mu += np.exp(m.predict(pev, prediction_type="RawFormulaVal") + np.log(offe[evm]) + base) * loading / seeds
        if tag == "v24":
            res["d2_v24"] = round(d2(y[evm], mu), 5)
            res["balance_v24"] = round(float(mu.sum() / y[evm].sum()), 4)
            pd.DataFrame({"row_id": row_ids[evm], "line": line, "y": y[evm], "mu": mu}).to_parquet(out / "v24.parquet", index=False)
        else:
            res["pred_2025_total_CU"] = round(float(mu.sum()), 2)
            pd.DataFrame({"row_id": row_ids[evm], "line": line, "prediction": mu}).to_parquet(out / "prediccion_2025.parquet", index=False)
        print(tag, res, flush=True)
    res["secs"] = round(time.time() - t)
    prev = json.loads((out / "resumen.json").read_text()) if (out / "resumen.json").exists() else {}
    (out / "resumen.json").write_text(json.dumps(prev | res, indent=1))


if __name__ == "__main__":
    main()
