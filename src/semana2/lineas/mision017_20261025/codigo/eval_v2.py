import numpy as np, pandas as pd, json
exec(open("forma_v2.py").read().split("out = {}")[0])
exec(open("ncb_local.py").read().split("def evalua")[0].split("exec(")[0] if False else "")
pm = pd.read_parquet("datos/emerging/policies_motor.parquet", columns=["row_id", "ncb_years"]).set_index("row_id")
tm = pd.read_parquet("datos/emerging/test_motor.parquet", columns=["row_id", "ncb_years"]).set_index("row_id")
ncb = pd.concat([pm, tm]).ncb_years
cu = pd.read_parquet("datos/emerging/customers.parquet").set_index("customer_id")
def bnd(v): return pd.cut(v, [-1, 0, 2, 5, 9, 99], labels=["0", "1-2", "3-5", "6-9", "10+"]).astype(str)
def celda(t): return (t.line + "_" + t.new_business.astype(int).astype(str)).values
def fac(t, clave, k=300):
    c = celda(t); f = {}
    for cc in np.unique(c):
        i = c == cc; base = t.y.values[i].sum() / t.m.values[i].sum(); kk = clave(t)[i]
        for v in np.unique(kk):
            j = kk == v; n = (t.y.values[i][j] > 0).sum(); ae = t.y.values[i][j].sum() / t.m.values[i][j].sum() / base
            f[(cc, v)] = 1 + n / (n + k) * (ae - 1)
    return f
def aplica(t, f, clave, m=None):
    m = t.m.values.copy() if m is None else m.copy(); c = celda(t); kk = clave(t); m0 = m.copy()
    m = m * np.array([f.get((a, v), 1.0) for a, v in zip(c, kk)])
    for cc in np.unique(c): i = c == cc; m[i] *= m0[i].sum() / m[i].sum()
    return m
k_ncb = lambda t: np.where(t.line.values == "motor", bnd(ncb.reindex(t.index).fillna(0).values), "x")
k_pri = lambda t: np.minimum(cu.prior_claims_5y.reindex(t.customer_id.values).fillna(0).values, 2).astype(int).astype(str)
res = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("DEV23_T2b", "HOLD24_A1"), ("DEV23_T2b", "HOLD24_mezcla"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k], sets[te_k]; w = pesos(te)
    f1 = fac(tr, k_ncb); f2 = fac(tr, k_pri)
    m_n = aplica(te, f1, k_ncb); t2 = te.copy(); t2["m"] = m_n; m_np = aplica(t2, f2, k_pri)
    base = d2w(te, nivel_celda(te, te.m.values), w); r = {"base": round(base, 5)}
    r["ncb"] = round(d2w(te, nivel_celda(te, m_n), w) - base, 5)
    r["ncb+prior"] = round(d2w(te, nivel_celda(te, m_np), w) - base, 5)
    t3 = te.copy(); t3["m"] = m_np
    for a1 in (0.6, 0.7, 0.8, 0.9, 1.0):
        r[f"ncb+prior+forma({a1},0.85)"] = round(d2w(te, nivel_celda(te, aplicar(t3, {"motor_1": a1, "motor_0": 0.85})), w) - base, 5)
    res[f"{tr_k}->{te_k}"] = r
print(json.dumps(res, indent=1)); json.dump(res, open("eval_v2.json", "w"), indent=1)
