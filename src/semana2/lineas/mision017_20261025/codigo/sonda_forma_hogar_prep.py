"""Sondas de forma en hogar de nuevo negocio (buildings_1, contents_1) sobre F1: a = 0,7 y 1,3 en una sola celda por archivo,
con la razón de nivel Tweedie medida en 2023 y 2024; ruido del óptimo de a por remuestreo de 2024 al tamaño de 2025."""
import numpy as np, pandas as pd, json, hashlib
exec(open("construir_forma.py").read().split("# 2025")[0])
A = np.round(np.arange(0.3, 1.81, 0.05), 2)
def razon(c, a):
    rs = []
    for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
        t = sets[k]; cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values; i = cel == c
        m2 = aplicar(t, {c: a}); rs.append(kopt(t.y.values[i], m2[i]) / kopt(t.y.values[i], t.m.values[i]))
    return float(np.mean(rs))
n25 = {"buildings_1": 39716, "contents_1": 50441}
F1 = pd.read_csv("F1_forma_ncb_2025.csv", dtype={"row_id": str}); tt = b.loc[F1.row_id].copy(); tt["m"] = F1.prediction.values; tt["c_fila"] = 1.0
cel25 = (tt.line + "_" + tt.new_business.astype(int).astype(str)).values
info = {}; rng = np.random.default_rng(20261026)
for c in ["buildings_1", "contents_1"]:
    t = sets["HOLD24_mezcla"]; cel = (t.line + "_" + t.new_business.astype(int).astype(str)).values; s = t[cel == c]
    custs = s.customer_id.unique(); por = s.groupby("customer_id").indices; yv, ev, mv = s.y.values, (s.exposure * s.c_fila).values, s.m.values
    def aopt(ii):
        yy, e, m = yv[ii], ev[ii], mv[ii]; r = m / e; gm = m.sum() / e.sum()
        return A[int(np.argmin([dev(yy, (lambda mm: mm * kopt(yy, mm))(e * gm * (r / gm) ** a)).sum() for a in A]))]
    dif = []
    for _ in range(100):
        idx = []
        while len(idx) < n25[c]:
            idx.extend(por[custs[rng.integers(len(custs))]])
        idx = np.array(idx[:n25[c]]); pub = rng.random(len(idx)) < 0.33; dif.append(aopt(idx[pub]) - aopt(idx[~pub]))
    sig = float(np.std(dif)); tau = 0.25; Z = tau ** 2 / (tau ** 2 + sig ** 2); info[c] = {"sigma": round(sig, 3), "tau": tau, "Z": round(Z, 3), "archivos": {}}
    for a in (0.7, 1.3):
        R = razon(c, a); m2 = aplicar(tt, {c: a}); i = cel25 == c
        out = F1.copy(); out.loc[i, "prediction"] = m2[i] * R
        assert np.allclose(out.prediction.values[~i], F1.prediction.values[~i]) and (out.prediction > 0).all()
        p = f"sonda_forma_{c}_a{int(round(a*10)):02d}.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
        info[c]["archivos"][p] = {"a": a, "razon_nivel": round(R, 4), "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()}
info["regla"] = "Por celda: parábola en a por (0,7; 1,0 = F1; 1,3); si es cóncava y a* en [0,3; 1,8], a_final = 1 + Z (a* − 1); si no, 1. Nunca se marca una sonda."
json.dump(info, open("sonda_forma_hogar_info.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(info, indent=1, ensure_ascii=False))
