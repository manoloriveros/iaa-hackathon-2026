"""Momentos independientes y replay de etapas residuales, sin nuevas estimaciones."""
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

b = load('factor10', R / 'herramientas/mision017_fase2_tanda10_factores.py')
stats = load('stats10', R / 'herramientas/validar_mision017_fase2_tanda3.py')
wstats = load('weighted10', R / 'herramientas/validar_mision017_fase2_tanda7.py')
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits
OUT = b.OUT / 'validation_v1'
unit = b.b.b.unit

def moment_check(f, base, a):
    assert b.digest(base.tolist()) == a['input_base_digest']
    assert b.digest(f.T0.to_numpy(float).tolist()) == a['training_label_digest']
    assert b.digest(sorted(f.row_id)) == a['training_row_ids_digest']
    assert b.digest(sorted(set(f.group_id))) == a['training_groups_digest']
    y = f.T0.to_numpy(float); adjusted = base.copy(); maximum_nuisance_error = 0.
    for year in [2023, 2024]:
        for nb in [0, 1]:
            mask = f.year.eq(year).to_numpy() & (f.new_business.to_numpy(dtype=int) == nb)
            root = np.sqrt(base[mask]); predicted_sum = root.sum(); weighted_observed = np.dot(y[mask], np.reciprocal(root))
            k = weighted_observed / predicted_sum; saved = a['nuisance_year_business'][f'{year}|{nb}']
            assert np.isclose(k, saved, rtol=1e-14, atol=1e-14)
            derivative = np.sqrt(k) * predicted_sum - weighted_observed / np.sqrt(k)
            maximum_nuisance_error = max(maximum_nuisance_error, abs(float(derivative)) / max(1., predicted_sum))
            assert maximum_nuisance_error < 1e-12
            adjusted[mask] *= saved
    labels = b.key(f[a['variable']]); errors = []; factors = {}
    for label in sorted(set(labels)):
        mask = labels == label; n = int(np.count_nonzero(y[mask])); assert n == a['positive_period_counts'][label]
        if n == 0:
            assert a['raw_factors'][label] is None and a['factors'][label] == 1.; factors[label] = 1.; continue
        root = np.sqrt(adjusted[mask]); observed = np.dot(y[mask], np.reciprocal(root)); expected = root.sum()
        optimum = observed / expected; assert np.isclose(optimum, a['raw_factors'][label], rtol=1e-14, atol=1e-14)
        derivative = np.sqrt(optimum) * expected - observed / np.sqrt(optimum)
        error = float(abs(derivative) / max(1., expected)); assert error < 1e-12; errors.append(error)
        estimate = float(np.exp(n / (n + 300.) * np.log(optimum))); factors[label] = estimate
        assert np.isclose(estimate, a['factors'][label], rtol=1e-14, atol=1e-14)
        loss = mean_tweedie_deviance(y[mask], adjusted[mask] * optimum, power=1.5)
        assert np.isclose(loss, unit(y[mask], adjusted[mask] * optimum).mean(), rtol=1e-12, atol=1e-9)
        for perturb in [np.exp(-.01), np.exp(.01)]:
            assert mean_tweedie_deviance(y[mask], adjusted[mask] * optimum * perturb, power=1.5) >= loss - 1e-9
        assert unit(y[mask], adjusted[mask] * estimate).sum() <= unit(y[mask], adjusted[mask]).sum() + 1e-6
    return {'variable': a['variable'], 'factor_parameters': len(factors), 'nuisance_levels': 4,
        'training_rows': len(f), 'independent_sufficient_statistics': True, 'raw_MLE_derivative_and_loss_checked': True,
        'shrinkage_formula_checked': True, 'max_relative_nuisance_derivative': maximum_nuisance_error,
        'max_relative_factor_derivative': max(errors, default=0.), 'new_factor_estimates': 0}

def predict_stages(f, base, stages):
    predictions = {}; m = base.copy(); norms = {}
    for step, a in enumerate(stages):
        m, n = b.apply_stage(f, m, a); predictions[b.NAMES[step]] = m.copy(); norms[a['variable']] = n
    for name in b.NAMES:
        if name not in predictions: predictions[name] = m.copy()
    return predictions, norms

