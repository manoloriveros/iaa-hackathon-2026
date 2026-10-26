"""K tarea 4: reconstrucción propia de F4 (y de F3b con pesos 0) desde F2, comprobación de formato, totales, R4 y doble conteo."""
import sys; sys.path.insert(0, "/home/claude/m017/revision")
from K_lib import *

W_ARG = [a for a in sys.argv if a.startswith("--w=")]
WL = dict(zip(LINES, [float(x) for x in W_ARG[0][4:].split(",")])) if W_ARG else {"motor": 0.25, "buildings": 0.25, "contents": 0.5}
WC_ARG = [a for a in sys.argv if a.startswith("--wc=")]   # pesos por celda (orden CELS), sustituye a --w
WC = dict(zip(CELS, [float(x) for x in WC_ARG[0][5:].split(",")])) if WC_ARG else None
RW = [a for a in sys.argv if a.startswith("--rpeso=")]   # peso de 2023 en R4 (0,5 por defecto, como el autor)
R_W23 = float(RW[0][8:]) if RW else 0.5
TAG = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "K_F4_mio"

FT = fsp_tables(""); FP = fsp_tables("_prod")
if WC is not None:
    _blend_line = blend
    def blend(FTx, t, m, w, kap_by_line, ultimate=False, alt=None):
        out = m.copy(); cc_ = celda(t)
        for l in LINES:
            i = (t.line == l).values
            if not i.any(): continue
            wv = np.array([WC[x] for x in cc_[i]])
            if (wv == 0).all(): continue
            r = fsp_pred(FTx, t.index[i], l, kap_by_line[l], ultimate); r = r * m[i].sum() / r.sum()
            out[i] = np.exp((1 - wv) * np.log(m[i]) + wv * np.log(r))
        return keep_cell_sum(t, out, m)
S = base_sets()
sig = json.load(open(R + "/sigma_forma.json")); fuga = json.load(open(R + "/exp26/fuga_celdas.json"))
A_M1 = 1 + sig["motor_1"]["Z_tau0.25"] * (fuga["motor_1"]["sin_nivel"]["vertice"] - 1)

# --- F2: transformación ajustada con el pool 2023+2024 de T2b (para el pool local de factores y las series de R4)
pool = pd.concat([S["DEV23_T2b"], S["HOLD24_T2b"]]).copy()
F1, F2f = f2_fit(pool)
def transformar(t): return f2_apply(t, F1, F2f)
KAPD = {2023: {l: kappa(FT, l, [2024]) for l in LINES}, 2024: {l: kappa(FT, l, [2023]) for l in LINES}}
def blend_local(t, m):
    out = m.copy(); yr = t.year.values.astype(int)
    for y_ in (2023, 2024):
        i = yr == y_
        if i.any(): out[i] = blend(FT, t[i], m[i], WL, KAPD[y_])
    return out
def fm1(t, m): return forma(t, m, {"motor_1": A_M1})
pm = fm1(pool, blend_local(pool, transformar(pool)))
FAC = fit_factors(pool, pm)
# --- R4 (dos años con igual peso por defecto)
raz = {}; razb = {}
for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    s = S[k]; m2 = transformar(s); m0 = fm1(s, m2); mb = fm1(s, blend_local(s, m2)); m1 = apply_factors(s, mb, FAC); c = celda(s); y = s.y.values
    raz[k] = {cc: kopt(y[c == cc], m1[c == cc]) / kopt(y[c == cc], m0[c == cc]) for cc in CELS}
    razb[k] = {cc: kopt(y[c == cc], mb[c == cc]) / kopt(y[c == cc], m0[c == cc]) for cc in CELS}   # solo mezcla
R4 = {cc: R_W23 * raz["DEV23_T2b"][cc] + (1 - R_W23) * np.mean([raz[k][cc] for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]]) for cc in CELS}
Rb = {cc: 0.5 * razb["DEV23_T2b"][cc] + 0.5 * np.mean([razb[k][cc] for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]]) for cc in CELS}
# --- nivel creíble (resolutor propio)
pre = json.load(open(R + "/in/preinscripcion.json")); Bp = pre["base"]; CEL = pre["celdas"]; DED = pre["celda_deducida"]
rec = {r["sha256"]: r["d2"] for r in json.load(open(R + "/recibos_reales_20261026.json"))}
dF = rec[Bp["sha256"]]; g = Bp["g"]; Kp = 1.2
sc = {v["celda"]: rec[v["sha256"]] for v in pre["sondas"].values()}
b_s = {s: Bp["beta_B"] * CEL[s]["cuota_raiz_mu"] for s in CEL}
a_s = {s: (dF - sc[s] - b_s[s] * ((g * Kp) ** 0.5 - g ** 0.5)) / ((g * Kp) ** -0.5 - g ** -0.5) for s in CEL if s != DED}
a_s[DED] = Bp["beta_A"] - sum(a_s.values())
cstar = {s: a_s[s] / b_s[s] for s in CEL}
cred = {s: float(np.clip((cstar[s] / Bp["c_optimo_global"]) ** CEL[s]["Z"], 0.75, 1.33)) for s in CEL}   # relativo a g
# --- 2025
F2p = R + "/F2_ncb_previos_2025.csv"; assert sha(F2p).startswith("119627d9")
F2 = pd.read_csv(F2p, dtype={"row_id": str}); t = LAB.loc[F2.row_id].copy(); t["c_fila"] = 1.0; c = celda(t)
m = F2.prediction.values.copy()
KAPP = {l: kappa(FP, l, [2023, 2024]) for l in LINES}
m = blend(FP, t, m, WL, KAPP, ultimate=True)              # total de ramo y luego de celda = F2
i = c == "motor_1"; ms = fm1(t, m); m[i] = ms[i] * (np.sqrt(m[i]).sum() / np.sqrt(ms[i]).sum()) ** 2
m_pre_fac = m.copy()
m = apply_factors(t, m, FAC)
m_pre_lvl = m.copy()
for cc in CELS: m[c == cc] *= R4[cc] * cred[cc]
out = F2[["row_id"]].copy(); out["prediction"] = m
p = f"{OUT}/{TAG}_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
info = {"archivo": p, "sha256": sha(p), "pesos": WL if WC is None else WC, "A_M1": A_M1, "R4": R4, "R_solo_mezcla": Rb, "raz_por_serie": raz, "raz_mezcla_por_serie": razb,
        "kappa_prod": KAPP, "cred_rel_F": cred, "a_s": a_s, "b_s": b_s, "c_estrella": cstar, "dF": dF, "g": g,
        "factores": {v: {f"{a}|{b}": x for (a, b), x in f.items()} for v, f in FAC},
        "total": float(m.sum()), "total_celda": {cc: float(m[c == cc].sum()) for cc in CELS}}
jdump(info, f"{OUT}/{TAG}_info.json")
np.save(f"{OUT}/{TAG}_etapas.npy", np.vstack([m_pre_fac, m_pre_lvl, m]))
print(TAG, info["sha256"], "R4", {k: round(v, 4) for k, v in R4.items()}, "Rb", {k: round(v, 4) for k, v in Rb.items()})
