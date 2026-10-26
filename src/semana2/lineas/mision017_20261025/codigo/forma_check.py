import numpy as np, pandas as pd, json
exec(open("ncb_local.py").read().split("res = {}")[0])
out = {}
# 1) fuera de tiempo: a estimado solo en 2023 (motor_1 0,4; motor_0 0,9) aplicado a 2024
for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    t = sets[k]; base = evalua(t, t.m.values)
    out[k] = {"a_de_2023_en_2024": round(evalua(t, aplicar(t, {"motor_1": 0.4, "motor_0": 0.9})) - base, 5),
              "regla_0.5_0.85": round(evalua(t, aplicar(t, {"motor_1": 0.5, "motor_0": 0.85})) - base, 5)}
# 2) cambio del nivel óptimo de la celda al cambiar la forma conservando el total de la celda
for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    t = sets[k]; cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values; m2 = aplicar(t, {"motor_1": 0.5, "motor_0": 0.85})
    out[k + "_nivel"] = {c: round(kopt(t.y.values[cel == c], m2[cel == c]) / kopt(t.y.values[cel == c], t.m.values[cel == c]), 4) for c in ["motor_0", "motor_1"]}
print(json.dumps(out, indent=1))
