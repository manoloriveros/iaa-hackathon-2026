exec(open("/home/claude/m017/exp26/lib26.py").read())
import sys
K = float(sys.argv[1]) if len(sys.argv) > 1 else 300
CANDS = {"gender": ["motor", "contents", "buildings"], "previous_insurer": ["motor", "buildings", "contents"], "occ": ["motor", "buildings", "contents"],
         "marketing_segment": ["contents", "motor", "buildings"], "licence_points": ["buildings", "motor", "contents"], "marketing_consent": ["contents"],
         "payment_method": ["buildings"], "region": ["motor", "buildings", "contents"], "campaign_code": ["motor", "buildings", "contents"],
         "email_domain": ["motor", "buildings", "contents"], "branch_id": ["motor", "buildings", "contents"]}
res = {}
for tr_k, te_k in (("DEV23_T2b", "HOLD24_T2b"), ("HOLD24_T2b", "DEV23_T2b")):
    tr, te = sets[tr_k].copy(), sets[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    r = {}
    for v, lines in CANDS.items():
        cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(tr, cl, lines, K); m = aplica_tw(te, f, cl, te.m.values)
        for l in lines:
            for nm, sel in (("REN", te.new_business.values == False), ("NB", te.new_business.values == True), ("ALL", np.ones(len(te), bool))):
                i = (te.line.values == l) & sel; s = te[i]
                r[f"{l}|{v}|{nm}"] = round(d2u(s, nivel_celda(s, m[i])) - d2u(s, nivel_celda(s, s.m.values)), 5)
    res[f"{tr_k[:5]}->{te_k[:6]}"] = r
df = pd.DataFrame(res); df["min"] = df.min(axis=1)
df = df.reset_index(); df[["line", "var", "seg"]] = df["index"].str.split("|", expand=True)
p = df.pivot_table(index=["line", "var"], columns="seg", values=[c for c in df.columns if "->" in c])
p.columns = [f"{a[:5]}{a[-4:]}_{b}" for a, b in p.columns]
p["minALL"] = p[[c for c in p.columns if c.endswith("ALL")]].min(axis=1)
pd.set_option("display.width", 250); print(f"K={K}"); print(p.sort_values("minALL", ascending=False).round(5).to_string())
