"""Calibración de la proyección analítica (tarea 7): en los años locales, compara la ganancia observada fuera de
tiempo con la esperada analíticamente cuando la verdad es (a) el factor creíble K=300 agrupado 2023+2024 o
(b) el EMV agrupado. Además: media del nulo de permutación por dirección (costo esperado de una variable ruido)."""
import sys, json
sys.path.insert(0, "/home/claude/m017/revision")
import numpy as np, pandas as pd
from I_lib import *

OUT = "/home/claude/m017/revision"
df = cargar()
cl = pd.read_parquet(f"{DE}/claims.parquet")
cl = cl[cl.status != "repudiated"]
cl = cl.assign(neto=cl.incurred_to_date - cl.recoveries)
SEV = {l: g.neto.values[g.neto.values > 0] for l, g in cl.groupby("line")}


def fit_seq(d, seq, K):
    y, m = d.y.values, d.m.values
    cy = (d.new_business.values.astype(int) * 2 + (d.year.values == 2024)).astype(int)
    w = np.ones(len(y))
    ml = nivel(y, m, cy, w, C=4)
    out = {}
    for v in seq:
        cd, uni = pd.factorize(d[v])
        if K > 0:
            f = ajusta(y, ml, cd, len(uni), K, w)
        else:
            a = np.bincount(cd, y / np.sqrt(ml), len(uni)); bb = np.bincount(cd, np.sqrt(ml), len(uni)); f = a / bb
        out[v] = dict(zip(uni, f))
        ml = nivel(y, ml * f[cd], cy, w, C=4)
    return out


def prod(t, fac, seq):
    f = np.ones(len(t))
    for v in seq:
        f *= t[v].map(fac[v]).fillna(1.0).values
    return f


res = {}
for l, seq in VARS.items():
    d = df[df.line == l].reset_index(drop=True)
    tru = {"K300_agrupado": fit_seq(d, seq, 300), "EMV_agrupado": fit_seq(d, seq, 0)}
    for tr, te in ((2023, 2024), (2024, 2023)):
        A, B = d[d.year == tr], d[d.year == te].reset_index(drop=True)
        cell = B.new_business.values.astype(int)
        fa = fit_seq(A.assign(year=2023), seq, 300)
        f = prod(B, fa, seq)
        m = nivel(B.y.values, B.m.values, cell, np.ones(len(B)))
        m1 = nivel(B.y.values, m * f, cell, np.ones(len(B)))
        obs = (np.sum(dev(B.y.values, m)) - np.sum(dev(B.y.values, m1)))
        null = np.sum(dev(B.y.values, np.full(len(B), B.y.mean())))
        r = {"observada": obs / null}
        for nm, tf in tru.items():
            g = prod(B, tf, seq)
            for c in (0, 1):
                i = cell == c; g[i] *= m[i].sum() / (m[i] * g[i]).sum()
            mu = m * g
            dE = 4 * mu * (1 / np.sqrt(m) - 1 / np.sqrt(m1)) + 4 * (np.sqrt(m) - np.sqrt(m1))
            sd = np.sqrt(np.sum(16 * (1 / np.sqrt(m) - 1 / np.sqrt(m1)) ** 2 * mu * (SEV[l] ** 2).mean() / SEV[l].mean()))
            r[f"esperada_{nm}"] = dE.sum() / null
            r[f"sd_eval"] = sd / null
        res[f"{l}|{tr}->{te}"] = {k: round(float(v) * 1e4, 1) for k, v in r.items()}
nul = pd.read_csv(f"{OUT}/I_t3_nulo.csv")
res["media_nulo_por_direccion_bp"] = {f"{a}|{b}": round(float(g.oneway.mean()) * 1e4, 1) for (a, b), g in nul[nul["var"] != "SEQ"].groupby(["line", "var"])}
print(json.dumps(res, indent=1))
json.dump(res, open(f"{OUT}/I_t7b_calibracion.json", "w"), indent=1)
