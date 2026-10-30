"""Apply convex line blends, C1/C2 calibration and optional trend.
parametros estimates weights/factors on DEV for HOLD or PCV for production.
aplicar generates the target phase's predictions from those fixed parameters.
"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from comun import *
from evaluar import tabla_eval, cargar_pred, mezcla_pesos, mezcla_cruzada, calibrar_cruzado, metricas, bootstrap_dif

K_NB = 200.0


def tabla(fase):
    if fase == "dev":
        t = tabla_eval("dev", 2023)
    elif fase == "hold":
        t = tabla_eval("hold", 2024)
    elif fase == "pcv":
        t = pd.concat([tabla_eval("dev", 2023), tabla_eval("dev", 2024)], ignore_index=True)
    else:  # Production uses test rows.
        filas = []
        for l in LINEAS:
            b = pd.read_parquet(TRABAJO / f"base_emerging_{l}.parquet",
                                columns=["row_id", "y", "c_fila", "exposure", "customer_id", "year", "new_business", "conjunto"])
            filas.append(b[b.conjunto == "test"].assign(line=l))
        t = pd.concat(filas, ignore_index=True)
    return t.reset_index(drop=True)


def componentes(fase, comps, t):
    out = {}
    for c in comps:
        p = cargar_pred(fase, c)
        if p is None:
            raise FileNotFoundError(f"{fase}/{c}")
        mu = t[["row_id"]].merge(p, on="row_id", how="left").mu.values
        if np.isnan(mu).any():
            raise ValueError(f"faltan filas en {fase}/{c}")
        out[c] = mu
    return out


def parametros(fase_oof, comps, calib="ramo_nb"):
    t = tabla(fase_oof)
    P = componentes(fase_oof, comps, t)
    y = t.y.values; res = {"componentes": comps, "calib": calib, "ramos": {}}
    for l in LINEAS:
        il = (t.line == l).values
        M = np.column_stack([P[c][il] * t.c_fila.values[il] for c in comps])
        w = mezcla_pesos(y[il], M)
        m = M @ w
        kl = factor_tweedie(y[il], m)
        r = {"pesos": dict(zip(comps, w.round(6).tolist())), "k_ramo": kl, "k_nb": {}}
        for nb in (True, False):
            s = t.new_business.values[il] == nb
            ks = factor_tweedie(y[il][s], m[s] * kl); n = int((y[il][s] > 0).sum()); z = n / (n + K_NB)
            r["k_nb"][str(nb)] = {"k_seg": ks, "n_sin": n, "Z": z, "factor": kl * (z * ks + 1 - z)}
        res["ramos"][l] = r
    return res


def aplicar(fase, params, tend=None):
    t = tabla(fase)
    comps = params["componentes"]; P = componentes(fase, comps, t)
    mu = np.zeros(len(t))
    for l in LINEAS:
        il = (t.line == l).values; r = params["ramos"][l]
        U = np.column_stack([P[c][il] for c in comps]); w = np.array([r["pesos"][c] for c in comps])
        base = U @ w
        if params["calib"] == "ramo":
            f = np.full(il.sum(), r["k_ramo"])
        else:
            nb = t.new_business.values[il]
            f = np.where(nb, r["k_nb"]["True"]["factor"], r["k_nb"]["False"]["factor"])
        tf = 1.0 if tend is None else tend[l]["factor"]
        mu[il] = base * f * tf
    return t, mu


def oof_cruzado(fase, comps, calib="ramo_nb"):
    """Generate DEV/PCV OOF predictions with fold-crossed blend weights and calibration."""
    t = tabla(fase); P = componentes(fase, comps, t)
    folds = pliegue(t.customer_id.values)
    if len(comps) > 1:
        mu, pesos = mezcla_cruzada(t, P, folds)
    else:
        mu, pesos = P[comps[0]], []
    mu = calibrar_cruzado(t, mu, folds, por_nb=(calib == "ramo_nb"), K=K_NB) if calib != "sin" else mu
    return t, mu, pesos
