import numpy as np, pandas as pd, json
P = 1.5
def dev(y, m):
    return 2 * (np.maximum(y, 0) ** (2 - P) / ((1 - P) * (2 - P)) - y * m ** (1 - P) / (1 - P) + m ** (2 - P) / (2 - P))
def kopt(y, m):  # escalar Tweedie 1,5 óptimo
    return np.sum(y / np.sqrt(m)) / np.sum(np.sqrt(m))
b = pd.read_parquet("base_etiquetas.parquet").set_index("row_id")
def cargar(conj, mod):
    d = pd.concat([pd.read_parquet(f"oof/pred/{conj}/{mod}_{l}.parquet") for l in ["motor", "buildings", "contents"]]).set_index("row_id")
    t = b.loc[d.index].copy(); t["m"] = d.mu.values * t.c_fila.values; return t
p24 = pd.read_parquet("in/predicciones_2024.parquet").set_index("row_id")
sets = {"DEV23_T2b": cargar("dev", "T2b"), "HOLD24_T2b": cargar("hold", "T2b")}
for c in ["A1", "R0"]:
    t = b.loc[p24.index].copy(); t["m"] = p24[c].values; sets[f"HOLD24_{c}"] = t
for k, t in sets.items():
    print(k, len(t), "y", round(t.y.sum()), "m", round(t.m.sum()), "ratio", round(t.y.sum() / t.m.sum(), 3))
A = np.round(np.arange(0.6, 1.41, 0.05), 2)
res = {}
for k, t in sets.items():
    t = t.copy(); t["cel"] = t.line + "_" + t.new_business.astype(int).astype(str)
    y = t.y.values; null = dev(y, np.full(len(y), y.mean())).sum(); res[k] = {}
    base_dev = 0.0; best_dev = 0.0
    for c, g in t.groupby("cel"):
        yy = g.y.values; e = g.exposure.values * g.c_fila.values; r = g.m.values / e; gm = np.sum(g.m.values) / np.sum(e)
        devs = []
        for a in A:
            m = e * gm * (r / gm) ** a; m = m * kopt(yy, m); devs.append(dev(yy, m).sum())
        devs = np.array(devs); i1 = int(np.where(A == 1.0)[0][0]); ib = int(devs.argmin())
        base_dev += devs[i1]; best_dev += devs[ib]
        res[k][c] = {"n": len(g), "positivos": int((yy > 0).sum()), "a_opt": float(A[ib]), "ganancia_D2": round(float((devs[i1] - devs[ib]) / null), 5)}
    res[k]["_total_ganancia_D2"] = round(float((base_dev - best_dev) / null), 5)
print(json.dumps(res, indent=1))
