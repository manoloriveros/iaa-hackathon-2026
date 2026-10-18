"""¿Ayuda entrenar solo con los años recientes o ponderarlos más? V24 con LightGBM vigente por ramo.

Variantes: 2021-2023 (vigente), 2022-2023, y 2021-2023 con pesos por año (2021: 0,5; 2022: 0,75; 2023: 1).
Misma configuración y rondas de V23 x 1,15; una semilla; comparación pareada en 2024.
"""
from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np

from comun import d2, to_model_frame
from experimentos import PARAMS, features, load

cfg = json.load(open("/home/claude/work/cfg_total.json"))
RONDAS = {"motor": 595, "buildings": 350, "contents": 303}
for line in ["motor", "buildings", "contents"]:
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    ev = (df.year == 2024).values
    cap = cfg[line]["params"].get("cap")
    for tag, trm, wfun in (("2021_2023", (df.year <= 2023).values, None), ("2022_2023", df.year.isin([2022, 2023]).values, None),
                           ("pesos_recientes", (df.year <= 2023).values, {2021: 0.5, 2022: 0.75, 2023: 1.0})):
        p = dict(PARAMS, **cfg[line]["params"]); p.pop("cap", None)
        yt = np.minimum(y, cap) if cap else y
        loading = y[trm].sum() / yt[trm].sum() if cap else 1.0
        w = df.year.map(wfun).values[trm] if wfun else None
        base = float(np.log(np.average(yt[trm] / off[trm], weights=(w if w is not None else None) * off[trm] if w is not None else off[trm])))
        dtr = lgb.Dataset(X[trm], label=yt[trm], init_score=np.log(off[trm]) + base, weight=w)
        b = lgb.train(p, dtr, num_boost_round=int(RONDAS[line] * 1.15))
        mu = np.exp(b.predict(X[ev], raw_score=True) + base + np.log(off[ev])) * loading
        print(line, tag, "V24", round(d2(y[ev], mu), 5), flush=True)
