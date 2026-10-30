"""Cross-year check: estimate the new-business factor from one PCV OOF year and apply it to the other."""
import numpy as np, pandas as pd
from comun import *
import receta
t, mu, _ = receta.oof_cruzado("pcv", ["T2b"], "ramo")
m = mu * t.c_fila.values; y = t.y.values; res = {}
for l in LINEAS:
    il = (t.line == l).values; curva = {}
    for z in np.round(np.arange(0, 1.01, 0.1), 1):
        dv = 0.0
        for a, b in [(2023, 2024), (2024, 2023)]:
            ia = il & (t.year.values == a); ib = il & (t.year.values == b)
            nb_a = ia & t.new_business.values; nb_b = ib & t.new_business.values
            ka = factor_tweedie(y[ia], m[ia]); ks = factor_tweedie(y[nb_a], m[nb_a] * ka)
            mb = m.copy(); mb[nb_b] = m[nb_b] * (1 + z * (ks - 1))
            kb = factor_tweedie(y[ib], mb[ib])
            dv += desviacion(y[ib], mb[ib] * kb).sum()
        curva[float(z)] = dv
    d0 = curva[0.0]
    res[l] = {"z_optimo": min(curva, key=curva.get), "cambio_relativo_desviacion_por_10mil": {k: round((v - d0) / d0 * 1e4, 2) for k, v in curva.items()}}
    print(l, res[l]["z_optimo"])
guardar_json(res, ENTREGA / "credibilidad_entre_anios.json")
