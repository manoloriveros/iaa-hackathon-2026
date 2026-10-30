"""Reconstruct the historical F4b frequency-severity blend alternative.
Blend transferred FSp geometrically using recorded line weights (0.25 motor,
0.25 buildings, 0.5 contents), credible peril calibration n/(n+100), and fixed
cell totals. Apply F2, FSp blend, motor new-business shape, residual factors,
local level ratios and credible cell levels in that order. Preserve F2's multiplier.
Usage: python construir_F4b.py [--w=m,b,c] [--sin-factores]
"""
import sys, json, hashlib
argv = sys.argv[:]; sys.argv = ["x", "--prueba"]
import numpy as np, pandas as pd
exec(open("exp26/lib26.py").read())
exec(open("construir_final.py").read())
exec(open("exp26/fsp_blend_eval.py").read().split("SEQ = [")[0].split('exec(open("__RUN_ROOT__/m017/exp26/lib26.py").read())')[1])
sys.argv = argv
wa = [a for a in sys.argv if a.startswith("--w=")]
WM, WB, WC = [float(x) for x in wa[0][4:].split(",")] if wa else (0.25, 0.0, 0.5)
WL = {"motor": WM, "buildings": WB, "contents": WC}
SIN_F = "--sin-factores" in sys.argv
SEQ = [] if SIN_F else [("gender", ["motor", "contents"]), ("works_from_home", ["contents"]), ("marketing_segment", ["contents"])]
FUGA = json.load(open("exp26/fuga_celdas.json"))
A_M1 = 1 + SIG["motor_1"]["Z_tau0.25"] * (FUGA["motor_1"]["sin_nivel"]["vertice"] - 1)
cels = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]
# Fit factors on the local F2, out-of-time FSp blend and shape pool.
KAP_DEV = {2023: {l: kappas(l, [2024]) for l in WL}, 2024: {l: kappas(l, [2023]) for l in WL}}   # Peril calibration kappa from the other year.
def blend_local(t, m, mbase=None):
    """Blend FSp geometrically while preserving the F2 multiplier m/mbase."""
    mbase = t.m.values if mbase is None else mbase
    out = m.copy(); yr = t.year.values.astype(int)
    for y_ in (2023, 2024):
        for l in WL:
            i = (yr == y_) & (t.line.values == l)
            if not i.any() or WL[l] == 0: continue
            r = fsp_pred(t.index[i], l, KAP_DEV[y_][l]); r = r * mbase[i].sum() / r.sum()
            out[i] = m[i] * (r / mbase[i]) ** WL[l]
    c_ = celda(t)
    for cc in np.unique(c_): j = c_ == cc; out[j] *= m[j].sum() / out[j].sum()
    return out
def forma(t, m):
    tt = t.copy(); tt["m"] = m; return aplicar(tt, {"motor_1": A_M1})
pool = pd.concat([sets["DEV23_T2b"], sets["HOLD24_T2b"]]).copy()
pool["m"] = forma(pool, blend_local(pool, transformar(pool)))
FAC = []
for v, lines in SEQ:
    cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(pool, cl, lines, 300)
    pool["m"] = aplica_tw(pool, f, cl, pool.m.values); FAC.append((v, cl, f))
def factores(t, m):
    for v, cl, f in FAC: m = aplica_tw(t, f, cl, m)
    return m
# Compare local level before (F2 plus shape) and after blend, shape and factors.
raz = {}
for k_ in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    s_ = sets[k_].copy(); m2 = transformar(s_)
    m0 = forma(s_, m2); m1 = factores(s_, forma(s_, m2)); c_ = celda(s_)   # Factor-only ratio; the historical blend ratio was treated as noise.
    raz[k_] = {cc: kopt(s_.y.values[c_ == cc], m1[c_ == cc]) / kopt(s_.y.values[c_ == cc], m0[c_ == cc]) for cc in cels}
R4 = {cc: 0.5 * raz["DEV23_T2b"][cc] + 0.5 * np.mean([raz[k][cc] for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]]) for cc in cels}
# Credibility-weighted level.
sc = {}
for r in json.load(open("recibos_reales_20261026.json")):
    if r["sha256"] in nombre_sha:
        tipo, cual = nombre_sha[r["sha256"]]; sc[tipo if cual is None else (tipo, cual)] = float(r["d2"])
lv = resolver(sc)
# Production FSp uses developed 2021-2024, kappa from 2023-2024 and ultimate completeness 1.
FP = {}
for l in WL:
    f = pd.read_parquet(f"{T}/pred/fsp/{l}_prod.parquet").set_index("row_id"); per = [c[2:] for c in f.columns if c.startswith("f_")]
    FP[l] = (f, per, FT[l][2], FT[l][3])
KAP_P = {}
for l in WL:
    FT_save = FT[l]; FT[l] = FP[l]; KAP_P[l] = kappas(l, [2023, 2024]); FT[l] = FT_save
F2 = pd.read_csv("F2_ncb_previos_2025.csv", dtype={"row_id": str}); pass
t = b.loc[F2.row_id].copy(); t["m"] = F2.prediction.values; t["c_fila"] = 1.0; c = celda(t)
Fb = pd.read_csv("in/final_sonda_global_2025.csv", dtype={"row_id": str}); assert (Fb.row_id.values == F2.row_id.values).all()
m = F2.prediction.values.copy()
for l in WL:
    i = (t.line == l).values
    if WL[l] == 0: continue
    f, per, _, _ = FP[l]; idx = t.index[i]
    r = sum(KAP_P[l][p] * f.loc[idx, f"f_{p}"].values * f.loc[idx, f"s_{p}"].values for p in per)
    mb = Fb.prediction.values[i]; r = r * mb.sum() / r.sum(); m[i] = m[i] * (r / mb) ** WL[l]
for cc in cels: j = c == cc; m[j] *= F2.prediction.values[j].sum() / m[j].sum()
i = c == "motor_1"; ms = forma(t, m); m[i] = ms[i] * (np.sqrt(m[i]).sum() / np.sqrt(ms[i]).sum()) ** 2
m = factores(t, m)
for cc in cels: m[c == cc] *= R4[cc] * lv["cred"][cc] / lv["g"]
out = F2.copy(); out["prediction"] = m
assert len(out) == 209063 and np.isfinite(m).all() and (m > 0).all()
tag = "F4b" + ("_sinfac" if SIN_F else "") + ("" if not wa else "_w" + wa[0][4:].replace(",", "-"))
p = f"exp26/{tag}_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
info = {"archivo": p, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "pesos_fsp": WL, "a_motor_1": A_M1, "seq": [v for v, _ in SEQ],
        "kappa_prod": {l: {p_: round(v, 3) for p_, v in d.items()} for l, d in KAP_P.items()},
        "razon_nivel": {k: round(v, 4) for k, v in R4.items()}, "razon_por_serie": {k: {c_: round(v, 4) for c_, v in d.items()} for k, d in raz.items()},
        "nivel_cred_rel_F": {k: round(v / lv["g"], 4) for k, v in lv["cred"].items()},
        "total": round(float(m.sum()), 2), "total_celda": {cc: round(float(m[c == cc].sum()), 2) for cc in cels},
        "corr_log_F2": {cc: round(float(np.corrcoef(np.log(m[c == cc] / t.exposure.values[c == cc]), np.log(F2.prediction.values[c == cc] / t.exposure.values[c == cc]))[0, 1]), 4) for cc in cels}}
json.dump(info, open(f"exp26/{tag}_info.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in info.items() if k != "razon_por_serie"}, indent=1, ensure_ascii=False))
