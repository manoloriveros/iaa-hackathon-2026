import numpy as np, pandas as pd, json
exec(open("forma_local.py").read().split("A = np.round")[0].replace('print(k, len(t)', '0 and print(k, len(t)'))
te = b[b.conjunto == "test"].copy(); te["cel"] = te.line + "_" + te.new_business.astype(int).astype(str)
n25 = te.cel.value_counts(normalize=True)
A = np.round(np.arange(0.2, 1.51, 0.05), 2)
def curva(t, w):
    """D² ponderado por celda (pesos de composición) con nivel óptimo por celda; devuelve dev por celda y a."""
    out = {}
    for c, g in t.groupby("cel"):
        yy = g.y.values; e = g.exposure.values * g.c_fila.values; r = g.m.values / e; gm = g.m.values.sum() / e.sum()
        out[c] = np.array([dev(yy, (lambda m: m * kopt(yy, m))(e * gm * (r / gm) ** a)).sum() for a in A]) * w[c]
    return out
res = {}
rng = np.random.default_rng(7)
for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1"]:
    t = sets[k].copy(); t["cel"] = t.line + "_" + t.new_business.astype(int).astype(str)
    n = t.cel.value_counts(normalize=True); w25 = (n25 / n).to_dict(); w1 = {c: 1.0 for c in n.index}
    null1 = dev(t.y.values, np.full(len(t), t.y.mean())).sum()
    null25 = (dev(t.y.values, np.full(len(t), t.y.mean())) * t.cel.map(w25).values).sum()
    i1 = int(np.where(A == 1.0)[0][0]); r = {}
    for nombre, w, nl in (("composicion_propia", w1, null1), ("composicion_2025", w25, null25)):
        cv = curva(t, w); tot = sum(v[i1] - v.min() for v in cv.values()) / nl
        r[nombre] = {"ganancia_D2_total": round(float(tot), 5), "a_opt": {c: float(A[v.argmin()]) for c, v in cv.items()},
                     "ganancia_por_celda": {c: round(float((v[i1] - v.min()) / nl), 5) for c, v in cv.items()}}
    # bootstrap por cliente del a óptimo en motor_1 y motor_0
    bs = {"motor_1": [], "motor_0": [], "buildings_1": [], "contents_1": []}
    custs = t.customer_id.unique()
    for _ in range(200):
        s = pd.Series(rng.choice(custs, len(custs)), name="customer_id").value_counts()
        tw = t.join(s.rename("bw"), on="customer_id").dropna(subset=["bw"])
        for c in bs:
            g = tw[tw.cel == c]; yy = g.y.values; e = g.exposure.values * g.c_fila.values; rr = g.m.values / e; gm = g.m.values.sum() / e.sum(); ww = g.bw.values
            dv = [ (dev(yy, (lambda m: m * kopt(np.repeat(yy, ww.astype(int)), np.repeat(m, ww.astype(int))))(e * gm * (rr / gm) ** a)) * ww).sum() for a in A]
            bs[c].append(float(A[int(np.argmin(dv))]))
    r["bootstrap_a_opt_p05_p50_p95"] = {c: [float(np.percentile(v, q)) for q in (5, 50, 95)] for c, v in bs.items()}
    res[k] = r
print(json.dumps(res, indent=1))
json.dump(res, open("forma_local2.json", "w"), indent=1)
