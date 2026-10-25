"""OOF 2023-2024 (fase pcv, troncos 2021-2024) de MLind v2 frente a v1 (T2b), pesos y nivel cruzados por pliegue."""
import json, numpy as np, pandas as pd
from comun import *
from evaluar import mezcla_pesos, metricas, bootstrap_dif
import receta
t = receta.tabla("pcv"); comps = ["T2b", "T2h", "FS", "T2o"]; P = receta.componentes("pcv", comps, t)
folds = pliegue(t.customer_id.values)
def oof(cs, enc):
    out = np.zeros(len(t))
    for l in LINEAS:
        il = (t.line == l).values
        for f in range(5):
            te = folds == f; tr = ~te & il
            M = np.column_stack([P[c][tr] * t.c_fila.values[tr] for c in cs])
            w = mezcla_pesos(t.y.values[tr], M) if len(cs) > 1 else np.ones(1)
            w = (1 - enc) * w + enc / len(cs)
            b = np.column_stack([P[c] for c in cs]) @ w
            k = factor_tweedie(t.y.values[tr], b[tr] * t.c_fila.values[tr])
            out[te & il] = b[te & il] * k
    return out
v1 = oof(["T2b"], 0); res = {"v1_T2b": metricas(t, v1)}
for enc in (0, 0.5, 1):
    v2 = oof(comps, enc); nom = f"v2_e{int(enc*100)}"
    res[nom] = metricas(t, v2)
    res[nom + "_vs_v1"] = {"todo": bootstrap_dif(t, v2, v1)}
    for a in (2023, 2024):
        s = (t.year == a).values
        res[nom + "_vs_v1"][str(a)] = bootstrap_dif(t[s].reset_index(drop=True), v2[s], v1[s])
    for nb in (True, False):
        s = (t.new_business == nb).values
        res[nom + "_vs_v1"]["NB" if nb else "REN"] = bootstrap_dif(t[s].reset_index(drop=True), v2[s], v1[s])
    print(nom, "D2 %.4f" % res[nom]["D2"], {k: (round(v["dif"], 4), [round(x, 4) for x in v["ic95"]]) for k, v in res[nom + "_vs_v1"].items()})
print("v1 D2 %.4f" % res["v1_T2b"]["D2"], {k: round(v, 4) for k, v in res["v1_T2b"].items() if k.startswith("D2")})
print("v2 e50", {k: round(v, 4) for k, v in res["v2_e50"].items() if k.startswith("D2") or k.startswith("AE")})
guardar_json(res, ENTREGA / "evolucion" / "pcv_v2_frente_v1.json")
# ponderado a la cartera 2025 (pesos de razón de densidad, solo filas 2023)
s = (t.year == 2023).values
t23 = t[s].reset_index(drop=True).merge(pd.read_parquet(TRABAJO / "pesos_2025_dev.parquet"), on="row_id", how="left")
assert t23.w2025.notna().all()
v2 = oof(comps, 0.5)
res["w2025_2023"] = {"v1": d2(t23.y.values, v1[s] * t23.c_fila.values, t23.w2025.values),
                     "v2_e50": d2(t23.y.values, v2[s] * t23.c_fila.values, t23.w2025.values),
                     "dif": bootstrap_dif(t23, v2[s], v1[s], w=t23.w2025.values)}
print("w2025 2023", {k: (round(v, 4) if isinstance(v, float) else (round(v["dif"], 4), [round(x, 4) for x in v["ic95"]])) for k, v in res["w2025_2023"].items()})
guardar_json(res, ENTREGA / "evolucion" / "pcv_v2_frente_v1.json")
