import numpy as np, pandas as pd, json
exec(open("forma_local3.py").read().split("REGLA =")[0])
pm = pd.read_parquet("datos/emerging/policies_motor.parquet", columns=["row_id", "ncb_years"]).set_index("row_id")
tm = pd.read_parquet("datos/emerging/test_motor.parquet", columns=["row_id", "ncb_years"]).set_index("row_id")
ncb = pd.concat([pm, tm]).ncb_years
def band(v): return pd.cut(v, [-1, 0, 2, 5, 9, 99], labels=["0", "1-2", "3-5", "6-9", "10+"]).astype(str)
def factores(t, por_nb):
    g = t[t.line == "motor"].copy(); g["nb"] = band(ncb.reindex(g.index).values)
    g["k"] = g.new_business.astype(int) if por_nb else 0
    f = {}
    for (k, nbd), s in g.groupby(["k", "nb"]):
        tot = g[g.k == k]; base = tot.y.sum() / tot.m.sum()
        ae = (s.y.sum() / s.m.sum()) / base; n = (s.y > 0).sum(); z = n / (n + 300)   # credibilidad por número de siniestros
        f[(k, nbd)] = 1 + z * (ae - 1)
    return f
def aplicar_ncb(t, f, por_nb):
    m = t.m.values.copy(); i = (t.line == "motor").values
    nbd = band(ncb.reindex(t.index[i]).values); k = t.new_business.values[i].astype(int) if por_nb else np.zeros(i.sum(), int)
    m[i] = m[i] * np.array([f[(kk, bb)] for kk, bb in zip(k, nbd)]); return m
def evalua(t, m):
    cel = t.line + "_" + t.new_business.astype(int).astype(str); n = cel.value_counts(normalize=True); w = cel.map(n25 / n).values
    m = m.copy()
    for c in cel.unique():
        i = (cel == c).values; m[i] = m[i] * kopt(t.y.values[i], m[i])
    return d2w(t, m, w)
res = {}
for por_nb in (False, True):
    f = factores(sets["DEV23_T2b"], por_nb); res[f"factores_2023_por_nb={por_nb}"] = {f"{k}|{b_}": round(v, 3) for (k, b_), v in f.items()}
    for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
        t = sets[k]; base = evalua(t, t.m.values)
        t2 = t.copy(); t2["m"] = aplicar_ncb(t, f, por_nb); con_ncb = evalua(t2, t2.m.values)
        con_ambos = evalua(t2, aplicar(t2, {"motor_1": 0.5, "motor_0": 0.85}))
        solo_forma = evalua(t, aplicar(t, {"motor_1": 0.5, "motor_0": 0.85}))
        res[f"{k}_por_nb={por_nb}"] = {"base": round(base, 5), "ncb_2023": round(con_ncb - base, 5), "forma": round(solo_forma - base, 5), "ncb+forma": round(con_ambos - base, 5)}
print(json.dumps(res, indent=1))
