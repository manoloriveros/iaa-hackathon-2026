"""F3 (candidato, sin enviar): F2 + forma de motor_1 con el vértice corregido por fuga de nivel (agente H) + factores residuales
de variables del emergente que T2b no tiene o no transfiere (género, aseguradora previa, ocupación en autos; género, teletrabajo y
segmento de marketing en contenidos), Tweedie-óptimos con credibilidad n/(n+K), estimados con los OOF de T2b de 2023+2024
(NB y REN agrupados por ramo) + nivel creíble por celda de las sondas sobre F, con la razón de nivel Tweedie local de toda la
transformación. Uso: python construir_F3.py [K] [--sin-factores] [--sin-forma]"""
import sys, json, hashlib
argv = sys.argv[:]; sys.argv = ["x", "--prueba"]
import numpy as np, pandas as pd
exec(open("construir_final.py").read())
sys.argv = argv
exec(open("exp26/lib26.py").read())
KC = float([a for a in sys.argv[1:] if not a.startswith("--")][0]) if [a for a in sys.argv[1:] if not a.startswith("--")] else 300.0
SIN_F = "--sin-factores" in sys.argv; SIN_A = "--sin-forma" in sys.argv
FUGA = json.load(open("exp26/fuga_celdas.json"))
A_M1 = 1.0 if SIN_A else 1 + SIG["motor_1"]["Z_tau0.25"] * (FUGA["motor_1"]["sin_nivel"]["vertice"] - 1)
SEQ = [] if SIN_F else [("gender", ["motor", "contents"]), ("previous_insurer", ["motor"]), ("occ", ["motor"]),
                         ("works_from_home", ["contents"]), ("marketing_segment", ["contents"])]
def paso_forma(t, m):
    tt = t.copy(); tt["m"] = m
    return aplicar(tt, {"motor_1": A_M1}) if A_M1 != 1.0 else m
# 1) factores estimados sobre el pool 2023+2024 ya transformado (F2 + forma)
pool = pd.concat([sets["DEV23_T2b"], sets["HOLD24_T2b"]]).copy()
pool["m"] = paso_forma(pool, transformar(pool))
FAC = []
for v, lines in SEQ:
    cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(pool, cl, lines, KC)
    pool["m"] = aplica_tw(pool, f, cl, pool.m.values); FAC.append((v, cl, f))
def transformar3(t):
    m = paso_forma(t, transformar(t))
    for v, cl, f in FAC: m = aplica_tw(t, f, cl, m)
    return m
# 2) razón de nivel Tweedie local de toda la transformación, por celda (4 series)
cels = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]
raz = {}
for k_ in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    s_ = sets[k_]; m3 = transformar3(s_); c_ = celda(s_)
    raz[k_] = {cc: kopt(s_.y.values[c_ == cc], m3[c_ == cc]) / kopt(s_.y.values[c_ == cc], s_.m.values[c_ == cc]) for cc in cels}
R3 = {cc: float(np.mean([raz[k][cc] for k in raz])) for cc in cels}
# 3) nivel creíble por celda (sondas sobre F, recibos reales)
sc = {}
for r in json.load(open("recibos_reales_20261026.json")):
    if r["sha256"] in nombre_sha:
        tipo, cual = nombre_sha[r["sha256"]]; sc[tipo if cual is None else (tipo, cual)] = float(r["d2"])
lv = resolver(sc)
F = pd.read_csv("in/final_sonda_global_2025.csv", dtype={"row_id": str}); assert hashlib.sha256(open("in/final_sonda_global_2025.csv", "rb").read()).hexdigest().startswith("42659dbb")
t = b.loc[F.row_id].copy(); t["m"] = F.prediction.values; t["c_fila"] = 1.0
m = transformar3(t); c = celda(t)
for cc in cels: m[c == cc] *= R3[cc] * lv["cred"][cc] / lv["g"]
out = F.copy(); out["prediction"] = m
assert len(out) == 209063 and np.isfinite(m).all() and (m > 0).all() and (out.row_id.values == F.row_id.values).all()
tag = ("F3" + ("_sinfac" if SIN_F else "") + ("_sinforma" if SIN_A else "") + (f"_K{int(KC)}" if KC != 300 else ""))
p = f"exp26/{tag}_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
info = {"archivo": p, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "K": KC, "a_motor_1": A_M1,
        "factores": {v: {f"{a}|{vv}": round(x, 4) for (a, g_, vv), x in f.items()} for v, cl, f in FAC},
        "razon_nivel_local": {k: round(v, 4) for k, v in R3.items()}, "razon_por_serie": {k: {c_: round(v, 4) for c_, v in d.items()} for k, d in raz.items()},
        "nivel_cred_rel_F": {k: round(v / lv["g"], 4) for k, v in lv["cred"].items()},
        "total": round(float(m.sum()), 2), "total_celda": {cc: round(float(m[c == cc].sum()), 2) for cc in cels},
        "total_F_celda": {cc: round(float(F.prediction.values[c == cc].sum()), 2) for cc in cels}}
json.dump(info, open(f"exp26/{tag}_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps({k: v for k, v in info.items() if k != "factores"}, indent=1, ensure_ascii=False))
