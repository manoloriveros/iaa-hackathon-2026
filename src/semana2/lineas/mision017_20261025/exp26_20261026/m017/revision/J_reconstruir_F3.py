"""J, tarea 1: reconstrucción independiente de F3 desde F, comparación fila a fila, SHA y formato.
También construye F3 sin factores (J_F3_sinfac_2025.csv) para la tarea 3."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
from J_lib import *

OUT = R + "revision/"
res = {}
# ---------- forma: vértice corregido (método de H) recalculado aquí y el usado por el autor ----------
fug = json.load(open(R + "exp26/fuga_celdas.json"))
SIG = json.load(open(R + "sigma_forma.json"))
Z = SIG["motor_1"]["Z_tau0.25"]
v_autor = fug["motor_1"]["sin_nivel"]["vertice"]
A_M1 = 1 + Z * (v_autor - 1)
res["a_motor_1"] = A_M1

ser = series()
pool = pd.concat([ser["DEV23_T2b"], ser["HOLD24_T2b"]])
T3 = TransfF3(pool, A_M1)

# ---------- factores frente a los publicados ----------
info = json.load(open(R + "exp26/F3_info.json"))
dif_fac = {}
for v, f in T3.fac:
    pub = info["factores"][v]
    mine = {f"{l}|{vv}": x for (l, vv), x in f.items()}
    claves = set(pub) | set(mine)
    d = max(abs(mine.get(k, np.nan) - pub.get(k, np.nan)) for k in claves)
    dif_fac[v] = {"n_niveles": len(claves), "max_dif_abs": float(d), "faltan": sorted(set(pub) ^ set(mine))}
res["factores_vs_publicados"] = dif_fac
f2info = json.load(open(R + "F2_info.json"))
d1 = max(abs(T3.f2.f1[tuple(k.split("|"))] - x) for k, x in f2info["factores_ncb"].items())
d2_ = max(abs(T3.f2.f2[tuple(k.split("|"))] - x) for k, x in f2info["factores_previos"].items())
res["F2_factores_max_dif"] = {"ncb": float(d1), "previos": float(d2_)}

# ---------- razón de nivel local ----------
R3, R3s = razon_local(ser, lambda s: T3(s, s.m.values))
R3sf, _ = razon_local(ser, lambda s: T3(s, s.m.values, con_factores=False))
res["R3"] = R3; res["R3_dif_publicado"] = {c: R3[c] - info["razon_nivel_local"][c] for c in CELS}
res["R3_sin_factores"] = R3sf

# ---------- nivel: resolutor propio ----------
Bp = PRE["base"]; CEL = PRE["celdas"]; g = Bp["g"]; Kp = 1.2
dF = REC[Bp["sha256"]]
sc = {v["celda"]: REC[v["sha256"]] for v in PRE["sondas"].values()}
bs = {s: Bp["beta_B"] * CEL[s]["cuota_raiz_mu"] for s in CEL}
as_ = {s: (dF - sc[s] - bs[s] * ((g * Kp) ** .5 - g ** .5)) / ((g * Kp) ** -.5 - g ** -.5) for s in sc}
as_[PRE["celda_deducida"]] = Bp["beta_A"] - sum(as_.values())
cst = {s: as_[s] / bs[s] for s in CEL}
cg = Bp["c_optimo_global"]
cred = {s: g * float(np.clip((cst[s] / cg) ** CEL[s]["Z"], 0.75, 1.33)) for s in CEL}
res["nivel"] = {"a_s": as_, "b_s": bs, "c_opt": cst, "cred_rel_F": {s: cred[s] / g for s in CEL}}

# ---------- F3 propio ----------
F = leer_pred(R + "in/final_sonda_global_2025.csv")
assert sha(R + "in/final_sonda_global_2025.csv") == Bp["sha256"]
t = test_df(F.row_id.values); c = celda(t)
m_sf = T3(t, F.prediction.values, con_factores=False)
m = T3(t, F.prediction.values)
for cc in CELS:
    m[c == cc] *= R3[cc] * cred[cc] / g
    m_sf[c == cc] *= R3sf[cc] * cred[cc] / g

F3 = leer_pred(R + "exp26/F3_2025.csv")
raw = open(R + "exp26/F3_2025.csv", "rb").read()
lines_ = raw.split(b"\n")
fmt = {"sha256": sha(R + "exp26/F3_2025.csv"), "sha_info": info["sha256"], "filas": len(F3),
       "cabecera": lines_[0].decode(), "CRLF": b"\r" in raw, "termina_en_LF": raw.endswith(b"\n"),
       "mismo_orden_row_id": bool((F3.row_id.values == F.row_id.values).all()), "row_id_unicos": bool(F3.row_id.is_unique),
       "finitos": bool(np.isfinite(F3.prediction).all()), "positivos": bool((F3.prediction > 0).all()),
       "min": float(F3.prediction.min()), "max": float(F3.prediction.max()), "decimales_6": all(len(l.split(b",")[1].split(b".")[1]) == 6 for l in lines_[1:-1][:5000])}
rel = np.abs(m / F3.prediction.values - 1)
fmt["max_dif_rel_vs_mia"] = float(rel.max()); fmt["p99_dif_rel"] = float(np.quantile(rel, .99))
fmt["max_dif_rel_por_celda"] = {cc: float(rel[c == cc].max()) for cc in CELS}
fmt["total_mio"] = float(m.sum()); fmt["total_archivo"] = float(F3.prediction.sum())
res["formato_y_coincidencia"] = fmt

# sin factores: si el autor lo generó, comparar; si no, guardar el mío
out = F.copy(); out["prediction"] = m_sf
p = OUT + "J_F3_sinfac_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
res["F3_sinfac_J"] = {"archivo": p, "sha256": sha(p), "total": float(m_sf.sum()),
                      "total_celda": {cc: float(m_sf[c == cc].sum()) for cc in CELS}}
import os
if os.path.exists(R + "exp26/F3_sinfac_2025.csv"):
    a = leer_pred(R + "exp26/F3_sinfac_2025.csv"); res["F3_sinfac_autor_max_dif_rel"] = float(np.abs(a.prediction.values / m_sf - 1).max())
# mi F3 también en disco (para las tareas siguientes)
out = F.copy(); out["prediction"] = m; out.to_csv(OUT + "J_F3_mio_2025.csv", index=False, float_format="%.6f", lineterminator="\n")
res["F3_mio_sha"] = sha(OUT + "J_F3_mio_2025.csv")
res["F3_mio_igual_bytes_archivo"] = res["F3_mio_sha"] == fmt["sha256"]
json.dump(res, open(OUT + "J_reconstruir_F3.json", "w"), indent=1, default=float, ensure_ascii=False)
print(json.dumps(res, indent=1, default=float, ensure_ascii=False))
