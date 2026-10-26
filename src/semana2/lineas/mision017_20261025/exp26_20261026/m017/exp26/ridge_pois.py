exec(open("/home/claude/m017/exp26/ridge_glm.py").read().split("LAMS =")[0])
NS = pd.concat([pd.read_parquet(f"/home/claude/ml2/trabajo/base_emerging_{l}.parquet", columns=["row_id", "n_sin"]) for l in ["motor", "buildings", "contents"]]).set_index("row_id").n_sin
def fit_pois(n, m, X, lam, iters=40):
    Zf = np.column_stack([np.ones(len(n)), X.values]); b = np.zeros(Zf.shape[1])
    P = 2 * lam * np.eye(Zf.shape[1]); P[0, 0] = 0
    for _ in range(iters):
        mu = m * np.exp(Zf @ b); g = Zf.T @ (mu - n) + P @ b; H = (Zf * mu[:, None]).T @ Zf + P
        st = np.linalg.solve(H, g); b -= st
        if np.max(np.abs(st)) < 1e-9: break
    return b[0], b[1:]
LAMS = [float(x) for x in sys.argv[1:]]
out = {}; coefs = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = nivel_celda(tr, f2_apply(tr, f1, f2)); te["m"] = f2_apply(te, f1, f2)
    for l in ["motor", "buildings", "contents"]:
        trl = tr[tr.line == l]; tel = te[te.line == l]
        cats_ = {}; Xa = design(trl, l, allcols); C = dict(cats_)
        Xb = design(tel, l, allcols, C).reindex(columns=Xa.columns, fill_value=0.0)
        mu_ = Xa.mean(); Xa = Xa - mu_; Xb = Xb - mu_
        n = NS.reindex(trl.index).fillna(0).values.astype(float)
        mf = trl.m.values / trl.m.values.sum() * n.sum()   # frecuencia esperada ∝ coste esperado
        base = {nm: d2u(tel[sel], nivel_celda(tel[sel], tel.m.values[sel])) for nm, sel in (("ALL", np.ones(len(tel), bool)), ("REN", ~tel.new_business.values.astype(bool)), ("NB", tel.new_business.values.astype(bool)))}
        for lam in LAMS:
            b0, bb = fit_pois(n, mf, Xa, lam)
            f = np.exp(Xb.values @ bb); mm = tel.m.values * f
            coefs[(l, tr_k, lam)] = pd.Series(bb, index=Xa.columns)
            for nm, sel in (("ALL", np.ones(len(tel), bool)), ("REN", ~tel.new_business.values.astype(bool)), ("NB", tel.new_business.values.astype(bool))):
                out.setdefault(f"{l}|lam{lam:g}|{nm}", {})[f"{tr_k[:5]}->{te_k[:6]}"] = round(d2u(tel[sel], nivel_celda(tel[sel], mm[sel])) - base[nm], 5)
df = pd.DataFrame(out).T; df["min"] = df.min(axis=1); print(df.to_string())
import pickle; pickle.dump(coefs, open("exp26/coefs_pois.pkl", "wb"))
