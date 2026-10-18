"""Exposición efectiva por segmento: ponderar la completitud de cada peligro con la mezcla de coste del segmento.

e_ef_seg = sum_p share_p(segmento) x e_ef_p, con share_p estimado en años maduros (2021-2022) por segmento:
autos por cover_type (la cobertura decide qué peligros existen), edificios por soil_type (hundimiento), contenidos por
flood_zone. Compara con e_ef_coste (mezcla del ramo) en V23 (selección) y V24, con la configuración vigente.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from comun import PERILS, d2, to_model_frame
from experimentos import features, fit, load, predict

cfg = json.load(open("/home/claude/work/cfg_total.json"))
SEG = {"motor": "cover_type", "buildings": "soil_type", "contents": "flood_zone"}
RONDAS = {"motor": 595, "buildings": 350, "contents": 303}
for line in ["motor", "buildings", "contents"]:
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    seg = df[SEG[line]].astype(str).fillna("nan")
    mature = df.year.isin([2021, 2022]).values
    shares = {}
    tot = pd.Series(0.0, index=seg[mature].unique())
    for p in PERILS[line]:
        s = pd.Series(df[f"y_{p}"].fillna(0).values[mature]).groupby(seg[mature].values).sum()
        shares[p] = s
        tot = tot.add(s, fill_value=0)
    e_seg = np.zeros(len(df))
    line_share = {p: shares[p].sum() / tot.sum() for p in PERILS[line]}
    for p in PERILS[line]:
        sh = (shares[p] / tot).reindex(seg.unique()).fillna(line_share[p])
        e_seg += df[f"e_ef_{p}"].values * seg.map(sh).fillna(line_share[p]).values
    off_line = df["e_ef_coste"].values
    p_ = dict(cfg[line]["params"])
    tr23 = df.year.isin([2021, 2022]).values; cal = ((df.year == 2023) & (df.cal_half == 0)).values; sel = ((df.year == 2023) & (df.cal_half == 1)).values
    tr24 = (df.year <= 2023).values; ev24 = (df.year == 2024).values
    for tag, off in (("e_ef_ramo", off_line), ("e_ef_segmento", e_seg)):
        b, s = fit(X[tr23], y[tr23], off[tr23], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(p_))
        d23 = d2(y[sel], predict(b, s, X[sel], off[sel], b.best_iteration))
        b2, s2 = fit(X[tr24], y[tr24], off[tr24], rounds=int(RONDAS[line] * 1.15), early=None, params=dict(p_))
        d24 = d2(y[ev24], predict(b2, s2, X[ev24], off[ev24]))
        print(line, tag, "V23", round(d23, 5), "V24", round(d24, 5), "ratio_2024", round(float(off[ev24].sum() / df.exposure.values[ev24].sum()), 4), flush=True)
