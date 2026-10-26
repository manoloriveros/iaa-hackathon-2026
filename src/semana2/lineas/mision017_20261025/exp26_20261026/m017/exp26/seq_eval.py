exec(open("/home/claude/m017/exp26/lib26.py").read())
import sys
SEQ = [("gender", ["motor", "contents"]), ("previous_insurer", ["motor"]), ("occ", ["motor"]), ("licence_points", ["buildings"]), ("marketing_segment", ["contents"])]
out = {}
for K in (150, 300, 600, 1200):
    for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("DEV23_T2b", "HOLD24_mezcla"), ("HOLD24_T2b", "DEV23_T2b")):
        tr, te = sets[tr_k].copy(), sets[te_k].copy()
        f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
        w = pesos(te); m_te = te.m.values.copy(); trs = tr.copy()
        b_all = d2u(te, nivel_celda(te, te.m.values)); b_w = d2w(te, nivel_celda(te, te.m.values), w)
        r = {}
        for v, lines in SEQ:
            cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(trs, cl, lines, K)
            trs["m"] = aplica_tw(trs, f, cl, trs.m.values); m_te = aplica_tw(te, f, cl, m_te)
        mm = nivel_celda(te, m_te)
        r["ALL_unw"] = round(d2u(te, mm) - b_all, 5); r["ALL_w2025"] = round(d2w(te, mm, w) - b_w, 5)
        for nm, sel in (("REN", te.new_business.values == False), ("NB", te.new_business.values == True)):
            s = te[sel]; r[nm] = round(d2u(s, nivel_celda(s, m_te[sel])) - d2u(s, nivel_celda(s, s.m.values)), 5)
        for l in ["motor", "buildings", "contents"]:
            i = (te.line == l).values; s = te[i]; r[l] = round(d2u(s, nivel_celda(s, m_te[i])) - d2u(s, nivel_celda(s, s.m.values)), 5)
        out[f"K{K}|{tr_k[:5]}->{te_k[:9]}"] = r
print(pd.DataFrame(out).T.to_string())
