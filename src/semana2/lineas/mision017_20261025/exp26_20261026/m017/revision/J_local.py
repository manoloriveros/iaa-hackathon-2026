"""J, tarea 3: evidencia local por celda (fuera de tiempo) para F2, la forma de motor_1 y los factores de F3.
Medida: ρ_s = reducción relativa de Q_s = 8√(Σw·y/√m · Σw·√m) (desvianza al nivel óptimo de la celda sin el término de y),
con pesos w de composición 2025 por banda de exposición dentro de la celda. En el público: G_s ≈ 2·ρ_s·A_s(F)."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
from J_lib import *

A3 = 1 + 0.927 * (1.3212 - 1)
te25 = B[B.conjunto == "test"]


def banda(e):
    return np.where(e < 0.5, "c", np.where(e < 0.9, "m", "l"))


k25 = pd.Series([f"{a}|{b_}" for a, b_ in zip(celda(te25), banda(te25.exposure.values))]).value_counts(normalize=True)


def pesos(t):
    k = pd.Series([f"{a}|{b_}" for a, b_ in zip(celda(t), banda(t.exposure.values))])
    n = k.value_counts(normalize=True); return k.map(k25 / n).fillna(0).values


def Q(y, m, w):
    return 8 * np.sqrt(np.sum(w * y / np.sqrt(m)) * np.sum(w * np.sqrt(m)))


def rho(t, m0, m1, w):
    c = celda(t); y = t.y.values; r = {}
    for cc in CELS:
        i = c == cc; q0 = Q(y[i], m0[i], w[i]); r[cc] = (q0 - Q(y[i], m1[i], w[i])) / q0
    return r


ser = series()
out = {}
pares = [("DEV23_T2b", "HOLD24_T2b"), ("DEV23_T2b", "HOLD24_mezcla"), ("DEV23_T2b", "HOLD24_A1"), ("HOLD24_T2b", "DEV23_T2b")]
for tr_k, te_k in pares + [("POOL", "POOL")]:
    if tr_k == "POOL":
        tr = pd.concat([ser["DEV23_T2b"], ser["HOLD24_T2b"]]); te = tr
    else:
        tr, te = ser[tr_k], ser[te_k]
    T3 = TransfF3(tr, A3)
    w = pesos(te); w1 = np.ones(len(te))
    m0 = te.m.values
    mF2 = T3.f2(te, m0)
    msh = T3.forma(te, mF2)
    mf = msh.copy(); pasos = {}
    prev = msh.copy()
    for v, f in T3.fac:
        mf = aplica_ramo(te, mf, f, var(te, v)); pasos[v] = rho(te, prev, mf, w); prev = mf.copy()
    r = {"F2": rho(te, m0, mF2, w), "forma_m1": rho(te, mF2, msh, w), "factores": rho(te, msh, mf, w),
         "factores_sin_peso": rho(te, msh, mf, w1), "factores_por_paso": pasos}
    out[f"{tr_k}->{te_k}"] = r
    print(tr_k, "->", te_k, {k: {c: round(x * 1e4, 1) for c, x in v.items()} for k, v in r.items() if k != "factores_por_paso"}, flush=True)

# estabilidad de los factores: estimados por año (sobre F2+forma de ese año) y comparados
fy = {}
for k in ["DEV23_T2b", "HOLD24_T2b"]:
    T3 = TransfF3(ser[k], A3); fy[k] = {v: {f"{l}|{vv}": x for (l, vv), x in f.items()} for v, f in T3.fac}
estab = {}
for v in fy["DEV23_T2b"]:
    a, b_ = fy["DEV23_T2b"][v], fy["HOLD24_T2b"][v]; ks = sorted(set(a) & set(b_))
    la, lb = np.log([a[k] for k in ks]), np.log([b_[k] for k in ks])
    estab[v] = {"corr_log_2023_2024": float(np.corrcoef(la, lb)[0, 1]) if len(ks) > 2 else None,
                "pares": {k: [round(a[k], 3), round(b_[k], 3)] for k in ks} if len(ks) <= 12 else None}
out["estabilidad_factores"] = estab
json.dump(out, open(R + "revision/J_local.json", "w"), indent=1, default=float, ensure_ascii=False)
print(json.dumps(estab, indent=1, ensure_ascii=False))
