exec(open("/home/claude/m017/exp26/lib26.py").read())
# variantes de F2: (a) actual A/E por celda; (b) Tweedie-óptimo por celda (by_nb); (c) Tweedie-óptimo agrupado NB+REN
k_ncb_l = lambda t: np.where(t.line.values == "motor", bnd(ncb.reindex(t.index).fillna(0).values), "x").astype(object)
k_pri_l = lambda t: np.minimum(cu.prior_claims_5y.reindex(t.customer_id.values).fillna(0).values, 2).astype(int).astype(str).astype(object)
def var_tw(tr, te, by_nb, K=300):
    f1 = fac_tw(tr, k_ncb_l, ["motor"], K, by_nb); t2 = tr.copy(); t2["m"] = aplica_tw(tr, f1, k_ncb_l, tr.m.values, by_nb)
    f2 = fac_tw(t2, k_pri_l, ["motor", "buildings", "contents"], K, by_nb)
    m = aplica_tw(te, f1, k_ncb_l, te.m.values, by_nb); tt = te.copy(); tt["m"] = m; m = aplica_tw(tt, f2, k_pri_l, m, by_nb); tt["m"] = m
    return aplicar(tt, {"motor_0": 0.9})
out = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("DEV23_T2b", "HOLD24_mezcla"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy(); w = pesos(te)
    b0 = nivel_celda(te, te.m.values)
    f1, f2 = f2_fit(tr); ma = f2_apply(te, f1, f2)
    r = {}
    for nm, m in (("F2_AE", ma), ("TW_bynb", var_tw(tr, te, True)), ("TW_pool", var_tw(tr, te, False))):
        mm = nivel_celda(te, m)
        r[nm + "_unw"] = round(d2u(te, mm) - d2u(te, b0), 5); r[nm + "_w"] = round(d2w(te, mm, w) - d2w(te, b0, w), 5)
        for seg, sel in (("REN", ~te.new_business.values.astype(bool)), ("NB", te.new_business.values.astype(bool))):
            s = te[sel]; r[nm + "_" + seg] = round(d2u(s, nivel_celda(s, m[sel])) - d2u(s, nivel_celda(s, s.m.values)), 5)
    out[f"{tr_k[:5]}->{te_k[:9]}"] = r
print(pd.DataFrame(out).to_string())
