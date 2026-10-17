"""Comprobaciones propias con reconstrucción de642 pares y132 vecinos desde fuentes."""
from pathlib import Path
import json,re,sys,importlib.util
import review_incomplete as a
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
    cat=json.loads((out/'evidence/dataset_catalog.json').read_text('utf-8'));protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    for path,sha in protected.items():ok('Protected SHA256 '+path,c.digest(c.ROOT/path)==sha)
    idx=json.loads((out/'evidence/retrospective_index.json').read_text('utf-8'))
    ok('Prior closed manifests verify',all(a.cap.manifest_ok(p) for p in [c.ROOT/idx['workspace_relative_run'],a.D48,a.D40,a.D55]))
    pending=read('remaining_467_inventory');original=pd.read_parquet(out/'evidence/frozen_467_pending.parquet');cohort=read('frozen_202_cohort');kept=pd.read_parquet(out/'evidence/frozen_108_kept_pending.parquet')
    d48=pd.read_parquet(out/'evidence/D48_assessment.parquet');other=read('other_265_inventory')
    ok('All467 inventory fields unchanged',len(pending)==467 and same(pending,original,'row_id',[col for col in original if col!='row_id']))
    expected=original.loc[original.review_group.eq('F_incomplete_context')]
    ok('Exact202 frozen D48 groupF',len(cohort)==cohort.row_id.nunique()==cohort.policy_id.nunique()==202 and set(cohort.row_id)==set(expected.row_id)==set(d48.loc[d48.review_group.eq('F_incomplete_context'),'row_id']))
    ok('Every cohort field unchanged',same(cohort,expected,'row_id',[col for col in expected if col!='row_id']))
    ok('Exact265 complement includes all108 retained pending',len(other)==265 and set(other.row_id)==set(original.row_id)-set(cohort.row_id) and set(kept.row_id).issubset(set(other.row_id)))
    h=read('all_policy_histories');f=read('incomplete_assessment');refs=read('all_original_references');bridge=read('missing_field_bridges')
    ok('844 complete unique history rows',len(h)==h.row_id.nunique()==844 and set(h.policy_id)==set(cohort.policy_id))
    for line in ['buildings','contents']:
        for pref in ['policies','test']:
            name=pref+'_'+line;source=pq.read_table(c.ROOT/cat[name]['workspace_relative_path'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
            ok('Complete current source cells '+name,same(h.loc[h.source_table.eq(name)],source,'row_id',[col for col in source if col!='row_id']))
            raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
            ok('All capital values remain original '+name,same(h.loc[h.source_table.eq(name)],raw,'row_id',['sum_insured']))
    hl=h.set_index('row_id');fl=f.set_index('row_id')
    ok('All assessment source fields equal full histories',same(f,h.loc[h.focus_202],'row_id',[col for col in h if col!='row_id']))
    ok('63 buildings,139 contents and40 test rows',f.line.value_counts().to_dict()=={'contents':139,'buildings':63} and f.source_table.str.startswith('test').sum()==40)
    expected_pairs=set()
    def compare(x,y,skip=()):
        cols=[col for col in a.cap.FIELDS[x.line] if col not in skip];missing={col for col in cols if pd.isna(x[col]) or pd.isna(y[col])}
        norm=lambda col,value:str(value).strip().lower() if col=='construction_type' else value
        changes={col for col in cols if col not in missing and norm(col,x[col])!=norm(col,y[col])}
        return missing,changes
    for row in f.itertuples():
        cur=hl.loc[row.row_id];g=h.loc[h.policy_id.eq(row.policy_id)]
        normals=g.loc[g.original_capital_CU.gt(0)&g.original_capital_CU.le(a.THRESHOLDS[row.line])&g.row_id.ne(row.row_id)]
        expected_pairs.update((row.row_id,rid) for rid in normals.row_id)
        local=refs.loc[refs.focus_row_id.eq(row.row_id)]
        ok(row.row_id+': exhaustive ordinary originals',set(local.reference_row_id)==set(normals.row_id))
        for direction in ['prior','later']:
            candidates=normals.loc[normals.period_start.lt(cur.period_start) if direction=='prior' else normals.period_start.gt(cur.period_start)]
            nearest=(candidates.sort_values('period_start').iloc[-1 if direction=='prior' else 0].row_id) if len(candidates) else None
            observed=local.loc[local.direction.eq(direction)&local.nearest_original_in_direction,'reference_row_id'].tolist()
            ok(row.row_id+': nearest '+direction,observed==([nearest] if nearest else []))
        missing={col for col in a.cap.FIELDS[row.line] if pd.isna(cur[col])}
        ok(row.row_id+': current missing mask preserved',set(filter(None,row.focus_missing_fields.split('|')))==missing and row.hypothetical_div1000_CU==cur.sum_insured/1000)
        distant=local.distant_complete_compatible.any();tier=('A_focus_complete_distant_anchor' if distant else 'B_focus_complete_only_incomplete_nearby') if not missing else 'C_focus_missing'
        ok(row.row_id+': treatment tier',row.review_tier==tier and row.strict_original_support_count==0 and row.distant_complete_compatible_count==local.distant_complete_compatible.sum())
        near=local.loc[local.nearest_original_in_direction&local.missing_only_compatible]
        ok(row.row_id+': near incomplete directional evidence',row.nearest_missing_only_compatible_pairs==len(near) and len(near)>0 and row.nearest_prior_missing_only_compatible==near.direction.eq('prior').any() and row.nearest_later_missing_only_compatible==near.direction.eq('later').any())
    ok('Exactly642 full reference pairs',len(refs)==642 and set(zip(refs.focus_row_id,refs.reference_row_id))==expected_pairs)
    for row in refs.itertuples():
        cur=hl.loc[row.focus_row_id];ref=hl.loc[row.reference_row_id];missing,changes=compare(cur,ref)
        gap=abs((cur.period_start-ref.period_start).days);direction='prior' if ref.period_start<cur.period_start else 'later'
        temporal=ref.period_end<cur.period_start if direction=='prior' else cur.period_end<ref.period_start
        ratio=(cur.sum_insured/1000)/ref.sum_insured;complete=not missing and not changes
        strict=bool(complete and temporal and 1<=gap<=400 and .9<=ratio<=1.1)
        incomplete=bool(missing and not changes and temporal and 1<=gap<=400 and .9<=ratio<=1.1)
        distant=bool(complete and temporal and gap>400 and .9<=ratio<=1.1)
        ok(row.focus_row_id+'/'+row.reference_row_id+': exact context, time, amount and classifications',set(filter(None,row.missing_fields.split('|')))==missing and set(filter(None,row.changed_fields.split('|')))==changes and row.direction==direction and row.start_gap_days==gap and row.reference_capital_CU==ref.sum_insured==ref.original_capital_CU and row.ratio_hypothetical_over_reference==ratio and row.strict_original_support==strict and row.missing_only_compatible==incomplete and row.distant_complete_compatible==distant)
    ok('No strict support and259 nearest incomplete pairs',refs.strict_original_support.sum()==0 and (refs.missing_only_compatible&refs.nearest_original_in_direction).sum()==259)
    ok('Exact tiers48,23,131 and132 field issues',f.review_tier.value_counts().to_dict()=={'C_focus_missing':131,'A_focus_complete_distant_anchor':48,'B_focus_complete_only_incomplete_nearby':23} and len(bridge)==132)
    for row in bridge.itertuples():
        cur=hl.loc[row.focus_row_id];g=h.loc[h.policy_id.eq(row.policy_id)&h[row.field].notna()]
        prior=g.loc[g.period_start.lt(cur.period_start)].sort_values('period_start');later=g.loc[g.period_start.gt(cur.period_start)].sort_values('period_start')
        prev=prior.iloc[-1] if len(prior) else None;nxt=later.iloc[0] if len(later) else None
        skip=[col for col in a.cap.FIELDS[cur.line] if pd.isna(cur[col])]
        usable=lambda ref:ref is not None and compare(cur,ref,skip)==(set(),set())
        if prev is not None and nxt is not None:status='BOTH_EQUAL_RECORDED_CONTEXT' if prev[row.field]==nxt[row.field] and usable(prev) and usable(nxt) else ('BOTH_DIFFERENT_VALUE' if prev[row.field]!=nxt[row.field] else 'BOTH_EQUAL_WITH_CONTEXT_CHANGE_OR_MISSING')
        else:status='ONE_SIDED_KNOWN' if prev is not None or nxt is not None else 'NO_KNOWN_NEIGHBOR'
        prev_ok=(row.prior_row_id==prev.row_id and row.prior_value==str(prev[row.field])) if prev is not None else pd.isna(row.prior_row_id)
        later_ok=(row.later_row_id==nxt.row_id and row.later_value==str(nxt[row.field])) if nxt is not None else pd.isna(row.later_row_id)
        ok(row.focus_row_id+'/'+row.field+': exact observed neighbors and no imputation',status==row.bridge_status and prev_ok and later_ok and not row.imputation_applied and not row.equality_of_unobserved_value_proven)
    ok('Bridge counts distinguish132 fields from131 rows',bridge.bridge_status.value_counts().to_dict()=={'ONE_SIDED_KNOWN':69,'BOTH_EQUAL_RECORDED_CONTEXT':50,'BOTH_EQUAL_WITH_CONTEXT_CHANGE_OR_MISSING':12,'BOTH_DIFFERENT_VALUE':1} and bridge.focus_row_id.nunique()==131)
    claims=read('all_claim_histories');actual=pq.read_table(c.ROOT/cat['claims']['workspace_relative_path'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
    ok('Every claim source cell preserved',len(claims)==24 and same(claims,actual,'claim_id',[col for col in actual if col!='claim_id']))
    for row in claims.itertuples():
        periods=h.loc[h.policy_id.eq(row.policy_id)&h.line.eq(row.line)]
        hits=[p.row_id for p in periods.itertuples() if p.period_start<=row.loss_date<=p.period_end]
        ok(row.claim_id+': unique occurrence assignment and unchanged costs',hits==[row.row_id] and row.diagnostic_only_not_used_for_selection and not row.audit_pre00)
    ok('Four focus claims, none above hypothetical capital',claims.focus_202.sum()==4 and claims.incurred_above_hypothetical_capital.sum()==0)
    ad=read('address_context');actual=pq.read_table(c.ROOT/cat['addresses']['workspace_relative_path'],filters=[('address_id','in',h.address_id.unique().tolist())]).to_pandas()
    ok('All complete address master cells retained',same(ad,actual,'address_id',[col for col in actual if col!='address_id']))
    for name,part in original.groupby('source_table'):
        values=pq.read_table(c.ROOT/cat[name]['workspace_relative_path'],columns=['row_id','sum_insured'],filters=[('row_id','in',part.row_id.tolist())]).to_pandas().set_index('row_id').sum_insured
        ok(name+': every467 pending including108 unchanged',np.array_equal(values.loc[part.row_id].to_numpy(),part.sum_insured.to_numpy()))
    plan=read('proposed_treatment_NOT_APPLIED');ok('All202 treatments preserve capital and nulos',len(plan)==202 and not plan.capital_change_applied.any() and not plan.correction_authorized.any() and plan.proposed_action.eq('KEEP_PENDING_NO_IMPUTATION_NO_WINDOW_EXTENSION').all())
    backlog=json.loads((out/'validation_backlog_58.json').read_text('utf-8'));old=json.loads((out/'evidence/D40_controls.json').read_text('utf-8'));old_by={r['id']:r for r in old}
    ok('All58 original controls reconciled, no IDs dropped or invented',len(backlog)==58 and {r['id'] for r in backlog}==set(old_by))
    for row in backlog:ok(row['id']+': original provenance retained and remaining action explicit',all(row[k]==old_by[row['id']][k] for k in old_by[row['id']]) and bool(row['remaining_work_current']) and bool(row['current_status']))
    streams=read('validation_workstreams');ok('16 workstreams cover all58 controls',len(streams)==16 and {x for ids in streams.control_ids for x in ids.split(',')}==set(old_by))
    spec=importlib.util.spec_from_file_location('guard_check',c.ROOT/'Preparación/src/iaa_lab/predictor_guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    probe=json.loads((out/'predictor_guard_gap.json').read_text('utf-8'))
    ok('Contacts operational gap independently reproduced',guard.exclusion_reason('customer_service_contacts') is None and probe['customer_service_contacts'] is None and guard.select_predictor_columns(['renewal_decision','audit_ref_test2025','customer_service_contacts','sum_insured'])==probe['selected_from_probe']==['customer_service_contacts','sum_insured'])
    ok('Renewal/audit exclusion remains effective',guard.exclusion_reason('renewal_decision') is not None and guard.exclusion_reason('audit_ref_test2025') is not None)
    explorer=json.loads((out/'explorer_data.json').read_text('utf-8'));html=(out/'informe.html').read_text('utf-8');embedded=json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',html).group(1))
    ok('All202 rows and12 cases in exact stored/embedded payload',explorer==embedded and len(explorer['index'])==202 and set(r['row_id'] for r in explorer['index'])==set(f.row_id) and len(explorer['cases'])==12)
    for pid,e in explorer['histories'].items():ok('Full explorer history '+pid,set(r['row_id'] for r in e['policies'])==set(h.loc[h.policy_id.eq(pid),'row_id']) and len(e['references'])==len(refs.loc[refs.policy_id.eq(pid)]) and len(e['bridges'])==len(bridge.loc[bridge.policy_id.eq(pid)]))
    ok('No operational data or external network resources created',not (out/'data').exists() and not re.search(r'(?:href|src)=[\"\x27]https?://',html))
    ok('Protected files and dataset indexes unchanged after checks',all(c.digest(c.ROOT/p)==sha for p,sha in protected.items()))
    result={'status':'passed_own_source_rechecks','passed':len(checks),'failed':0,'checks':checks,'data_modified':False,'independent_validation':False}
    c.dump(out/'verification.json',result);print(json.dumps({k:result[k] for k in ['status','passed','failed','data_modified']}))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
