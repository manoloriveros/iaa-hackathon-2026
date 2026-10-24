"""Backtest de estimadores de nivel con muestras del tamaño del emergente tomadas del desarrollado.

Pregunta: con dos años de experiencia del tamaño del emergente, ¿qué estimador de nivel por ramo predice mejor el nivel
del año siguiente? Se usa el desarrollado (cuatro años) con las relatividades g del GBM desarrollado (fijas).
Ventanas: 2021-2022 -> 2023 y 2022-2023 -> 2024 (2024 con e_ef). Muestras: pólizas al azar hasta igualar las filas
emergentes por año (autos 23.600, edificios 13.700, contenidos 17.300); 300 réplicas por ventana.
Nivel verdadero: Σ T0 / Σ e_ef·g del año objetivo en TODO el desarrollado (sin muestrear).
Estimadores:
  E1 agrupado: Σ T0 / Σ e_ef·g de los dos años de la muestra (receta de A1).
  E2 último año de la muestra.
  E3 agrupado con tendencia: E1 × (1 + t)^1,5, t = tendencia del desarrollado completo en los años de la ventana.
  E4 grandes siniestros: costes recortados a C (100.000 CU) en la muestra × factor de exceso del desarrollado completo
     en los años de la ventana (información externa a la muestra, como la que da el desarrollado al emergente).
  E5 = E4 con tendencia.
Error: log(estimado / verdadero); se informan sesgo, desviación típica y raíz del error cuadrático medio.
"""
import json, pathlib, sys
import numpy as np, pandas as pd

R = pathlib.Path('/home/claude/noche')
N = {'motor': 23600, 'buildings': 13700, 'contents': 17300}
CAP = 100000.0
rng = np.random.default_rng(20261024)
out = {}
a = pd.read_parquet(R / 'salidas/s1/asignacion.parquet'); a = a[(a.category == 'unica') & a.accepted]
for line in ['motor', 'buildings', 'contents']:
    b = pd.read_parquet(R / f'salidas/s1/base_{line}.parquet'); b = b[b.split == 'train'].reset_index(drop=True)
    g = pd.read_parquet(R / f'salidas/transfer/lg_dev21222324_m02_{line}_dev.parquet' if line != 'motor' else R / 'salidas/transfer/lg_dev21222324_v2fixs11_motor_dev.parquet').set_index('row_id').lg_dev
    b['m'] = b.eef_coste * np.exp(b.row_id.map(g).values)
    cap = a[a.line == line].assign(c=lambda x: np.minimum(x.net, CAP)).groupby('row_id').c.sum()
    b['t0c'] = b.row_id.map(cap).fillna(0.0).values
    yr = b.year.values; pol = b.policy_id.values
    S = {y: (b.t0.values[yr == y].sum(), b.t0c.values[yr == y].sum(), b.m.values[yr == y].sum()) for y in (2021, 2022, 2023, 2024)}
    Lt = {y: S[y][0] / S[y][2] for y in S}
    res = {}
    for (y1, y2, yt) in ((2021, 2022, 2023), (2022, 2023, 2024)):
        t = Lt[y2] / Lt[y1] - 1  # tendencia del desarrollado completo dentro de la ventana
        exc = (S[y1][0] + S[y2][0]) / (S[y1][1] + S[y2][1])
        idx = np.where((yr == y1) | (yr == y2))[0]
        pols = pd.unique(pol[idx]); rows_per_pol = len(idx) / len(pols) / 2
        npol = int(N[line] / rows_per_pol)
        errs = {k: [] for k in ['E1', 'E2', 'E3', 'E4', 'E5']}
        sub = b.iloc[idx]
        grp = sub.groupby('policy_id').indices
        for r in range(300):
            ch = rng.choice(pols, size=npol, replace=False)
            ii = np.concatenate([grp[p] for p in ch])
            s = sub.iloc[ii]
            T0, TC, MM = s.t0.values, s.t0c.values, s.m.values; Y = s.year.values
            e1 = T0.sum() / MM.sum(); e2 = T0[Y == y2].sum() / MM[Y == y2].sum()
            e4 = TC.sum() / MM.sum() * exc
            est = {'E1': e1, 'E2': e2, 'E3': e1 * (1 + t) ** 1.5, 'E4': e4, 'E5': e4 * (1 + t) ** 1.5}
            for k, v in est.items(): errs[k].append(np.log(v / Lt[yt]))
        res[f'{y1}-{y2}->{yt}'] = {k: {'sesgo': round(float(np.mean(v)), 4), 'de': round(float(np.std(v)), 4),
                                        'rmse': round(float(np.sqrt(np.mean(np.square(v)))), 4)} for k, v in errs.items()}
        res[f'{y1}-{y2}->{yt}']['tendencia_ventana'] = round(t, 4); res[f'{y1}-{y2}->{yt}']['exceso_100k'] = round(exc, 4)
    out[line] = res
    print(line, json.dumps(res), flush=True)
json.dump(out, open(R / 'salidas/produccion/nivel_backtest.json', 'w'), indent=1)
