"""J: ¿el componente de R3 debido a los factores es ajuste dentro de muestra? Razón de escalar óptimo del paso de factores
dentro de muestra (pool) y fuera de tiempo, frente al cambio de Σ√μ del mismo paso. Y R3 con pesos iguales por año."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
from J_lib import *
A3 = 1 + 0.927 * (1.3212 - 1)
ser = series(); pool = pd.concat([ser["DEV23_T2b"], ser["HOLD24_T2b"]])
res = {}
for nm, tr, te in (("pool->pool", pool, pool), ("23->24", ser["DEV23_T2b"], ser["HOLD24_T2b"]), ("24->23", ser["HOLD24_T2b"], ser["DEV23_T2b"])):
    T3 = TransfF3(tr, A3); m_sf = T3(te, te.m.values, con_factores=False); m_f = T3(te, te.m.values); c = celda(te); y = te.y.values
    r = {}
    for cc in ["motor_0", "motor_1", "contents_0", "contents_1"]:
        i = c == cc
        r[cc] = {"kopt_ratio": kopt(y[i], m_f[i]) / kopt(y[i], m_sf[i]), "sqrt_ratio": np.sqrt(m_f[i]).sum() / np.sqrt(m_sf[i]).sum()}
    res[nm] = r
info = json.load(open(R + "exp26/F3_info.json"))["razon_por_serie"]
res["R3_igual_por_año"] = {cc: 0.5 * info["DEV23_T2b"][cc] + 0.5 * np.mean([info[k][cc] for k in ("HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla")]) for cc in CELS}
res["R3_autor"] = json.load(open(R + "exp26/F3_info.json"))["razon_nivel_local"]
print(json.dumps(res, indent=1, default=float))
json.dump(res, open(R + "revision/J_R3_check.json", "w"), indent=1, default=float)
