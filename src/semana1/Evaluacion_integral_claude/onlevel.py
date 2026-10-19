"""Llevar el coste histórico al nivel del año objetivo por peligro ("on-level") y medir si mejora la predicción del año
siguiente con el LightGBM vigente de cada ramo.

Severidad por peligro y año de ocurrencia: media de los siniestros aceptados recortada al percentil 99 del peligro (para
que un solo siniestro extremo no mueva el índice). Índice del año objetivo: ajuste log-lineal sobre los años de
entrenamiento del pliegue, ponderado por número de siniestros; en lesiones corporales de autos se añade un escalón desde
2023, porque la severidad cae de golpe entre 2022T4 y 2023T1 (mediana 13.916 a 10.187) con la misma proporción de
abiertos (36 % y 35 %), lo que descarta un efecto de desarrollo; el escalón solo se estima si el entrenamiento incluye
algún año posterior a 2022. El objetivo de cada fila se recompone como suma de los costes por peligro multiplicados por
el factor índice(objetivo) / índice(año de la fila). Con --frecuencia también se lleva la frecuencia por peligro al año
objetivo con su tendencia log-lineal (exposición efectiva del peligro).
Pliegues: V23 (entrena 2021-2022, objetivo 2023, parada en calibración y comparación en selección) y V24 (2021-2023,
objetivo 2024, rondas V23 x 1,15, dos semillas). Siempre se compara con el T0 observado del año evaluado.
Uso: python3 onlevel.py <ramo> [--frecuencia]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/claude/modelos_claude")
from comun import PERILS, WORK, d2, deviance, to_model_frame  # noqa: E402
from experimentos import features, fit, load, predict  # noqa: E402

CLAIMS = "/mnt/user-data/uploads/Hakaton/Hackaton/Semana 1/Limpieza/runs/preaudit_20261016T211816Z_817285a5/data/claims.parquet"
OUT = Path(__file__).resolve().parent / "salidas"
F3S2 = ["prior_claims_5y", "credit_band", "missed_payments_12m", "household_size", "years_at_address", "marital_status", "licence_points"]


def severity_table():
    c = pd.read_parquet(CLAIMS)
    c = c[(c.status != "repudiated") & (~c.audit_pre00)].copy()
    c["net"] = c.incurred_to_date - c.recoveries
    c["ly"] = pd.to_datetime(c.loss_date).dt.year
    rows = []
    for (line, peril), g in c.groupby(["line", "peril"]):
        cap = g.net.quantile(0.99)
        for y, gy in g.groupby("ly"):
            rows.append({"line": line, "peril": peril, "year": int(y), "n": len(gy), "sev_rec": float(gy.net.clip(upper=cap).mean())})
    return pd.DataFrame(rows)


def index_factors(sev, line, peril, train_years, target):
    s = sev[(sev.line == line) & (sev.peril == peril) & (sev.year.isin(train_years))].sort_values("year")
    x = s.year.values.astype(float) - 2022.0
    yv = np.log(s.sev_rec.values)
    w = np.sqrt(s.n.values)
    step = (line == "motor" and peril == "bodily_injury" and (s.year > 2022).any())
    X = np.column_stack([np.ones_like(x), x] + ([(s.year.values > 2022).astype(float)] if step else []))
    beta = np.linalg.lstsq(X * w[:, None], yv * w, rcond=None)[0]

    def lev(year):
        v = beta[0] + beta[1] * (year - 2022.0)
        if step and year > 2022:
            v += beta[2]
        return v
    return {int(y): float(np.exp(lev(target) - lev(y))) for y in range(2021, target + 1)}, beta.tolist()


def freq_factors(df, line, peril, train_years, target):
    g = df[df.year.isin(train_years)].groupby("year").agg(n=(f"n_{peril}", "sum"), e=(f"e_ef_{peril}", "sum"))
    x = g.index.values.astype(float) - 2022.0
    b = np.polyfit(x, np.log(g.n.values / g.e.values), 1, w=np.sqrt(g.n.values))[0]
    return {int(y): float(np.exp(b * (target - y))) for y in range(2021, target + 1)}, float(b)


def main():
    line = sys.argv[1]
    use_freq = "--frecuencia" in sys.argv
    sev = severity_table()
    cfg = json.load(open(WORK / "cfg_hogar_s2.json"))[line]
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    feats += [c for c in cfg.get("add", []) if c in df.columns and c not in feats]
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    yr = df.year.values
    p = dict(cfg["params"])
    rep = {"line": line, "frecuencia": use_freq, "folds": {}}

    def target(train_years, tgt):
        tot = np.zeros(len(df))
        info = {}
        for per in PERILS[line]:
            fs, beta = index_factors(sev, line, per, train_years, tgt)
            ff, bf = freq_factors(df, line, per, train_years, tgt) if use_freq else ({k: 1.0 for k in fs}, 0.0)
            fac = pd.Series(yr).map({k: fs[k] * ff[k] for k in fs}).fillna(1.0).values
            tot += df[f"y_{per}"].fillna(0).values * fac
            info[per] = {"factores": {k: round(fs[k] * ff[k], 4) for k in fs}, "beta_sev": [round(b, 4) for b in beta], "tend_frec": round(bf, 4)}
        return tot, info

    tr = yr <= 2022; cal = (yr == 2023) & (df.cal_half.values == 0); sel = (yr == 2023) & (df.cal_half.values == 1)
    tr24 = yr <= 2023; ev = yr == 2024
    y23_ol, info23 = target([2021, 2022], 2023)
    y24_ol, info24 = target([2021, 2022, 2023], 2024)
    rep["folds"]["V23"] = info23; rep["folds"]["V24"] = info24
    pr23, pr24 = {}, {}
    for tag, yt23, yt24 in (("base", y, y), ("onlevel", y23_ol, y24_ol)):
        # entrenamiento con el objetivo llevado al nivel del año evaluado; calibración (parada) con el observado de 2023
        yfit = np.where(tr, yt23, y)
        b, s = fit(X[tr], yfit[tr], off[tr], X[cal], y[cal], off[cal], rounds=6000, early=200, params=dict(p))
        best = b.best_iteration
        pr23[tag] = predict(b, s, X[sel], off[sel], best)
        yfit24 = np.where(tr24, yt24, y)
        mu = np.zeros(ev.sum())
        for k in range(2):
            b2, s2 = fit(X[tr24], yfit24[tr24], off[tr24], rounds=int(round(best * 1.15)), early=None, params=dict(p, seed=20261017 + 101 * k))
            mu += predict(b2, s2, X[ev], off[ev]) / 2
        pr24[tag] = mu
        f23 = float((y[sel] / np.sqrt(pr23[tag])).sum() / np.sqrt(pr23[tag]).sum())
        f24 = float((y[ev] / np.sqrt(mu)).sum() / np.sqrt(mu).sum())
        out = {"best": best, "V23": round(d2(y[sel], pr23[tag]), 5), "V24": round(d2(y[ev], mu), 5),
               "V23_f_optimo": round(d2(y[sel], pr23[tag] * f23), 5), "V24_f_optimo": round(d2(y[ev], mu * f24), 5), "f23": round(f23, 4), "f24": round(f24, 4)}
        if tag != "base":
            for fold, yy, pr in (("V23", y[sel], pr23), ("V24", y[ev], pr24)):
                out[f"dif_{fold}"] = round(float((deviance(yy, pr["base"]).sum() - deviance(yy, pr[tag]).sum()) / deviance(yy, np.full(len(yy), yy.mean())).sum()), 5)
        rep[tag] = out
        print(line, tag, out, flush=True)
    for per, v in info24.items():
        print("   V24", per, v["factores"], "beta", v["beta_sev"], flush=True)
    name = f"onlevel_{line}{'_frec' if use_freq else ''}.json"
    (OUT / name).write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
