"""Verifica el objetivo conjunto, la exposición, los grupos y las comparaciones congeladas."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

b = load('joint11', R / 'herramientas/mision017_fase2_tanda11_conjunto.py')
stats = load('stats11', R / 'herramientas/validar_mision017_fase2_tanda3.py')
wstats = load('weighted11', R / 'herramientas/validar_mision017_fase2_tanda7.py')
encoding = load('encoding11', R / 'herramientas/validar_mision017_fase2_tanda4.py')
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits
t10 = b.b; scope = t10.b; unit = scope.b.unit
OUT = b.OUT / 'validation_v1'

def mathematics(train, a):
    y = train.T0.to_numpy(float); base = train.base_N3.to_numpy(float)
    assert b.digest(base.tolist()) == a['input_base_digest'] and b.digest(y.tolist()) == a['training_label_digest']
    blocks = [encoding.block(t10.key(train[name]), levels, False) for name, levels in zip(a['variables'], a['categories'])]
    ncat = sum(block.shape[1] for block in blocks); assert ncat == a['cat_dimensions']
    values = np.array([f'{int(y)}|{int(nb)}' for y, nb in zip(train.year, train.new_business)])
    nuisance = np.column_stack([values == key for key in a['nuisance_keys']]).astype(float)
    X = sparse.hstack([*blocks, sparse.csr_matrix(nuisance)], format='csr')
    S = np.sqrt(base).sum(); npos = np.count_nonzero(y > 0); ridge = 300 / npos
    assert S == a['baseline_Fisher_mass'] and npos == a['positive_training_periods'] and ridge == a['ridge_normalized']
    penalty = np.r_[np.full(ncat, ridge), np.zeros(4)]; assert np.array_equal(penalty, a['penalty'])
    coef = np.asarray(a['coef']); off = np.log(base)
    def objective(beta):
        mu = np.exp(off + X @ beta); root = np.sqrt(mu)
        value = .5 * unit(y, mu).sum() / S + .5 * np.dot(penalty * beta, beta)
        grad = np.asarray(X.T @ ((root - y / root) / S)).ravel() + penalty * beta
        return float(value), grad
    value, grad = objective(coef); mu = np.exp(off + X @ coef)
    independent = .5 * mean_tweedie_deviance(y, mu, power=1.5) * len(y) / S + .5 * np.dot(penalty * coef, coef)
    assert abs(value - independent) < 1e-10 and abs(value - a['objective']) < 1e-10
    assert abs(grad).max() < 1e-6
    curvature = .5 * (np.sqrt(mu) + y / np.sqrt(mu)) / S
    H = (X.T @ X.multiply(curvature[:, None])).toarray() + np.diag(penalty)
    eigen = np.linalg.eigvalsh(H); assert eigen.min() > 0 and np.isclose(eigen.min(), a['hessian_min_eigenvalue'], rtol=1e-10, atol=1e-12)
    rng = np.random.default_rng(711); err1 = []; err2 = []
    for _ in range(3):
        direction = rng.normal(size=len(coef)); direction /= np.linalg.norm(direction); h = 1e-4
        vp, gp = objective(coef + h * direction); vm, gm = objective(coef - h * direction)
        first = abs((vp - vm) / (2 * h) - grad @ direction); second = np.max(abs((gp - gm) / (2 * h) - H @ direction))
        assert first < 1e-6 and second < 1e-6; err1.append(float(first)); err2.append(float(second))
    return {'line': a['line'], 'fold': a['held_fold'], 'family': a['family'], 'training_rows': len(train),
        'independent_full_category_encoding': True, 'sklearn_loss_objective_checked': True,
        'K300_Fisher_penalty_and_nuisance_exclusion_checked': True, 'max_abs_gradient': float(abs(grad).max()),
        'minimum_Hessian_eigenvalue': float(eigen.min()), 'gradient_finite_difference_errors': err1,
        'Hessian_direction_errors': err2, 'new_fit_calls': 0}

def validate():
    assert not (OUT / 'report.json').exists(); OUT.mkdir(exist_ok=True)
    plan = b.read(b.PLAN); assert b.read(b.OUT / 'registration.json')['plan_sha256'] == b.sha(b.PLAN)
    for path, value in plan['sources'].items(): assert b.sha(ROOT / path) == value, path
    price = b.read(b.OUT / 'price_report.json'); assert price['new_joint_GLM_fits'] == 20
    p = pd.read_parquet(b.OUT / 'oof_2023_2024.parquet'); assert len(p) == 109296 and p.row_id.is_unique
    assert p.groupby('group_id').fold.nunique().max() == 1
    sequential = pd.read_parquet(t10.OUT / 'oof_2023_2024.parquet', columns=['row_id', 'N3', 'T0', 'G1', 'G2', 'G3'])
    p = p.merge(sequential, on='row_id', validate='one_to_one', suffixes=['', '_old'])
    for col in ['N3', 'T0']: assert np.array_equal(p[col], p[col + '_old'])
    weight_path = t10.BASE / 'estimando_cartera2025_v3/weights.parquet'
    p = p.merge(pd.read_parquet(weight_path, columns=['row_id', 'weight']), on='row_id', validate='one_to_one')
    a1path = t10.BASE.parent / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet'
    proxy = p.loc[p.year.eq(2024)].merge(pd.read_parquet(a1path, columns=['row_id', 'A1']), on='row_id', validate='one_to_one')
    assert len(proxy) == 59202
    for name in b.NAMES: proxy[name] = proxy.A1.to_numpy(float)
    saved_optimizer = b.optimize.minimize
    def reject(*args, **kwargs): raise AssertionError('No optimization during validation')
    b.optimize.minimize = reject; math_checks = []; replays = []; coefficients = []
    try:
        with threadpool_limits(limits=2):
            for line in b.FAMILIES:
                cov = pd.read_parquet(t10.OUT / f'covariates_{line}.parquet').set_index('row_id')
                for held in range(5):
                    f = pd.read_parquet(scope.OUT / f'inputs_{line}_fold{held}.parquet')
                    for col in ['gender', 'works_from_home', 'marketing_segment']: f[col] = cov.loc[f.row_id, col].to_numpy()
                    mask = f.fold.ne(held); train = f.loc[mask]; valid = f.loc[~mask]
                    assert not set(train.group_id).intersection(valid.group_id)
                    c0 = b.read(t10.CV / f'learning_{line}_fold{held}.json')['artifact']['C0']
                    assert sorted(train.row_id) == c0['fit_row_ids']
                    target = p.set_index('row_id').loc[valid.row_id]; saved_norms = b.read(b.OUT / f'normalizers_{line}_fold{held}.json')
                    q = proxy.loc[proxy.line.eq(line) & proxy.fold.eq(held)].copy()
                    for col in ['gender', 'works_from_home', 'marketing_segment']: q[col] = cov.loc[q.row_id, col].to_numpy()
                    for family in b.FAMILIES[line]:
                        a = b.read(b.OUT / f'model_{line}_fold{held}_{family}.json')
                        assert b.digest(sorted(train.row_id)) == a['training_row_ids_digest']
                        assert b.digest(sorted(set(train.group_id))) == a['training_groups_digest']
                        math_checks.append(mathematics(train, a))
                        prediction, norm = b.apply(valid, valid.base_N3.to_numpy(float), a); assert norm == saved_norms[family]
                        poison, n2 = b.apply(valid.assign(T0=-1e30, reserve=-1e30), valid.base_N3.to_numpy(float), a)
                        assert np.array_equal(prediction, poison) and norm == n2
                        assert np.array_equal(prediction, target[family].to_numpy(float))
                        qpred, _ = b.apply(q, q.A1.to_numpy(float), a)
                        mapped = [family] if line == 'contents' else b.NAMES
                        for name in mapped:
                            assert np.array_equal(prediction, target[name].to_numpy(float)); proxy.loc[q.index, name] = qpred
                        offset = 0
                        for variable, levels in zip(a['variables'], a['categories']):
                            for level, value in zip(levels, a['coef'][offset:offset + len(levels)]):
                                coefficients.append({'line': line, 'family': family, 'fold': held, 'variable': variable,
                                    'level': level, 'log_effect': value, 'factor': float(np.exp(value))})
                            offset += len(levels)
                    replays.append({'line': line, 'fold': held, 'held_rows': len(valid), 'C0_training_group_exclusion': True,
                        'exact_prediction_and_normalizer_replay': True, 'held_cost_and_reserve_invariant': True,
                        'source_levels_not_transferred': True, 'new_fit_calls': 0})
            stats.OUT = OUT; wstats.OUT = OUT
            schema = {'N3': 'N0', 'J1': 'Q1', 'J2': 'Q2', 'J3': 'Q3'}
            x = p[['T0', 'group_id', 'line', 'new_business', 'fold', 'year', *schema]].rename(columns=schema).copy()
            comparisons = stats.evaluate(x, plan)
            weighted = wstats.weighted_sensitivity(p.rename(columns={'J1': 'W1', 'J2': 'W2', 'J3': 'W3'}), plan)
            comparisons = {'J' + k[1:]: v for k, v in comparisons.items()}; weighted = {'J' + k[1:]: v for k, v in weighted.items()}
            y = proxy.T0.to_numpy(float); weights = proxy.weight.to_numpy(float)
            den_proxy = 8 * (np.sqrt(np.dot(weights, y) * weights.sum()) - np.dot(weights, np.sqrt(y)))
            base_proxy = unit(y, proxy.A1.to_numpy(float))
            proxies = {name: {'weighted2024_delta': float(np.dot(weights, base_proxy - unit(y, proxy[name].to_numpy(float))) / den_proxy),
                'proxy_only_not_corrected_A1_or_complete_C1_F2': True} for name in b.NAMES}
            yy = p.T0.to_numpy(float); null = stats.null(yy)
            matched = {name: float(np.sum(unit(yy, p['G' + name[1:]].to_numpy(float)) - unit(yy, p[name].to_numpy(float))) / null) for name in b.NAMES}
            for name, v in comparisons.items():
                v['additional_veto_checks'] = {'weighted_sensitivity_point_positive': weighted[name]['delta'] > 0,
                    'original_A1_2024_proxy_not_deteriorated': proxies[name]['weighted2024_delta'] >= 0,
                    'matching_sequential_not_deteriorated': matched[name] >= 0}
                v['all_exploratory_checks_pass'] = v['exploratory_pass'] and all(v['additional_veto_checks'].values())
            for filename in ['segments.csv', 'folds.csv', 'years.csv']:
                f = pd.read_csv(OUT / filename); f['model'] = f.model.map({'Q1': 'J1', 'Q2': 'J2', 'Q3': 'J3'}); f.to_csv(OUT / filename, index=False)
    finally: b.optimize.minimize = saved_optimizer
    pd.DataFrame(coefficients).to_csv(OUT / 'coefficients_by_fold.csv', index=False)
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'scores': price['scores'], 'comparisons': comparisons,
        'weighted2025_sensitivity': weighted, 'original_A1_2024_proxy': proxies, 'matched_sequential_delta': matched,
        'joint_GLM_mathematics': math_checks, 'replays': replays, 'reference': 'N3 research comparator, not full C1/F2',
        'Fisher_K_equivalence_approximate_not_proof_of_optimal_prior': True,
        'weighted2025_primary_ESS_gate_still_failed': True, '2024_is_adaptive_development': True,
        'new_fits': 0, 'new_C0_fits': 0, 'new_test_predictions': 0, 'new_submissions': 0,
        'B00_preserved': True, 'all_alternatives_preserved': True, 'goal_achieved': False,
        'code_sha256': b.sha(Path(__file__)), 'OOF_sha256': b.sha(b.OUT / 'oof_2023_2024.parquet')}
    b.dump(OUT / 'report.json', result)
    print(json.dumps({'scores': price['scores'], 'comparisons': comparisons, 'matched_sequential_delta': matched,
        'weighted2025_sensitivity': weighted, 'original_A1_proxy': proxies, 'joint_math_checks': len(math_checks),
        'exact_scope_replays': len(replays), 'new_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    try: validate()
    except Exception as exc:
        OUT.mkdir(exist_ok=True); b.dump(OUT / ('failure_' + str(__import__('time').time_ns()) + '.json'),
            {'utc': datetime.now(timezone.utc).isoformat(), 'error': type(exc).__name__, 'message': str(exc), 'new_fits': 0})
        raise