def validate():
    assert not (OUT / 'report.json').exists(); OUT.mkdir(exist_ok=True)
    plan = b.read(b.PLAN); assert b.read(b.OUT / 'registration.json')['plan_sha256'] == b.sha(b.PLAN)
    for path, value in plan['sources'].items(): assert b.sha(ROOT / path) == value, path
    price = b.read(b.OUT / 'price_report.json'); assert price['closed_form_stage_learning_calls'] == 20
    p = pd.read_parquet(b.OUT / 'oof_2023_2024.parquet'); assert len(p) == 109296 and p.row_id.is_unique
    assert p.groupby('group_id').fold.nunique().max() == 1
    old = pd.read_parquet(b.CV / 'oof_2023_2024.parquet', columns=['row_id', 'T0', 'N3', 'fold', 'group_id'])
    aligned = p.merge(old, on='row_id', validate='one_to_one', suffixes=['', '_old'])
    for col in ['T0', 'N3', 'fold', 'group_id']: assert np.array_equal(aligned[col], aligned[col + '_old'])
    assert all(np.array_equal(p.loc[p.line.eq('buildings'), name], p.loc[p.line.eq('buildings'), 'N3']) for name in b.NAMES)
    weight_path = b.BASE / 'estimando_cartera2025_v3/weights.parquet'
    p = p.merge(pd.read_parquet(weight_path, columns=['row_id', 'weight']), on='row_id', validate='one_to_one')
    a1path = b.BASE.parent / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet'
    proxy = p.loc[p.year.eq(2024)].merge(pd.read_parquet(a1path, columns=['row_id', 'A1']), on='row_id', validate='one_to_one')
    assert len(proxy) == 59202
    for name in b.NAMES: proxy[name] = proxy.A1.to_numpy(float)
    original = b.fit_stage
    def reject(*args, **kwargs): raise AssertionError('No factor learning during validation/replay')
    b.fit_stage = reject; math_checks = []; replays = []; parameter_rows = []
    try:
        with threadpool_limits(limits=2):
            for line in ['motor', 'contents']:
                cov = pd.read_parquet(b.OUT / f'covariates_{line}.parquet').set_index('row_id')
                for held in range(5):
                    f = pd.read_parquet(b.b.OUT / f'inputs_{line}_fold{held}.parquet')
                    for col in ['gender', 'works_from_home', 'marketing_segment']: f[col] = cov.loc[f.row_id, col].to_numpy()
                    a = b.read(b.OUT / f'learning_{line}_fold{held}.json'); mask = f.fold.ne(held).to_numpy()
                    train = f.loc[mask]; valid = f.loc[~mask]; base = train.base_N3.to_numpy(float)
                    assert b.digest(sorted(train.row_id)) == a['training_row_ids_digest']
                    assert not set(train.group_id).intersection(valid.group_id)
                    c0 = b.read(b.CV / f'learning_{line}_fold{held}.json')['artifact']['C0']
                    assert sorted(train.row_id) == c0['fit_row_ids']
                    for stage in a['stages']:
                        check = moment_check(train, base, stage); math_checks.append({'line': line, 'fold': held, **check})
                        base, norm = b.apply_stage(train, base, stage); assert norm == a['training_normalizers'][stage['variable']]
                        parameter_rows += [{'line': line, 'fold': held, 'variable': stage['variable'], 'level': level,
                            'factor': value, 'positive_periods': stage['positive_period_counts'][level]} for level, value in stage['factors'].items()]
                    result, norms = predict_stages(valid, valid.base_N3.to_numpy(float), a['stages'])
                    target = p.set_index('row_id').loc[valid.row_id]
                    assert norms == a['held_normalizers']
                    for name in b.NAMES: assert np.array_equal(result[name], target[name].to_numpy(float))
                    poison, poison_norms = predict_stages(valid.assign(T0=-1e30, reserve=-1e30), valid.base_N3.to_numpy(float), a['stages'])
                    assert all(np.array_equal(poison[name], result[name]) for name in b.NAMES) and poison_norms == norms
                    q = proxy.loc[proxy.line.eq(line) & proxy.fold.eq(held)].copy()
                    for col in ['gender', 'works_from_home', 'marketing_segment']: q[col] = cov.loc[q.row_id, col].to_numpy()
                    predictions, _ = predict_stages(q, q.A1.to_numpy(float), a['stages'])
                    for name in b.NAMES: proxy.loc[q.index, name] = predictions[name]
                    replays.append({'line': line, 'fold': held, 'held_rows': len(valid), 'training_rows': len(train),
                        'C0_group_exclusion_checked': True, 'prediction_and_normalisers_bit_exact': True,
                        'held_cost_and_reserve_invariant': True, 'year_business_totals_preserved': True, 'new_estimates': 0})
            checkpoint = OUT / 'statistics.json'
            if checkpoint.exists(): result_stats = b.read(checkpoint)
            else:
                stats.OUT = OUT; wstats.OUT = OUT
                schema = {'N3': 'N0', 'G1': 'Q1', 'G2': 'Q2', 'G3': 'Q3'}
                x = p[['T0', 'group_id', 'line', 'new_business', 'fold', 'year', *schema]].rename(columns=schema).copy()
                comparisons = stats.evaluate(x, plan)
                weighted = wstats.weighted_sensitivity(p.rename(columns={'G1': 'W1', 'G2': 'W2', 'G3': 'W3'}), plan)
                comparisons = {'G' + key[1:]: value for key, value in comparisons.items()}
                weighted = {'G' + key[1:]: value for key, value in weighted.items()}
                y = proxy.T0.to_numpy(float); weight = proxy.weight.to_numpy(float)
                den = 8 * (np.sqrt(np.dot(weight, y) * weight.sum()) - np.dot(weight, np.sqrt(y)))
                baseline = unit(y, proxy.A1.to_numpy(float))
                a1checks = {name: {'weighted2024_delta': float(np.dot(weight, baseline - unit(y, proxy[name].to_numpy(float))) / den),
                    'proxy_only_not_corrected_A1_or_complete_C1_F2': True} for name in b.NAMES}
                for name, v in comparisons.items():
                    v['additional_veto_checks'] = {'weighted_sensitivity_point_positive': weighted[name]['delta'] > 0,
                        'original_A1_2024_proxy_not_deteriorated': a1checks[name]['weighted2024_delta'] >= 0}
                    v['all_exploratory_checks_pass'] = v['exploratory_pass'] and all(v['additional_veto_checks'].values())
                for filename in ['segments.csv', 'folds.csv', 'years.csv']:
                    f = pd.read_csv(OUT / filename); f['model'] = f.model.map({'Q1': 'G1', 'Q2': 'G2', 'Q3': 'G3'}); f.to_csv(OUT / filename, index=False)
                result_stats = {'comparisons': comparisons, 'weighted2025_sensitivity': weighted, 'original_A1_2024_proxy': a1checks}
                b.dump(checkpoint, result_stats)
    finally: b.fit_stage = original
    params = pd.DataFrame(parameter_rows); params.to_csv(OUT / 'factor_parameters_by_fold.csv', index=False)
    variation = params.groupby(['line', 'variable', 'level'], observed=True).agg(min_factor=('factor', 'min'),
        max_factor=('factor', 'max'), min_positive_periods=('positive_periods', 'min')).reset_index()
    variation.to_csv(OUT / 'factor_variation.csv', index=False)
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'scores': price['scores'], **result_stats,
        'closed_form_mathematics': math_checks, 'replays': replays, 'buildings_predictions_unchanged': True,
        'factor_parameters': len(params), 'source_of_variable_hypotheses': 'Received F3c evidence, recipe Claude; own scope/implementation/validation Codex',
        'reference': 'N3 research comparator, not complete C1/F2 or replication of F3c learning',
        'weighted2025_primary_ESS_gate_still_failed': True, '2024_is_adaptive_development': True,
        'prior_variable_selection_adaptive': True, 'masters_undated_not_prospective_vintage_proof': True,
        'new_factor_estimates': 0, 'new_iterative_model_fits': 0, 'new_C0_fits': 0, 'new_test_predictions': 0, 'new_submissions': 0,
        'B00_preserved': True, 'all_alternatives_preserved': True, 'goal_achieved': False,
        'oof_sha256': b.sha(b.OUT / 'oof_2023_2024.parquet'), 'code_sha256': b.sha(Path(__file__)),
        'statistics_code_sha256': b.sha(Path(stats.__file__)), 'weights_sha256': b.sha(weight_path)}
    b.dump(OUT / 'report.json', result)
    print(json.dumps({'scores': price['scores'], **result_stats, 'closed_stage_math_checks': len(math_checks),
        'scope_replays': len(replays), 'new_estimates': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    try: validate()
    except Exception as exc:
        OUT.mkdir(exist_ok=True); b.dump(OUT / ('failure_' + str(__import__('time').time_ns()) + '.json'),
            {'utc': datetime.now(timezone.utc).isoformat(), 'error': type(exc).__name__, 'message': str(exc), 'new_estimates': 0})
        raise
