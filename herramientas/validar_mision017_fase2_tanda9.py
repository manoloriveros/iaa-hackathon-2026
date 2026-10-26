"""Verifica las quince adaptaciones de hojas y su validación agrupada sin entrenar."""
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

b = load('leaf9', R / 'herramientas/mision017_fase2_tanda9_hojas_v3.py')
stats = load('stats9', R / 'herramientas/validar_mision017_fase2_tanda3.py')
wstats = load('weighted9', R / 'herramientas/validar_mision017_fase2_tanda7.py')
import numpy as np
import pandas as pd
import lightgbm as lgb
from threadpoolctl import threadpool_limits

OUT = b.OUT / 'validation_v1'

def validate():
    assert not (OUT / 'report.json').exists(); OUT.mkdir(exist_ok=True)
    plan = b.read(b.PLAN); assert b.read(b.OUT / 'registration.json')['plan_sha256'] == b.sha(b.PLAN)
    for path, digest in plan['sources'].items(): assert b.sha(ROOT / path) == digest, path
    price = b.read(b.OUT / 'price_report.json'); assert price['new_leaf_refit_calls'] == 15
    p = pd.read_parquet(b.OUT / 'oof_2023_2024.parquet'); assert len(p) == 109296 and p.row_id.is_unique
    assert p.groupby('group_id').fold.nunique().max() == 1
    old = pd.read_parquet(b.CV / 'oof_2023_2024.parquet', columns=['row_id', 'N3', 'T0', 'fold', 'group_id'])
    aligned = p.merge(old, on='row_id', validate='one_to_one', suffixes=['', '_old'])
    for col in ['N3', 'T0', 'fold', 'group_id']: assert np.array_equal(aligned[col], aligned[col + '_old'])
    weights_path = b.BASE / 'estimando_cartera2025_v3/weights.parquet'
    p = p.merge(pd.read_parquet(weights_path, columns=['row_id', 'weight']), on='row_id', validate='one_to_one')
    original_refit = lgb.Booster.refit; original_train = lgb.train
    def reject(*args, **kwargs): raise AssertionError('No training/refit during validation')
    lgb.Booster.refit = reject; lgb.train = reject
    math_checks = []; replays = []; delta_frames = []
    a1path = b.BASE.parent / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet'
    a1 = pd.read_parquet(a1path, columns=['row_id', 'A1']); assert len(a1) == 59202
    proxy = p.loc[p.year.eq(2024)].merge(a1, on='row_id', validate='one_to_one')
    for name, _ in b.NAMES: proxy[name] = np.nan
    try:
        with threadpool_limits(limits=2):
            for line in ['motor', 'buildings', 'contents']:
                parent_path = b.PARENT / f'modelos/prod/T2b_{line}.txt'
                parent = lgb.Booster(model_file=str(parent_path)); parent_topology = b.topology(parent)
                features = pd.read_parquet(b.PARENT / f'features_{line}.parquet'); X = b.matrix.source_matrix(features, parent)
                raw_frame = pd.read_parquet(b.OUT / f'parent_raw_{line}.parquet'); assert np.array_equal(raw_frame.row_id, features.row_id)
                raw = raw_frame.raw.to_numpy(float)
                for held in range(5):
                    trace = b.read(b.OUT / f'trace_{line}_fold{held}.json'); path = b.OUT / f'model_{line}_fold{held}.txt'
                    assert b.sha(parent_path) == trace['parent_model_sha256'] and b.sha(path) == trace['output_model_sha256']
                    inp = pd.read_parquet(ROOT / trace['scope_input']); assert b.sha(ROOT / trace['scope_input']) == trace['scope_input_sha256']
                    assert np.array_equal(inp.row_id, features.row_id); tr = inp.fold.ne(held).to_numpy(); val = ~tr
                    assert b.digest(sorted(inp.loc[tr, 'row_id'])) == trace['training_row_ids_digest']
                    assert b.digest(sorted(set(inp.loc[tr, 'group_id']))) == trace['training_groups_digest']
                    assert not set(inp.loc[tr, 'group_id']).intersection(inp.loc[val, 'group_id'])
                    assert b.digest(inp.loc[tr, 'T0'].to_numpy(float).tolist()) == trace['training_label_digest']
                    init = np.log(inp.loc[tr, 'base_N3'].to_numpy(float)) - raw[tr]
                    assert b.digest(init.tolist()) == trace['init_score_digest']
                    fitted = lgb.Booster(model_file=str(path)); assert b.topology(fitted) == parent_topology
                    assert b.digest(parent_topology) == trace['topology_digest']
                    assert parent.params['objective'] == fitted.params['objective'] == 'tweedie'
                    assert parent.params['tweedie_variance_power'] == fitted.params['tweedie_variance_power'] == 1.5
                    assert parent.params['lambda_l2'] == fitted.params['lambda_l2']
                    checkpoint = OUT / f'math_{line}_fold{held}.json'
                    if checkpoint.exists(): math_check = b.read(checkpoint)
                    else:
                        outputs, training_score = b.independent_refit(parent, X.loc[tr], inp.loc[tr, 'T0'].to_numpy(float), init, b.DECAY)
                        error = max(abs(fitted.get_leaf_output(j, k) - value) for j, row in enumerate(outputs) for k, value in enumerate(row))
                        assert error < 2e-6, (line, held, error)
                        independent_score = init + fitted.predict(X.loc[tr], raw_score=True, num_threads=2)
                        assert np.allclose(training_score, independent_score, rtol=0, atol=1e-5)
                        math_check = {'line': line, 'fold': held, 'training_rows': int(tr.sum()),
                            'independent_sequential_gradient_hessian_leaf_replay': True, 'max_leaf_error': float(error),
                            'max_training_score_error': float(np.max(abs(training_score - independent_score))),
                            'training_label_float32_representation_explicit': True, 'topology_and_objective_unchanged': True,
                            'C0_scope_training_membership_reused': True, 'no_fit_calls': True}
                        b.dump(checkpoint, math_check)
                    math_checks.append(math_check)
                    new_raw = fitted.predict(X.loc[val], raw_score=True, num_threads=2); delta = new_raw - raw[val]
                    valid = p.set_index('row_id').loc[inp.loc[val, 'row_id']].reset_index()
                    assert np.array_equal(valid.row_id, inp.loc[val, 'row_id'])
                    saved_norms = b.read(b.OUT / f'normalizers_{line}_fold{held}.json')
                    for name, strength in b.NAMES:
                        base = valid.N3.to_numpy(float); predicted, norm = b.apply(valid, base, delta, strength)
                        assert np.array_equal(predicted, valid[name]) and norm == saved_norms[name]
                        poison, changed_norm = b.apply(valid.assign(T0=-1e30, reserve=-1e30), base, delta, strength)
                        assert np.array_equal(poison, predicted) and changed_norm == norm
                        # Algebraic implementation using annual-risk ratios and groupwise sums.
                        factor = np.exp(delta * strength); independent = base * factor
                        for (_, _), idx in valid.groupby(['year', 'new_business'], observed=True).groups.items():
                            idx = np.asarray(idx); independent[idx] *= base[idx].sum() / independent[idx].sum()
                        assert np.allclose(predicted, independent, rtol=2e-14, atol=1e-10)
                        zero, _ = b.apply(valid, base, np.zeros(len(base)), strength); assert np.array_equal(zero, base)
                    d = pd.DataFrame({'row_id': valid.row_id, 'raw_delta': delta}); delta_frames.append(d)
                    t = proxy.loc[proxy.line.eq(line) & proxy.fold.eq(held)].copy()
                    target_delta = t.row_id.map(d.set_index('row_id').raw_delta).to_numpy(float); assert np.isfinite(target_delta).all()
                    for name, strength in b.NAMES:
                        pred, _ = b.apply(t, t.A1.to_numpy(float), target_delta, strength); proxy.loc[t.index, name] = pred
                    replays.append({'line': line, 'fold': held, 'rows': len(valid), 'bit_exact_prediction_and_normalizers': True,
                        'held_label_and_reserve_payload_invariant': True, 'independent_overlay_algebra': True,
                        'zero_overlay_identity': True, 'held_group_exclusion': True, 'new_fits': 0})
            checkpoint = OUT / 'statistics.json'
            if checkpoint.exists(): result_stats = b.read(checkpoint)
            else:
                stats.OUT = OUT; wstats.OUT = OUT
                schema = {'N3': 'N0', 'L1': 'Q1', 'L2': 'Q2', 'L3': 'Q3'}
                x = p[['T0', 'group_id', 'line', 'new_business', 'fold', 'year', *schema]].rename(columns=schema).copy()
                comparison = stats.evaluate(x, plan)
                weighted = wstats.weighted_sensitivity(p.rename(columns={'L1': 'W1', 'L2': 'W2', 'L3': 'W3'}), plan)
                comparison = {'L' + k[1:]: v for k, v in comparison.items()}; weighted = {'L' + k[1:]: v for k, v in weighted.items()}
                y = proxy.T0.to_numpy(float); weight = proxy.weight.to_numpy(float)
                den = 8 * (np.sqrt(np.dot(weight, y) * weight.sum()) - np.dot(weight, np.sqrt(y)))
                baseline = b.matrix.unit(y, proxy.A1.to_numpy(float))
                a1checks = {name: {'weighted2024_delta': float(np.dot(weight, baseline - b.matrix.unit(y, proxy[name].to_numpy(float))) / den),
                    'proxy_only_not_corrected_A1_or_complete_F2': True} for name, _ in b.NAMES}
                for name in comparison:
                    comparison[name]['additional_veto_checks'] = {'weighted_sensitivity_point_positive': weighted[name]['delta'] > 0,
                        'original_A1_2024_proxy_not_deteriorated': a1checks[name]['weighted2024_delta'] >= 0}
                    comparison[name]['all_exploratory_checks_pass'] = comparison[name]['exploratory_pass'] and all(comparison[name]['additional_veto_checks'].values())
                for filename in ['segments.csv', 'folds.csv', 'years.csv']:
                    df = pd.read_csv(OUT / filename); df['model'] = df.model.map({'Q1': 'L1', 'Q2': 'L2', 'Q3': 'L3'}); df.to_csv(OUT / filename, index=False)
                result_stats = {'comparisons': comparison, 'weighted2025_sensitivity': weighted, 'original_A1_2024_proxy': a1checks}
                b.dump(checkpoint, result_stats)
    finally: lgb.Booster.refit = original_refit; lgb.train = original_train
    pd.concat(delta_frames, ignore_index=True).to_parquet(OUT / 'raw_deltas.parquet', index=False)
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'scores': price['scores'], **result_stats,
        'source_and_refit_mathematics': math_checks, 'replays': replays,
        'reference': 'N3 research comparator, not full C1/F2', 'frozen_tree_structure_source_author': 'Claude',
        'adaptation_and_validation_author': 'Codex', 'weighted2025_primary_ESS_gate_still_failed': True,
        'many_fixed_leaves_can_still_overfit': True, '2024_is_adaptive_development': True,
        'new_fits': 0, 'new_C0_fits': 0, 'new_test_prices': 0, 'new_submissions': 0,
        'B00_preserved': True, 'all_alternatives_preserved': True, 'goal_achieved': False,
        'oof_sha256': b.sha(b.OUT / 'oof_2023_2024.parquet'), 'code_sha256': b.sha(Path(__file__)),
        'statistics_code_sha256': b.sha(Path(stats.__file__)), 'weight_sha256': b.sha(weights_path)}
    b.dump(OUT / 'report.json', result)
    print(json.dumps({'scores': price['scores'], **result_stats, 'independent_refits_checked': len(math_checks),
        'exact_replays': len(replays), 'new_fits': 0, 'new_submissions': 0}))

if __name__ == '__main__':
    try: validate()
    except Exception as exc:
        OUT.mkdir(exist_ok=True); b.dump(OUT / ('failure_' + str(__import__('time').time_ns()) + '.json'),
            {'utc': datetime.now(timezone.utc).isoformat(), 'error': type(exc).__name__, 'message': str(exc), 'new_fit_calls': 0})
        raise
