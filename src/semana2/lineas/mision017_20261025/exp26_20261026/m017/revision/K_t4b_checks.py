"""K tarea 4b: formato de F4, totales y Σ√ por celda frente a F3b/F2/F, R4 por serie, dilución de los factores de F2, compresión del orden."""
import sys; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *

P4 = R + "/exp26/F4_2025.csv"; P3 = R + "/exp26/F3b_2025.csv"; P2 = R + "/F2_ncb_previos_2025.csv"; PF = R + "/in/final_sonda_global_2025.csv"
raw = open(P4, "rb").read()
F4 = pd.read_csv(P4, dtype={"row_id": str}); F3 = pd.read_csv(P3, dtype={"row_id": str}); F2 = pd.read_csv(P2, dtype={"row_id": str}); F = pd.read_csv(PF, dtype={"row_id": str})
fmt = {"sha256": sha(P4), "filas": len(F4), "cabecera": raw.split(b"\n")[0].decode(), "CR": b"\r" in raw, "termina_LF": raw.endswith(b"\n"),
       "orden_igual_F2": bool((F4.row_id.values == F2.row_id.values).all()), "orden_igual_F3b": bool((F4.row_id.values == F3.row_id.values).all()),
       "ids_unicos": bool(F4.row_id.is_unique), "ids_igual_test": bool(set(F4.row_id) == set(LAB[LAB.conjunto == "test"].index)),
       "finitos": bool(np.isfinite(F4.prediction).all()), "positivos": bool((F4.prediction > 0).all()),
       "min": float(F4.prediction.min()), "max": float(F4.prediction.max()), "total": float(F4.prediction.sum()),
       "igual_reconstruccion_K": sha(P4) == sha(OUT + "/K_F4_mio_2025.csv")}
t = LAB.loc[F4.row_id].copy(); c = celda(t)
tot = {}
for cc in CELS:
    i = c == cc
    a4, a3, a2, a0 = F4.prediction.values[i], F3.prediction.values[i], F2.prediction.values[i], F.prediction.values[i]
    tot[cc] = {"n": int(i.sum()), "suma_F4": round(a4.sum(), 2), "suma_F3b": round(a3.sum(), 2), "F4/F3b_suma": round(a4.sum() / a3.sum(), 5),
               "F4/F3b_raiz": round(np.sqrt(a4).sum() / np.sqrt(a3).sum(), 5), "F4/F2_suma": round(a4.sum() / a2.sum(), 5),
               "s_F4_vs_F": round(np.sqrt(a4).sum() / np.sqrt(a0).sum(), 5), "s_F3b_vs_F": round(np.sqrt(a3).sum() / np.sqrt(a0).sum(), 5),
               "sd_log_F4/F3b": round(float(np.std(np.log(a4 / a3))), 4), "corr_log_tasa_F4_F3b": round(float(np.corrcoef(np.log(a4 / t.exposure.values[i]), np.log(a3 / t.exposure.values[i]))[0, 1]), 4),
               "sd_log_tasa_F2": round(float(np.std(np.log(a2 / t.exposure.values[i]))), 4), "sd_log_tasa_F3b": round(float(np.std(np.log(a3 / t.exposure.values[i]))), 4),
               "sd_log_tasa_F4": round(float(np.std(np.log(a4 / t.exposure.values[i]))), 4)}
info4 = json.load(open(OUT + "/K_F4_mio_info.json")); info3 = json.load(open(OUT + "/K_F3b_mio_info.json"))
# R4: descomposición y sensibilidad al peso por año
r4 = {}
for cc in CELS:
    rs = info4["raz_por_serie"]; rb = info4["raz_mezcla_por_serie"]
    r4[cc] = {"R4": round(info4["R4"][cc], 5), "Rf_F3b": round(info3["R4"][cc], 5), "R4/Rf": round(info4["R4"][cc] / info3["R4"][cc], 5),
              "R_solo_mezcla": round(info4["R_solo_mezcla"][cc], 5),
              "R4_2023": round(rs["DEV23_T2b"][cc], 4), "R4_2024_media3": round(np.mean([rs[k][cc] for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]]), 4),
              "R4_peso_3a1_2024": round(np.mean([rs[k][cc] for k in rs]), 4),
              "mezcla_2023": round(rb["DEV23_T2b"][cc], 4), "mezcla_2024_media3": round(np.mean([rb[k][cc] for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]]), 4)}
