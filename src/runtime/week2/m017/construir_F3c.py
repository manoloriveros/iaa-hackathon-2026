"""Reconstruct selected F3c and the historical F4c alternative from the credible base.
F3c applies validated motor/contents gender and contents home-working/marketing
residual factors, preserving cell totals, then their equal-year local level ratio.
Factors and ratios follow F3b. F4c additionally blends FSp using the frozen motor
0.25/contents 0.5 weights while preserving F2's multiplier, then uses F4b factors.
Selection is recorded separately; this script does not submit predictions.
Usage: python construir_F3c.py F3c|F4c
"""
import sys, json, hashlib
QUE = sys.argv[1]
import numpy as np, pandas as pd
src = open("construir_F3b.py" if QUE == "F3c" else "construir_F4b.py").read()
src = src.split("# nivel creíble")[0] if QUE == "F3c" else src.split("# --- nivel creíble")[0]
sys.argv = ["x"]
exec(src)
R = Rf if QUE == "F3c" else R4
FC = "revision/J_final_creible_2025.csv"; pass
fc = pd.read_csv(FC, dtype={"row_id": str})
F2 = pd.read_csv("F2_ncb_previos_2025.csv", dtype={"row_id": str}); assert (fc.row_id.values == F2.row_id.values).all()
t = b.loc[fc.row_id].copy(); t["m"] = fc.prediction.values; t["c_fila"] = 1.0; c = celda(t)
m = fc.prediction.values.copy()
if QUE == "F4c":
    Fb = pd.read_csv("in/final_sonda_global_2025.csv", dtype={"row_id": str}); assert (Fb.row_id.values == fc.row_id.values).all()
    FP = {}
    for l in WL:
        f = pd.read_parquet(f"{T}/pred/fsp/{l}_prod.parquet").set_index("row_id"); per = [c_[2:] for c_ in f.columns if c_.startswith("f_")]
        FP[l] = (f, per, FT[l][2], FT[l][3])
    KAP_P = {}
    for l in WL:
        sv = FT[l]; FT[l] = FP[l]; KAP_P[l] = kappas(l, [2023, 2024]); FT[l] = sv
    for l in WL:
        i = (t.line == l).values
        if WL[l] == 0: continue
        f, per, _, _ = FP[l]; idx = t.index[i]
        r = sum(KAP_P[l][p] * f.loc[idx, f"f_{p}"].values * f.loc[idx, f"s_{p}"].values for p in per)
        mb = Fb.prediction.values[i]; r = r * mb.sum() / r.sum(); m[i] = m[i] * (r / mb) ** WL[l]
    for cc in cels: j = c == cc; m[j] *= fc.prediction.values[j].sum() / m[j].sum()
m = factores(t, m)
for cc in cels: m[c == cc] *= R[cc]
out = fc.copy(); out["prediction"] = m
assert len(out) == 209063 and np.isfinite(m).all() and (m > 0).all()
p = f"exp26/{QUE}_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
info = {"archivo": p, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "base": "final_creible 1a003d86… (público 0,16519)",
        "pasos": ["mezcla FSp (autos 0,25, contenidos 0,5)"] * (QUE == "F4c") + ["factores " + ",".join(v for v, _, _ in FAC)],
        "razon_nivel_factores": {k: round(v, 4) for k, v in R.items()}, "total": round(float(m.sum()), 2),
        "total_celda": {cc: round(float(m[c == cc].sum()), 2) for cc in cels},
        "total_celda_base": {cc: round(float(fc.prediction.values[c == cc].sum()), 2) for cc in cels}}
json.dump(info, open(f"exp26/{QUE}_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(info, indent=1, ensure_ascii=False))
