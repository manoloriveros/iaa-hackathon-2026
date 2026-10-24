"""Traza financiera y temporal focal de B19. No importa modelos ni calcula scores."""
from pathlib import Path
from datetime import datetime, date, timezone
import argparse
import hashlib
import json
import platform
import sys
import uuid

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO.parents[1]
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

KEY = ['market', 'line', 'row_id']
MONEY = ['paid', 'incurred', 'recoveries', 'reserve', 'T0']
RAW = ['claim_id', 'policy_id', 'line', 'peril', 'loss_date', 'report_date', 'status',
       'paid_to_date', 'incurred_to_date', 'recoveries', 'repairer_id', 'third_party_id']
PBASE = KEY + ['policy_id', 'period_start', 'period_end', 'year', 'is_test', 'group_id',
               'fold', 'T0', 'reserve', 'x_new_business']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))


def dump(path, x):
    with path.open('x', encoding='utf-8') as f:
        json.dump(x, f, ensure_ascii=False, indent=2,
                  default=lambda v: v.item() if hasattr(v, 'item') else str(v))
        f.write('\n')


def require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def cents(s):
    x = pd.to_numeric(s, errors='raise').to_numpy(dtype=float)
    require(np.isfinite(x).all(), 'Nonfinite money')
    y = np.rint(x * 100)
    require(np.max(np.abs(x * 100 - y), initial=0) < 1e-5, 'Noncent money')
    return y.astype('int64')


def selections(contrib, influence):
    rows = []
    for scope in ['buildings', 'motor_new']:
        g = contrib[contrib.scope.eq(scope) & contrib.loss_delta.gt(0)].sort_values(
            ['loss_delta', 'group_id'], ascending=[False, True], kind='stable').head(5)
        for rank, item in enumerate(g.itertuples(), 1):
            rows.append({'reason': 'OOF_top5_adverse_' + scope, 'line': 'motor' if scope == 'motor_new' else scope,
                         'fold': int(item.fold), 'rank': rank, 'group_id': item.group_id})
    for (line, fold), g in influence.groupby(['line', 'fold'], sort=True):
        h = g.assign(magnitude=g.local_delete_delta_coverage_beta.abs()).sort_values(
            ['magnitude', 'group_id'], ascending=[False, True], kind='stable').iloc[0]
        rows.append({'reason': 'training_top1_abs_coverage', 'line': line, 'fold': int(fold),
                     'rank': 1, 'group_id': h.group_id})
    return pd.DataFrame(rows)


def validate_snapshot(c):
    require(c.year.eq(2023).all(), 'Claim policy year outside2023')
    require(c.claim_id.is_unique and c.claim_id.notna().all(), 'Duplicate/missing saved claim')
    require(c.included_in_T0.all() and c.status.ne('repudiated').all(), 'Invalid accepted saved scope')
    loss = pd.to_datetime(c.loss_date, errors='raise')
    report = pd.to_datetime(c.report_date, errors='raise')
    require(loss.notna().all() and report.notna().all() and loss.dt.year.eq(2023).all(), 'Saved loss date scope')
    require(report.ge(loss).all() and report.le(pd.Timestamp('2024-12-31')).all(), 'Saved date order or valuation')
    require(c[[m + '_cents' for m in MONEY]].ge(0).all().all(), 'Saved negative money')
    require((c.incurred_cents - c.paid_cents).eq(c.reserve_cents).all(), 'Saved reserve identity')
    require((c.incurred_cents - c.recoveries_cents).eq(c.T0_cents).all(), 'Saved net identity')
    require((c.paid_cents + c.reserve_cents - c.recoveries_cents).eq(c.T0_cents).all(), 'Saved cash decomposition')


