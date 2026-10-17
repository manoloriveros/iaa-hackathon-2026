"""Comprobaciones propias separadas para CAL00; ninguna transformación activa."""
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main(out):
    checks = []
    def check(name, condition):
        checks.append({'check': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    summary = json.loads((out / 'summary.json').read_text('utf-8'))
    protected = json.loads((out / 'protected_hashes_before.json').read_text('utf-8'))
    for path, sha in protected.items():
        check('Unchanged protected file: ' + path, c.digest(ROOT / path) == sha)
    cat = json.loads((out / 'evidence/dataset_catalog.json').read_text('utf-8'))
    policy = []
    for line in ['motor', 'buildings', 'contents']:
        for prefix in ['policies', 'test']:
            name = prefix + '_' + line
            p = pq.read_table(ROOT / cat[name]['workspace_relative_path'], columns=['row_id', 'policy_id', 'customer_id',
                'address_id', 'period_start', 'period_end', 'exposure']).to_pandas()
            p['line'] = line
            p['period_start'] = pd.to_datetime(p.period_start); p['period_end'] = pd.to_datetime(p.period_end)
            policy.append(p)
    f = pd.concat(policy, ignore_index=True).sort_values(['line', 'policy_id', 'period_start', 'period_end', 'row_id'])
    gg = f.groupby(['line', 'policy_id'], sort=False)
    oldend = gg.period_end.shift(); oldrow = gg.row_id.shift()
    gap = (f.period_start - oldend).dt.days - 1
    own = f.loc[gap > 0, ['line', 'row_id']].copy(); own['previous_row_id'] = oldrow.loc[gap > 0]
    cohort = pd.read_parquet(out / 'tables/gap_cohort.parquet')
    frozen = pd.read_parquet(out / 'evidence/D40_frozen_calendar_gaps.parquet')
    keys = lambda z: set(zip(z.line, z.row_id, z.previous_row_id))
    check('Independent full-source adjacency equals current diagnostic cohort', keys(own) == keys(cohort))
    check('Cohort equals frozen D40 pair IDs', keys(cohort) == keys(frozen))
    check('500245 one-day gaps, one per policy', len(cohort) == 500245 and cohort.policy_id.nunique() == 500245 and (cohort.gap_days == 1).all())
    check('No other positive gaps or overlaps', int((gap > 0).sum()) == 500245 and not (gap < 0).any())
    check('Current EXP01 preserved, dates inclusive', np.allclose(f.exposure, ((f.period_end - f.period_start).dt.days.add(1) / 365).round(4), rtol=0, atol=1e-10))
    for col in ['period_start', 'previous_period_end', 'previous_period_start']:
        cohort[col] = pd.to_datetime(cohort[col])
    check('Endpoints exactly Dec30 to Jan1', (cohort.previous_period_end == pd.Timestamp('2024-12-30')).all() and (cohort.period_start == pd.Timestamp('2025-01-01')).all())
    before = f.set_index('row_id').loc[cohort.previous_row_id].reset_index()
    after = f.set_index('row_id').loc[cohort.row_id].reset_index()
    same_customer = before.customer_id.to_numpy() == after.customer_id.to_numpy()
    same_address = before.address_id.to_numpy() == after.address_id.to_numpy()
    check('All customers preserved, exactly 3153 motor address changes', same_customer.all() and int((~same_address).sum()) == 3153 and cohort.loc[~same_address, 'line'].eq('motor').all())
    check('Stored address comparison equals source endpoints', np.array_equal(same_address, cohort.same_address.to_numpy()))
    risk = pd.read_parquet(out / 'tables/risk_context_comparison.parquet')
    check('Motor model, cover and value group stable in compared endpoints', risk.loc[risk.line == 'motor', ['same_make_model', 'same_cover_type', 'same_vehicle_value_group']].all().all())
    check('Exactly all Dec30 endings have successors, no silent extra cohort', set(before.row_id) == set(f.loc[f.period_end == pd.Timestamp('2024-12-30'), 'row_id']))
    check('2024 coverage never reaches Dec31', not ((f.period_start <= pd.Timestamp('2024-12-31')) & (f.period_end >= pd.Timestamp('2024-12-31'))).any())
    check('497503 renewed, 2742 declined', cohort.previous_renewal_decision.value_counts().to_dict() == {'renewed': 497503, 'declined_by_insurer': 2742})
    ah = pd.read_parquet(out / 'tables/all_affected_policy_histories.parquet')
    check('Complete source policy history for all cohort policies', set(ah.row_id) == set(f.loc[f.policy_id.isin(cohort.policy_id), 'row_id']) and len(ah) == summary['all_affected_history_rows'])
    claims = pd.read_parquet(ROOT / cat['claims']['workspace_relative_path'])
    for col in ['loss_date', 'report_date']:
        claims[col] = pd.to_datetime(claims[col])
    ac = pd.read_parquet(out / 'tables/all_affected_claim_histories.parquet')
    check('Complete current DUP01 claim history, not original duplicates', set(ac.claim_id) == set(claims.loc[claims.policy_id.isin(cohort.policy_id), 'claim_id']) and len(claims) == 162546)
    check('Claims loss cutoff and report cutoff separately confirmed', claims.loss_date.max() == pd.Timestamp('2024-12-29') and claims.report_date.max() == pd.Timestamp('2024-12-30'))
    check('Minimum observed reporting delay one day', (claims.report_date - claims.loss_date).dt.days.min() == 1)
    check('111 Dec30 reports, no Dec31 reports', int((claims.report_date == pd.Timestamp('2024-12-30')).sum()) == 111 and not (claims.report_date == pd.Timestamp('2024-12-31')).any())
    check('Zero Dec30 and Dec31 loss records; not evidence of zero risk', not claims.loss_date.isin(pd.to_datetime(['2024-12-30', '2024-12-31'])).any())
    check('Leap day is present in claims', int((claims.loss_date == pd.Timestamp('2024-02-29')).sum()) == 90)
    assignment = pd.read_parquet(out / 'evidence/D42_claim_assignment.parquet')
    current = assignment.loc[assignment.row_id.notna(), ['claim_id', 'row_id']].merge(
        claims[['claim_id', 'policy_id', 'line', 'loss_date']], on='claim_id', validate='one_to_one').merge(
        f[['row_id', 'policy_id', 'line', 'period_start', 'period_end']], on=['row_id', 'policy_id', 'line'], validate='many_to_one')
    check('Every prior assigned claim independently inside unchanged source interval', len(current) == int(assignment.row_id.notna().sum()) and current.loss_date.between(current.period_start, current.period_end).all())
    check('413 prehistory records remain separate', int(assignment.row_id.isna().sum()) == 413)
    daily = pd.read_parquet(out / 'tables/daily_calendar.parquet')
    check('Daily coverage sums reconcile all inclusive policy days', int(daily.covered_policy_rows.sum()) == int((f.period_end - f.period_start).dt.days.add(1).sum()))
    for line in ['motor', 'buildings', 'contents']:
        for year in range(2021, 2026):
            x = daily.loc[(daily.line == line) & (daily.year == year)]
            sub = claims.loc[claims.line == line]
            check(f'Daily claim counts reconcile {line}/{year}', int(x.loss_records.sum()) == int((sub.loss_date.dt.year == year).sum()) and int(x.report_records.sum()) == int((sub.report_date.dt.year == year).sum()))
    sc = pd.read_parquet(out / 'tables/hypothetical_exposure_scenarios.parquet')
    for r in sc.itertuples():
        z = cohort if r.line == 'ALL' else cohort.loc[cohort.line == r.line]
        if r.scenario == 'bridge_consistent_renewed':
            z = z.loc[z.consistent_renewed_label]
        ndays = (z.previous_period_end - z.previous_period_start).dt.days + 1
        recalculated_delta = float((((ndays + 1) / 365).round(4) - (ndays / 365).round(4)).sum())
        check(f'Exposure arithmetic independently recomputed {r.line}/{r.scenario}', r.rows == len(z) and abs(r.ACT365_unrounded_extra_years - len(z) / 365) < 1e-9 and abs(r.ACT365_row_rounded_extra_years - recalculated_delta) < 1e-9)
    cases = json.loads((out / 'cases.json').read_text('utf-8'))
    check('Thirteen distinct real cases', len(cases) == 13 and len({x['case']['policy_id'] for x in cases}) == 13)
    cp = pd.read_parquet(out / 'tables/case_policy_histories.parquet')
    cc = pd.read_parquet(out / 'tables/case_claim_histories.parquet')
    for item in cases:
        pid = item['case']['policy_id']
        check('Full case history and raw claim dates ' + pid, set(r['row_id'] for r in item['policies']) == set(f.loc[f.policy_id == pid, 'row_id']) and set(r['claim_id'] for r in item['claims']) == set(claims.loc[claims.policy_id == pid, 'claim_id']))
    control = [x for x in cases if x['case']['label'].startswith('Control:')]
    check('A genuine cancellation control remains outside gap cohort', len(control) == 1 and control[0]['case']['policy_id'] not in set(cohort.policy_id))
    report = (out / 'informe.html').read_text('utf-8')
    check('No unresolved template tokens', '@@' not in report)
    embedded = re.search(r'<script id="caseData" type="application/json">(.*?)</script>', report, re.S)
    check('Embedded histories equal verified cases', embedded is not None and json.loads(embedded.group(1)) == cases)
    for ref in re.findall(r'(?:href|src)="([^"]+)"', report):
        if ref.startswith(('#', 'http')) or ref in ['verification.json', 'manifest.json']:
            continue
        check('Report local link exists: ' + ref, (out / ref).is_file())
    check('No active data output or new dataset catalog', not (out / 'data').exists() and not (out / 'dataset_catalog.json').exists())
    check('Summary accurately states review only', not any(summary[k] for k in ['dates_modified', 'exposure_modified', 'claims_modified', 'active_dataset_changed', 'models_trained', 'independent_validation']))
    result = {'status': 'passed_own_verification', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'checks': checks, 'passed': len(checks), 'failed': 0, 'independent_validation': False,
        'browser_rendering_verified': False, 'figure_visual_inspection': 'recorded separately at closure'}
    if (out / 'manifest.json').exists():
        manifest = json.loads((out / 'manifest.json').read_text('utf-8'))
        assert all(c.digest(out / e['path']) == e['sha256'] for e in manifest['files'])
    else:
        c.dump(out / 'verification.json', result)
    print(json.dumps({'status': result['status'], 'passed': len(checks), 'failed': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
