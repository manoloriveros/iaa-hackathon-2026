"""Relectura de fuentes y conciliación independiente por joins del conjunto descriptivo."""
from pathlib import Path
from decimal import Decimal
from html.parser import HTMLParser
import json
import sys
import review_endorsements as a
import clean_data as c
import pandas as pd
import numpy as np
import pyarrow.parquet as pq


def same(x, y):
    return (pd.isna(x) and pd.isna(y)) or (pd.notna(x) and pd.notna(y) and x == y)


def main(out):
    assert not (out/'manifest.json').exists()
    checks = []
    def check(label, ok):
        checks.append({'check': label, 'passed': bool(ok)})
        if not ok:
            c.dump(out/'verification_failure.json', {'checks': checks, 'status': 'failed_not_closed'})
            raise AssertionError(label)
    read = lambda name: pd.read_parquet(out/'tables'/(name+'.parquet'))
    cat = json.loads((out/'evidence/dataset_catalog.json').read_text('utf-8'))
    idx = json.loads((out/'evidence/retrospective_index.json').read_text('utf-8'))
    h, raw, f = read('all_policy_histories'), read('all_original_policy_histories'), read('assessment_2')
    pending = pd.read_parquet(out/'evidence/frozen_421_pending.parquet')
    protected = json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    check('All protected original, catalog, index, protocol and guard hashes unchanged', all(c.digest(c.ROOT/path) == sha for path, sha in protected.items()))
    check('CAP05R and D57 manifests intact', a.cap.manifest_ok(c.ROOT/idx['workspace_relative_run']) and a.cap.manifest_ok(a.REVIEW))
    check('Exactly eight unique train periods, two policies and two pending rows', len(h) == h.row_id.nunique() == 8 and set(h.policy_id) == set(a.PIDS) and h.source_table.eq('policies_contents').all() and len(f) == 2 and set(f.row_id) == set(a.FOCUS) and set(a.FOCUS).issubset(set(pending.row_id)) and len(pending) == 421)
    for name in ['policies_contents', 'test_contents']:
        actual = a.dates(pq.read_table(c.ROOT/cat[name]['workspace_relative_path'], filters=[('policy_id', 'in', a.PIDS)]).to_pandas()).set_index('row_id')
        original = a.dates(pq.read_table(c.RAW/(name+'.parquet'), filters=[('policy_id', 'in', a.PIDS)]).to_pandas()).set_index('row_id')
        check(name+': actual current and original row membership frozen exactly', set(actual.index) == set(h.loc[h.source_table.eq(name), 'row_id']) and set(original.index) == set(raw.loc[raw.source_table.eq(name), 'row_id']))
        for row_id in actual.index:
            record = h.set_index('row_id').loc[row_id]
            old = raw.set_index('row_id').loc[row_id]
            for col in actual.columns:
                check(row_id+': current source '+col, same(actual.loc[row_id, col], record[col]))
            for col in original.columns:
                check(row_id+': original source '+col, same(original.loc[row_id, col], old[col]))
            check(row_id+': no prior capital correction in this history', actual.loc[row_id, 'sum_insured'] == original.loc[row_id, 'sum_insured'])
    comparisons = read('transition_comparisons')
    for pid, g in h.groupby('policy_id', sort=True):
        g = g.sort_values('period_start').reset_index(drop=True)
        q = f.loc[f.policy_id.eq(pid)].iloc[0]
        base, initial, endorsed, renewal = [g.iloc[i] for i in range(4)]
        hypot = float(Decimal(str(base.sum_insured))/Decimal(1000))
        check(pid+': exact Decimal hypothesis, not applied or authorized', q.hypothetical_div1000_CU == hypot and not q.correction_authorized and not q.capital_change_applied and not q.test2025_reference)
        check(pid+': two 2022 segments and counter continuity followed by renewal', initial.renewal_decision == 'mid_term_change' and initial.renewal_count == endorsed.renewal_count == base.renewal_count+1 and renewal.renewal_count == endorsed.renewal_count+1 and (g.period_start.dt.year.to_numpy() == [2021,2022,2022,2023]).all() and g.new_business.eq(False).all())
        check(pid+': contiguous original calendar, observed lapse in2023', all((g.iloc[i].period_start-g.iloc[i-1].period_end).days == 1 for i in range(1,4)) and renewal.renewal_decision == 'lapsed_by_customer')
        check(pid+': exposure in2022 sums to one and all rows match inclusive days/365', initial.exposure+endorsed.exposure == 1 and np.allclose(g.exposure, np.round(((g.period_end-g.period_start).dt.days+1)/365,4),rtol=0,atol=0))
        check(pid+': fields known in2021/endorsement/2023 equal and complete', all(pd.notna(base[col]) and base[col] == endorsed[col] == renewal[col] for col in a.FIELDS))
        missing = [col for col in a.FIELDS if pd.isna(initial[col])]
        check(pid+': exact unfilled intermediate missing field', missing == ([ 'high_value_items'] if pid == 'C50633171' else ['security_level']) and q.immediate_2022_missing_fields == missing[0] and all(pd.isna(h.loc[h.row_id.eq(initial.row_id), col]).all() for col in missing))
        check(pid+': known intermediate context compatible, without imputing unknown', all(pd.isna(initial[col]) or initial[col] == base[col] for col in a.FIELDS))
        for field, value in {'growth_2021hyp_to_2022_pct':100*(initial.sum_insured/hypot-1), 'midterm_growth_pct':100*(endorsed.sum_insured/initial.sum_insured-1), 'renewal_vs_endorsed_pct':100*(renewal.sum_insured/endorsed.sum_insured-1), 'renewal_vs_2022_baseline_pct':100*(renewal.sum_insured/initial.sum_insured-1), 'two_year_base_growth_pct':100*(renewal.sum_insured/hypot-1)}.items():
            check(pid+': exact comparison '+field, np.isclose(q[field],value,rtol=0,atol=1e-12))
        check(pid+': first complete reference conflicts with smooth path and remains explicit', q.endorsed_2022_row_id == endorsed.row_id and q.nearest_complete_reference_gap_days == (endorsed.period_start-base.period_start).days and not .9 <= hypot/endorsed.sum_insured <= 1.1 and q.renewal_2023_gap_days == 730)
        check(pid+': both original endorsement and renewal capitals retained', q.endorsed_2022_CU == endorsed.sum_insured and q.renewal_2023_CU == renewal.sum_insured and endorsed.sum_insured in [39400,37700] and renewal.sum_insured in [28300,26700])
        check(pid+': total covered days correct', q.total_observed_covered_days == int(((g.period_end-g.period_start).dt.days+1).sum()))
        for row in comparisons.loc[comparisons.policy_id.eq(pid)].itertuples(index=False):
            left, right = g.set_index('row_id').loc[row.from_row_id], g.set_index('row_id').loc[row.to_row_id]
            check(pid+': transition '+row.to_row_id+' values and labels', row.uncovered_days == 0 and row.renewal_count_change == right.renewal_count-left.renewal_count and row.left_capital_CU == (hypot if row.left_is_hypothetical else left.sum_insured) and row.right_capital_CU == right.sum_insured and np.isclose(row.capital_change_pct,100*(row.right_capital_CU/row.left_capital_CU-1),rtol=0,atol=1e-12))
    # Independently reconstruct every adjacent change, not only the reported risk variables.
    diffs = []
    for pid, g in h.groupby('policy_id', sort=True):
        g = g.sort_values('period_start').reset_index(drop=True)
        for i in range(1,len(g)):
            for col in h.columns:
                if col in ['row_id','policy_id','source_table']: continue
                left,right = g.iloc[i-1][col],g.iloc[i][col]
                if not same(left,right):
                    diffs.append((pid,g.iloc[i-1].row_id,g.iloc[i].row_id,col,None if pd.isna(left) else str(left),None if pd.isna(right) else str(right)))
    reported = read('all_adjacent_field_changes')
    reported_tuples = [tuple(None if pd.isna(x) else x for x in row) for row in reported[['policy_id','from_row_id','to_row_id','field','old_display','new_display']].itertuples(index=False,name=None)]
    check('Every field-change entry complete and exact', set(diffs) == set(reported_tuples))
    for label, filename in [('current','all_claim_histories'),('original','all_original_claim_histories')]:
        path = c.ROOT/cat['claims']['workspace_relative_path'] if label == 'current' else c.RAW/'claims.parquet'
        actual = pq.read_table(path,filters=[('policy_id','in',a.PIDS)])
        check(label+': zero observed claims verified against source',actual.num_rows == len(read(filename)) == 0)
    linked = read('customer_linked_periods')
    counts = read('linked_source_counts')
    for name in counts.source_table:
        actual = pq.read_table(c.ROOT/cat[name]['workspace_relative_path'],columns=['row_id','policy_id','customer_id','address_id','period_start','period_end'],filters=[('customer_id','in',h.customer_id.unique().tolist())])
        check(name+': all customer-linked periods and no replacement policy', set(actual['row_id'].to_pylist()) == set(linked.loc[linked.source_table.eq(name),'row_id']) and set(actual['policy_id'].to_pylist()).issubset(set(a.PIDS)))
    for tab, col, vals in [('addresses','address_id',h.address_id.unique().tolist()),('customers','customer_id',h.customer_id.unique().tolist())]:
        stored = read('address_context' if tab == 'addresses' else 'customer_context')
        actual = pq.read_table(c.ROOT/cat[tab]['workspace_relative_path'],columns=stored.columns.tolist(),filters=[(col,'in',vals)]).to_pandas()
        pd.testing.assert_frame_equal(actual.sort_values(col).reset_index(drop=True),stored.sort_values(col).reset_index(drop=True),check_exact=True)
        check(tab+': all stored context matches source',True)
    # Independent joins select the peer cohort without using the analysis shift implementation.
    cols = list(dict.fromkeys(['row_id','policy_id','period_start','period_end','sum_insured','renewal_decision','renewal_count','new_business',*a.FIELDS]))
    allrows = a.dates(pq.read_table(c.RAW/'policies_contents.parquet',columns=cols).to_pandas())
    left = allrows.loc[allrows.period_start.dt.year.eq(2022)&allrows.renewal_decision.eq('mid_term_change')]
    middle = allrows.loc[allrows.period_start.dt.year.eq(2022)]
    right = allrows.loc[allrows.period_start.eq(pd.Timestamp('2023-01-01'))]
    rename = lambda d,s: d.rename(columns={col:col+s for col in d if col!='policy_id'})
    joined = rename(left,'_a').merge(rename(middle,'_b'),on='policy_id')
    joined = joined.loc[(joined.period_start_b-joined.period_end_a).dt.days.eq(1)]
    joined = joined.merge(rename(right,'_c'),on='policy_id')
    ok = ((joined.period_start_c-joined.period_end_b).dt.days.eq(1) & joined.renewal_count_a.eq(joined.renewal_count_b) & joined.renewal_count_c.eq(joined.renewal_count_a+1))
    for suffix in ['_a','_b','_c']:
        ok &= joined['sum_insured'+suffix].between(1,1000000)&joined['new_business'+suffix].eq(False)
    for col in a.FIELDS:
        for x,y in [('_a','_b'),('_a','_c'),('_b','_c')]:
            ok &= joined[col+x].isna()|joined[col+y].isna()|joined[col+x].eq(joined[col+y])
    selected = joined.loc[ok]
    cohort = read('original_2022_2023_triads_including_focus')
    keys = ['policy_id','baseline_row_id','endorsed_row_id','renewed_row_id']
    expected = set(selected[['policy_id','row_id_a','row_id_b','row_id_c']].itertuples(index=False,name=None))
    check('All2307 original triads independently reconstructed by date joins without amount-change selection', len(cohort) == len(expected) == 2307 and set(cohort[keys].itertuples(index=False,name=None)) == expected)
    peers = read('other_original_2022_2023_triads')
    pd.testing.assert_frame_equal(peers,cohort.loc[~cohort.policy_id.isin(a.PIDS)].reset_index(drop=True),check_exact=True)
    check('2305 other original policies, focal cases excluded from statistics',len(peers) == peers.policy_id.nunique() == 2305 and not peers.policy_id.isin(a.PIDS).any())
    original_values = allrows.set_index('row_id')
    for prefix, field in [('baseline','baseline_CU'),('endorsed','endorsed_CU'),('renewed','renewed_CU')]:
        check(prefix+': every peer amount re-read from raw source', np.array_equal(cohort[field].to_numpy(),original_values.loc[cohort[prefix+'_row_id'],'sum_insured'].to_numpy()))
    for metric,num,den in [('endorsement_growth_pct','endorsed_CU','baseline_CU'),('renewal_vs_endorsed_pct','renewed_CU','endorsed_CU'),('renewal_vs_baseline_pct','renewed_CU','baseline_CU')]:
        check(metric+': every peer ratio recomputed', np.allclose(cohort[metric],100*(cohort[num]/cohort[den]-1),rtol=0,atol=1e-12))
        values = peers[metric]
        expected_stats = {'count':len(values),'minimum':values.min(),'q25':values.quantile(.25),'median':values.median(),'q75':values.quantile(.75),'maximum':values.max()}
        st = read('peer_statistics').loc[lambda x:x.metric.eq(metric)].set_index('statistic').value
        check(metric+': published summary statistics exact', set(st.index) == set(expected_stats) and all(np.isclose(st[k],val,rtol=0,atol=1e-12) for k,val in expected_stats.items()))
    # Completeness/2021 metadata independently recomputed for every peer.
    complete = np.ones(len(cohort),dtype=bool)
    for col in a.FIELDS:
        for key in ['baseline_row_id','endorsed_row_id','renewed_row_id']:
            complete &= original_values.loc[cohort[key],col].notna().to_numpy()
    check('1991 fully observed other triads and exact completeness vector',np.array_equal(cohort.all_D34_fields_known_all_three.to_numpy(),complete) and int(peers.all_D34_fields_known_all_three.sum()) == 1991)
    prior_rows = original_values.reindex(cohort.predecessor_2021_row_id)
    pred = prior_rows.policy_id.to_numpy() == cohort.policy_id.to_numpy()
    pred &= prior_rows.period_start.dt.year.eq(2021).to_numpy() & prior_rows.period_end.eq(pd.Timestamp('2021-12-31')).to_numpy()
    pred &= cohort.baseline_start.eq(pd.Timestamp('2022-01-01')).to_numpy() & prior_rows.sum_insured.between(1,1000000).to_numpy() & prior_rows[a.FIELDS].notna().all(axis=1).to_numpy()
    for col in a.FIELDS:
        for key in ['baseline_row_id','endorsed_row_id','renewed_row_id']:
            x,y = prior_rows[col].reset_index(drop=True),original_values.loc[cohort[key],col].reset_index(drop=True)
            pred &= (x.isna()|y.isna()|x.eq(y)).to_numpy()
    check('All2021 predecessor evidence classified from original rows;2193 other complete normal predecessors',np.array_equal(pred,cohort.original_complete_normal_2021_predecessor.to_numpy()) and int(peers.original_complete_normal_2021_predecessor.sum()) == 2193 and np.array_equal(prior_rows.sum_insured.to_numpy(),cohort.predecessor_2021_CU.to_numpy(),equal_nan=True))
    check('2300 peer reversions under declared descriptive thresholds',int((peers.endorsement_growth_pct.gt(20)&peers.renewal_vs_endorsed_pct.lt(-10)&peers.renewal_vs_baseline_pct.abs().le(10)).sum()) == 2300)
    check('All2305 annual baseline changes positive and below4pct, all post-endorsement changes negative', peers.renewal_vs_baseline_pct.between(0,4).all() and peers.renewal_vs_endorsed_pct.lt(0).all())
    examples = read('other_policy_examples')
    pd.testing.assert_frame_equal(examples,peers.head(6),check_exact=True)
    check('Six real other-policy examples exactly drawn from peer file',len(examples) == 6)
    proposal = read('proposed_manual_scale_changes_NOT_APPLIED')
    pd.testing.assert_frame_equal(proposal,f,check_exact=True)
    check('Exact two-row proposal without application/authorization',set(proposal.row_id) == set(a.FOCUS) and not proposal.correction_authorized.any() and not proposal.capital_change_applied.any())
    scenarios = read('scenarios_NOT_APPLIED')
    check('All eight scenarios purely illustrative, no application',len(scenarios) == 8 and not scenarios.applied.any())
    description = (out/'evidence/data-description.md').read_text('utf-8')
    check('Source descriptions retained for split periods and unqualified written premium', 'changed mid-term' in description and "Premium charged under the insurer's current pricing" in description)
    class Parse(HTMLParser):
        def __init__(self): super().__init__();self.refs=[];self.tables=0;self.images=0
        def handle_starttag(self,tag,attrs):
            self.refs += [val for key,val in attrs if key in ['href','src']]
            self.tables += tag == 'table';self.images += tag == 'img'
    report = (out/'informe.html').read_text('utf-8');parser=Parse();parser.feed(report)
    check('All report links resolve, except this verification and future closing manifest',all(ref in ['manifest.json','verification.json'] or (out/ref).is_file() for ref in parser.refs))
    check('All eight source row IDs visible, both figures and proposal limits explicit',all(row_id in report for row_id in h.row_id) and parser.images == 2 and 'MANUAL_ENDORSE01-R' in report and '421' in report and 'No se modifica' in report)
    check('Protected data unchanged at end of verification',all(c.digest(c.ROOT/path) == sha for path,sha in protected.items()))
    verified = [p for p in out.rglob('*') if p.is_file() and p.name not in ['verification.json','verification_failure.json']]
    result = {'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'checks':checks,
        'capital_changes':0,'pending_unchanged':421,'proposed_manual_changes_NOT_APPLIED':2,
        'other_original_peer_policies':2305,'independent_validation':False,'real_browser_rendering_verified':False,
        'verified_files':{p.relative_to(out).as_posix():c.digest(p) for p in verified}}
    c.dump(out/'verification.json',result)
    print(json.dumps({k:val for k,val in result.items() if k not in ['checks','verified_files']}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
