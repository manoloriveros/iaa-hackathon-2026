"""E26: HOLD 2024 (exploratorio) de mezclas con pesos fijos de DES24 o encogidos (e50) estimados en DEV; nivel C1 de DEV."""
import sys, json, numpy as np, pandas as pd
from comun import *
from evaluar import metricas, bootstrap_dif, mezcla_pesos
from receta import tabla, componentes
fij = json.load(open(ENTREGA / "evolucion" / "e26_pesos_des24.json"))
td = tabla("dev"); th = tabla("hold")
def pred(comps, modo):
    Pd = componentes("dev", comps, td); Ph = componentes("hold", comps, th); mu = np.zeros(len(th))
    for l in LINEAS:
        il = (td.line == l).values; ih = (th.line == l).values
        M = np.column_stack([Pd[c][il] * td.c_fila.values[il] for c in comps])
        if modo == "des24":
            w = np.array(list(fij["ramos"][l]["pesos"].values()))
        else:
            w = mezcla_pesos(td.y.values[il], M) if len(comps) > 1 else np.ones(1)
            w = 0.5 * w + 0.5 / len(comps) if len(comps) > 1 else w
        k = factor_tweedie(td.y.values[il], M @ w)
        mu[ih] = np.column_stack([Ph[c][ih] for c in comps]) @ w * k
    return mu
R = {"T2b": pred(["T2b"], "e50"), "v2": pred(["T2b", "T2h", "FS", "T2o"], "e50"),
     "v2t": pred(["T2b", "T2h", "FSt", "T2o"], "e50"), "v3": pred(["T2b", "T2h", "FSt", "T2o"], "des24"), "FSt": pred(["FSt"], "e50")}
out = {}
for k, v in R.items():
    m = metricas(th, v); out[k] = {"D2": m["D2"], **{f"D2_{l}": m[f"D2_{l}"] for l in LINEAS}}
    if k != "T2b":
        out[k]["vs_T2b"] = bootstrap_dif(th, v, R["T2b"])
    if k in ("v2t", "v3"):
        out[k]["vs_v2"] = bootstrap_dif(th, v, R["v2"])
    print(k, {a: (round(b, 4) if isinstance(b, float) else (round(b["dif"], 4), [round(x, 4) for x in b["ic95"]])) for a, b in out[k].items()})
guardar_json(out, ENTREGA / "evolucion" / "e26_hold.json")
