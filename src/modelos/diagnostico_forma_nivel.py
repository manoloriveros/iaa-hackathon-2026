"""Efecto de la calibración de forma sobre el nivel de 2025 frente al de V23 y V24 (diagnóstico sin etiquetas de 2025).

La forma mu' = e (e/ē)^(b-1) g (r/g)^a cambia el total de cada corte. En V23 y V24 ese cambio lo absorbe el factor ftw,
que se ajusta después de la forma; en 2025 no hay etiqueta y el factor es la media de los dos. Si la forma cambia el total
de 2025 en una proporción distinta que en V23/V24 (porque 2025 usa exposición nominal y V23/V24 la efectiva, o porque la
dispersión de tasas cambia), el nivel de 2025 se desplaza respecto de la misma mezcla sin forma. Este script mide, por
ramo, L = total con forma / total sin forma en cada corte, los factores con y sin forma y el total 2025 resultante.
Uso: python3 diagnostico_forma_nivel.py <spec_json> <forma> <nivel|-> [<salida.json>]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK, d2
from mezcla3 import component, ftw, labels, shape_rate, sin_referencia


def main():
    spec = json.load(open(sys.argv[1]))
    forma = {kv.split(":")[0]: (float(kv.split(":")[1]), float(kv.split(":")[2])) for kv in sys.argv[2].split(",") if kv}
    nivel = sys.argv[3]
    excl = sin_referencia({"nivel": None if nivel == "-" else nivel})
    rep = {}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        ex = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        exn = (fe.exposure.reindex(ysel.index).values, fe.exposure.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        raw = []
        for run, sel_name, w in spec[line]:
            s, v, p = component(run, sel_name, line)
            raw.append((run, w, s.reindex(ysel.index).values, v.reindex(y24.index).values, p.reindex(idx25).values))
        own = [r for r in raw if r[0] not in excl]
        wo = sum(r[1] for r in own)
        ref = [sum(r[1] * r[j].sum() for r in own) / wo for j in (2, 3, 4)]
        ws = np.array([r[1] for r in raw], float); ws /= ws.sum()
        blends = [sum(w * r[j] * ref[j - 2] / r[j].sum() for w, r in zip(ws, raw)) for j in (2, 3, 4)]
        a, b = forma.get(line, (1.0, 1.0))
        shaped = [shape_rate(m, e, a, b) for m, e in zip(blends, ex)]
        L = [float(s.sum() / m.sum()) for s, m in zip(shaped, blends)]
        f_sin = [ftw(ysel.values, blends[0]), ftw(y24.values, blends[1])]
        f_con = [ftw(ysel.values, shaped[0]), ftw(y24.values, shaped[1])]
        tot25_sin = float(blends[2].sum() * np.mean(f_sin)); tot25_con = float(shaped[2].sum() * np.mean(f_con))
        # dispersión de la exposición usada en cada corte: media de (e/ē)^(b-1) y cuantiles de e
        disp = {}
        for k, e in zip(("V23", "V24", "2025"), ex):
            eb = np.exp(np.log(e).mean())
            disp[k] = {"media_(e/eb)^(b-1)": round(float(np.mean((e / eb) ** (b - 1.0))), 4), "e_p10_p50_p90": [round(float(q), 3) for q in np.quantile(e, [0.1, 0.5, 0.9])],
                       "media_e": round(float(e.mean()), 4)}
        rep[line] = {"forma": [a, b], "L_V23_V24_2025": [round(x, 4) for x in L], "f_sin_forma": [round(x, 4) for x in f_sin], "f_con_forma": [round(x, 4) for x in f_con],
                     "total_2025_sin_forma": round(tot25_sin, 1), "total_2025_con_forma": round(tot25_con, 1), "cociente_con_sin": round(tot25_con / tot25_sin, 4),
                     "d2_sin": [round(d2(ysel.values, blends[0]), 5), round(d2(y24.values, blends[1] * f_sin[0]), 5)],
                     "d2_con": [round(d2(ysel.values, shaped[0]), 5), round(d2(y24.values, shaped[1] * f_con[0]), 5)], "exposicion": disp}
        print(line, json.dumps(rep[line], ensure_ascii=False), flush=True)
    if len(sys.argv) > 4:
        (WORK / sys.argv[4]).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
