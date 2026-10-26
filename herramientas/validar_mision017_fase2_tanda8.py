"""Validación finita de Poisson por peril: estadísticas, matemática y flujo sin ajuste."""
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

resume = load('resume8', R / 'herramientas/mision017_fase2_tanda8_reanudar_v2.py')
b = resume.b
stats = load('stats8', R / 'herramientas/validar_mision017_fase2_tanda3.py')
wstats = load('weighted8', R / 'herramientas/validar_mision017_fase2_tanda7.py')
encoding = load('encoding8', R / 'herramientas/validar_mision017_fase2_tanda4.py')
import numpy as np
import pandas as pd
from scipy import sparse, special
from sklearn.metrics import mean_poisson_deviance
from threadpoolctl import threadpool_limits

OUT = resume.OUT / 'validation_v1'
NAMES = [('P1', 1.), ('P2', .5), ('P3', .25)]

def math_check(f, a):
    n0 = f['N_' + a['peril']].to_numpy(float); e0 = f['E_count_rkm_' + a['peril']].to_numpy(float)
    assert not ((n0 > 0) & (e0 <= 0)).any()
    active = e0 > 0; t = f.loc[active]; y = n0[active]; e = e0[active]; events = y.sum()
    assert len(t) == a['training_rows'] and int(events) == a['events']
    weather = t[a['weather']].to_numpy(float); nuisance = t[b.NUM].to_numpy(float)
    for data, prefix in [(weather, 'weather'), (nuisance, 'nuisance')]:
        assert np.allclose(data.mean(axis=0), a[prefix + '_center'], rtol=0, atol=1e-12)
        assert np.allclose(data.std(axis=0), a[prefix + '_scale'], rtol=0, atol=1e-12)
    w = (weather - a['weather_center']) / a['weather_scale']
    n = (nuisance - a['nuisance_center']) / a['nuisance_scale']
    cats = [encoding.block(t[col].astype('string').fillna('__MISSING__').astype(str), levels, True)
            for col, levels in zip(b.CATS, a['categories'])]
    year = encoding.block(t.year, a['years'], False)
    X = sparse.hstack([sparse.csr_matrix(w), sparse.csr_matrix(n), *cats, year], format='csr')
    precision = np.r_[np.full(w.shape[1], 25.), np.full(n.shape[1] + sum(c.shape[1] for c in cats), 4.), np.zeros(year.shape[1])]
    assert np.array_equal(precision, a['precision'])
    coef = np.asarray(a['coef']); offset = np.log(e); constant = np.sum(special.xlogy(y, y) - y)
    def objective(beta):
        eta = offset + X @ beta; mu = np.exp(eta)
        value = (np.sum(mu - y * eta) + constant + .5 * np.dot(precision * beta, beta)) / events
        gradient = (np.asarray(X.T @ (mu - y)).ravel() + precision * beta) / events
        return value, gradient
    value, gradient = objective(coef); mu = np.exp(offset + X @ coef)
    independent = .5 * mean_poisson_deviance(y, mu) * len(y) / events + .5 * np.dot(precision * coef, coef) / events
    assert abs(value - independent) < 1e-10 and abs(value - a['objective']) < 1e-10
    assert np.abs(gradient).max() < 1e-6
    H = (X.T @ X.multiply((mu / events)[:, None])).toarray() + np.diag(precision / events)
    rng = np.random.default_rng(1268); first = []; second = []
    for _ in range(3):
        direction = rng.normal(size=len(coef)); direction /= np.linalg.norm(direction); h = 1e-4
        plus, gp = objective(coef + h * direction); minus, gm = objective(coef - h * direction)
        err1 = abs((plus - minus) / (2 * h) - gradient @ direction)
        err2 = np.max(abs((gp - gm) / (2 * h) - H @ direction))
        assert err1 < 1e-6 and err2 < 1e-6
        first.append(float(err1)); second.append(float(err2))
    keys = t.source_region.astype(str).to_numpy() + '|' + t.year.astype(str).to_numpy(); scores = []
    for key in sorted(set(keys)):
        mask = keys == key; scores.append(np.asarray(X[mask].T @ ((mu[mask] - y[mask]) / events)).ravel())
    U = np.stack(scores); assert len(U) == a['source_clusters'] == 48
    inverse = np.linalg.inv(H); cov = inverse @ (U.T @ U) @ inverse * len(U) / (len(U) - 1)
    nw = len(a['weather']); assert np.allclose(cov[:nw, :nw], a['weather_cluster_covariance'], rtol=1e-8, atol=1e-12)
    return {'line': a['line'], 'peril': a['peril'], 'active_rows': len(t), 'events': int(events),
        'independent_sparse_encoding_and_sklearn_objective': True, 'max_abs_gradient': float(abs(gradient).max()),
        'finite_difference_gradient_errors': first, 'hessian_errors': second,
        'cluster_covariance_reproduced': True, 'source_clusters': len(U), 'new_fits': 0}

