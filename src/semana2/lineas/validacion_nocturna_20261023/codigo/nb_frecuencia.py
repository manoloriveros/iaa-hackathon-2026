"""NB-N1: relatividad del nuevo negocio en frecuencia (más estable que el coste) y en severidad, en los dos mercados.
Frecuencia: Poisson GBM del desarrollado (esquema común, sin new_business, renewal_count ni cust_tenure, para medir el
efecto total del nuevo negocio), aplicado a ambos mercados; A/E de conteos NB frente a renovación.
"""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numpy as np, pandas as pd, lightgbm as lgb
from variables import features
import marco as M
R = pathlib.Path('/home/claude/noche'); res = {}
DROP = ['new_business', 'renewal_count', 'cust_tenure']
for line in ['motor', 'buildings', 'contents']:
    b1 = pd.read_parquet(R / f'salidas/s1/base_{line}.parquet'); b1 = b1[b1.split == 'train'].reset_index(drop=True)
    X1, c1, _ = features(b1, line, 's1'); X1['exposure_model'] = b1.exposure_model.values
    b2 = pd.read_parquet(R / f'salidas/s2/base_{line}.parquet'); b2 = b2[(b2.split == 'train') & (b2.year == 2023)].reset_index(drop=True)
    X2, c2, _ = features(b2, line, 's2'); X2['exposure_model'] = b2.exposure_model.values
    cols = [c for c in X1.columns if c in X2.columns and c not in DROP]
    for c in cols:
        if str(X1[c].dtype) == 'category':
            cats = list(X1[c].cat.categories); v = X2[c].astype('string')
            X2[c] = pd.Categorical(v.where(v.isin(cats), 'missing'), categories=cats)
    off1 = np.log(b1.eef_coste.values); n1 = b1.n_claims.values
    base = np.log(n1.sum() / np.exp(off1).sum())
    p = dict(objective='poisson', learning_rate=0.05, num_leaves=31, min_data_in_leaf=1000, feature_fraction=0.8,
             bagging_fraction=0.8, bagging_freq=1, lambda_l2=10, min_data_per_group=1000, cat_smooth=50, verbose=-1,
             seed=5, deterministic=True, force_row_wise=True, num_threads=2)
    inner = M.fold_of(b1.customer_id.values, salt='noche_dev', k=5) == 0
    dtr = lgb.Dataset(X1.loc[~inner, cols], n1[~inner], init_score=off1[~inner] + base)
    dva = lgb.Dataset(X1.loc[inner, cols], n1[inner], init_score=off1[inner] + base, reference=dtr)
    bst = lgb.train(p, dtr, 3000, valid_sets=[dva], callbacks=[lgb.early_stopping(100, verbose=False)])
    r = {'rounds': bst.best_iteration}
    for mk, X, b in (('dev_inner', X1[inner], b1[inner]), ('em2023', X2, b2)):
        mu = np.exp(bst.predict(X[cols], raw_score=True, num_iteration=bst.best_iteration) + np.log(b.eef_coste.values) + base)
        nb = b.new_business.values.astype(bool); n = b.n_claims.values
        ae_nb = n[nb].sum() / mu[nb].sum(); ae_rn = n[~nb].sum() / mu[~nb].sum()
        se = np.sqrt(1 / max(n[nb].sum(), 1) + 1 / max(n[~nb].sum(), 1))
        sev_nb = b.t0.values[nb].sum() / max(n[nb].sum(), 1); sev_rn = b.t0.values[~nb].sum() / max(n[~nb].sum(), 1)
        r[mk] = {'claims_nb': int(n[nb].sum()), 'AE_nb': round(ae_nb, 4), 'AE_ren': round(ae_rn, 4),
                 'freq_rel_nb': round(ae_nb / ae_rn, 4), 'log_se': round(se, 4), 'sev_rel_nb_crudo': round(sev_nb / sev_rn, 4)}
    res[line] = r; print(line, r, flush=True)
json.dump(res, open(R / 'salidas/nb_frecuencia.json', 'w'), indent=1)
