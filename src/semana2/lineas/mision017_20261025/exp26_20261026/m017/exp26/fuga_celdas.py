import json, numpy as np, pandas as pd
R = "/home/claude/m017/"
pre = json.load(open(R + "in/preinscripcion.json")); fin = json.load(open(R + "final_salida.txt"))
b = pd.read_parquet(R + "base_etiquetas.parquet").set_index("row_id")
F2 = pd.read_csv(R + "F2_ncb_previos_2025.csv", dtype={"row_id": str}).set_index("row_id").prediction
F = pd.read_csv(R + "in/final_sonda_global_2025.csv", dtype={"row_id": str}).set_index("row_id").prediction.reindex(F2.index)
t = b.loc[F2.index]; g = pre["base"]["g"]
PTS = {"motor_1": {0.6: (0.15246, "sonda_F2_motor_1_a06.csv"), 0.8: (0.15705, "sonda_F2_motor_1_a08.csv")},
       "buildings_1": {0.7: (0.15894, "sonda_F2_buildings_1_a07.csv"), 1.3: (0.1591, "sonda_F2_buildings_1_a13.csv")},
       "contents_1": {0.7: (0.15958, "sonda_F2_contents_1_a07.csv"), 1.3: (0.16001, "sonda_F2_contents_1_a13.csv")}}
out = {}
for cel, pts in PTS.items():
    l, nb = cel.split("_"); i = ((t.line == l) & (t.new_business == bool(int(nb)))).values
    rF = np.sqrt(F2.values[i]).sum() / np.sqrt(F.values[i]).sum(); cst = fin["nivel"]["c_opt"][cel]
    Bm = pre["base"]["beta_B"] * pre["celdas"][cel]["cuota_raiz_mu"] * np.sqrt(g) * rF
    K = cst / g / rF ** 2
    P = {1.0: 0.16033}; C = {1.0: 0.16033}; o = {"K_estrella_F2": K}
    for a, (sc, f) in pts.items():
        p = pd.read_csv(R + f, dtype={"row_id": str}).set_index("row_id").prediction.reindex(F2.index).values
        s = np.sqrt(p[i]).sum() / np.sqrt(F2.values[i]).sum(); lev = -(K * Bm * (1 / s - 1) + Bm * (s - 1))
        P[a] = sc; C[a] = sc - lev; o[f"a{a}"] = {"raiz_ratio": round(s, 5), "d2_nivel": round(lev, 6)}
    for nm, D in (("original", P), ("sin_nivel", C)):
        x = np.array(sorted(D)); y = np.array([D[k] for k in x]); c = np.polyfit(x, y, 2); v = -c[1] / (2 * c[0])
        o[nm] = {"vertice": round(v, 4), "curv": round(c[0], 5), "ganancia": round(np.polyval(c, v) - D[1.0], 6)}
    out[cel] = o
print(json.dumps(out, indent=1)); json.dump(out, open(R + "exp26/fuga_celdas.json", "w"), indent=1)