def independent_apply(t, base, models, mixture, strength):
    neutral = 1 - sum(mixture[p] for p in models)
    factor = np.full(len(t), neutral)
    for peril, a in models.items():
        eta = sum(t[col].to_numpy(float) * strength * a['weather_coefficient'][col] / a['weather_scale'][i]
                  for i, col in enumerate(a['weather']))
        factor += mixture[peril] * np.exp(eta)
    out = np.empty(len(t))
    for (_, _), idx in t.reset_index(drop=True).groupby(['year', 'new_business'], observed=True).groups.items():
        ix = np.asarray(idx); out[ix] = base[ix] * factor[ix] * base[ix].sum() / np.dot(base[ix], factor[ix])
    return out

def proxy_a1(p):
    path = b.BASE.parent / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet'
    a1 = pd.read_parquet(path, columns=['row_id', 'A1']); assert len(a1) == 59202 and a1.row_id.is_unique
    f = p.loc[p.year.eq(2024)].merge(a1, on='row_id', validate='one_to_one'); assert len(f) == len(a1)
    for name, _ in NAMES: f[name] = np.nan
    for (line, held), idx in f.groupby(['line', 'fold'], observed=True).groups.items():
        t = f.loc[idx]; models = {peril: b.read(resume.OUT / f'{line}_{peril}.json') for peril in b.MAP[line]}
        mixture = b.read(b.m.CV / f'learning_{line}_fold{held}.json')['artifact']['C0']['mixture']
        for name, strength in NAMES:
            prediction, _ = b.apply(t, t.A1.to_numpy(float), models, mixture, strength); f.loc[idx, name] = prediction
    y = f.T0.to_numpy(float); weight = f.weight.to_numpy(float)
    den = 8 * (np.sqrt(np.dot(weight, y) * weight.sum()) - np.dot(weight, np.sqrt(y)))
    baseline = b.m.unit(y, f.A1.to_numpy(float))
    return {name: {'weighted2024_delta': float(np.dot(weight, baseline - b.m.unit(y, f[name].to_numpy(float))) / den),
        'proxy_only_not_corrected_A1_or_complete_F2': True, 'new_fits': 0} for name, _ in NAMES}

