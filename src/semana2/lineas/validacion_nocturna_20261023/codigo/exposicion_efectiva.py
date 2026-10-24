"""Exposición efectiva por peligro y por coste para cada fila de entrenamiento.

e_ef_p = (1/365) * suma_{d en el periodo} F_p(corte - d), con F_p de reporte.py (conteos) o ponderada por coste.
e_ef_coste = suma_p s_p * e_ef_p / suma_p s_p, con s_p la participación del peligro en el coste último del ramo.
Para 2025 (test) la exposición a usar al predecir el último es la nominal.
"""
import json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche')
CUT = pd.Timestamp('2024-12-31')
PERILS = {'motor': ['own_damage', 'third_party_prop', 'bodily_injury', 'theft', 'glass_hail'],
          'buildings': ['storm', 'flood', 'escape_of_water', 'subsidence', 'fire', 'accidental_damage'],
          'contents': ['theft', 'escape_of_water', 'accidental_damage', 'flood']}


def daily_G(F, B, n):
    Fd = np.repeat(np.asarray(F), B)[:n]
    if len(Fd) < n:
        Fd = np.concatenate([Fd, np.ones(n - len(Fd))])
    return np.concatenate([[0.0], np.cumsum(Fd)])  # G[k] = sum_{t<k} F(t)


def add_effective(df, line, Ftab, B, shares):
    ps = pd.to_datetime(df.period_start); pe = pd.to_datetime(df.period_end)
    w_hi = (CUT - ps).dt.days.values  # mayor ventana (primer día)
    w_lo = (CUT - pe).dt.days.values  # menor ventana (último día)
    train = (w_lo >= 0)
    tot = np.zeros(len(df)); wsum = 0.0
    for p in PERILS[line]:
        G = daily_G(Ftab[p], B, 4000)
        e = np.where(train, (G[np.clip(w_hi, 0, 3999) + 1] - G[np.clip(w_lo, 0, 3999)]) / 365.0, np.nan)
        df[f'eef_{p}'] = e
        tot += shares[p] * np.nan_to_num(e); wsum += shares[p]
    df['eef_coste'] = np.where(train, tot / wsum, np.nan)
    df['comp_coste'] = df.eef_coste / df.exposure_model
    return df
