"""Experimentos LightGBM Tweedie por ramo con offset de exposición efectiva (T0 a nivel último, D67/D70).

V23: entrena 2021-2022, parada temprana en la mitad de calibración de 2023 (cal_half = 0) y comparación en la mitad de
selección (cal_half = 1). V24: entrena 2021-2023 con las rondas fijadas en V23 y evalúa 2024 (consulta registrada).
El D² se calcula sobre importes con potencia 1,5, global (tres ramos concatenados) y por ramo.

Uso: python3 experimentos.py <nombre_salida> <conjunto>[,<conjunto>...] [--v24]
Conjuntos: M00, F0, F012, F0124, F01234 (diagnóstico con F3 sin marketing_segment), F01234m (con marketing_segment)
"""
from __future__ import annotations

import json
import sys
import time

import lightgbm as lgb
import numpy as np
import pandas as pd

from comun import F0DIR, LINES, WORK, blocks_for, d2, to_model_frame

PARAMS = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.05, num_leaves=31, min_data_in_leaf=500,
              feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, max_bin=255, num_threads=2,
              verbose=-1, boost_from_average=False, cat_smooth=50, min_data_per_group=200, max_cat_to_onehot=8, seed=20261017)
SETS = {"F0": ["F0"], "F012": ["F0", "F1", "F2"], "F0124": ["F0", "F1", "F2", "F4"], "F01234": ["F0", "F1", "F2", "F3", "F4"], "F01234m": ["F0", "F1", "F2", "F3", "F4"]}
ALWAYS_OUT = {"marketing_segment"}


def load(line):
    df = pd.read_parquet(WORK / f"feat_{line}.parquet")
    part = pd.read_parquet(F0DIR / "tables" / "particiones.parquet", columns=["row_id", "cal_half"])
    df = df.merge(part, on="row_id", how="left", validate="one_to_one")
    return df


def features(line, df, set_name):
    blocks = blocks_for(line, df)
    keep = SETS[set_name]
    feats = [c for c, b in blocks.items() if b in keep]
    if set_name != "F01234m":
        feats = [c for c in feats if c not in ALWAYS_OUT]
    return feats


def fit(X, y, off, Xv=None, yv=None, offv=None, rounds=4000, early=150, params=None):
    """Ajusta LightGBM Tweedie con offset log(exposición). Con 'cap' en params, la etiqueta de entrenamiento se acota por
    fila y el exceso se devuelve como recargo uniforme (booster.loading); la evaluación siempre usa la etiqueta completa."""
    params = dict(PARAMS, **(params or {}))
    cap = params.pop("cap", None)
    loading = 1.0
    if cap:
        yc = np.minimum(y, cap)
        loading = float(y.sum() / yc.sum())
        y = yc
        if yv is not None:
            yv = np.minimum(yv, cap)
    base = float(np.log(y.sum() / off.sum()))
    dtr = lgb.Dataset(X, label=y, init_score=np.log(off) + base, free_raw_data=False)
    valid = []
    if Xv is not None:
        valid = [lgb.Dataset(Xv, label=yv, init_score=np.log(offv) + base, reference=dtr)]
    cb = [lgb.early_stopping(early, verbose=False)] if (Xv is not None and early) else []
    booster = lgb.train(params, dtr, num_boost_round=rounds, valid_sets=valid, callbacks=cb)
    booster.loading = loading
    return booster, base


def predict(booster, base, X, off, iters=None):
    raw = booster.predict(X, raw_score=True, num_iteration=iters)
    return np.exp(raw + base + np.log(off)) * getattr(booster, "loading", 1.0)


def main():
    out_name = sys.argv[1]
    sets = sys.argv[2].split(",")
    do_v24 = "--v24" in sys.argv
    extra = {}
    for a in sys.argv[3:]:
        if a.startswith("--param="):
            k, v = a[len("--param="):].split(":", 1)
            extra[k] = float(v) if v.replace(".", "", 1).replace("-", "", 1).isdigit() else v
    results = {"params": dict(PARAMS, **extra), "sets": {}}
    for set_name in sets:
        sel_y, sel_mu, v24_y, v24_mu = [], [], [], []
        per_line = {}
        for line in LINES:
            t = time.time()
            df = load(line)
            tr = df.year.isin([2021, 2022]).values
            cal = ((df.year == 2023) & (df.cal_half == 0)).values
            sel = ((df.year == 2023) & (df.cal_half == 1)).values
            y = df["T0"].fillna(0).values
            off = df["e_ef_coste"].values
            if set_name == "M00":
                rate = y[tr].sum() / off[tr].sum()
                mu_sel = rate * off[sel]
                best = 0
                info = {"rate": rate}
                if do_v24:
                    tr24 = (df.year <= 2023).values
                    ev24 = (df.year == 2024).values
                    mu24 = y[tr24].sum() / off[tr24].sum() * off[ev24]
            else:
                feats = features(line, df, set_name)
                X = to_model_frame(df, feats)
                booster, base = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], params=extra)
                best = booster.best_iteration or booster.current_iteration()
                mu_sel = predict(booster, base, X[sel], off[sel], best)
                imp = pd.Series(booster.feature_importance("gain"), index=feats).sort_values(ascending=False)
                info = {"best_iter": best, "n_feats": len(feats), "top_gain": {k: round(float(v / imp.sum()), 4) for k, v in imp.head(15).items()}}
                if do_v24:
                    tr24 = (df.year <= 2023).values
                    ev24 = (df.year == 2024).values
                    b24, base24 = fit(X[tr24], y[tr24], off[tr24], rounds=int(round(best * 1.1)) or 100, early=None, params=extra)
                    mu24 = predict(b24, base24, X[ev24], off[ev24])
            per_line[line] = {"d2_sel": round(d2(y[sel], mu_sel), 5), "balance_sel": round(float(mu_sel.sum() / y[sel].sum()), 4), **info, "secs": round(time.time() - t)}
            sel_y.append(y[sel]); sel_mu.append(mu_sel)
            if do_v24:
                per_line[line]["d2_v24"] = round(d2(y[ev24], mu24), 5)
                per_line[line]["balance_v24"] = round(float(mu24.sum() / y[ev24].sum()), 4)
                v24_y.append(y[ev24]); v24_mu.append(mu24)
            print(set_name, line, per_line[line], flush=True)
        res = {"d2_sel_global": round(d2(np.concatenate(sel_y), np.concatenate(sel_mu)), 5), "lines": per_line}
        if do_v24:
            res["d2_v24_global"] = round(d2(np.concatenate(v24_y), np.concatenate(v24_mu)), 5)
        results["sets"][set_name] = res
        print("== ", set_name, "global sel", res["d2_sel_global"], "v24", res.get("d2_v24_global"), flush=True)
        (WORK / f"exp_{out_name}.json").write_text(json.dumps(results, indent=1, default=float))


if __name__ == "__main__":
    main()
