"""Revisión de artefactos anidados; estimación y ajuste bloqueados."""
from pathlib import Path
from itertools import combinations
from datetime import datetime, timezone
from unittest.mock import patch
import json
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
RUN = REPO / 'privado/semana2/desarrollo2023/b20_contraste_exploratorio_20261024_v2'
sys.path.insert(0, str(REPO / 'src'))
from semana2 import contraste_b20_exploratorio as core
np, pd, pq, u = core.np, core.pd, core.base.u.pq, core.base.u
KEY = core.KEY


def main():
    output = RUN / 'verification.json'
    u.require(not output.exists(), 'Verificación existente; conservar antes de repetir.')
    plan, evaluation = u.read(RUN / 'plan_execution.json'), u.read(RUN / 'evaluation.json')
    checks = []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    for source in plan['frozen_sources'] + plan['implementation_sources']:
        check('source_' + source['path'], u.sha(ROOT / source['path']) == source['sha256'])
    original = u.read(RUN / 'plan_preregistered.json')
    check('acceptance_unchanged', plan['acceptance'] == original['acceptance'])
    check('source_binding_evaluation', evaluation['plan_sha256'] == u.sha(RUN / 'plan_execution.json'))
    frame = pq.read_table(RUN / 'inputs_2023/buildings_outer0.parquet').to_pandas()
    claims = pq.read_table(RUN / 'inputs_2023/claims.parquet').to_pandas()
    all_oof = pq.read_table(RUN / 'contrast_oof_2023.parquet').to_pandas()
    predictions = {}
    # Esta revisión nunca reestima C0, transformaciones, GLM o calibración.
    with patch.object(core.c0, '_reporting_base', side_effect=AssertionError('C0 refit prohibited')), \
         patch.object(core.base.u.TweedieRegressor, 'fit', side_effect=AssertionError('GLM refit prohibited')), \
         patch.object(core, 'calibrate', side_effect=AssertionError('Calibration refit prohibited')):
        for pair in combinations(range(5), 2):
            path = RUN / 'inner' / ''.join(map(str, pair))
            artifact, receipt = u.read(path / 'C0.json'), u.read(path / 'receipt.json')
            fit = frame.loc[~frame.fold.isin(pair)]
            held = frame.loc[frame.fold.isin(pair)]
            metadata = fit[core.c0.META].to_dict('records')
            check('membership_' + str(pair), artifact['contract']['fit_membership_sha256'] == core.c0.membership_digest(metadata))
            check('folds_' + str(pair), receipt['excluded_folds'] == list(pair) and receipt['fit_rows'] == len(fit))
            for field in ['group_id', 'customer_id', 'address_id']:
                check(field + '_' + str(pair), set(fit[field]).isdisjoint(held[field]))
            weights = pd.DataFrame(artifact['weighted_claims'])
            expected = claims.loc[~claims.fold.isin(pair)]
            check('notifications_' + str(pair), not weights.fold.isin(pair).any()
                  and weights.year.eq(2023).all() and set(weights.claim_id) == set(expected.claim_id))
            for peril in core.c0.PERILS:
                selected = weights.loc[weights.peril.eq(peril)]
                check('weight_sum_' + str(pair) + peril, np.isclose(selected.weight.sum(), len(selected), rtol=0, atol=1e-10))
            bundle = core.joblib.load(path / 'bundle.joblib')
            check('whole_signature_' + str(pair), receipt['whole_learned_signature'] == {
                'C0': artifact['artifact_sha256'], 'transformer_and_GLM': core.joblib.hash(bundle)})
            replay = core.predict_inner({'C0': artifact, 'bundle': bundle, 'receipt': receipt}, held, pair)
            saved = pq.read_table(path / 'heldout_predictions.parquet').to_pandas()
            check('replay_' + str(pair), replay.equals(saved))
            predictions[pair] = saved
        inner_support = []
        for outer in range(5):
            params = u.read(RUN / 'calibration' / f'fold{outer}.json')
            data = pq.read_table(RUN / 'calibration' / f'fold{outer}_inner_oof.parquet').to_pandas()
            check('calibration_scope_' + str(outer), not data.fold.eq(outer).any()
                  and set(data.fold) == set(range(5)) - {outer}
                  and set(data.row_id) == set(frame.loc[frame.fold.ne(outer), 'row_id']))
            expected = pd.concat([predictions[tuple(sorted([outer, inner]))].loc[
                lambda f: f.fold.eq(inner)] for inner in range(5) if inner != outer], ignore_index=True)
            compared = expected.merge(data, on=KEY, validate='one_to_one', suffixes=('_expected', '_stored'))
            check('matching_inner_C0_rate_' + str(outer), np.array_equal(compared.C0_expected, compared.C0_stored)
                  and np.array_equal(compared.annual_rate_expected, compared.annual_rate_stored))
            m = float(np.average(np.log(data.annual_rate), weights=data.C0))
            check('centering_' + str(outer), m == params['m'])
            for arm in ['L', 'S']:
                b = 1. if arm == 'L' else params['b_S']
                a = params['a_L'] if arm == 'L' else params['a_S']
                h = data.C0.to_numpy() * np.exp(m + b * (np.log(data.annual_rate.to_numpy()) - m))
                a_formula = np.log(np.sum(data.T0.to_numpy() / np.sqrt(h)) / np.sum(np.sqrt(h)))
                check('intercept_identity_' + str(outer) + arm, np.isclose(a, a_formula, rtol=0, atol=1e-12))
                predicted = np.exp(a) * h
                g = 2 * (np.sqrt(predicted) - data.T0.to_numpy() / np.sqrt(predicted))
                check('intercept_score_' + str(outer) + arm, abs(float(g.mean())) < 1e-8)
                if arm == 'S':
                    gradient = float(np.mean(g * (np.log(data.annual_rate.to_numpy()) - m)))
                    kkt = abs(gradient) < 1e-4 if 1e-6 < b < 1 - 1e-6 else (gradient >= -1e-4 if b <= 1e-6 else gradient <= 1e-4)
                    check('slope_KKT_' + str(outer), kkt)
            # Nuevo soporte interior, no una repetición de las bandas retenidas.
            cuts = np.quantile(data.annual_rate, [.2, .4, .6, .8])
            bands = np.searchsorted(cuts, data.annual_rate, side='left') + 1
            for band in [1, 5]:
                cell = data.loc[bands == band]
                costs = cell.groupby('group_id', sort=True).T0.sum()
                positive = costs.loc[costs.gt(0)]
                total = float(positive.sum())
                largest = float(positive.max() / total) if total else None
                equivalent = float(total * total / np.sum(positive.to_numpy() ** 2)) if total else None
                rules = plan['support_v1']['pooled_tail']
                passed = len(positive) >= rules['positive_groups_min'] and largest is not None and largest <= rules['largest_cost_group_share_max'] and equivalent >= rules['cost_concentration_equivalent_groups_min']
                inner_support.append({'outer_fold': outer, 'band': band, 'positive_groups': len(positive),
                    'largest_cost_share': largest, 'concentration_equivalent': equivalent,
                    'passes_original_inner_tail_rule': bool(passed), 'diagnostic_only_under_v2': True})
    check('evaluation_preserves_failure_consequence', not evaluation['all_predictive_criteria_pass']
          or evaluation['verdict'] == 'exploratory_signal_only_support_failed_no_promotion')
    check('no_promotion_or_submission', not evaluation['promotion'] and not evaluation['submission'])
    event_text = (RUN / 'events.jsonl').read_text(encoding='utf-8')
    event_rows = [json.loads(row) for row in event_text.splitlines()]
    check('exact_price_budget', sum(x['event'] == 'inner_fit_started' for x in event_rows) == 10
          and sum(x['event'] == 'inner_fit_completed' for x in event_rows) == 10)
    check('scoped_source_materialization', all('2023' in x['predicate'] or '519 declared IDs' in x['predicate']
          for x in event_rows if x['event'] == 'scoped_read'))
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'author': 'Codex',
        'checks': checks, 'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks),
        'inner_support': inner_support, 'new_fits_this_verification': 0, '2024_test_closed': True,
        'scope': 'Saved-source membership, exact replay, independent algebra/KKT and preregistered criteria binding; own verification, not professional independence.'}
    u.dump(output, report)
    print(json.dumps({'passed': report['passed'], 'failed': report['failed'],
                      'inner_tail_cells_passing_v1': sum(x['passes_original_inner_tail_rule'] for x in inner_support)}))
    u.require(report['failed'] == 0, 'La verificación conserva fallos técnicos; revisar antes de cierre.')


if __name__ == '__main__':
    main()
