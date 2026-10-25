"""Complemento: 2024 por segmento de nuevo negocio, ponderado a la mezcla de 2025 y mezcla 50/50 con A1 (exploratorio)."""
import json
import numpy as np, pandas as pd
from comun import *
import receta

OTROS = RAIZ / "comparacion" / "otros"
o = pd.read_parquet(OTROS / "predicciones_2024.parquet")
p = receta.parametros("dev", ["T2b"], "ramo"); t, mu = receta.aplicar("hold", p, None)
d = t.merge(o[["row_id", "address_id", "A1", "R0"]], on="row_id").merge(pd.read_parquet(TRABAJO / "pesos_2025_hold.parquet"), on="row_id", how="left")
d["T2b"] = mu * t.c_fila.values
for w in (0.25, 0.5, 0.75):
    d[f"mez{int(w*100)}"] = w * d.T2b + (1 - w) * d.A1
y = d.y.values
padre = {}
def f(x):
    while padre.setdefault(x, x) != x:
        padre[x] = padre[padre[x]]; x = padre[x]
    return x
for c, a in zip("C" + d.customer_id, "A" + d.address_id):
    rc, ra = f(c), f(a)
    if rc != ra: padre[ra] = rc
_, gi = np.unique([f("C" + c) for c in d.customer_id], return_inverse=True)
G = gi.max() + 1; rng = np.random.default_rng(7)
def boot(a, b, mask=None, w=None, B=2000):
    m = np.ones(len(y), bool) if mask is None else mask
    ww = np.ones(len(y)) if w is None else w
    da = desviacion(y, d[a].values); db = desviacion(y, d[b].values); sy = np.sqrt(y); out = []
    for s in range(0, B, 100):
        W = rng.poisson(1.0, size=(100, G)).astype(float)[:, gi] * ww * m
        ybar = (W @ y) / W.sum(1)
        dn = 2 * ((W @ sy) / (-0.25) - (W @ y) * ybar ** -0.5 / (-0.5) + W.sum(1) * ybar ** 0.5 / 0.5)
        out.append((W @ db - W @ da) / dn)
    r = np.concatenate(out)
    pt = d2(y[m], d[a].values[m], ww[m]) - d2(y[m], d[b].values[m], ww[m])
    return {"dif": float(pt), "ic95": [float(np.quantile(r, .025)), float(np.quantile(r, .975))], "p_mayor": float((r > 0).mean())}
res = {"D2": {}, "pares": {}}
nb = d.new_business.values; w25 = d.w2025.values
for m in ["T2b", "A1", "mez25", "mez50", "mez75", "R0"]:
    res["D2"][m] = {"todas": d2(y, d[m].values), "NB": d2(y[nb], d[m].values[nb]), "REN": d2(y[~nb], d[m].values[~nb]),
                    "pond_2025": d2(y, d[m].values, w25)}
res["pares"]["T2b-A1_NB"] = boot("T2b", "A1", mask=nb)
res["pares"]["T2b-A1_REN"] = boot("T2b", "A1", mask=~nb)
res["pares"]["T2b-A1_pond2025"] = boot("T2b", "A1", w=w25)
res["pares"]["mez50-A1"] = boot("mez50", "A1")
res["pares"]["mez50-T2b"] = boot("mez50", "T2b")
res["pares"]["mez50-A1_pond2025"] = boot("mez50", "A1", w=w25)
res["NB_filas_2024"] = int(nb.sum()); res["NB_siniestros_2024"] = int((y[nb] > 0).sum())
# nivel por ramo en NB de 2024: cociente observado/predicho
res["AE_NB"] = {m: {l: float(y[nb & (d.line == l).values].sum() / d[m].values[nb & (d.line == l).values].sum()) for l in LINEAS} for m in ["T2b", "A1"]}
guardar_json(res, RAIZ / "comparacion" / "comparacion_lineas_2.json")
print(json.dumps(res, indent=1))
