exec(open("/home/claude/m017/exp26/lib26.py").read())
import statsmodels.api as sm
B = {l: pd.read_parquet(f"/home/claude/ml2/trabajo/base_emerging_{l}.parquet").set_index("row_id") for l in ["motor", "buildings"]}
PER = {"motor": "y_glass_hail", "buildings": "y_storm"}
def share_and_beta(t, l):
    s = t[t.line == l]; bb = B[l].reindex(s.index); yp = bb[PER[l]].fillna(0).values
    h = wvar(s, "hail_days"); hm = np.nanmean(h)
    X = sm.add_constant(pd.DataFrame({"h": h - hm})); ind = (yp > 0).astype(float)
    g = sm.GLM(ind, X, family=sm.families.Poisson(), offset=np.log(s.exposure.values.clip(1e-4))).fit()
    sh = yp.sum() / s.y.sum()
    cov = pol.cover_type.reindex(s.index).astype(str).values if l == "motor" else None
    shc = {c: yp[cov == c].sum() / s.y.values[cov == c].sum() for c in np.unique(cov)} if l == "motor" else None
    return sh, shc, g.params["h"], hm, g.tvalues["h"]
res = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy()
    f1, f2 = f2_fit(tr); te["m"] = f2_apply(te, f1, f2)
    r = {}
    for l in ["motor", "buildings"]:
        sh, shc, beta, hm, z = share_and_beta(tr, l)
        i = (te.line == l).values; s = te[i]; h = wvar(s, "hail_days"); h_te = np.nanmean(h)
        for mult in (0.5, 1.0, 1.5):
            if l == "motor":
                cov = pol.cover_type.reindex(s.index).astype(str).values; shr = np.array([shc[c] for c in cov])
            else: shr = sh
            # ranking only: centered on test-year mean so cell level unchanged after re-leveling anyway
            fct = 1 + shr * (np.exp(mult * beta * (h - h_te)) - 1)
            m = s.m.values * fct
            for nm, sel in (("REN", s.new_business.values == False), ("NB", s.new_business.values == True), ("ALL", np.ones(len(s), bool))):
                ss = s[sel]
                r[f"{l}|x{mult}|{nm}"] = round(d2u(ss, nivel_celda(ss, m[sel])) - d2u(ss, nivel_celda(ss, ss.m.values)), 5)
        r[f"{l}|beta"] = round(beta, 4); r[f"{l}|z"] = round(z, 1); r[f"{l}|share"] = round(sh, 3)
        if shc: r[f"{l}|share_cov"] = {k: round(v, 3) for k, v in shc.items()}
    res[f"{tr_k[:5]}->{te_k[:6]}"] = r
print(json.dumps(res, indent=1, default=str))
