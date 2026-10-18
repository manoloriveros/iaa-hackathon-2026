"""Tweedie total en V23 con variables adicionales leídas de WORK/<prefijo>_<ramo>.parquet (por row_id).

Mismo contrato que evaluar.py (config cfg_total.json: tope de autos, F3 solo en autos). Guarda sel_<nombre>.parquet.
Uso: python3 evaluar_extra.py <nombre> <prefijo> [ramos]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from comun import LINES, WORK, d2, to_model_frame
from experimentos import features, fit, load, predict


def main():
    name, prefix = sys.argv[1], sys.argv[2]
    lines = sys.argv[3].split(",") if len(sys.argv) > 3 else LINES
    cfg = json.load(open("/home/claude/work/cfg_total.json"))
    rep, frames = {}, []
    for line in lines:
        t = time.time()
        df = load(line)
        extra = pd.read_parquet(WORK / f"{prefix}_{line}.parquet")
        cols = [c for c in extra.columns if c != "row_id"]
        df["row_id_s"] = df.row_id.astype(str)
        df = df.merge(extra.rename(columns={"row_id": "row_id_s"}), on="row_id_s", how="left")
        feats = features(line, df, "F01234" if line == "motor" else "F0124") + cols
        X = to_model_frame(df, feats)
        tr = df.year.isin([2021, 2022]).values
        cal = ((df.year == 2023) & (df.cal_half == 0)).values
        sel = ((df.year == 2023) & (df.cal_half == 1)).values
        y = df["T0"].fillna(0).values
        off = df["e_ef_coste"].values
        b, base = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(cfg[line]["params"]))
        mu = predict(b, base, X[sel], off[sel], b.best_iteration)
        imp = pd.Series(b.feature_importance("gain"), index=feats)
        rep[line] = {"d2_sel": round(d2(y[sel], mu), 5), "best": b.best_iteration, "gain_extra": {c: round(float(imp[c] / imp.sum()), 4) for c in cols}, "secs": round(time.time() - t)}
        print(name, line, rep[line], flush=True)
        frames.append(pd.DataFrame({"row_id": df.row_id_s[sel].values, "line": line, "y": y[sel], "mu": mu}))
    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(WORK / f"sel_{name}.parquet", index=False)
    if len(lines) == 3:
        rep["global"] = round(d2(out.y, out.mu), 5)
        print("== ", name, "global", rep["global"], flush=True)
    (WORK / f"eval_{name}.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
