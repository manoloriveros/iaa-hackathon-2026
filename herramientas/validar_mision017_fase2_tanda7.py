"""Métrica, sensibilidad de cartera, fuente y replay de clima, sin ajustar."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

b = load('weather7', R / 'herramientas/mision017_fase2_tanda7_clima.py')
stats = load('stats3', R / 'herramientas/validar_mision017_fase2_tanda3.py')
encoding = load('encoding4', R / 'herramientas/validar_mision017_fase2_tanda4.py')
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits

OUT = b.OUT / 'validation_v1'

def weighted_sensitivity(p, plan):
    y = p.T0.to_numpy(float); weight = p.weight.to_numpy(float)
    unit = b.m.unit; names = ['W1', 'W2', 'W3']; base = unit(y, p.N3.to_numpy(float))
    den = float(8 * (np.sqrt(np.dot(weight, y) * weight.sum()) - np.dot(weight, np.sqrt(y))))
    assert abs(den - float(np.sum(weight * unit(y, np.full(len(y), np.average(y, weights=weight)))))) < 1e-6
    for name in ['N3', *names]:
        assert abs(np.average(unit(y, p[name]), weights=weight) - mean_tweedie_deviance(y, p[name], power=1.5, sample_weight=weight)) < 1e-7
    gi, groups = pd.factorize(p.group_id, sort=True); G = len(groups)
    total = np.bincount(gi, weights=weight * y); count = np.bincount(gi, weights=weight)
    root = np.bincount(gi, weights=weight * np.sqrt(y))
    d = np.column_stack([np.bincount(gi, weights=weight * (base - unit(y, p[name]))) for name in names])
    rng = np.random.default_rng(plan['bootstrap']['seed']); draws = []
    for _ in range(80):
        multiplicity = rng.multinomial(G, np.full(G, 1 / G), size=25)
        null = 8 * (np.sqrt((multiplicity @ total) * (multiplicity @ count)) - multiplicity @ root)
        assert (null > 0).all(); draws.append((multiplicity @ d) / null[:, None])
    draws = np.vstack(draws); result = {}
    for j, name in enumerate(names):
        result[name] = {'delta': float(d[:, j].sum() / den), 'bootstrap95': np.quantile(draws[:, j], [.025, .975]).tolist(),
            'role': 'Sensitivity only: the proposed weighted-primary ESS gate failed; no retrospective rescue'}
    np.save(OUT / 'weighted_bootstrap_deltas.npy', draws)
    return result

def mathematics(line, family):
    a = b.read(b.OUT / f'{family}_{line}.json'); path = b.OUT / f'source_inputs_{line}.parquet'
    assert b.sha(path) == a['source_input_sha256']; f = pd.read_parquet(path)
    assert f.market.eq('developed').all() and f.year.isin([2021, 2022, 2023, 2024]).all()
    original = pd.read_parquet(b.m.data.OUT / f'{line}.parquet', columns=['row_id', 'T0', 'year', 'address_id'])
    assert np.array_equal(f.row_id, original.row_id) and np.array_equal(f.T0, original.T0)
    assert np.array_equal(f.year, original.year) and np.array_equal(f.address_id, original.address_id)
    z = (f[a['features']].to_numpy(float) - np.asarray(a['center'])) / np.asarray(a['scale'])
    assert np.allclose(f[a['features']].mean().to_numpy(), a['center'], rtol=0, atol=1e-12)
    assert np.allclose(f[a['features']].std(ddof=0).to_numpy(), a['scale'], rtol=0, atol=1e-12)
    xr = encoding.block(f.source_region.astype(str), a['source_regions'], True)
    xy = encoding.block(f.year, a['source_years'], False)
    X = sparse.hstack([sparse.csr_matrix(z), xr, xy], format='csr')
    penalty = np.r_[np.ones(len(a['features'])), np.zeros(xr.shape[1] + xy.shape[1])]
    assert np.array_equal(penalty, a['penalty'])
    coef = np.asarray(a['coef']); y = f.T0.to_numpy(float); off = np.log(f.offset.to_numpy(float))
    def evaluate(beta):
        root = np.exp((off + X @ beta) / 2)
        value = 2 * np.mean(root + y / root - 2 * np.sqrt(y)) + .5 * a['alpha'] * np.dot(penalty * beta, beta)
        gradient = np.asarray(X.T @ ((root - y / root) / len(y))).ravel() + a['alpha'] * penalty * beta
        return value, gradient
    value, gradient = evaluate(coef); mu = np.exp(off + X @ coef)
    independent = mean_tweedie_deviance(y, mu, power=1.5) / 2 + .5 * a['alpha'] * np.dot(penalty * coef, coef)
    assert abs(independent - a['objective']) < 1e-8 * (1 + abs(independent))
    assert np.abs(gradient).max() < 1e-4
    curvature = .5 * (np.sqrt(mu) + y / np.sqrt(mu)) / len(y)
    H = (X.T @ X.multiply(curvature[:, None])).toarray() + a['alpha'] * np.diag(penalty)
    rng = np.random.default_rng(754); errors = []; second_errors = []
    for _ in range(3):
        direction = rng.normal(size=len(coef)); direction /= np.linalg.norm(direction); h = 1e-4
        plus, gp = evaluate(coef + h * direction); minus, gm = evaluate(coef - h * direction)
        error = abs((plus - minus) / (2 * h) - float(gradient @ direction))
        second_error = float(np.max(abs((gp - gm) / (2 * h) - H @ direction)))
        assert error < 5e-6 and second_error < 5e-5; errors.append(error); second_errors.append(second_error)
    keys = f.source_region.astype(str).to_numpy() + '|' + f.year.astype(str).to_numpy()
    residual = (np.sqrt(mu) - y / np.sqrt(mu)) / len(y); U = []
    for key in sorted(set(keys)):
        mask = keys == key; U.append(np.asarray(X[mask].T @ residual[mask]).ravel())
    U = np.stack(U); assert len(U) == a['source_region_year_clusters'] == 48
    inverse = np.linalg.inv(H); cov = inverse @ (U.T @ U) @ inverse * len(U) / (len(U) - 1)
    k = len(a['features']); assert np.allclose(cov[:k, :k], a['weather_cluster_covariance'], rtol=1e-9, atol=1e-12)
    return {'line': line, 'family': family, 'rows': len(f), 'exact_source_row_cost_and_year_membership': True,
        'independent_sparse_encoding_and_sklearn_objective': True, 'max_abs_gradient': float(np.abs(gradient).max()),
        'finite_difference_errors': errors, 'hessian_direction_errors': second_errors, 'cluster_sandwich_reproduced': True,
        'source_clusters': len(U), 'new_fit_calls': 0}

def proxy_a1(p):
    path = b.OUT.parent.parent / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet'
    a1 = pd.read_parquet(path, columns=['row_id', 'A1']); assert len(a1) == 59202 and a1.row_id.is_unique
    f = p.loc[p.year.eq(2024)].merge(a1, on='row_id', validate='one_to_one'); assert len(f) == len(a1)
    for name in ['W1', 'W2', 'W3']: f[name] = np.nan
    for (line, held), idx in f.groupby(['line', 'fold'], observed=True).groups.items():
        t = f.loc[idx]; effects = {name: b.read(b.OUT / f'{name}_{line}.json') for name in ['anomalies', 'extended']}
        for name, family, strength in [('W1', 'anomalies', 1.), ('W2', 'extended', 1.), ('W3', 'extended', .5)]:
            pred, _ = b.apply(t, t.A1.to_numpy(float), effects[family], strength); f.loc[idx, name] = pred
    y = f.T0.to_numpy(float); weight = f.weight.to_numpy(float)
    den = 8 * (np.sqrt(np.dot(weight, y) * weight.sum()) - np.dot(weight, np.sqrt(y)))
    base = b.m.unit(y, f.A1.to_numpy(float))
    return {name: {'weighted2024_delta': float(np.dot(weight, base - b.m.unit(y, f[name].to_numpy(float))) / den),
        'proxy_only_not_corrected_A1_or_complete_F2': True, 'new_fits': 0} for name in ['W1', 'W2', 'W3']}

def validate():
    assert not OUT.exists(); plan = b.read(b.PLAN)
    assert b.read(b.OUT / 'registration.json')['plan_sha256'] == b.sha(b.PLAN)
    for path, digest in plan['sources'].items(): assert b.sha(ROOT / path) == digest, path
    price = b.read(b.OUT / 'price_report.json'); assert price['new_source_GLM_fits'] == 6 and price['new_C0_fits'] == 0
    p = pd.read_parquet(b.OUT / 'oof_2023_2024.parquet'); assert p.row_id.is_unique and len(p) == 109296
    OUT.mkdir(); schema = {'N3': 'N0', 'W1': 'Q1', 'W2': 'Q2', 'W3': 'Q3'}
    x = p[['T0', 'group_id', 'line', 'new_business', 'fold', 'year', *schema]].rename(columns=schema).copy()
    stats.OUT = OUT
    with threadpool_limits(limits=2):
        comparisons = stats.evaluate(x, plan); weighted = weighted_sensitivity(p, plan); proxy = proxy_a1(p)
    rename = {'Q1': 'W1', 'Q2': 'W2', 'Q3': 'W3'}; comparisons = {rename[k]: v for k, v in comparisons.items()}
    for name in ['segments.csv', 'folds.csv', 'years.csv']:
        f = pd.read_csv(OUT / name); f['model'] = f.model.map(rename); f.to_csv(OUT / name, index=False)
    for old, new in rename.items(): (OUT / f'influence_{new}.parquet').write_bytes((OUT / f'influence_{old}.parquet').read_bytes())
    for name in comparisons:
        comparisons[name]['additional_veto_checks'] = {'weighted_sensitivity_point_positive': weighted[name]['delta'] > 0,
            'original_A1_2024_proxy_not_deteriorated': proxy[name]['weighted2024_delta'] >= 0}
        comparisons[name]['all_exploratory_checks_pass'] = comparisons[name]['exploratory_pass'] and all(comparisons[name]['additional_veto_checks'].values())
    original = b.optimize.minimize
    b.optimize.minimize = lambda *a, **kw: (_ for _ in ()).throw(AssertionError('No optimizer in validation/replay'))
    mathematics_checks = []; replays = []
    try:
        with threadpool_limits(limits=2):
            for line in b.m.data.LINES:
                effects = {}
                for family in ['anomalies', 'extended']:
                    mathematics_checks.append(mathematics(line, family)); effects[family] = b.read(b.OUT / f'{family}_{line}.json')
                for held in range(5):
                    t = p.loc[p.line.eq(line) & p.fold.eq(held)].copy()
                    norms = b.read(b.OUT / f'normalizers_{line}_fold{held}.json')
                    for name, family, strength in [('W1', 'anomalies', 1.), ('W2', 'extended', 1.), ('W3', 'extended', .5)]:
                        pred, norm = b.apply(t, t.N3.to_numpy(float), effects[family], strength)
                        assert np.array_equal(pred, t[name].to_numpy(float)) and norm == norms[name]
                        bad, alt_norm = b.apply(t.assign(T0=-1e30, reserve=-1e30), t.N3.to_numpy(float), effects[family], strength)
                        assert np.array_equal(pred, bad) and alt_norm == norm
                    replays.append({'line': line, 'fold': held, 'rows': len(t), 'exact': True, 'held_payload_invariant': True,
                        'year_business_totals_preserved': True, 'new_fit_calls': 0})
    finally: b.optimize.minimize = original
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'scores': price['scores'],
        'reference': 'N3 research comparator, not complete F2/C1', 'comparisons': comparisons,
        'weighted2025_sensitivity': weighted, 'original_A1_2024_proxy': proxy,
        'source_mathematics': mathematics_checks, 'replays': replays,
        'weighted_primary_ESS_gate_still_failed': True, 'weighted_scores_not_independent_confirmation': True,
        'source_cluster_covariance_approximate_and_target_CI_conditional_on_source': True,
        'conditional_official_weather_not_prospective_quote_time': True, '2024_is_adaptive_development': True,
        'new_fits': 0, 'new_C0_fits': 0, 'new_test_predictions': 0, 'new_submissions': 0,
        'B00_preserved': True, 'all_alternatives_preserved': True, 'goal_achieved': False,
        'statistic_source': {'path': b.rel(Path(stats.__file__)), 'sha256': b.sha(Path(stats.__file__)), 'schema': schema},
        'code_sha256': b.sha(Path(__file__))}
    b.dump(OUT / 'report.json', result)
    print(json.dumps({'scores': price['scores'], 'comparisons': comparisons, 'weighted_sensitivity': weighted,
        'original_A1_2024_proxy': proxy, 'source_math_checks': len(mathematics_checks), 'exact_replays': len(replays),
        'new_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    validate()
