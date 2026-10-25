"""Producción 2025 de la línea ML independiente.

Receta final (A03): T2b (LightGBM Tweedie preentrenado en el desarrollado 2021-2024) x nivel por ramo del emergente
2023-2024 x factor C1 del OOF cruzado de 2023-2024, sin tendencia.
Sensibilidades: C2 (ramo y negocio), tendencia del desarrollado, y la receta preinscrita (C2 + tendencia).
"""
import json
import numpy as np, pandas as pd
from comun import *
import receta

params_c2 = receta.parametros("pcv", ["T2b"], "ramo_nb")
params_c1 = dict(params_c2, calib="ramo")
tend = json.load(open(TRABAJO / "pred" / "prod" / "tendencia.json"))
p2c = receta.parametros("pcv", ["T2c"], "ramo")
variantes = {"final_C1": (params_c1, None), "C2": (params_c2, None), "C1_tendencia": (params_c1, tend),
             "preinscrita_C2_tendencia": (params_c2, tend), "T2c_C1": (p2c, None)}
sub = pd.read_parquet(DATOS / "emerging" / "sample_submission.parquet")
res = {"params": params_c2, "tendencia": tend, "variantes": {}}
for nom, (p, tt) in variantes.items():
    t, mu = receta.aplicar("prod", p, tt)
    out = sub[["row_id"]].merge(pd.DataFrame({"row_id": t.row_id.values, "prediction": mu}), on="row_id", how="left")
    ctl = {"filas": int(len(out)), "orden_igual_plantilla": bool((out.row_id.values == sub.row_id.values).all()),
           "nulos": int(out.prediction.isna().sum()), "min": float(out.prediction.min()),
           "positivas_estrictas": bool((out.prediction > 0).all()), "ids_unicos": bool(out.row_id.is_unique)}
    assert ctl["filas"] == 209063 and ctl["nulos"] == 0 and ctl["positivas_estrictas"] and ctl["orden_igual_plantilla"], ctl
    f = ENTREGA / ("prediccion_2025_mlind.csv" if nom == "final_C1" else f"prediccion_2025_mlind_{nom}.csv")
    out.to_csv(f, index=False, float_format="%.6f", lineterminator="\n")
    ctl["sha256"] = sha256(f); ctl["archivo"] = f.name
    tot = {}
    for l in LINEAS:
        i = (t.line == l).values; e = t.exposure.values[i]; nb = t.new_business.values[i]
        tot[l] = {"filas": int(i.sum()), "exposicion": float(e.sum()), "total": float(mu[i].sum()), "tasa": float(mu[i].sum() / e.sum()),
                  "tasa_NB": float(mu[i][nb].sum() / e[nb].sum()), "tasa_REN": float(mu[i][~nb].sum() / e[~nb].sum())}
    res["variantes"][nom] = {"controles": ctl, "totales": tot, "total": float(mu.sum())}
    print(nom, round(mu.sum()), {l: round(v["tasa"], 1) for l, v in tot.items()}, ctl["sha256"][:12])
# factor de balance (sum y / sum mu c) por ramo en el OOF cruzado 2023-2024 de la receta final: para la prima comercial
t, mu, _ = receta.oof_cruzado("pcv", ["T2b"], "ramo")
res["balance_oof_pcv"] = {l: float(t.y[(t.line == l).values].sum() / (mu * t.c_fila.values)[(t.line == l).values].sum()) for l in LINEAS}
guardar_json(res, ENTREGA / "produccion_2025.json")
print("balance", res["balance_oof_pcv"])
