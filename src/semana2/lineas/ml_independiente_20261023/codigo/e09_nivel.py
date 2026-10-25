"""E09: sensibilidad del D2 al nivel por ramo y al nivel del nuevo negocio (T2b + C1), DEV 2023 y HOLD 2024."""
import json
import numpy as np, pandas as pd
from comun import *
import receta

res = {}
fs = [0.8, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3]
for fase in ["dev", "hold"]:
    if fase == "dev":
        t, mu, _ = receta.oof_cruzado("dev", ["T2b"], "ramo")
    else:
        t, mu = receta.aplicar("hold", receta.parametros("dev", ["T2b"], "ramo"), None)
    m = mu * t.c_fila.values; y = t.y.values; base = d2(y, m)
    r = {"base": base, "ramo": {}, "nuevo_negocio": {}, "optimo": {}}
    for l in LINEAS:
        i = (t.line == l).values
        r["ramo"][l] = {str(f): d2(y, np.where(i, m * f, m)) - base for f in fs}
        r["nuevo_negocio"][l] = {str(f): d2(y, np.where(i & t.new_business.values, m * f, m)) - base for f in fs}
        r["optimo"][l] = {"factor_tweedie": factor_tweedie(y[i], m[i]),
                          "factor_tweedie_NB": factor_tweedie(y[i & t.new_business.values], m[i & t.new_business.values])}
    res[fase] = r
guardar_json(res, ENTREGA / "e09_nivel.json")
for fase in res:
    print(fase, round(res[fase]["base"], 4))
    for l in LINEAS:
        print(" ", l, "ramo", {k: round(v, 4) for k, v in res[fase]["ramo"][l].items()})
        print(" ", l, "NB  ", {k: round(v, 4) for k, v in res[fase]["nuevo_negocio"][l].items()}, {k: round(v, 3) for k, v in res[fase]["optimo"][l].items()})
