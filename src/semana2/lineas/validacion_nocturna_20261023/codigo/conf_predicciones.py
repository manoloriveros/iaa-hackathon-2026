"""Predicciones congeladas de la confirmación 2024 (ajuste solo con etiquetas emergentes de 2023 y desarrollado 2021-2023).

R0  tasa por ramo: mu = e_ef_2024 * sum(T0_2023) / sum(e_ef_2023).
A1  relatividades GBM del desarrollado (v2: sin make_model, con mes de inicio, lr 0,02) x nivel emergente por ramo de 2023.
A2  A1 + factor de región emergente (GLM Tweedie con offset, ridge 1), reescalado al total de 2023.
A3  A1 x (1 + t_ramo), t = crecimiento anual geométrico 2021->2023 del índice de coste del desarrollado dado el modelo.
El script no lee T0 de 2024: las columnas de etiqueta de las filas 2024 se eliminan antes de cualquier cálculo.
"""
import hashlib, json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M
from variables import features, CATEG

R = pathlib.Path('/home/claude/noche'); C = R / 'salidas/conf'; T = R / 'salidas/transfer'
OUT = C / 'predicciones'; OUT.mkdir(exist_ok=True)
LABELS = ['t0', 'paid', 'incurred', 'recov', 'n_claims', 'n_open', 'case_reserve']
rows = []; info = {}
for line in ['motor', 'buildings', 'contents']:
    b = pd.read_parquet(C / f'base_s2_{line}.parquet')
    lab = [c for c in b.columns if c in LABELS or c.startswith('t0_') or (c.startswith('n_') and c not in ('n_rows',))]
    b.loc[b.year == 2024, lab] = np.nan  # sin etiquetas 2024
    g = pd.read_parquet(T / f'lg_dev212223_v2conf_{line}_em.parquet').set_index('row_id').lg_dev
    b['g'] = np.exp(b.row_id.map(g).values)
    assert b.g.notna().all()
    f = b.year == 2023; v = b.year == 2024
    assert b.loc[v, 't0'].isna().all()
    y23 = b.loc[f, 't0'].values
    # R0
    r0 = b.loc[v, 'eef_coste'].values * y23.sum() / b.loc[f, 'eef_coste'].sum()
    # A1
    m23 = b.loc[f, 'eef_coste'] * b.loc[f, 'g']; L1 = y23.sum() / m23.sum()
    a1 = (b.loc[v, 'eef_coste'] * b.loc[v, 'g']).values * L1
    # A2
    X, cols, df = features(b, line, 's2')
    A, Bm = M.design_glm(X.loc[f, ['region']], X.loc[v, ['region']], ['region'], CATEG)
    off23 = np.log(m23.values); off24 = np.log((b.loc[v, 'eef_coste'] * b.loc[v, 'g']).values)
    mu_v, mdl = M.fit_glm_tweedie(A, y23, off23, Bm, off24, 1.0)
    mu_f = mdl.predict(A, offset=off23); a2 = mu_v * y23.sum() / mu_f.sum()
    # A3: índice de coste del desarrollado por año dado el modelo (2021-2023)
    d = pd.read_parquet(C / f'base_s1_{line}.parquet')
    gd = pd.read_parquet(T / f'lg_dev212223_v2conf_{line}_dev.parquet').set_index('row_id').lg_dev
    d['m'] = d.eef_coste * np.exp(d.row_id.map(gd))
    idx = d.groupby('year').apply(lambda x: x.t0.sum() / x.m.sum(), include_groups=False)
    t = (idx[2023] / idx[2021]) ** 0.5 - 1
    a3 = a1 * (1 + t)
    info[line] = {'L_R0': float(y23.sum() / b.loc[f, 'eef_coste'].sum()), 'L_A1': float(L1), 'trend_A3': float(t),
                  'dev_index': {int(k): float(v_) for k, v_ in idx.items()},
                  'region_coef': dict(zip(map(str, mdl.feature_names_), np.round(mdl.coef_, 4).tolist()))}
    rows.append(pd.DataFrame({'row_id': b.loc[v, 'row_id'].values, 'line': line, 'customer_id': b.loc[v, 'customer_id'].values,
                              'address_id': b.loc[v, 'address_id'].values, 'new_business': b.loc[v, 'new_business'].values,
                              'R0': r0, 'A1': a1, 'A2': a2, 'A3': a3}))
P = pd.concat(rows, ignore_index=True)
assert (P[['R0', 'A1', 'A2', 'A3']] > 0).all().all() and np.isfinite(P[['R0', 'A1', 'A2', 'A3']]).all().all()
P.to_parquet(OUT / 'predicciones_2024.parquet', index=False)
info['sha256_predicciones'] = hashlib.sha256((OUT / 'predicciones_2024.parquet').read_bytes()).hexdigest()
info['filas'] = int(len(P)); info['totales'] = P.groupby('line')[['R0', 'A1', 'A2', 'A3']].sum().round(2).to_dict()
json.dump(info, open(OUT / 'predicciones_2024_info.json', 'w'), indent=1)
print(json.dumps(info, indent=1))
