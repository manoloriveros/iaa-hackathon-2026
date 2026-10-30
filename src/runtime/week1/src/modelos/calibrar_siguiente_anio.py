"""Calibrate each line to the year after training with Tweedie power 1.5.

V23 uses training years 2021-2022 and the 2023 selection partition; V24 uses
training years 2021-2023 and the 2024 observations. For each cut calculate
f = sum(y/sqrt(mu)) / sum(sqrt(mu)); apply the mean of both factors to 2025.
The predictions already include effective-exposure development, so the factor
does not apply IBNR a second time. The historical transfer check applies the
V23 factor to V24; these cuts informed model decisions.

Usage: python calibrar_siguiente_anio.py <base_run> <output> <line>:<V23_selection>[,...]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import BASE, LINES, WORK, d2, digest


def ftw(y, mu):
    return float((y / np.sqrt(mu)).sum() / np.sqrt(mu).sum())


def main():
    base_run, out_name = sys.argv[1], sys.argv[2]
    sel_map = dict(kv.split(":") for kv in sys.argv[3].split(","))
    base = WORK / base_run
    pred = pd.read_parquet(base / "prediccion_2025.parquet")
    v24 = pd.read_parquet(base / "v24.parquet")
    out = WORK / out_name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"base_run": base_run, "lines": {}}
    v24c = v24.copy()
    for line in LINES:
        s = pd.read_parquet(WORK / f"sel_{sel_map[line]}.parquet")
        s = s[s.line == line]
        b = v24[v24.line == line]
        f23, f24 = ftw(s.y.values, s.mu.values), ftw(b.y.values, b.mu.values)
        f = (f23 + f24) / 2
        rep["lines"][line] = {"f_v23": round(f23, 4), "f_v24": round(f24, 4), "f_aplicado": round(f, 4),
                              "d2_v24_sin": round(d2(b.y, b.mu), 5), "d2_v24_con_f_v23": round(d2(b.y, b.mu * f23), 5), "sel_v23": sel_map[line]}
        v24c.loc[v24c.line == line, "mu"] = b.mu.values * f23
        pred.loc[pred.line == line, "prediction"] = pred.loc[pred.line == line, "prediction"].values * f
    rep["d2_v24_global_sin"] = round(d2(v24.y, v24.mu), 5)
    rep["d2_v24_global_con_f_v23"] = round(d2(v24c.y, v24c.mu), 5)
    sample = pd.read_parquet(BASE / "Datos" / "sample_submission.parquet", columns=["row_id"])
    sub = sample.merge(pred[["row_id", "prediction"]], on="row_id", how="left", validate="one_to_one")
    assert len(sub) == 626639 and np.isfinite(sub.prediction).all() and (sub.prediction > 0).all()
    csv = out / f"{out_name}.csv"
    sub.to_csv(csv, index=False, float_format="%.6f")
    back = pd.read_csv(csv, dtype={"row_id": str})
    assert (back.row_id.values == sample.row_id.values).all() and len(back) == 626639
    rep["file"] = {"path": str(csv), "sha256": digest(csv), "rows": 626639, "total_CU": round(float(back.prediction.sum()), 2),
                   "by_line_CU": {l: round(float(pred[pred.line == l].prediction.sum()), 2) for l in LINES}}
    pred.to_parquet(out / "prediccion_2025.parquet", index=False)
    (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
