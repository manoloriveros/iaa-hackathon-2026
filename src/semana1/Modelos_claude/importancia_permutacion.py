"""Importancia por permutación en la mitad de calibración de V23 y prueba de eliminar las variables sin aporte.

1. Ajusta el modelo vigente del ramo con 2021-2022 (parada temprana en calibración).
2. Para cada variable, permuta su columna en la mitad de calibración y mide la caída de D² (media de 2 permutaciones).
3. Elimina las variables con caída <= umbral y vuelve a ajustar; compara en la mitad de selección (no usada en 1-2).
Uso: python3 importancia_permutacion.py <ramo> [umbral] [--drop=var1,var2]
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comun import WORK, d2, to_model_frame
from experimentos import features, fit, load, predict


def main():
    line = sys.argv[1]
    thr = float(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else 0.0
    pre = next((a.split("=", 1)[1].split(",") for a in sys.argv[2:] if a.startswith("--drop=")), [])
    cfg = json.load(open("/home/claude/work/cfg_total.json"))[line]["params"]
    df = load(line)
    feats = [f for f in features(line, df, "F01234" if line == "motor" else "F0124") if f not in pre]
    X = to_model_frame(df, feats)
    tr = df.year.isin([2021, 2022]).values
    cal = ((df.year == 2023) & (df.cal_half == 0)).values
    sel = ((df.year == 2023) & (df.cal_half == 1)).values
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    b, base = fit(X[tr], y[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(cfg))
    it = b.best_iteration
    Xc = X[cal].copy()
    yc = y[cal]
    oc = off[cal]
    if line == "motor":  # la fila de 11,9 millones domina la calibración; se mide sobre la etiqueta acotada con recargo
        yc = np.minimum(yc, 15000.0) * (y[tr].sum() / np.minimum(y[tr], 15000.0).sum())
    ref = d2(yc, predict(b, base, Xc, oc, it))
    rng = np.random.default_rng(7)
    imp = {}
    for f in feats:
        drops = []
        for _ in range(2):
            Xp = Xc.copy()
            Xp[f] = Xp[f].values[rng.permutation(len(Xp))]
            drops.append(ref - d2(yc, predict(b, base, Xp, oc, it)))
        imp[f] = float(np.mean(drops))
    s = pd.Series(imp).sort_values()
    weak = list(s[s <= thr].index)
    mu_full = predict(b, base, X[sel], off[sel], it)
    keep = [f for f in feats if f not in weak]
    X2 = to_model_frame(df, keep)
    b2, base2 = fit(X2[tr], y[tr], off[tr], X2[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(cfg))
    mu_red = predict(b2, base2, X2[sel], off[sel], b2.best_iteration)
    res = {"line": line, "pre_drop": pre, "threshold": thr, "n_feats": len(feats), "n_weak": len(weak), "weak": weak,
           "d2_sel_completo": round(d2(y[sel], mu_full), 5), "d2_sel_reducido": round(d2(y[sel], mu_red), 5),
           "importancia": {k: round(v, 6) for k, v in s.items()}}
    print(json.dumps({k: v for k, v in res.items() if k != "importancia"}, ensure_ascii=False), flush=True)
    print("menores:", {k: round(v, 6) for k, v in s.head(25).items()}, flush=True)
    (WORK / f"permutacion_{line}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
