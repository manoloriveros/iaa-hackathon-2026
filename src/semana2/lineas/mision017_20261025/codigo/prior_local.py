import numpy as np, pandas as pd, json
exec(open("construir_forma.py").read().split("# 2025")[0])
cu = pd.read_parquet("datos/emerging/customers.parquet").set_index("customer_id")
def pc(t): return np.minimum(cu.prior_claims_5y.reindex(t.customer_id.values).fillna(0).values, 2).astype(int)
def base_f1(t):
    m2, cel = transformar(t, fN); t2 = t.copy(); t2["m"] = m2; return t2
def fac_prior(t, k=300):
    t = t.copy(); t["pc"] = pc(t); t["cel"] = t.line + "_" + t.new_business.astype(int).astype(str); f = {}
    for c, g in t.groupby("cel"):
        base = g.y.sum() / g.m.sum()
        for v, s in g.groupby("pc"):
            n = (s.y > 0).sum(); ae = s.y.sum() / s.m.sum() / base; f[(c, v)] = 1 + n / (n + k) * (ae - 1)
    return f
def aplicar_prior(t, f):
    cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values; p = pc(t); m = t.m.values * np.array([f.get((c, v), 1.0) for c, v in zip(cel, p)])
    for c in np.unique(cel): i = cel == c; m[i] *= t.m.values[i].sum() / m[i].sum()
    return m
out = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("DEV23_T2b", "HOLD24_A1"), ("DEV23_T2b", "HOLD24_mezcla"), ("HOLD24_T2b", "DEV23_T2b")):
    tr = base_f1(sets[tr_k]); te = base_f1(sets[te_k]); f = fac_prior(tr)
    b0 = evalua(te, te.m.values); b1 = evalua(te, aplicar_prior(te, f))
    out[f"{tr_k}->{te_k}"] = {"ganancia_prior_sobre_F1": round(b1 - b0, 5), "factores": {f"{c}|{v}": round(x, 3) for (c, v), x in f.items()}}
print(json.dumps(out, indent=1))
