"""Compare a blend with A_G and H on identical 2024 rows and fixed mixtures.

A_G is a GAM meta-model and H a nested geometric meta-model from the N01 archive.
Their customer cross-validation occurs within 2024, so their local D2 is optimistic
relative to an out-of-time test. Reconstruct the candidate as in mezcla3, applying
the V23 factor to V24. Report both its original level and its line-specific 2024
Tweedie-optimal level to distinguish level from shape. Read references unchanged.
Usage: python compare_reference.py <output.json> <spec> <shape>
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import LINES, WORK, d2
from mezcla3 import ftw, labels
from robustez import blend, parse

C = "/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Modelado_reference/nocturna_20261017_N01"


def main():
    out_path, spec_arg = sys.argv[1], sys.argv[2]
    name, spec, forma = parse("CL=" + spec_arg)
    ag = pd.read_parquet(f"{C}/crossfit_meta_gam_guard/predictions_V24_crossfit.parquet", columns=["row_id", "T0", "meta_gam", "S09b"]).set_index("row_id")
    hh = pd.read_parquet(f"{C}/geometric_meta_nested/V24.parquet", columns=["row_id", "candidate", "anchor"]).set_index("row_id")
    rep = {}
    allv = {k: [] for k in ("y", "CL", "AG", "H", "S09b")}
    for line in LINES:
        ysel, y24, idx25 = labels(line)
        fe = pd.read_parquet(WORK / f"feat_{line}.parquet", columns=["row_id", "e_ef_coste", "exposure"])
        fe["row_id"] = fe.row_id.astype(str); fe = fe.set_index("row_id")
        expos = (fe.e_ef_coste.reindex(ysel.index).values, fe.e_ef_coste.reindex(y24.index).values, fe.exposure.reindex(idx25).values)
        _, _, b24, _ = blend(spec, forma, line, ysel, y24, idx25, expos)
        idx = y24.index
        assert ag.index.isin(idx).sum() >= len(idx) * 0.999
        y = y24.values
        assert np.allclose(ag.T0.reindex(idx).values, y, atol=0.01)
        P = {"CL": b24, "AG": ag.meta_gam.reindex(idx).values, "H": hh.candidate.reindex(idx).values, "S09b": ag.S09b.reindex(idx).values}
        assert all(np.isfinite(v).all() for v in P.values())
        r = {k: {"d2": round(d2(y, v), 5), "d2_renivelado": round(d2(y, v * ftw(y, v)), 5), "nivel_sobre_real": round(float(v.sum() / y.sum()), 4)} for k, v in P.items()}
        for other in ("AG", "H"):
            for w in (0.3, 0.5, 0.7):
                for kind in ("arit", "geom"):
                    m = w * P["CL"] + (1 - w) * P[other] if kind == "arit" else np.exp(w * np.log(P["CL"]) + (1 - w) * np.log(P[other]))
                    r[f"{kind}_{w}CL_{other}"] = {"d2": round(d2(y, m), 5), "d2_renivelado": round(d2(y, m * ftw(y, m)), 5)}
        rep[line] = r
        for k in allv:
            allv[k].append(y if k == "y" else P[k])
        print(line, {k: (v["d2"], v["d2_renivelado"]) for k, v in r.items()}, flush=True)
    y = np.concatenate(allv["y"]); P = {k: np.concatenate(v) for k, v in allv.items() if k != "y"}
    g = {k: round(d2(y, v), 5) for k, v in P.items()}
    for other in ("AG", "H"):
        for w in (0.3, 0.5, 0.7):
            g[f"arit_{w}CL_{other}"] = round(d2(y, w * P["CL"] + (1 - w) * P[other]), 5)
            g[f"geom_{w}CL_{other}"] = round(d2(y, np.exp(w * np.log(P["CL"]) + (1 - w) * np.log(P[other]))), 5)
    rep["global"] = g
    print("global", g, flush=True)
    (WORK / out_path).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
