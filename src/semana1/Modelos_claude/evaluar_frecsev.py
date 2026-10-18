"""Frecuencia por peligro (LightGBM Poisson con offset de exposición efectiva del peligro) por severidad media del peligro.

mu = sum_p lambda_p(x) * e_ef_p * s_p, con s_p = coste positivo / número de siniestros positivos del peligro en el
entrenamiento (sin tope, así el nivel conserva los siniestros grandes). Se evalúa en V23 como evaluar.py y se guardan las
predicciones de la mitad de selección para mezclar con el Tweedie total.
Uso: python3 evaluar_frecsev.py <nombre> <conjunto_autos> <conjunto_hogar> <config_json> [ramos]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from comun import LINES, PERILS, WORK, d2, to_model_frame
from experimentos import features, fit, load, predict


def main():
    name, set_motor, set_home, cfg_path = sys.argv[1:5]
    lines = sys.argv[5].split(",") if len(sys.argv) > 5 else LINES
    cfg = json.loads(open(cfg_path).read())
    rep, frames = {}, []
    for line in lines:
        t = time.time()
        df = load(line)
        set_name = set_motor if line == "motor" else set_home
        feats = features(line, df, set_name)
        X = to_model_frame(df, feats)
        tr = df.year.isin([2021, 2022]).values
        cal = ((df.year == 2023) & (df.cal_half == 0)).values
        sel = ((df.year == 2023) & (df.cal_half == 1)).values
        y = df["T0"].fillna(0).values
        mu = np.zeros(sel.sum())
        info = {}
        for p in PERILS[line]:
            n = df[f"n_{p}"].fillna(0).values.astype(float)
            yp = df[f"y_{p}"].fillna(0).values
            off = df[f"e_ef_{p}"].values
            sev = yp[tr].sum() / max(n[tr].sum(), 1.0)
            params = dict(cfg[line]["params"])
            params.pop("cap", None)
            params.update({"objective": "poisson"})
            params.pop("tweedie_variance_power", None)
            b, base = fit(X[tr], n[tr], off[tr], X[cal], n[cal], off[cal], rounds=6000, early=200, params=params)
            best = b.best_iteration or b.current_iteration()
            lam = predict(b, base, X[sel], off[sel], best)
            mu += lam * sev
            info[p] = {"best": best, "sev": round(float(sev), 2), "d2_coste_peligro": round(d2(yp[sel], lam * sev), 5)}
        rep[line] = {"d2_sel": round(d2(y[sel], mu), 5), "balance_sel": round(float(mu.sum() / y[sel].sum()), 4), **info, "secs": round(time.time() - t)}
        print(name, line, rep[line], flush=True)
        frames.append(pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu}))
    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(WORK / f"sel_{name}.parquet", index=False)
    if len(lines) == 3:
        rep["global"] = round(d2(out.y, out.mu), 5)
        print("== ", name, "global", rep["global"], flush=True)
    (WORK / f"eval_{name}.json").write_text(json.dumps(rep, indent=1, default=float))


if __name__ == "__main__":
    main()
