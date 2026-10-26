"""Valida pendientes, flujo real y sensibilidad sin nuevos ajustes."""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

b = load('slope6', R / 'herramientas/mision017_fase2_tanda6_pendiente.py')
stats = load('stats3', R / 'herramientas/validar_mision017_fase2_tanda3.py')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits

OUT = b.OUT / 'validation_v1'

def mathematics(f, a):
    tr = f.loc[f.fold.ne(a['held_fold'])].copy()
    nb = tr.new_business.to_numpy(dtype=int)
    risk = np.log(tr.base_N3.to_numpy(float) / tr.e_cost_scope.to_numpy(float))
    weight = tr.base_N3.to_numpy(float)
    centers = {str(k): float(np.dot(risk[nb == k], weight[nb == k]) / weight[nb == k].sum()) for k in [0, 1]}
    assert all(abs(centers[k] - a['centers'][k]) < 1e-13 for k in centers)
    centered = risk - np.array([centers[str(k)] for k in nb])
    scale = float(np.sqrt(np.dot(centered ** 2, weight) / weight.sum()))
    assert abs(scale - a['scale']) < 1e-13
    # Use saved moments below so the independent matrix agrees at native precision.
    x = (risk - np.array([a['centers'][str(k)] for k in nb])) / a['scale']
    slopes = [x * (nb == k) for k in [0, 1]] if a['separate'] else [x]
    columns = list(slopes)
    for key in a['nuisance_keys']:
        year, business = (int(s) for s in key.split('|'))
        columns.append((tr.year.to_numpy() == year) & (nb == business))
    X = np.column_stack(columns).astype(float)
    penalty = np.r_[np.ones(len(slopes)), np.zeros(4)]
    assert np.array_equal(penalty, a['penalty'])
    coef = np.asarray(a['coef']); y = tr.T0.to_numpy(float); off = np.log(tr.base_N3.to_numpy(float))
    mu = np.exp(off + X @ coef)
    objective = mean_tweedie_deviance(y, mu, power=1.5) / 2 + .5 * a['alpha'] * np.dot(penalty * coef, coef)
    assert abs(objective - a['objective']) < 1e-9 * (1 + abs(objective))
    gradient = X.T @ ((np.sqrt(mu) - y / np.sqrt(mu)) / len(y)) + a['alpha'] * penalty * coef
    assert np.abs(gradient).max() < 1e-5
    def value(beta):
        root = np.exp((off + X @ beta) / 2)
        return float(2 * np.mean(root + y / root - 2 * np.sqrt(y)) + .5 * a['alpha'] * np.dot(penalty * beta, beta))
    rng = np.random.default_rng(753); errors = []
    for _ in range(3):
        direction = rng.normal(size=len(coef)); direction /= np.linalg.norm(direction); h = 1e-4
        error = abs((value(coef + h * direction) - value(coef - h * direction)) / (2 * h) - float(gradient @ direction))
        assert error < 5e-6; errors.append(error)
    return {'max_abs_gradient': float(np.abs(gradient).max()), 'finite_difference_errors': errors,
        'independent_matrix_moments_and_sklearn_objective': True, 'new_fit_calls': 0}

def replay_learning(f, a):
    # Exercise the real selection, centering, nuisance setup and objective. The
    # optimizer is replaced by the saved solution, so there is no new fitting.
    signatures = []
    def frozen_optimizer(fun, initial, **kwargs):
        coef = np.asarray(a['coef']); probes = [initial, coef, coef + .01, coef - .01]
        signature = {'initial': initial.tolist(), 'probes': []}
        for probe in probes:
            value, gradient = fun(probe)
            signature['probes'].append({'objective': value, 'gradient': gradient.tolist()})
        signatures.append(b.b.digest(signature))
        return SimpleNamespace(x=coef, success=True, nit=a['iterations'], message='Frozen solution replay, no optimizer fit')
    original = b.optimize.minimize; b.optimize.minimize = frozen_optimizer
    try:
        replay = b.fit(f, a['held_fold'], a['separate'])
        poisoned = f.copy(); poisoned.loc[poisoned.fold.eq(a['held_fold']), ['T0', 'reserve']] = -1e30
        adverse = b.fit(poisoned, a['held_fold'], a['separate'])
    finally:
        b.optimize.minimize = original
    assert b.b.digest(replay) == b.b.digest(adverse) == b.b.digest(a)
    assert len(signatures) == 2 and signatures[0] == signatures[1]
    return {'real_learning_flow_replayed': True, 'selection_moments_objectives_and_initialization_held_payload_invariant': True,
        'saved_solution_injected_not_refitted': True, 'new_fit_calls': 0}

