"""Diferencias de D² en 2024 por semestre de inicio del periodo (H1: enero-junio; H2: julio-diciembre), nominal y con +25 %.

Compara una mezcla de Claude con H, A_G y otra mezcla de Claude, por ramo y en el agregado, con IC95 por cliente y por
dirección (Poisson(1), 1.000 réplicas, denominador fijo dentro de cada semestre; la dirección usa su propio generador para
que los intervalos por cliente no cambien respecto de la versión anterior). Informa también el peso de cada semestre en la
exposición y su madurez (exposición efectiva entre nominal), porque el segundo semestre tiene las etiquetas menos maduras.
Uso: python3 semestres.py <salida.json> <cand>=<spec>@<forma>@<nivel> <otra>=<spec>@<forma>@<nivel>
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK, d2, deviance
from escenarios_reserva import C, reserva_por_fila
from mezcla3 import labels
from robustez import blend, parse

B = 1000


def ic(dif, groups, null, rng):
    codes, inv = np.unique(groups, return_inverse=True)
    d = np.bincount(inv, weights=dif)
    bs = np.concatenate([rng.poisson(1.0, size=(50, len(d))) @ d for _ in range(B // 50)]) / null
    return [round(float(np.quantile(bs, 0.025)), 6), round(float(np.quantile(bs, 0.975)), 6)]


def main():
    out = sys.argv[1]
    (cn, cspec, cfm), (on, ospec, ofm) = parse(sys.argv[2]), parse(sys.argv[3])
    R = reserva_por_fila()
    ag = pd.read_parquet(f"{C}/crossfit_meta_gam_guard/predictions_V24_crossfit.parquet", columns=["row_id", "meta_gam"]).set_index("row_id").meta_gam
    hh = pd.read_parquet(f"{C}/geometric_meta_nested/V24.parquet", columns=["row_id", "candidate"]).set_index("row_id").candidate
    rng = np.random.default_rng(20261018)
    rng_ad = np.random.default_rng(20261019)
    V = {k: [] for k in ("y", "r", "cu", "ad", "ln", "sem", "e", "eef", cn, on, "H", "A_G")}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "customer_id", "address_id", "e_ef_coste", "exposure", "period_start"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        V[cn].append(blend(cspec, cfm, line, ysel, y24, idx25, expos)[2]); V[on].append(blend(ospec, ofm, line, ysel, y24, idx25, expos)[2])
        V["H"].append(hh.reindex(y24.index).values); V["A_G"].append(ag.reindex(y24.index).values)
        f = fe.reindex(y24.index)
        V["y"].append(y24.values); V["r"].append(R.reindex(y24.index).fillna(0.0).values); V["cu"].append(f.customer_id.astype(str).values)
        V["ad"].append(f.address_id.astype(str).values)
        V["ln"].append(np.full(len(y24), line)); V["sem"].append(np.where(pd.to_datetime(f.period_start).dt.month.values <= 6, "H1", "H2"))
        V["e"].append(f.exposure.values); V["eef"].append(f.e_ef_coste.values)
    V = {k: np.concatenate(v) for k, v in V.items()}
    rep = {"candidato": cn, "comparadores": [on, "H", "A_G"], "resultados": {}}
    for a in (1.0, 1.25):
        y_all = V["y"] + (a - 1.0) * V["r"]
        res = {}
        for scope in LINES + ["agregado"]:
            for sem in ("H1", "H2"):
                msk = (V["sem"] == sem) & (np.ones(len(y_all), bool) if scope == "agregado" else (V["ln"] == scope))
                y = y_all[msk]; null = deviance(y, np.full_like(y, y.mean())).sum()
                row = {"filas": int(msk.sum()), "peso_exposicion": round(float(V["e"][msk].sum() / V["e"][(np.ones(len(y_all), bool) if scope == "agregado" else (V["ln"] == scope))].sum()), 4),
                       "madurez": round(float(V["eef"][msk].sum() / V["e"][msk].sum()), 3), "d2": {k: round(d2(y, V[k][msk]), 6) for k in (cn, on, "H", "A_G")}}
                for k in (on, "H", "A_G"):
                    dif = deviance(y, V[k][msk]) - deviance(y, V[cn][msk])
                    row[f"{cn}_menos_{k}"] = {"dif": round(float(dif.sum() / null), 6), "ic95_cliente": ic(dif, V["cu"][msk], null, rng),
                                              "ic95_direccion": ic(dif, V["ad"][msk], null, rng_ad)}
                res[f"{scope}_{sem}"] = row
                print(f"a={a} {scope} {sem} filas {row['filas']} peso {row['peso_exposicion']} madurez {row['madurez']} " +
                      " ".join(f"{k}: {row[f'{cn}_menos_{k}']['dif']:+.6f} {row[f'{cn}_menos_{k}']['ic95_cliente']} dir {row[f'{cn}_menos_{k}']['ic95_direccion']}" for k in (on, "H", "A_G")), flush=True)
        rep["resultados"][str(a)] = res
    (WORK / out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
