"""Inspect motor shape using the correct Tweedie scalar and 2025 cell/exposure-band composition."""
import numpy as np, pandas as pd, json
exec(open("forma_local3.py").read().split("REGLA =")[0])
def banda(e): return np.where(e < 0.5, "c", np.where(e < 0.9, "m", "l"))
te = b[b.conjunto == "test"]; k25 = (te.line + "_" + te.new_business.astype(int).astype(str) + "_" + banda(te.exposure.values)).value_counts(normalize=True)
def pesos(t):
    k = t.line + "_" + t.new_business.astype(int).astype(str) + "_" + banda(t.exposure.values); n = k.value_counts(normalize=True)
    return k.map(k25 / n).fillna(0).values
A = np.round(np.arange(0.2, 1.31, 0.05), 2)
def nivel_celda(t, m):
    cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values; m = m.copy()
    for c in np.unique(cel): i = cel == c; m[i] *= kopt(t.y.values[i], m[i])
    return m
def d2w(t, m, w):
    y = t.y.values; mu0 = np.average(y, weights=w); return 1 - (dev(y, m) * w).sum() / (dev(y, np.full(len(y), mu0)) * w).sum()
out = {}
for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    t = sets[k]; w = pesos(t); r = {}
    for c in ["motor_1", "motor_0"]:
        cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values; i = cel == c; s = t[i]; ww = w[i]
        yy = s.y.values; e = (s.exposure * s.c_fila).values; rr = s.m.values / e; gm = s.m.values.sum() / e.sum()
        def curva(mask, wt):
            return np.array([(dev(yy[mask], (lambda mm: mm * kopt(yy[mask], mm))(e[mask] * gm * (rr[mask] / gm) ** a)) * wt[mask]).sum() for a in A])
        todo = curva(np.ones(len(s), bool), np.ones(len(s))); largo = curva(s.exposure.values >= 0.9, np.ones(len(s))); rep = curva(np.ones(len(s), bool), ww)
        r[c] = {"a_opt_todas": float(A[todo.argmin()]), "a_opt_expo>=0.9": float(A[largo.argmin()]), "a_opt_reponderado2025": float(A[rep.argmin()]),
                "positivos_expo>=0.9": int(((yy > 0) & (s.exposure.values >= 0.9)).sum())}
    base = d2w(t, nivel_celda(t, t.m.values), w)
    for a1, a0 in ((0.5, 0.85), (0.6, 0.9), (0.7, 0.9), (0.75, 0.9), (0.8, 0.9), (0.85, 0.9)):
        r[f"ganancia_reponderada_a{a1}_{a0}"] = round(d2w(t, nivel_celda(t, aplicar(t, {"motor_1": a1, "motor_0": a0})), w) - base, 5)
    out[k] = r
print(json.dumps(out, indent=1)); json.dump(out, open("forma_v2.json", "w"), indent=1)
