"""Sondas de forma sobre F2 (escalar Tweedie correcto): motor_1 a = 0,6 y 0,8; buildings_1 y contents_1 a = 0,7 y 1,3.
Cada archivo cambia solo su celda; razón de nivel medida en las cuatro series ya transformadas como F2."""
import numpy as np, pandas as pd, json, hashlib
exec(open("construir_F2.py").read().split("F = pd.read_csv")[0])
F2 = pd.read_csv("F2_ncb_previos_2025.csv", dtype={"row_id": str}); t25 = b.loc[F2.row_id].copy(); t25["m"] = F2.prediction.values; t25["c_fila"] = 1.0; c25 = celda(t25)
ser = {}
for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    t = sets[k].copy(); t["m"] = transformar(t); ser[k] = t
def razon(cc, a):
    rs = []
    for k, t in ser.items():
        c = celda(t); i = c == cc; m2 = aplicar(t, {cc: a}); rs.append(kopt(t.y.values[i], m2[i]) / kopt(t.y.values[i], t.m.values[i]))
    return float(np.mean(rs))
info = {"base": {"archivo": "F2_ncb_previos_2025.csv", "sha256": hashlib.sha256(open("F2_ncb_previos_2025.csv", "rb").read()).hexdigest()}, "sondas": {}}
for cc, aa in (("motor_1", (0.6, 0.8)), ("buildings_1", (0.7, 1.3)), ("contents_1", (0.7, 1.3))):
    for a in aa:
        R = razon(cc, a); m2 = aplicar(t25, {cc: a}); i = c25 == cc
        out = F2.copy(); out.loc[i, "prediction"] = m2[i] * R
        assert (out.prediction.values[~i] == F2.prediction.values[~i]).all() and (out.prediction > 0).all()
        p = f"sonda_F2_{cc}_a{int(round(a*10)):02d}.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
        info["sondas"][p] = {"celda": cc, "a": a, "razon_nivel": round(R, 4), "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
                             "total_celda": round(float(out.prediction.values[i].sum()), 2), "total_celda_F2": round(float(F2.prediction.values[i].sum()), 2)}
json.dump(info, open("sondas_F2_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(info, indent=1, ensure_ascii=False))
