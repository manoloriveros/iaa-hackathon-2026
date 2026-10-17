"""Revisa48 filas completas; regla distante candidata, sin aplicar correcciones."""
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
D56=ROOT/'Hackaton/Semana 1/Revision_contexto_incompleto/runs/incomplete_20261016T230501Z_37407a29'
THRESHOLDS={'buildings':10_000_000,'contents':1_000_000}
REQUEST='Revisemos al detalle las 48 filas completas con referencias a más de 400 días. Compara sus historiales y propón cuándo tendría sentido corregir la escala, sin modificar los datos todavía.'
def save(f,out,name):
    f.to_parquet(out/'tables'/(name+'.parquet'),index=False);f.to_csv(out/'tables'/(name+'.csv'),index=False)
def compare(x,y,line):
    missing=[];changed=[]
    for col in cap.FIELDS[line]:
        a,b=x[col],y[col]
        if pd.isna(a) or pd.isna(b):missing.append(col);continue
        if col=='construction_type':a,b=str(a).strip().casefold(),str(b).strip().casefold()
        if a!=b:changed.append(col)
    return missing,changed
def main():
    index=c.BASE/'current_retrospective_dataset.json';idx=json.loads(index.read_text('utf-8'));parent=ROOT/idx['workspace_relative_run'];catpath=ROOT/idx['catalog_workspace_relative'];cat=json.loads(catpath.read_text('utf-8'))
    assert idx['capital_rule']=='CAP04R' and cap.manifest_ok(parent) and cap.manifest_ok(D56)
    prior=pd.read_parquet(D56/'tables/incomplete_assessment.parquet');cohort=prior.loc[prior.review_tier.eq('A_focus_complete_distant_anchor')].copy()
    pending=pd.read_parquet(parent/'tables/pending_capitals.parquet')
    assert len(pending)==467 and len(cohort)==cohort.row_id.nunique()==cohort.policy_id.nunique()==48 and set(cohort.row_id).issubset(set(pending.row_id))
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('distant_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['tables','evidence','source_snapshot','figures']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')};protected.update({e['workspace_relative_path']:e['sha256'] for e in cat.values()})
    for p in [index,c.BASE/'current_dataset.json',catpath,parent/'manifest.json',D56/'manifest.json',D56/'tables/incomplete_assessment.parquet',
        parent/'tables/pending_capitals.parquet',ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',ROOT/'Preparación/src/iaa_lab/predictor_guard.py']:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items());c.dump(out/'protected_hashes_before.json',protected)
    copies={'retrospective_index.json':index,'base_index.json':c.BASE/'current_dataset.json','dataset_catalog.json':catpath,
        'CAP04R_manifest.json':parent/'manifest.json','D56_manifest.json':D56/'manifest.json','D56_assessment.parquet':D56/'tables/incomplete_assessment.parquet',
        'D56_references.parquet':D56/'tables/all_original_references.parquet','frozen_467_pending.parquet':parent/'tables/pending_capitals.parquet',
        'D56_proposal.json':D56/'proposal.json','data-description.md':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'}
    for name,p in copies.items():shutil.copy2(p,out/'evidence'/name)
    shutil.copy2(__file__,out/'source_snapshot'/Path(__file__).name)
    c.dump(out/'request.json',{'messages':[{'role':'user','content':REQUEST}],'scope':'Review exact48 frozen D56 rows, evaluate a bounded two-calendar-year scale hypothesis, preserve all current data, protocol and dataset indexes.'})
    save(cohort,out,'frozen_48_cohort');save(pending,out,'remaining_467_inventory');save(pending.loc[~pending.row_id.isin(cohort.row_id)],out,'other_419_inventory')
    parts=[]
    for line in ['buildings','contents']:
        for prefix in ['policies','test']:
            name=prefix+'_'+line;f=pq.read_table(ROOT/cat[name]['workspace_relative_path'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
            f['source_table']=name;f['line']=line
            for col in ['period_start','period_end']:f[col]=pd.to_datetime(f[col]).dt.as_unit('ns')
            raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas().set_index('row_id').sum_insured
            f['original_capital_CU']=f.row_id.map(raw);parts.append(f)
    history=pd.concat(parts,ignore_index=True).sort_values(['policy_id','period_start','row_id']).reset_index(drop=True)
    history['year']=history.period_start.dt.year;history['focus_48']=history.row_id.isin(cohort.row_id);history['pending_467']=history.row_id.isin(pending.row_id)
    assert len(history)==210 and history.sum_insured.eq(history.original_capital_CU).all();save(history,out,'all_policy_histories')
    references=[];evaluations=[];nodes=[];edges=[];assessments=[]
    for _,cur in history.loc[history.focus_48].iterrows():
        g=history.loc[history.policy_id.eq(cur.policy_id)].sort_values('period_start');normal=g.loc[g.original_capital_CU.gt(0)&g.original_capital_CU.le(THRESHOLDS[cur.line])&g.row_id.ne(cur.row_id)]
        assert cur[cap.FIELDS[cur.line]].notna().all()
        local=[]
        for _,ref in normal.iterrows():
            missing,changed=compare(cur,ref,cur.line);gap=abs((cur.period_start-ref.period_start).days);ratio=(cur.sum_insured/1000)/ref.sum_insured
            local.append({'focus_row_id':cur.row_id,'policy_id':cur.policy_id,'line':cur.line,'reference_row_id':ref.row_id,'reference_source_table':ref.source_table,
                'reference_period_start':ref.period_start,'reference_period_end':ref.period_end,'reference_capital_CU':float(ref.sum_insured),
                'direction':'prior' if ref.period_start<cur.period_start else 'later','start_gap_days':gap,'ratio_hypothetical_over_reference':float(ratio),
                'reference_fields_complete':bool(ref[cap.FIELDS[cur.line]].notna().all()),'missing_fields':'|'.join(missing),'changed_fields':'|'.join(changed),
                'strict_400day_support':bool(not missing and not changed and 1<=gap<=400 and .9<=ratio<=1.1),
                'complete_context_compatible':not missing and not changed,'numeric_compatible':bool(.9<=ratio<=1.1)})
        references.extend(local);directions=[]
        for direction in ['prior','later']:
            # Choose chronology and completeness before context/numeric compatibility.
            eligible=[r for r in local if r['direction']==direction and r['reference_fields_complete']]
            if not eligible:continue
            refinfo=min(eligible,key=lambda r:r['start_gap_days']);ref=g.loc[g.row_id.eq(refinfo['reference_row_id'])].iloc[0]
            lo,hi=min(cur.period_start,ref.period_start),max(cur.period_start,ref.period_start)
            chain=g.loc[g.period_start.between(lo,hi)].copy();mid=chain.loc[~chain.row_id.isin([cur.row_id,ref.row_id])]
            no_known_conflict=True;all_mid_incomplete=True;mid_original_normal=True
            for _,m in mid.iterrows():
                missing,changed=compare(cur,m,cur.line);no_known_conflict &= not changed;all_mid_incomplete &= bool(missing)
                mid_original_normal &= 0<m.original_capital_CU<=THRESHOLDS[cur.line] and m.sum_insured==m.original_capital_CU
                nodes.append({'focus_row_id':cur.row_id,'direction':direction,'selected_reference_row_id':ref.row_id,'intermediate_row_id':m.row_id,
                    'period_start':m.period_start,'period_end':m.period_end,'capital_CU':float(m.sum_insured),'missing_fields':'|'.join(missing),'changed_fields':'|'.join(changed)})
            chain_values=chain.sum_insured.to_numpy().copy();chain_values[chain.row_id.eq(cur.row_id).to_numpy()]/=1000
            numeric_edges=True;calendar_edges=True
            for j in range(1,len(chain)):
                left,right=chain.iloc[j-1],chain.iloc[j];uncovered=int((right.period_start-left.period_end).days-1);ratio=chain_values[j]/chain_values[j-1]
                allowed=bool(uncovered==0 or (uncovered==1 and left.period_end==pd.Timestamp('2024-12-30') and right.period_start==pd.Timestamp('2025-01-01')))
                calendar_edges &= allowed;numeric_edges &= .9<=ratio<=1.1
                edges.append({'focus_row_id':cur.row_id,'direction':direction,'selected_reference_row_id':ref.row_id,'from_row_id':left.row_id,'to_row_id':right.row_id,
                    'from_capital_hypothesis_CU':float(chain_values[j-1]),'to_capital_hypothesis_CU':float(chain_values[j]),'ratio_next_over_prior':float(ratio),
                    'uncovered_days':uncovered,'calendar_edge_allowed_with_CAL00_pending':allowed,'numeric_edge_within_10pct':bool(.9<=ratio<=1.1)})
            within_two_years=hi<=lo+pd.DateOffset(years=2)
            tests={'complete_equal_endpoints':refinfo['complete_context_compatible'],'ratio_endpoints_within_10pct':refinfo['numeric_compatible'],
                'distance_above_400':refinfo['start_gap_days']>400,'within_two_calendar_years':bool(within_two_years),
                'one_intermediate_original_row':len(mid)==1,'intermediate_context_missing_without_known_change':bool(all_mid_incomplete and no_known_conflict),
                'intermediate_original_normal':bool(mid_original_normal),'each_capital_step_within_10pct':bool(numeric_edges),
                'dates_no_overlap_or_new_gap':bool(calendar_edges)}
            ev={**refinfo,**tests,'intermediate_rows':len(mid),'failure_reasons':'|'.join(k for k,v in tests.items() if not v),
                'candidate_NOT_APPLIED':all(tests.values()),'reference_test2025':bool(ref.source_table.startswith('test_') and ref.year==2025),
                'reference_is_future_at_focus_start':direction=='later','correction_authorized':False,'capital_change_applied':False}
            evaluations.append(ev);directions.append(ev)
        valid=[d for d in directions if d['candidate_NOT_APPLIED']]
        selected=min(valid,key=lambda d:d['start_gap_days']) if valid else min(directions,key=lambda d:d['start_gap_days'])
        rec=cur.to_dict();rec.update({'hypothetical_div1000_CU':float(cur.sum_insured/1000),'review_status':'PROPOSE_RETROSPECTIVE_SCALE_ONLY' if valid else 'HOLD_NUMERIC_CONFLICT',
            'selected_reference_row_id':selected['reference_row_id'],'selected_reference_source_table':selected['reference_source_table'],
            'selected_reference_period_start':selected['reference_period_start'],'selected_reference_capital_CU':selected['reference_capital_CU'],
            'selected_reference_direction':selected['direction'],'selected_start_gap_days':selected['start_gap_days'],
            'selected_reference_test2025':selected['reference_test2025'],'selected_reference_future':selected['reference_is_future_at_focus_start'],
            'selected_intermediate_rows':selected['intermediate_rows'],'failure_reasons':selected['failure_reasons'],
            'candidate_NOT_APPLIED':bool(valid),'correction_authorized':False,'capital_change_applied':False})
        assessments.append(rec)
    assessment=pd.DataFrame(assessments);ref_frame=pd.DataFrame(references);eval_frame=pd.DataFrame(evaluations);edge_frame=pd.DataFrame(edges);node_frame=pd.DataFrame(nodes)
    save(assessment,out,'assessment_48');save(ref_frame,out,'all_original_references');save(eval_frame,out,'direction_evaluations');save(node_frame,out,'intermediate_nodes');save(edge_frame,out,'chain_edges')
    cols=['row_id','policy_id','line','source_table','sum_insured','hypothetical_div1000_CU','selected_reference_row_id','selected_reference_source_table',
        'selected_reference_period_start','selected_reference_capital_CU','selected_reference_direction','selected_start_gap_days',
        'selected_reference_test2025','selected_reference_future','correction_authorized','capital_change_applied']
    candidates=assessment.loc[assessment.candidate_NOT_APPLIED,cols].copy()
    save(candidates,out,'proposed_scale_changes_NOT_APPLIED');save(candidates.loc[candidates.selected_reference_test2025],out,'proposed_test2025_supported_NOT_APPLIED')
    save(assessment.loc[~assessment.candidate_NOT_APPLIED],out,'held_numeric_conflicts')
    addresses=pq.read_table(ROOT/cat['addresses']['workspace_relative_path'],filters=[('address_id','in',history.address_id.unique().tolist())]).to_pandas();save(addresses,out,'address_context')
    claims=pq.read_table(ROOT/cat['claims']['workspace_relative_path'],filters=[('policy_id','in',cohort.policy_id.tolist())]).to_pandas()
    for col in ['loss_date','report_date']:claims[col]=pd.to_datetime(claims[col]).dt.as_unit('ns')
    cl=claims[['claim_id','policy_id','line','loss_date']].merge(history[['row_id','policy_id','line','period_start','period_end']],on=['policy_id','line'],how='left')
    hits=cl.loc[cl.loss_date.between(cl.period_start,cl.period_end),['claim_id','row_id']];assert hits.claim_id.is_unique
    claims=claims.merge(hits,on='claim_id',how='left',validate='one_to_one');claims['focus_48']=claims.row_id.isin(cohort.row_id);claims['diagnostic_only_not_used_for_selection']=True;save(claims,out,'all_claim_histories')
    ce=edge_frame.merge(candidates[['row_id','selected_reference_row_id']].rename(columns={'row_id':'focus_row_id','selected_reference_row_id':'selected_reference_row_id'}),on=['focus_row_id','selected_reference_row_id'],how='inner')
    summary={'rows':48,'policies':48,'by_line':assessment.line.value_counts().to_dict(),'history_rows':len(history),'original_reference_pairs':len(ref_frame),
        'candidates_NOT_APPLIED':len(candidates),'candidate_by_line':candidates.line.value_counts().to_dict(),
        'candidate_direction_counts':candidates.selected_reference_direction.value_counts().to_dict(),'held_rows':int((~assessment.candidate_NOT_APPLIED).sum()),
        'candidate_gap_min_days':int(candidates.selected_start_gap_days.min()),'candidate_gap_max_days':int(candidates.selected_start_gap_days.max()),
        'test2025_focus_rows':int(assessment.source_table.str.startswith('test_').sum()),'test2025_candidate_anchor_rows':int(candidates.selected_reference_test2025.sum()),
        'test2025_candidate_anchor_by_line':candidates.loc[candidates.selected_reference_test2025].line.value_counts().to_dict(),
        'selected_candidate_edges':len(ce),'candidate_uncovered_day_counts':ce.uncovered_days.value_counts().to_dict(),
        'candidate_step_growth_min_pct':float(100*(ce.ratio_next_over_prior.min()-1)),'candidate_step_growth_max_pct':float(100*(ce.ratio_next_over_prior.max()-1)),
        'claims':len(claims),'claims_in_focus_periods':int(claims.focus_48.sum()),'retrospective_pending_unchanged':467,'other_pending_not_adjudicated':419,
        'base_pending_unchanged':1454,'values_changed':0,'dataset_indexes_changed':False,'live_400day_rule_changed':False,'models_trained':False,'independent_validation':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'protocol.json',{'status':'CANDIDATE_RULE_NOT_ACTIVATED','rule_name':'DIST01-R proposal v1','cohort':'Exact48 D56 complete-focus/distant-reference rows, no expansion.',
        'reference_choice':'Nearest original ordinary row with all named fields known in each direction BEFORE checking context or amount; never skip a nearer complete contradiction.',
        'fields':cap.FIELDS,'screen_thresholds_CU':THRESHOLDS,'distance':'More than400 days and at most two calendar years between starts. This is a proposed exception, not a verified official rule.',
        'path':'Exactly one intermediate original ordinary row, incomplete but without known field changes versus focus. Do not impute it.',
        'endpoints':'Focus and anchor complete/equal for named fields, same policy and line; /1000 versus original anchor within0.90–1.10.',
        'amount_path':'After hypothetical scaling of focus only, each chronological step is within0.90–1.10. Preserve every other original amount.',
        'calendar':'No overlap or new gap; retain known single uncovered31-12-2024 as CAL00 pending, never call it fully covered.',
        'limitations':'Named context is partial; equal endpoints do not prove every unobserved event or contract term. No outcome/premium filtering, no T/W merge, no cascade, no source-unit confirmation.'})
    c.dump(out/'proposal.json',{'status':'review_only_no_application_authorization','recommendation':'Propose exact46 frozen rows for a separately authorized retrospective /1000 operation under DIST01-R; retain2 numeric-conflict cases pending.',
        'why':'Both endpoints have observed complete matching context. Missing intermediate fields stay unknown; they are not the corrected risk attributes. Chronology and monetary steps provide supporting evidence only.',
        'held':'C50633171/C00502745 and C56600576/C00399729 have nearer complete2022 endorsed limits39400 and37700 incompatible with hypothetical27200 and25700. Later2023 values28300/26700 cannot erase those observations.',
        'temporal':'21 selected anchors are prior observations,25 are later;7 later anchors are test2025. Prior dates alone do not certify historical F0 availability or a causal rule learned at the time.',
        'preserve':'All467 remain pending now, including108 previously held, other154 context-incomplete rows and all other groups. Preserve gaps, nulls, dates, claims and both dataset indexes.',
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    print(json.dumps({'run':str(out),'summary':summary},ensure_ascii=False))
if __name__=='__main__':main()
