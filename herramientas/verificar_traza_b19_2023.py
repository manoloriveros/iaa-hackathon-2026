"""Cotejo propio por Decimal, diccionarios y datetime; no repite las suites GLM."""
from pathlib import Path
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import argparse
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq

read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
day = lambda x: x.date() if hasattr(x, 'date') else x


def verify(run):
    run = run.resolve()
    p = read(run / 'plan_snapshot.json')
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'pass': bool(condition)})
        assert condition, name
    def money(x):
        v = Decimal(str(x)) * 100
        check('Raw amount exact cents', v == v.to_integral_value())
        return int(v)
    for item in p['frozen_sources']:
        check('Frozen source ' + item['path'], sha(ROOT / item['path']) == item['sha256'])
    contrib = pq.read_table(ROOT / p['contributions']).to_pylist()
    influence = pq.read_table(ROOT / p['influence']).to_pylist()
    expected = []
    for scope in ['buildings', 'motor_new']:
        rows = sorted([r for r in contrib if r['scope'] == scope and r['loss_delta'] > 0], key=lambda r: (-r['loss_delta'], r['group_id']))[:5]
        for rank, r in enumerate(rows, 1):
            expected.append(('OOF_top5_adverse_' + scope, 'motor' if scope == 'motor_new' else scope, int(r['fold']), rank, r['group_id']))
    best = {}
    for r in influence:
        key = (r['line'], r['fold'])
        order = (-abs(r['local_delete_delta_coverage_beta']), r['group_id'])
        if key not in best or order < best[key][0]:
            best[key] = (order, r['group_id'])
    for (line, fold), (_, group) in sorted(best.items()):
        expected.append(('training_top1_abs_coverage', line, int(fold), 1, group))
    chosen = pq.read_table(run / 'selection_reasons.parquet').to_pylist()
    actual = [(r['reason'], r['line'], r['fold'], r['rank'], r['group_id']) for r in chosen]
    check('Selection reconstructed without producer function', expected == actual)
    groups = {r[-1] for r in expected}
    periods = {}
    for path in p['saved_periods']:
        columns = ['market', 'line', 'row_id', 'policy_id', 'period_start', 'period_end', 'year', 'is_test', 'group_id', 'fold', 'T0', 'reserve', 'x_new_business']
        for r in pq.read_table(ROOT / path, columns=columns).to_pylist():
            if r['group_id'] not in groups:
                continue
            key = (r['market'], r['line'], r['row_id'])
            check('Selected saved period is2023 only', r['year'] == 2023 and not r['is_test'])
            check('Unique selected period', key not in periods)
            periods[key] = r
    ids = sorted({r['policy_id'] for r in periods.values()})
    raw = pq.read_table(ROOT / p['raw_claims'], filters=[('policy_id', 'in', ids),
        ('loss_date', '>=', date(2023, 1, 1)), ('loss_date', '<', date(2024, 1, 1))]).to_pylist()
    query = pq.read_table(run / 'raw_query_2023.parquet').to_pylist()
    check('Original raw query IDs exact', {r['claim_id'] for r in raw} == {r['claim_id'] for r in query})
    original_periods = {}
    for line, path in p['raw_policies'].items():
        lineids = sorted({r['policy_id'] for r in periods.values() if r['line'] == line})
        h = pq.read_table(ROOT / path, columns=['row_id', 'policy_id', 'period_start', 'period_end', 'new_business'],
            filters=[('policy_id', 'in', lineids), ('period_start', '>=', date(2023, 1, 1)), ('period_start', '<', date(2024, 1, 1))]).to_pylist()
        for r in h:
            original_periods.setdefault((line, r['policy_id']), []).append(r)
    saved = {r['claim_id']: r for r in pq.read_table(ROOT / p['claims_2023']).to_pylist() if r['group_id'] in groups}
    output = {r['claim_id']: r for r in pq.read_table(run / 'claims_original_selected_2023.parquet').to_pylist()}
    balances = {key: [0, 0] for key in periods}
    matched_ids = set()
    precoverage_ids = set()
    valuation = date.fromisoformat(p['valuation_date'])
    for r in raw:
        loss, report = day(r['loss_date']), day(r['report_date'])
        check('Independent raw temporal scope', loss.year == 2023 and loss <= report <= valuation)
        options = original_periods[(r['line'], r['policy_id'])]
        matches = [h for h in options if day(h['period_start']) <= loss <= day(h['period_end'])]
        check('Independent interval unique', len(matches) <= 1)
        if not matches:
            check('Independent precoverage justification', loss < min(day(h['period_start']) for h in options))
            precoverage_ids.add(r['claim_id'])
            continue
        key = ('emerging', r['line'], matches[0]['row_id'])
        if key not in periods:
            continue
        matched_ids.add(r['claim_id'])
        o = output[r['claim_id']]
        paid, incurred, recovery = (money(r[x]) for x in ['paid_to_date', 'incurred_to_date', 'recoveries'])
        reserve = incurred - paid
        net = paid - recovery + reserve
        for field, value in [('paid_cents', paid), ('incurred_cents', incurred), ('recoveries_cents', recovery), ('reserve_cents', reserve), ('T0_cents', net)]:
            check('Independent cents ' + field, o[field] == value)
        for field in ['policy_id', 'line', 'peril', 'status', 'repairer_id', 'third_party_id']:
            check('Original string field ' + field, o[field] == r[field])
        check('Independent linked row and group', o['row_id'] == key[2] and o['group_id'] == periods[key]['group_id'] and o['fold'] == periods[key]['fold'])
        check('Independent business flag', int(o['x_new_business']) == int(matches[0]['new_business']))
        check('Independent delay and age', o['delay_days'] == (report - loss).days and o['age_days'] == (valuation - loss).days)
        check('Independent late flag', o['late_gt365'] == ((report - loss).days > 365))
        check('Independent closed reserve flag', o['closed_with_reserve'] == (r['status'] == 'closed' and reserve > 0))
        for factor, field in [(Decimal('0.75'), 'reserve075_quarter_cent_units'), (Decimal('1.25'), 'reserve125_quarter_cent_units')]:
            quarter_units = (Decimal(paid - recovery) + Decimal(reserve) * factor) * 4
            check('Independent reserve design identity ' + str(factor), quarter_units == o[field])
        accepted = r['status'] != 'repudiated'
        check('Independent rejected exclusion', o['included_in_T0'] == accepted)
        if accepted:
            check('Original accepted claim found in saved', r['claim_id'] in saved)
            s = saved[r['claim_id']]
            for field in ['policy_id', 'line', 'peril', 'status', 'row_id', 'group_id', 'fold']:
                check('Saved identity ' + field, s[field] == o[field])
            for field in ['loss_date', 'report_date']:
                check('Saved dates ' + field, day(s[field]) == day(o[field]))
            balances[key][0] += net
            balances[key][1] += reserve
        else:
            check('Declined absent from accepted snapshot', r['claim_id'] not in saved)
    check('Exact output source claim universe', set(output) == matched_ids)
    check('Exact accepted cached claim universe', set(saved) == {k for k, r in output.items() if r['status'] != 'repudiated'})
    for key, r in periods.items():
        check('Decimal source balance T0', money(r['T0']) == balances[key][0])
        check('Decimal source balance reserve', money(r['reserve']) == balances[key][1])
    check('Precoverage source IDs exact', precoverage_ids == {r['claim_id'] for r in pq.read_table(run / 'queried_precoverage_excluded_2023.parquet').to_pylist()})
    tree = ast.parse((ROOT / p['code']).read_text(encoding='utf-8'))
    forbidden = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ['fit', 'fit_transform', 'predict', 'predict_proba', 'score']]
    check('Producer has no training or pricing calls', not forbidden)
    spec = importlib.util.spec_from_file_location('traceguard', ROOT / p['code'])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cached = pq.read_table(ROOT / p['claims_2023']).to_pandas()
    adversaries = ['year', 'duplicate', 'reserve_identity', 'date_order']
    for name in adversaries:
        fixture = cached.copy()
        if name == 'year': fixture.loc[0, 'year'] = 2024
        if name == 'duplicate': fixture.loc[1, 'claim_id'] = fixture.loc[0, 'claim_id']
        if name == 'reserve_identity': fixture.loc[0, 'reserve_cents'] += 1
        if name == 'date_order': fixture.loc[0, 'report_date'] = fixture.loc[0, 'loss_date'] - timedelta(days=1)
        caught = False
        try: module.validate_snapshot(fixture)
        except ValueError: caught = True
        check('Adverse cache rejected ' + name, caught)
    folder = run / 'adversaries_real_flow'
    folder.mkdir()
    poisoned = cached.copy(); poisoned.loc[0, 'reserve_cents'] += 1
    poison_path = folder / 'claims_poisoned_cents_2023.parquet'
    poisoned.to_parquet(poison_path, index=False)
    invalid = dict(p, id=p['id'] + '-ADVERSE-CENTS', claims_2023=rel(poison_path))
    invalid['frozen_sources'] = [x for x in p['frozen_sources'] if x['path'] != p['claims_2023']] + [{'path': rel(poison_path), 'sha256': sha(poison_path)}]
    invalid_path = folder / 'plan_poisoned_cents.json'
    invalid_path.write_text(json.dumps(invalid, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    before = set(run.parent.glob('traza_b19_*'))
    proc = subprocess.run([sys.executable, str(ROOT / p['code']), '--plan', str(invalid_path)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    (folder / 'stdout.txt').write_text(proc.stdout, encoding='utf-8')
    (folder / 'stderr.txt').write_text(proc.stderr, encoding='utf-8')
    failures = [x for x in set(run.parent.glob('traza_b19_*')) - before if (x / 'plan_snapshot.json').exists() and read(x / 'plan_snapshot.json')['id'] == invalid['id']]
    check('Actual CLI rejects poisoned cents before reconciliation outputs', proc.returncode != 0 and 'Saved reserve identity' in proc.stderr and len(failures) == 1 and not (failures[0] / 'period_reconciliation_2023.parquet').exists())
    failure = failures[0]
    check('Actual CLI failure receipt exact reason', read(failure / 'failure.json')['error'] == 'Saved reserve identity')
    (failure / 'expected_adversary_failure.json').write_text(json.dumps({'expected': True, 'author': 'Codex', 'reason': 'Synthetic one-cent reserve mismatch; original sources unmodified', 'verification': rel(run / 'verification.json'), 'new_fits': 0}, indent=2) + '\n', encoding='utf-8')
    receipt = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
               'passed': sum(x['pass'] for x in checks), 'failed': sum(not x['pass'] for x in checks), 'checks': checks,
               'expected_failure_runs': [rel(failure)], 'new_fits': 0, 'new_predictions': 0, 'new_scores': 0, 'new_bootstrap': 0,
               'professional_independent_validation': False,
               'scope': 'Separate Decimal/datetime/dictionary verification of selected source claims, interval assignment and reserve mechanics. Prior GLM/statistical suites not repeated.'}
    (run / 'verification.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ['passed', 'failed', 'expected_failure_runs', 'new_fits', 'new_scores']}, ensure_ascii=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--run', required=True)
    verify(Path(parser.parse_args().run))
