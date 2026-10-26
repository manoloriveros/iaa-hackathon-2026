exec(open("/home/claude/m017/exp26/lib26.py").read())
import sys
EXCL = {"row_id","policy_id","customer_id","address_id","period_start","period_end","exposure","written_premium","customer_service_contacts",
        "renewal_decision","surname","date_of_birth","customer_since_year","y","line","occupation","make_model","vehicle_colour","new_business","renewal_count","branch_id","email_domain"}
allcols = [c for c in list(dict.fromkeys(list(pol.columns) + list(cu.columns) + list(ad.columns))) if c not in EXCL] + ["occ"]
def design(t, l, cols, cats=None):
    X = []; names = []
    for c in cols:
        v = pd.Series(_col(t, c), index=t.index)
        if v.isna().all(): continue
        if v.dtype.kind in "fi" and v.nunique() > 12:
            q = cats.get(c) if cats else np.unique(np.nanquantile(v.astype(float), [0.2, 0.4, 0.6, 0.8]))
            if cats is None: cats_[c] = q
            v = pd.Series(np.digitize(v.fillna(-9e9).astype(float), q), index=t.index).astype(str)
        else:
            v = v.astype(str)
            if cats is None:
                vc = v.value_counts(); keep = list(vc[vc >= 100].index); cats_[c] = keep
            keep = cats_[c] if cats is None else cats[c]
            v = v.where(v.isin(keep), "_otros")
        lv = (cats_ if cats is None else cats)
        d = pd.get_dummies(v, prefix=c, dtype=float); X.append(d)
    return pd.concat(X, axis=1)
def fit_ridge(y, m, X, lam, iters=30):
    Z = X.values; b = np.zeros(Z.shape[1]); b0 = 0.0
    for _ in range(iters):
        mu = m * np.exp(b0 + Z @ b); s = np.sqrt(mu); wgt = (y / s + s)
        g = Z.T @ (2 * s * (1 - y / mu)) + 2 * lam * b; g0 = np.sum(2 * s * (1 - y / mu))
        H = (Z * wgt[:, None]).T @ Z + 2 * lam * np.eye(Z.shape[1])
        # bloque: actualizar intercepto y coeficientes juntos
        Zf = np.column_stack([np.ones(len(y)), Z]); Hf = (Zf * wgt[:, None]).T @ Zf; Hf[1:, 1:] += 2 * lam * np.eye(Z.shape[1])
        gf = np.concatenate([[g0], g]); st = np.linalg.solve(Hf, gf); b0 -= st[0]; b -= st[1:]
        if np.max(np.abs(st)) < 1e-8: break
    return b0, b
LAMS = [float(x) for x in sys.argv[1:]] or [30, 100, 300, 1000]
out = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = nivel_celda(tr, f2_apply(tr, f1, f2)); te["m"] = f2_apply(te, f1, f2)
    for l in ["motor", "buildings", "contents"]:
        trl = tr[tr.line == l]; tel = te[te.line == l]
        cats_ = {}; Xa = design(trl, l, allcols); C = dict(cats_)
        Xb = design(tel, l, allcols, C).reindex(columns=Xa.columns, fill_value=0.0)
        mu_ = Xa.mean(); Xa = Xa - mu_; Xb = Xb - mu_
        base = {nm: d2u(tel[sel], nivel_celda(tel[sel], tel.m.values[sel])) for nm, sel in (("ALL", np.ones(len(tel), bool)), ("REN", ~tel.new_business.values.astype(bool)), ("NB", tel.new_business.values.astype(bool)))}
        for lam in LAMS:
            b0, bb = fit_ridge(trl.y.values, trl.m.values, Xa, lam)
            f = np.exp(Xb.values @ bb); mm = tel.m.values * f
            for nm, sel in (("ALL", np.ones(len(tel), bool)), ("REN", ~tel.new_business.values.astype(bool)), ("NB", tel.new_business.values.astype(bool))):
                out.setdefault(f"{l}|lam{lam}|{nm}", {})[f"{tr_k[:5]}->{te_k[:6]}"] = round(d2u(tel[sel], nivel_celda(tel[sel], mm[sel])) - base[nm], 5)
        print(l, tr_k, Xa.shape, flush=True)
df = pd.DataFrame(out).T; df["min"] = df.min(axis=1); print(df.to_string())
