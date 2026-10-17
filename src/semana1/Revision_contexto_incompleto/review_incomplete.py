"""Revisión de202 contextos incompletos y actualización documental de pendientes."""
from datetime import datetime,timezone
from pathlib import Path
import json,shutil,sys,uuid
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import correct_capitals as cap
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
BASE=Path(__file__).parent
D48=ROOT/'Hackaton/Semana 1/Revision_capitales_pendientes/runs/pending_20261016T212234Z_3c7bd248'
D40=ROOT/'Hackaton/Semana 1/Validacion_datos/runs/gaps_20261016T193906Z_70462cf9'
D55=ROOT/'Hackaton/Semana 1/Revision_sin_referencia/runs/noanchor_20261016T221747Z_595339db'
THRESHOLDS={'buildings':10_000_000,'contents':1_000_000}
REQUEST='Dejemos los 108 pendientes y revisemos los 202 capitales con contexto incompleto. Compara sus historiales, muestra casos concretos y propón cómo tratarlos sin modificar los datos todavía. y enlista las validaciones que nos faltan'
def save(frame,out,name):
    frame.to_parquet(out/'tables'/(name+'.parquet'),index=False);frame.to_csv(out/'tables'/(name+'.csv'),index=False)
def compare(x,y,line,skip=()):
    missing=[];changed=[]
    for col in cap.FIELDS[line]:
        if col in skip:continue
        left,right=x[col],y[col]
        if pd.isna(left) or pd.isna(right):missing.append(col);continue
        if col=='construction_type':left,right=str(left).strip().casefold(),str(right).strip().casefold()
        if left!=right:changed.append(col)
    return missing,changed
