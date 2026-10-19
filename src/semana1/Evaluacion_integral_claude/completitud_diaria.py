"""Completitud de reporte diaria frente a la mensual de D67 y su efecto en la exposición efectiva de 2024.

1. Distribución del retraso de reporte en días por ramo y peligro (siniestros aceptados), con un estimador de
   producto para datos truncados por la derecha: g(d) = P(retraso <= d | retraso <= d+1) se estima solo con pérdidas cuya
   ventana hasta la valoración (30-12-2024) es al menos d+1 días; F(d) = prod_{k>=d} g(k) x F(D), con la cola F(D) del
   chain-ladder mensual de D67 en el retraso equivalente.
2. Completitud de cada fila de 2024: media de F(V - t) sobre los días cubiertos del periodo, ponderada por la mezcla de
   coste de los peligros del ramo en años maduros (2021-2022), como e_ef_coste.
3. Compara con e_ef_coste (D68) por mes de inicio y en total, y guarda e_ef_diaria por fila para pruebas posteriores.
Uso: python3 completitud_diaria.py  ->  salidas/completitud_diaria_<ramo>.parquet y salidas/completitud_resumen.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/claude/modelos_claude")
from comun import BASESDIR, PERILS, WORK  # noqa: E402

V = pd.Timestamp("2024-12-30")
DMAX = 1460
OUT = Path(__file__).resolve().parent / "salidas"
OUT.mkdir(exist_ok=True)

a = pd.read_parquet(BASESDIR / "tables" / "asignacion_por_siniestro.parquet")
a = a[(a.status != "repudiated") & (a.category == "unica")].copy()
a["delay"] = (a.report_date - a.loss_date).dt.days.clip(lower=0)
a["window"] = (V - a.loss_date).dt.days
fac = pd.read_csv(BASESDIR / "tables" / "factores_desarrollo_conteos.csv")
resumen = {}
for line in ["motor", "buildings", "contents"]:
    feat = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "year", "period_start", "period_end", "exposure", "e_ef_coste"]
                           + [f"y_{p}" for p in PERILS[line]] + [f"e_ef_{p}" for p in PERILS[line]])
    mature = feat.year.isin([2021, 2022])
    share = {p: feat.loc[mature, f"y_{p}"].fillna(0).sum() for p in PERILS[line]}
    tot = sum(share.values()); share = {p: v / tot for p, v in share.items()}
    r24 = feat[feat.year == 2024].copy()
    days = pd.date_range("2024-01-01", V, freq="D")
    comp_day = np.zeros(len(days))
    curves = {}
    for p in PERILS[line]:
        c = a[(a.line == line) & (a.peril == p)]
        d, w = c.delay.values, c.window.values
        g = np.ones(DMAX)
        for k in range(DMAX - 1):
            m = w >= k + 1
            den = (d[m] <= k + 1).sum()
            g[k] = (d[m] <= k).sum() / den if den > 0 else 1.0
        # cola: completitud en DMAX desde el factor mensual a último de D67 en el retraso equivalente (meses)
        fl = fac[(fac.line == line) & (fac.peril == p)].set_index("lag_meses")["factor_a_ultimo"]
        lag_m = min(int(DMAX / 30.44), int(fl.index.max()))
        F_tail = 1.0 / float(fl.loc[lag_m]) if lag_m in fl.index else 1.0
        F = np.empty(DMAX)
        F[-1] = F_tail
        for k in range(DMAX - 2, -1, -1):
            F[k] = F[k + 1] * g[k]
        curves[p] = F
        lag = (V - days).days.values
        comp_day += share[p] * F[np.minimum(lag, DMAX - 1)]
    # media de la completitud sobre los días cubiertos de cada fila (sumas acumuladas)
    cs = np.concatenate([[0.0], np.cumsum(comp_day)])
    s_idx = (r24.period_start.clip(lower=days[0]) - days[0]).dt.days.values
    e_idx = (r24.period_end.clip(upper=V) - days[0]).dt.days.values
    ndays = np.maximum(e_idx - s_idx + 1, 1)
    c_row = np.where(e_idx >= s_idx, (cs[np.maximum(e_idx + 1, 0)] - cs[np.maximum(s_idx, 0)]) / ndays, 0.0)
    r24["completitud_diaria"] = c_row
    r24["e_ef_diaria"] = r24.exposure * c_row
    r24["mes_inicio"] = r24.period_start.dt.month
    g_m = r24.groupby("mes_inicio").agg(expo=("exposure", "sum"), mensual=("e_ef_coste", "sum"), diaria=("e_ef_diaria", "sum"))
    g_m["razon_diaria_mensual"] = (g_m.diaria / g_m.mensual).round(4)
    r24[["row_id", "e_ef_coste", "e_ef_diaria", "completitud_diaria"]].assign(row_id=lambda x: x.row_id.astype(str)).to_parquet(OUT / f"completitud_diaria_{line}.parquet", index=False)
    resumen[line] = {"mezcla_coste_madura": {p: round(v, 4) for p, v in share.items()},
                     "completitud_2024_mensual": round(float(r24.e_ef_coste.sum() / r24.exposure.sum()), 5),
                     "completitud_2024_diaria": round(float(r24.e_ef_diaria.sum() / r24.exposure.sum()), 5),
                     "completitud_dia_31dic_aprox": {p: round(float(curves[p][0]), 4) for p in PERILS[line]},
                     "completitud_a_30_dias": {p: round(float(curves[p][30]), 4) for p in PERILS[line]},
                     "completitud_a_365_dias": {p: round(float(curves[p][365]), 4) for p in PERILS[line]},
                     "razon_por_mes_inicio": g_m.razon_diaria_mensual.to_dict()}
    print(line, json.dumps(resumen[line], ensure_ascii=False), flush=True)
(OUT / "completitud_resumen.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False))
