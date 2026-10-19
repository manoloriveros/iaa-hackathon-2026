"""Entrena el candidato final por ramo y escribe el archivo de envío.

Para cada ramo: V24 de confirmación (entrena 2021-2023 con las rondas de V23 x 1,15 y evalúa 2024 sobre T0 con el
offset de exposición efectiva) y producción (entrena 2021-2024 con las rondas de V23 x 1,3 y predice 2025 con la
exposición nominal, que en 2025 coincide con la efectiva: nivel último sin segundo factor, D70). Promedia varias
semillas. Escribe WORK/<nombre>/: prediccion_2025.parquet, v24.parquet, resumen.json y el CSV de envío con row_id y
prediction en el orden de sample_submission.

Uso: python3 produccion.py <nombre> <conjunto> <config_json> [--semillas=3] [--tendencia=motor:1.0,buildings:1.0,contents:1.0]
config_json: {"motor": {"params": {...}, "rounds": N}, "buildings": {...}, "contents": {...}}
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from comun import BASE, LINES, WORK, d2, digest, to_model_frame
from experimentos import features, fit, load, predict


def main():
    name, set_name, cfg_path = sys.argv[1], sys.argv[2], sys.argv[3]
    cfg = json.loads(open(cfg_path).read())
    seeds = 3
    trend = {l: 1.0 for l in LINES}
    only = list(LINES)
    reuse = None
    for a in sys.argv[4:]:
        if a.startswith("--solo="):
            only = a.split("=", 1)[1].split(",")
        if a.startswith("--reusar="):
            reuse = WORK / a.split("=", 1)[1]
        if a.startswith("--semillas="):
            seeds = int(a.split("=")[1])
        if a.startswith("--tendencia="):
            for kv in a.split("=", 1)[1].split(","):
                k, v = kv.split(":")
                trend[k] = float(v)
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    preds, v24_rows, summary = [], [], {"set": set_name, "config": cfg, "seeds": seeds, "trend": trend, "lines": {}}
    for line in LINES:
        if line not in only:
            rp = pd.read_parquet(reuse / "prediccion_2025.parquet")
            rv = pd.read_parquet(reuse / "v24.parquet")
            preds.append(rp[rp.line == line].copy())
            v24_rows.append(rv[rv.line == line].copy())
            summary["lines"][line] = json.loads((reuse / "resumen.json").read_text())["lines"][line] | {"reutilizado_de": reuse.name}
            continue
        t = time.time()
        df = load(line)
        feats = [f for f in features(line, df, set_name) if f not in set(cfg[line].get("drop", []))]
        feats += [f for f in cfg[line].get("add", []) if f in df.columns and f not in feats]
        X = to_model_frame(df, feats)
        y = df["T0"].fillna(0).values
        off = df["e_ef_coste"].values
        expo = df["exposure"].values
        tr24 = (df.year <= 2023).values
        ev24 = (df.year == 2024).values
        trp = (df.year <= 2024).values
        te = (df.year == 2025).values
        r = int(cfg[line]["rounds"])
        mu24 = np.zeros(ev24.sum())
        mu25 = np.zeros(te.sum())
        for s in range(seeds):
            params = dict(cfg[line]["params"], seed=20261017 + 101 * s)
            b24, base24 = fit(X[tr24], y[tr24], off[tr24], rounds=int(round(r * 1.15)), early=None, params=dict(params))
            mu24 += predict(b24, base24, X[ev24], off[ev24]) / seeds
            bp, basep = fit(X[trp], y[trp], off[trp], rounds=int(round(r * 1.3)), early=None, params=dict(params))
            mu25 += predict(bp, basep, X[te], expo[te]) / seeds
        mu25 *= trend[line]
        imp = pd.Series(bp.feature_importance("gain"), index=feats).sort_values(ascending=False)
        summary["lines"][line] = {
            "n_feats": len(feats), "rounds_v24": int(round(r * 1.15)), "rounds_prod": int(round(r * 1.3)),
            "d2_v24": round(d2(y[ev24], mu24), 5), "balance_v24": round(float(mu24.sum() / y[ev24].sum()), 4),
            "pred_2025_total_CU": round(float(mu25.sum()), 2), "pred_2025_rate_CU": round(float(mu25.sum() / expo[te].sum()), 4),
            "train_T0_rate_dev_CU": round(float(y[trp].sum() / off[trp].sum()), 4), "loading": round(float(getattr(bp, "loading", 1.0)), 5),
            "top_gain": {k: round(float(v / imp.sum()), 4) for k, v in imp.head(20).items()}, "secs": round(time.time() - t)}
        print(line, summary["lines"][line], flush=True)
        preds.append(pd.DataFrame({"row_id": df.row_id[te].astype(str).values, "line": line, "prediction": mu25}))
        v24_rows.append(pd.DataFrame({"row_id": df.row_id[ev24].astype(str).values, "line": line, "y": y[ev24], "mu": mu24}))
    pred = pd.concat(preds, ignore_index=True)
    v24 = pd.concat(v24_rows, ignore_index=True)
    summary["d2_v24_global"] = round(d2(v24.y, v24.mu), 5)
    sample = pd.read_parquet(BASE / "Datos" / "sample_submission.parquet", columns=["row_id"])
    sub = sample.merge(pred[["row_id", "prediction"]], on="row_id", how="left", validate="one_to_one")
    assert len(sub) == 626639 and sub.prediction.notna().all() and np.isfinite(sub.prediction).all() and (sub.prediction > 0).all()
    csv = out / f"{name}.csv"
    sub.to_csv(csv, index=False, float_format="%.6f")
    back = pd.read_csv(csv, dtype={"row_id": str})
    assert len(back) == 626639 and (back.row_id.values == sample.row_id.values).all() and (back.prediction > 0).all()
    summary["file"] = {"path": str(csv), "sha256": digest(csv), "rows": int(len(back)), "total_CU": round(float(back.prediction.sum()), 2),
                       "by_line_CU": {l: round(float(pred[pred.line == l].prediction.sum()), 2) for l in LINES}}
    pred.to_parquet(out / "prediccion_2025.parquet", index=False)
    v24.to_parquet(out / "v24.parquet", index=False)
    (out / "resumen.json").write_text(json.dumps(summary, indent=1, default=float))
    print("V24 global", summary["d2_v24_global"], "archivo", summary["file"], flush=True)


if __name__ == "__main__":
    main()
