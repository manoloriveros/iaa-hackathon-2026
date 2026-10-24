"""Guardas reales de atribución; sin entrenamientos, nuevos precios o remuestreo."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import importlib.util
import json
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
spec = importlib.util.spec_from_file_location('actual_attribution_b20', REPO/'src/semana2/atribuir_b20_grupos2023.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def main():
    run = Path(sys.argv[1]).resolve()
    run.relative_to(REPO/'privado/semana2/desarrollo2023')
    plan = m.read(run/'plan_snapshot.json')
    out = run/'adversaries'
    out.mkdir(exist_ok=False)
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
        raise AssertionError('Fit bloqueado en fixtures de atribución')
    for cls in [m.TweedieRegressor, m.ColumnTransformer, m.SimpleImputer, m.StandardScaler, m.OneHotEncoder, m.Pipeline]:
        cls.fit = forbidden
        if hasattr(cls, 'fit_transform'):
            cls.fit_transform = forbidden
    data = m.pq.read_table(ROOT/plan['ridge_run']/'oof_2023.parquet', filters=[('model_id', 'in', ['W2-B20', 'W2-B19'])]).to_pandas()
    a = data[data.model_id.eq('W2-B20')].sort_values(m.KEY).head(20).reset_index(drop=True)
    b = data[data.model_id.eq('W2-B19')].sort_values(m.KEY).head(20).reset_index(drop=True)
    for name, column, value in [('year', 'year', 2024), ('test', 'is_test', True), ('negative_target', 'T0', -1.),
                                ('nan_target', 'T0', float('nan')), ('zero_prediction', 'prediction', 0.),
                                ('nan_prediction', 'prediction', float('nan'))]:
        bad = a.copy()
        bad[column] = value
        reject('Reject '+name, lambda bad=bad: m.pair_frame(bad, b))
    for column, value in [('T0', 999999.), ('fold', 99), ('group_id', 'synthetic_wrong_group'), ('e_cost_mix_1.0', 1e15)]:
        bad = a.copy()
        bad[column] = value
        reject('Pair contract '+column, lambda bad=bad: m.pair_frame(bad, b))
    duplicate = m.pd.concat([a, a.head(1)], ignore_index=True)
    reject('Duplicate keys', lambda: m.pair_frame(duplicate, b))
    mismatch = b.copy()
    mismatch.loc[0, 'row_id'] = 'synthetic_wrong_ID'
    reject('Different keys', lambda: m.pair_frame(a, mismatch))
    same = m.pair_frame(a, a)
    check('Identicalsavedmodelsidentity', m.np.array_equal(same.gain.to_numpy(), m.np.zeros(len(same))))
    reversed_pair = m.pair_frame(b, a)
    original = m.pair_frame(a, b)
    check('Swapchangesgainexactsign', m.np.array_equal(original.gain.to_numpy(), -reversed_pair.gain.to_numpy()))
    commands = []
    for label in ['wrong_source', 'duplicate_run']:
        pp = copy.deepcopy(plan)
        if label == 'wrong_source':
            pp['frozen_sources'][0]['sha256'] = '0'*64
        path = out/(label+'_plan.json')
        m.dump(path, pp)
        proc = subprocess.run([sys.executable, str(ROOT/plan['producer']), str(path)], capture_output=True, text=True)
        (out/(label+'_stdout.txt')).write_text(proc.stdout, encoding='utf-8')
        (out/(label+'_stderr.txt')).write_text(proc.stderr, encoding='utf-8')
        phrase = 'Fuente cambió' if label == 'wrong_source' else 'FileExistsError'
        valid = proc.returncode != 0 and phrase in proc.stderr and not proc.stdout.strip()
        check('NativeCLI '+label, valid)
        commands.append({'case': label, 'exit_code': proc.returncode, 'expected_failure': valid})
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'new_fits': 0,
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks),
              'checks': checks, 'native_commands': commands, 'professional_independent_validation': False}
    m.dump(run/'fixture_checks.json', result)
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'failures': [x for x in checks if not x['pass']]}))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
