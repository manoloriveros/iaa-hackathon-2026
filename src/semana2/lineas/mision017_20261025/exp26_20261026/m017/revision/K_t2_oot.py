"""K tarea 2: ganancia fuera de tiempo de la mezcla FSp (implementación propia), por ramo y NB/renovación, en ambas direcciones;
selección de pesos (fijo 0,25, elegido 0,25/0,25/0,5, mejor a posteriori, selección cruzada entre direcciones);
bootstrap por cliente (conjunto para las dos direcciones). Guarda también las predicciones para las tareas 3 y 5."""
import sys, pickle; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *

FT = fsp_tables("")
S = base_sets()
A_M1 = 1.2977524   # forma de motor_1 de F3b/F4 (comprobada en la tarea 4)
DIRS = [("DEV23_T2b", "HOLD24_T2b", [2023]), ("DEV23_T2b", "HOLD24_mezcla", [2023]), ("DEV23_T2b", "HOLD24_A1", [2023]), ("HOLD24_T2b", "DEV23_T2b", [2024])]
WGRID = [0.0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75]
CHOSEN = {"motor": 0.25, "buildings": 0.25, "contents": 0.5}


def segs(te):
    nb = te.new_business.values
    out = {"ALLu": (np.ones(len(te), bool), None), "w2025": (np.ones(len(te), bool), pesos25(te)),
           "NB": (nb, None), "REN": (~nb, None), "NB_w2025": (nb, pesos25(te))}
    for l in LINES:
        for s, msk in (("REN", ~nb), ("NB", nb)):
            out[f"{l}_{s}"] = ((te.line.values == l) & msk, None)
    return out


def metrics(te, m, SG):
    return {k: d2_lev(te, m, msk, w) for k, (msk, w) in SG.items()}


def line_contrib(te, m, m_ref, l, w=None, mask=None):
    """contribución exacta del ramo l a la ganancia de D² del conjunto (las celdas son disjuntas)"""
    mask = np.ones(len(te), bool) if mask is None else mask
    y = te.y.values; c = celda(te); ww = np.ones(len(te)) if w is None else w
    mu0 = np.sum(ww[mask] * y[mask]) / np.sum(ww[mask]); null = np.sum(ww[mask] * dev(y[mask], np.full(mask.sum(), mu0)))
    d = 0.0
    for cc in [x for x in CELS if x.startswith(l)]:
        i = (c == cc) & mask
        if not i.any(): continue
        k1, k0 = kopt(y[i], m[i]), kopt(y[i], m_ref[i])
        d += np.sum(ww[i] * (dev(y[i], k0 * m_ref[i]) - dev(y[i], k1 * m[i])))
    return d / null


