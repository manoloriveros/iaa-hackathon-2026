exec(open("/home/claude/m017/exp26/lib26.py").read())
EXCL = {"row_id","policy_id","customer_id","address_id","period_start","period_end","exposure","written_premium","customer_service_contacts",
        "renewal_decision","surname","date_of_birth","customer_since_year","y","line"}
def bins(t, c):
    v = _col(t, c)
    s = pd.Series(v)
    if s.dtype.kind in "fi" and s.nunique() > 12:
        q = np.unique(np.nanquantile(s.astype(float), [0.2, 0.4, 0.6, 0.8])); return np.array([str(x) for x in np.digitize(s.fillna(-9e9).astype(float), q)], dtype=object)
    return np.array([str(x) for x in v], dtype=object)
allcols = [c for c in list(pol.columns) + list(cu.columns) + list(ad.columns) if c not in EXCL] + ["occ"]
allcols = list(dict.fromkeys(allcols))
G = [("gender", ["motor", "contents"])]
res = {}
base_sets = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    for v, lines in G:
        cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(tr, cl, lines, 300); tr["m"] = aplica_tw(tr, f, cl, tr.m.values); te["m"] = aplica_tw(te, f, cl, te.m.values)
    base_sets[tr_k] = (tr, te)
rows = []
for l in ["motor", "buildings", "contents"]:
    for c in allcols:
        g = {}
        for tr_k, (tr, te) in base_sets.items():
            try:
                trl = tr[tr.line == l]; tel = te[te.line == l]
                v_tr = bins(trl, c); v_te = bins(tel, c)
                if len(np.unique(v_tr)) < 2 or len(np.unique(v_tr)) > 60: raise ValueError
                cl_tr = lambda t, v=v_tr: v; cl_te = lambda t, v=v_te: v
                f = fac_tw(trl, cl_tr, [l], 300); m = aplica_tw(tel, f, cl_te, tel.m.values)
                g[tr_k] = d2u(tel, nivel_celda(tel, m)) - d2u(tel, nivel_celda(tel, tel.m.values))
            except Exception as e:
                g[tr_k] = np.nan
        rows.append(dict(line=l, var=c, g23_24=g.get("DEV23_T2b"), g24_23=g.get("HOLD24_T2b")))
r = pd.DataFrame(rows); r["min"] = r[["g23_24", "g24_23"]].min(axis=1)
r.to_csv("exp26/screen.csv", index=False)
pd.set_option("display.width", 200)
print(r.sort_values("min", ascending=False).head(40).round(5).to_string())
