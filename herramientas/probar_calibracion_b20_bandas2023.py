"""Adversos de cortes/empates/cohortes y del comando real; cero entrenamiento."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import importlib.util
import json
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
spec = importlib.util.spec_from_file_location('actual_b20_band_consumer', REPO/'src/semana2/revisar_calibracion_b20_bandas2023.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def main():
    run = Path(sys.argv[1]).resolve()
    run.relative_to(REPO/'privado/semana2/desarrollo2023')
    p = m.read(run/'plan_snapshot.json')
    ad = run/'adversaries'
    ad.mkdir(exist_ok=False)
    checks = []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    def reject(name, fn):
        try:
            fn()
        except ValueError:
            check(name, True)
        else:
            check(name, False)
    def forbidden(*args, **kwargs):
        raise AssertionError('Fit bloqueado en adversos de bandas')
    for cls in [m.TweedieRegressor, m.ColumnTransformer, m.SimpleImputer, m.StandardScaler, m.OneHotEncoder, m.Pipeline]:
        cls.fit = forbidden
        if hasattr(cls, 'fit_transform'):
            cls.fit_transform = forbidden
    train = m.pq.read_table(run/'training_rate_replays_2023.parquet').to_pandas()
    part = train[train.line.eq('motor') & train.model_fold.eq(0)].copy()
    edges = m.edges_from_fit_rates(part.annual_rate)
    poisoned = part.copy()
    poisoned['T0'], poisoned['row_id'], poisoned['group_id'] = 1e15, 'poison', 'poison'
    check('TargetandIDscannotchangeedges', m.np.array_equal(edges, m.edges_from_fit_rates(poisoned.annual_rate)))
    check('Rowordercannotchangeedges', m.np.array_equal(edges, m.edges_from_fit_rates(part.annual_rate.iloc[::-1])))
    tied = m.edges_from_fit_rates([1., 1., 1., 1., 1.])
    check('TieskeptnotIDsplit', m.np.array_equal(tied, [1., 1., 1., 1.]))
    check('Emptybandsretained', m.np.array_equal(m.assign_band([.5, 1., 2.], tied), [1, 1, 5]))
    check('Exactuppercutinclusive', m.np.array_equal(m.assign_band([1., 2., 3., 4., 5.], [1., 2., 3., 4.]), [1, 2, 3, 4, 5]))
    for name, values in [('zero', [0., 1.]), ('negative', [-1., 2.]), ('nan', [float('nan'), 2.]), ('emptyfit', [])]:
        reject('Invalidfitrates '+name, lambda values=values: m.edges_from_fit_rates(values))
    reject('Descendingcuts', lambda: m.assign_band([1., 2.], [2., 1., 3., 4.]))
    reject('Nonfinitecuts', lambda: m.assign_band([1., 2.], [1., 2., 3., float('inf')]))
    reject('Invalidheldoutrates', lambda: m.assign_band([0., 2.], edges))
    source = m.pq.read_table(ROOT/p['frame_source']/'inputs_2023/motor_fold0.parquet').to_pandas().head(20)
    for name, col, value in [('year', 'year', 2024), ('test', 'is_test', True), ('T0', 'T0', -1.), ('C0', 'e_cost_mix_1.0', 0.)]:
        bad = source.copy()
        bad[col] = value
        reject('Cohortguard '+name, lambda bad=bad: m.guard(bad))
    reject('Duplicatedcohortkeys', lambda: m.guard(m.pd.concat([source, source.head(1)])))
    empty = part.head(0)
    c = m.cell_stats(empty, 'W2-B20', 'fit')
    check('EmptyAEundefined', c['rows'] == 0 and c['actual_over_expected'] is None)
    zeros = part.head(3).copy()
    zeros['T0'] = 0.
    c = m.cell_stats(zeros, 'W2-B20', 'fit')
    check('ZeroobservationspositiveEhasAEzero', c['predicted_total'] > 0 and c['actual_over_expected'] == 0. and c['largest_group_cost_share'] is None)
    native = []
    for label in ['wrong_source', 'duplicate_run']:
        altered = copy.deepcopy(p)
        if label == 'wrong_source':
            altered['frozen_sources'][0]['sha256'] = '0'*64
        pp = ad/(label+'_plan.json')
        m.dump(pp, altered)
        proc = subprocess.run([sys.executable, str(ROOT/p['producer']), str(pp)], capture_output=True, text=True)
        (ad/(label+'_stdout.txt')).write_text(proc.stdout, encoding='utf-8')
        (ad/(label+'_stderr.txt')).write_text(proc.stderr, encoding='utf-8')
        phrase = 'Fuente cambió' if label == 'wrong_source' else 'FileExistsError'
        valid = proc.returncode != 0 and phrase in proc.stderr and not proc.stdout.strip()
        check('NativeCLI '+label, valid)
        native.append({'case': label, 'exit_code': proc.returncode, 'expected_failure': valid})
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'passed': sum(x['pass'] for x in checks),
              'failed': sum(not x['pass'] for x in checks), 'checks': checks, 'native_commands': native,
              'new_fits': 0, 'professional_independent_validation': False}
    m.dump(run/'fixture_checks.json', result)
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'failures': [x for x in checks if not x['pass']]}))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