res = {"repro_autor": {}, "elegidos": {}, "contrib_ramo": {}, "pipeline_F4": {}}
PRED = {}
for tr_k, te_k, tr_y in DIRS:
    name = f"{tr_k[:5]}->{te_k}"
    tr, te = S[tr_k].copy(), S[te_k].copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    kap = {l: kappa(FT, l, tr_y) for l in LINES}
    FAC = fit_factors(tr, tr.m.values)
    b0 = te.m.values.copy(); SG = segs(te)
    base = metrics(te, b0, SG)
    mf0 = apply_factors(te, b0, FAC); basef = metrics(te, mf0, SG)
    # (i) réplica de la tabla del autor: pesos uniformes, ganancia frente a F2 sin factores
    rep = {}
    for W in [0.0, 0.25, 0.5]:
        mb = blend(FT, te, b0, {l: W for l in LINES}, kap); mbf = apply_factors(te, mb, FAC)
        for nm, mm in ((f"w{int(W*100)}", mb), (f"w{int(W*100)}+fac", mbf)):
            mt = metrics(te, mm, SG)
            for k in ["ALLu", "w2025"] + [f"{l}_{s}" for l in LINES for s in ("REN", "NB")]:
                rep[f"{nm}|{k}"] = round(mt[k] - base[k], 5)
    res["repro_autor"][name] = rep
    # (ii) pesos elegidos y alternativas, sin y con factores; incremento de la FSp dado factores
    cfgs = {"elegido_25_25_50": CHOSEN, "fijo_25": {l: 0.25 for l in LINES}, "sin_edif_25_0_50": {"motor": 0.25, "buildings": 0.0, "contents": 0.5},
            "fijo_50": {l: 0.5 for l in LINES}}
    el = {}
    for cn_, W in cfgs.items():
        mb = blend(FT, te, b0, W, kap); mbf = apply_factors(te, mb, FAC)
        mt, mtf = metrics(te, mb, SG), metrics(te, mbf, SG)
        el[cn_] = {"sin_factores": {k: round(mt[k] - base[k], 5) for k in mt}, "con_factores_vs_F2": {k: round(mtf[k] - base[k], 5) for k in mtf},
                   "incremento_FSp_dado_factores": {k: round(mtf[k] - basef[k], 5) for k in mtf}}
        if te_k in ("HOLD24_T2b", "DEV23_T2b"): PRED[(name, cn_)] = (mb, mbf)
    el["solo_factores_vs_F2"] = {k: round(basef[k] - base[k], 5) for k in basef}
    res["elegidos"][name] = el
    if te_k in ("HOLD24_T2b", "DEV23_T2b"):
        PRED[(name, "base")] = (b0, mf0); PRED[(name, "te")] = te; PRED[(name, "kap")] = kap; PRED[(name, "FAC")] = FAC
    # (iii) contribución por ramo para la rejilla de pesos (con factores, incremento dado factores)
    cr = {}
    for l in LINES:
        for W in WGRID:
            Wd = {x: (W if x == l else 0.0) for x in LINES}
            mbf = apply_factors(te, blend(FT, te, b0, Wd, kap), FAC)
            cr[f"{l}|{W}|ALLu"] = line_contrib(te, mbf, mf0, l)
            cr[f"{l}|{W}|w2025"] = line_contrib(te, mbf, mf0, l, w=pesos25(te))
            cr[f"{l}|{W}|NB"] = line_contrib(te, mbf, mf0, l, mask=te.new_business.values)
    res["contrib_ramo"][name] = cr
    # (iv) tubería fiel a F4: F2 -> [mezcla] -> forma motor_1 (a = 1,2978) -> factores reestimados en el año de entrenamiento
    #      sobre su propia base (con κ del propio año de entrenamiento); comparación con F3b-like (sin mezcla)
    kap_tr = kap
    trb0 = tr.m.values
    pf = {}
    for cn_, W in (("F3b_like", {l: 0.0 for l in LINES}), ("F4_like", CHOSEN), ("F4_like_sin_edif", {"motor": 0.25, "buildings": 0.0, "contents": 0.5}), ("F4_like_fijo25", {l: 0.25 for l in LINES})):
        mtr = forma(tr, blend(FT, tr, trb0, W, kap_tr), {"motor_1": A_M1}); FACp = fit_factors(tr, mtr)
        mte = apply_factors(te, forma(te, blend(FT, te, b0, W, kap), {"motor_1": A_M1}), FACp)
        pf[cn_] = metrics(te, mte, SG)
        if te_k in ("HOLD24_T2b", "DEV23_T2b"): PRED[(name, "pipe_" + cn_)] = mte
    res["pipeline_F4"][name] = {cn_: {k: round(v[k] - pf["F3b_like"][k], 5) for k in v} for cn_, v in pf.items() if cn_ != "F3b_like"}
    res["pipeline_F4"][name]["F3b_like_vs_F2"] = {k: round(pf["F3b_like"][k] - base[k], 5) for k in base}
    print(name, "listo", flush=True)

# --- selección de pesos por ramo
sel = {}
dirs = list(res["contrib_ramo"].keys()); main = [d for d in dirs if d.endswith("HOLD24_T2b") or d.endswith("DEV23_T2b")]
for met in ("ALLu", "w2025", "NB"):
    tab = {l: {W: {d: res["contrib_ramo"][d][f"{l}|{W}|{met}"] for d in dirs} for W in WGRID} for l in LINES}
    def g(Wd, d): return sum(tab[l][Wd[l]][d] for l in LINES)
    # promedio de las dos direcciones principales; 23->24 se resume con la media de sus tres bases
    def two(Wd):
        a = np.mean([g(Wd, d) for d in dirs if d.startswith("DEV23")]); b_ = g(Wd, [d for d in dirs if d.startswith("HOLD2")][0]); return a, b_, (a + b_) / 2
    best = {l: max(WGRID, key=lambda W: np.mean([np.mean([tab[l][W][d] for d in dirs if d.startswith("DEV23")]), tab[l][W][[d for d in dirs if d.startswith("HOLD2")][0]]])) for l in LINES}
    best23 = {l: max(WGRID, key=lambda W: np.mean([tab[l][W][d] for d in dirs if d.startswith("DEV23")])) for l in LINES}
    best24 = {l: max(WGRID, key=lambda W: tab[l][W][[d for d in dirs if d.startswith("HOLD2")][0]]) for l in LINES}
    out = {"elegido": two(CHOSEN), "fijo_25": two({l: 0.25 for l in LINES}), "mejor_a_posteriori": (best, two(best)),
           "cruzado_elige23_evalua24": (best23, two(best23)[1]), "cruzado_elige24_evalua23": (best24, two(best24)[0]),
           "sin_edif": two({"motor": 0.25, "buildings": 0.0, "contents": 0.5})}
    out["por_ramo"] = {l: {str(W): [round(np.mean([tab[l][W][d] for d in dirs if d.startswith("DEV23")]), 5), round(tab[l][W][[d for d in dirs if d.startswith("HOLD2")][0]], 5)] for W in WGRID} for l in LINES}
    sel[met] = out
