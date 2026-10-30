"""Explore paired differences on random 33% customer subsets of 2024.
Compare the fixed T2b/A1 blend with ML-family v2/v2.1 replacements. A1 serves
as the designated-model proxy; this is an exploratory historical comparison.
"""
import json, numpy as np, pandas as pd
from comun import *
from receta import tabla, componentes
from evaluar import mezcla_pesos
td = tabla("dev"); th = tabla("hold")
def pred(comps):
    Pd = componentes("dev", comps, td); Ph = componentes("hold", comps, th); mu = np.zeros(len(th))
    for l in LINEAS:
        il = (td.line == l).values; ih = (th.line == l).values
        M = np.column_stack([Pd[c][il] * td.c_fila.values[il] for c in comps])
        w = mezcla_pesos(td.y.values[il], M) if len(comps) > 1 else np.ones(1)
        w = 0.5 * w + 0.5 / len(comps) if len(comps) > 1 else w
        mu[ih] = np.column_stack([Ph[c][ih] for c in comps]) @ w * factor_tweedie(td.y.values[il], M @ w)
    return mu * th.c_fila.values
o = pd.read_parquet(RAIZ / "comparacion" / "otros" / "predicciones_2024.parquet")
d = th[["row_id", "y"]].merge(o[["row_id", "A1"]], on="row_id", how="left").merge(
    pd.read_parquet(TRABAJO / "pesos_2025_hold.parquet"), on="row_id", how="left")
assert d.A1.notna().all() and (d.row_id.values == th.row_id.values).all()
y = d.y.values
m = {"v1": 0.5 * pred(["T2b"]) + 0.5 * d.A1.values, "v2": 0.5 * pred(["T2b", "T2h", "FS", "T2o"]) + 0.5 * d.A1.values,
     "v21": 0.5 * pred(["T2b", "T2h", "FSt", "T2o"]) + 0.5 * d.A1.values}
rng = np.random.default_rng(20261024); res = {}
for k in ("v2", "v21"):
    r = {"corr_log": float(np.corrcoef(np.log(m[k]), np.log(m["v1"]))[0, 1]), "dif_total": d2(y, m[k]) - d2(y, m["v1"]),
         "dif_pond2025": d2(y, m[k], d.w2025.values) - d2(y, m["v1"], d.w2025.values)}
    sims = []
    for _ in range(1000):
        s = rng.random(len(y)) < 0.33
        sims.append(d2(y[s], m[k][s]) - d2(y[s], m["v1"][s]))
    r["sd_33"] = float(np.std(sims)); r["p_negativa_33"] = float(np.mean(np.array(sims) < 0))
    res[k] = r
    print(k, {a: round(b, 5) for a, b in r.items()})
guardar_json(res, ENTREGA / "evolucion" / "ruido_pareado_v2.json")
