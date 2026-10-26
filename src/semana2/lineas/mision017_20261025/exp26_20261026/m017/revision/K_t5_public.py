"""K tarea 5: previsión del D² público de F4 frente a F3b.
Identidad (J): D²(X) = D²(F) + Σ_s [A_s(1 − 1/s_s) + B_s(1 − s_s)] + Σ_s G_s/s_s, con s_s = Σ√X_s/Σ√F_s.
- Nivel: exacto con los archivos (K_t4b_checks.json).
- Orden: ΔG_s = G4_s − G3_s ≈ g_s · A_s(F) · (1 − G3_s/A_s), con g_s = reducción relativa de Σ w·y/√m a Σ w·√m fijo, medida fuera de tiempo
  (tubería F4-like frente a F3b-like: F2 → [mezcla] → forma motor_1 → factores reestimados), w = composición 2025 celda × banda.
- Ruido público: bootstrap por cliente de g_s escalado al tamaño efectivo del tercio público de cada celda."""
import sys; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *

FT = fsp_tables(""); S = base_sets()
A_M1 = 1.2977524
chk = json.load(open(OUT + "/K_t4b_checks.json")); Apub = chk["nivel_publico"]["A"]; s4pub = {c: chk["celdas"][c]["s_F4_vs_F"] for c in CELS}
DIRS = [("DEV23_T2b", "HOLD24_T2b", [2023]), ("DEV23_T2b", "HOLD24_mezcla", [2023]), ("DEV23_T2b", "HOLD24_A1", [2023]), ("HOLD24_T2b", "DEV23_T2b", [2024])]
CH = {"motor": 0.25, "buildings": 0.25, "contents": 0.5}
VAR = {"elegido": {c: CH[c.split("_")[0]] for c in CELS},
       "sin_edif": {c: (0.0 if c.startswith("buildings") else CH[c.split("_")[0]]) for c in CELS},
       "solo_REN": {c: (CH[c.split("_")[0]] if c.endswith("_0") else 0.0) for c in CELS},
       "fijo25": {c: 0.25 for c in CELS},
       "elegido_FSpxF2": "especial"}
n25 = pd.Series(celda(LAB[LAB.conjunto == "test"])).value_counts()


def blend_cell(t, m, wc, kap, mult=None):
    out = m.copy(); c = celda(t)
    for l in LINES:
        i = (t.line == l).values
        r = fsp_pred(FT, t.index[i], l, kap[l])
        if mult is not None: r = r * mult[i]
        r = r * m[i].sum() / r.sum(); wv = np.array([wc[x] for x in c[i]])
        out[i] = np.exp((1 - wv) * np.log(m[i]) + wv * np.log(r))
    return keep_cell_sum(t, out, m)


def g_rel(y, x3, x4, w):
    """reducción relativa de Σw·y/√m a Σw·√m fijo"""
    x4p = x4 * (np.sum(w * np.sqrt(x3)) / np.sum(w * np.sqrt(x4))) ** 2
    return 1 - np.sum(w * y / np.sqrt(x4p)) / np.sum(w * y / np.sqrt(x3))


