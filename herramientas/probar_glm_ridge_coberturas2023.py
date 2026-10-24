"""Adversos del consumidor real de B20; cero ajustes adicionales."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import copy
import json
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
spec = importlib.util.spec_from_file_location('ridge_real_consumer', REPO/'src/semana2/entrenar_glm_ridge_coberturas2023.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def main():
    run = Path(sys.argv[1]).resolve()
    run.relative_to(REPO/'privado/semana2/desarrollo2023')
    p = m.u.read(run/'plan_snapshot.json')
    ad = run/'adversaries'
    ad.mkdir(exist_ok=False)
    checks = []
    def check(name, value):
        checks.append({'name': name, 'pass': bool(value)})
    def reject(name, fn):
        try:
            fn()
        except (ValueError, KeyError):
            check(name, True)
        else:
            check(name, False)
    def forbidden(*args, **kwargs):
        raise AssertionError('Fit adicional bloqueado en adversos')
    for cls in [m.u.TweedieRegressor, m.u.SimpleImputer, m.u.StandardScaler,
                m.u.OneHotEncoder, m.u.ColumnTransformer, m.u.Pipeline]:
        cls.fit = forbidden
        if hasattr(cls, 'fit_transform'):
            cls.fit_transform = forbidden
    for line in ['motor', 'buildings', 'contents']:
        source = ROOT/p['input_run']/f'inputs_2023/{line}_fold0.parquet'
        f = m.pq.read_table(source).to_pandas()
        valid = f[f.fold.eq(0)].head(24).copy()
        b = m.u.joblib.load(run/'models'/f'{line}_fold0'/'bundle.joblib')
        field = 'x_cover_type' if line == 'motor' else 'x_accidental_damage_cover'
        with m.u.threadpool_limits(limits=2):
            expected = m.predict(b, valid, line)
        for name, column, value in [('year', 'year', 2024), ('test', 'is_test', True),
                                     ('missingcover', field, None), ('unknowncover', field, 'unknown' if line == 'motor' else 2.),
                                     ('zerolink', 'e_cost_mix_1.0', 0.), ('nanlink', 'e_cost_mix_1.0', float('nan')),
                                     ('negativetarget', 'T0', -1.), ('nanbusiness', 'x_new_business', float('nan'))]:
            bad = valid.copy()
            bad[column] = value
            reject(name+line, lambda bad=bad: m.predict(b, bad, line))
        duplicate = m.pd.concat([valid, valid.head(1)], ignore_index=True)
        reject('duplicatekeys'+line, lambda: m.predict(b, duplicate, line))
        reject('heldoutcannotfit'+line, lambda: m.fit_ridge(valid, line, 0, p['recipe']))
        wrong = dict(b, model_id='invalid')
        reject('wrongmodel'+line, lambda: m.predict(wrong, valid, line))
        poison = valid.copy()
        poison['T0'], poison['reserve'], poison['written_premium'] = 1e15, 1e15, -1e15
        poison['row_id'] = ['poison'+str(j) for j in range(len(poison))]
        with m.u.threadpool_limits(limits=2):
            actual = m.predict(b, poison, line)
            reordered = m.predict(b, valid.iloc[::-1], line)
        check('targetreservetariffIDsnotpredictors'+line, m.np.array_equal(actual, expected))
        check('roworderonly'+line, m.np.array_equal(reordered[::-1], expected))
        check('positivefinite'+line, m.np.isfinite(expected).all() and (expected > 0).all())
        if line != 'motor':
            off = valid.copy()
            off[field] = 0.
            with m.u.threadpool_limits(limits=2):
                rates = m.predict(b, off, line)
            check('falsecoverneverstructuralzero'+line, (rates > 0).all())
    before = m.u.sha(run/'events.jsonl')
    native = []
    for label in ['duplicate_run', 'wrong_code', 'wrong_source']:
        plan = copy.deepcopy(p)
        if label == 'wrong_code':
            plan['code_sha256'] = '0'*64
        elif label == 'wrong_source':
            plan['frozen_sources'][0]['sha256'] = '0'*64
        pp = ad/(label+'_plan.json')
        m.u.dump(pp, plan)
        result = subprocess.run([sys.executable, str(ROOT/p['code']), str(pp)], capture_output=True, text=True)
        (ad/(label+'_stdout.txt')).write_text(result.stdout, encoding='utf-8')
        (ad/(label+'_stderr.txt')).write_text(result.stderr, encoding='utf-8')
        phrase = {'duplicate_run': 'FileExistsError', 'wrong_code': 'Código/receta cambió', 'wrong_source': 'Fuente cambió'}[label]
        accepted = result.returncode != 0 and phrase in result.stderr and 'fit_started' not in result.stdout
        check('nativecommandrejects'+label, accepted)
        native.append({'case': label, 'returncode': result.returncode, 'expected_failure': accepted})
    check('nofitneworduplicate', m.u.sha(run/'events.jsonl') == before)
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks),
              'checks': checks, 'native_negative_commands': native, 'new_fits': 0,
              'checker_sha256': m.u.sha(Path(__file__)), 'professional_independent_validation': False}
    m.u.dump(run/'fixture_checks.json', result)
    print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'failures': [x for x in checks if not x['pass']]}))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
