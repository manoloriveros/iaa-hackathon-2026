exec(open("__RUN_ROOT__/m017/exp26/lib26.py").read())
import sys
T = "__RUN_ROOT__/ml/trabajo"
KP = 100.0
def fsp_tables():
    out = {}
    for l in ["motor", "buildings", "contents"]:
        f = pd.read_parquet(f"{T}/pred/fsp/{l}.parquet").set_index("row_id")
        per = [c[2:] for c in f.columns if c.startswith("f_")]
        cn = pd.read_parquet(f"{T}/conteos_emerging_{l}.parquet").set_index("row_id")
        be = pd.read_parquet(f"{T}/base_emerging_{l}.parquet", columns=["row_id", "y", "year", "conjunto"] + [f"y_{p}" for p in per]).set_index("row_id")
        out[l] = (f, per, cn, be)
    return out
FT = fsp_tables()
def kappas(l, years):
    f, per, cn, be = FT[l]; tr = be[(be.conjunto == "train") & be.year.astype(int).isin(years)].index
    ef = {p: (f.loc[tr, f"f_{p}"] * f.loc[tr, f"cp_{p}"]).values for p in per}; es = {p: f.loc[tr, f"s_{p}"].values for p in per}
    single = sum(ef[p] * es[p] for p in per); kg = be.loc[tr, "y"].sum() / single.sum(); kap = {}
    for p in per:
        n = cn.loc[tr, f"n_{p}"].values; kf = n.sum() / ef[p].sum(); ks = be.loc[tr, f"y_{p}"].sum() / max((n * es[p]).sum(), 1e-9)
        z = n.sum() / (n.sum() + KP); kap[p] = float(np.exp(z * np.log(max(kf * ks / kg, 1e-3))))
    return kap
def fsp_pred(idx, l, kap, ultimate=False):
    f, per, cn, be = FT[l]
    return sum(kap[p] * f.loc[idx, f"f_{p}"].values * (1.0 if ultimate else f.loc[idx, f"cp_{p}"].values) * f.loc[idx, f"s_{p}"].values for p in per)
def blend(t, m, w, kap_by_line):
    out = m.copy()
    for l in ["motor", "buildings", "contents"]:
        i = (t.line == l).values
        if w[l] == 0: continue
        r = fsp_pred(t.index[i], l, kap_by_line[l])
        r = r * m[i].sum() / r.sum()
        out[i] = np.exp((1 - w[l]) * np.log(m[i]) + w[l] * np.log(r))
    c = celda(t)
    for cc in np.unique(c): j = c == cc; out[j] *= m[j].sum() / out[j].sum()
    return out
SEQ = [("gender", ["motor", "contents"]), ("works_from_home", ["contents"]), ("marketing_segment", ["contents"])]
res = {}
for tr_k, te_k, tr_y in (("DEV23_T2b", "HOLD24_T2b", [2023]), ("DEV23_T2b", "HOLD24_mezcla", [2023]), ("DEV23_T2b", "HOLD24_A1", [2023]), ("HOLD24_T2b", "DEV23_T2b", [2024])):
    tr, te = sets[tr_k].copy(), sets[te_k].copy(); w25 = pesos(te)
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    kap = {l: kappas(l, tr_y) for l in ["motor", "buildings", "contents"]}
    # Estimate factors on the training year's F2-transformed base.
    FAC = []
    trs = tr.copy()
    for v, lines in SEQ:
        cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(trs, cl, lines, 300); trs["m"] = aplica_tw(trs, f, cl, trs.m.values); FAC.append((cl, f))
    def facs(t, m):
        for cl, f in FAC: m = aplica_tw(t, f, cl, m)
        return m
    b0 = te.m.values
    r = {}
    for nm, W in (("w0", 0.0), ("w25", 0.25), ("w40", 0.4), ("w50", 0.5), ("w60", 0.6), ("w75", 0.75)):
        for usefac in (False, True):
            m = blend(te, b0, {"motor": W, "buildings": W, "contents": W}, kap)
            if usefac: m = facs(te, m)
            key = nm + ("+fac" if usefac else "")
            mm = nivel_celda(te, m)
            r[key + "|ALLu"] = round(d2u(te, mm) - d2u(te, nivel_celda(te, b0)), 5)
            r[key + "|w2025"] = round(d2w(te, mm, w25) - d2w(te, nivel_celda(te, b0), w25), 5)
            for l in ["motor", "buildings", "contents"]:
                for seg, s in (("REN", ~te.new_business.values.astype(bool)), ("NB", te.new_business.values.astype(bool))):
                    j = (te.line == l).values & s; tt = te[j]
                    r[f"{key}|{l}_{seg}"] = round(d2u(tt, nivel_celda(tt, m[j])) - d2u(tt, nivel_celda(tt, b0[j])), 5)
    res[f"{tr_k[:5]}->{te_k[:9]}"] = r
    print(tr_k, te_k, flush=True)
df = pd.DataFrame(res); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
df.to_csv("__RUN_ROOT__/m017/exp26/fsp_blend_eval.csv")
print(df.to_string())
