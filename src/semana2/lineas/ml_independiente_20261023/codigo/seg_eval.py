"""D2 por segmento (nuevo negocio / renovación) y por ramo, DEV (C1 cruzado) y HOLD (C1), renivelado por ramo y segmento para medir solo estructura."""
import sys, numpy as np, pandas as pd
from comun import *
from receta import tabla, componentes
from evaluar import calibrar_cruzado
cands = sys.argv[1:]
td = tabla("dev").merge(pd.read_parquet(TRABAJO / "pesos_2025_dev.parquet"), on="row_id", how="left"); th = tabla("hold")
Pd = componentes("dev", cands, td); Ph = componentes("hold", cands, th)
folds = pliegue(td.customer_id.values)
filas = []
for c in cands:
    for fase, t, mu in (("dev", td, calibrar_cruzado(td, Pd[c], folds)), ("hold", th, Ph[c])):
        m = mu * t.c_fila.values; y = t.y.values
        r = {"cand": c, "fase": fase}
        for nb in (True, False):
            s = t.new_business.values == nb
            mm = m.copy()
            for l in LINEAS:  # renivelado por ramo dentro del segmento
                i = s & (t.line == l).values; mm[i] *= factor_tweedie(y[i], m[i])
            r["NB" if nb else "REN"] = d2(y[s], mm[s])
        filas.append(r)
df = pd.DataFrame(filas).pivot(index="cand", columns="fase", values=["NB", "REN"])
print(df.round(4))
