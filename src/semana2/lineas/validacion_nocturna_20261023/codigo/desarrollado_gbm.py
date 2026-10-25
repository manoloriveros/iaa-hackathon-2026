"""Relatividades del mercado desarrollado con el esquema común (TRF-N1).

LightGBM Tweedie 1,5 por ramo, entrenado con 2021-2024 del desarrollado (offset log e_ef_coste), solo con variables que
existen en los dos mercados (edad en bandas, sin región, sin crédito, kilometraje ni telemática) más la exposición.
Las etiquetas emergentes no intervienen: aplicar el modelo al emergente no filtra información del desarrollo 2023.
Guarda el modelo y la predicción log-relativa g_dev para cada fila emergente (train y test) y para el desarrollado.
Uso: python desarrollado_gbm.py ramo [--años 2021,2022,2023,2024]
"""
import json, pathlib, sys, time
import numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from variables import features
import marco as M

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/transfer'; O.mkdir(parents=True, exist_ok=True)
line = sys.argv[1]
years = [2021, 2022, 2023, 2024]
if '--años' in sys.argv:
    years = [int(x) for x in sys.argv[sys.argv.index('--años') + 1].split(',')]
tag = 'dev' + ''.join(str(y)[-2:] for y in years) + (sys.argv[sys.argv.index('--sufijo') + 1] if '--sufijo' in sys.argv else '')
LR = float(sys.argv[sys.argv.index('--lr') + 1]) if '--lr' in sys.argv else 0.05
PAT = int(sys.argv[sys.argv.index('--pat') + 1]) if '--pat' in sys.argv else 200
SEED = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 11
t = time.time()
CONF = '--conf' in sys.argv  # confirmación: bases sin etiquetas de 2024
b1 = pd.read_parquet(R / (f'salidas/conf/base_s1_{line}.parquet' if CONF else f'salidas/s1/base_{line}.parquet'))
b1 = b1[(b1.split == 'train') & b1.year.isin(years)].reset_index(drop=True)
X1, cols1, _ = features(b1, line, 's1')
X1['exposure_model'] = b1.exposure_model.values
b2 = pd.read_parquet(R / (f'salidas/conf/base_s2_{line}.parquet' if CONF else f'salidas/s2/base_{line}.parquet'))
X2, cols2, _ = features(b2, line, 's2')
X2['exposure_model'] = b2.exposure_model.values
DROPC = sys.argv[sys.argv.index('--sin') + 1].split(',') if '--sin' in sys.argv else []
CLIMA = ['wind_exposure_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c']
if '--clima' in sys.argv:  # CLIMA-N1: clima persistente de la dirección medido en los otros años (nunca el del propio año)
    def otros(base, mk, yrs):
        w = pd.read_parquet(R / f'datos/{mk}/weather.parquet'); w = w[w.year.isin(yrs)]
        pv = w.pivot_table(index='address_id', columns='year', values=CLIMA)
        out = pd.DataFrame(index=base.index)
        for v in CLIMA:
            vals = np.stack([base.address_id.map(pv[(v, y)]).values for y in yrs], axis=1)
            mask = np.stack([(base.year.values != y) for y in yrs], axis=1)
            out[f'cl_{v}'] = np.nansum(np.where(mask, vals, 0), axis=1) / np.maximum((mask & ~np.isnan(vals)).sum(axis=1), 1)
        return out
    c1x = otros(b1, 's1', [2021, 2022, 2023, 2024]); c2x = otros(b2, 's2', [2023, 2024])
    for c in c1x: X1[c] = c1x[c].values; X2[c] = c2x[c].values
if '--f1' in sys.argv:  # F1-N1: historia propia de la póliza conocida al inicio (reportada antes de period_start)
    def hist(base, mk):
        a = pd.read_parquet(R / f'salidas/{mk}/asignacion.parquet'); a = a[(a.line == line) & a.accepted][['policy_id', 'report_date']]
        a['rd'] = pd.to_datetime(a.report_date)
        bb = base[['row_id', 'policy_id', 'period_start']].copy(); bb['ps'] = pd.to_datetime(bb.period_start)
        mm = bb.merge(a, on='policy_id'); mm = mm[mm.rd < mm.ps]
        n = bb.row_id.map(mm.groupby('row_id').size()).fillna(0).values
        first = bb.groupby('policy_id').ps.min()
        yrs = ((bb.ps - bb.policy_id.map(first)).dt.days / 365.25).values
        return n, yrs
    n1, y1 = hist(b1, 's1'); n2, y2 = hist(b2, 's2')
    X1['f1_siniestros_previos'] = n1; X1['f1_anios_observados'] = y1
    X2['f1_siniestros_previos'] = n2; X2['f1_anios_observados'] = y2
