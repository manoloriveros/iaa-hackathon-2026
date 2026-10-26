exec(open("/home/claude/m017/exp26/lib26.py").read())
import hashlib
G = [("gender", ["motor", "contents"])]
base_sets = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    for v, lines in G:
        cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(tr, cl, lines, 300); tr["m"] = aplica_tw(tr, f, cl, tr.m.values); te["m"] = aplica_tw(te, f, cl, te.m.values)
    base_sets[tr_k] = (tr, te)
rng = np.random.default_rng(7)
rows = []
for rep in range(60):
    for nlev, ent in ((2, "customer_id"), (5, "customer_id"), (5, "address_id")):
        salt = rng.integers(1e9)
        for l in ["motor", "buildings", "contents"]:
            g = []
            for tr_k, (tr, te) in base_sets.items():
                trl = tr[tr.line == l]; tel = te[te.line == l]
                def fake(t):
                    ids = t.customer_id.values if ent == "customer_id" else pol.address_id.reindex(t.index).values
                    return np.array([str(hash((salt, x)) % nlev) for x in ids], dtype=object)
                f = fac_tw(trl, fake, [l], 300); m = aplica_tw(tel, f, fake, tel.m.values)
                g.append(d2u(tel, nivel_celda(tel, m)) - d2u(tel, nivel_celda(tel, tel.m.values)))
            rows.append(dict(rep=rep, nlev=nlev, ent=ent, line=l, g1=g[0], g2=g[1], mn=min(g)))
r = pd.DataFrame(rows); r.to_csv("exp26/null_screen.csv", index=False)
print(r.groupby(["line", "nlev", "ent"]).mn.describe(percentiles=[0.5, 0.9, 0.95, 0.99]).round(5).to_string())
print(r.groupby("line")[["g1","g2"]].describe(percentiles=[0.5,0.95]).round(5).T.to_string())
