"""Relatividades del desarrollado con un GLM Tweedie 1,5 (alternativa interpretable a desarrollado_gbm.py).

Mismo esquema común y offset; numéricas a seis cuantiles, categorías raras a 'otros', ridge pequeño (1,9 millones de filas).
Uso: python desarrollado_glm.py ramo alpha
"""
import json, pathlib, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from variables import features, CATEG
import marco as M

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/transfer'
line = sys.argv[1]; alpha = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
t = time.time()
CONF = '--conf' in sys.argv
years = [int(x) for x in sys.argv[sys.argv.index('--años') + 1].split(',')] if '--años' in sys.argv else [2021, 2022, 2023, 2024]
b1 = pd.read_parquet(R / (f'salidas/conf/base_s1_{line}.parquet' if CONF else f'salidas/s1/base_{line}.parquet'))
b1 = b1[(b1.split == 'train') & b1.year.isin(years)].reset_index(drop=True)
X1, c1, _ = features(b1, line, 's1'); X1['exposure_model'] = b1.exposure_model.values
b2 = pd.read_parquet(R / (f'salidas/conf/base_s2_{line}.parquet' if CONF else f'salidas/s2/base_{line}.parquet'))
X2, c2, _ = features(b2, line, 's2'); X2['exposure_model'] = b2.exposure_model.values
if '--f1' in sys.argv:  # misma historia F1 que desarrollado_gbm.py (reportada antes de period_start, años observados)
    def hist(base, mk):
        a = pd.read_parquet(R / f'salidas/{mk}/asignacion.parquet'); a = a[(a.line == line) & a.accepted][['policy_id', 'report_date']]
        a['rd'] = pd.to_datetime(a.report_date)
        bb = base[['row_id', 'policy_id', 'period_start']].copy(); bb['ps'] = pd.to_datetime(bb.period_start)
        mm = bb.merge(a, on='policy_id'); mm = mm[mm.rd < mm.ps]
        n = bb.row_id.map(mm.groupby('row_id').size()).fillna(0).values
        first = bb.groupby('policy_id').ps.min()
        return np.minimum(n, 3), ((bb.ps - bb.policy_id.map(first)).dt.days / 365.25).round().clip(0, 3).values
    n1, y1 = hist(b1, 's1'); n2, y2 = hist(b2, 's2')
    X1['f1_siniestros_previos'] = n1; X1['f1_anios_observados'] = y1; X2['f1_siniestros_previos'] = n2; X2['f1_anios_observados'] = y2
cols = [c for c in X1.columns if c in X2.columns and c != 'make_model']
cat = CATEG | {c for c in cols if str(X1[c].dtype) == 'category'}
A1, A2 = M.design_glm(X1[cols], X2[cols], cols, cat, nbins=8, min_share=0.002)
y = b1.t0.values; off = np.log(b1.eef_coste.values)
inner = M.fold_of(b1.customer_id.values, salt='noche_dev', k=5) == 0
mu_va, _ = M.fit_glm_tweedie(A1[~inner], y[~inner], off[~inner], A1[inner], off[inner], alpha)
mu1, m = M.fit_glm_tweedie(A1, y, off, A1, off, alpha)
g1 = np.log(mu1) - off
g2 = np.log(m.predict(A2, offset=np.zeros(len(A2))))
c = np.log(np.average(np.exp(g1), weights=b1.exposure_model))
tag = (('dev' + ''.join(str(x)[-2:] for x in years) + '_') if '--años' in sys.argv or CONF or '--f1' in sys.argv else '') + f'glm{alpha:g}' + (sys.argv[sys.argv.index('--sufijo') + 1] if '--sufijo' in sys.argv else '')
pd.DataFrame({'row_id': b2.row_id, 'lg_dev': g2 - c}).to_parquet(O / f'lg_{tag}_{line}_em.parquet', index=False)
info = {'line': line, 'alpha': alpha, 'valid_d2_inner': round(float(M.d2(y[inner], mu_va)), 5), 'seconds': round(time.time() - t, 1),
        'n_coef': int(len(m.coef_)), 'cols': cols}
json.dump(info, open(O / f'info_{tag}_{line}.json', 'w'), indent=1)
print(info['line'], info['alpha'], info['valid_d2_inner'], info['n_coef'], info['seconds'])
