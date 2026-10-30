"""Compare E10-E12 with references in DEV (uncalibrated/C1) and HOLD (DEV-derived C1), using customer resampling."""
import json
import numpy as np, pandas as pd
from comun import *
from evaluar import metricas, bootstrap_dif
import receta
res = {}
tdev = receta.tabla("dev")
for fase in ["dev", "hold"]:
    res[fase] = {}
    for c in ["T2", "T2cap", "T2b", "T2bs4", "T2bw"]:
        if fase == "dev":
            t, mu, _ = receta.oof_cruzado("dev", [c], "ramo"); _, mu0, _ = receta.oof_cruzado("dev", [c], "sin")
            res[fase][c] = {"C1": metricas(t, mu), "sin": metricas(t, mu0)}
        else:
            t, mu = receta.aplicar("hold", receta.parametros("dev", [c], "ramo"), None)
            res[fase][c] = {"C1": metricas(t, mu)}
        res[fase][c]["_mu"] = mu
    for a, b in [("T2cap", "T2"), ("T2bs4", "T2b"), ("T2bw", "T2b")]:
        res[fase][f"{a}-{b}"] = bootstrap_dif(t, res[fase][a]["_mu"], res[fase][b]["_mu"], B=1000)
    for c in ["T2", "T2cap", "T2b", "T2bs4", "T2bw"]:
        res[fase][c].pop("_mu")
guardar_json(res, ENTREGA / "e10_e12_resultados.json")
for fase in res:
    for k, v in res[fase].items():
        if "-" in k: print(fase, k, round(v["dif"], 4), [round(x, 4) for x in v["ic95"]], v["p_mayor"])
        else: print(fase, k, {kk: round(vv["D2"], 4) for kk, vv in v.items()}, {l: round(v["C1"][f"D2_{l}"], 4) for l in LINEAS})
