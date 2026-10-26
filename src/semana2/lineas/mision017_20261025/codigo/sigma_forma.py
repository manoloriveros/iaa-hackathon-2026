"""Ruido público→privado del óptimo de forma por celda (escalar correcto), remuestreando 2024 (mezcla proxy, tras NCB+previos) al tamaño 2025
y a su mezcla de bandas de exposición."""
import numpy as np, pandas as pd, json
exec(open("construir_F2.py").read().split("F = pd.read_csv")[0])
A = np.round(np.arange(0.2, 1.81, 0.05), 2)
t = sets["HOLD24_mezcla"].copy(); t["m"] = transformar(t); c = celda(t)
te = b[b.conjunto == "test"]; c25 = (te.line + "_" + te.new_business.astype(int).astype(str)).values
out = {}; rng = np.random.default_rng(42)
for cc, n25 in (("motor_1", 68823), ("buildings_1", 39716), ("contents_1", 50441)):
    s = t[c == cc]; sb = banda(s.exposure.values); tb = pd.Series(banda(te.exposure.values[c25 == cc])).value_counts(normalize=True)
    yv, ev, mv = s.y.values, (s.exposure * s.c_fila).values, s.m.values
    idx_b = {k: np.where(sb == k)[0] for k in tb.index}
    def aopt(ii):
        yy, e, m = yv[ii], ev[ii], mv[ii]; r = m / e; gm = m.sum() / e.sum()
        return A[int(np.argmin([dev(yy, (lambda mm: mm * kopt(yy, mm))(e * gm * (r / gm) ** a)).sum() for a in A]))]
    dif = []; full = []
    for _ in range(150):
        ii = np.concatenate([rng.choice(idx_b[k], int(round(n25 * p))) for k, p in tb.items() if len(idx_b[k])])
        pub = rng.random(len(ii)) < 0.33; dif.append(aopt(ii[pub]) - aopt(ii[~pub])); full.append(aopt(ii))
    out[cc] = {"sigma": round(float(np.std(dif)), 3), "a_opt_media_remuestreo": round(float(np.mean(full)), 3), "bandas_2025": tb.round(3).to_dict()}
    tau = 0.25; out[cc]["Z_tau0.25"] = round(tau ** 2 / (tau ** 2 + out[cc]["sigma"] ** 2), 3)
print(json.dumps(out, indent=1)); json.dump(out, open("sigma_forma.json", "w"), indent=1)