def validate():
    assert not (OUT / 'report.json').exists(); OUT.mkdir(exist_ok=True)
    plan = b.read(resume.PLAN); scientific = b.read(b.PLAN)
    assert b.read(resume.OUT / 'registration.json')['plan_sha256'] == b.sha(resume.PLAN)
    for path, digest in plan['sources'].items(): assert b.sha(ROOT / path) == digest, path
    price = b.read(resume.OUT / 'price_report.json'); assert price['source_unique_GLMs'] == 11 and price['source_GLM_attempts_total'] == 12
    p = pd.read_parquet(resume.OUT / 'oof_2023_2024.parquet'); original = pd.read_parquet(b.m.CV / 'oof_2023_2024.parquet')
    assert len(p) == 109296 and p.row_id.is_unique and p.groupby('group_id').fold.nunique().max() == 1
    merged = p.merge(original[['row_id', 'N3', 'T0', 'group_id', 'fold', 'year']], on='row_id', validate='one_to_one', suffixes=['', '_old'])
    for col in ['N3', 'T0', 'group_id', 'fold', 'year']: assert np.array_equal(merged[col], merged[col + '_old'])
    checkpoint = OUT / 'statistics.json'
    schema = {'N3': 'N0', 'P1': 'Q1', 'P2': 'Q2', 'P3': 'Q3'}
    original_optimizer = b.optimize.minimize
    def reject(*args, **kwargs): raise AssertionError('No optimizer during validation')
    b.optimize.minimize = reject
    try:
        with threadpool_limits(limits=2):
            if checkpoint.exists(): result_stats = b.read(checkpoint)
            else:
                stats.OUT = OUT; wstats.OUT = OUT
                x = p[['T0', 'group_id', 'line', 'new_business', 'fold', 'year', *schema]].rename(columns=schema).copy()
                comparisons = stats.evaluate(x, scientific)
                weighted = wstats.weighted_sensitivity(p.rename(columns={'P1': 'W1', 'P2': 'W2', 'P3': 'W3'}), scientific)
                proxy = proxy_a1(p); rename = {'Q1': 'P1', 'Q2': 'P2', 'Q3': 'P3'}
                comparisons = {rename[k]: v for k, v in comparisons.items()}; weighted = {'P' + k[1:]: v for k, v in weighted.items()}
                for name in ['segments.csv', 'folds.csv', 'years.csv']:
                    f = pd.read_csv(OUT / name); f['model'] = f.model.map(rename); f.to_csv(OUT / name, index=False)
                for old, new in rename.items(): (OUT / f'influence_{new}.parquet').write_bytes((OUT / f'influence_{old}.parquet').read_bytes())
                for name in comparisons:
                    comparisons[name]['additional_veto_checks'] = {'weighted_sensitivity_point_positive': weighted[name]['delta'] > 0,
                        'original_A1_2024_proxy_not_deteriorated': proxy[name]['weighted2024_delta'] >= 0}
                    comparisons[name]['all_exploratory_checks_pass'] = comparisons[name]['exploratory_pass'] and all(comparisons[name]['additional_veto_checks'].values())
                result_stats = {'comparisons': comparisons, 'weighted2025_sensitivity': weighted, 'original_A1_2024_proxy': proxy}
                b.dump(checkpoint, result_stats)
            math_checks = []; replays = []
            for line in b.MAP:
                f = pd.read_parquet(b.OUT / f'source_{line}.parquet'); digest = b.sha(b.OUT / f'source_{line}.parquet')
                assert f.market.eq('developed').all() and f.year.isin([2021, 2022, 2023, 2024]).all()
                models = {}
                for peril in b.MAP[line]:
                    a = b.read(resume.OUT / f'{line}_{peril}.json'); assert a['source_input_sha256'] == digest
                    math_path = OUT / f'math_{line}_{peril}.json'
                    if math_path.exists(): check = b.read(math_path)
                    else: check = math_check(f, a); b.dump(math_path, check)
                    math_checks.append(check); models[peril] = a
                del f
                for held in range(5):
                    t = p.loc[p.line.eq(line) & p.fold.eq(held)].copy()
                    saved = b.read(resume.OUT / f'normalizers_{line}_fold{held}.json'); parent = ROOT / saved['parent_C0']
                    assert b.sha(parent) == saved['parent_C0_sha256']
                    c0 = b.read(parent)['artifact']['C0']; train = p.loc[p.line.eq(line) & p.fold.ne(held)]
                    assert sorted(train.row_id) == c0['fit_row_ids']
                    assert not set(train.group_id).intersection(t.group_id)
                    for name, strength in NAMES:
                        base = t.N3.to_numpy(float); pred, norm = b.apply(t, base, models, c0['mixture'], strength)
                        assert np.array_equal(pred, t[name].to_numpy(float)) and norm == saved['normalizers'][name]
                        independent = independent_apply(t, base, models, c0['mixture'], strength)
                        assert np.allclose(pred, independent, rtol=2e-14, atol=1e-10)
                        poison, changed_norm = b.apply(t.assign(T0=-1e30, reserve=-1e30), base, models, c0['mixture'], strength)
                        assert np.array_equal(poison, pred) and changed_norm == norm
                        zero = t.copy()
                        for col in b.DELTA: zero[col] = 0.
                        identity, _ = b.apply(zero, base, models, c0['mixture'], strength); assert np.array_equal(identity, base)
                    replays.append({'line': line, 'fold': held, 'rows': len(t), 'exact': True, 'independent_algebra': True,
                        'held_labels_and_reserves_invariant': True, 'C0_training_groups_exclude_held': True,
                        'zero_weather_identity': True, 'year_business_totals_preserved': True, 'new_fit_calls': 0})
    finally: b.optimize.minimize = original_optimizer
    passing = [k for k, v in result_stats['comparisons'].items() if v['all_exploratory_checks_pass']]
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'scores': price['scores'], **result_stats,
        'source_mathematics': math_checks, 'replays': replays, 'source_unique_models': 11, 'real_GLM_attempts_including_v1_failure': 12,
        'two_completed_v1_models_reused_without_refit': True, 'conditional_stress_triggered': bool(passing),
        'conditional_stress_skip_reason': 'No candidate passes the preinscribed primary and veto checks' if not passing else None,
        'reference': 'N3 research benchmark, not full C1/F2', 'weighted_primary_ESS_gate_still_failed': True,
        'source_cluster_covariance_approximate_target_CI_conditional': True, '2024_is_adaptive_development': True,
        'official_weather_conditional_not_quote_time': True, 'full_ultimate_tail_not_identified': True,
        'new_fits': 0, 'new_C0_fits': 0, 'new_test_predictions': 0, 'new_submissions': 0,
        'B00_preserved': True, 'all_alternatives_preserved': True, 'goal_achieved': False,
        'input_oof_sha256': b.sha(resume.OUT / 'oof_2023_2024.parquet'), 'code_sha256': b.sha(Path(__file__)),
        'statistics_code_sha256': b.sha(Path(stats.__file__)), 'weighted_code_sha256': b.sha(Path(wstats.__file__))}
    b.dump(OUT / 'report.json', result)
    print(json.dumps({'scores': price['scores'], **result_stats, 'source_math_checks': len(math_checks), 'exact_replays': len(replays),
        'conditional_stress_triggered': bool(passing), 'new_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    try: validate()
    except Exception as exc:
        OUT.mkdir(exist_ok=True); b.dump(OUT / ('failure_' + str(__import__('time').time_ns()) + '.json'),
            {'utc': datetime.now(timezone.utc).isoformat(), 'error': type(exc).__name__, 'message': str(exc), 'no_fit_calls': True})
        raise
