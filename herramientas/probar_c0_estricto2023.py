"""Pruebas sintéticas de C0; nunca carga filas o estimadores del concurso."""
from pathlib import Path
from datetime import datetime, timezone
from itertools import permutations
from copy import deepcopy
from unittest.mock import patch
import hashlib
import io
import json
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
RUN = REPO / 'privado/semana2/desarrollo2023/c0_adapter_sintetico_20261024_v1'
sys.path.insert(0, str(REPO / 'src'))
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from semana2 import c0_estricto2023 as core
from semana2.variables_ultimo import fit_reporting, average_completion

SOURCES = {'synthetic_fixture': hashlib.sha256(b'fixed-C0-fixture-v1').hexdigest(),
           'recipe': hashlib.sha256(core.RECIPE.encode()).hexdigest()}
FIT_CALLS = 0
POISON_CASES = 0
BLOCKED_DATA_OPENS = []


def fixture():
    periods, claims = [], []
    for fold in range(5):
        for j, start in enumerate(['2023-01-01', '2023-02-01', '2023-04-01', '2023-07-01']):
            periods.append({'market': 'emerging', 'line': 'buildings', 'row_id': f'B{fold}_{j}',
                'year': 2023, 'is_test': False, 'fold': fold, 'group_id': f'g{fold}_{j}',
                'customer_id': f'c{fold}_{j}', 'address_id': f'a{fold}_{j}',
                'period_start': start, 'period_end': '2023-12-31', 'exposure': 1. - j * .15})
        for p, peril in enumerate(core.PERILS):
            for j in range(6):
                period = periods[-4 + j % 4]
                loss = pd.Timestamp(period['period_start']) + pd.Timedelta(days=2 * j)
                report = loss + pd.Timedelta(days=50 * j + p * 7)
                claims.append({'market': 'emerging', 'line': 'buildings', 'row_id': period['row_id'],
                    'claim_id': f'cl{fold}_{p}_{j}', 'year': 2023, 'is_test': False, 'fold': fold,
                    'included_in_T0': True, 'peril': peril, 'loss_date': loss,
                    'report_date': report, 'T0_cents': 100 * (fold + 1) * (p + 1) * (j + 1),
                    'reserve_cents': 0})
    return pd.DataFrame(periods), pd.DataFrame(claims)


def fit(periods, claims, excluded=(0, 1), sources=None):
    global FIT_CALLS
    FIT_CALLS += 1
    return core.fit_c0_2023(periods, claims, excluded_folds=excluded,
                           source_versions=SOURCES if sources is None else sources)