def materialize(plan_path):
    p = read(plan_path)
    run = REPO / 'privado/semana2/desarrollo2023' / ('traza_b19_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    (run / 'plan_snapshot.json').write_bytes(plan_path.read_bytes())
    (run / 'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'pass': bool(condition)})
        require(condition, name)
    try:
        for x in p['frozen_sources']:
            check('Frozen source ' + x['path'], sha(ROOT / x['path']) == x['sha256'])
        influence = pq.read_table(ROOT / p['influence']).to_pandas()
        contrib = pq.read_table(ROOT / p['contributions']).to_pandas()
        selection = selections(contrib, influence)
        selection.to_parquet(run / 'selection_reasons.parquet', index=False)
        groups = set(selection.group_id)
        check('Fixed selection has at most20 unique components', 0 < len(groups) <= 20)
        frames = [pq.read_table(ROOT / path, columns=PBASE).to_pandas() for path in p['saved_periods']]
        periods = pd.concat(frames, ignore_index=True)
        check('Saved period scope', periods.year.eq(2023).all() and not periods.is_test.any())
        check('Saved unique period keys', not periods.duplicated(KEY).any())
        periods = periods[periods.group_id.isin(groups)].copy()
        check('Every selected group has saved periods', set(periods.group_id) == groups)
        check('One saved fold per group', periods.groupby('group_id').fold.nunique().eq(1).all())
        cached = pq.read_table(ROOT / p['claims_2023']).to_pandas()
        validate_snapshot(cached)
        check('Saved claim financial identities and2023scope', True)
        cached = cached[cached.group_id.isin(groups)].copy()
        check('Selected claim groups contained', set(cached.group_id).issubset(groups))
        raw = pq.read_table(ROOT / p['raw_claims'], columns=RAW, filters=[
            ('policy_id', 'in', sorted(set(periods.policy_id))),
            ('loss_date', '>=', date(2023, 1, 1)), ('loss_date', '<', date(2024, 1, 1))]).to_pandas()
        check('Raw claims unique', raw.claim_id.is_unique)
        raw['market'] = 'emerging'
        for col in ['loss_date', 'report_date']:
            raw[col] = pd.to_datetime(raw[col], errors='raise')
        check('Raw loss years only2023', raw.loss_date.dt.year.eq(2023).all())
        check('Raw temporal order and valuation', raw.report_date.ge(raw.loss_date).all() and raw.report_date.le(pd.Timestamp(p['valuation_date'])).all())
        for col, src in [('paid', 'paid_to_date'), ('incurred', 'incurred_to_date'), ('recoveries', 'recoveries')]:
            raw[col + '_cents'] = cents(raw[src])
        raw['reserve_cents'] = raw.incurred_cents - raw.paid_cents
        raw['T0_cents'] = raw.incurred_cents - raw.recoveries_cents
        check('Raw monetary contract', raw[[m + '_cents' for m in MONEY]].ge(0).all().all())
        check('Raw status known', raw.status.isin(['closed', 'open', 'repudiated']).all())
        policy_rows = []
        for line, path in p['raw_policies'].items():
            cols = ['row_id', 'policy_id', 'period_start', 'period_end', 'new_business']
            h = pq.read_table(ROOT / path, columns=cols, filters=[
                ('policy_id', 'in', sorted(set(periods.loc[periods.line.eq(line), 'policy_id']))),
                ('period_start', '>=', date(2023, 1, 1)), ('period_start', '<', date(2024, 1, 1))]).to_pandas()
            h['market'] = 'emerging'; h['line'] = line
            for col in ['period_start', 'period_end']:
                h[col] = pd.to_datetime(h[col], errors='raise')
            check('Raw policy years ' + line, h.period_start.dt.year.eq(2023).all() and h.period_end.dt.year.eq(2023).all())
            policy_rows.append(h)
        original_periods = pd.concat(policy_rows, ignore_index=True)
        check('Original period keys unique', not original_periods.duplicated(KEY).any())
        mapped = periods.merge(original_periods, on=KEY, how='left', validate='one_to_one', suffixes=('', '_raw'), indicator=True)
        check('Saved periods found in original2023', mapped._merge.eq('both').all())
        check('Policy identities and intervals exact', mapped.policy_id.eq(mapped.policy_id_raw).all() and
              pd.to_datetime(mapped.period_start).eq(mapped.period_start_raw).all() and pd.to_datetime(mapped.period_end).eq(mapped.period_end_raw).all())
        check('Business flags exact', mapped.x_new_business.astype(float).eq(mapped.new_business.astype(float)).all())
        candidates = raw.merge(original_periods[['market', 'line', 'policy_id', 'row_id', 'period_start', 'period_end']],
                               on=['market', 'line', 'policy_id'], how='left')
        matches = candidates[candidates.loss_date.ge(candidates.period_start) & candidates.loss_date.le(candidates.period_end)].copy()
        check('Original interval assignments unambiguous', matches.claim_id.is_unique)
        unassigned = raw[~raw.claim_id.isin(matches.claim_id)].copy()
        bounds = original_periods.groupby(['market', 'line', 'policy_id'], as_index=False).period_start.min()
        unassigned = unassigned.merge(bounds, on=['market', 'line', 'policy_id'], how='left', validate='many_to_one')
        check('Only justified precoverage outside original2023 intervals', unassigned.period_start.notna().all() and unassigned.loss_date.lt(unassigned.period_start).all())
        unassigned.to_parquet(run / 'queried_precoverage_excluded_2023.parquet', index=False)
        linked = matches.merge(periods[KEY + ['group_id', 'fold', 'x_new_business']], on=KEY, how='inner', validate='many_to_one')
        linked['included_in_T0'] = linked.status.ne('repudiated')
        accepted = linked[linked.included_in_T0].copy()
        check('Exact accepted selected claim universe', set(accepted.claim_id) == set(cached.claim_id))
        both = cached.merge(accepted, on='claim_id', how='outer', suffixes=('_saved', '_raw'), validate='one_to_one', indicator=True)
        check('Saved/raw claim universe exact', both._merge.eq('both').all())
        for col in ['policy_id', 'line', 'peril', 'status', *KEY[:1], 'row_id', 'group_id', 'fold', 'x_new_business'] + [m + '_cents' for m in MONEY]:
            check('Saved/raw exact ' + col, both[col + '_saved'].eq(both[col + '_raw']).all())
        for col in ['loss_date', 'report_date']:
            check('Saved/raw exact ' + col, pd.to_datetime(both[col + '_saved']).eq(pd.to_datetime(both[col + '_raw'])).all())
        linked['delay_days'] = (linked.report_date - linked.loss_date).dt.days
        linked['age_days'] = (pd.Timestamp(p['valuation_date']) - linked.loss_date).dt.days
        linked['late_gt365'] = linked.delay_days.gt(365)
        linked['closed_with_reserve'] = linked.status.eq('closed') & linked.reserve_cents.gt(0)
        linked['net_paid_cents'] = linked.paid_cents - linked.recoveries_cents
        linked['reserve075_quarter_cent_units'] = 4 * linked.T0_cents - linked.reserve_cents
        linked['reserve125_quarter_cent_units'] = 4 * linked.T0_cents + linked.reserve_cents
        accepted = linked[linked.included_in_T0].copy()
        sums = accepted.groupby(KEY)[[m + '_cents' for m in MONEY]].sum().reset_index()
        rec = periods.merge(sums, on=KEY, how='left', validate='one_to_one')
        for m in MONEY:
            rec[m + '_cents'] = rec[m + '_cents'].fillna(0).astype('int64')
        check('Selected saved period T0 exact from original cash', np.array_equal(cents(rec.T0), rec.T0_cents.to_numpy()))
        check('Selected saved period reserve exact', np.array_equal(cents(rec.reserve), rec.reserve_cents.to_numpy()))
        check('Net cash plus reserve exact', (accepted.net_paid_cents + accepted.reserve_cents).eq(accepted.T0_cents).all())
        # Preserve admitted/declined records separately; no correction or new target is adopted.
        linked.to_parquet(run / 'claims_original_selected_2023.parquet', index=False)
        cached.to_parquet(run / 'claims_saved_selected_2023.parquet', index=False)
        raw.to_parquet(run / 'raw_query_2023.parquet', index=False)
        original_periods.to_parquet(run / 'raw_period_query_2023.parquet', index=False)
        rec.to_parquet(run / 'period_reconciliation_2023.parquet', index=False)
        group = accepted.groupby(['line', 'group_id', 'fold'], as_index=False).agg(
            claims=('claim_id', 'size'), paid_cents=('paid_cents', 'sum'), incurred_cents=('incurred_cents', 'sum'),
            recoveries_cents=('recoveries_cents', 'sum'), reserve_cents=('reserve_cents', 'sum'), T0_cents=('T0_cents', 'sum'),
            open_claims=('status', lambda x: int(x.eq('open').sum())), late_claims=('late_gt365', 'sum'),
            closed_with_reserve=('closed_with_reserve', 'sum'), max_delay_days=('delay_days', 'max'))
        group.to_parquet(run / 'group_financial_trace_2023.parquet', index=False)
        report = {'id': p['id'], 'author': 'Codex', 'completed_utc': datetime.now(timezone.utc).isoformat(),
                  'run': rel(run), 'selected_groups': len(groups), 'selected_periods': len(periods),
                  'queried_original_claims': len(raw), 'selected_accepted_claims': len(accepted),
                  'selected_declined_claims': int(linked.status.eq('repudiated').sum()),
                  'passed': len(checks), 'failed': 0, 'checks': checks,
                  'new_fits': 0, 'new_models': 0, 'new_predictions': 0, 'new_scores': 0, 'new_bootstrap': 0,
                  'valuation_date': p['valuation_date'], 'reference': 'W2-B00', 'all_alternatives_preserved': True,
                  'policy_years': [2023], 'report_dates_in_2024_are_valuation_history_not_2024_pricing': True,
                  'ledger_read': False, 'professional_independent_validation': False,
                  'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'pyarrow': pa.__version__}}
        dump(run / 'report.json', report)
        files = [x for x in run.rglob('*') if x.is_file()]
        dump(run / 'manifest.json', {'files': [{'path': rel(x), 'sha256': sha(x), 'bytes': x.stat().st_size} for x in sorted(files)]})
        print(json.dumps({k: report[k] for k in ['run', 'selected_groups', 'selected_periods', 'selected_accepted_claims', 'passed', 'failed', 'new_fits', 'new_scores']}, ensure_ascii=True))
        return run
    except Exception as exc:
        dump(run / 'failure.json', {'utc': datetime.now(timezone.utc).isoformat(), 'error': str(exc), 'checks': checks,
                                   'new_fits': 0, 'new_scores': 0, 'run': rel(run)})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    args = parser.parse_args()
    materialize(Path(args.plan))
