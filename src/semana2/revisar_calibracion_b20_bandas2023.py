"""Bandas B20 definidas con ajuste; lectura OOF2023, sin fit o recalibración."""
from pathlib import Path
from datetime import datetime, timezone
import json
import math
import os
import sys

for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '2'
REPO = Path(__file__).resolve().parents[2]
ROOT = REPO.parents[1]
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.linear_model import TweedieRegressor
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

KEY = ['market', 'line', 'row_id']
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: __import__('hashlib').sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def require(value, message):
    if not bool(value):
        raise ValueError(message)


def edges_from_fit_rates(rates):
    a = np.asarray(rates, float)
    require(len(a) > 0 and np.isfinite(a).all() and (a > 0).all(), 'Tasas de ajuste inválidas')
    order = np.sort(a)
    indices = [(len(a)*k+4)//5-1 for k in range(1, 5)]
    return order[indices]


def assign_band(rates, edges):
    a, e = np.asarray(rates, float), np.asarray(edges, float)
    require(np.isfinite(a).all() and (a > 0).all(), 'Tasas de lectura inválidas')
    require(e.shape == (4,) and np.isfinite(e).all() and (e > 0).all() and (np.diff(e) >= 0).all(), 'Cortes inválidos')
    # Band1 includes its upper cut. Repeated cuts retain empty bands, no tie splitting.
    return np.searchsorted(e, a, side='left')+1


def guard(frame):
    require(len(frame) > 0 and frame.year.eq(2023).all() and not frame.is_test.any(), 'Solo2023, test cerrado')
    require(not frame.duplicated(KEY).any(), 'Claves repetidas')
    require(frame.T0.ge(0).all() and np.isfinite(frame.T0).all(), 'T0 inválido')
    require(frame['e_cost_mix_1.0'].gt(0).all() and np.isfinite(frame['e_cost_mix_1.0']).all(), 'C0 inválido')


def cell_stats(f, model, cohort):
    pred = f['mu20'] if model == 'W2-B20' else f['mu19']
    cost, expected = float(f.T0.sum()), float(pred.sum())
    bygroup = f.groupby('group_id', sort=True).T0.sum()
    sq = float(np.square(bygroup).sum())
    return {'rows': len(f), 'groups': int(f.group_id.nunique()), 'positive_rows': int(f.T0.gt(0).sum()),
            'positive_groups': int(bygroup.gt(0).sum()), 'observed_total': cost, 'predicted_total': expected,
            'actual_over_expected': cost/expected if expected > 0 else None,
            'observed_minus_expected': cost-expected,
            'nominal_exposure': float(f.exposure.sum()), 'effective_cost_exposure': float(f['e_cost_mix_1.0'].sum()),
            'largest_group_cost_share': float(bygroup.max()/cost) if cost > 0 else None,
            'cost_concentration_equivalent_groups': cost*cost/sq if sq > 0 else None,
            'outside_training_rate_range': int(f.outside_training_rate_range.sum()), 'cohort': cohort, 'model_id': model}


def main():
    pp = Path(sys.argv[1]).resolve()
    plan = read(pp)
    require(sha(Path(__file__)) == plan['producer_sha256'], 'Código cambió')
    for x in plan['frozen_sources']:
        require(sha(ROOT/x['path']) == x['sha256'], 'Fuente cambió '+x['path'])
    forum = (ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
    require(forum.count(('<!-- aporte:'+plan['forum_prior']+' -->').encode()) == 1, 'Falta registro previo')
    def no_fit(*args, **kwargs):
        raise AssertionError('Reentrenamiento bloqueado en bandas')
    for cls in [TweedieRegressor, ColumnTransformer, SimpleImputer, StandardScaler, OneHotEncoder, Pipeline]:
        cls.fit = no_fit
        if hasattr(cls, 'fit_transform'):
            cls.fit_transform = no_fit
    out = ROOT/plan['output_run']
    out.mkdir(exist_ok=False)
    for src, name in [(pp, 'plan_snapshot.json'), (Path(__file__), 'code_snapshot.py')]:
        (out/name).write_bytes(src.read_bytes())
    (out/'forum_before_analysis.md').write_bytes(forum)
    started = datetime.now(timezone.utc).isoformat()
    source, frame_source = ROOT/plan['ridge_run'], ROOT/plan['frame_source']
    oof = pq.read_table(source/'oof_2023.parquet', filters=[('model_id', 'in', ['W2-B20', 'W2-B19'])]).to_pandas()
    data = {mid: f.sort_values(KEY).reset_index(drop=True) for mid, f in oof.groupby('model_id')}
    require(set(data) == {'W2-B20', 'W2-B19'} and all(len(f) == 50094 for f in data.values()), 'OOF incompleto')
    candidate, reference = data['W2-B20'], data['W2-B19']
    require(candidate[KEY].equals(reference[KEY]), 'Claves de comparadores distintas')
    for field in ['T0', 'fold', 'group_id', 'exposure', 'e_cost_mix_1.0']:
        require(candidate[field].equals(reference[field]), 'Comparadores incompatibles '+field)
    cuts, fitrows, heldrows = [], [], []
    for line in ['motor', 'buildings', 'contents']:
        for fold in range(5):
            f = pq.read_table(frame_source/f'inputs_2023/{line}_fold{fold}.parquet').to_pandas()
            guard(f)
            fit = f[f.fold.ne(fold)].copy()
            valid = f[f.fold.eq(fold)].sort_values(KEY).reset_index(drop=True)
            require(all(set(fit[k]).isdisjoint(valid[k]) for k in ['group_id', 'customer_id', 'address_id']), 'Fuga de grupo')
            bundle = joblib.load(source/'models'/f'{line}_fold{fold}'/'bundle.joblib')
            # This is inference with a saved estimator; no model or transform fit is possible.
            with threadpool_limits(limits=2):
                rate = bundle['estimator'].predict(bundle['transformer'].transform(fit[bundle['columns']]))
            edges = edges_from_fit_rates(rate)
            fr = fit[KEY+['year', 'fold', 'group_id', 'customer_id', 'address_id', 'T0', 'exposure', 'x_new_business', 'e_cost_mix_1.0']].copy()
            fr['model_fold'], fr['annual_rate'], fr['band'] = fold, rate, assign_band(rate, edges)
            fr['mu20'] = rate*fit['e_cost_mix_1.0'].to_numpy()
            fr['mu19'] = np.nan
            fr['outside_training_rate_range'] = False
            fitrows.append(fr)
            a = candidate[candidate.line.eq(line) & candidate.fold.eq(fold)].reset_index(drop=True)
            b = reference[reference.line.eq(line) & reference.fold.eq(fold)].reset_index(drop=True)
            require(a[KEY].equals(valid[KEY]) and a.T0.equals(valid.T0), 'OOF distinto de fuente')
            hr = a[KEY+['year', 'fold', 'group_id', 'T0', 'exposure', 'x_new_business', 'e_cost_mix_1.0']].copy()
            hr['annual_rate'], hr['band'] = a.annual_rate, assign_band(a.annual_rate, edges)
            hr['mu20'], hr['mu19'] = a.prediction, b.prediction
            hr['outside_training_rate_range'] = (a.annual_rate < float(rate.min())) | (a.annual_rate > float(rate.max()))
            heldrows.append(hr)
            score = float((np.sqrt(fr.mu20)-fr.T0/np.sqrt(fr.mu20)).sum()/np.sqrt(fr['e_cost_mix_1.0']).sum())
            cuts.append({'line': line, 'fold': fold, 'fit_rows': len(fit), 'heldout_rows': len(valid), 'edges': edges.tolist(),
                         'edge_indices0': [(len(fit)*k+4)//5-1 for k in range(1, 5)],
                         'training_rate_min': float(rate.min()), 'training_rate_max': float(rate.max()),
                         'unique_cuts': int(len(np.unique(edges))), 'normalized_intercept_score': score,
                         'fit_AE_not_forced_to_one': float(fr.T0.sum()/fr.mu20.sum()), 'labels_used_for_edges': False})
    fit = pd.concat(fitrows, ignore_index=True)
    held = pd.concat(heldrows, ignore_index=True).sort_values(KEY).reset_index(drop=True)
    require(len(fit) == 200376 and len(held) == 50094 and not held.duplicated(KEY).any(), 'Cohorte incompleta')
    fit.to_parquet(out/'training_rate_replays_2023.parquet', index=False)
    held.to_parquet(out/'heldout_bands_2023.parquet', index=False)
    dump(out/'band_cuts.json', cuts)
    cells = []
    for cohort, f, models in [('fit', fit, ['W2-B20']), ('heldout', held, ['W2-B20', 'W2-B19'])]:
        f = f.copy()
        f['business'] = np.where(f.x_new_business.eq(1), 'new_business', 'renewal')
        for dimension, keys in [('line', ['line']), ('line_fold', ['line', 'fold']), ('line_business', ['line', 'business'])]:
            # Training rows carry both original fold and model_fold: group by actual fitted model.
            usekeys = ['line', 'model_fold'] if cohort == 'fit' and dimension == 'line_fold' else keys
            for groupkey, g in f.groupby(usekeys, observed=True):
                labels = groupkey if isinstance(groupkey, tuple) else (groupkey,)
                label = '|'.join(map(str, labels))
                for band in range(1, 6):
                    cell = g[g.band.eq(band)]
                    for model in models:
                        cells.append({'dimension': dimension, 'label': label, 'band': band, **cell_stats(cell, model, cohort)})
    pd.DataFrame(cells).to_parquet(out/'calibration_cells_2023.parquet', index=False)
    report = {'id': plan['id'], 'author': 'Codex', 'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
              'run': rel(out), 'training_replay_rows': len(fit), 'heldout_rows': len(held), 'groups': int(held.group_id.nunique()),
              'total_observed': float(held.T0.sum()), 'total_expected_B20': float(held.mu20.sum()), 'total_expected_B19': float(held.mu19.sum()),
              'global_AE_B20': float(held.T0.sum()/held.mu20.sum()), 'global_AE_B19': float(held.T0.sum()/held.mu19.sum()),
              'outside_training_range_rows': int(held.outside_training_rate_range.sum()), 'new_fits': 0,
              'saved_estimators_replayed_on_training_rows': 15, 'new_model_recipes': 0, 'new_test_prices': 0, 'new_bootstrap': 0,
              'bands': 'Five nominalannualrate quintilebands perline/fold, training-only equalrow empiricalinverseCDF; ties retained and emptybands visible. Common B20 assignment for bothmodels.',
              'training_replays_not_independent_rows': True, 'reference': 'W2-B00', 'promotion': False,
              '2024_test_closed': True, 'ledger_read': False, 'prior_external2024_subject_exposure_disclosed': True,
              'professional_independent_validation': False, 'plan_sha256': sha(pp), 'code_sha256': sha(Path(__file__))}
    for x in plan['frozen_sources']:
        require(sha(ROOT/x['path']) == x['sha256'], 'Fuente cambió al cerrar')
    dump(out/'report.json', report)
    dump(out/'manifest.json', {'files': [{'path': x.relative_to(out).as_posix(), 'sha256': sha(x)} for x in sorted(out.rglob('*')) if x.is_file()]})
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
