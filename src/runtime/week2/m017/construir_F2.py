"""Build frozen F2 from the recorded F blend and its 1.1877 level factor.
Estimate motor NCB and all-cell prior_claims_5y factors from pooled 2023-2024 T2b
OOF, separately by business status, with n/(n+300) credibility and fixed cell
totals. Apply motor-renewal shape 0.9 and the recorded correct-scalar local
Tweedie level ratios measured across four series.
"""
import numpy as np, pandas as pd, json, hashlib
exec(open("eval_v2.py").read().split("res = {}")[0])
FORMA = {"motor_0": 0.9}
pool = pd.concat([sets["DEV23_T2b"], sets["HOLD24_T2b"]]); f1 = fac(pool, k_ncb)
t2 = pool.copy(); t2["m"] = aplica(pool, f1, k_ncb); f2 = fac(t2, k_pri)
def transformar(t):
    m = aplica(t, f1, k_ncb); tt = t.copy(); tt["m"] = m; m = aplica(tt, f2, k_pri); tt["m"] = m
    return aplicar(tt, FORMA)
cels = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]
raz = {}
for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    t = sets[k]; m2 = transformar(t); c = celda(t)
    raz[k] = {cc: kopt(t.y.values[c == cc], m2[c == cc]) / kopt(t.y.values[c == cc], t.m.values[c == cc]) for cc in cels}
R = {cc: float(np.mean([raz[k][cc] for k in raz])) for cc in cels}
F = pd.read_csv("in/final_sonda_global_2025.csv", dtype={"row_id": str}); pass
t = b.loc[F.row_id].copy(); t["m"] = F.prediction.values; t["c_fila"] = 1.0
m2 = transformar(t); c = celda(t)
for cc, r in R.items(): m2[c == cc] *= r
out = F.copy(); out["prediction"] = m2
assert len(out) == 209063 and np.isfinite(out.prediction).all() and (out.prediction > 0).all() and (out.row_id.values == F.row_id.values).all()
p = "F2_ncb_previos_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
info = {"archivo": p, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "base": "F 42659dbb…", "forma": FORMA,
        "factores_ncb": {f"{a}|{v}": round(x, 4) for (a, v), x in f1.items() if a.startswith("motor")},
        "factores_previos": {f"{a}|{v}": round(x, 4) for (a, v), x in f2.items()},
        "razon_nivel": {k: round(v, 4) for k, v in R.items()}, "razon_por_serie": {k: {c_: round(v, 4) for c_, v in d.items()} for k, d in raz.items()},
        "total": round(float(m2.sum()), 2), "total_F": round(float(F.prediction.sum()), 2),
        "total_celda": {cc: round(float(m2[c == cc].sum()), 2) for cc in cels}, "total_F_celda": {cc: round(float(F.prediction.values[c == cc].sum()), 2) for cc in cels},
        "evidencia_fuera_de_tiempo": "eval_v2.json: NCB+previos de 2023 aplicados en 2024 con la composición 2025 por celda y banda de exposición: +0,0029 a +0,0031 (T2b, A1, mezcla); de 2024 en 2023: +0,0093"}
json.dump(info, open("F2_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(info, indent=1, ensure_ascii=False))
