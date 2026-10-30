"""Diagnose candidate ordering in the body of the 2024 loss distribution.

For archived A_G, H, S09b, S21 and S22 predictions, report D2 on all rows and
after excluding observed losses above p99.9, p99.5 and p99. Relevel the optional
comparison within each subset to distinguish shape from level. Filtering by the
observed label is a diagnostic, not a valid prospective scoring or selection rule.
Read all archived predictions unchanged.
Usage: python diagnostico_cuerpo_cola.py <output.json>
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import WORK, d2

C = "/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Modelado_reference/nocturna_20261017_N01"
PUBLICO = {"A_G": 0.12908, "S09b": 0.12889, "H": 0.12886, "S21": 0.12874}  # Historical comparison and submission ledger reference: COD-20261018-049.


def ftw(y, mu):
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def main():
    ag = pd.read_parquet(f"{C}/crossfit_meta_gam_guard/predictions_V24_crossfit.parquet", columns=["row_id", "line", "T0", "S09b", "meta_gam"]).set_index("row_id")
    hh = pd.read_parquet(f"{C}/geometric_meta_nested/V24.parquet", columns=["row_id", "candidate"]).set_index("row_id")
    df = ag.join(hh).rename(columns={"meta_gam": "A_G", "candidate": "H"})
    for k in ("s21", "s22"):
        p = pd.read_parquet(WORK / f"predicciones_v23_v24_{k}.parquet")
        df = df.join(p[p.corte == "V24"].set_index("row_id")[["prediction"]].rename(columns={"prediction": k.upper()}))
    cands = ["A_G", "S09b", "H", "S21", "S22"]
    assert df[cands].notna().all().all()
    y = df.T0.values
    rep = {"publico": PUBLICO, "orden_publico": sorted(PUBLICO, key=PUBLICO.get, reverse=True), "bruto": {}, "renivelado": {},
           "media_predicha_V24": {k: round(float(df[k].mean()), 2) for k in cands}, "media_T0_V24": round(float(y.mean()), 2)}
    for q in (None, 0.999, 0.995, 0.99):
        m = np.ones(len(y), bool) if q is None else (y <= np.quantile(y, q))
        lab = "completo" if q is None else f"sin_p{q * 100:g}"
        bruto, ren = {}, {}
        for k in cands:
            mu = df[k].values[m]; yy = y[m]; ln = df.line.values[m]
            bruto[k] = round(d2(yy, mu), 5)
            mu2 = mu.copy()
            for line in ("motor", "buildings", "contents"):
                l = ln == line
                mu2[l] = mu[l] * ftw(yy[l], mu[l])
            ren[k] = round(d2(yy, mu2), 5)
        rep["bruto"][lab] = {"d2": bruto, "orden": sorted(bruto, key=bruto.get, reverse=True)}
        rep["renivelado"][lab] = {"d2": ren, "orden": sorted(ren, key=ren.get, reverse=True)}
        print(lab, "bruto", rep["bruto"][lab]["orden"], "renivelado", rep["renivelado"][lab]["orden"], ren, flush=True)
    (WORK / sys.argv[1]).write_text(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
