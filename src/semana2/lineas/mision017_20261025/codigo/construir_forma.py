"""Candidato F1: F (mezcla × 1,1877) con corrección NCB y forma en autos, reglas medidas en 2023 y 2024."""
import numpy as np, pandas as pd, json, hashlib
exec(open("ncb_local.py").read().split("res = {}")[0])
FORMA = {"motor_1": 0.5, "motor_0": 0.85}
# factores NCB con 2023 y 2024 juntos (T2b), por tipo de negocio, credibilidad n/(n+300)
pool = pd.concat([sets["DEV23_T2b"], sets["HOLD24_T2b"]])
fN = factores(pool, True)
# razón de nivel tras NCB + forma (conservando el total de la celda), medida en las cuatro series
def transformar(t, fN):
    t2 = t.copy(); t2["m"] = aplicar_ncb(t, fN, True)
    cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values
    for c in ["motor_0", "motor_1"]:
        i = cel == c; t2.loc[i, "m"] = t2.m.values[i] * t.m.values[i].sum() / t2.m.values[i].sum()
    return aplicar(t2, FORMA), cel
razones = {}
for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    t = sets[k]; m2, cel = transformar(t, fN)
    razones[k] = {c: kopt(t.y.values[cel == c], m2[cel == c]) / kopt(t.y.values[cel == c], t.m.values[cel == c]) for c in ["motor_0", "motor_1"]}
R = {c: float(np.mean([razones[k][c] for k in razones])) for c in ["motor_0", "motor_1"]}
# 2025
F = pd.read_csv("in/final_sonda_global_2025.csv", dtype={"row_id": str})
assert hashlib.sha256(open("in/final_sonda_global_2025.csv", "rb").read()).hexdigest().startswith("42659dbb")
t = b.loc[F.row_id].copy(); t["m"] = F.prediction.values; t["c_fila"] = 1.0
m2, cel = transformar(t, fN)
for c, r in R.items(): m2[cel == c] *= r
out = F.copy(); out["prediction"] = m2
assert len(out) == 209063 and np.isfinite(out.prediction).all() and (out.prediction > 0).all() and (out.row_id.values == F.row_id.values).all()
p = "F1_forma_ncb_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
info = {"archivo": p, "sha256": sha, "base": "final_sonda_global_2025.csv (42659dbb…)", "forma": FORMA,
        "factores_ncb": {f"{'NB' if k else 'REN'}|{b_}": round(v, 4) for (k, b_), v in fN.items()},
        "razon_nivel_media": {c: round(v, 4) for c, v in R.items()}, "razon_nivel_por_serie": {k: {c: round(v, 4) for c, v in d.items()} for k, d in razones.items()},
        "total": round(float(out.prediction.sum()), 2), "total_F": round(float(F.prediction.sum()), 2),
        "total_por_celda": {c: round(float(out.prediction.values[cel == c].sum()), 2) for c in sorted(set(cel))},
        "total_F_por_celda": {c: round(float(F.prediction.values[cel == c].sum()), 2) for c in sorted(set(cel))},
        "corr_log_con_F_por_celda": {c: round(float(np.corrcoef(np.log(out.prediction.values[cel == c]), np.log(F.prediction.values[cel == c]))[0, 1]), 4) for c in ["motor_0", "motor_1"]}}
json.dump(info, open("F1_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(info, indent=1, ensure_ascii=False))
