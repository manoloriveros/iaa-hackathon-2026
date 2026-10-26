"""K tarea 3: placebos y descomposición de la ganancia de la mezcla FSp (sin factores y dado factores).
V0 FSp con κ (real) · V1 FSp con κ = 1 · V2 κ permutados entre peligros (nulo de κ) · V3 mezcla con T2c (otro árbol transferido)
V4 compresión pura (F2^a_eff por celda, a_eff = 1 − w + wβ, β = pendiente de log tasa FSp sobre log tasa F2) · V5 F2 × (rec/single)^w (solo canal κ)."""
import sys, itertools; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *

FT = fsp_tables("")
S = base_sets(extra=("T2c",))
CH = {"motor": 0.25, "buildings": 0.25, "contents": 0.5}
DIRS = [("DEV23_T2b", "HOLD24_T2b", [2023], "HOLD24_T2c"), ("DEV23_T2b", "HOLD24_A1", [2023], "HOLD24_T2c"), ("HOLD24_T2b", "DEV23_T2b", [2024], "DEV23_T2c")]
rng = np.random.default_rng(7)
NPERM = 200


def comps(te, l):
    D = FT[l]; f = D["f"].loc[te.index[(te.line == l).values]]
    return {p: f[f"f_{p}"].values * f[f"cp_{p}"].values * f[f"s_{p}"].values for p in D["per"]}


def geo(te, m, rvec_by_line, w):
    out = m.copy()
    for l in LINES:
        i = (te.line == l).values
        if w[l] == 0: continue
        r = rvec_by_line[l] * m[i].sum() / rvec_by_line[l].sum()
        out[i] = np.exp((1 - w[l]) * np.log(m[i]) + w[l] * np.log(r))
    return keep_cell_sum(te, out, m)


def segs(te):
    nb = te.new_business.values; w = pesos25(te)
    out = {"ALLu": (None, None), "w2025": (None, w), "NB": (nb, None), "NB_w2025": (nb, w), "REN": (~nb, None)}
    for l in LINES: out[l] = ((te.line == l).values, None); out[l + "_w2025"] = ((te.line == l).values, w)
    return out


def met(te, m, SG): return {k: d2_lev(te, m, msk, w) for k, (msk, w) in SG.items()}


def slope(te, m, r, cc):
    c = celda(te); i = c == cc; e = te.exposure.values[i] * te.c_fila.values[i]
    x = np.log(m[i] / e); y_ = np.log(r[i] / e)
    return float(np.cov(x, y_)[0, 1] / np.var(x, ddof=1)), float(np.corrcoef(x, y_)[0, 1])


res = {}
for tr_k, te_k, tr_y, alt_k in DIRS:
    name = f"{tr_k[:5]}->{te_k}"
    tr, te = S[tr_k].copy(), S[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    FAC = fit_factors(tr, tr.m.values)
    b0 = te.m.values.copy(); SG = segs(te); base = met(te, b0, SG); mf0 = apply_factors(te, b0, FAC); basef = met(te, mf0, SG)
    kap = {l: kappa(FT, l, tr_y) for l in LINES}
    C = {l: comps(te, l) for l in LINES}
    single = {l: sum(C[l].values()) for l in LINES}
    rec = {l: sum(kap[l][p] * C[l][p] for p in C[l]) for l in LINES}
    alt = S[alt_k].m.reindex(te.index).values
    altv = {l: alt[(te.line == l).values] for l in LINES}
    r = {}
    def add(nm, m):
        a = met(te, m, SG); af = met(te, apply_factors(te, m, FAC), SG)
        r[nm] = {"sin_fac": {k: round(a[k] - base[k], 5) for k in a}, "dado_fac": {k: round(af[k] - basef[k], 5) for k in af}}
        return a
    for wn, W in (("elegido", CH), ("fijo25", {l: 0.25 for l in LINES})):
        add(f"V0_FSp_kappa|{wn}", geo(te, b0, rec, W))
        add(f"V1_FSp_kappa1|{wn}", geo(te, b0, single, W))
        add(f"V3_T2c|{wn}", geo(te, b0, altv, W))
        # V4 compresión pura con la pendiente β de la FSp real (κ) sobre F2, por celda
        fs_full = np.zeros(len(te))
        for l in LINES: fs_full[(te.line == l).values] = rec[l]
        aeff = {}; beta = {}
        for cc in CELS:
            l = cc.split("_")[0]; bt, rho = slope(te, b0, fs_full, cc); beta[cc] = (round(bt, 3), round(rho, 3)); aeff[cc] = 1 - W[l] + W[l] * bt
        r[f"beta_rho|{wn}"] = beta; r[f"a_eff|{wn}"] = {k: round(v, 3) for k, v in aeff.items()}
        add(f"V4_compresion|{wn}", forma(te, b0, aeff))
        # V5 canal κ sobre F2: m × (rec/single)^w
        corr = {l: b0[(te.line == l).values] * rec[l] / single[l] for l in LINES}
        add(f"V5_F2xcorr|{wn}", geo(te, b0, corr, W))
        # V2 nulo de κ: permutaciones de κ entre peligros dentro del ramo
        null = []
        for _ in range(NPERM):
            rp = {}
            for l in LINES:
                per = list(C[l].keys()); vals = [kap[l][p] for p in per]; pv = rng.permutation(vals)
                rp[l] = sum(pv[j] * C[l][per[j]] for j in range(len(per)))
            mm = geo(te, b0, rp, W); a = met(te, mm, SG)
            null.append({k: a[k] - base[k] for k in ("ALLu", "w2025", "NB", "REN", "motor", "buildings", "contents")})
        nd = pd.DataFrame(null)
        r[f"V2_kappa_permutado|{wn}"] = {k: {"media": round(nd[k].mean(), 5), "p05": round(nd[k].quantile(0.05), 5), "p95": round(nd[k].quantile(0.95), 5),
                                              "rango_real": round(float((nd[k] < r[f"V0_FSp_kappa|{wn}"]["sin_fac"][k]).mean()), 3)} for k in nd.columns}
    res[name] = r
    print(name, json.dumps({k: v["sin_fac"] if isinstance(v, dict) and "sin_fac" in v else v for k, v in r.items() if "elegido" in k}, indent=0)[:4000], flush=True)
jdump(res, OUT + "/K_t3_placebo.json")
