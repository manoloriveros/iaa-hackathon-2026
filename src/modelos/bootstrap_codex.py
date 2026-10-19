"""Intervalos pareados de una mezcla de Claude frente a A_G y H de Codex en 2024, por cliente y por dirección.

Reproduce el criterio que usa Codex para decidir envíos: diferencia de D² por ramo y agregada, con IC del 95 % por
remuestreo de grupos (Poisson(1) por cliente o por dirección, 1.000 réplicas) y denominador fijo. Lee las predicciones de
Codex sin modificarlas. Su D² local es optimista (meta ajustada con validación cruzada por cliente dentro de 2024).
Uso: python3 bootstrap_codex.py <salida.json> <spec>@<forma>
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK, deviance
from mezcla3 import labels
from robustez import blend, parse

C = "/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Modelado_codex/nocturna_20261017_N01"
B = 1000


def ci(dif, groups, null, rng):
    codes, inv = np.unique(groups, return_inverse=True)
    d = np.bincount(inv, weights=dif)
    bs = np.concatenate([rng.poisson(1.0, size=(50, len(d))) @ d for _ in range(B // 50)]) / null
    return [round(float(np.quantile(bs, 0.025)), 6), round(float(np.quantile(bs, 0.975)), 6)], round(float((bs > 0).mean()), 3)


def main():
    out, arg = sys.argv[1], sys.argv[2]
    _, spec, forma = parse("CL=" + arg)
    ag = pd.read_parquet(f"{C}/crossfit_meta_gam_guard/predictions_V24_crossfit.parquet", columns=["row_id", "meta_gam"]).set_index("row_id").meta_gam
    hh = pd.read_parquet(f"{C}/geometric_meta_nested/V24.parquet", columns=["row_id", "candidate"]).set_index("row_id").candidate
    rng = np.random.default_rng(20261018)
    rep, allv = {}, {"y": [], "CL": [], "AG": [], "H": [], "cu": [], "ad": []}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "customer_id", "address_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        _, _, b24, _ = blend(spec, forma, line, ysel, y24, idx25, expos)
        y = y24.values
        P = {"CL": b24, "AG": ag.reindex(y24.index).values, "H": hh.reindex(y24.index).values}
        cu = fe.customer_id.reindex(y24.index).astype(str).values; ad = fe.address_id.reindex(y24.index).astype(str).values
        null = deviance(y, np.full_like(y, y.mean())).sum()
        r = {}
        for ref in ("AG", "H"):
            dif = deviance(y, P[ref]) - deviance(y, P["CL"])
            r[f"CL_menos_{ref}"] = {"dif": round(float(dif.sum() / null), 6), "ic95_cliente": ci(dif, cu, null, rng)[0], "ic95_direccion": ci(dif, ad, null, rng)[0]}
        rep[line] = r
        for k, v in (("y", y), ("cu", cu), ("ad", ad)):
            allv[k].append(v)
        for k in ("CL", "AG", "H"):
            allv[k].append(P[k])
        print(line, r, flush=True)
    y = np.concatenate(allv["y"]); cu = np.concatenate(allv["cu"]); ad = np.concatenate(allv["ad"])
    null = deviance(y, np.full_like(y, y.mean())).sum()
    g = {}
    for ref in ("AG", "H"):
        dif = deviance(y, np.concatenate(allv[ref])) - deviance(y, np.concatenate(allv["CL"]))
        g[f"CL_menos_{ref}"] = {"dif": round(float(dif.sum() / null), 6), "ic95_cliente": ci(dif, cu, null, rng)[0], "ic95_direccion": ci(dif, ad, null, rng)[0]}
    rep["agregado"] = g
    print("agregado", g, flush=True)
    (WORK / out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
