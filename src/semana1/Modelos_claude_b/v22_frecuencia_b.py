"""Corte V22 de frecuencia por peligro: modelo entrenado solo con 2021, parada temprana en una mitad de 2022 y cociente
observado/esperado en la otra mitad, para las dos familias de partes de la mezcla (CatBoost Poisson de cat_frecsev.py y
LightGBM aditivo de frecsev2.py --aditivo), con sus mismas variables, offset y parámetros.

Sirve para dar al corte V23 un factor de deriva de frecuencia fuera de muestra (r22) con la misma lógica que V24 usa r23
y 2025 usa r23 y r24 (frecuencia_tendencia_b.py). La mitad de 2022 se parte por paridad del hash del cliente (semilla
fija), como cal_half parte 2023 en la matriz F0.
Escribe experimentos/frec_v22_<ramo>.json. Uso: python3 v22_frecuencia_b.py <ramo> [--familias=cat,aditivo] [--peligros=p1,p2]
"""
from __future__ import annotations

import hashlib
import json
import os as _os
import sys
import time
from pathlib import Path as _Path

import numpy as np
import pandas as pd

_MC = _os.environ.get("MODELOS_CLAUDE") or next((str(p) for p in (_Path(__file__).resolve().parent.parent / "Modelos_claude", _Path("/home/claude/mc")) if p.exists()), "/home/claude/mc")
sys.path.insert(0, _MC)
sys.path.insert(0, str(_Path(__file__).resolve().parent))
from cat_experimento import frame  # noqa: E402
from cat_frecsev import F3S2  # noqa: E402
from comun import PERILS, WORK, to_model_frame  # noqa: E402
from experimentos import features, fit, load, predict  # noqa: E402

EXP = _Path(__file__).resolve().parent / "experimentos"


def main():
    line = sys.argv[1]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[2:] if a.startswith("--"))
    familias = opts.get("familias", "cat,aditivo").split(",")
    perils = opts.get("peligros", ",".join(PERILS[line])).split(",")
    t0 = time.time()
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    if line != "motor":
        feats += [c for c in F3S2 if c in df.columns and c not in feats]
    yr = df.year.values
    h = np.array([int(hashlib.md5(f"v22-{c}".encode()).hexdigest()[-4:], 16) % 2 for c in df.customer_id.astype(str).values])
    tr, cal, sel = yr == 2021, (yr == 2022) & (h == 0), (yr == 2022) & (h == 1)
    out_path = EXP / f"frec_v22_{line}.json"
    rep = json.loads(out_path.read_text()) if out_path.exists() else {"line": line, "filas": {"2021": int(tr.sum()), "2022_cal": int(cal.sum()), "2022_sel": int(sel.sum())}}
    if "aditivo" in familias:
        cfg = json.load(open(WORK / "cfg_total.json"))[line]["params"]
        pf = dict(cfg); pf.pop("cap", None); pf["objective"] = "poisson"; pf.pop("tweedie_variance_power", None)
        pf.update({"num_leaves": 2, "learning_rate": 0.05, "min_data_in_leaf": 2000})
        X = to_model_frame(df, feats)
        rep.setdefault("aditivo", {})
        for p in perils:
            n = df[f"n_{p}"].fillna(0).values.astype(float); off = df[f"e_ef_{p}"].values
            b, base = fit(X[tr], n[tr], off[tr], X[cal], n[cal], off[cal], rounds=6000, early=200, params=dict(pf))
            bf = b.best_iteration or b.current_iteration()
            lam = predict(b, base, X[sel], off[sel], bf)
            rep["aditivo"][p] = {"best": int(bf), "observados": int(n[sel].sum()), "esperados": round(float(lam.sum()), 1), "cociente": round(float(n[sel].sum() / lam.sum()), 4)}
            print("aditivo", p, rep["aditivo"][p], round(time.time() - t0), flush=True)
            out_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
        del X
    if "cat" in familias:
        from catboost import CatBoostRegressor, Pool
        X, cats = frame(df, feats)
        for c in X.columns:
            if c in cats:
                X[c] = X[c].astype("category")
            elif X[c].dtype == "float64":
                X[c] = X[c].astype("float32")
        rep.setdefault("cat", {})
        for p in perils:
            n = df[f"n_{p}"].fillna(0).values.astype(float); off = df[f"e_ef_{p}"].values
            base = float(np.log(n[tr].sum() / off[tr].sum()))
            m = CatBoostRegressor(loss_function="Poisson", iterations=3000, learning_rate=0.05, depth=6, l2_leaf_reg=10, od_type="Iter", od_wait=150,
                                  thread_count=2, random_seed=20261017, verbose=0, boost_from_average=False, one_hot_max_size=8, use_best_model=True)
            m.fit(Pool(X[tr], n[tr], cat_features=cats, baseline=np.log(off[tr]) + base),
                  eval_set=Pool(X[cal], n[cal], cat_features=cats, baseline=np.log(off[cal]) + base))
            lam = np.exp(m.predict(Pool(X[sel], cat_features=cats), prediction_type="RawFormulaVal") + np.log(off[sel]) + base)
            rep["cat"][p] = {"best": int(m.get_best_iteration()) + 1, "observados": int(n[sel].sum()), "esperados": round(float(lam.sum()), 1), "cociente": round(float(n[sel].sum() / lam.sum()), 4)}
            print("cat", p, rep["cat"][p], round(time.time() - t0), flush=True)
            out_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
