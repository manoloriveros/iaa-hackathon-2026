import numpy as np, pandas as pd, json
exec(open("construir_F2.py").read().split("F = pd.read_csv")[0])
A = np.round(np.arange(0.5, 1.61, 0.05), 2); out = {}
for k in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    t = sets[k].copy(); t["m"] = transformar(t); c = celda(t); r = {}
    for cc in ["buildings_0", "contents_0", "motor_0"]:
        i = c == cc; s = t[i]; yy = s.y.values; e = (s.exposure * s.c_fila).values; rr = s.m.values / e; gm = s.m.values.sum() / e.sum()
        dv = np.array([dev(yy, (lambda mm: mm * kopt(yy, mm))(e * gm * (rr / gm) ** a)).sum() for a in A])
        null = dev(yy, np.full(len(yy), yy.mean())).sum(); i1 = int(np.where(A == 1.0)[0][0])
        r[cc] = {"a_opt": float(A[dv.argmin()]), "ganancia_rel_celda": round(float((dv[i1] - dv.min()) / null), 5), "pos": int((yy > 0).sum())}
    out[k] = r
print(json.dumps(out, indent=1))
