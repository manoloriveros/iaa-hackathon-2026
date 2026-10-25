"""Preflight sintético del flujo C0/transformaciones/GLM/calibrador completo."""
from pathlib import Path
from itertools import combinations
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
import sys
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
RUN = REPO / 'privado/semana2/desarrollo2023/b20_contraste_exploratorio_20261024_v2'
sys.path.insert(0, str(REPO / 'src'))
from semana2 import contraste_b20_exploratorio as core
np, pd = core.np, core.pd
PLAN = json.loads((RUN / 'plan_preregistered.json').read_text(encoding='utf-8'))
SETTINGS = PLAN['calibration_numerics']
VERSIONS = {'synthetic': 'a' * 64}
FITS = 0


def fixture():
    periods, claims = [], []
    for fold in range(5):
        for i in range(50):
            row = {'market': 'emerging', 'line': 'buildings', 'row_id': f'B{fold}_{i:03}',
                'year': 2023, 'is_test': False, 'fold': fold, 'group_id': f'g{fold}_{i}',
                'customer_id': f'c{fold}_{i}', 'address_id': f'a{fold}_{i}',
                'period_start': pd.Timestamp('2023-01-01'), 'period_end': pd.Timestamp('2023-12-31'),
                'exposure': 1., 'T0': 0., 'x_new_business': float(i % 2),
                'x_log_sum_insured': np.log(1 + i), 'x_property_age': float(i),
                'x_flood_zone': float(i % 3), 'x_accidental_damage_cover': float(i % 2),
                'x_property_type': ['house', 'flat'][i % 2], 'x_region': ['E01', 'E02'][i % 2]}
            periods.append(row)
        for p, peril in enumerate(core.c0.PERILS):
            for i in range(40):
                row = periods[-50 + i]
                mark = int(round(100 * (1 + i) ** 2 * (1 + .1 * p)))
                loss = pd.Timestamp('2023-01-01') + pd.Timedelta(days=i)
                claims.append({'market': 'emerging', 'line': 'buildings', 'row_id': row['row_id'],
                    'claim_id': f'cl{fold}_{p}_{i}', 'year': 2023, 'is_test': False, 'fold': fold,
                    'included_in_T0': True, 'peril': peril, 'loss_date': loss,
                    'report_date': loss + pd.Timedelta(days=(i % 6) * 80 + p), 'T0_cents': mark})
                row['T0'] += mark / 100
    return pd.DataFrame(periods), pd.DataFrame(claims)


def fit(frame, claims, pair):
    global FITS
    FITS += 1
    return core.fit_inner(frame, claims, pair, PLAN['recipe'], VERSIONS)


class Preflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame, cls.claims = fixture()
        cls.nodes, cls.predictions = {}, {}
        for pair in combinations(range(5), 2):
            node = fit(cls.frame, cls.claims, pair)
            cls.nodes[pair] = node
            cls.predictions[pair] = core.predict_inner(node, cls.frame.loc[cls.frame.fold.isin(pair)], pair)

    def test_all_five_outer_folds_whole_pipeline_poisoning(self):
        for outer in range(5):
            with self.subTest(outer=outer):
                frame, claims = self.frame.copy(), self.claims.copy()
                frame.loc[frame.fold.eq(outer), 'T0'] = np.nan
                held = claims.fold.eq(outer)
                claims.loc[held, 'T0_cents'] = np.nan
                claims.loc[held, 'report_date'] = pd.NaT
                claims.loc[held, 'peril'] = 'protected_invalid_payload'
                predictions = {}
                for inner in range(5):
                    if inner == outer:
                        continue
                    pair = tuple(sorted([inner, outer]))
                    node = fit(frame, claims, pair)
                    self.assertEqual(node['receipt']['whole_learned_signature'],
                                     self.nodes[pair]['receipt']['whole_learned_signature'])
                    predictions[pair] = core.predict_inner(node, frame.loc[frame.fold.eq(inner)], pair)
                clean, data = core.calibration_for_outer(self.frame, self.predictions, outer, SETTINGS)
                poisoned, again = core.calibration_for_outer(frame, predictions, outer, SETTINGS)
                self.assertEqual(clean, poisoned)
                pd.testing.assert_frame_equal(data, again, check_exact=True)

    def test_scalar_fit_recovers_known_parameters(self):
        rate, exposure = np.exp(np.linspace(1, 5, 100)), np.linspace(.2, 1.2, 100)
        m = np.average(np.log(rate), weights=exposure)
        y = np.exp(.3) * exposure * np.exp(m + .6 * (np.log(rate) - m))
        fit = core.calibrate(y, rate, exposure, SETTINGS)
        self.assertAlmostEqual(fit['b_S'], .6, places=6)
        self.assertAlmostEqual(fit['a_S'], .3, places=6)
        self.assertLess(fit['fit_loss_S'], fit['fit_loss_L'])
        self.assertLess(abs(fit['intercept_score_L']), 1e-8)
        np.testing.assert_allclose(core.apply_calibration(rate, exposure, fit, 'S'), y, rtol=1e-6)

    def test_endpoints_have_explicit_parsimony_and_degeneracy(self):
        rate, exposure = np.exp(np.linspace(1, 5, 100)), np.ones(100)
        self.assertEqual(core.calibrate(rate * 1.3, rate, exposure, SETTINGS)['b_S'], 1.)
        self.assertEqual(core.calibrate(np.ones(100) * 50, rate, exposure, SETTINGS)['b_S'], 0.)

    def test_positive_training_target_control_changes_pipeline(self):
        frame, claims = self.frame.copy(), self.claims.copy()
        chosen = claims.index[claims.fold.eq(2)][0]
        key = claims.loc[chosen, 'row_id']
        increment = int(claims.loc[chosen, 'T0_cents'] * 20)
        claims.loc[chosen, 'T0_cents'] += increment
        frame.loc[frame.row_id.eq(key), 'T0'] += increment / 100
        changed = fit(frame, claims, (0, 1))
        self.assertNotEqual(changed['receipt']['whole_learned_signature'],
                            self.nodes[(0, 1)]['receipt']['whole_learned_signature'])

    def test_2024_rejected_before_glm(self):
        frame = self.frame.copy()
        frame.loc[0, 'year'] = 2024
        with patch.object(core.base, 'fit_ridge', side_effect=AssertionError('GLM called')):
            with self.assertRaises(ValueError):
                fit(frame, self.claims, (0, 1))

    def test_duplicate_prediction_rows_cannot_reach_calibration(self):
        predictions = deepcopy(self.predictions)
        predictions[(0, 1)] = pd.concat([predictions[(0, 1)], predictions[(0, 1)].iloc[:1]])
        # Duplicate a row specifically used as inner fold1 for outer0.
        row = predictions[(0, 1)].loc[predictions[(0, 1)].fold.eq(1)].iloc[:1]
        predictions[(0, 1)] = pd.concat([predictions[(0, 1)], row])
        with self.assertRaises(ValueError):
            core.calibration_for_outer(self.frame, predictions, 0, SETTINGS)


def main():
    output = RUN / 'synthetic_preflight.json'
    assert not output.exists(), 'Preflight existente; conservarlo antes de otra revisión.'
    stream = io.StringIO()
    # Ninguna prueba del flujo puro puede entrar a lectores Parquet o modelos.
    with patch.object(core.base.u.pq, 'read_table', side_effect=AssertionError('Data read prohibited')), \
         patch.object(core.joblib, 'load', side_effect=AssertionError('Model load prohibited')):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Preflight))
    (RUN / 'synthetic_tests.txt').write_text(stream.getvalue(), encoding='utf-8')
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'success': result.wasSuccessful(),
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'synthetic_inner_GLM_invocations': FITS, 'whole_pipeline_outer_poison_cases': 5 if result.wasSuccessful() else None,
        'competition_data_loaded': False, 'competition_fits': 0,
        'coverage': 'C0 curves/marks/frequencies/mixture + imputer/scaler/OHE + GLM + slope/intercepts'}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(stream.getvalue())
    print(json.dumps(report, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
