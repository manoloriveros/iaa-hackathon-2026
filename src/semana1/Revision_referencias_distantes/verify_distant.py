"""Relee fuentes y reconstruye el criterio distante propuesto; revisión propia."""
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import calendar,json,re,sys
import review_distant as a
import clean_data as c
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
def main(out):
    assert not (out/'manifest.json').exists()
    checks=[]
    def ok(name,value):
        checks.append({'check':name,'passed':bool(value)})
        if not value:c.dump(out/'verification_failure.json',{'checks':checks});raise AssertionError(name)
    def same(x,y,key,cols):
        x=x.set_index(key).sort_index()[cols].copy();y=y.set_index(key).sort_index()[cols].copy()
        for col in cols:
            if col in ['period_start','period_end','loss_date','report_date']:x[col]=pd.to_datetime(x[col]).dt.as_unit('ns');y[col]=pd.to_datetime(y[col]).dt.as_unit('ns')
        pd.testing.assert_frame_equal(x,y,check_exact=True,check_dtype=False);return True
    read=lambda name:pd.read_parquet(out/'tables'/(name+'.parquet'))
    protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'));cat=json.loads((out/'evidence/dataset_catalog.json').read_text('utf-8'));idx=json.loads((out/'evidence/retrospective_index.json').read_text('utf-8'))
    for path,sha in protected.items():ok('Protected SHA256 '+path,c.digest(c.ROOT/path)==sha)
    ok('CAP04R and D56 closed manifests valid',a.cap.manifest_ok(c.ROOT/idx['workspace_relative_run']) and a.cap.manifest_ok(a.D56))
    cohort=read('frozen_48_cohort');prior=pd.read_parquet(out/'evidence/D56_assessment.parquet');expected=prior.loc[prior.review_tier.eq('A_focus_complete_distant_anchor')]
    ok('Exact48 D56 rows and every assessment field retained',len(cohort)==cohort.policy_id.nunique()==cohort.row_id.nunique()==48 and same(cohort,expected,'row_id',[col for col in expected if col!='row_id']))
    pending=read('remaining_467_inventory');original=pd.read_parquet(out/'evidence/frozen_467_pending.parquet');other=read('other_419_inventory')
    ok('All467 pending inventory fields unchanged',len(pending)==467 and same(pending,original,'row_id',[col for col in original if col!='row_id']))
    ok('419 complement preserved without adjudication',len(other)==419 and same(other,original.loc[~original.row_id.isin(cohort.row_id)],'row_id',[col for col in original if col!='row_id']))
    h=read('all_policy_histories');f=read('assessment_48');refs=read('all_original_references');ev=read('direction_evaluations');nodes=read('intermediate_nodes');edges=read('chain_edges');candidates=read('proposed_scale_changes_NOT_APPLIED')
    ok('210 complete unique period rows',len(h)==h.row_id.nunique()==210 and set(h.policy_id)==set(cohort.policy_id))
    for name in ['policies_buildings','test_buildings','policies_contents','test_contents']:
        source=pq.read_table(c.ROOT/cat[name]['workspace_relative_path'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
        ok('Every current source cell '+name,same(h.loc[h.source_table.eq(name)],source,'row_id',[col for col in source if col!='row_id']))
        raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
        ok('Every original capital '+name,same(h.loc[h.source_table.eq(name)],raw,'row_id',['sum_insured']))
    ok('All48 focus attributes in D34 criterion complete',all(h.loc[h.row_id.eq(row.row_id),a.cap.FIELDS[row.line]].notna().all().all() for row in f.itertuples()))
    ok('Assessment source cells retained',same(f,h.loc[h.focus_48],'row_id',[col for col in h if col!='row_id']))
    lookup=h.set_index('row_id');expected_refs=set();independent={}
    def context(x,y):
        cols=a.cap.FIELDS[x.line];missing={col for col in cols if pd.isna(x[col]) or pd.isna(y[col])}
        norm=lambda col,v:str(v).strip().lower() if col=='construction_type' else v
        changed={col for col in cols if col not in missing and norm(col,x[col])!=norm(col,y[col])}
        return missing,changed
    for row in f.itertuples():
        cur=lookup.loc[row.row_id];g=h.loc[h.policy_id.eq(row.policy_id)].sort_values(['period_start','row_id'])
        normal=g.loc[g.original_capital_CU.between(0,a.THRESHOLDS[row.line],inclusive='right')&g.row_id.ne(row.row_id)]
        expected_refs.update((row.row_id,rid) for rid in normal.row_id)
        selected=[]
        for direction in ['prior','later']:
            available=normal.loc[normal.period_start.lt(cur.period_start) if direction=='prior' else normal.period_start.gt(cur.period_start)]
            available=available.loc[available[a.cap.FIELDS[row.line]].notna().all(axis=1)].sort_values('period_start',ascending=direction=='later')
            saved=ev.loc[ev.focus_row_id.eq(row.row_id)&ev.direction.eq(direction)]
            ok(row.row_id+': nearest-complete population '+direction,len(saved)==int(len(available)>0))
            if not len(available):continue
            ref=available.iloc[0];record=saved.iloc[0]
            ok(row.row_id+': complete reference chosen before numeric/context check '+direction,record.reference_row_id==ref.row_id)
            lo,hi=sorted([cur.period_start,ref.period_start]);chain=g.loc[g.period_start.between(lo,hi)];mid=chain.loc[~chain.row_id.isin([cur.name,ref.row_id])]
            miss,changed=context(cur,ref);gap=abs((cur.period_start-ref.period_start).days);ratio=(cur.sum_insured/1000)/ref.sum_insured
            enddate=datetime(lo.year+2,lo.month,min(lo.day,calendar.monthrange(lo.year+2,lo.month)[1]))
            calendar_valid=True;amount_valid=True;values=[]
            for p in chain.itertuples():values.append(p.sum_insured/1000 if p.row_id==cur.name else p.sum_insured)
            saved_edges=edges.loc[edges.focus_row_id.eq(cur.name)&edges.selected_reference_row_id.eq(ref.row_id)]
            ok(row.row_id+': every chronological edge exported '+direction,len(saved_edges)==len(chain)-1)
            for j in range(1,len(chain)):
                left,right=chain.iloc[j-1],chain.iloc[j];days=(right.period_start-left.period_end).days-1
                cal=days==0 or (days==1 and left.period_end.date().isoformat()=='2024-12-30' and right.period_start.date().isoformat()=='2025-01-01')
                step=values[j]/values[j-1];calendar_valid &= cal;amount_valid &= .9<=step<=1.1
                edge=saved_edges.loc[saved_edges.from_row_id.eq(left.row_id)&saved_edges.to_row_id.eq(right.row_id)].iloc[0]
                ok(row.row_id+': original/hypothetical amounts and actual calendar edge '+left.row_id,edge.from_capital_hypothesis_CU==values[j-1] and edge.to_capital_hypothesis_CU==values[j] and edge.ratio_next_over_prior==step and edge.uncovered_days==days and edge.calendar_edge_allowed_with_CAL00_pending==cal)
            no_change=all(not context(cur,m)[1] for _,m in mid.iterrows());incomplete=all(bool(context(cur,m)[0]) for _,m in mid.iterrows())
            mid_original=all(0<m.original_capital_CU<=a.THRESHOLDS[row.line] and m.original_capital_CU==m.sum_insured for _,m in mid.iterrows())
            conditions={'complete_equal_endpoints':not miss and not changed,'ratio_endpoints_within_10pct':.9<=ratio<=1.1,'distance_above_400':gap>400,
                'within_two_calendar_years':hi<=enddate,'one_intermediate_original_row':len(mid)==1,
                'intermediate_context_missing_without_known_change':no_change and incomplete,'intermediate_original_normal':mid_original,
                'each_capital_step_within_10pct':amount_valid,'dates_no_overlap_or_new_gap':calendar_valid}
            ok(row.row_id+': each proposed condition independently rebuilt '+direction,all(record[col]==bool(value) for col,value in conditions.items()) and record.candidate_NOT_APPLIED==all(conditions.values()) and record.start_gap_days==gap and record.ratio_hypothetical_over_reference==ratio)
            for _,m in mid.iterrows():
                nr=nodes.loc[nodes.focus_row_id.eq(cur.name)&nodes.selected_reference_row_id.eq(ref.row_id)&nodes.intermediate_row_id.eq(m.row_id)].iloc[0]
                missing_mid,changed_mid=context(cur,m)
                ok(row.row_id+': missing intermediate cells remain observed original '+m.row_id,nr.capital_CU==m.sum_insured==m.original_capital_CU and set(filter(None,nr.missing_fields.split('|')))==missing_mid and set(filter(None,nr.changed_fields.split('|')))==changed_mid)
            if all(conditions.values()):selected.append(record)
        independent[row.row_id]=selected
        chosen=min(selected,key=lambda r:r.start_gap_days) if selected else ev.loc[ev.focus_row_id.eq(row.row_id)].sort_values('start_gap_days').iloc[0]
        ok(row.row_id+': proposed status and exact Decimal hypothesis',row.candidate_NOT_APPLIED==bool(selected) and row.selected_reference_row_id==chosen.reference_row_id and Decimal(str(row.sum_insured))/Decimal(1000)==Decimal(str(row.hypothetical_div1000_CU)))
        ref=lookup.loc[row.selected_reference_row_id];test=ref.source_table.startswith('test_') and ref.year==2025
        ok(row.row_id+': temporal provenance flag',row.selected_reference_test2025==test and row.selected_reference_future==(ref.period_start>cur.period_start))
    ok('All162 original references retained including contradictions',len(refs)==162 and set(zip(refs.focus_row_id,refs.reference_row_id))==expected_refs)
    for row in refs.itertuples():
        cur,ref=lookup.loc[row.focus_row_id],lookup.loc[row.reference_row_id];miss,changed=context(cur,ref);ratio=cur.sum_insured/1000/ref.sum_insured
        ok('Reference pair '+row.focus_row_id+'/'+row.reference_row_id,row.reference_capital_CU==ref.sum_insured and set(filter(None,row.missing_fields.split('|')))==miss and set(filter(None,row.changed_fields.split('|')))==changed and row.ratio_hypothetical_over_reference==ratio)
    ok('No original complete support under live400-day criterion',refs.strict_400day_support.sum()==0)
    valid={rid for rid,pairs in independent.items() if pairs}
    ok('Exact46 frozen candidate IDs,18 buildings28 contents',len(candidates)==46 and set(candidates.row_id)==valid and candidates.line.value_counts().to_dict()=={'contents':28,'buildings':18})
    ok('Every proposed field matches assessment',same(candidates,f.loc[f.candidate_NOT_APPLIED],'row_id',[col for col in candidates if col!='row_id']))
    ok('Exactly two real numeric conflicts retained',set(f.loc[~f.candidate_NOT_APPLIED,'policy_id'])=={'C50633171','C56600576'})
    for rid,near,amount,new in [('C00502745','C01153989',39400,27200),('C00399729','C01147928',37700,25700)]:
        row=f.set_index('row_id').loc[rid];ok(rid+': nearer complete endorsed limit cannot be skipped',row.selected_reference_row_id==near and lookup.loc[near,'sum_insured']==amount and row.hypothetical_div1000_CU==new and not row.candidate_NOT_APPLIED and not .9<=new/amount<=1.1)
    signal=read('proposed_test2025_supported_NOT_APPLIED')
    ok('Seven test2025 anchors exactly marked,one building six contents',len(signal)==7 and signal.line.value_counts().to_dict()=={'contents':6,'buildings':1} and set(signal.row_id)==set(candidates.loc[candidates.selected_reference_test2025,'row_id']))
    ok('21 prior and25 future anchors,13 focus rows in test',candidates.selected_reference_direction.value_counts().to_dict()=={'later':25,'prior':21} and f.source_table.str.startswith('test_').sum()==13)
    ok('All authorization/application flags stay false',not f.correction_authorized.any() and not f.capital_change_applied.any() and not candidates.correction_authorized.any() and not candidates.capital_change_applied.any())
    chosen_edges=edges.merge(candidates[['row_id','selected_reference_row_id']].rename(columns={'row_id':'focus_row_id'}),on=['focus_row_id','selected_reference_row_id'])
    ok('92 proposed edges preserve72 contiguous and20 known CAL00 gaps',len(chosen_edges)==92 and chosen_edges.uncovered_days.value_counts().to_dict()=={0:72,1:20})
    outside=read('other_endpoint_comparisons')
    for field,group in outside.groupby('field'):
        good=True
        for row in group.itertuples():
            x,y=lookup.loc[row.focus_row_id,field],lookup.loc[row.reference_row_id,field]
            good &= row.focus_value==str(x) and row.reference_value==str(y) and row.missing_pair==bool(pd.isna(x) or pd.isna(y)) and row.changed_when_known==bool(not(pd.isna(x) or pd.isna(y)) and x!=y)
        ok('Other endpoint values '+field,good)
    ok('All18 building days-unoccupied changes explicitly observed',outside.loc[outside.field.eq('days_unoccupied'),'changed_when_known'].tolist()==[True]*18)
    sensitivity=read('window_sensitivity');factors=['complete_equal_endpoints','ratio_endpoints_within_10pct','one_intermediate_original_row','intermediate_context_missing_without_known_change','intermediate_original_normal','each_capital_step_within_10pct','dates_no_overlap_or_new_gap']
    for row in sensitivity.itertuples():ok('Window sensitivity '+str(row.maximum_start_days),row.rows_passing_other_proposed_checks==ev.loc[ev[factors].all(axis=1)&ev.start_gap_days.le(row.maximum_start_days),'focus_row_id'].nunique())
    claims=read('all_claim_histories');source=pq.read_table(c.ROOT/cat['claims']['workspace_relative_path'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
    ok('All seven claim source cells preserved',len(claims)==7 and same(claims,source,'claim_id',[col for col in source if col!='claim_id']))
    for row in claims.itertuples():
        g=h.loc[h.policy_id.eq(row.policy_id)&h.line.eq(row.line)];hits=[p.row_id for p in g.itertuples() if p.period_start<=row.loss_date<=p.period_end]
        ok('Independent occurrence assignment '+row.claim_id,hits==[row.row_id] and row.diagnostic_only_not_used_for_selection)
    ok('No claim used in48 focus periods',not claims.focus_48.any())
    ad=read('address_context');source=pq.read_table(c.ROOT/cat['addresses']['workspace_relative_path'],filters=[('address_id','in',h.address_id.unique().tolist())]).to_pandas()
    ok('Complete original address context preserved',same(ad,source,'address_id',[col for col in source if col!='address_id']))
    for name,part in pending.groupby('source_table'):
        values=pq.read_table(c.ROOT/cat[name]['workspace_relative_path'],columns=['row_id','sum_insured'],filters=[('row_id','in',part.row_id.tolist())]).to_pandas().set_index('row_id').sum_insured
        ok(name+': every467 pending capital unchanged',np.array_equal(values.loc[part.row_id].to_numpy(),part.sum_insured.to_numpy()))
    data=json.loads((out/'explorer_data.json').read_text('utf-8'));report=(out/'informe.html').read_text('utf-8');embedded=json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',report).group(1))
    ok('48 actual rows and12 explained cases in matching payload',data==embedded and len(data['index'])==48 and set(r['row_id'] for r in data['index'])==set(f.row_id) and len(data['cases'])==12)
    for pid,entry in data['histories'].items():ok('Complete explorer history '+pid,set(r['row_id'] for r in entry['policies'])==set(h.loc[h.policy_id.eq(pid),'row_id']) and len(entry['references'])==len(refs.loc[refs.policy_id.eq(pid)]))
    ok('No external resources or scenario dataset output',not (out/'data').exists() and not re.search(r'(?:href|src)=[\"\x27]https?://',report))
    ok('Protected originals,derived files,indexes and live protocol unchanged after checks',all(c.digest(c.ROOT/p)==sha for p,sha in protected.items()))
    result={'status':'passed_own_source_rechecks','passed':len(checks),'failed':0,'checks':checks,'data_modified':False,'independent_validation':False}
    c.dump(out/'verification.json',result);print(json.dumps({k:result[k] for k in ['status','passed','failed','data_modified']}))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
