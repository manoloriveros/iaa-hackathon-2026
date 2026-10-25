"""Evalúa una sola vez los tres brazos2023 con los criterios prerregistrados."""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
RUN = REPO / 'privado/semana2/desarrollo2023/b20_contraste_exploratorio_20261024_v2'
sys.path.insert(0, str(REPO / 'src'))
from semana2 import contraste_b20_exploratorio as core
np, pd, pq = core.np, core.pd, core.base.u.pq
u, KEY = core.base.u, core.KEY


def main():
    u.require(not (RUN / 'evaluation.json').exists(), 'Evaluación existente; no repetir.')
    plan = u.read(RUN / 'plan_execution.json')
    original = u.read(RUN / 'plan_preregistered.json')
    u.require(plan['acceptance'] == original['acceptance']
              and plan['preregistered_plan_sha256'] == u.sha(RUN / 'plan_preregistered.json'), 'Criterios alterados.')
    for source in plan['implementation_sources']:
        u.require(u.sha(ROOT / source['path']) == source['sha256'], 'Implementación congelada cambió.')
    work = u.read(RUN / 'training_completed.json')
    u.require(work['new_price_GLMs'] == 10 and work['new_reporting_fits'] == 60
              and work['new_slope_calibrations'] == 5 and work['new_intercept_values'] == 10, 'Presupuesto distinto.')
    all_rows = pq.read_table(RUN / 'contrast_oof_2023.parquet').to_pandas()
    arms = {arm: all_rows.loc[all_rows.model_id.eq(arm)].sort_values(KEY).reset_index(drop=True)
            for arm in ['raw', 'L', 'S']}
    raw, candidate = arms['raw'], arms['S']
    u.assert_2023(raw)
    technical = []
    def check(name, value, details=None):
        technical.append({'name': name, 'pass': bool(value), 'details': details})
    check('complete_arms', all(len(x) == 50094 and not x.duplicated(KEY).any() for x in arms.values()))
    for arm, frame in arms.items():
        check('identical_keys_target_C0_' + arm, frame[KEY].equals(raw[KEY]) and frame.T0.equals(raw.T0)
              and frame['e_cost_mix_1.0'].equals(raw['e_cost_mix_1.0']))
        check('strict2023_' + arm, frame.year.eq(2023).all())
        losses = u.unit_deviance(frame.T0, frame.prediction)
        check('stored_loss_' + arm, np.array_equal(losses, frame.unit_deviance.to_numpy()))
        independent = core.base.u.mean_tweedie_deviance(frame.T0, frame.prediction, power=1.5)
        check('sklearn_deviance_' + arm, np.isclose(losses.mean(), independent, rtol=1e-12, atol=1e-10))
    u.require(all(x['pass'] for x in technical), 'Fallo técnico antes de decidir.')
    acceptance = plan['acceptance']
    conditions = []
    def accept(name, value, observed, requirement):
        conditions.append({'name': name, 'pass': bool(value), 'observed': observed, 'requirement': requirement})
    summary = {arm: u.metrics(frame) for arm, frame in arms.items()}
    dSL = summary['S']['D2'] - summary['L']['D2']
    dSR = summary['S']['D2'] - summary['raw']['D2']
    accept('primary_S_minus_L', dSL >= acceptance['primary_global_delta_D2_S_minus_L_min'], dSL, '>=0.0005')
    accept('raw_anchor_guard', dSR >= acceptance['global_delta_D2_S_minus_rawB20_min'], dSR, '>=0')
    folds = []
    parameters = [u.read(RUN / 'calibration' / f'fold{k}.json') for k in range(5)]
    for k in range(5):
        m = {arm: u.metrics(frame.loc[frame.fold.eq(k)]) for arm, frame in arms.items()}
        folds.append({'fold': k, 'delta_S_L': m['S']['D2'] - m['L']['D2'],
                      'delta_S_raw': m['S']['D2'] - m['raw']['D2'],
                      'metrics': m, 'calibration': parameters[k]})
    positive = sum(x['delta_S_L'] >= 0 for x in folds)
    worst = min(x['delta_S_L'] for x in folds)
    accept('fold_agreement', positive >= acceptance['nonnegative_outer_fold_deltas_S_minus_L_min_count'], positive, '>=4of5')
    accept('worst_fold', worst >= acceptance['worst_outer_fold_delta_D2_S_minus_L_min'], worst, '>=-0.001')
    boundary = plan['calibration_numerics']['boundary_tolerance']
    slopes = [x['b_S'] for x in parameters]
    interior = sum(boundary < x < 1 - boundary for x in slopes)
    accept('interior_slopes', interior >= acceptance['strict_0_lt_b_lt_1_min_outer_scopes'], slopes, '>=4of5 strictly interior at1e-6')
    accept('no_zero_slope', all(x > boundary for x in slopes), slopes, 'no b at0')
    bands = pq.read_table(RUN / 'inputs_2023/bands.parquet').to_pandas()
    gap = {}
    for arm in ['L', 'S']:
        buildings = arms[arm].loc[arms[arm].line.eq('buildings')].merge(bands[KEY + ['band']], on=KEY, validate='one_to_one')
        ratios = {b: float(buildings.loc[buildings.band.eq(b), 'T0'].sum() /
                           buildings.loc[buildings.band.eq(b), 'prediction'].sum()) for b in [1, 5]}
        gap[arm] = {'AE_band1': ratios[1], 'AE_band5': ratios[5], 'G': float(np.log(ratios[1]) - np.log(ratios[5]))}
    gL, gS = gap['L']['G'], gap['S']['G']
    accept('tail_gap', gL > 0 and gS >= 0 and gS <= acceptance['tail_gap']['G_S_over_G_L_max'] * gL,
           gap, 'G_L>0,0<=G_S<=0.8*G_L; original bands unchanged')
    metadata = pq.read_table(RUN / 'inputs_2023/customer_metadata.parquet').to_pandas()
    u.require(len(metadata) == 50094 and not metadata.duplicated(KEY).any(), 'Metadatos de cliente incompletos.')
    enriched = raw.merge(metadata, on=KEY, validate='one_to_one')
    masks = {line: enriched.line.eq(line).to_numpy() for line in ['motor', 'buildings', 'contents']}
    masks.update(new_customer=enriched.x_customer_tenure_years.eq(0).to_numpy(),
        renewal=enriched.x_new_business.eq(0).to_numpy(),
        buildings_new=(enriched.line.eq('buildings') & enriched.x_new_business.eq(1)).to_numpy(),
        buildings_renewal=(enriched.line.eq('buildings') & enriched.x_new_business.eq(0)).to_numpy())
    segments = []
    for name in acceptance['segments']:
        mask = masks[name]
        metrics = {arm: u.metrics(frame.loc[mask]) for arm, frame in arms.items()}
        delta = (metrics['S']['D2'] - metrics['raw']['D2']) if metrics['S']['D2'] is not None and metrics['raw']['D2'] is not None else None
        segments.append({'segment': name, 'metrics': metrics, 'delta_S_raw': delta})
        accept('segment_' + name, delta is not None and delta >= acceptance['segment_delta_D2_S_minus_rawB20_min'], delta, '>=-0.001')
    unchanged = ~raw.line.eq('buildings')
    for arm in ['L', 'S']:
        exact = np.array_equal(arms[arm].loc[unchanged, 'prediction'], raw.loc[unchanged, 'prediction']) and np.array_equal(
                arms[arm].loc[unchanged, 'annual_rate'], raw.loc[unchanged, 'annual_rate'])
        accept('motor_contents_exact_' + arm, exact, exact, 'bit exact predictions and rates')
    influence = []
    for reference in ['L', 'raw']:
        loss_delta = arms[reference].unit_deviance.to_numpy() - candidate.unit_deviance.to_numpy()
        groups = pd.DataFrame({'group_id': raw.group_id, 'advantage': loss_delta}).groupby('group_id', sort=True).advantage.sum()
        count = min(len(groups) - 1, max(5, int(np.ceil(.001 * len(groups)))))
        selected = groups.sort_values(ascending=False, kind='stable').head(count).index
        kept = ~raw.group_id.isin(selected).to_numpy()
        metrics = {arm: u.metrics(arms[arm].loc[kept]) for arm in ['S', reference]}
        delta = metrics['S']['D2'] - metrics[reference]['D2']
        info = {'reference': reference, 'removed_favorable_groups': count, 'delta_after_removal': delta,
                'selected_group_ids': list(selected), 'evaluation_only_no_refit': True}
        influence.append(info)
        accept('influence_S_minus_' + reference, delta >= acceptance['influence']['delta_D2_remaining_min'],
               {'groups': count, 'delta': delta}, '>=0 after evaluation-only removal')
    nominal = {arm: float((frame.loc[frame.line.eq('buildings'), 'exposure'] *
                          frame.loc[frame.line.eq('buildings'), 'annual_rate']).sum()) for arm, frame in arms.items()}
    change = nominal['S'] / nominal['raw'] - 1
    accept('buildings_nominal_level', abs(change) <= acceptance['absolute_buildings_nominal2023_total_change_vs_raw_max'], change, 'absolute change<=5%')
    passed = all(x['pass'] for x in conditions)
    report = {'id': plan['id'], 'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'plan_sha256': u.sha(RUN / 'plan_execution.json'), 'summary': summary, 'delta_S_L': dSL, 'delta_S_raw': dSR,
        'folds': folds, 'segments': segments, 'tail_gap': gap, 'influence': influence,
        'buildings_nominal_totals': nominal, 'buildings_nominal_change_S_raw': change,
        'technical_checks': technical, 'acceptance_checks': conditions, 'all_predictive_criteria_pass': passed,
        'failed_criteria': [x['name'] for x in conditions if not x['pass']],
        'support_v1': 'FAILED preserved, not resolved by exploration',
        'verdict': 'exploratory_signal_only_support_failed_no_promotion' if passed else 'exploratory_contrast_rejected_preserve_raw_B20',
        'reference': 'W2-B00', 'promotion': False, 'submission': False, '2024_test_closed': True,
        'new_CI': False, 'new_bootstrap': 0,
        'limits': 'Adaptive repeated2023 exploration; fold variation and influence are diagnostic, not independent confirmation or full-refit uncertainty.'}
    u.dump(RUN / 'evaluation.json', report)
    print(json.dumps({k: report[k] for k in ['verdict', 'delta_S_L', 'delta_S_raw', 'failed_criteria']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
