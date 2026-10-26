"""J, tarea 3: (1) validación cruzada en el tiempo agrupada por cliente (5 pliegues, 2023+2024 juntos) de F2, forma y factores;
(2) ruido de muestreo de ρ por celda (bootstrap por cliente sobre la evaluación) llevado al tamaño del público 2025 (1/3 del test)."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
from J_lib import *
exec(open(R + "revision/J_local.py").read().split("ser = series()")[0].split("from J_lib import *")[1])

ser = series()
pool = pd.concat([ser["DEV23_T2b"], ser["HOLD24_T2b"]])
cust = pool.customer_id.values
fold = np.array([hash(x) % 5 for x in cust]) if False else (pd.util.hash_array(cust.astype(str)) % 5).astype(int)
pred = {k: np.zeros(len(pool)) for k in ("m0", "F2", "forma", "fac")}
for f in range(5):
    tr = pool[fold != f]; te = pool[fold == f]; T3 = TransfF3(tr, A3)
    i = fold == f
    pred["m0"][i] = te.m.values; pred["F2"][i] = T3.f2(te, te.m.values); pred["forma"][i] = T3.forma(te, pred["F2"][i])
    pred["fac"][i] = T3(te, te.m.values)
w = pesos(pool)
cv = {"F2": rho(pool, pred["m0"], pred["F2"], w), "forma_m1": rho(pool, pred["F2"], pred["forma"], w),
      "factores": rho(pool, pred["forma"], pred["fac"], w), "factores_sin_peso": rho(pool, pred["forma"], pred["fac"], np.ones(len(pool)))}
for yr in (2023, 2024):
    j = pool.year.values == yr; p = pool[j]
    cv[f"factores_{yr}"] = rho(p, pred["forma"][j], pred["fac"][j], w[j])
print("CV", {k: {c: round(x * 1e4, 1) for c, x in v.items()} for k, v in cv.items()}, flush=True)

# bootstrap por cliente del ρ de los factores (CV) por celda → error típico, y escalado al público 2025
rng = np.random.default_rng(11)
uc, inv = np.unique(cust, return_inverse=True)
c_ = celda(pool); y = pool.y.values
bs = {cc: [] for cc in CELS}; bsF2 = {cc: [] for cc in CELS}
for b in range(300):
    wc = rng.poisson(1.0, len(uc))[inv] * w
    for cc in CELS:
        i = c_ == cc
        q0 = Q(y[i], pred["forma"][i], wc[i]); bs[cc].append((q0 - Q(y[i], pred["fac"][i], wc[i])) / q0)
        q0 = Q(y[i], pred["m0"][i], wc[i]); bsF2[cc].append((q0 - Q(y[i], pred["F2"][i], wc[i])) / q0)
te25 = B[B.conjunto == "test"]; n25 = pd.Series(celda(te25)).value_counts()
nh = pd.Series(c_).value_counts()
se = {cc: {"se_rho_hist": float(np.std(bs[cc])), "se_rho_F2_hist": float(np.std(bsF2[cc])), "n_hist": int(nh[cc]), "n_pub": float(n25[cc] / 3),
           "se_rho_pub": float(np.std(bs[cc]) * np.sqrt(nh[cc] / (n25[cc] / 3))), "se_rho_F2_pub": float(np.std(bsF2[cc]) * np.sqrt(nh[cc] / (n25[cc] / 3)))}
      for cc in CELS}
print("SE", json.dumps(se, indent=1))
json.dump({"cv": cv, "se": se}, open(R + "revision/J_local2.json", "w"), indent=1, default=float)
