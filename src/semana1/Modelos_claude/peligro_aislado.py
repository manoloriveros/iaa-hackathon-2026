"""D² por peligro aislado en V24 (2024) de las frecuencias por peligro de Claude, con reserva de caso nominal y ±25 %.

Para cada peligro de un ramo reconstruye la predicción de 2024 del peligro en tres versiones: la frecuencia por la
severidad media del entrenamiento (partes guardadas), la misma con la relatividad GLM de severidad_cfs.py (capital y
sótano en hogar) y, si se indica, otra corrida de partes con la misma relatividad (por ejemplo la frecuencia aditiva).
La etiqueta es el coste T0 del peligro en la fila (y_<peligro>), con la reserva de caso de los abiertos aceptados del
peligro × 0,75, × 1 y × 1,25. Las predicciones no cambian entre escenarios y no se recalibran.
Uso: python3 peligro_aislado.py <ramo> <salida.json> <corrida_cfs>[,<corrida2>...] [<corrida_aditiva>[,<corrida2>...]]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import PERILS, WORK, d2
from experimentos import load
from influencia_reservas import reservas
from severidad_cfs import glm_gamma


def main():
    line, out = sys.argv[1], sys.argv[2]
    runs = {"CFS": sys.argv[3].split(",")}
    if len(sys.argv) > 4:
        runs["aditiva"] = sys.argv[4].split(",")
    df = load(line)
    yr = df.year.values
    trm, evm = yr <= 2023, yr == 2024
    row_ids = df.row_id.astype(str).values
    si = df.sum_insured.astype(float).values
    si = np.where(np.isfinite(si) & (si > 0), si, np.nan)
    bas = df.basement.astype(float).fillna(0).values
    med = np.nanmedian(si[trm]); zsi = np.log(np.where(np.isnan(si), med, si) / med)
    R = reservas().reindex(row_ids[evm]).fillna(0.0)
    rep = {}
    for p in PERILS[line]:
        n = df[f"n_{p}"].fillna(0).values.astype(float); yp = df[f"y_{p}"].fillna(0).values
        pos = trm & (n > 0) & (yp > 0)
        Z = np.column_stack([zsi] + ([bas] if p == "flood" else []))
        beta = glm_gamma(Z[pos], yp[pos] / n[pos], n[pos])
        rel = np.exp(Z @ beta[1:]); rel = rel / np.average(rel[pos], weights=n[pos])
        preds = {}
        for k, rr in runs.items():
            part = sum(np.load(WORK / r / f"v24_{p}.npy") for r in rr) / len(rr)
            if k == "CFS":
                preds["CFS_severidad_media"] = part
            preds[f"{k}_severidad_capital"] = part * rel[evm]
        rp = R[p].values if p in R.columns else np.zeros(evm.sum())
        y0 = yp[evm]
        res = {"reserva_CU": round(float(rp.sum()), 0), "coste_T0_CU": round(float(y0.sum()), 0)}
        for a in (0.75, 1.0, 1.25):
            y = y0 + (a - 1.0) * rp
            res[str(a)] = {k: round(d2(y, v), 6) for k, v in preds.items()}
        rep[p] = res
        print(line, p, json.dumps(res, ensure_ascii=False), flush=True)
    (WORK / out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