cols = [c for c in X1.columns if c in X2.columns and c not in DROPC]
# categorías alineadas: las del desarrollado; las emergentes nuevas pasan a 'missing'
for c in cols:
    if str(X1[c].dtype) == 'category':
        cats = list(X1[c].cat.categories)
        v = X2[c].astype('string')
        X2[c] = pd.Categorical(v.where(v.isin(cats), 'missing'), categories=cats)
        unseen = int((~v.isin(cats)).sum())
        if unseen: print('categoría no vista', c, unseen)
y = b1.t0.values; off = np.log(b1.eef_coste.values)
if '--cap' in sys.argv:  # ROB-C1: relatividades con siniestros topados a CAP; el exceso lo absorbe el nivel emergente por balance
    CAP = float(sys.argv[sys.argv.index('--cap') + 1])
    asg = pd.read_parquet(R / 'salidas/s1/asignacion.parquet'); asg = asg[(asg.category == 'unica') & asg.accepted & (asg.line == line)]
    full_t0 = b1.row_id.map(asg.groupby('row_id').net.sum()).fillna(0.0).values
    assert np.allclose(full_t0, y, atol=0.01), 'el T0 de la base no cuadra con la asignación'
    y = b1.row_id.map(asg.assign(c=np.minimum(asg.net, CAP)).groupby('row_id').c.sum()).fillna(0.0).values
base = np.log(y.sum() / np.exp(off).sum())
p = dict(objective='tweedie', tweedie_variance_power=1.5, learning_rate=LR, num_leaves=31, min_data_in_leaf=1000,
         feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, min_data_per_group=1000,
         cat_smooth=50, verbose=-1, seed=SEED, deterministic=True, force_row_wise=True, num_threads=2)
if '--reg' in sys.argv:  # ROB-C2: árboles más pequeños y más regularizados
    p.update(num_leaves=15, min_data_in_leaf=3000, lambda_l2=50.0, feature_fraction=0.7)
if '--params' in sys.argv:  # ROB-C4: rejilla elegida solo con la validación interna del desarrollado
    p.update(json.loads(sys.argv[sys.argv.index('--params') + 1]))
inner = M.fold_of(b1.customer_id.values, salt='noche_dev', k=5) == 0
dtr = lgb.Dataset(X1.loc[~inner, cols], y[~inner], init_score=off[~inner] + base, free_raw_data=False)
dva = lgb.Dataset(X1.loc[inner, cols], y[inner], init_score=off[inner] + base, reference=dtr)
bst = lgb.train(p, dtr, num_boost_round=4000, valid_sets=[dva], callbacks=[lgb.early_stopping(PAT, verbose=False)])
nb = bst.best_iteration
full = lgb.train(p, lgb.Dataset(X1[cols], y, init_score=off + base), num_boost_round=nb)
full.save_model(str(O / f'gbm_{tag}_{line}.txt'))
g1 = full.predict(X1[cols], raw_score=True); g2 = full.predict(X2[cols], raw_score=True)
c1 = np.log(np.average(np.exp(g1), weights=b1.exposure_model))  # centrar a relatividad media 1 en el desarrollado
pd.DataFrame({'row_id': b2.row_id, 'lg_dev': g2 - c1}).to_parquet(O / f'lg_{tag}_{line}_em.parquet', index=False)
pd.DataFrame({'row_id': b1.row_id, 'lg_dev': g1 - c1}).to_parquet(O / f'lg_{tag}_{line}_dev.parquet', index=False)
imp = pd.Series(full.feature_importance('gain'), index=cols).sort_values(ascending=False)
info = {'line': line, 'years': years, 'rows': int(len(b1)), 'rounds': int(nb), 'valid_d2_inner': None,
        'seconds': round(time.time() - t, 1), 'importance_gain_share': (imp / imp.sum()).round(4).head(25).to_dict(),
        'cols': cols}
mu_va = np.exp(bst.predict(X1.loc[inner, cols], raw_score=True) + off[inner] + base)
info['valid_d2_inner'] = round(float(M.d2(y[inner], mu_va)), 5)
json.dump(info, open(O / f'info_{tag}_{line}.json', 'w'), indent=1)
print(json.dumps(info, indent=1))
