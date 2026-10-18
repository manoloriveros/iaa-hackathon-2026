"""Diagnóstico: ¿añade señal el clima del mismo año del periodo (realizado, disponible en los datos de 2025)?"""
import json, numpy as np, pandas as pd
from comun import BASE, LINES, WEATHER_VARS, d2, to_model_frame
from experimentos import features, fit, load, predict
cfg = json.load(open('/home/claude/work/cfg_total.json'))
w = pd.read_parquet(BASE / "Datos" / "weather.parquet").rename(columns={v: f"{v}_curr" for v in WEATHER_VARS})
out = {}
for line in LINES:
    df = load(line).merge(w, on=["address_id", "year"], how="left")
    base_feats = features(line, df, "F01234" if line == "motor" else "F0124")
    y = df["T0"].fillna(0).values; off = df["e_ef_coste"].values
    tr = df.year.isin([2021, 2022]).values; cal = ((df.year == 2023) & (df.cal_half == 0)).values; sel = ((df.year == 2023) & (df.cal_half == 1)).values
    for tag, feats in (("sin", base_feats), ("con_clima_actual", base_feats + [f"{v}_curr" for v in WEATHER_VARS])):
        X = to_model_frame(df, feats)
        b, base = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(cfg[line]["params"]))
        mu = predict(b, base, X[sel], off[sel], b.best_iteration)
        out.setdefault(line, {})[tag] = round(d2(y[sel], mu), 5)
        print(line, tag, out[line][tag], flush=True)
json.dump(out, open('/home/claude/work/clima_actual.json', 'w'), indent=1)