# coste/beneficio público exacto del nivel (identidad de J) para F4 frente a F3b y para variantes de R4
a_s, b_s, g = info4["a_s"], info4["b_s"], info4["g"]
A = {s: a_s[s] / np.sqrt(g) for s in CELS}; Bc = {s: b_s[s] * np.sqrt(g) for s in CELS}
def nivel(sv): return sum(A[s] * (1 - 1 / sv[s]) + Bc[s] * (1 - sv[s]) for s in CELS)
s4 = {cc: tot[cc]["s_F4_vs_F"] for cc in CELS}; s3 = {cc: tot[cc]["s_F3b_vs_F"] for cc in CELS}
lev = {"nivel_F3b": nivel(s3), "nivel_F4": nivel(s4), "F4_menos_F3b": nivel(s4) - nivel(s3),
       "s_optimo_sin_G": {s: round(np.sqrt(A[s] / Bc[s]), 5) for s in CELS}, "A": A, "B": Bc}
for nm, key in (("R4_solo_2023", "R4_2023"), ("R4_solo_2024", "R4_2024_media3"), ("R4_3a1", "R4_peso_3a1_2024")):
    sv = {cc: s4[cc] * np.sqrt(r4[cc][key] / r4[cc]["R4"]) for cc in CELS}; lev[nm + "_menos_F4"] = nivel(sv) - nivel(s4)
sv = {cc: s4[cc] * np.sqrt(r4[cc]["Rf_F3b"] / r4[cc]["R4"]) for cc in CELS}; lev["F4_con_Rf_de_F3b_menos_F4"] = nivel(sv) - nivel(s4)
# dilución de los factores NCB / previos de F2 por la mezcla (2025, antes de forma y factores)
et = np.load(OUT + "/K_F4_mio_etapas.npy"); mbf = et[0]          # tras mezcla + forma motor_1
m2 = F2.prediction.values
_FP = fsp_tables("_prod"); _KP = {l: kappa(_FP, l, [2023, 2024]) for l in LINES}
mb = blend(_FP, t, m2, {"motor": 0.25, "buildings": 0.25, "contents": 0.5}, _KP, ultimate=True)   # solo mezcla
dil = {}
f2info = json.load(open(R + "/F2_info.json"))
for nm, key in (("ncb", key_ncb(t)), ("previos", key_prior(t))):
    for cc in CELS:
        i = c == cc; lr = np.log(mb[i] / m2[i]); lr = lr - lr.mean(); kk = key[i]
        for v in np.unique(kk):
            if v == "x": continue
            j = kk == v
            fk = f2info["factores_ncb" if nm == "ncb" else "factores_previos"].get(f"{cc}|{v}")
            dil[f"{nm}|{cc}|{v}"] = {"n": int(j.sum()), "rel_mezcla/F2": round(float(np.exp(lr[j].mean())), 4), "factor_F2": fk,
                                    "factor_F2^-w": round(fk ** -{"motor": 0.25, "buildings": 0.25, "contents": 0.5}[cc.split("_")[0]], 4) if fk else None}
