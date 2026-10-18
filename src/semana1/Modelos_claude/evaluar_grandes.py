"""Autos: base acotada + modelo de propensión a siniestros grandes, frente al recargo uniforme.

Base: Tweedie sobre T0 acotado por fila al tope (sin recargo). Grandes: Poisson sobre el número de siniestros
positivos con coste neto por encima del tope, con offset e_ef_bodily_injury (los grandes son casi todos lesiones, de
reporte lento), por el exceso medio por siniestro grande del entrenamiento. mu = base + lambda_grandes * exceso_medio.
Se compara en la mitad de selección de V23 con el recargo uniforme. Uso: python3 evaluar_grandes.py <nombre> <tope>
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import BASESDIR, WORK, d2, to_model_frame
from experimentos import features, fit, load, predict


def main():
    name, cap = sys.argv[1], float(sys.argv[2])
    cfg = json.load(open("/home/claude/work/cfg_total.json"))["motor"]["params"]
    df = load("motor")
    feats = features("motor", df, "F01234")
    X = to_model_frame(df, feats)
    tr = df.year.isin([2021, 2022]).values
    cal = ((df.year == 2023) & (df.cal_half == 0)).values
    sel = ((df.year == 2023) & (df.cal_half == 1)).values
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    # número de siniestros grandes y exceso por fila, a partir de la asignación D67 y el coste neto por siniestro
    a = pd.read_parquet(BASESDIR / "tables" / "asignacion_por_siniestro.parquet", columns=["claim_id", "row_id", "line", "category"])
    claims = pd.read_parquet("/home/claude/work/claims_net_motor.parquet") if (WORK / "claims_net_motor.parquet").exists() else None
    if claims is None:
        raise SystemExit("falta claims_net_motor.parquet")
    big = claims[claims.net > cap].groupby("row_id").agg(n_big=("net", "size"), exc=("net", lambda s: float((s - cap).sum())))
    df["n_big"] = df.row_id.astype(str).map(big.n_big).fillna(0).values
    df["exc_big"] = df.row_id.astype(str).map(big.exc).fillna(0).values
    n_big = df["n_big"].values
    mean_exc = df.loc[tr, "exc_big"].sum() / max(df.loc[tr, "n_big"].sum(), 1)
    p = dict(cfg)
    p.pop("cap", None)
    # base acotada sin recargo
    yc = np.minimum(y, cap)
    b0, base0 = fit(X[tr], yc[tr], off[tr], X[cal], yc[cal], off[cal], rounds=6000, early=200, params=dict(p))
    mu0 = predict(b0, base0, X[sel], off[sel], b0.best_iteration)
    loading = y[tr].sum() / yc[tr].sum()
    # propensión a grandes
    pg = dict(p, objective="poisson")
    pg.pop("tweedie_variance_power", None)
    offb = df["e_ef_bodily_injury"].values
    b1, base1 = fit(X[tr], n_big[tr], offb[tr], X[cal], n_big[cal], offb[cal], rounds=6000, early=200, params=pg)
    lam = predict(b1, base1, X[sel], offb[sel], b1.best_iteration)
    res = {"cap": cap, "mean_excess": round(float(mean_exc), 2), "uniform_loading": round(float(loading), 4),
           "d2_sel_recargo_uniforme": round(d2(y[sel], mu0 * loading), 5),
           "d2_sel_base_mas_grandes": round(d2(y[sel], mu0 + lam * mean_exc), 5),
           "best_base": b0.best_iteration, "best_grandes": b1.best_iteration,
           "n_big_train": int(n_big[tr].sum()), "balance_uniforme": round(float((mu0 * loading).sum() / y[sel].sum()), 4),
           "balance_grandes": round(float((mu0 + lam * mean_exc).sum() / y[sel].sum()), 4)}
    print(res, flush=True)
    pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "y": y[sel], "mu_uniforme": mu0 * loading, "mu_grandes": mu0 + lam * mean_exc}).to_parquet(WORK / f"sel_{name}.parquet", index=False)


if __name__ == "__main__":
    main()
