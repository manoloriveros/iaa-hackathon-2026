"""Variables de experiencia (credibilidad): notificaciones previas observadas frente a esperadas según el riesgo.

Etapa 1: Poisson LightGBM fuera de pliegue (5 pliegues por póliza) sobre las notificaciones de cada fila de
entrenamiento, con las variables sin historia (F0, F2, F4 y, en autos, F3) y offset de exposición efectiva por conteo.
Da el número esperado de notificaciones a último de cada periodo pasado. Para cada fila del año Y, sumando los periodos
de la misma póliza con año < Y: esperado reportado al 1 de enero de Y (esperado a último x completitud del conteo a esa
fecha, con los factores del chain-ladder D67) y observado (f1_notificaciones_previas, el mismo corte).
Salida: WORK/cred_<ramo>.parquet con row_id, cred_esperado_prev, cred_ratio_k05, cred_ratio_k2.
Uso: python3 credibilidad.py [ramos]
"""
from __future__ import annotations

import hashlib
import json
import sys
import time

import numpy as np
import pandas as pd

from comun import BASESDIR, LINES, PERILS, WORK, blocks_for, to_model_frame
from experimentos import ALWAYS_OUT, fit, load, predict

MONTHS = pd.period_range("2021-01", "2025-12", freq="M")


def count_cdf(line, a_line):
    f = pd.read_csv(BASESDIR / "tables" / "factores_desarrollo_conteos.csv")
    f = f[f.line == line]
    shares = a_line.groupby("peril").size()
    shares = shares / shares.sum()
    comp = np.zeros(120)
    for p, s in shares.items():
        g = f[f.peril == p].set_index("lag_meses")["factor_a_ultimo"]
        cdf = np.ones(120)
        for lag, v in g.items():
            cdf[int(lag)] = float(v)
        comp += s / cdf
    return comp  # completitud media del conteo por edad en meses (>= 48 meses: 1 salvo cola)


def main():
    lines = sys.argv[1].split(",") if len(sys.argv) > 1 else LINES
    a = pd.read_parquet(BASESDIR / "tables" / "asignacion_por_siniestro.parquet")
    for line in lines:
        t = time.time()
        df = load(line)
        al = a[(a.line == line)]
        notif = al[al.category == "unica"].groupby("row_id").size()
        df["n_notif"] = df.row_id.astype(str).map(notif).fillna(0).values
        comp_age = count_cdf(line, al)
        # offset de conteo: completitud media del periodo al 30-12-2024 aplicada a la exposición
        shares = al.groupby("peril").size(); shares = shares / shares.sum()
        e_cnt = sum(df[f"e_ef_{p}"].values * shares.get(p, 0.0) for p in PERILS[line])
        bl = blocks_for(line, df)
        keep = {"F0", "F2", "F4"} | ({"F3"} if line == "motor" else set())
        feats = [c for c, b in bl.items() if b in keep and c not in ALWAYS_OUT]
        X = to_model_frame(df, feats)
        trn = (~df.is_test).values
        fold = df.policy_id.astype(str).map(lambda s: int(hashlib.sha256(f"cred|{s}".encode()).hexdigest()[:8], 16) % 5).values
        lam_ult = np.full(len(df), np.nan)
        params = {"objective": "poisson", "learning_rate": 0.05, "num_leaves": 15, "min_data_in_leaf": 2000, "cat_smooth": 200, "cat_l2": 50,
                  "min_data_per_group": 1000, "max_cat_threshold": 16, "feature_fraction": 0.8}
        y = df["n_notif"].values
        for k in range(5):
            tr = trn & (fold != k); te = trn & (fold == k)
            b, base = fit(X[tr], y[tr], e_cnt[tr], rounds=400, early=None, params=dict(params))
            lam_ult[te] = predict(b, base, X[te], df["exposure"].values[te])  # esperado a último del periodo
        # completitud de cada periodo pasado a cada corte del 1 de enero
        ps = df.period_start.values.astype("datetime64[M]"); pe = df.period_end.values.astype("datetime64[M]")
        start_idx = (ps - np.datetime64("2021-01", "M")).astype(int); end_idx = (pe - np.datetime64("2021-01", "M")).astype(int)
        hist = df.loc[trn, ["policy_id", "year"]].copy()
        hist["lam"] = lam_ult[trn]
        si = start_idx[trn]; ei = end_idx[trn]
        rows = []
        for Y in range(2022, 2026):
            cut = (Y - 2021) * 12  # índice del mes de enero de Y
            m = hist.year.values < Y
            # completitud media del periodo al corte: media simple por meses cubiertos de 1/cdf(edad)
            ages_lo = cut - 1 - ei[m]; ages_hi = cut - 1 - si[m]
            c = np.array([comp_age[np.clip(np.arange(lo, hi + 1), 0, 119)].mean() for lo, hi in zip(ages_lo, ages_hi)])
            e = pd.DataFrame({"policy_id": hist.policy_id.values[m], "e": hist.lam.values[m] * c}).groupby("policy_id")["e"].sum()
            r = e.rename("cred_esperado_prev").reset_index(); r["year"] = Y
            rows.append(r)
        ep = pd.concat(rows, ignore_index=True)
        df = df.merge(ep, on=["policy_id", "year"], how="left")
        df["cred_esperado_prev"] = df["cred_esperado_prev"].fillna(0.0)
        o = df["f1_notificaciones_previas"].values.astype(float); e = df["cred_esperado_prev"].values
        for k in (0.5, 2.0):
            df[f"cred_ratio_k{str(k).replace('.', '')}"] = (o + k * 1.0) / (e + k * 1.0)
        out = df[["row_id", "cred_esperado_prev", "cred_ratio_k05", "cred_ratio_k20"]].copy()
        out["row_id"] = out.row_id.astype(str)
        out.to_parquet(WORK / f"cred_{line}.parquet", index=False)
        print(line, "listo", round(time.time() - t), "s; media esperado previo 2025:", round(float(df.loc[df.year == 2025, "cred_esperado_prev"].mean()), 4),
              "observado:", round(float(df.loc[df.year == 2025, "f1_notificaciones_previas"].mean()), 4), flush=True)


if __name__ == "__main__":
    main()
