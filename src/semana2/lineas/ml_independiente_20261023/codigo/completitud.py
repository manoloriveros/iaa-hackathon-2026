"""Completitud de reporte ponderada por coste por ramo y peligro (misma estimación que preparar_datos.py)."""
import numpy as np, pandas as pd
from comun import *

D = 1095
_G = None


def _estimar():
    c = pd.read_parquet(DATOS / "developed" / "claims.parquet")
    cols = [x for x in c.columns if x != "claim_id"]
    c = c[~(c.duplicated(cols, keep=False) & (c.claim_id.str.len() == 11))]
    c = c[c.status != "repudiated"].copy()
    c["loss_date"] = pd.to_datetime(c.loss_date); c["report_date"] = pd.to_datetime(c.report_date)
    c["neto"] = c.incurred_to_date - c.recoveries
    G = {}
    for (l, p), g in c.groupby(["line", "peril"]):
        g = g[(V - g.loss_date.values.astype("datetime64[D]")).astype(int) >= D]
        dly = (g.report_date - g.loss_date).dt.days.values; w = g.neto.values; ok = dly <= D
        cum = np.clip(np.bincount(dly[ok], weights=w[ok], minlength=D + 1).cumsum() / w[ok].sum(), 0, 1)
        G[(l, p)] = np.concatenate([[0.0], np.cumsum(np.concatenate([cum, np.ones(4000 - len(cum))]))])
    return G


def por_peligro(linea, peligro, inicio, fin):
    global _G
    if _G is None:
        _G = _estimar()
    g = _G[(linea, peligro)]
    s = pd.to_datetime(inicio).values.astype("datetime64[D]"); e = pd.to_datetime(fin).values.astype("datetime64[D]")
    a = np.clip((V - e).astype(int), 0, None); b = np.clip((V - s).astype(int), 0, None)
    return (g[b + 1] - g[a]) / (b - a + 1)
