"""K tarea 5b: g_s sin reponderar (todas las filas de la celda, w = 1) y por banda de exposición en NB, para F4-like frente a F3b-like."""
import sys; sys.path.insert(0, "/home/claude/m017/revision")
exec(open("/home/claude/m017/revision/K_t5_public.py").read().split("rng = np.random.default_rng(11)")[0])
rng = np.random.default_rng(12); NB_ = 400
out = {}
for tr_k, te_k, tr_y in DIRS:
    name = f"{tr_k[:5]}->{te_k}"
    tr, te = S[tr_k].copy(), S[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    kap = {l: kappa(FT, l, tr_y) for l in LINES}
    def pipe(wc):
        mtr = forma(tr, blend_cell(tr, tr.m.values, wc, kap), {"motor_1": A_M1}); FACp = fit_factors(tr, mtr)
        return apply_factors(te, forma(te, blend_cell(te, te.m.values, wc, kap), {"motor_1": A_M1}), FACp)
    X3 = pipe({c: 0.0 for c in CELS}); X4 = pipe(VAR["elegido"])
    c = celda(te); y = te.y.values; cust = te.customer_id.values; bd = banda(te.exposure.values)
    for cc in CELS:
        for bn, bm in (("todas", np.ones(len(te), bool)), ("anual", bd == "l"), ("parcial", bd != "l")):
            i = (c == cc) & bm
            if i.sum() < 50: continue
            w1 = np.ones(i.sum()); g = g_rel(y[i], X3[i], X4[i], w1)
            uc, inv = np.unique(cust[i], return_inverse=True); bs = []
            for _ in range(NB_ if bn == "todas" else 200):
                cnt = rng.multinomial(len(uc), np.full(len(uc), 1 / len(uc)))[inv].astype(float); bs.append(g_rel(y[i], X3[i], X4[i], cnt))
            out[f"{name}|{cc}|{bn}"] = {"g_pb": round(g * 1e4, 1), "sd_pb": round(float(np.std(bs)) * 1e4, 1), "n": int(i.sum()), "pos": int((y[i] > 0).sum())}
    print(name, {k.split("|", 1)[1]: v for k, v in out.items() if k.startswith(name)}, flush=True)
jdump(out, OUT + "/K_t5b_g_noponderado.json")