rng = np.random.default_rng(11); NB_ = 400
res = {"g": {}, "sd_boot_g": {}, "neff": {}}
for tr_k, te_k, tr_y in DIRS:
    name = f"{tr_k[:5]}->{te_k}"
    tr, te = S[tr_k].copy(), S[te_k].copy(); T2b_tr, T2b_te = tr.m.values.copy(), te.m.values.copy()
    f1, f2 = f2_fit(tr); tr["m"] = f2_apply(tr, f1, f2); te["m"] = f2_apply(te, f1, f2)
    kap = {l: kappa(FT, l, tr_y) for l in LINES}
    q_tr, q_te = tr.m.values / T2b_tr, te.m.values / T2b_te      # multiplicador de F2 por fila (NCB, previos, forma motor_0)
    def pipe(wc, mult_tr=None, mult_te=None):
        mtr = forma(tr, blend_cell(tr, tr.m.values, wc, kap, mult_tr), {"motor_1": A_M1}); FACp = fit_factors(tr, mtr)
        return apply_factors(te, forma(te, blend_cell(te, te.m.values, wc, kap, mult_te), {"motor_1": A_M1}), FACp)
    X3 = pipe({c: 0.0 for c in CELS})
    w25 = pesos25(te); c = celda(te); y = te.y.values
    cust = te.customer_id.values
    for vn, wc in VAR.items():
        X4 = pipe(VAR["elegido"], q_tr, q_te) if wc == "especial" else pipe(wc)
        for cc in CELS:
            i = c == cc
            res["g"][f"{name}|{vn}|{cc}"] = g_rel(y[i], X3[i], X4[i], w25[i])
            if vn in ("elegido", "sin_edif", "solo_REN") and te_k in ("HOLD24_T2b", "DEV23_T2b"):
                uc, inv = np.unique(cust[i], return_inverse=True); bs = []
                for _ in range(NB_):
                    cnt = rng.multinomial(len(uc), np.full(len(uc), 1 / len(uc)))[inv].astype(float)
                    bs.append(g_rel(y[i], X3[i], X4[i], w25[i] * cnt))
                res["sd_boot_g"][f"{name}|{vn}|{cc}"] = float(np.std(bs))
                ww = w25[i]; res["neff"][f"{name}|{cc}"] = float(ww.sum() ** 2 / (ww ** 2).sum())
    print(name, {k.split("|", 1)[1]: round(v * 1e4, 1) for k, v in res["g"].items() if k.startswith(name) and "|elegido|" in k}, flush=True)

# --- traslado al público
G3 = {"motor_0": 0.0004, "motor_1": 0.0030, "buildings_0": 0.0001, "buildings_1": 0.0003, "contents_0": 0.0002, "contents_1": 0.0006}   # orden de F3b frente a F (aprox., J)
pub = {}
for vn in VAR:
    per_dir = {}
    for tr_k, te_k, _ in DIRS:
        name = f"{tr_k[:5]}->{te_k}"
        per_dir[name] = {cc: res["g"][f"{name}|{vn}|{cc}"] * Apub[cc] * (1 - G3[cc] / Apub[cc]) / s4pub[cc] for cc in CELS}
    d23 = {cc: np.mean([per_dir[n][cc] for n in per_dir if n.startswith("DEV23")]) for cc in CELS}
    d24 = per_dir["HOLD2->DEV23_T2b"]
    mid = {cc: 0.5 * (d23[cc] + d24[cc]) for cc in CELS}
    pub[vn] = {"23->24_media3": {**{k: round(v, 6) for k, v in d23.items()}, "total": round(sum(d23.values()), 6)},
               "24->23": {**{k: round(v, 6) for k, v in d24.items()}, "total": round(sum(d24.values()), 6)},
               "media_direcciones": {**{k: round(v, 6) for k, v in mid.items()}, "total": round(sum(mid.values()), 6)},
               "REN_total": round(sum(mid[c] for c in CELS if c.endswith("_0")), 6), "NB_total": round(sum(mid[c] for c in CELS if c.endswith("_1")), 6)}
# ruido público (tercio aleatorio): sd de g_s escalada a n_pub efectivo
noise = {}
for vn in ("elegido", "sin_edif", "solo_REN"):
    v = 0.0; vloc = 0.0
    for cc in CELS:
        sds = [res["sd_boot_g"][f"{n}|{vn}|{cc}"] * np.sqrt(res["neff"][f"{n}|{cc}"] / (n25[cc] / 3)) for n in ("DEV23->HOLD24_T2b", "HOLD2->DEV23_T2b")]
        v += (np.mean(sds) * Apub[cc] / s4pub[cc]) ** 2
        vloc += np.mean([(res["sd_boot_g"][f"{n}|{vn}|{cc}"] * Apub[cc] / s4pub[cc]) ** 2 for n in ("DEV23->HOLD24_T2b", "HOLD2->DEV23_T2b")])
    noise[vn] = {"sd_publico_realizacion": round(float(np.sqrt(v)), 6), "sd_privado_realizacion": round(float(np.sqrt(v / 2)), 6),
                 "sd_estimacion_local_por_direccion": round(float(np.sqrt(vloc)), 6)}
res["publico_orden"] = pub; res["ruido"] = noise; res["nivel_F4_menos_F3b"] = chk["nivel_publico"]["F4_menos_F3b"]
jdump(res, OUT + "/K_t5_public.json")
print(json.dumps({"publico_orden": pub, "ruido": noise, "nivel": res["nivel_F4_menos_F3b"]}, indent=1))
