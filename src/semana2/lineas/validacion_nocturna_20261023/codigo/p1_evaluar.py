"""Evaluación de la escalera de la parte 1 en V24 frente a S30 (misma etiqueta T0 de 2024, mismas filas)."""
import json, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/p1'
v = pd.concat([pd.read_parquet(O / f'v24_{l}.parquet') for l in ['motor', 'buildings', 'contents']], ignore_index=True)
f1 = [O / f'v24_f1_{l}.parquet' for l in ['motor', 'buildings', 'contents']]
if all(p.exists() for p in f1):
    v = v.merge(pd.concat([pd.read_parquet(p) for p in f1]), on='row_id', how='left')
s = pd.read_parquet(R / 'datos/p1ref/predicciones_v23_v24_s30.parquet'); s = s[s.corte == 'V24'].set_index('row_id')
res = {'filas_mias': int(len(v)), 'filas_S30_V24': int(len(s))}
v = v[v.row_id.isin(s.index)].reset_index(drop=True)
res['filas_comunes'] = int(len(v))
v['S30'] = s.loc[v.row_id, 'prediction'].values
res['y_igual_a_S30'] = bool(np.allclose(v.y.values, s.loc[v.row_id, 'y_T0'].values, atol=0.005))
res['max_dif_y'] = float(np.abs(v.y.values - s.loc[v.row_id, 'y_T0'].values).max())
MODELS = ['P1-L0', 'P1-GLM', 'P1-GBMc', 'P1-GBMf'] + (['P1-GBMf1'] if 'P1-GBMf1' in v else []) + ['S30']
y = v.y.values


def rescale(df, col):
    out = df[col].values.copy()
    for l, g in df.groupby('line'):
        idx = g.index.values; out[idx] *= g.y.sum() / g[col].sum()
    return out


thr = np.quantile(y, 0.995); body = y <= thr
tab = {}
for m in MODELS:
    mu = v[m].values; mo = rescale(v, m)
    vb = v[body].reset_index(drop=True); mb = rescale(vb, m)
    tab[m] = {'D2': round(M.d2(y, mu), 5), 'D2_nivel_oraculo': round(M.d2(y, mo), 5), 'D2_cuerpo': round(M.d2(vb.y.values, mb), 5),
              **{f'D2_{l}': round(M.d2(g.y.values, g[m].values), 5) for l, g in v.groupby('line')},
              **{f'AE_{l}': round(g.y.sum() / g[m].sum(), 4) for l, g in v.groupby('line')}}
res['tabla'] = tab
comp = M.components(v.customer_id.values, v.address_id.values)
bs = M.boot_d2_diff(y, {m: v[m].values for m in MODELS}, comp, n=2000)
res['dif_frente_a_S30'] = {m: {'diff': round(tab[m]['D2'] - tab['S30']['D2'], 5), 'q05': round(float(np.quantile(bs[m] - bs['S30'], .05)), 5),
                               'q95': round(float(np.quantile(bs[m] - bs['S30'], .95)), 5)} for m in MODELS if m != 'S30'}
json.dump(res, open(O / 'p1_evaluacion.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
