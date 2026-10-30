"""Reconstruct the historical F3b alternative using recorded audits I and J.
Start from F2. Apply the level-leakage-corrected motor new-business shape while
holding the 2025 cell sum of sqrt(mu) fixed. Retain the validated motor gender
and contents gender/home-working/marketing factors, excluding prior insurer
and occupation under the corrected null comparison. Estimate factors from pooled
T2b OOF after F2, with n/(n+K) credibility and fixed cell totals; calculate local
level ratios using equal year weights, then apply credible cell levels.
Usage: python construir_F3b.py [<K>] [--sin-factores] [--sin-forma] [--seq=...]
"""
import sys, json, hashlib
argv = sys.argv[:]; sys.argv = ["x", "--prueba"]
import numpy as np, pandas as pd
exec(open("exp26/lib26.py").read())
exec(open("construir_final.py").read())
sys.argv = argv
pos = [a for a in sys.argv[1:] if not a.startswith("--")]
KC = float(pos[0]) if pos else 300.0
SIN_F = "--sin-factores" in sys.argv; SIN_A = "--sin-forma" in sys.argv
SEQ_ALL = {"gender": ["motor", "contents"], "works_from_home": ["contents"], "marketing_segment": ["contents"],
           "previous_insurer": ["motor"], "occ": ["motor"]}
seqarg = [a for a in sys.argv if a.startswith("--seq=")]
SEQN = seqarg[0][6:].split(",") if seqarg else ["gender", "works_from_home", "marketing_segment"]
SEQ = [] if SIN_F else [(v, SEQ_ALL[v]) for v in SEQN]
FUGA = json.load(open("exp26/fuga_celdas.json"))
A_M1 = 1.0 if SIN_A else 1 + SIG["motor_1"]["Z_tau0.25"] * (FUGA["motor_1"]["sin_nivel"]["vertice"] - 1)
cels = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]
# Fit factors on the local F2-plus-shape pool with fixed sum(mu).
pool = pd.concat([sets["DEV23_T2b"], sets["HOLD24_T2b"]]).copy()
pt = pool.copy(); pt["m"] = transformar(pool); pool["m"] = aplicar(pt, {"motor_1": A_M1}) if A_M1 != 1.0 else pt.m.values
FAC = []
for v, lines in SEQ:
    cl = (lambda vv: (lambda t: col(t, vv)))(v); f = fac_tw(pool, cl, lines, KC)
    pool["m"] = aplica_tw(pool, f, cl, pool.m.values); FAC.append((v, cl, f))
def factores(t, m):
    for v, cl, f in FAC: m = aplica_tw(t, f, cl, m)
    return m
# Local before/after factor-level ratio over F2 plus shape; weight both years equally.
raz = {}
for k_ in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    s_ = sets[k_].copy(); tt = s_.copy(); tt["m"] = transformar(s_); m0 = aplicar(tt, {"motor_1": A_M1}) if A_M1 != 1.0 else tt.m.values
    m1 = factores(s_, m0); c_ = celda(s_)
    raz[k_] = {cc: kopt(s_.y.values[c_ == cc], m1[c_ == cc]) / kopt(s_.y.values[c_ == cc], m0[c_ == cc]) for cc in cels}
Rf = {cc: 0.5 * raz["DEV23_T2b"][cc] + 0.5 * np.mean([raz[k][cc] for k in ["HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]]) for cc in cels}
# Credibility-weighted cell level.
sc = {}
for r in json.load(open("recibos_reales_20261026.json")):
    if r["sha256"] in nombre_sha:
        tipo, cual = nombre_sha[r["sha256"]]; sc[tipo if cual is None else (tipo, cual)] = float(r["d2"])
lv = resolver(sc)
F2 = pd.read_csv("F2_ncb_previos_2025.csv", dtype={"row_id": str}); pass
F = pd.read_csv("in/final_sonda_global_2025.csv", dtype={"row_id": str}); assert (F.row_id.values == F2.row_id.values).all()
t = b.loc[F2.row_id].copy(); t["m"] = F2.prediction.values; t["c_fila"] = 1.0; c = celda(t)
m = F2.prediction.values.copy()
if A_M1 != 1.0:
    i = c == "motor_1"; ms = aplicar(t.assign(m=m), {"motor_1": A_M1})
    m[i] = ms[i] * (np.sqrt(m[i]).sum() / np.sqrt(ms[i]).sum()) ** 2     # Hold the cell's sum(sqrt(mu)) fixed.
m = factores(t, m)
for cc in cels: m[c == cc] *= Rf[cc] * lv["cred"][cc] / lv["g"]
out = F2.copy(); out["prediction"] = m
assert len(out) == 209063 and np.isfinite(m).all() and (m > 0).all()
tag = "F3b" + ("_sinfac" if SIN_F else "") + ("_sinforma" if SIN_A else "") + (f"_K{int(KC)}" if KC != 300 else "") + ("" if not seqarg else "_" + "-".join(SEQN))
p = f"exp26/{tag}_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
info = {"archivo": p, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "K": KC, "a_motor_1": A_M1, "seq": [v for v, _ in SEQ],
        "factores": {v: {f"{a}|{vv}": round(x, 4) for (a, g_, vv), x in f.items()} for v, cl, f in FAC},
        "razon_nivel_factores": {k: round(v, 4) for k, v in Rf.items()}, "razon_por_serie": {k: {c_: round(v, 4) for c_, v in d.items()} for k, d in raz.items()},
        "nivel_cred_rel_F": {k: round(v / lv["g"], 4) for k, v in lv["cred"].items()},
        "total": round(float(m.sum()), 2), "total_celda": {cc: round(float(m[c == cc].sum()), 2) for cc in cels},
        "total_F2_celda": {cc: round(float(F2.prediction.values[c == cc].sum()), 2) for cc in cels},
        "total_F_celda": {cc: round(float(F.prediction.values[c == cc].sum()), 2) for cc in cels}}
json.dump(info, open(f"exp26/{tag}_info.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in info.items() if k not in ("razon_por_serie",)}, indent=1, ensure_ascii=False))
