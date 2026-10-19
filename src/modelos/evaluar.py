"""Evalúa una configuración por ramo en V23 (parada en la mitad de calibración, comparación en la de selección).

Modos: 'total' ajusta T0 del ramo con el offset e_ef_coste; 'componentes' ajusta un modelo por peligro con su etiqueta
y_<peligro> y su offset e_ef_<peligro>, y suma las predicciones. La configuración puede fijar 'cap' por ramo o por
peligro ('caps': {"bodily_injury": 15000}). Guarda las predicciones de selección para mezclas posteriores.
Uso: python3 evaluar.py <nombre> <conjunto> <config_json> <modo> [ramos]
La configuración admite "drop" y "add" (listas de columnas) por ramo.
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
    name, set_name, cfg_path, mode = sys.argv[1:5]
    cfg = json.loads(open(cfg_path).read())
    rep, ys, mus, frames = {}, [], [], []
    lines = sys.argv[5].split(",") if len(sys.argv) > 5 else LINES
    for line in lines:
        t = time.time()
        df = load(line)
        feats = [f for f in features(line, df, set_name) if f not in set(cfg[line].get("drop", []))]
        feats += [f for f in cfg[line].get("add", []) if f in df.columns and f not in feats]
        X = to_model_frame(df, feats)
        tr = df.year.isin([2021, 2022]).values
        cal = ((df.year == 2023) & (df.cal_half == 0)).values
        sel = ((df.year == 2023) & (df.cal_half == 1)).values
        y = df["T0"].fillna(0).values
        if mode == "total":
            off = df["e_ef_coste"].values
            b, base = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(cfg[line]["params"]))
            best = b.best_iteration or b.current_iteration()
            mu = predict(b, base, X[sel], off[sel], best)
            info = {"best": best}
        else:
            mu = np.zeros(sel.sum())
            info = {}
            for p in PERILS[line]:
                yp = df[f"y_{p}"].fillna(0).values
                op = df[f"e_ef_{p}"].values
                params = dict(cfg[line]["params"])
                params.pop("cap", None)
                c = cfg[line].get("caps", {}).get(p)
                if c:
                    params["cap"] = c
                b, base = fit(X[tr], yp[tr], op[tr], X[cal], yp[cal], op[cal], rounds=6000, early=200, params=params)
                best = b.best_iteration or b.current_iteration()
                mp = predict(b, base, X[sel], op[sel], best)
                info[p] = {"best": best, "d2": round(d2(yp[sel], mp), 5)}
                mu += mp
        rep[line] = {"d2_sel": round(d2(y[sel], mu), 5), "balance_sel": round(float(mu.sum() / y[sel].sum()), 4), "n_feats": len(feats), **info, "secs": round(time.time() - t)}
        print(name, line, rep[line], flush=True)
        ys.append(y[sel]); mus.append(mu)
        frames.append(pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu}))
    rep["global"] = round(d2(np.concatenate(ys), np.concatenate(mus)), 5)
    print("== ", name, "global sel", rep["global"], flush=True)
    pd.concat(frames, ignore_index=True).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    (WORK / f"eval_{name}.json").write_text(json.dumps(rep, indent=1, default=float))


if __name__ == "__main__":
    main()
