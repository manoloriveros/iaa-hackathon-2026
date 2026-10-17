"""Revisa los 109 capitales con contexto previo distinto; no altera ninguna capa de datos."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import sys
import uuid

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import correct_capitals as cap
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

BASE=Path(__file__).parent
D48=ROOT/'Hackaton/Semana 1/Revision_capitales_pendientes/runs/pending_20261016T212234Z_3c7bd248'
REQUEST='Ahora revisemos los 109 capitales con apoyo posterior y cambios de contexto previo. Compara sus historiales, muestra casos concretos y propón cómo tratarlos sin modificar los datos todavía.'


def save(frame,out,name):
    frame.to_parquet(out/'tables'/(name+'.parquet'),index=False)
    frame.to_csv(out/'tables'/(name+'.csv'),index=False)


def comparison(current,reference,line):
    missing=[];changed=[];values={}
    for col in cap.FIELDS[line]:
        x,y=current[col],reference[col]
        if pd.isna(x) or pd.isna(y):missing.append(col);continue
        if col=='construction_type':x,y=str(x).casefold().strip(),str(y).casefold().strip()
        if x!=y:changed.append(col);values[col]={'focus':x,'reference':y}
    return {'missing_fields':'|'.join(missing),'changed_fields':'|'.join(changed),'complete':not missing,
            'same_known_context':not missing and not changed,
            'differences_json':json.dumps(values,ensure_ascii=False,default=lambda x:x.item())}


def main():
    index=c.BASE/'current_retrospective_dataset.json';pointer=json.loads(index.read_text('utf-8'))
    parent=ROOT/pointer['workspace_relative_run'];catpath=ROOT/pointer['catalog_workspace_relative']
    catalog=json.loads(catpath.read_text('utf-8'));assert cap.manifest_ok(parent) and cap.manifest_ok(D48)
    pending_path=parent/'tables/pending_capitals.parquet';pending=pd.read_parquet(pending_path)
    cohort=pending.loc[pending.review_group.eq('B_later_with_prior_conflict')].copy()
    assert len(pending)==576 and len(cohort)==cohort.row_id.nunique()==cohort.policy_id.nunique()==109
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('context_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['tables','evidence','source_snapshot','figures']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={path.relative_to(ROOT).as_posix():c.digest(path) for path in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:e['sha256'] for e in catalog.values()})
    for path in [index,c.BASE/'current_dataset.json',catpath,parent/'manifest.json',D48/'manifest.json',pending_path,
                 c.BASE/'current_numeric_capital_correction.json']:
        protected[path.relative_to(ROOT).as_posix()]=c.digest(path)
    assert all(c.digest(ROOT/path)==sha for path,sha in protected.items())
    c.dump(out/'protected_hashes_before.json',protected)
    copies={'retrospective_index.json':index,'base_index.json':c.BASE/'current_dataset.json','dataset_catalog.json':catpath,
        'CAP03R_manifest.json':parent/'manifest.json','D48_manifest.json':D48/'manifest.json',
        'frozen_576_pending.parquet':pending_path,'D48_assessment.parquet':D48/'tables/pending_assessment.parquet',
        'CAP01_ledger.parquet':parent/'evidence/CAP01_ledger.parquet','prior_retrospective_ledger.parquet':parent/'ledger/cumulative_retrospective_changes.parquet',
        'data-description.md':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'}
    for name,path in copies.items():shutil.copy2(path,out/'evidence'/name)
    shutil.copy2(__file__,out/'source_snapshot'/Path(__file__).name)
    c.dump(out/'request.json',{'messages':[{'role':'user','content':REQUEST}],
        'scope':'Review exact 109 frozen D48 group B rows still pending in CAP03R, with complete histories, cases and proposal. No values or dataset indexes changed.'})
    save(cohort,out,'frozen_109_cohort');save(pending,out,'remaining_576_inventory')
    save(pending.loc[~pending.row_id.isin(cohort.row_id)],out,'other_467_inventory')
    fixed=pd.read_parquet(out/'evidence/CAP01_ledger.parquet')[['row_id','rule']]
    retrofixed=pd.read_parquet(out/'evidence/prior_retrospective_ledger.parquet')[['row_id','rule']]
    repair=pd.concat([fixed,retrofixed],ignore_index=True).set_index('row_id').rule
    frames=[]
    for line in ['buildings','contents']:
        ids=set(cohort.loc[cohort.line.eq(line),'policy_id'])
        for prefix in ['policies','test']:
            name=prefix+'_'+line;frame=pq.read_table(ROOT/catalog[name]['workspace_relative_path']).to_pandas()
            frame=frame.loc[frame.policy_id.isin(ids)].copy();frame['source_table']=name;frame['line']=line
            for col in ['period_start','period_end']:frame[col]=pd.to_datetime(frame[col]).dt.as_unit('ns')
            raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured']).to_pandas().set_index('row_id')
            frame['original_capital_CU']=frame.row_id.map(raw.sum_insured)
            frame['capital_repair_rule']=frame.row_id.map(repair)
            frames.append(frame)
    hist=pd.concat(frames,ignore_index=True).sort_values(['policy_id','period_start','row_id']).reset_index(drop=True)
    hist['year']=hist.period_start.dt.year;hist['covered_days']=(hist.period_end-hist.period_start).dt.days+1
    hist['focus_109']=hist.row_id.isin(cohort.row_id);hist['pending_576']=hist.row_id.isin(pending.row_id)
    save(hist,out,'all_policy_histories')
    lookup=hist.set_index('row_id');groups={pid:g.reset_index(drop=True) for pid,g in hist.groupby('policy_id',sort=False)}
    addresses=pq.read_table(ROOT/catalog['addresses']['workspace_relative_path']).to_pandas().set_index('address_id')
    save(addresses.loc[addresses.index.isin(hist.address_id)].reset_index(),out,'address_context')
    assessments=[];stages=[];intermediates=[]
    for _,q in cohort.iterrows():
        current=lookup.loc[q.row_id];previous=lookup.loc[q.original_prior_row_id];later=lookup.loc[q.original_later_row_id]
        g=groups[q.policy_id];i=g.index[g.row_id.eq(q.row_id)][0];j=g.index[g.row_id.eq(q.original_later_row_id)][0]
        immediate=g.loc[i-1]
        rec={'row_id':q.row_id,**current.to_dict()}
        rec['frozen_group']='B_later_with_prior_conflict';rec['hypothetical_div1000_CU']=float(current.sum_insured/1000)
        rec['prior_row_id']=q.original_prior_row_id;rec['prior_capital_CU']=float(previous.sum_insured)
        rec['prior_period_start']=previous.period_start;rec['prior_period_end']=previous.period_end
        rec['prior_address_id']=previous.address_id;rec['prior_customer_id']=previous.customer_id
        rec['later_row_id']=q.original_later_row_id;rec['later_capital_CU']=float(later.sum_insured)
        rec['later_period_start']=later.period_start;rec['later_period_end']=later.period_end;rec['later_source_table']=later.source_table
        rec['later_address_id']=later.address_id;rec['later_customer_id']=later.customer_id
        rec['test2025_reference']=later.source_table.startswith('test_') and later.year==2025
        rec['prior_start_gap_days']=int((current.period_start-previous.period_start).days)
        rec['later_start_gap_days']=int((later.period_start-current.period_start).days)
        rec['later_after_current_end']=bool(later.period_start>current.period_end)
        rec['later_original_unrepaired']=bool(later.sum_insured==later.original_capital_CU and pd.isna(later.capital_repair_rule))
        rec['hypothetical_vs_prior_pct']=float(100*((current.sum_insured/1000)/previous.sum_insured-1))
        rec['later_vs_hypothetical_pct']=float(100*(later.sum_insured/(current.sum_insured/1000)-1))
        rec['hypothetical_over_later']=float((current.sum_insured/1000)/later.sum_insured)
        for direction,ref in [('prior',previous),('later',later),('immediate_prior',immediate)]:
            for key,value in comparison(current,ref,current.line).items():rec[direction+'_'+key]=value
        rec['immediate_prior_row_id']=immediate.row_id;rec['immediate_prior_capital_CU']=float(immediate.sum_insured)
        rec['immediate_prior_is_pending']=bool(immediate.pending_576);rec['immediate_prior_is_frozen_normal']=immediate.row_id==previous.name
        rec['intervening_before_later_rows']=j-i-1
        rec['address_change_from_original_prior']=current.address_id!=previous.address_id
        if current.line=='contents':rec['review_pattern']='contents_address_change'
        elif not rec['address_change_from_original_prior']:rec['review_pattern']='buildings_TW_only'
        else:rec['review_pattern']='buildings_'+rec['prior_changed_fields'].replace('|','_')
        for label,addr in [('prior',previous.address_id),('current',current.address_id)]:
            for field in ['property_type','bedrooms','year_built','region','flood_zone','listed_building','roof_type']:
                rec[label+'_address_'+field]=addresses.loc[addr,field]
        rec['prior_premium_CU']=float(previous.written_premium);rec['later_premium_CU']=float(later.written_premium)
        rec['premium_vs_prior_pct']=float(100*(current.written_premium/previous.written_premium-1))
        rec['premium_vs_later_pct']=float(100*(current.written_premium/later.written_premium-1))
        rec['later_premium_comparable_long_periods']=bool(current.covered_days>=300 and later.covered_days>=300 and .95<=current.covered_days/later.covered_days<=1.05)
        rec['candidate_retrospective_scale_only_NOT_APPLIED']=bool(rec['later_same_known_context'] and rec['later_original_unrepaired'] and
            rec['later_after_current_end'] and 1<=rec['later_start_gap_days']<=400 and .9<=rec['hypothetical_over_later']<=1.1 and j==i+1)
        rec['correction_authorized']=False;rec['capital_change_applied']=False
        assessments.append(rec)
        for role,row in [('prior_original_normal',previous),('immediate_prior',immediate),('focus',current),('later_original_normal',later)]:
            stages.append({'focus_row_id':q.row_id,'comparison_role':role,'row_id':row.get('row_id',row.name),**row.to_dict()})
        for _,row in g.loc[i+1:j-1].iterrows():intermediates.append({'focus_row_id':q.row_id,**row.to_dict()})
    assessment=pd.DataFrame(assessments)
    save(assessment,out,'context_assessment');save(pd.DataFrame(stages),out,'comparison_stages')
    proposal_cols=['row_id','policy_id','line','source_table','sum_insured','hypothetical_div1000_CU','prior_row_id','prior_capital_CU',
        'prior_changed_fields','prior_missing_fields','later_row_id','later_capital_CU','later_source_table','later_period_start',
        'later_start_gap_days','later_same_known_context','later_original_unrepaired','test2025_reference','review_pattern',
        'immediate_prior_row_id','immediate_prior_is_pending','capital_change_applied','correction_authorized']
    save(assessment.loc[assessment.candidate_retrospective_scale_only_NOT_APPLIED,proposal_cols],out,'proposed_scale_changes_NOT_APPLIED')
    claims=pq.read_table(ROOT/catalog['claims']['workspace_relative_path']).to_pandas()
    claims=claims.loc[claims.policy_id.isin(cohort.policy_id)].copy()
    for col in ['loss_date','report_date']:claims[col]=pd.to_datetime(claims[col])
    links=claims[['claim_id','policy_id','line','loss_date']].merge(hist[['row_id','policy_id','line','period_start','period_end']],on=['policy_id','line'],how='left')
    hits=links.loc[links.loss_date.between(links.period_start,links.period_end),['claim_id','row_id']];assert hits.claim_id.is_unique
    claims=claims.merge(hits,on='claim_id',how='left',validate='one_to_one')
    claims['accepted']=claims.status.isin(['open','closed']);claims['observed_net_accepted_CU']=np.where(claims.accepted,claims.incurred_to_date-claims.recoveries,0.)
    claims['focus_109']=claims.row_id.isin(cohort.row_id)
    claims['hypothetical_capital_CU']=claims.row_id.map(assessment.set_index('row_id').hypothetical_div1000_CU)
    claims['incurred_above_hypothetical_capital']=claims.accepted&claims.incurred_to_date.gt(claims.hypothetical_capital_CU)
    claims['diagnostic_only_not_used_to_select_correction']=True
    save(claims,out,'all_claim_histories')
    pattern_counts=assessment.groupby(['review_pattern','line']).agg(rows=('row_id','size'),test2025_references=('test2025_reference','sum')).reset_index()
    save(pattern_counts,out,'pattern_counts')
    summary={'scope':'Review only of exact 109 group-B rows in CAP03R; no modification or cohort expansion.',
        'rows':109,'policies':cohort.policy_id.nunique(),'by_line':cohort.line.value_counts().to_dict(),'history_rows':len(hist),
        'patterns':assessment.review_pattern.value_counts().to_dict(),'address_changes':int(assessment.address_change_from_original_prior.sum()),
        'TW_only_rows':int(assessment.review_pattern.eq('buildings_TW_only').sum()),
        'prior_missing_rows':int(assessment.prior_missing_fields.ne('').sum()),'later_complete_equal_rows':int(assessment.later_same_known_context.sum()),
        'later_original_unrepaired_rows':int(assessment.later_original_unrepaired.sum()),
        'immediate_later_reference_rows':int(assessment.intervening_before_later_rows.eq(0).sum()),
        'test2025_references':int(assessment.test2025_reference.sum()),
        'test2025_by_line':assessment.loc[assessment.test2025_reference].line.value_counts().to_dict(),
        'candidate_rows_NOT_APPLIED':int(assessment.candidate_retrospective_scale_only_NOT_APPLIED.sum()),
        'contents_same_hypothetical_and_prior_rows':int((assessment.line.eq('contents')&assessment.hypothetical_vs_prior_pct.eq(0)).sum()),
        'normal_reference_skips_immediate_prior_rows':int((~assessment.immediate_prior_is_frozen_normal).sum()),
        'claims':len(claims),'claims_in_focus_periods':int(claims.focus_109.sum()),
        'accepted_incurred_above_hypothetical_capital':int(claims.incurred_above_hypothetical_capital.sum()),
        'claims_before_observed_history':int(claims.row_id.isna().sum()),'capital_repaired_context_rows':int(hist.capital_repair_rule.notna().sum()),
        'retrospective_pending_unchanged':576,'baseline_pending_unchanged':1454,'other_pending_not_reviewed':467,
        'values_changed':0,'dataset_indexes_changed':False,'CON01_activated':False,'models_trained':False,'independent_validation':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'proposal.json',{'status':'review_only_no_application_authorization',
        'recommendation':'Propose exactly the frozen candidate list for a separate retrospective /1000 scale-only operation, retaining every prior and later value, risk field, date and claim.',
        'why_prior_change_is_not_unit_disproof':'Previous values describe an old address or a different construction code. The independent later original row describes the focus context and supports its monetary scale. Do not copy the old risk limit.',
        'TW':'Do not merge T and W. For the 31 cases, the later W row validates the scale under the same recorded code, without confirming material semantics.',
        'missing_previous_fields':'Three old-risk rows lack smoke_alarms. Keep nulls; the candidate comparison to the later current-risk row is complete and does not require imputing the old property.',
        'special_case':'B19256617: candidate B01414378 can be considered using original later B02040322; preceding B00962235 remains a separate uncorrected pending capital. No cascading correction.',
        'future_evidence':'All later references are future at focus-period start; 17 use test 2025. Retrospective only, not approved causal backtest preparation.',
        'claims':'Separate diagnostic only; do not use realized losses or premium values to select/adjust capital repairs. No loss clipping or scaling.',
        'remaining':'Keep all 576 pending in this review; 467 outside the current 109 receive no new individual adjudication.',
        'source_confirmation_pending':['Currency unit/serialization factor','Capital change endorsements at address changes','Meaning of T/W construction coding','Any monetary limits or sublimits beyond sum_insured'],
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    c.dump(out/'protocol.json',{'cohort':'Exact frozen D48 B_later_with_prior_conflict IDs still pending under current CAP03R.',
        'fields':cap.FIELDS,'normal_reference':'Unrepaired original amount, same policy and line.',
        'candidate_criterion':'Immediate next original normal row, complete equal specified context, same policy/line, later start after current end, 1–400 start-day gap, (capital/1000)/reference within 0.90–1.10.',
        'earlier_comparison':'Retain original normal and immediately previous rows separately; do not assume either describes the focus risk.',
        'construction':'Only trim/casefold for comparison; T and W remain distinct.',
        'master_context':'Address master lacks historical effective dates; attributes only contextual, not proof of true old/new property value.',
        'hypothetical_only':True,'no_claim_or_premium_selection':True,'no_original_or_derived_changes':True})
    assert all(c.digest(ROOT/path)==sha for path,sha in protected.items())
    print(json.dumps({'run':str(out),'summary':summary},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
