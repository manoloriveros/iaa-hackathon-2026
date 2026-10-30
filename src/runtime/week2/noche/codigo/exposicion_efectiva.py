"""Derive peril- and cost-weighted effective exposure for each training row.
e_ef_p=sum_d F_p(cutoff-d)/365, using count- or cost-weighted reporting curves.
e_ef_coste=sum_p(s_p*e_ef_p)/sum_p(s_p), where s_p are ultimate-cost shares.
Use nominal exposure when predicting ultimate cost for the 2025 test period.
"""
import json, pathlib
import numpy as np, pandas as pd

R = pathlib.Path('__RUN_ROOT__/noche')
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
    w_hi = (CUT - ps).dt.days.values  # Largest observation window, at the period's first day.
    w_lo = (CUT - pe).dt.days.values  # Smallest observation window, at the period's last day.
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
