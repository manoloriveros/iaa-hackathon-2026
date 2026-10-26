"""Valida la información residual de prima con matemática y replay sin ajuste."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton')
R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

b = load('premium5', R / 'herramientas/mision017_fase2_tanda5_prima.py')
stats = load('stat3', R / 'herramientas/validar_mision017_fase2_tanda3.py')
encoding = load('encoding4', R / 'herramientas/validar_mision017_fase2_tanda4.py')
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits

OUT = b.OUT / 'validation_v1'

def independent_premium(f):
    # Rebuild the group medians with NumPy, without pandas groupby/transform.
    logp = np.log(f.written_premium.to_numpy(float))
    keys = list(zip(f.year.to_numpy(), f.channel.astype(str).to_numpy()))
    positions = {}
    for i, key in enumerate(keys):
        positions.setdefault(key, []).append(i)
    centered = np.empty(len(f))
    for ids in positions.values():
        ids = np.asarray(ids)
        centered[ids] = logp[ids] - np.median(logp[ids])
    assert np.array_equal(centered, b.premium_feature(f))
    return centered

def source_mathematics(line, master, regions):
    f = pd.read_parquet(b.data.OUT / f'{line}.parquet')
    premium = pd.read_parquet(b.data.RAW / f'policies_{line}.parquet', columns=['row_id', 'written_premium'])
    f = f.merge(premium, on='row_id', validate='one_to_one').merge(master, on='customer_id', validate='many_to_one')
    f = f.merge(regions, on='address_id', validate='many_to_one')
    model = b.m.lgb.Booster(model_file=str(b.PARENT / f'modelos/prod/T2b_{line}.txt'))
    offset = f.e_cost.to_numpy(float) * np.exp(model.predict(b.m.source_matrix(f, model), raw_score=True, num_threads=2))
    off = np.log(offset)
    premium_x = independent_premium(f)
    y = f.T0.to_numpy(float)
    reports = []
    for family in ['premium', 'joint']:
        effect = b.read(b.OUT / f'{family}_{line}.json')
        assert b.sha(b.data.OUT / f'{line}.parquet') == effect['source_sha256']
        blocks = [sparse.csr_matrix(premium_x[:, None])]
        for col, categories in zip(effect['catcols'], effect['categories']):
            values = f[col].astype('string').fillna('__MISSING__').astype(str)
            blocks.append(encoding.block(values, categories, True))
        blocks.append(encoding.block(f.year, effect['year_categories'], False))
        X = sparse.hstack(blocks, format='csr')
        coef = np.asarray(effect['coef'])
        penalty = np.r_[np.ones(X.shape[1] - len(effect['year_categories'])), np.zeros(len(effect['year_categories']))]
        assert np.array_equal(penalty, effect['penalty']) and effect['alpha'] == b.ALPHA
        def objective(beta):
            root = np.exp((off + X @ beta) / 2)
            return float(2 * np.mean(root + y / root - 2 * np.sqrt(y)) + .5 * b.ALPHA * np.dot(penalty * beta, beta))
        mu = np.exp(off + X @ coef)
        independent = mean_tweedie_deviance(y, mu, power=1.5) / 2 + .5 * b.ALPHA * np.dot(penalty * coef, coef)
        assert abs(independent - effect['objective']) < 1e-8 * (1 + abs(independent))
        gradient = np.asarray(X.T @ ((np.sqrt(mu) - y / np.sqrt(mu)) / len(y))).ravel() + b.ALPHA * penalty * coef
        assert np.abs(gradient).max() < 1e-4
        rng = np.random.default_rng(752)
        errors = []
        for _ in range(3):
            direction = rng.normal(size=len(coef)); direction /= np.linalg.norm(direction)
            h = 1e-4
            error = abs((objective(coef + h * direction) - objective(coef - h * direction)) / (2 * h) - float(gradient @ direction))
            assert error < 5e-6
            errors.append(error)
        reports.append({'line': line, 'family': family, 'rows': len(f), 'sklearn_objective_match': True,
            'independent_medians_and_sparse_encoding': True, 'max_abs_gradient': float(np.abs(gradient).max()),
            'finite_difference_errors': errors, 'new_fit_calls': 0})
    return reports

def validate():
    assert not OUT.exists()
    plan = b.read(b.PLAN)
    assert b.read(b.OUT / 'registration.json')['plan_sha256'] == b.sha(b.PLAN)
    for path, digest in plan['sources'].items():
        assert b.sha(ROOT / path) == digest, path
    report = b.read(b.OUT / 'price_report.json')
    assert report['source_price_fits'] == 6 and report['target_C0_fits'] == 0
    p = pd.read_parquet(b.OUT / 'oof_2023_2024.parquet')
    assert p.row_id.is_unique and len(p) == 109296
    OUT.mkdir()
    schema = {'N3': 'N0', 'S1': 'Q1', 'S2': 'Q2', 'S3': 'Q3'}
    x = p[['T0', 'group_id', 'line', 'new_business', 'fold', 'year', *schema]].rename(columns=schema).copy()
    stats.OUT = OUT
    with threadpool_limits(limits=2):
        comparison = stats.evaluate(x, plan)
    rename = {'Q1': 'S1', 'Q2': 'S2', 'Q3': 'S3'}
    comparison = {rename[key]: value for key, value in comparison.items()}
    for filename in ['segments.csv', 'folds.csv', 'years.csv']:
        t = pd.read_csv(OUT / filename); t['model'] = t.model.map(rename)
        t.to_csv(OUT / filename, index=False)
    for old, new in rename.items():
        (OUT / f'influence_{new}.parquet').write_bytes((OUT / f'influence_{old}.parquet').read_bytes())
    original = b.optimize.minimize
    b.optimize.minimize = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('No optimizer during replay'))
    replays = []; mathematics = []
    try:
        with threadpool_limits(limits=2):
            master = pd.read_parquet(b.data.RAW / 'customers.parquet', columns=['customer_id', 'marketing_segment'])
            regions = pd.read_parquet(b.data.RAW / 'addresses.parquet', columns=['address_id', 'region']).rename(columns={'region': 'source_region'})
            for line in b.data.LINES:
                mathematics.extend(source_mathematics(line, master, regions))
                effects = {family: b.read(b.OUT / f'{family}_{line}.json') for family in ['premium', 'joint']}
                for held in range(5):
                    t = p.loc[p.line.eq(line) & p.fold.eq(held)].copy()
                    independent_premium(t)
                    saved = b.read(b.OUT / f'normalizers_{line}_fold{held}.json')
                    for family in ['premium', 'joint']:
                        assert saved[f'{family}_effect_sha256'] == b.sha(b.OUT / f'{family}_{line}.json')
                    for name, family, strength in [('S1', 'premium', 1.), ('S2', 'joint', 1.), ('S3', 'joint', .5)]:
                        pred, norm = b.apply(t, t.N3.to_numpy(float), effects[family], strength)
                        assert np.array_equal(pred, t[name].to_numpy(float)) and norm == saved['normalizers'][name]
                        poison = t.assign(T0=-1e30, reserve=-1e30, exposure=t.exposure * 1000)
                        alt, _ = b.apply(poison, t.N3.to_numpy(float), effects[family], strength)
                        assert np.array_equal(pred, alt)
                        shifted, _ = b.apply(t.assign(written_premium=t.written_premium * 1000), t.N3.to_numpy(float), effects[family], strength)
                        assert np.allclose(pred, shifted, rtol=1e-12, atol=1e-10)
                    replays.append({'line': line, 'fold': held, 'rows': len(t), 'bit_exact': True,
                        'label_and_exposure_poison_invariant': True, 'currency_invariant': True,
                        'cell_totals_preserved': True, 'new_fit_calls': 0})
    finally:
        b.optimize.minimize = original
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'scores': report['scores'],
        'reference': 'N3 research comparator, not promoted', 'comparisons': comparison,
        'source_mathematics': mathematics, 'replays': replays, 'metric_second_method': True,
        'new_fits': 0, 'new_reporting_fits': 0, 'new_submissions': 0, 'B00_preserved': True,
        '2024_is_adaptive_development': True, 'not_prospective_independent_confirmation': True,
        'CI_conditional_on_fixed_source_model': True, 'quote_history_and_reporting_uncertainty_not_identified': True,
        'statistic_source': {'path': b.rel(Path(stats.__file__)), 'sha256': b.sha(Path(stats.__file__)), 'input_schema_mapping': schema},
        'goal_achieved': False}
    b.dump(OUT / 'report.json', result)
    print(json.dumps({'scores': report['scores'], 'comparisons': comparison,
        'source_math_pass': True, 'replays': len(replays), 'new_fits': 0}))

if __name__ == '__main__':
    validate()
