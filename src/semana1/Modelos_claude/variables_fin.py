"""Variables de duración derivadas de la fecha de fin del periodo (mismo criterio F0 que mes_inicio y periodo_corto, D37).

El fin del periodo forma parte de los datos de test (define la exposición que se predice). Un periodo que termina antes
del 30 de diciembre lo hace por cambio a mitad de año, anulación o no renovación, y en el entrenamiento esos periodos
cortos tienen más siniestros por unidad de exposición de lo que predice un offset proporcional. Variables: fin_anticipado
(termina antes del 30 de diciembre), mes_fin, dias_al_fin_anio y la combinación inicio-fin (inicio_1ene, ambos extremos).
Uso: python3 variables_fin.py <ramo>  ->  WORK/fin_<ramo>.parquet
"""
from __future__ import annotations

import sys

import pandas as pd

from comun import WORK

line = sys.argv[1]
df = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "year", "period_start", "period_end", "exposure"])
end = df.period_end
dec30 = pd.to_datetime(df.year.astype(str) + "-12-30")
out = pd.DataFrame({"row_id": df.row_id.astype(str)})
out["fin_anticipado"] = (end < dec30).astype("float32")
out["mes_fin"] = end.dt.month.astype("float32")
out["dias_al_fin_anio"] = (pd.to_datetime(df.year.astype(str) + "-12-31") - end).dt.days.clip(lower=0).astype("float32")
out["inicio_1ene"] = ((df.period_start.dt.month == 1) & (df.period_start.dt.day == 1)).astype("float32")
out.to_parquet(WORK / f"fin_{line}.parquet", index=False)
print(line, out.drop(columns="row_id").describe().T[["mean", "std", "min", "max"]].round(3).to_string())
