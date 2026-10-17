"""Comprobaciones propias con relectura de fuentes; no acreditan independencia."""
from pathlib import Path
import json
import re
import sys
import review_context as a
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main(out):
    assert not (out/'manifest.json').exists()
    checks=[]
    def ok(name,value):
        checks.append({'check':name,'passed':bool(value)})
        if not value:raise AssertionError(name)
    def same(left,right,key,cols):
        x=left.set_index(key).sort_index()[cols].copy();y=right.set_index(key).sort_index()[cols].copy()
        for col in cols:
            if col.endswith('_date') or col in ['period_start','period_end']:
                x[col]=pd.to_datetime(x[col]).dt.as_unit('ns');y[col]=pd.to_datetime(y[col]).dt.as_unit('ns')
        pd.testing.assert_frame_equal(x,y,check_dtype=False,check_exact=True)
        return True
    read=lambda name:pd.read_parquet(out/'tables'/(name+'.parquet'))
    protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    for path,sha in protected.items():ok('Protected SHA256 '+path,c.digest(c.ROOT/path)==sha)
    catalog=json.loads((out/'evidence/dataset_catalog.json').read_text('utf-8'))
    idx=json.loads((out/'evidence/retrospective_index.json').read_text('utf-8'))
    ok('Parent immutable manifest verifies',a.cap.manifest_ok(c.ROOT/idx['workspace_relative_run']))
    ok('D48 immutable manifest verifies',a.cap.manifest_ok(a.D48))
    pending=read('remaining_576_inventory');cohort=read('frozen_109_cohort');other=read('other_467_inventory')
    frozen=pd.read_parquet(out/'evidence/frozen_576_pending.parquet')
    d48=pd.read_parquet(out/'evidence/D48_assessment.parquet')
    ok('Full 576 inventory exactly preserved',same(pending,frozen,'row_id',[x for x in frozen if x!='row_id']))
    expected=frozen.loc[frozen.review_group.eq('B_later_with_prior_conflict')]
    ok('Exact frozen group-B 109, one policy per row',len(cohort)==109 and cohort.policy_id.nunique()==109 and set(cohort.row_id)==set(expected.row_id))
    ok('All frozen cohort fields preserved',same(cohort,expected,'row_id',[x for x in expected if x!='row_id']))
    ok('Exact 467 complement without adjudication',len(other)==467 and set(other.row_id)==set(pending.row_id)-set(cohort.row_id))
    ok('Original D48 group membership unchanged',set(cohort.row_id)==set(d48.loc[d48.review_group.eq('B_later_with_prior_conflict'),'row_id']))
    h=read('all_policy_histories');f=read('context_assessment');proposed=read('proposed_scale_changes_NOT_APPLIED')
    ok('571 unique complete history periods',len(h)==h.row_id.nunique()==571 and set(h.policy_id)==set(cohort.policy_id))
    source_frames=[];raw_frames=[]
    for line in ['buildings','contents']:
        ids=set(cohort.loc[cohort.line.eq(line),'policy_id'])
        for prefix in ['policies','test']:
            name=prefix+'_'+line;source=pq.read_table(c.ROOT/catalog[name]['workspace_relative_path']).to_pandas()
            selection=source.loc[source.policy_id.isin(ids)].copy()
            ok('Complete current source cells '+name,same(h.loc[h.source_table.eq(name)],selection,'row_id',[col for col in selection if col!='row_id']))
            selection['source_table']=name;selection['line']=line;source_frames.append(selection)
            raw=pq.read_table(c.RAW/(name+'.parquet')).to_pandas();raw=raw.loc[raw.policy_id.isin(ids)].copy()
            raw['source_table']=name;raw['line']=line;raw_frames.append(raw)
    sources=pd.concat(source_frames,ignore_index=True);raw=pd.concat(raw_frames,ignore_index=True)
    ok('Complete source history population',set(sources.row_id)==set(h.row_id))
    ok('All 571 capital values equal original',same(h,raw,'row_id',['sum_insured']))
    ok('No prior repair used in history',h.capital_repair_rule.isna().all())
    orig=raw.set_index('row_id');current=sources.set_index('row_id');lookup=h.set_index('row_id')
    ok('All 109 current source fields preserved in assessment',same(f,h.loc[h.focus_109],'row_id',[x for x in h if x!='row_id']))
    ok('Line counts 75 buildings and 34 contents',f.line.value_counts().to_dict()=={'buildings':75,'contents':34})
    ok('Pending years 24/16/52/17',f.year.value_counts().sort_index().to_dict()=={2021:24,2022:16,2023:52,2024:17})
    # Different implementation from review_context.comparison: build the entire mismatch set before classifying.
    def compare(x,y,line):
        cols=a.cap.FIELDS[line]
        missing={col for col in cols if pd.isna(x[col]) or pd.isna(y[col])}
        norm=lambda col,v:str(v).strip().lower() if col=='construction_type' else v
        changes={col for col in cols if col not in missing and norm(col,x[col])!=norm(col,y[col])}
        return missing,changes
    test_ids=[];missing_ids=[];skips=[];rules=[]
    for row in f.itertuples(index=False):
        x=current.loc[row.row_id];q=cohort.loc[cohort.row_id.eq(row.row_id)].iloc[0]
        ok('Frozen references '+row.row_id,row.prior_row_id==q.original_prior_row_id and row.later_row_id==q.original_later_row_id)
        g=sources.loc[sources.policy_id.eq(row.policy_id)].sort_values(['period_start','row_id']).reset_index(drop=True)
        pos=g.index[g.row_id.eq(row.row_id)][0];later=g.iloc[pos+1];prior=g.iloc[pos-1]
        ok('Immediate later reference '+row.row_id,later.row_id==row.later_row_id and prior.row_id==row.immediate_prior_row_id)
        for direction,rid in [('prior',row.prior_row_id),('later',row.later_row_id),('immediate_prior',row.immediate_prior_row_id)]:
            y=current.loc[rid];mis,changed=compare(x,y,row.line)
            saved_missing=set(filter(None,getattr(row,direction+'_missing_fields').split('|')))
            saved_changed=set(filter(None,getattr(row,direction+'_changed_fields').split('|')))
            ok('Context fields '+direction+' '+row.row_id,mis==saved_missing and changed==saved_changed and getattr(row,direction+'_complete')==(not mis) and getattr(row,direction+'_same_known_context')==(not mis and not changed))
            ok('Reference source identity and original capital '+direction+' '+row.row_id,y.policy_id==x.policy_id and y.line==x.line and y.sum_insured==orig.loc[rid,'sum_insured'] and y.sum_insured==getattr(row,direction+'_capital_CU'))
        if row.prior_missing_fields:missing_ids.append(row.policy_id)
        if row.immediate_prior_row_id!=row.prior_row_id:skips.append(row.policy_id)
        days=(pd.Timestamp(later.period_start)-pd.Timestamp(x.period_start)).days
        complete=compare(x,later,row.line)==(set(),set())
        candidate=complete and pd.Timestamp(later.period_start)>pd.Timestamp(x.period_end) and 1<=days<=400 and .9<=(x.sum_insured/1000)/later.sum_insured<=1.1 and 0<later.sum_insured<=1_000_000
        rules.append(candidate)
        ok('Independent posterior candidate criterion '+row.row_id,candidate==row.candidate_retrospective_scale_only_NOT_APPLIED and row.hypothetical_div1000_CU==x.sum_insured/1000 and row.later_start_gap_days==days and row.intervening_before_later_rows==0)
        test=later.source_table.startswith('test_') and pd.Timestamp(later.period_start).year==2025
        ok('Future/test flag '+row.row_id,test==row.test2025_reference and pd.Timestamp(later.period_start)>pd.Timestamp(x.period_start))
        if test:test_ids.append(row.row_id)
    ok('109 proposal candidates pass',len(rules)==109 and all(rules))
    ok('Exactly 17 actual test2025 references',len(test_ids)==17 and f.loc[f.test2025_reference].line.value_counts().to_dict()=={'contents':11,'buildings':6})
    ok('Three old-context null cases remain',set(missing_ids)=={'B18335664','B31552770','B43866315'} and set(f.loc[f.prior_missing_fields.ne(''),'prior_missing_fields'])=={'smoke_alarms'})
    ok('Only B19256617 has another immediate prior',skips==['B19256617'])
    patterns={'buildings_TW_only':31,'buildings_address_id':16,'buildings_address_id_construction_type':17,'buildings_address_id_smoke_alarms':6,'buildings_address_id_construction_type_smoke_alarms':5,'contents_address_change':34}
    ok('Six exact context patterns',f.review_pattern.value_counts().to_dict()==patterns)
    tw=f.loc[f.review_pattern.eq('buildings_TW_only')]
    ok('31 original T to W pairs, all focus 2023',all(str(orig.loc[r.prior_row_id,'construction_type']).strip().lower()=='t' and str(orig.loc[r.row_id,'construction_type']).strip().lower()=='w' and orig.loc[r.prior_row_id,'address_id']==orig.loc[r.row_id,'address_id'] and pd.Timestamp(r.period_start)==pd.Timestamp('2023-01-01') for r in tw.itertuples()))
    ok('All 34 contents preserve hypothetical prior limit',(f.loc[f.line.eq('contents'),'hypothetical_vs_prior_pct']==0).all())
    ok('78 address changes and all same customer',f.address_change_from_original_prior.sum()==78 and all(current.loc[r.row_id,'customer_id']==current.loc[r.prior_row_id,'customer_id']==current.loc[r.later_row_id,'customer_id'] for r in f.itertuples()))
    ok('Proposal exactly matches 109 evaluated rows',len(proposed)==109 and set(proposed.row_id)==set(f.row_id) and same(proposed,f,'row_id',[x for x in proposed if x!='row_id']))
    ok('All proposal/assessment authorization and application flags false',not proposed[['capital_change_applied','correction_authorized']].any().any() and not f[['capital_change_applied','correction_authorized']].any().any())
    ok('B192 earlier 377 million untouched and excluded','B00962235' in set(other.row_id) and 'B00962235' not in set(proposed.row_id) and current.loc['B00962235','sum_insured']==377000000 and f.set_index('row_id').loc['B01414378','hypothetical_div1000_CU']==388000)
    ok('C48613718 remains excluded and pending 29.3 million','C01596694' in set(other.row_id) and frozen.set_index('row_id').loc['C01596694','sum_insured']==29300000)
    addresses=pq.read_table(c.ROOT/catalog['addresses']['workspace_relative_path']).to_pandas()
    ad=read('address_context');expected_ad=addresses.loc[addresses.address_id.isin(h.address_id)]
    ok('Full address master cells exactly retained',same(ad,expected_ad,'address_id',[x for x in expected_ad if x!='address_id']))
    claims=read('all_claim_histories');source_claims=pq.read_table(c.ROOT/catalog['claims']['workspace_relative_path']).to_pandas()
    selected=source_claims.loc[source_claims.policy_id.isin(cohort.policy_id)]
    ok('All eight claims and all original current claim cells retained',len(claims)==8 and same(claims,selected,'claim_id',[x for x in selected if x!='claim_id']))
    for claim in claims.itertuples():
        g=h.loc[h.policy_id.eq(claim.policy_id)&h.line.eq(claim.line)]
        matches=[r.row_id for r in g.itertuples() if pd.Timestamp(r.period_start)<=pd.Timestamp(claim.loss_date)<=pd.Timestamp(r.period_end)]
        ok('Occurrence assignment '+claim.claim_id,matches==[claim.row_id] and not claim.audit_pre00)
        expected_net=claim.incurred_to_date-claim.recoveries if claim.status in ['open','closed'] else 0
        ok('Claim amounts unchanged '+claim.claim_id,claim.observed_net_accepted_CU==expected_net and claim.diagnostic_only_not_used_to_select_correction)
    ok('Exactly two focus-period claims',set(claims.loc[claims.focus_109,'claim_id'])=={'CL83963478','CL25718230'} and not claims.incurred_above_hypothetical_capital.any())
    explorer=json.loads((out/'explorer_data.json').read_text('utf-8'))
    ok('Explorer has every assessment',set(r['row_id'] for r in explorer['index'])==set(f.row_id) and len(explorer['index'])==109)
    ok('Explorer has every full history and claim',sum(len(x['policies']) for x in explorer['histories'].values())==571 and sum(len(x['claims']) for x in explorer['histories'].values())==8)
    for pid,entry in explorer['histories'].items():
        ok('Explorer full rows '+pid,set(x['row_id'] for x in entry['policies'])==set(h.loc[h.policy_id.eq(pid),'row_id']))
    html=(out/'informe.html').read_text('utf-8')
    embedded=json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',html).group(1))
    ok('Embedded JSON equals saved explorer',embedded==explorer)
    ok('Twelve actual explained cases',len(explorer['cases'])==12 and all(case['focus_row_id'] in set(f.row_id) for case in explorer['cases']))
    outside=read('noncriterion_later_comparisons');counts=read('noncriterion_later_counts')
    ok('All noncriterion comparisons inventoried',len(outside)==75*13+34*12 and set(outside.focus_row_id)==set(f.row_id))
    for field,group in outside.groupby('field'):
        rebuilt=[]
        for row in group.itertuples():
            x,y=lookup.loc[row.focus_row_id,field],lookup.loc[row.later_row_id,field]
            rebuilt.append((row.pair_missing==bool(pd.isna(x) or pd.isna(y))) and row.changed_when_both_known==bool(not (pd.isna(x) or pd.isna(y)) and x!=y) and row.focus_value==str(x) and row.later_value==str(y))
        ok('Outside criterion source values '+field,all(rebuilt))
    expected_counts=outside.groupby(['line','field'],sort=False).agg(pairs=('focus_row_id','size'),missing_pairs=('pair_missing','sum'),changed_known_pairs=('changed_when_both_known','sum')).reset_index()
    pd.testing.assert_frame_equal(counts,expected_counts)
    ok('Outside criterion counts exactly aggregate source pairs',True)
    unoccupied=counts.loc[counts.field.eq('days_unoccupied')].iloc[0]
    ok('68 known differences and one missing pair disclosed',unoccupied.changed_known_pairs==68 and unoccupied.missing_pairs==1 and '68 pares informados' in html)
    ok('No external resources or derived data output',not re.search(r'(?:src|href)=[\"\x27]https?://',html) and not (out/'data').exists())
    ok('Protected files unchanged after full verification',all(c.digest(c.ROOT/path)==sha for path,sha in protected.items()))
    result={'status':'passed_own_source_rechecks','passed':len(checks),'failed':0,'checks':checks,'independent_validation':False,'real_browser_rendering':False,'data_modified':False}
    c.dump(out/'verification.json',result)
    print(json.dumps({k:result[k] for k in ['status','passed','failed','data_modified']}))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
