"""Diferencias pareadas de D² en 2024 de una mezcla de Claude frente a H, A_G y otra mezcla, con IC95 por cliente, dirección y región.

Codex usa, además de cliente y dirección, un remuestreo por región (12 regiones) como control de incertidumbre regional.
Este script calcula las tres versiones con multiplicadores Poisson(1), 1.000 réplicas y denominador fijo, con la etiqueta
T0 + (a - 1) x reserva de caso de los abiertos aceptados (a = 0,75; 1; 1,25), por ramo y en el agregado. Informa también
la diferencia dentro de cada región y cuántas regiones quedan negativas. Cada agrupación usa su propio generador.
Uso: python3 intervalos_region.py <salida.json> <cand>=<spec>@<forma>@<nivel> <otra>=<spec>@<forma>@<nivel>
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK, deviance
from escenarios_reserva import C, reserva_por_fila
from mezcla3 import labels
from robustez import blend, parse

B = 1000


def ic(dif, groups, null, rng):
    codes, inv = np.unique(groups, return_inverse=True)
    d = np.bincount(inv, weights=dif)
    bs = np.concatenate([rng.poisson(1.0, size=(50, len(d))) @ d for _ in range(B // 50)]) / null
    return [round(float(np.quantile(bs, 0.025)), 6), round(float(np.quantile(bs, 0.975)), 6)], round(float((bs > 0).mean()), 3)


def main():
    out = sys.argv[1]
    (cn, cspec, cfm), (on, ospec, ofm) = parse(sys.argv[2]), parse(sys.argv[3])
    R = reserva_por_fila()
    ag = pd.read_parquet(f"{C}/crossfit_meta_gam_guard/predictions_V24_crossfit.parquet", columns=["row_id", "meta_gam"]).set_index("row_id").meta_gam
    hh = pd.read_parquet(f"{C}/geometric_meta_nested/V24.parquet", columns=["row_id", "candidate"]).set_index("row_id").candidate
    V = {k: [] for k in ("y", "r", "cu", "ad", "rg", "ln", cn, on, "H", "A_G")}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "customer_id", "address_id", "region", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        V[cn].append(blend(cspec, cfm, line, ysel, y24, idx25, expos)[2]); V[on].append(blend(ospec, ofm, line, ysel, y24, idx25, expos)[2])
        V["H"].append(hh.reindex(y24.index).values); V["A_G"].append(ag.reindex(y24.index).values)
        f = fe.reindex(y24.index)
        V["y"].append(y24.values); V["r"].append(R.reindex(y24.index.astype(str)).fillna(0.0).values)
        V["cu"].append(f.customer_id.astype(str).values); V["ad"].append(f.address_id.astype(str).values)
        V["rg"].append(f.region.astype(str).values); V["ln"].append(np.full(len(y24), line))
    V = {k: np.concatenate(v) for k, v in V.items()}
    rep = {"candidato": cn, "comparadores": [on, "H", "A_G"], "escenarios": {}}
    for a in (0.75, 1.0, 1.25):
        y_all = V["y"] + (a - 1.0) * V["r"]
        res = {}
        for scope in LINES + ["agregado"]:
            msk = np.ones(len(y_all), bool) if scope == "agregado" else (V["ln"] == scope)
            y = y_all[msk]; null = deviance(y, np.full_like(y, y.mean())).sum()
            row = {}
            for k in (on, "H", "A_G"):
                dif = deviance(y, V[k][msk]) - deviance(y, V[cn][msk])
                rngs = {g: np.random.default_rng(20261018 + i) for i, g in enumerate(("cu", "ad", "rg"))}
                (icu, pcu), (iad, pad), (irg, prg) = (ic(dif, V[g][msk], null, rngs[g]) for g in ("cu", "ad", "rg"))
                por_region = pd.Series(dif).groupby(V["rg"][msk]).sum() / null
                row[f"{cn}_menos_{k}"] = {"dif": round(float(dif.sum() / null), 6), "ic95_cliente": icu, "ic95_direccion": iad, "ic95_region": irg,
                                          "P_mayor_que_0_region": prg, "regiones_negativas": int((por_region < 0).sum()), "regiones": int(len(por_region))}
            res[scope] = row
            print(f"a={a} {scope} " + " ".join(f"{k}: {row[f'{cn}_menos_{k}']['dif']:+.6f} cli {row[f'{cn}_menos_{k}']['ic95_cliente']} dir {row[f'{cn}_menos_{k}']['ic95_direccion']} reg {row[f'{cn}_menos_{k}']['ic95_region']} neg {row[f'{cn}_menos_{k}']['regiones_negativas']}/12" for k in (on, "H", "A_G")), flush=True)
        rep["escenarios"][str(a)] = res
    (WORK / out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
