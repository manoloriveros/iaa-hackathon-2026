"""Open the registered 2024 HOLD evaluation once for the frozen candidate list.
Read entrega/lista_congelada.json; use DEV OOF blend/calibration parameters and
the recorded hold-phase trend. This historical procedure is not a new selection.
"""
import json
import numpy as np, pandas as pd
from comun import *
from evaluar import metricas, bootstrap_dif
import receta

lista = json.load(open(ENTREGA / "lista_congelada.json"))
tend = json.load(open(TRABAJO / "pred" / "hold" / "tendencia.json"))
pesos = pd.read_parquet(TRABAJO / "pesos_2025_hold.parquet")
res = {"candidatos": {}, "bootstrap": {}}
mus = {}
for nombre, spec in lista["candidatos"].items():
    params = receta.parametros("dev", spec["componentes"], spec["calib"])
    t, mu_sin = receta.aplicar("hold", params, None)
    _, mu_con = receta.aplicar("hold", params, tend)
    t = t.merge(pesos, on="row_id", how="left")
    mus[nombre] = mu_con if lista.get("tendencia", True) else mu_sin
    res["candidatos"][nombre] = {"con_tendencia": metricas(t, mu_con), "sin_tendencia": metricas(t, mu_sin), "params": params}
    print(nombre, round(res["candidatos"][nombre]["con_tendencia"]["D2"], 4), round(res["candidatos"][nombre]["sin_tendencia"]["D2"], 4), flush=True)
ref = lista["referencias"]
for nombre in lista["candidatos"]:
    for r in ref:
        if nombre != r:
            res["bootstrap"][f"{nombre}-{r}"] = bootstrap_dif(t, mus[nombre], mus[r], B=1000)
elegido = lista["elegido"]
res["elegido"] = elegido
guardar_json(res, ENTREGA / "resultados_hold.json")
print(json.dumps({k: v for k, v in res["bootstrap"].items() if k.startswith(elegido)}, indent=1))
