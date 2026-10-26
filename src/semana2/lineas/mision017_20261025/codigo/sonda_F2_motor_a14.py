import numpy as np, pandas as pd, json, hashlib
exec(open("sondas_F2.py").read().split("info = {")[0])
cc, a = "motor_1", 1.4
R = razon(cc, a); m2 = aplicar(t25, {cc: a}); i = c25 == cc
out = F2.copy(); out.loc[i, "prediction"] = m2[i] * R
assert (out.prediction.values[~i] == F2.prediction.values[~i]).all() and (out.prediction > 0).all() and len(out) == 209063
p = "sonda_F2_motor_1_a14.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
info = {"archivo": p, "celda": cc, "a": a, "razon_nivel": round(R, 4), "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
        "total_celda": round(float(out.prediction.values[i].sum()), 2), "total_celda_F2": round(float(F2.prediction.values[i].sum()), 2),
        "prevision_parabola_3_puntos": round(float(np.polyval([-0.016375, 0.045875, 0.13083], a)), 5),
        "motivo": "La parábola de motor_1 con (0,6; 0,8; 1,0) tiene vértice extrapolado en 1,40; esta sonda confirma la curva más allá de 1 antes de construir el final."}
json.dump(info, open("sonda_F2_motor_1_a14_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(info, indent=1, ensure_ascii=False))
