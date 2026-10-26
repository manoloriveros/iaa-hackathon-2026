exec(open("/home/claude/m017/exp26/lib26.py").read())
SEQ = [("gender", ["motor", "contents"]), ("works_from_home", ["contents"]), ("marketing_segment", ["contents"])]
out = {}
for K in (30, 60, 100, 150, 300):
    for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("DEV23_T2b", "HOLD24_mezcla"), ("HOLD24_T2b", "DEV23_T2b")):
        tr, te = sets[tr_k].copy(), sets[te_k].copy()
        f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
        m_te = te.m.values.copy(); trs = tr.copy(); r = {}
        for v, lines in SEQ:
            cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(trs, cl, lines, K)
            trs["m"] = aplica_tw(trs, f, cl, trs.m.values); m_te = aplica_tw(te, f, cl, m_te)
        for l in ["motor", "contents"]:
            for seg, sel in (("ALL", np.ones(len(te), bool)), ("NB", te.new_business.values.astype(bool))):
                i = (te.line == l).values & sel; s = te[i]
                r[f"{l}_{seg}"] = round(d2u(s, nivel_celda(s, m_te[i])) - d2u(s, nivel_celda(s, s.m.values)), 5)
        out[f"K{K}|{tr_k[:5]}->{te_k[:9]}"] = r
print(pd.DataFrame(out).T.to_string())
