import numpy as np, pandas as pd, json
exec(open("f3_eval.py").read().split("K = 300")[0])
W = pd.read_parquet("/home/claude/ml2/datos/emerging/weather.parquet")
def hail(t):
    a = pol.address_id.reindex(t.index).values; yr = t.year.values.astype(int)
    k = pd.MultiIndex.from_arrays([a, yr]); return W.set_index(["address_id", "year"]).hail_days.reindex(k).values
def d2u(t, m):  # sin reponderar
    y = t.y.values; return 1 - dev(y, m).sum() / dev(y, np.full(len(y), y.mean())).sum()
CANDS = {"gender": ["motor", "contents"], "previous_insurer": ["motor"], "occ": ["motor"], "marketing_segment": ["contents"],
         "licence_points": ["buildings"], "marketing_consent": ["contents"], "payment_method": ["buildings"], "region": ["motor"]}
res = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    r = {}
    for nbsel, nm in ((False, "REN"), (True, "NB"), (None, "ALL")):
        trs = tr if nbsel is None else tr[tr.new_business == nbsel] if False else tr  # factores siempre con todo el train
        tes = te if nbsel is None else te[te.new_business == nbsel]
        base = {l: d2u(tes[tes.line == l], nivel_celda(tes[tes.line == l], tes.m.values[(tes.line == l).values])) for l in ["motor", "buildings", "contents"]}
        for v, lines in CANDS.items():
            cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_linea(tr, cl, lines, 300); m = aplica_linea(tes, f, cl, tes.m.values)
            for l in lines:
                i = (tes.line == l).values
                r[f"{nm}|{l}|{v}"] = round(d2u(tes[i], nivel_celda(tes[i], m[i])) - base[l], 5)
    res[f"{tr_k}->{te_k}"] = r
df = pd.DataFrame(res); print(df.to_string())