def validate():
    assert not OUT.exists()
    plan = b.read(b.PLAN); assert b.read(b.OUT / 'registration.json')['plan_sha256'] == b.sha(b.PLAN)
    for path, digest in plan['sources'].items(): assert b.sha(ROOT / path) == digest, path
    price = b.read(b.OUT / 'price_report.json'); assert price['price_GLM_fits'] == 30 and price['new_C0_fits'] == 0
    p = pd.read_parquet(b.OUT / 'oof_2023_2024.parquet'); assert len(p) == 109296 and p.row_id.is_unique
    OUT.mkdir(); schema = {'base_N3': 'N0', 'T1': 'Q1', 'T2': 'Q2', 'T3': 'Q3'}
    x = p[['T0', 'group_id', 'line', 'new_business', 'fold', 'year', *schema]].rename(columns=schema).copy()
    stats.OUT = OUT
    with threadpool_limits(limits=2): comparisons = stats.evaluate(x, plan)
    rename = {'Q1': 'T1', 'Q2': 'T2', 'Q3': 'T3'}
    comparisons = {rename[k]: v for k, v in comparisons.items()}
    for name in ['segments.csv', 'folds.csv', 'years.csv']:
        f = pd.read_csv(OUT / name); f['model'] = f.model.map(rename); f.to_csv(OUT / name, index=False)
    for old, new in rename.items(): (OUT / f'influence_{new}.parquet').write_bytes((OUT / f'influence_{old}.parquet').read_bytes())
    checks = []; replay = []
    with threadpool_limits(limits=2):
        for scope in b.read(b.OUT / 'preflight.json')['scopes']:
            assert b.sha(ROOT / scope['input']) == scope['input_sha256']
            f = pd.read_parquet(ROOT / scope['input']); held = scope['held_fold']; line = scope['line']
            valid = f.loc[f.fold.eq(held)].copy(); saved = p.set_index('row_id').loc[valid.row_id]
            normalizers = b.read(b.OUT / f'normalizers_{line}_fold{held}.json')
            artifacts = {}
            for name in ['global', 'business']:
                a = b.read(b.OUT / f'{name}_{line}_fold{held}.json'); artifacts[name] = a
                checks.append({'line': line, 'fold': held, 'family': name, **mathematics(f, a), **replay_learning(f, a)})
            for name, family, strength in [('T1', 'global', 1.), ('T2', 'business', 1.), ('T3', 'business', .5)]:
                pred, norm = b.apply(valid, artifacts[family], strength)
                assert np.array_equal(pred, saved[name].to_numpy(float)) and norm == normalizers[name]
                adverse, norm2 = b.apply(valid.assign(T0=-1e30, reserve=-1e30), artifacts[family], strength)
                assert np.array_equal(pred, adverse) and norm == norm2
            replay.append({'line': line, 'fold': held, 'rows': len(valid), 'predictions_bit_exact': True,
                'held_payload_invariant': True, 'cell_totals_preserved': True, 'new_fit_calls': 0})
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'reference': 'N3 research comparator, not the complete F2',
        'scores': price['scores'], 'comparisons': comparisons, 'mathematics_and_real_learning_replays': checks,
        'replays': replay, 'metric_second_method': True, 'new_fits': 0, 'new_C0_fits': 0, 'new_submissions': 0,
        '2024_is_adaptive_development': True, 'CI_conditional_on_fixed_source': True,
        'source_master_reporting_case_reserve_uncertainty_not_fully_identified': True,
        'B00_preserved': True, 'all_alternatives_preserved': True, 'goal_achieved': False,
        'statistic_source': {'path': b.rel(Path(stats.__file__)), 'sha256': b.sha(Path(stats.__file__)), 'input_schema_mapping': schema},
        'code_sha256': b.sha(Path(__file__))}
    b.dump(OUT / 'report.json', result)
    print(json.dumps({'scores': price['scores'], 'comparisons': comparisons,
        'mathematics_and_learning_checks': len(checks), 'exact_replays': len(replay), 'new_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    validate()
