"""Prepare the historical, unsent 50/50 designated-production and ML-family blend option."""
import json
import numpy as np, pandas as pd
from comun import *
OTROS = RAIZ / "comparacion" / "otros"
sub = pd.read_parquet(DATOS / "emerging" / "sample_submission.parquet")[["row_id"]]
a = pd.read_csv(PRIVADO / "prediccion_2025_mlind.csv", dtype={"row_id": str})
b = pd.read_csv(OTROS / "A1fixF1b3n_2025.csv", dtype={"row_id": str})
assert (a.row_id.values == sub.row_id.values).all() and (b.row_id.values == sub.row_id.values).all()
m = pd.DataFrame({"row_id": sub.row_id, "prediction": 0.5 * a.prediction.values + 0.5 * b.prediction.values})
assert m.prediction.notna().all() and (m.prediction > 0).all() and len(m) == 209063 and m.row_id.is_unique
f = PRIVADO / "mezcla50_designada_mlind_2025.csv"
m.to_csv(f, index=False, float_format="%.6f", lineterminator="\n")
pref = m.row_id.str[0]
r = {"archivo": f.name, "sha256": sha256(f), "filas": len(m), "total": float(m.prediction.sum()),
     "por_ramo": {k: float(v) for k, v in m.groupby(pref).prediction.sum().items()},
     "fuentes": {"mlind": sha256(PRIVADO / "prediccion_2025_mlind.csv"), "designada": sha256(OTROS / "A1fixF1b3n_2025.csv")}}
guardar_json(r, RAIZ / "comparacion" / "mezcla50_info.json"); print(json.dumps(r, indent=1))
