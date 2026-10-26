"""Corrección residual: GLM Tweedie 1,5 con ridge sobre el cociente y/m (offset log m), ajustado en un año y evaluado en el otro.
Base: predicción OOF con la forma de autos ya aplicada (a = 0,5 / 0,85). Evaluación con la composición de celdas de 2025."""
import numpy as np, pandas as pd, json, warnings
from sklearn.linear_model import TweedieRegressor
warnings.filterwarnings("ignore")
exec(open("forma_local3.py").read().split("REGLA =")[0])
FORMA = {"motor_1": 0.5, "motor_0": 0.85}
cu = pd.read_parquet("datos/emerging/customers.parquet"); ad = pd.read_parquet("datos/emerging/addresses.parquet")
pol = {}
for l in ["motor", "buildings", "contents"]:
    p = pd.concat([pd.read_parquet(f"datos/emerging/policies_{l}.parquet"), pd.read_parquet(f"datos/emerging/test_{l}.parquet")], ignore_index=True)
    p = p.merge(cu, on="customer_id", how="left").merge(ad, on="address_id", how="left"); pol[l] = p.set_index("row_id")
EXCL = {"policy_id", "customer_id", "address_id", "period_start", "period_end", "exposure", "written_premium", "customer_service_contacts",
        "renewal_decision", "surname", "email_domain", "gender", "new_business", "discount_applied", "branch_id", "marketing_consent",
        "document_preference", "marketing_segment", "campaign_code", "make_model", "vehicle_colour", "days_quote_to_inception"}
def matriz(l, idx):
    p = pol[l].loc[idx]; cols = [c for c in p.columns if c not in EXCL]; X = []
    for c in cols:
        v = p[c]
        if v.dtype == bool or v.dtype == object or str(v.dtype) in ("str", "string", "category") or v.nunique() <= 8:
            v = v.astype(str).fillna("NA")
            top = v.value_counts(); keep = top[top >= 200].index; v = v.where(v.isin(keep), "otros")
        else:
            q = np.unique(np.nanquantile(pol[l][c].astype(float), [0.2, 0.4, 0.6, 0.8]))
            v = pd.Series(np.digitize(v.astype(float).fillna(-9e9), q), index=v.index).astype(str)
        X.append(pd.get_dummies(v, prefix=c, dtype=float))
    return pd.concat(X, axis=1)
res = {}
for k_tr, k_te in (("DEV23_T2b", "HOLD24_T2b"), ("HOLD24_T2b", "DEV23_T2b"), ("DEV23_T2b", "HOLD24_A1")):
    tr = sets[k_tr].copy(); te = sets[k_te].copy(); tr["m"] = aplicar(tr, FORMA); te["m"] = aplicar(te, FORMA)
    cel = te.line + "_" + te.new_business.astype(int).astype(str); n = cel.value_counts(normalize=True); w = cel.map(n25 / n).values
    def nivel(t, m):
        c_ = (t.line + "_" + t.new_business.astype(int).astype(str)).values; m = m.copy()
        for c in np.unique(c_): i = c_ == c; m[i] *= kopt(t.y.values[i], m[i])
        return m
    base = d2w(te, nivel(te, te.m.values), w); r = {"base_forma": round(base, 5)}
    for alpha in (0.3, 1.0, 3.0, 10.0, 30.0):
        m_new = te.m.values.copy()
        for l in ["motor", "buildings", "contents"]:
            itr = (tr.line == l).values; ite = (te.line == l).values
            Xa = matriz(l, tr.index[itr]); Xb = matriz(l, te.index[ite]).reindex(columns=Xa.columns, fill_value=0.0)
            Xa["nb"] = tr.new_business.values[itr].astype(float); Xb["nb"] = te.new_business.values[ite].astype(float)
            mm = tr.m.values[itr]; g = TweedieRegressor(power=1.5, link="log", alpha=alpha, max_iter=1000)
            g.fit(Xa.values, tr.y.values[itr] / mm, sample_weight=np.sqrt(mm))
            f = g.predict(Xb.values); f = f / np.average(f, weights=te.m.values[ite])
            m_new[ite] = te.m.values[ite] * f
        r[f"alpha={alpha}"] = round(d2w(te, nivel(te, m_new), w) - base, 5)
    res[f"{k_tr}->{k_te}"] = r; print(k_tr, "->", k_te, r, flush=True)
json.dump(res, open("residual_glm.json", "w"), indent=1)
