"""F3: factores residuales de variables propias del emergente o excluidas de T2b (género, aseguradora previa, ocupación,
segmento de marketing...), sobre la transformación de F2. Fuera de tiempo, composición 2025 por celda × banda."""
import numpy as np, pandas as pd, json, sys
exec(open("eval_v2.py").read().split("res = {}")[0])
DE = "datos/emerging"
pol = pd.concat([pd.concat([pd.read_parquet(f"{DE}/policies_{l}.parquet"), pd.read_parquet(f"{DE}/test_{l}.parquet")]) for l in ["motor","buildings","contents"]], ignore_index=True).set_index("row_id")
ad = pd.read_parquet(f"{DE}/addresses.parquet").set_index("address_id")
def col(t, c):
    return np.array([str(x) for x in _col(t, c)], dtype=object)
def _col(t, c):
    if c in cu.columns: return cu[c].reindex(t.customer_id.values).astype(str).values
    if c in pol.columns: return pol[c].reindex(t.index).astype(str).values
    if c in ad.columns: return ad[c].reindex(pol.address_id.reindex(t.index).values).astype(str).values
    if c == "occ": return cu.occupation.reindex(t.customer_id.values).astype(str).str.lower().str.replace("self-employed ", "", regex=False).str.strip().values
    raise KeyError(c)
FORMA = {"motor_0": 0.9}
def f2_fit(pool):
    f1 = fac(pool, k_ncb); t2 = pool.copy(); t2["m"] = aplica(pool, f1, k_ncb); f2 = fac(t2, k_pri); return f1, f2
def f2_apply(t, f1, f2):
    m = aplica(t, f1, k_ncb); tt = t.copy(); tt["m"] = m; m = aplica(tt, f2, k_pri); tt["m"] = m
    return aplicar(tt, FORMA)
def fac_linea(t, clave, lines, k=300):
    """factor por línea (agrupa NB y REN), relativo a la base de cada celda"""
    c = celda(t); kk = clave(t); f = {}
    rel = t.m.values.copy()
    for cc in np.unique(c):
        i = c == cc; rel[i] = rel[i] * t.y.values[i].sum() / t.m.values[i].sum()
    for l in lines:
        i = t.line.values == l
        for v in np.unique(kk[i]):
            j = i & (kk == v); n = (t.y.values[j] > 0).sum(); ae = t.y.values[j].sum() / rel[j].sum()
            f[(l, v)] = 1 + n / (n + k) * (ae - 1)
    return f
def aplica_linea(t, f, clave, m):
    c = celda(t); kk = clave(t); m0 = m.copy()
    m = m * np.array([f.get((l, v), 1.0) for l, v in zip(t.line.values, kk)])
    for cc in np.unique(c): i = c == cc; m[i] *= m0[i].sum() / m[i].sum()
    return m
K = 300
CANDS = {"gender": ["motor", "contents"], "gender_b": ["buildings"], "previous_insurer": ["motor"], "occ": ["motor"],
         "marketing_segment": ["contents"], "licence_points": ["buildings"], "policyholder_age_band": ["contents"],
         "marketing_consent": ["contents"], "payment_method": ["buildings"], "region": ["motor"], "campaign_code": ["contents", "buildings"]}
def clave_de(v):
    vv = "gender" if v == "gender_b" else v
    return lambda t: col(t, vv)
res = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("DEV23_T2b", "HOLD24_A1"), ("DEV23_T2b", "HOLD24_mezcla"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy(); w = pesos(te)
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    base = d2w(te, nivel_celda(te, te.m.values), w); r = {"base_F2": round(base, 5)}
    for v, lines in CANDS.items():
        cl = clave_de(v); f = fac_linea(tr, cl, lines, K); m = aplica_linea(te, f, cl, te.m.values)
        r[v] = round(d2w(te, nivel_celda(te, m), w) - base, 5)
    # secuencial: gender -> previous_insurer -> occ -> marketing_segment
    seq = ["gender", "previous_insurer", "occ", "marketing_segment"]
    trs, m_te = tr.copy(), te.m.values.copy()
    for v in seq:
        cl = clave_de(v); f = fac_linea(trs, cl, CANDS[v], K); trs["m"] = aplica_linea(trs, f, cl, trs.m.values); m_te = aplica_linea(te, f, cl, m_te)
        r["seq+" + v] = round(d2w(te, nivel_celda(te, m_te), w) - base, 5)
    res[f"{tr_k}->{te_k}"] = r; print(f"{tr_k}->{te_k}", r, flush=True)
json.dump(res, open("exp26/f3_eval.json", "w"), indent=1)
