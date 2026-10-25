"""T5: adaptación GLM con ridge sobre las relatividades transferidas de T2 (E03).

log mu = raw_T2 + log(e c) + b0 + Z b, con penalización ridge sobre b (credibilidad).
Uso: python adaptacion.py fase
"""
from __future__ import annotations
import sys, hashlib
import numpy as np, pandas as pd
from scipy.optimize import minimize
from comun import *
from variables import cargar

FASE = sys.argv[1] if len(sys.argv) > 1 else "dev"
CONF = {"dev": ("hasta2023", [2023], None), "hold": ("hasta2023", [2023], 2024), "prod": ("hasta2024", [2023, 2024], 2025),
        "pcv": ("hasta2024", [2023, 2024], None)}[FASE]
OUT = TRABAJO / "pred" / FASE
FACT = ["region", "channel", "age_band", "gender", "occupation"]
LAMBDAS = [1e2, 1e3, 3e3, 1e4, 3e4, 1e5, 3e5, 1e6, 3e6, 1e7]


def diseno(df, niveles=None):
    cols = [df.new_business.astype(float).values[:, None], df.self_employed.fillna(False).astype(float).values[:, None]]
    nombres = ["new_business", "self_employed"]
    niv = {} if niveles is None else niveles
    for f in FACT:
        v = df[f].astype(object).where(df[f].notna(), "NA").astype(str).values
        if niveles is None:
            niv[f] = sorted(set(v))
        for n in niv[f]:
            cols.append((v == n).astype(float)[:, None]); nombres.append(f"{f}={n}")
    return np.hstack(cols), nombres, niv


def ajustar(Z, y, off, lam):
    n, k = Z.shape

    def f(beta):
        eta = off + beta[0] + Z @ beta[1:]
        a = np.exp(0.5 * eta); b = np.exp(-0.5 * eta)  # mu^(2-p), mu^(1-p) con p=1.5
        loss = np.sum(2 * (y * 2 * b + 2 * a)) + lam * np.sum(beta[1:] ** 2)  # constantes de y omitidas
        g_eta = 2 * (-y * b + a)
        grad = np.concatenate([[g_eta.sum()], Z.T @ g_eta + 2 * lam * beta[1:]])
        return loss, grad
    b0 = np.log(max(np.sum(y / np.sqrt(np.exp(off))) / np.sum(np.sqrt(np.exp(off))), 1e-9))
    x0 = np.zeros(k + 1); x0[0] = b0
    r = minimize(f, x0, jac=True, method="L-BFGS-B", options={"maxiter": 2000})
    return r.x


def interno(cids):
    return np.array([int(hashlib.sha256(("mlind_inner|" + c).encode()).hexdigest()[:8], 16) % 5 == 0 for c in cids])


coefs = {}
for l in LINEAS:
    em = cargar("emerging", l, CONF[0])
    raw = pd.read_parquet(OUT / f"T2raw_{l}.parquet")
    em = em.merge(raw, on="row_id")
    tr = em[(em.conjunto == "train") & em.year.isin(CONF[1])].reset_index(drop=True)
    sets = [(tr[tr.fold != k], tr[tr.fold == k]) for k in range(5)] if CONF[2] is None else [(tr, em[em.year == CONF[2]].reset_index(drop=True))]
    preds = []; lams = []
    for a, b in sets:
        Za, nom, niv = diseno(a); Zb, _, _ = diseno(b, niv)
        offa = a.raw.values + np.log(a.exposure.values * a.c_fila.values)
        offb = b.raw.values + np.log(b.exposure.values)
        ya = a.y.values
        v = interno(a.customer_id.values)
        best = None
        for lam in LAMBDAS:
            bt = ajustar(Za[~v], ya[~v], offa[~v], lam)
            mu = np.exp(offa[v] + bt[0] + Za[v] @ bt[1:])
            dev = desviacion(ya[v], mu).sum()
            if best is None or dev < best[0]:
                best = (dev, lam)
        lam = best[1]; lams.append(lam)
        bt = ajustar(Za, ya, offa, lam)
        preds.append(pd.DataFrame({"row_id": b.row_id.values, "mu": np.exp(offb + bt[0] + Zb @ bt[1:])}))
        coefs.setdefault(l, []).append({"lambda": lam, "b0": bt[0], **dict(zip(nom, bt[1:]))})
    pd.concat(preds).to_parquet(OUT / f"T5_{l}.parquet", index=False)
    print(l, "lambdas", lams, "b_NB", [round(c["new_business"], 3) for c in coefs[l]])
guardar_json(coefs, OUT / "T5_coeficientes.json")
