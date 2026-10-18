"""Producción de la estructura frecuencia por peligro x severidad media (V24 de confirmación y 2025).

Para cada peligro: Poisson con offset e_ef_<peligro> y las rondas de V23 (x1,15 en V24 y x1,3 en producción); severidad
media del peligro en el entrenamiento de cada corte. Escribe WORK/<nombre>/prediccion_2025.parquet, v24.parquet y
resumen.json con el mismo formato que produccion.py, para mezclar después.
Uso: python3 produccion_frecsev.py <nombre> <eval_json_v23> <ramos> [--semillas=1]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from comun import PERILS, WORK, d2, to_model_frame
from experimentos import features, fit, load, predict


def main():
    name, eval_path, lines = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    seeds = int(next((a.split("=")[1] for a in sys.argv[4:] if a.startswith("--semillas=")), 1))
    ev = json.load(open(eval_path))
    cfg = json.load(open("/home/claude/work/cfg_total.json"))
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    preds, v24s, summary = [], [], {"lines": {}}
    for line in lines:
        t = time.time()
        df = load(line)
        feats = features(line, df, "F01234" if line == "motor" else "F0124")
        X = to_model_frame(df, feats)
        y = df["T0"].fillna(0).values
        tr24 = (df.year <= 2023).values; ev24 = (df.year == 2024).values
        trp = (df.year <= 2024).values; te = (df.year == 2025).values
        expo = df["exposure"].values
        mu24 = np.zeros(ev24.sum()); mu25 = np.zeros(te.sum())
        info = {}
        for p in PERILS[line]:
            n = df[f"n_{p}"].fillna(0).values.astype(float)
            yp = df[f"y_{p}"].fillna(0).values
            off = df[f"e_ef_{p}"].values
            r = int(ev[line][p]["best"])
            params = dict(cfg[line]["params"]); params.pop("cap", None); params.pop("tweedie_variance_power", None)
            params["objective"] = "poisson"
            sev24 = yp[tr24].sum() / max(n[tr24].sum(), 1.0)
            sevp = yp[trp].sum() / max(n[trp].sum(), 1.0)
            for s in range(seeds):
                ps = dict(params, seed=20261017 + 101 * s)
                b24, base24 = fit(X[tr24], n[tr24], off[tr24], rounds=int(round(r * 1.15)), early=None, params=dict(ps))
                mu24 += predict(b24, base24, X[ev24], off[ev24]) * sev24 / seeds
                bp, basep = fit(X[trp], n[trp], off[trp], rounds=int(round(r * 1.3)), early=None, params=dict(ps))
                mu25 += predict(bp, basep, X[te], expo[te]) * sevp / seeds
            info[p] = {"rounds_v24": int(round(r * 1.15)), "rounds_prod": int(round(r * 1.3)), "sev_v24": round(float(sev24), 2), "sev_prod": round(float(sevp), 2)}
            print(line, p, info[p], flush=True)
        summary["lines"][line] = {"d2_v24": round(d2(y[ev24], mu24), 5), "balance_v24": round(float(mu24.sum() / y[ev24].sum()), 4),
                                  "pred_2025_total_CU": round(float(mu25.sum()), 2), "perils": info, "secs": round(time.time() - t)}
        print(line, summary["lines"][line], flush=True)
        preds.append(pd.DataFrame({"row_id": df.row_id[te].astype(str).values, "line": line, "prediction": mu25}))
        v24s.append(pd.DataFrame({"row_id": df.row_id[ev24].astype(str).values, "line": line, "y": y[ev24], "mu": mu24}))
    pd.concat(preds, ignore_index=True).to_parquet(out / "prediccion_2025.parquet", index=False)
    pd.concat(v24s, ignore_index=True).to_parquet(out / "v24.parquet", index=False)
    (out / "resumen.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
