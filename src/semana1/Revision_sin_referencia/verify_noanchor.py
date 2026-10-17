"""Verificación propia mediante nuevas lecturas; no certifica contratos ni independencia."""
from pathlib import Path
import json
import re
import sys
import review_noanchor as a
import clean_data as c
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

def main(out):
    assert not (out/'manifest.json').exists()
    checks=[]
    def check(name,value):
        checks.append({'check':name,'passed':bool(value)})
        if not value:
            c.dump(out/'verification_failure.json',{'checks':checks});raise AssertionError(name)
    def same(left,right,key,cols):
        x=left.set_index(key).sort_index()[cols].copy();y=right.set_index(key).sort_index()[cols].copy()
        for col in cols:
            if col in ['period_start','period_end'] or col.endswith('_date'):
                x[col]=pd.to_datetime(x[col]).dt.as_unit('ns');y[col]=pd.to_datetime(y[col]).dt.as_unit('ns')
        pd.testing.assert_frame_equal(x,y,check_dtype=False,check_exact=True)
        return True
    read=lambda name:pd.read_parquet(out/'tables'/(name+'.parquet'))
    protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    for p,sha in protected.items():check('Protected SHA256 '+p,c.digest(c.ROOT/p)==sha)
    cat=json.loads((out/'evidence/dataset_catalog.json').read_text('utf-8'));idx=json.loads((out/'evidence/retrospective_index.json').read_text('utf-8'))
    check('CAP04R and D48 immutable manifests verify',a.cap.manifest_ok(c.ROOT/idx['workspace_relative_run']) and a.cap.manifest_ok(a.D48))
    pending=read('remaining_467_inventory');frozen=pd.read_parquet(out/'evidence/frozen_467_pending.parquet');d48=pd.read_parquet(out/'evidence/D48_assessment.parquet')
    cohort=read('frozen_108_cohort');other=read('other_359_inventory');f=read('noanchor_assessment');h=read('all_policy_histories')
    check('467 pending assessments exactly preserved',len(pending)==467 and same(pending,frozen,'row_id',[k for k in frozen if k!='row_id']))
    expected=frozen.loc[frozen.review_group.eq(a.GROUP)]
    check('Exact 108 frozen D48 group-C IDs still pending',len(cohort)==cohort.row_id.nunique()==108 and set(cohort.row_id)==set(expected.row_id)==set(d48.loc[d48.review_group.eq(a.GROUP),'row_id']))
    check('Every cohort assessment field preserved',same(cohort,expected,'row_id',[k for k in expected if k!='row_id']))
    check('Exact 359 other pending IDs and fields',len(other)==359 and same(other,frozen.loc[~frozen.row_id.isin(cohort.row_id)],'row_id',[k for k in frozen if k!='row_id']))
    check('108 rows in 107 policies and full history population',len(h)==h.row_id.nunique()==108 and h.policy_id.nunique()==107 and set(h.row_id)==set(cohort.row_id))
    check('62 buildings,46 contents and107 test2025 rows',f.line.value_counts().to_dict()=={'buildings':62,'contents':46} and f.source_table.value_counts().to_dict()=={'test_buildings':61,'test_contents':46,'policies_buildings':1})
    check('106 singleton policies and one two-period history',h.groupby('policy_id').size().value_counts().to_dict()=={1:106,2:1})
    check('No previous scale changes in any cohort capital',(h.original_capital_CU==h.sum_insured).all())
    linked=read('all_linked_policy_histories');links=read('linked_comparisons');peers=read('descriptive_peer_population')
    wanted=set(cohort.policy_id);address_ids=set(cohort.address_id);customer_ids=set(cohort.customer_id)
    eligible_keys=set(zip(f.source_table,f.year,f.new_business));direct=[];reconstructed_peers=[]
    for name in ['policies_buildings','test_buildings','policies_contents','test_contents']:
        line=name.split('_',1)[1];source=pq.read_table(c.ROOT/cat[name]['workspace_relative_path']).to_pandas()
        selection=source.loc[source.policy_id.isin(wanted)].copy()
        check('All full current source cells '+name,same(h.loc[h.source_table.eq(name)],selection,'row_id',[col for col in source if col!='row_id']))
        raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
        check('Original capital values '+name,np.array_equal(selection.row_id.map(raw).to_numpy(),h.loc[h.source_table.eq(name)].set_index('row_id').loc[selection.row_id,'original_capital_CU'].to_numpy()))
        source['original_capital_CU']=source.row_id.map(raw);source['source_table']=name;source['line']=line
        for col in ['period_start','period_end']:source[col]=pd.to_datetime(source[col]).dt.as_unit('ns')
        source['year']=source.period_start.dt.year;source['covered_days']=(source.period_end-source.period_start).dt.days+1
        direct.append(source.loc[~source.policy_id.isin(wanted)&(source.address_id.isin(address_ids)|source.customer_id.isin(customer_ids))].copy())
        keep=(~source.policy_id.isin(wanted))&source.original_capital_CU.gt(0)&source.original_capital_CU.le(a.THRESHOLDS[line])&source.original_capital_CU.eq(source.sum_insured)
        allowed=pd.Series([(name,int(year),bool(nb)) in eligible_keys for year,nb in zip(source.year,source.new_business)],index=source.index)
        reconstructed_peers.append(source.loc[keep&allowed,list(peers.columns)].copy())
    found=pd.concat(direct,ignore_index=True)
    check('Every directly linked peer policy discovered',set(found.policy_id)==set(linked.policy_id) and found.row_id.nunique()==79)
    for name in ['policies_buildings','test_buildings','policies_contents','test_contents']:
        source=pq.read_table(c.ROOT/cat[name]['workspace_relative_path'],filters=[('policy_id','in',list(set(linked.policy_id)))]).to_pandas()
        check('Complete linked histories from actual catalog '+name,same(linked.loc[linked.source_table.eq(name)],source,'row_id',[col for col in source if col!='row_id']))
    exp_peers=pd.concat(reconstructed_peers,ignore_index=True)
    check('All 240141 comparable population rows exactly reproduced',len(peers)==len(exp_peers)==240141 and same(peers,exp_peers,'row_id',[col for col in peers if col!='row_id']))
    check('Peer selection excludes every focus policy and all repaired capitals',not set(peers.policy_id)&wanted and peers.original_capital_CU.eq(peers.sum_insured).all())
    # Rebuild links by two keyed joins and a union, rather than the producer's per-row predicate.
    keys=['row_id','policy_id','customer_id','address_id','line','period_start','period_end']
    x=h[keys];y=linked[keys]
    unions=[]
    for on in ['address_id','customer_id']:
        merged=x.merge(y,on=on,suffixes=('_focus','_peer'),how='inner')
        unions.append(merged[['row_id_focus','row_id_peer']].rename(columns={'row_id_focus':'focus_row_id','row_id_peer':'peer_row_id'}))
    expected_pairs=pd.concat(unions,ignore_index=True).drop_duplicates()
    check('Exact 81 link pairs reproduced independently',len(links)==81 and set(zip(links.focus_row_id,links.peer_row_id))==set(zip(expected_pairs.focus_row_id,expected_pairs.peer_row_id)))
    hl=h.set_index('row_id');ll=linked.set_index('row_id')
    for row in links.itertuples():
        own=hl.loc[row.focus_row_id];peer=ll.loc[row.peer_row_id]
        check('Linked evidence '+row.focus_row_id+'/'+row.peer_row_id,row.same_customer==(own.customer_id==peer.customer_id) and row.same_address==(own.address_id==peer.address_id) and row.same_line==(own.line==peer.line) and row.same_interval==(own.period_start==peer.period_start and own.period_end==peer.period_end) and row.peer_capital_CU==peer.sum_insured and row.peer_original_capital_CU==peer.original_capital_CU)
    check('No same-line same-customer address anchor',(links.same_line&links.same_customer&links.same_address).sum()==0)
    check('Other-line same-customer address interval evidence for71 rows',links.loc[~links.same_line&links.same_customer&links.same_address&links.same_interval,'focus_row_id'].nunique()==71)
    check('Only C52311091 has same-line address peer with different customer',set(links.loc[links.same_line,'focus_row_id'])=={'C03012340'} and not links.loc[links.same_line,'same_customer'].any())
    check('Assessment retains all source history cells',same(f,h,'row_id',[col for col in h if col!='row_id']))
    for row in f.itertuples():
        own=h.loc[h.policy_id.eq(row.policy_id)];rel=links.loc[links.focus_row_id.eq(row.row_id)]
        cross=rel.loc[~rel.same_line&rel.same_customer&rel.same_address];ao=rel.loc[rel.same_address&~rel.same_customer]
        group='A_two_high_periods' if len(own)>1 else ('B_singleton_crossline_same_customer' if len(cross) else ('C_address_only_other_customer' if len(ao) else 'D_singleton_no_household_link'))
        check(row.row_id+': no original ordinary own-policy reference',own.original_capital_CU.gt(a.THRESHOLDS[row.line]).all() and row.original_normal_reference_rows==0 and row.history_rows==len(own))
        check(row.row_id+': individual evidence group',row.review_group==group and row.crossline_same_customer_address_peer_rows==len(cross) and row.address_only_other_customer_peer_rows==len(ao))
        pv=peers.loc[peers.source_table.eq(row.source_table)&peers.year.eq(row.year)&peers.new_business.eq(row.new_business),'sum_insured']
        check(row.row_id+': hypothetical arithmetic and matched peer rank',row.hypothetical_div1000_CU==row.sum_insured/1000 and row.peer_population_rows==len(pv) and np.isclose(row.peer_hypothetical_percentile,100*pv.le(row.hypothetical_div1000_CU).sum()/len(pv),rtol=0,atol=1e-12) and row.hypothetical_inside_peer_range==(pv.min()<=row.hypothetical_div1000_CU<=pv.max()) and row.peer_min_CU==pv.min() and row.peer_max_CU==pv.max())
        missing={col for col in a.cap.FIELDS[row.line] if pd.isna(getattr(row,col))}
        check(row.row_id+': context missingness unchanged',set(filter(None,row.context_missing_fields.split('|')))==missing)
    check('Four exact evidence groups',f.review_group.value_counts().to_dict()=={'B_singleton_crossline_same_customer':69,'D_singleton_no_household_link':36,'A_two_high_periods':2,'C_address_only_other_customer':1})
    check('Five missing-context rows remain without imputation',f.context_missing_fields.ne('').sum()==5 and f.loc[f.context_missing_fields.ne(''),'context_missing_fields'].value_counts().to_dict()=={'smoke_alarms':2,'security_level':2,'high_value_items':1})
    check('B672 two high originals and no ordinary anchor',hl.loc['B02208778','sum_insured']==435000000 and hl.loc['B02808426','sum_insured']==448000000 and hl.loc['B02208778','policy_id']==hl.loc['B02808426','policy_id']=='B67263929')
    check('B672 ratio invariant under common /1000',(448000000/435000000)==(448000/435000))
    bands=read('peer_bands')
    for band in bands.itertuples():
        v=peers.loc[peers.source_table.eq(band.source_table)&peers.year.eq(band.year)&peers.new_business.eq(band.new_business),'sum_insured']
        check('Actual quantiles '+band.source_table+'/'+str(band.new_business),band.rows==len(v) and all(getattr(band,'capital_'+name)==v.quantile(q) for name,q in [('min',0),('p01',.01),('p05',.05),('p50',.5),('p95',.95),('p99',.99),('max',1)]))
    for name,policies in [('all_claim_histories',set(h.policy_id)),('linked_claim_histories',set(linked.policy_id))]:
        actual=pq.read_table(c.ROOT/cat['claims']['workspace_relative_path'],filters=[('policy_id','in',list(policies))]).to_pandas();saved=read(name)
        check('No omitted claim rows '+name,len(actual)==len(saved)==0 and list(actual.columns)==list(saved.columns))
    ad=read('address_context');actual_ad=pq.read_table(c.ROOT/cat['addresses']['workspace_relative_path'],filters=[('address_id','in',list(set(h.address_id)|set(linked.address_id)))]).to_pandas()
    check('Complete original address context retained',same(ad,actual_ad,'address_id',[col for col in actual_ad if col!='address_id']))
    plan=read('proposed_treatment_NOT_APPLIED');proposal=json.loads((out/'proposal.json').read_text('utf-8'))
    check('All108 proposed treatments are pending, with no application or authorization',len(plan)==108 and set(plan.row_id)==set(f.row_id) and plan.proposed_action.eq('KEEP_PENDING_NO_AUTOMATIC_SCALE_REPAIR').all() and not plan.capital_change_applied.any() and not plan.correction_authorized.any() and proposal['status']=='review_only_no_application_authorization')
    html=(out/'informe.html').read_text('utf-8');explorer=json.loads((out/'explorer_data.json').read_text('utf-8'))
    embedded=json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',html).group(1))
    check('Embedded explorer exactly matches stored payload',embedded==explorer)
    check('All108 rows and12 explained cases exported',set(x['row_id'] for x in explorer['index'])==set(f.row_id) and len(explorer['index'])==108 and len(explorer['cases'])==12)
    for pid,entry in explorer['histories'].items():
        rel=links.loc[links.focus_policy_id.eq(pid)];expected=linked.loc[linked.policy_id.isin(rel.peer_policy_id)]
        check('Explorer complete own/related histories '+pid,set(r['row_id'] for r in entry['policies'])==set(h.loc[h.policy_id.eq(pid),'row_id']) and set(r['row_id'] for r in entry['linked_policies'])==set(expected.row_id) and entry['claims']==[])
    check('No network resource or scenario data output',not re.search(r'(?:href|src)=[\"\x27]https?://',html) and not (out/'data').exists())
    check('All protected data and indexes unchanged after checks',all(c.digest(c.ROOT/p)==sha for p,sha in protected.items()))
    result={'status':'passed_own_source_rechecks','passed':len(checks),'failed':0,'checks':checks,'data_modified':False,'independent_validation':False,'real_browser_rendering_verified':False}
    c.dump(out/'verification.json',result);print(json.dumps({k:result[k] for k in ['status','passed','failed','data_modified']}))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
