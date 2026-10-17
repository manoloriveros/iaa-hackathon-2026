"""Verificación propia separada REN00, con reconstrucción desde fuentes e importes Decimal."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def money(f, column):
    return sum((Decimal(str(x)) for x in f[column]), Decimal('0'))


def main(out):
    checks = []
    def check(name, condition):
        checks.append({'check': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    s = json.loads((out / 'summary.json').read_text('utf-8'))
    cat = json.loads((out / 'evidence/dataset_catalog.json').read_text('utf-8'))
    protected = json.loads((out / 'protected_hashes_before.json').read_text('utf-8'))
    for p, sha in protected.items():
        check('Protected source unchanged: ' + p, c.digest(ROOT / p) == sha)
    cohort = pd.read_parquet(out / 'tables/frozen_cohort.parquet')
    frozen = pd.read_parquet(out / 'evidence/D43_frozen_gaps.parquet')
    expected = frozen.loc[frozen.previous_renewal_decision.eq('declined_by_insurer')]
    key = lambda z: set(zip(z.line, z.policy_id, z.previous_row_id, z.row_id))
    check('Exact 2742 frozen D43 pair IDs, no expansion', key(cohort) == key(expected) and len(cohort) == 2742 and not cohort.policy_id.duplicated().any())
    check('Line counts 1513/1010/219', cohort.line.value_counts().to_dict() == {'motor': 1513, 'buildings': 1010, 'contents': 219})
    data = json.loads((out / 'explorer_data.json').read_text('utf-8'))
    source_history = pd.read_parquet(out / 'tables/cohort_and_control_source_histories.parquet')
    selected_ids = set(source_history.policy_id)
    minimal = []
    for line in ['motor', 'buildings', 'contents']:
        for prefix in ['policies', 'test']:
            name = prefix + '_' + line
            arrow = pq.read_table(ROOT / cat[name]['workspace_relative_path'])
            source = arrow.to_pandas()
            actual = source.loc[source.policy_id.isin(selected_ids)].copy()
            for col in ['period_start', 'period_end']:
                actual[col] = pd.to_datetime(actual[col])
            recorded = source_history.loc[source_history.source_table.eq(name)].copy()
            check('Complete source rows preserved in diagnostic history: ' + name, set(actual.row_id) == set(recorded.row_id))
            fields = [col for col in arrow.column_names if col != 'row_id']
            pd.testing.assert_frame_equal(actual.set_index('row_id')[fields].sort_index(),
                recorded.set_index('row_id')[fields].sort_index(), check_dtype=False, check_exact=True)
            check('Every original field in diagnostic history equals current source: ' + name, True)
            fields = ['row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end', 'renewal_count', 'new_business', 'exposure']
            if prefix == 'policies':
                fields.append('renewal_decision')
            light = source[fields].copy()
            light['line'] = line
            for col in ['period_start', 'period_end']:
                light[col] = pd.to_datetime(light[col])
            light['year'] = light.period_start.dt.year
            minimal.append(light)
    f = pd.concat(minimal, ignore_index=True).sort_values(['line', 'policy_id', 'period_start', 'period_end', 'row_id'])
    gg = f.groupby(['line', 'policy_id'], sort=False)
    for col in ['year', 'row_id', 'period_start']:
        f['n_' + col] = gg[col].shift(-1)
    declined = f.loc[f.renewal_decision.eq('declined_by_insurer')]
    got = declined.loc[declined.year.eq(2024) & declined.n_year.eq(2025)]
    check('Fresh full-source adjacency reproduces cohort', set(zip(got.row_id, got.n_row_id)) == set(zip(cohort.previous_row_id, cohort.row_id)))
    annual = pd.read_parquet(out / 'tables/decision_successors_all_years.parquet')
    for (line, year), z in declined.groupby(['line', 'year']):
        r = annual.loc[annual.line.eq(line) & annual.year.eq(year) & annual.renewal_decision.eq('declined_by_insurer')].iloc[0]
        check(f'Historical successor counts independently reproduced {line}/{year}', len(z) == r.rows and int(z.n_row_id.notna().sum()) == r.successors and int(z.n_year.eq(year + 1).sum()) == r.next_year)
    check('3002 declined 2024, 260 without observed successor', len(declined.loc[declined.year.eq(2024)]) == 3002 and int(declined.loc[declined.year.eq(2024), 'n_row_id'].isna().sum()) == 260)
    before = f.set_index('row_id').loc[cohort.previous_row_id].reset_index()
    after = f.set_index('row_id').loc[cohort.row_id].reset_index()
    check('Same customer, no new business, counter increases one in every pair', (before.customer_id.to_numpy() == after.customer_id.to_numpy()).all() and not after.new_business.any() and np.all(after.renewal_count.to_numpy() - before.renewal_count.to_numpy() == 1))
    moved = before.address_id.to_numpy() != after.address_id.to_numpy()
    check('Exactly 22 motor address changes, not 2742 constant addresses', int(moved.sum()) == 22 and cohort.loc[moved, 'line'].eq('motor').all())
    check('Published endpoints and calendar gap preserved', before.period_end.eq(pd.Timestamp('2024-12-30')).all() and after.period_start.eq(pd.Timestamp('2025-01-01')).all())
    hist = pd.read_parquet(out / 'tables/cohort_policy_histories.parquet')
    check('All 12041 cohort periods and 2931 test rows', len(hist) == 12041 and hist.year.eq(2025).sum() == 2931 and set(hist.row_id) == set(f.loc[f.policy_id.isin(cohort.policy_id), 'row_id']))
    check('2025 claim diagnostics stay missing, not synthetic zero outcomes', hist.loc[hist.year.eq(2025), ['observed_claim_records', 'accepted_claims', 'net_accepted_cents']].isna().all().all())
    repeat = hist.loc[hist.renewal_decision.eq('declined_by_insurer')].groupby('policy_id').size()
    check('83 multiple declines, two with three, exact histories', int(repeat.gt(1).sum()) == 83 and int(repeat.eq(3).sum()) == 2)
    # Verify all original claim payloads independently of exported net/cents columns.
    raw = pd.read_parquet(ROOT / cat['claims']['workspace_relative_path'])
    original_columns = raw.columns.tolist()
    for col in ['loss_date', 'report_date']:
        raw[col] = pd.to_datetime(raw[col])
    selected_raw = raw.loc[raw.policy_id.isin(selected_ids)].copy()
    recorded_claims = pd.read_parquet(out / 'tables/cohort_and_control_claim_histories.parquet')
    fields = [col for col in original_columns if col != 'claim_id']
    pd.testing.assert_frame_equal(selected_raw.set_index('claim_id')[fields].sort_index(),
        recorded_claims.set_index('claim_id')[fields].sort_index(), check_dtype=False, check_exact=True)
    check('All selected source claim fields and IDs preserved exactly', len(selected_raw) == len(recorded_claims))
    claims = raw.merge(pd.read_parquet(out / 'evidence/D42_claim_assignment.parquet')[['claim_id', 'row_id']], on='claim_id', validate='one_to_one')
    cohort_claims = claims.loc[claims.policy_id.isin(cohort.policy_id)]
    check('3928 full historical cohort claims, all original DUP01 records', len(cohort_claims) == 3928 and set(cohort_claims.claim_id) == set(pd.read_parquet(out / 'tables/cohort_claim_histories.parquet').claim_id))
    pairs = selected_raw[['claim_id', 'line', 'policy_id', 'loss_date']].merge(
        source_history[['row_id', 'line', 'policy_id', 'period_start', 'period_end']], on=['line', 'policy_id'])
    hits = pairs.loc[pairs.loss_date.between(pairs.period_start, pairs.period_end)]
    check('Unique interval matches, no calendar repair used', not hits.claim_id.duplicated().any())
    lookup = hits.set_index('claim_id').row_id
    recorded = recorded_claims.set_index('claim_id').row_id
    check('Fresh loss-date assignment equals exported histories and DUP01', recorded.fillna('NONE').equals(lookup.reindex(recorded.index).fillna('NONE')))
    prior = claims.loc[claims.row_id.isin(cohort.previous_row_id)]
    check('2855 preceding-row claims, 2850 accepted, five repudiated', len(prior) == 2855 and prior.status.isin(['open', 'closed']).sum() == 2850 and prior.status.eq('repudiated').sum() == 5)
    profile = pd.read_parquet(out / 'tables/cohort_profile.parquet')
    for line in ['motor', 'buildings', 'contents', 'ALL']:
        z = prior if line == 'ALL' else prior.loc[prior.line.eq(line)]
        acc = z.loc[z.status.isin(['open', 'closed'])]
        net = money(acc, 'incurred_to_date') - money(acc, 'recoveries')
        op = z.loc[z.status.eq('open')]
        reserve = money(op, 'incurred_to_date') - money(op, 'paid_to_date')
        r = profile.loc[profile.line.eq(line)].iloc[0]
        check('Independent Decimal accepted net and open reserve: ' + line,
              net == Decimal(str(r.last_2024_net_CU)) and reserve == Decimal(str(r.last_2024_open_reserve_CU)))
    check('58932110.98 CU exact observed net in preceding rows', money(prior.loc[prior.status.isin(['open','closed'])], 'incurred_to_date') - money(prior.loc[prior.status.isin(['open','closed'])], 'recoveries') == Decimal('58932110.98'))
    ids_2024_claims = set(cohort_claims.loc[cohort_claims.loss_date.dt.year.eq(2024), 'policy_id'])
    check('372 policies without any observed 2024 occurrence', sum(pid not in ids_2024_claims for pid in cohort.policy_id) == 372)
    year_rows = f.loc[f.year.eq(2024)]
    year_claims = claims.loc[claims.row_id.isin(year_rows.row_id) & claims.status.isin(['open', 'closed'])]
    year_cost = money(year_claims, 'incurred_to_date') - money(year_claims, 'recoveries')
    total = profile.loc[profile.line.eq('ALL')].iloc[0]
    check('All 2024 baseline cost reconciles with Decimal and current claims', year_cost == Decimal(str(total.base_2024_net_CU)))
    check('Cost concentration uses 2024 assigned cost as denominator', abs(float(Decimal('58932110.98') / year_cost * 100) - s['preceding_cost_share_2024_pct']) < 1e-9)
    sensitivity = pd.read_parquet(out / 'tables/exclusion_sensitivity_NOT_APPLIED.parquet')
    for r in sensitivity.itertuples():
        drop = cohort.previous_row_id if r.hypothetical_scope == 'delete_preceding_2742_rows' else f.loc[f.year.eq(2024) & f.policy_id.isin(cohort.policy_id), 'row_id']
        cc = year_claims.loc[year_claims.row_id.isin(drop)]
        removed = money(cc, 'incurred_to_date') - money(cc, 'recoveries')
        removed_exp = float(f.loc[f.row_id.isin(drop), 'exposure'].sum())
        rate_before = float(year_cost) / float(year_rows.exposure.sum())
        rate_after = float(year_cost - removed) / (float(year_rows.exposure.sum()) - removed_exp)
        check('Hypothetical exclusion arithmetic, never applied: ' + r.hypothetical_scope,
              removed == Decimal(str(r.observed_net_removed_CU)) and abs(removed_exp - r.exposure_removed) < 1e-8 and abs((rate_after / rate_before - 1) * 100 - r.observed_rate_change_pct) < 1e-8 and not r.applied)
    check('Explorer includes every cohort policy and only two controls extra', {x['policy_id'] for x in data['index']} == set(cohort.policy_id) and set(data['histories']) == selected_ids and len(selected_ids) == 2744)
    check('Twelve distinct cases, ten in cohort and two controls', len(data['cases']) == 12 and len({x['policy_id'] for x in data['cases']}) == 12 and sum(not x['cohort_member'] for x in data['cases']) == 2)
    for pid, h in data['histories'].items():
        assert set(p['row_id'] for p in h['policies']) == set(source_history.loc[source_history.policy_id.eq(pid), 'row_id']), pid
        assert set(p['claim_id'] for p in h['claims']) == set(raw.loc[raw.policy_id.eq(pid), 'claim_id']), pid
    check('Every explorer entry has complete source policy and claim histories', True)
    report = (out / 'informe.html').read_text('utf-8')
    embedded = re.search(r'<script id="reviewData" type="application/json">(.*?)</script>', report, re.S)
    check('Embedded explorer exactly equals evidence JSON', embedded is not None and json.loads(embedded.group(1)) == data)
    for ref in re.findall(r'(?:href|src)="([^"]+)"', report):
        if ref.startswith(('#','http')) or ref in ['verification.json', 'manifest.json', 'interface_verification.json']:
            continue
        check('Local report link exists: ' + ref, (out / ref).is_file())
    check('Report complete without template tokens', '@@' not in report)
    check('No new active catalog or corrected dataset', not (out / 'data').exists() and not (out / 'dataset_catalog.json').exists())
    check('Calendar remains pending; no data changes, training or independent claims', s['dates_pending'] and not any(s[k] for k in ['dates_modified','exposures_modified','decisions_modified','claims_modified','active_dataset_changed','models_trained','independent_validation']))
    result = {'status': 'passed_own_verification', 'created_utc': datetime.now(timezone.utc).isoformat(), 'passed': len(checks),
        'failed': 0, 'checks': checks, 'independent_validation': False, 'real_browser_rendering': False}
    if (out / 'manifest.json').exists():
        m = json.loads((out / 'manifest.json').read_text('utf-8'))
        assert all(c.digest(out / e['path']) == e['sha256'] for e in m['files'])
    else:
        c.dump(out / 'verification.json', result)
    print(json.dumps({'status': result['status'], 'passed': result['passed'], 'failed': 0}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
