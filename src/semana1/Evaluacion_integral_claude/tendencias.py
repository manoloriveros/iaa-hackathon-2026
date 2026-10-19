"""Tendencias de frecuencia y severidad por ramo y peligro, 2021-2024, con la madurez controlada.

Frecuencia del peligro p en el año a: número de siniestros aceptados del peligro / exposición efectiva del peligro
(e_ef_p de D68, que descuenta el reporte pendiente de conteos). Severidad: coste T0 del peligro / número de siniestros;
la de 2024 (y en menor medida 2023) sigue inmadura en importes por las reservas de caso y los grandes tardíos, así que la
tendencia de severidad se mide con 2021-2023 y se informa 2024 aparte. Para cada ramo se compara la tasa de coste por
exposición efectiva con un ajuste log-lineal y se extrapola a 2025 con el horizonte explícito desde la media ponderada de
los años de entrenamiento, para contrastarla con el factor de año siguiente que usan las mezclas.
Uso: python3 tendencias.py  ->  salidas/tendencias.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/claude/modelos_claude")
from comun import PERILS, WORK  # noqa: E402

OUT = Path(__file__).resolve().parent / "salidas"
res = {}
for line in ["motor", "buildings", "contents"]:
    cols = ["year", "T0", "e_ef_coste", "exposure"] + [f"y_{p}" for p in PERILS[line]] + [f"n_{p}" for p in PERILS[line]] + [f"e_ef_{p}" for p in PERILS[line]]
    df = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=cols)
    df = df[df.year <= 2024]
    out = {"perils": {}}
    for p in PERILS[line]:
        g = df.groupby("year").agg(n=(f"n_{p}", "sum"), y=(f"y_{p}", lambda s: s.fillna(0).sum()), e=(f"e_ef_{p}", "sum"))
        g["frec"] = g.n / g.e
        g["sev"] = g.y / g.n
        yrs = g.index.values.astype(float)
        bf = np.polyfit(yrs - 2022.5, np.log(g.frec.values), 1, w=np.sqrt(g.n.values))[0]
        m = g.index <= 2023
        bs = np.polyfit(yrs[m] - 2022, np.log(g.sev.values[m]), 1, w=np.sqrt(g.n.values[m]))[0]
        out["perils"][p] = {"frecuencia": {int(k): round(float(v), 5) for k, v in g.frec.items()},
                            "severidad": {int(k): round(float(v), 1) for k, v in g.sev.items()},
                            "tendencia_frecuencia_anual": round(float(np.exp(bf) - 1), 4),
                            "tendencia_severidad_anual_2021_2023": round(float(np.exp(bs) - 1), 4)}
    g = df.groupby("year").agg(y=("T0", lambda s: s.fillna(0).sum()), e=("e_ef_coste", "sum"))
    g["tasa"] = g.y / g.e
    yrs = g.index.values.astype(float)
    b, a = np.polyfit(yrs - 2022.5, np.log(g.tasa.values), 1, w=g.e.values)
    wmean = float((g.index.values * g.e.values).sum() / g.e.values.sum())
    out["tasa_coste_por_exposicion_efectiva"] = {int(k): round(float(v), 2) for k, v in g.tasa.items()}
    out["tendencia_tasa_anual"] = round(float(np.exp(b) - 1), 4)
    out["anio_medio_entrenamiento_2021_2024"] = round(wmean, 3)
    out["horizonte_2025_desde_media"] = round(2025.5 - wmean - 0.5, 3)
    out["factor_tendencia_2025_sobre_media"] = round(float(np.exp(b * (2025.0 - wmean))), 4)
    out["tasa_2025_extrapolada"] = round(float(np.exp(a + b * 2.5)), 2)
    res[line] = out
    print(line, json.dumps({k: v for k, v in out.items() if k != "perils"}, ensure_ascii=False), flush=True)
    for p, v in out["perils"].items():
        print("   ", p, "frec", v["tendencia_frecuencia_anual"], "sev", v["tendencia_severidad_anual_2021_2023"], v["frecuencia"], v["severidad"], flush=True)
(OUT / "tendencias.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
