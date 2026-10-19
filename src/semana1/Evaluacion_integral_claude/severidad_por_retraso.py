"""Severidad según el retraso de reporte y completitud en coste frente a completitud en conteos.

En cohortes maduras (pérdidas de 2021 y 2022, valoradas al 30-12-2024) se mide, por ramo y peligro, qué parte del coste
neto aceptado (incurrido - recuperaciones) llega con cada retraso de reporte. Si los siniestros tardíos son más caros,
la completitud en coste es menor que la de conteos que usa la exposición efectiva de D67/D68, y el T0 de 2024 queda por
debajo de su último aunque el número de siniestros esté bien desarrollado. Se aplica la curva de coste de la cohorte
2021 (retrasos hasta 1.094 días observables) a las pérdidas de 2024 con su ventana real hasta la valoración.
Uso: python3 severidad_por_retraso.py  ->  salidas/severidad_por_retraso.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

V = pd.Timestamp("2024-12-30")
OUT = Path(__file__).resolve().parent / "salidas"
c = pd.read_parquet("/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Limpieza/runs/preaudit_20261016T211816Z_817285a5/data/claims.parquet")
c = c[(c.status != "repudiated") & (~c.audit_pre00)].copy()
c["loss_date"] = pd.to_datetime(c.loss_date); c["report_date"] = pd.to_datetime(c.report_date)
c["net"] = c.incurred_to_date - c.recoveries
c["delay"] = (c.report_date - c.loss_date).dt.days.clip(lower=0)
c["ly"] = c.loss_date.dt.year
res = {}
edges = [0, 7, 30, 90, 180, 365, 730, 1100]
for (line, peril), g in c.groupby(["line", "peril"]):
    m21 = g[g.ly == 2021]
    out = {}
    if len(m21) < 50:
        continue
    tot_n, tot_c = len(m21), m21.net.sum()
    buckets = pd.cut(m21.delay, edges, right=False)
    t = m21.groupby(buckets, observed=False).agg(n=("net", "size"), coste=("net", "sum"))
    t["sev"] = t.coste / t.n
    out["cohorte_2021_por_retraso"] = {str(k): {"n": int(r.n), "cuota_n": round(r.n / tot_n, 4), "cuota_coste": round(r.coste / tot_c, 4), "sev": round(float(r.sev), 1) if r.n else None} for k, r in t.iterrows()}
    # curvas acumuladas por día (cohorte 2021, retraso observable hasta ~1.094 días)
    d = np.arange(0, 1095)
    sd = np.sort(m21.delay.values)
    Fn = np.searchsorted(sd, d, side="right") / tot_n
    order = np.argsort(m21.delay.values)
    cum_c = np.cumsum(m21.net.values[order]) / tot_c
    Fc = np.concatenate([[0.0], cum_c])[np.searchsorted(m21.delay.values[order], d, side="right")]
    # pérdidas de 2024: ventana real hasta la valoración, completitud media en conteos y en coste
    g24 = g[g.ly == 2024]
    w = np.clip((V - g24.loss_date).dt.days.values, 0, 1094)
    # aproximación: completitud media de una pérdida de 2024 = curva evaluada en su ventana, promediada sobre pérdidas
    # observadas no sirve (ya están reportadas); se usa el calendario uniforme de días de 2024
    days = pd.date_range("2024-01-01", V, freq="D")
    wd = np.clip((V - days).days.values, 0, 1094)
    out["completitud_2024_conteos"] = round(float(Fn[wd].mean()), 4)
    out["completitud_2024_coste"] = round(float(Fc[wd].mean()), 4)
    out["razon_coste_conteos"] = round(out["completitud_2024_coste"] / out["completitud_2024_conteos"], 4) if out["completitud_2024_conteos"] else None
    # severidad de 2024 frente a la de 2021 con el mismo retraso máximo (reportados dentro de la ventana típica)
    sev21_corto = m21.loc[m21.delay <= 180, "net"].mean()
    sev24_corto = g24.loc[g24.delay <= 180, "net"].mean()
    out["sev_reportados_180d"] = {"2021": round(float(sev21_corto), 1), "2024": round(float(sev24_corto), 1),
                                  "razon_2024_2021": round(float(sev24_corto / sev21_corto), 4)}
    out["abiertos_2024"] = round(float((g24.status == "open").mean()), 4)
    res[f"{line}/{peril}"] = out
    print(line, peril, "conteos", out["completitud_2024_conteos"], "coste", out["completitud_2024_coste"], "razón", out["razon_coste_conteos"],
          "sev<=180d 2021/2024", out["sev_reportados_180d"], "abiertos 2024", out["abiertos_2024"], flush=True)
(OUT / "severidad_por_retraso.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
