"""Exporta las predicciones por fila de una mezcla de Claude en V23 selección y V24, y resume las medias por ramo.

Las predicciones son exactamente las que miden los D² locales de mezcla3.py y robustez.py:
- V23: entrenamiento 2021-22, evaluación 2023 con cal_half = 1 (corte de selección), mezcla con forma y regla de nivel,
  sin factor de año siguiente (d2_sel);
- V24: entrenamiento 2021-23, evaluación 2024, misma mezcla multiplicada por el factor ftw de V23 (d2_v24_f23).
Cada fila lleva la etiqueta T0 y la reserva de caso de los siniestros abiertos aceptados asignados a ella
(escenarios_reserva.reserva_por_fila), para que la revisión pueda rehacer los escenarios T0 + (a - 1) x reserva.
Las medias por ramo comparan la media observada con la predicha (y su cociente) con a = 0,75, 1 y 1,25.
Uso: python3 exportar_predicciones.py <clave> <cand>=<spec>@<forma>@<nivel>
Escribe WORK/predicciones_v23_v24_<clave>.parquet y WORK/medias_por_ramo_<clave>.json
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK, d2
from escenarios_reserva import reserva_por_fila
from mezcla3 import labels
from robustez import blend, parse


def main():
    key = sys.argv[1]
    cn, spec, fm = parse(sys.argv[2])
    R = reserva_por_fila()
    filas, medias = [], {}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        res, bsel, b24, b25 = blend(spec, fm, line, ysel, y24, idx25, expos)
        medias[line] = {}
        for corte, ys, pr in (("V23", ysel, bsel), ("V24", y24, b24)):
            r = R.reindex(ys.index.astype(str)).fillna(0.0).values
            filas.append(pd.DataFrame({"row_id": ys.index.astype(str), "line": line, "corte": corte, "y_T0": ys.values,
                                       "reserva_caso": r, "prediction": pr}))
            m = {"filas": int(len(ys)), "media_predicha": round(float(pr.mean()), 4)}
            for a in (0.75, 1.0, 1.25):
                y = ys.values + (a - 1.0) * r
                m[f"a={a}"] = {"media_observada": round(float(y.mean()), 4), "observada_entre_predicha": round(float(y.sum() / pr.sum()), 4),
                               "d2": round(d2(y, pr), 6)}
            medias[line][corte] = m
        medias[line]["2025"] = {"filas": int(len(idx25)), "media_predicha": round(float(b25.mean()), 4)}
        print(line, json.dumps(medias[line], ensure_ascii=False), flush=True)
    df = pd.concat(filas, ignore_index=True)
    df.to_parquet(WORK / f"predicciones_v23_v24_{key}.parquet", index=False)
    agg = {}
    for corte in ("V23", "V24"):
        d = df[df.corte == corte]
        agg[corte] = {"filas": int(len(d)), "media_predicha": round(float(d.prediction.mean()), 4)}
        for a in (0.75, 1.0, 1.25):
            y = d.y_T0.values + (a - 1.0) * d.reserva_caso.values
            agg[corte][f"a={a}"] = {"media_observada": round(float(y.mean()), 4), "observada_entre_predicha": round(float(y.sum() / d.prediction.sum()), 4),
                                    "d2": round(d2(y, d.prediction.values), 6)}
    medias["agregado"] = agg
    rep = {"candidato": cn, "medias": medias,
           "definiciones": {"V23": "selección: entrenamiento 2021-22, evaluación 2023 con cal_half = 1; mezcla con forma y regla de nivel, sin factor (d2_sel)",
                            "V24": "entrenamiento 2021-23, evaluación 2024; mezcla con forma y regla de nivel por el factor ftw de V23 (d2_v24_f23)",
                            "a": "etiqueta T0 + (a - 1) x reserva de caso de los siniestros abiertos aceptados asignados a la fila"}}
    (WORK / f"medias_por_ramo_{key}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(agg, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
