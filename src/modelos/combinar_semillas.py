"""Promedia corridas de producción del mismo modelo con semillas distintas (v24.parquet y prediccion_2025.parquet).

Cada corrida aporta según su número de semillas. La selección V23 no cambia (es un único modelo con parada temprana).
Uso: python3 combinar_semillas.py <nombre_salida> <corrida1> <corrida2> [...]
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from comun import WORK, d2

name, runs = sys.argv[1], sys.argv[2:]
out = WORK / name
out.mkdir(parents=True, exist_ok=True)
reps = [json.loads((WORK / r / "resumen.json").read_text()) for r in runs]
w = [r.get("seeds", 1) for r in reps]
rep = {"corridas": runs, "semillas": w}
for f, col in (("v24.parquet", "mu"), ("prediccion_2025.parquet", "prediction")):
    frames = [pd.read_parquet(WORK / r / f).set_index("row_id") for r in runs]
    base = frames[0].copy()
    for fr in frames[1:]:
        assert (fr.index == base.index).all()
    base[col] = sum(wi * fr[col] for wi, fr in zip(w, frames)) / sum(w)
    base.reset_index().to_parquet(out / f, index=False)
    if f == "v24.parquet":
        rep["d2_v24"] = round(d2(base.y.values, base.mu.values), 5)
        rep["d2_v24_por_corrida"] = [round(d2(fr.y.values, fr.mu.values), 5) for fr in frames]
    else:
        rep["pred_2025_total_CU"] = round(float(base.prediction.sum()), 2)
(out / "resumen.json").write_text(json.dumps(rep, indent=1))
print(json.dumps(rep), flush=True)