def main():
    index=c.BASE/'current_retrospective_dataset.json';idx=json.loads(index.read_text('utf-8'));parent=ROOT/idx['workspace_relative_run'];catpath=ROOT/idx['catalog_workspace_relative'];cat=json.loads(catpath.read_text('utf-8'))
    assert idx['capital_rule']=='CAP04R' and all(cap.manifest_ok(p) for p in [parent,D48,D40,D55])
    pending=pd.read_parquet(parent/'tables/pending_capitals.parquet');cohort=pending.loc[pending.review_group.eq('F_incomplete_context')].copy()
    kept108=pd.read_parquet(D55/'tables/frozen_108_cohort.parquet')
    assert len(pending)==467 and len(cohort)==cohort.row_id.nunique()==cohort.policy_id.nunique()==202 and set(kept108.row_id).issubset(set(pending.row_id))
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('incomplete_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['tables','evidence','source_snapshot','figures']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')};protected.update({e['workspace_relative_path']:e['sha256'] for e in cat.values()})
    extra=[index,c.BASE/'current_dataset.json',catpath,parent/'manifest.json',parent/'tables/pending_capitals.parquet',D48/'manifest.json',D40/'manifest.json',D55/'manifest.json',
        D40/'review_controls.json',ROOT/'Preparación/src/iaa_lab/predictor_guard.py',ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json']
    for p in extra:protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items());c.dump(out/'protected_hashes_before.json',protected)
    copies={'retrospective_index.json':index,'base_index.json':c.BASE/'current_dataset.json','dataset_catalog.json':catpath,
        'CAP04R_manifest.json':parent/'manifest.json','D48_manifest.json':D48/'manifest.json','D40_manifest.json':D40/'manifest.json','D55_manifest.json':D55/'manifest.json',
        'frozen_467_pending.parquet':parent/'tables/pending_capitals.parquet','D48_assessment.parquet':D48/'tables/pending_assessment.parquet',
        'frozen_108_kept_pending.parquet':D55/'tables/frozen_108_cohort.parquet','D40_controls.json':D40/'review_controls.json',
        'state_before.json':ROOT/'Preparación/ESTADO_PROYECTO.json','protocol_1_8.json':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'predictor_guard.py':ROOT/'Preparación/src/iaa_lab/predictor_guard.py',
        'D50_report.md':ROOT/'Hackaton/Semana 1/Modelado/Investigacion_tecnicas_claude/INFORME.md',
        'data-description.md':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'}
    for name,p in copies.items():shutil.copy2(p,out/'evidence'/name)
    shutil.copy2(__file__,out/'source_snapshot'/Path(__file__).name)
    c.dump(out/'request.json',{'messages':[{'role':'user','content':REQUEST}],'scope':'Review exact202 groupF, keep108 D55 pending, reconcile58 D40 controls without modifying source/derived data, indexes, predictors or protocol.'})
    save(cohort,out,'frozen_202_cohort');save(pending,out,'remaining_467_inventory');save(pending.loc[~pending.row_id.isin(cohort.row_id)],out,'other_265_inventory')
    parts=[]
    for line in ['buildings','contents']:
        for prefix in ['policies','test']:
            name=prefix+'_'+line;f=pq.read_table(ROOT/cat[name]['workspace_relative_path'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
            f['source_table']=name;f['line']=line
            for col in ['period_start','period_end']:f[col]=pd.to_datetime(f[col]).dt.as_unit('ns')
            raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas().set_index('row_id').sum_insured
            f['original_capital_CU']=f.row_id.map(raw);parts.append(f)
    hist=pd.concat(parts,ignore_index=True).sort_values(['policy_id','period_start','row_id']).reset_index(drop=True)
    hist['year']=hist.period_start.dt.year;hist['focus_202']=hist.row_id.isin(cohort.row_id);hist['pending_467']=hist.row_id.isin(pending.row_id)
    assert len(hist)==844 and hist.sum_insured.eq(hist.original_capital_CU).all();save(hist,out,'all_policy_histories')
    references=[];bridges=[];ass=[]
    for _,cur in hist.loc[hist.focus_202].iterrows():
        group=hist.loc[hist.policy_id.eq(cur.policy_id)];missing=[col for col in cap.FIELDS[cur.line] if pd.isna(cur[col])]
        normals=group.loc[group.original_capital_CU.gt(0)&group.original_capital_CU.le(THRESHOLDS[cur.line])&group.row_id.ne(cur.row_id)]
        local=[]
        for _,ref in normals.iterrows():
            miss,changed=compare(cur,ref,cur.line);direction='prior' if ref.period_start<cur.period_start else 'later';gap=abs((cur.period_start-ref.period_start).days)
            temporal=ref.period_end<cur.period_start if direction=='prior' else cur.period_end<ref.period_start
            ratio=(cur.sum_insured/1000)/ref.sum_insured
            rec={'focus_row_id':cur.row_id,'policy_id':cur.policy_id,'line':cur.line,'reference_row_id':ref.row_id,'reference_source_table':ref.source_table,
                'reference_capital_CU':float(ref.sum_insured),'reference_period_start':ref.period_start,'direction':direction,'start_gap_days':gap,'nonoverlap':bool(temporal),
                'ratio_hypothetical_over_reference':float(ratio),'missing_fields':'|'.join(miss),'changed_fields':'|'.join(changed),
                'focus_missing_fields':'|'.join(col for col in cap.FIELDS[cur.line] if pd.isna(cur[col])),
                'reference_missing_fields':'|'.join(col for col in cap.FIELDS[cur.line] if pd.isna(ref[col])),
                'complete_equal_context':not miss and not changed,'nearest_original_in_direction':False,
                'reference_test2025':bool(ref.source_table.startswith('test_') and ref.year==2025),
                'missing_only_compatible':bool(miss and not changed and temporal and 1<=gap<=400 and .9<=ratio<=1.1),
                'strict_original_support':bool(not miss and not changed and temporal and 1<=gap<=400 and .9<=ratio<=1.1),
                'distant_complete_compatible':bool(not miss and not changed and temporal and gap>400 and .9<=ratio<=1.1)}
            local.append(rec)
        for direction in ['prior','later']:
            options=[r for r in local if r['direction']==direction]
            if options:min(options,key=lambda r:r['start_gap_days'])['nearest_original_in_direction']=True
        references.extend(local)
        for field in missing:
            before=group.loc[group.period_start.lt(cur.period_start)&group[field].notna()].sort_values('period_start')
            after=group.loc[group.period_start.gt(cur.period_start)&group[field].notna()].sort_values('period_start')
            prev=before.iloc[-1] if len(before) else None;nxt=after.iloc[0] if len(after) else None
            def usable(ref):return ref is not None and compare(cur,ref,cur.line,skip=missing)==([],[])
            if prev is not None and nxt is not None:
                state='BOTH_EQUAL_RECORDED_CONTEXT' if prev[field]==nxt[field] and usable(prev) and usable(nxt) else ('BOTH_DIFFERENT_VALUE' if prev[field]!=nxt[field] else 'BOTH_EQUAL_WITH_CONTEXT_CHANGE_OR_MISSING')
            elif prev is not None or nxt is not None:state='ONE_SIDED_KNOWN'
            else:state='NO_KNOWN_NEIGHBOR'
            bridges.append({'focus_row_id':cur.row_id,'policy_id':cur.policy_id,'field':field,'bridge_status':state,
                'prior_row_id':prev.row_id if prev is not None else None,'prior_value':str(prev[field]) if prev is not None else None,
                'later_row_id':nxt.row_id if nxt is not None else None,'later_value':str(nxt[field]) if nxt is not None else None,
                'prior_context_equal_excluding_focus_missing_fields':usable(prev),'later_context_equal_excluding_focus_missing_fields':usable(nxt),
                'imputation_applied':False,'equality_of_unobserved_value_proven':False})
        nearest=[r for r in local if r['nearest_original_in_direction']];compatible=[r for r in nearest if r['missing_only_compatible']]
        assert compatible
        distant=[r for r in local if r['distant_complete_compatible']]
        tier=('A_focus_complete_distant_anchor' if distant else 'B_focus_complete_only_incomplete_nearby') if not missing else 'C_focus_missing'
        rec=cur.to_dict();rec.update({'hypothetical_div1000_CU':float(cur.sum_insured/1000),'focus_missing_fields':'|'.join(missing),
            'review_tier':tier,'original_reference_count':len(local),'strict_original_support_count':sum(r['strict_original_support'] for r in local),
            'nearest_missing_only_compatible_pairs':len(compatible),'nearest_prior_missing_only_compatible':any(r['direction']=='prior' for r in compatible),
            'nearest_later_missing_only_compatible':any(r['direction']=='later' for r in compatible),
            'distant_complete_compatible_count':len(distant),'any_known_context_conflict':any(r['changed_fields'] for r in local),
            'nearby_later_test2025_missing_context':any(r['reference_test2025'] for r in compatible if r['direction']=='later'),
            'proposed_action':'KEEP_PENDING_NO_IMPUTATION_NO_WINDOW_EXTENSION','capital_change_applied':False,'correction_authorized':False})
        ass.append(rec)
    assessment=pd.DataFrame(ass);refs=pd.DataFrame(references);bridge=pd.DataFrame(bridges)
    save(assessment,out,'incomplete_assessment');save(refs,out,'all_original_references');save(bridge,out,'missing_field_bridges')
    plan=assessment[['row_id','policy_id','line','source_table','sum_insured','hypothetical_div1000_CU','review_tier','focus_missing_fields',
        'distant_complete_compatible_count','proposed_action','capital_change_applied','correction_authorized']];save(plan,out,'proposed_treatment_NOT_APPLIED')
    addresses=pq.read_table(ROOT/cat['addresses']['workspace_relative_path'],filters=[('address_id','in',hist.address_id.unique().tolist())]).to_pandas();save(addresses,out,'address_context')
    claims=pq.read_table(ROOT/cat['claims']['workspace_relative_path'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
    for col in ['loss_date','report_date']:claims[col]=pd.to_datetime(claims[col]).dt.as_unit('ns')
    link=claims[['claim_id','policy_id','line','loss_date']].merge(hist[['row_id','policy_id','line','period_start','period_end']],on=['policy_id','line'],how='left')
    hits=link.loc[link.loss_date.between(link.period_start,link.period_end),['claim_id','row_id']];assert hits.claim_id.is_unique
    claims=claims.merge(hits,on='claim_id',how='left',validate='one_to_one');claims['focus_202']=claims.row_id.isin(cohort.row_id)
    claims['hypothetical_capital_CU']=claims.row_id.map(assessment.set_index('row_id').hypothetical_div1000_CU)
    claims['accepted']=claims.status.isin(['open','closed']);claims['incurred_above_hypothetical_capital']=claims.accepted&claims.incurred_to_date.gt(claims.hypothetical_capital_CU)
    claims['diagnostic_only_not_used_for_selection']=True;save(claims,out,'all_claim_histories')
    summary={'rows':202,'policies':202,'by_line':assessment.line.value_counts().to_dict(),'by_source':assessment.source_table.value_counts().to_dict(),
        'history_rows':len(hist),'original_reference_pairs':len(refs),'strict_original_support_pairs':int(refs.strict_original_support.sum()),
        'focus_complete_rows':int(assessment.focus_missing_fields.eq('').sum()),'focus_missing_rows':int(assessment.focus_missing_fields.ne('').sum()),
        'focus_missing_masks':assessment.focus_missing_fields.value_counts().to_dict(),'review_tiers':assessment.review_tier.value_counts().to_dict(),
        'nearest_missing_only_compatible_pairs':int((refs.missing_only_compatible&refs.nearest_original_in_direction).sum()),
        'both_directions_missing_compatible_rows':int((assessment.nearest_prior_missing_only_compatible&assessment.nearest_later_missing_only_compatible).sum()),
        'distant_complete_compatible_rows':int(assessment.distant_complete_compatible_count.gt(0).sum()),'missing_field_bridge_records':len(bridge),
        'bridge_statuses':bridge.bridge_status.value_counts().to_dict(),'nearby_later_test2025_missing_context_rows':int(assessment.nearby_later_test2025_missing_context.sum()),
        'claims':len(claims),'claims_in_focus_periods':int(claims.focus_202.sum()),'claims_outside_history':int(claims.row_id.isna().sum()),
        'accepted_incurred_above_hypothetical_capital':int(claims.incurred_above_hypothetical_capital.sum()),
        'keep_108_pending':True,'retrospective_pending_unchanged':467,'other_pending_not_adjudicated':265,'base_pending_unchanged':1454,
        'values_changed':0,'dataset_indexes_changed':False,'automatic_repair_candidates':0,'models_trained':False,'independent_validation':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'proposal.json',{'status':'review_only_no_application_authorization','recommendation':'Keep202 pending; preserve all missing fields, current400-day criterion and108 D55 pending.',
        '71_complete_focus_rows':'Missingness belongs to comparison references;48 have complete compatible original references more than400 days away. These require separate evidence/rule review, not an implicit window extension.',
        '131_incomplete_focus_rows':'Recorded values on either side are evidence about those dates, not proof of the unobserved current value. No forward/backward filling or treating null as false/zero.',
        'other_references':'Retain all642 original references, known changes and temporal/numeric conflicts; no cherry-picking.',
        'claims':'Separate diagnostic only. No repair selected by losses/premiums; preserve dates, costs, labels and target.',
        'next_steps':['Confirm missingness and contract terms from source if obtainable','Prioritize48 complete-focus/distant-reference rows for a separately scoped methodological review','Keep ambiguous and missing-focus rows as unresolved; any model imputation must be train-cutoff specific and separate from source repair'],
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    c.dump(out/'protocol.json',{'cohort':'Exact202 D48 groupF still pending inCAP04R, no re-screening.',
        'fields':cap.FIELDS,'normal_original_screen_thresholds':THRESHOLDS,'strict_reference':'Original positive non-extreme capital in same policy/line, complete equal named fields, nonoverlap, start-gap1–400 days, (capital/1000)/reference0.90–1.10.',
        'nearest':'Nearest original ordinary reference in each direction; all other originals retained. Repairs never count as independent original anchors.',
        'bridge':'Nearest nonmissing field observations before/after focus; no imputation, persistence proof or equality claim at unobserved date.',
        'named_context_only':True,'T_W_remain_distinct':True,'no_claim_premium_selection':True,'no_imputation_window_extension_or_data_change':True})
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    print(json.dumps({'run':str(out),'summary':summary},ensure_ascii=False))
if __name__=='__main__':main()
