"""K tarea 5c: parte ortogonal de la mezcla en la tubería (F4-like frente a F4-like con la mezcla sustituida por compresión pura
F2^a_eff, a_eff = 1 − w + wβ por celda), sin reponderar y con composición 2025."""
import sys; sys.path.insert(0, "/home/claude/m017/revision")
exec(open("/home/claude/m017/revision/K_t5_public.py").read().split("rng = np.random.default_rng(11)")[0])
out = {}
for tr_k, te_k, tr_y in DIRS:
    name = f"{tr_k[:5]}->{te_k}"
    tr, te = S[tr_k].copy(), S[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    kap = {l: kappa(FT, l, tr_y) for l in LINES}
    def aeff(t, m):
        fs = np.zeros(len(t)); c = celda(t)
        for l in LINES: i = (t.line == l).values; fs[i] = fsp_pred(FT, t.index[i], l, kap[l])
        a = {}
        for cc in CELS:
            i = c == cc; e = t.exposure.values[i] * t.c_fila.values[i]; x = np.log(m[i] / e); yv = np.log(fs[i] / e)
            a[cc] = 1 - VAR["elegido"][cc] + VAR["elegido"][cc] * float(np.cov(x, yv)[0, 1] / np.var(x, ddof=1))
        return a
    a_tr, a_te = aeff(tr, tr.m.values), aeff(te, te.m.values)
    def pipe(kind):
        if kind == "F3b": btr, bte = tr.m.values, te.m.values
        elif kind == "F4": btr, bte = blend_cell(tr, tr.m.values, VAR["elegido"], kap), blend_cell(te, te.m.values, VAR["elegido"], kap)
        else: btr, bte = forma(tr, tr.m.values, a_tr), forma(te, te.m.values, a_te)
        mtr = forma(tr, btr, {"motor_1": A_M1}); FACp = fit_factors(tr, mtr)
        return apply_factors(te, forma(te, bte, {"motor_1": A_M1}), FACp)
    X3, X4, X4c = pipe("F3b"), pipe("F4"), pipe("comp")
    c = celda(te); y = te.y.values; w25 = pesos25(te)
    for cc in CELS:
        i = c == cc
        for wn, ww in (("u", np.ones(i.sum())), ("w2025", w25[i])):
            out[f"{name}|{cc}|{wn}"] = {"g_total_pb": round(g_rel(y[i], X3[i], X4[i], ww) * 1e4, 1), "g_compresion_pb": round(g_rel(y[i], X3[i], X4c[i], ww) * 1e4, 1),
                                         "g_ortogonal_pb": round(g_rel(y[i], X4c[i], X4[i], ww) * 1e4, 1), "a_eff": round(a_te[cc], 3)}
    print(name, {k.split("|", 1)[1]: v for k, v in out.items() if k.startswith(name) and k.endswith("|u")}, flush=True)
jdump(out, OUT + "/K_t5c_ortogonal.json")
