"""Parte 1: escalera simple en V24 (ajuste 2021-2023 del desarrollado, evaluación sobre el T0 observado de 2024).

Vínculo de observación: e_ef_coste con la curva de reporte de ocurrencias <= 2023 (salidas/conf/reporte_F_conf.json).
P1-L0   tasa por ramo (balance 2021-2023).
P1-GLM  GLM Tweedie 1,5 con el esquema común (desarrollado_glm, ridge 1), 2021-2023.
P1-GBMc LightGBM Tweedie con el esquema común (el de la semana 2, sin make_model en autos), 2021-2023.
P1-GBMf LightGBM Tweedie con todas las variables F0 del desarrollado (edad exacta, crédito, kilometraje, telemática,
        región, make_model fuera), mismos hiperparámetros, 2021-2023.
Referencias: S30 (y S41 = S30 con factores de nivel; en V24 solo cambia la escala por ramo) desde
predicciones_v23_v24_s30.parquet (corte V24, ya con el factor f23 de la receta).
Métricas: D² completo; D² con cada modelo reescalado al total observado de 2024 por ramo (oráculo de nivel, mide forma);
D² del cuerpo (sin el 0,5 % de filas con mayor T0, reescalado por ramo).
"""
import json, pathlib, sys, time
import numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M
from variables import features, CATEG
from exposicion_efectiva import add_effective, PERILS

R = pathlib.Path('/home/claude/noche'); O = R / 'salidas/p1'; O.mkdir(parents=True, exist_ok=True)
rep = json.load(open(R / 'salidas/conf/reporte_F_conf.json')); Fc = rep['F_coste']; B = rep['bucket_days']
ins = json.load(open(R / 'salidas/conf/conf_insumos.json'))
EXTRA = {'motor': ['driver_age', 'annual_mileage', 'telematics_opt_in', 'telematics_score', 'credit_band', 'region'],
         'buildings': ['policyholder_age', 'credit_band', 'region'], 'contents': ['policyholder_age', 'credit_band', 'region']}
lines = [a for a in sys.argv[1:] if not a.startswith('--')] or ['motor', 'buildings', 'contents']
out = []
for line in lines:
    t = time.time()
    b = pd.read_parquet(R / f'salidas/s1/base_{line}.parquet'); b = b[b.split == 'train'].reset_index(drop=True)
    b = add_effective(b, line, Fc, B, ins[f's1_{line}']['shares'])
    X, cols, df = features(b, line, 's1'); X['exposure_model'] = b.exposure_model.values
    for c in EXTRA[line]:
        if c.startswith('f1_'): continue
        v = df[c] if c in df else None
        if v is None: continue
        X[c] = v.astype('string').fillna('missing').astype('category') if c in ('credit_band', 'region') else pd.to_numeric(v, errors='coerce').astype(float)
    if '--f1' in sys.argv:  # F1: historia propia de la póliza conocida al inicio del periodo (reportada antes de period_start)
        a = pd.read_parquet(R / 'salidas/s1/asignacion.parquet'); a = a[(a.line == line) & a.accepted]
        a = a[['policy_id', 'loss_date', 'report_date']].copy(); a['rd'] = pd.to_datetime(a.report_date)
        bb = b[['row_id', 'policy_id', 'period_start']].copy(); bb['ps'] = pd.to_datetime(bb.period_start)
        mm = bb.merge(a, on='policy_id', how='inner'); mm = mm[mm.rd < mm.ps]
        hist = mm.groupby('row_id').size()
        X['f1_siniestros_previos'] = b.row_id.map(hist).fillna(0).values
        first = bb.groupby('policy_id').ps.min()
        X['f1_anios_observados'] = ((bb.ps - bb.policy_id.map(first)).dt.days / 365.25).values
        EXTRA[line] = EXTRA[line] + ['f1_siniestros_previos', 'f1_anios_observados']
    fit = b.year <= 2023; ev = b.year == 2024
    y = b.t0.values; off = np.log(b.eef_coste.values)
    base = np.log(y[fit].sum() / np.exp(off[fit]).sum())
    res = {'row_id': b.row_id[ev].values, 'line': line, 'y': y[ev], 'customer_id': b.customer_id[ev].values, 'address_id': b.address_id[ev].values}
    res['P1-L0'] = np.exp(off[ev] + base)
    common = [c for c in cols if c != 'make_model'] + ['exposure_model']
    full = common + [c for c in EXTRA[line] if c in X]
    # GLM esquema común
    A, Bm = M.design_glm(X.loc[fit, [c for c in common]], X.loc[ev, [c for c in common]], common, CATEG | {c for c in common if str(X[c].dtype) == 'category'}, nbins=8, min_share=0.002)
    mu_ev, mdl = M.fit_glm_tweedie(A, y[fit], off[fit], Bm, off[ev], 1.0)
    mu_fit = mdl.predict(A, offset=off[fit]); res['P1-GLM'] = mu_ev * y[fit].sum() / mu_fit.sum()
    p = dict(objective='tweedie', tweedie_variance_power=1.5, learning_rate=0.02, num_leaves=31, min_data_in_leaf=1000,
             feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, min_data_per_group=1000,
             cat_smooth=50, verbose=-1, seed=11, deterministic=True, force_row_wise=True, num_threads=2)
    inner = M.fold_of(b.customer_id.values, salt='noche_dev', k=5) == 0
    variants = (('P1-GBMf1', full),) if '--f1' in sys.argv else (('P1-GBMc', common), ('P1-GBMf', full))
    for name, cs in variants:
        f_tr = fit & ~inner; f_va = fit & inner
        dtr = lgb.Dataset(X.loc[f_tr, cs], y[f_tr], init_score=off[f_tr] + base, free_raw_data=False)
        dva = lgb.Dataset(X.loc[f_va, cs], y[f_va], init_score=off[f_va] + base, reference=dtr)
        bst = lgb.train(p, dtr, 4000, valid_sets=[dva], callbacks=[lgb.early_stopping(400, verbose=False)])
        nbr = bst.best_iteration
        fm = lgb.train(p, lgb.Dataset(X.loc[fit, cs], y[fit], init_score=off[fit] + base), nbr)
        mu_ev = np.exp(fm.predict(X.loc[ev, cs], raw_score=True) + off[ev] + base)
        mu_fit = np.exp(fm.predict(X.loc[fit, cs], raw_score=True) + off[fit] + base)
        res[name] = mu_ev * y[fit].sum() / mu_fit.sum(); res[name + '_rondas'] = nbr
    rd = {k: v for k, v in res.items() if not k.endswith('_rondas')}
    o = pd.DataFrame(rd)
    if '--f1' in sys.argv:
        o = o[['row_id', 'P1-GBMf1']]
        o.to_parquet(O / f'v24_f1_{line}.parquet', index=False)
    else:
        o.to_parquet(O / f'v24_{line}.parquet', index=False)
    print(line, 'filas 2024', int(ev.sum()), {k: v for k, v in res.items() if k.endswith('_rondas')}, round(time.time() - t, 1), 's', flush=True)
