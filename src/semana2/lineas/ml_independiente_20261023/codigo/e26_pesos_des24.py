"""E26: pesos convexos de mezcla por ramo estimados en el desarrollado 2024 (DES24), troncos 2021-2023.

Cada tronco se renivela en 2024 (factor Tweedie del ramo) y los pesos minimizan la desviación Tweedie 1,5 de la mezcla.
Se informa también el D2 de la mezcla con pesos cruzados por pliegue de cliente dentro de 2024 (control de sobreajuste).
Uso: python3 e26_pesos_des24.py A,B,C,D salida.json
"""
import sys, json
import numpy as np, pandas as pd
from comun import *
from evaluar import mezcla_pesos

COMPS = sys.argv[1].split(","); SALIDA = sys.argv[2]
res = {"componentes": COMPS, "ramos": {}}
for l in LINEAS:
    base = None; M = []
    for c in COMPS:
        d = pd.read_parquet(TRABAJO / "pred" / "hold" / f"{c}des24_{l}.parquet")
        if base is None:
            base = d
        assert (d.row_id.values == base.row_id.values).all()
        mu = np.exp(d.raw.values) * d.exposure.values * d.c_fila.values
        M.append(mu * factor_tweedie(d.y.values, mu))
    M = np.column_stack(M); y = base.y.values
    w = mezcla_pesos(y, M)
    cust = pd.read_parquet(TRABAJO / f"base_developed_{l}.parquet", columns=["row_id", "customer_id"])
    folds = pliegue(base[["row_id"]].merge(cust, on="row_id", how="left").customer_id.values)
    cruz = np.zeros(len(y))
    for f in range(5):
        te = folds == f
        cruz[te] = M[te] @ mezcla_pesos(y[~te], M[~te])
    ind = {c: d2(y, M[:, i]) for i, c in enumerate(COMPS)}
    eq = M.mean(1)
    res["ramos"][l] = {"pesos": dict(zip(COMPS, np.round(w, 4).tolist())), "D2_individual": ind,
                       "D2_mezcla_en_muestra": d2(y, M @ w), "D2_mezcla_cruzada": d2(y, cruz),
                       "D2_pesos_iguales": d2(y, eq), "filas": int(len(y))}
    print(l, {c: round(v, 4) for c, v in ind.items()}, "pesos", dict(zip(COMPS, np.round(w, 3))),
          "mezcla %.4f cruzada %.4f iguales %.4f" % (d2(y, M @ w), d2(y, cruz), d2(y, eq)), flush=True)
guardar_json(res, ENTREGA / "evolucion" / SALIDA)
