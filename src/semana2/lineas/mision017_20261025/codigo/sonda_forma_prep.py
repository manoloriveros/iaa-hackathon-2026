"""Prepara la sonda de forma en autos de nuevo negocio sobre F1 (a = 0,3 y 0,7) y mide el ruido público→privado del óptimo de a
remuestreando 2024 (mezcla proxy, tras NCB) al tamaño de la celda en 2025 (68.823 filas)."""
import numpy as np, pandas as pd, json, hashlib
exec(open("construir_forma.py").read().split("# 2025")[0])
A = np.round(np.arange(0.1, 1.31, 0.05), 2)
# razón de nivel para cada a (sobre la serie mezcla y T2b de 2024 y T2b 2023)
def razon(a):
    rs = []
    for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
        t = sets[k]; t2 = t.copy(); t2["m"] = aplicar_ncb(t, fN, True); cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values
        i = cel == "motor_1"; t2.loc[i, "m"] = t2.m.values[i] * t.m.values[i].sum() / t2.m.values[i].sum()
        m2 = aplicar(t2, {"motor_1": a}); rs.append(kopt(t.y.values[i], m2[i]) / kopt(t.y.values[i], t.m.values[i]))
    return float(np.mean(rs))
R = {a: razon(a) for a in (0.3, 0.5, 0.7)}
# ruido: remuestreo por cliente de motor_1 2024 (mezcla, tras NCB) a 68.823 filas, público 33 %
t = sets["HOLD24_mezcla"]; t2 = t.copy(); t2["m"] = aplicar_ncb(t, fN, True); s = t2[(t2.line == "motor") & t2.new_business]
rng = np.random.default_rng(20261025); custs = s.customer_id.unique(); por = s.groupby("customer_id").indices
yv, ev, mv = s.y.values, (s.exposure * s.c_fila).values, s.m.values
def aopt(ii):
    yy, e, m = yv[ii], ev[ii], mv[ii]; r = m / e; gm = m.sum() / e.sum()
    return A[int(np.argmin([dev(yy, (lambda mm: mm * kopt(yy, mm))(e * gm * (r / gm) ** a)).sum() for a in A]))]
dif = []
for _ in range(150):
    idx = []
    while len(idx) < 68823:
        c = custs[rng.integers(len(custs))]; idx.extend(por[c])
    idx = np.array(idx[:68823]); pub = rng.random(len(idx)) < 0.33
    dif.append(aopt(idx[pub]) - aopt(idx[~pub]))
sig = float(np.std(dif)); tau = 0.20; Z = tau ** 2 / (tau ** 2 + sig ** 2)
F1 = pd.read_csv("F1_forma_ncb_2025.csv", dtype={"row_id": str}); F = pd.read_csv("in/final_sonda_global_2025.csv", dtype={"row_id": str})
tt = b.loc[F.row_id].copy(); tt["m"] = F.prediction.values; tt["c_fila"] = 1.0
m_ncb = aplicar_ncb(tt, fN, True); cel = (tt.line + "_" + tt.new_business.astype(int).astype(str)).values
for c in ["motor_0", "motor_1"]:
    i = cel == c; m_ncb[i] *= F.prediction.values[i].sum() / m_ncb[i].sum()
info = {"razon_nivel": {str(a): round(v, 4) for a, v in R.items()}, "sigma_publico_privado_a": round(sig, 4), "tau": tau, "Z": round(Z, 3), "archivos": {}}
for a in (0.3, 0.7):
    tt2 = tt.copy(); tt2["m"] = m_ncb; m2 = aplicar(tt2, {"motor_1": a}); i = cel == "motor_1"
    out = F1.copy(); out.loc[i, "prediction"] = m2[i] * R[a]
    assert np.allclose(out.prediction.values[~i], F1.prediction.values[~i]) and (out.prediction > 0).all()
    p = f"sonda_forma_motor1_a{int(a*10):02d}.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
    info["archivos"][p] = {"a": a, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(), "total_motor_1": round(float(out.prediction.values[i].sum()), 2)}
info["total_motor_1_F1"] = round(float(F1.prediction.values[cel == "motor_1"].sum()), 2)
info["regla"] = "Con D²(F1) y las dos sondas: parábola en a por los tres puntos (0,3; 0,5; 0,7); si es cóncava y el vértice a* cae en [0,1; 1,0], a_final = 0,5 + Z (a* − 0,5); si no, se queda 0,5. Nunca se marca una sonda."
json.dump(info, open("sonda_forma_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(info, indent=1, ensure_ascii=False))