class TestStrictC0(unittest.TestCase):
    def setUp(self):
        self.periods, self.claims = fixture()

    def test_manual_reporting_reference(self):
        model, weights = core._reporting_base([0, 0, 10, 10, 10], [20] * 5, [1, 1, 3, 3, 3])
        np.testing.assert_allclose(model['count_mass'], [.4, .6], rtol=0, atol=1e-15)
        self.assertAlmostEqual(model['mean_net_mark'], 2.2)
        np.testing.assert_allclose(model['cost_cdf'], [.4 / 2.2, 1.], rtol=0, atol=1e-15)
        np.testing.assert_allclose(weights, np.ones(5), rtol=0, atol=1e-15)

    def test_historical_base_equivalence(self):
        artifact = fit(self.periods, self.claims)
        training = self.claims.loc[~self.claims.fold.isin([0, 1])].sort_values([*core.KEY, 'claim_id'])
        legacy_periods = core._period_features(self.periods)
        legacy_periods['is_test'] = False
        mask = ~self.periods.fold.isin([0, 1]).to_numpy()
        levels, completions = {}, {}
        for peril in core.PERILS:
            rows = training.loc[training.peril.eq(peril)]
            delay = (rows.report_date - rows.loss_date).dt.days
            age = (pd.Timestamp(core.VALUATION) - rows.loss_date).dt.days
            old, weights = fit_reporting(delay, age, rows.T0_cents / 100, rows.reserve_cents / 100)
            new = artifact['curves'][peril]
            for field in ['delay_days', 'events', 'risk_set', 'count_cdf', 'count_mass']:
                np.testing.assert_array_equal(new[field], old[field])
            np.testing.assert_array_equal(new['cost_cdf'], old['cost_cdf']['1.0'])
            self.assertEqual(new['mean_net_mark'], old['mean_net_mark']['1.0'])
            stored_weights = [x['weight'] for x in artifact['weighted_claims'] if x['peril'] == peril]
            np.testing.assert_array_equal(stored_weights, weights)
            qn = average_completion(legacy_periods, old)
            qc = average_completion(legacy_periods, old, 'cost', 1.)
            denominator = float(np.sum(legacy_periods.exposure.to_numpy()[mask] * qn[mask]))
            self.assertEqual(artifact['frequencies'][peril]['effective_count_exposure'], denominator)
            levels[peril] = len(rows) / denominator * old['mean_net_mark']['1.0']
            completions[peril] = qc
        expected = sum(levels[p] / sum(levels.values()) * completions[p] for p in core.PERILS)
        actual = core.apply_c0_2023(self.periods, artifact, excluded_folds=[0, 1])
        np.testing.assert_allclose(actual.q_cost_mix, expected, rtol=0, atol=1e-15)
        np.testing.assert_allclose(actual.C0, expected * self.periods.exposure, rtol=0, atol=1e-15)

    def test_all_twenty_ordered_exclusions_and_poisoning(self):
        global POISON_CASES
        for outer, inner in permutations(range(5), 2):
            with self.subTest(outer=outer, inner=inner):
                clean = fit(self.periods, self.claims, [outer, inner])
                poisoned = self.claims.copy()
                held = poisoned.fold.isin([outer, inner])
                poisoned.loc[held, 'T0_cents'] = np.nan
                poisoned.loc[held, 'loss_date'] = pd.NaT
                poisoned.loc[held, 'report_date'] = pd.NaT
                poisoned.loc[held, 'peril'] = 'protected_payload_not_a_peril'
                poisoned.loc[held, 'reserve_cents'] = -999999999
                p = self.periods.copy()
                protected = p.fold.isin([outer, inner])
                p.loc[protected, 'exposure'] = np.nan
                p.loc[protected, 'period_start'] = 'not-a-date'
                dirty = fit(p, poisoned, [outer, inner])
                self.assertEqual(clean, dirty)  # Todo el objeto, incluidas claves y ancestros.
                first = core.apply_c0_2023(self.periods, clean, excluded_folds=[outer, inner])
                again = core.apply_c0_2023(self.periods, dirty, excluded_folds=[outer, inner])
                pd.testing.assert_frame_equal(first, again, check_exact=True)
                POISON_CASES += 1

    def test_positive_training_target_control(self):
        clean = fit(self.periods, self.claims)
        poisoned = self.claims.copy()
        i = poisoned.index[poisoned.fold.eq(2)][0]
        poisoned.loc[i, 'T0_cents'] *= 100
        dirty = fit(self.periods, poisoned)
        self.assertNotEqual(clean['artifact_sha256'], dirty['artifact_sha256'])
        self.assertNotEqual(clean['cache_key'], dirty['cache_key'])
        self.assertNotEqual(clean['curves'], dirty['curves'])
        self.assertNotEqual(clean['cost_shares'], dirty['cost_shares'])
        self.assertFalse(core.apply_c0_2023(self.periods, clean, excluded_folds=[0, 1]).C0.equals(
            core.apply_c0_2023(self.periods, dirty, excluded_folds=[0, 1]).C0))

    def test_training_dates_and_exposure_affect_cache(self):
        clean = fit(self.periods, self.claims)
        p = self.periods.copy()
        p.loc[p.fold.eq(2), 'exposure'] *= 2
        changed = fit(p, self.claims)
        self.assertNotEqual(clean['cache_key'], changed['cache_key'])
        self.assertNotEqual(clean['frequencies'], changed['frequencies'])
        c = self.claims.copy()
        mask = c.fold.eq(2)
        c.loc[mask, 'report_date'] += pd.Timedelta(days=50)
        self.assertNotEqual(clean['cache_key'], fit(self.periods, c)['cache_key'])

    def test_source_versions_bound_and_order_invariant(self):
        clean = fit(self.periods, self.claims)
        shuffled = fit(self.periods.iloc[::-1], self.claims.iloc[::-1], [1, 0])
        self.assertEqual(clean, shuffled)
        changed = fit(self.periods, self.claims, sources={**SOURCES, 'recipe': 'f' * 64})
        self.assertNotEqual(clean['cache_key'], changed['cache_key'])
        self.assertEqual(clean['curves'], changed['curves'])

    def test_compound_keys_exclude_same_row_id_in_other_line(self):
        clean = fit(self.periods, self.claims)
        extra_p, extra_c = self.periods.copy(), self.claims.copy()
        extra_p['line'] = 'contents'
        extra_c['line'] = 'contents'
        extra_c['T0_cents'] = np.nan
        extra_c['report_date'] = pd.NaT
        both_p = pd.concat([self.periods, extra_p], ignore_index=True)
        both_c = pd.concat([self.claims, extra_c], ignore_index=True)
        self.assertEqual(clean, fit(both_p, both_c))

    def test_reserve_is_not_calibration_slope_or_base_input(self):
        clean = fit(self.periods, self.claims)
        c = self.claims.copy()
        c['reserve_cents'] = -999999999
        self.assertEqual(clean, fit(self.periods, c))
        self.assertEqual(clean['contract']['reserve_factor'], 1.)
        with self.assertRaises(TypeError):
            core.fit_c0_2023(self.periods, self.claims, excluded_folds=[0, 1],
                             source_versions=SOURCES, calibration_slope=.5)

    def test_foreign_period_metadata_fails_before_fit(self):
        for column, value in [('year', 2024), ('is_test', True), ('market', 'developed'),
                              ('address_id', 'a0_0'), ('fold', True)]:
            with self.subTest(column=column):
                p = self.periods.copy()
                if column == 'fold':
                    p[column] = p[column].astype(object)
                p.loc[p.index[-1], column] = value
                with patch.object(core, '_reporting_base', side_effect=AssertionError('Estimator called')):
                    with self.assertRaises(ValueError):
                        fit(p, self.claims)
        with self.assertRaises(ValueError):
            fit(self.periods.drop(columns='is_test'), self.claims)
        with self.assertRaises(ValueError):
            fit(pd.concat([self.periods, self.periods.iloc[:1]]), self.claims)

    def test_claim_metadata_and_links_fail_before_fit(self):
        for column, value in [('year', 2024), ('is_test', True), ('row_id', 'unknown'),
                              ('fold', 4), ('fold', True), ('included_in_T0', False)]:
            with self.subTest(column=column):
                c = self.claims.copy()
                if column == 'fold':
                    c[column] = c[column].astype(object)
                c.loc[0, column] = value
                with patch.object(core, '_reporting_base', side_effect=AssertionError('Estimator called')):
                    with self.assertRaises(ValueError):
                        fit(self.periods, c)

    def test_empty_or_undersupported_peril_has_no_heldout_fallback(self):
        c = self.claims.loc[~(self.claims.peril.eq('fire') & ~self.claims.fold.isin([0, 1]))]
        with self.assertRaises(ValueError):
            fit(self.periods, c)
        keep = self.claims.loc[self.claims.peril.eq('fire') & ~self.claims.fold.isin([0, 1])].head(4)
        with self.assertRaises(ValueError):
            fit(self.periods, pd.concat([c, keep]))

    def test_invalid_training_numerics_and_dates(self):
        for column, value in [('T0_cents', -1), ('T0_cents', .5), ('T0_cents', np.inf),
                              ('report_date', pd.Timestamp('2025-01-01'))]:
            with self.subTest(column=column, value=value):
                c = self.claims.copy()
                if column == 'T0_cents':
                    c[column] = c[column].astype(object)
                c.loc[c.index[c.fold.eq(2)][0], column] = value
                with self.assertRaises(ValueError):
                    fit(self.periods, c)

    def test_scope_bound_cache_and_tampering_rejected(self):
        outer = fit(self.periods, self.claims, [0])
        with self.assertRaises(ValueError):
            core.apply_c0_2023(self.periods, outer, excluded_folds=[0, 1])
        artifact = fit(self.periods, self.claims)
        changed = deepcopy(artifact)
        changed['cost_shares']['fire'] *= 2
        with self.assertRaises(ValueError):
            core.apply_c0_2023(self.periods, changed, excluded_folds=[0, 1])
        for excluded in [[], [0, 0], [0, 1, 2], [False, 1], [0, 5]]:
            with self.assertRaises(ValueError):
                fit(self.periods, self.claims, excluded)
        p = self.periods.copy()
        p.loc[0, 'row_id'] = 'not_in_manifest'
        with self.assertRaises(ValueError):
            core.apply_c0_2023(p, artifact, excluded_folds=[0, 1])


def main():
    # No fixture o prueba puede leer los originales, predicciones o estimadores.
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            name = str(args[0]).lower()
            if name.endswith(('.parquet', '.csv', '.joblib', '.pkl', '.pickle')):
                BLOCKED_DATA_OPENS.append(name)
                raise RuntimeError('Competition/data/model file reads prohibited in synthetic suite')
    sys.addaudithook(audit)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestStrictC0))
    (RUN / 'tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'author': 'Codex',
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'success': result.wasSuccessful(), 'ordered_poison_cases': POISON_CASES,
        'synthetic_C0_fit_calls': FIT_CALLS, 'competition_rows_read': 0,
        'competition_C0_fits': 0, 'new_pricing_fits': 0, 'new_predictions': 0,
        'new_scores': 0, 'blocked_data_open_attempts': len(BLOCKED_DATA_OPENS),
        'support_gate': 'FAILED unchanged', 'scope': 'C0 stage only; no GLM or calibrator certification',
        'environment': {'python': sys.version, 'numpy': np.__version__, 'pandas': pd.__version__}}
    (RUN / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(stream.getvalue())
    print(json.dumps(report, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
