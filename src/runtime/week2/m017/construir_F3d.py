"""Reconstruct the historical F3d sensitivity with weaker contents shrinkage.
Keep F3c's motor gender K=300 and use K=60 by default for contents gender,
home-working and marketing. Apply local factor-level ratios with equal year
weights. This preserves the archived alternative, not a new promotion rule.
Usage: python construir_F3d.py [<contents_K>]
"""
import sys, json, hashlib
KCONT = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
import numpy as np, pandas as pd
sys.argv = ["construir_F3b.py", "--sin-factores"]
exec(open("construir_F3b.py").read().split("# nivel creíble")[0])
SEQK = [("gender", ["motor"], 300.0), ("gender", ["contents"], KCONT), ("works_from_home", ["contents"], KCONT), ("marketing_segment", ["contents"], KCONT)]
FAC = []
for v, lines, k in SEQK:
    cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(pool, cl, lines, k)
    pool["m"] = aplica_tw(pool, f, cl, pool.m.values); FAC.append((v, cl, f))
def factores(t, m):
    for v, cl, f in FAC: m = aplica_tw(t, f, cl, m)
    return m
raz = {}
for k_ in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    s_ = sets[k_].copy(); tt = s_.copy(); tt["m"] = transformar(s_); m0 = aplicar(tt, {"motor_1": A_M1}); m1 = factores(s_, m0); c_ = celda(s_)
    raz[k_] = {cc: kopt(s_.y.values[c_ == cc], m1[c_ == cc]) / kopt(s_.y.values[c_ == cc], m0[c_ == cc]) for cc in cels}
R = {cc: 0.5 * raz["DEV23_T2b"][cc] + 0.5 * np.mean([raz[k][cc] for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]]) for cc in cels}
FC = "revision/J_final_creible_2025.csv"; pass
fc = pd.read_csv(FC, dtype={"row_id": str}); t = b.loc[fc.row_id].copy(); t["m"] = fc.prediction.values; t["c_fila"] = 1.0; c = celda(t)
m = factores(t, fc.prediction.values.copy())
for cc in cels: m[c == cc] *= R[cc]
out = fc.copy(); out["prediction"] = m; assert len(out) == 209063 and np.isfinite(m).all() and (m > 0).all()
tag = "F3d" + ("" if KCONT == 60 else f"_Kc{int(KCONT)}")
p = f"exp26/{tag}_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
f3c = pd.read_csv("exp26/F3c_2025.csv", dtype={"row_id": str})
info = {"archivo": p, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "K_contenidos": KCONT, "K_autos": 300,
        "factores": {f"{v}|{','.join(sorted(set(a for (a, g_, vv) in f)))}": {f"{a}|{vv}": round(x, 4) for (a, g_, vv), x in f.items()} for v, cl, f in FAC},
        "razon_nivel": {k: round(v, 4) for k, v in R.items()}, "total": round(float(m.sum()), 2),
        "total_celda": {cc: round(float(m[c == cc].sum()), 2) for cc in cels},
        "corr_log_F3c_contenidos": round(float(np.corrcoef(np.log(m[t.line.values == "contents"]), np.log(f3c.prediction.values[t.line.values == "contents"]))[0, 1]), 4),
        "igual_F3c_fuera_de_contenidos": bool(np.allclose(m[t.line.values != "contents"], f3c.prediction.values[t.line.values != "contents"], rtol=2e-6))}
json.dump(info, open(f"exp26/{tag}_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(info, indent=1, ensure_ascii=False))