# misma pregunta en datos locales: A/E por nivel de previos tras F2 y tras F2 + mezcla (fuera de tiempo, κ del otro año)
FT = fsp_tables(""); S = base_sets()
pool = pd.concat([S["DEV23_T2b"], S["HOLD24_T2b"]]).copy(); f1, f2 = f2_fit(pool)
WL = {"motor": 0.25, "buildings": 0.25, "contents": 0.5}
KAPD = {2023: {l: kappa(FT, l, [2024]) for l in LINES}, 2024: {l: kappa(FT, l, [2023]) for l in LINES}}
ae = {}
for k_ in ("DEV23_T2b", "HOLD24_T2b"):
    s_ = S[k_]; yy = int(s_.year.iloc[0]); mT = s_.m.values; mF2 = f2_apply(s_, f1, f2); mB = blend(FT, s_, mF2, WL, KAPD[yy]); cs = celda(s_); y = s_.y.values
    for nm, key in (("previos", key_prior(s_)), ("ncb", key_ncb(s_))):
        for cc in CELS:
            i = cs == cc
            for v in np.unique(key[i]):
                if v == "x": continue
                j = i & (key == v)
                ae[f"{k_}|{nm}|{cc}|{v}"] = {"n_pos": int((y[j] > 0).sum()), **{lab: round(float(y[j].sum() / mm[j].sum() / (y[i].sum() / mm[i].sum())), 3) for lab, mm in (("T2b", mT), ("F2", mF2), ("F2+mezcla", mB))}}
# compresión: pendiente de log tasa FSp (prod, κ) sobre log tasa F2 en 2025 por celda y exponente efectivo
FP = fsp_tables("_prod"); KP = {l: kappa(FP, l, [2023, 2024]) for l in LINES}
comp = {}
for cc in CELS:
    l = cc.split("_")[0]; i = c == cc; e = t.exposure.values[i]
    r = fsp_pred(FP, t.index[i], l, KP[l], ultimate=True)
    x = np.log(m2[i] / e); yv = np.log(r / e); beta = float(np.cov(x, yv)[0, 1] / np.var(x, ddof=1))
    w = WL[l]; aeff = 1 - w + w * beta
    xb = np.log(mb[i] / e); xbf = np.log(mbf[i] / e)
    comp[cc] = {"beta_FSp_sobre_F2": round(beta, 4), "corr": round(float(np.corrcoef(x, yv)[0, 1]), 4), "a_eff_mezcla": round(aeff, 4),
                "pendiente_mezcla_sobre_F2": round(float(np.cov(x, xb)[0, 1] / np.var(x, ddof=1)), 4), "pendiente_mezcla+forma_sobre_F2": round(float(np.cov(x, xbf)[0, 1] / np.var(x, ddof=1)), 4),
                "sd_log_tasa_F2": round(float(x.std()), 4), "sd_log_tasa_FSp": round(float(yv.std()), 4), "sd_log_tasa_tras_mezcla": round(float(xb.std()), 4),
                "sd_residuo_ortogonal_w": round(float(w * np.std(yv - beta * x)), 4)}
fuga = json.load(open(R + "/exp26/fuga_celdas.json")); AM1 = info4["A_M1"]
par = {}
for cc in ("motor_1", "buildings_1", "contents_1"):
    v, c2 = fuga[cc]["sin_nivel"]["vertice"], fuga[cc]["sin_nivel"]["curv"]
    a3 = AM1 if cc == "motor_1" else 1.0; a4 = a3 * comp[cc]["a_eff_mezcla"]
    par[cc] = {"vertice": v, "curv": c2, "a_F3b": round(a3, 4), "a_efectivo_F4": round(a4, 4), "coste_publico_compresion": round(c2 * ((a4 - v) ** 2 - (a3 - v) ** 2), 6)}
par["total"] = round(sum(p["coste_publico_compresion"] for p in par.values()), 6)
res = {"formato": fmt, "celdas": tot, "R4": r4, "nivel_publico": lev, "dilucion_2025": dil, "AE_local": ae, "compresion_2025": comp, "parabola_publica": par}
jdump(res, OUT + "/K_t4b_checks.json")
print(json.dumps({k: res[k] for k in ["formato", "celdas", "R4", "nivel_publico", "compresion_2025", "parabola_publica"]}, indent=1, default=float))
for k, v in dil.items(): print("dil", k, v)
for k, v in ae.items(): print("ae", k, v)