res["seleccion_pesos"] = sel

# --- bootstrap por cliente (direcciones T2b), remuestreo conjunto de clientes
rng = np.random.default_rng(20261025)
d23, d24 = "DEV23->HOLD24_T2b", "HOLD2->DEV23_T2b"
allc = pd.Index(sorted(set(PRED[(d23, "te")].customer_id) | set(PRED[(d24, "te")].customer_id)))
B = 1000
Wc = rng.multinomial(len(allc), np.full(len(allc), 1 / len(allc)), size=B).astype(np.float32)   # B × clientes


def agg(te, m, w=None):
    """sumas por cliente × celda: S1=Σy/√m, S2=Σ√m (sin ponderar, para el nivel) y S1w,S2w,S3w,Syw,nw (ponderadas) para desviación y nulo"""
    ci = allc.get_indexer(te.customer_id.values); c = pd.Categorical(celda(te), categories=CELS).codes
    ww = np.ones(len(te)) if w is None else w; y = te.y.values; sm = np.sqrt(m)
    st = [y / sm, sm, ww * y / sm, ww * sm, ww * np.sqrt(y), ww * y, ww]
    A = np.zeros((len(allc), len(CELS), len(st)))
    for j, v in enumerate(st): np.add.at(A[:, :, j], (ci, c), v)
    return A


def bootX(A):
    return (Wc @ A.reshape(A.shape[0], -1).astype(np.float32)).astype(np.float64).reshape(Wc.shape[0], A.shape[1], A.shape[2])


def d2_boot(X, cells_mask):
    """D² nivelado por celda para cada réplica: X (réplicas × celdas × 7)"""
    X = X[:, cells_mask, :]
    S1, S2, S1w, S2w, S3w, Syw, nw = [X[:, :, j] for j in range(7)]
    k = np.where(S2 > 0, S1 / np.maximum(S2, 1e-12), 1.0); k = np.maximum(k, 1e-12)
    num = (4 * S1w / np.sqrt(k) + 4 * np.sqrt(k) * S2w - 8 * S3w).sum(1)
    ybar = Syw.sum(1) / nw.sum(1); null = 8 * np.sqrt(ybar) * nw.sum(1) - 8 * S3w.sum(1)
    return 1 - num / null


boot = {}
_cache = {}
def XX(d, key, m, wname):
    if (d, key, wname) not in _cache:
        te = PRED[(d, "te")]; _cache[(d, key, wname)] = bootX(agg(te, m, pesos25(te) if wname == "w2025" else None))
    return _cache[(d, key, wname)]
for cfg in ("elegido_25_25_50", "fijo_25", "sin_edif_25_0_50"):
    for wname in ("u", "w2025"):
        for segname, cm in (("ALL", np.ones(6, bool)), ("NB", np.array([c.endswith("_1") for c in CELS])), ("REN", np.array([c.endswith("_0") for c in CELS]))):
            g = {}
            for d in (d23, d24):
                b0, mf0 = PRED[(d, "base")]; mb, mbf = PRED[(d, cfg)]
                g[d + "|sin_fac"] = d2_boot(XX(d, cfg + "b", mb, wname), cm) - d2_boot(XX(d, "b0", b0, wname), cm)
                g[d + "|inc_dado_fac"] = d2_boot(XX(d, cfg + "bf", mbf, wname), cm) - d2_boot(XX(d, "mf0", mf0, wname), cm)
            for kind in ("sin_fac", "inc_dado_fac"):
                comb = 0.5 * (g[d23 + "|" + kind] + g[d24 + "|" + kind])
                for lab, v in ((d23, g[d23 + "|" + kind]), (d24, g[d24 + "|" + kind]), ("combinada", comb)):
                    boot[f"{cfg}|{wname}|{segname}|{kind}|{lab}"] = {"media": round(float(v.mean()), 5), "sd": round(float(v.std()), 5),
                                                                       "p05": round(float(np.quantile(v, 0.05)), 5), "p95": round(float(np.quantile(v, 0.95)), 5),
                                                                       "P(<0)": round(float((v < 0).mean()), 3)}
    print("bootstrap", cfg, flush=True)
res["bootstrap"] = boot
res["bootstrap_B"] = B
jdump(res, OUT + "/K_t2_oot.json")
pickle.dump({k: v for k, v in PRED.items()}, open(OUT + "/K_t2_pred.pkl", "wb"))
print(json.dumps(res["elegidos"]["DEV23->HOLD24_T2b"]["elegido_25_25_50"], indent=0)[:3000])
