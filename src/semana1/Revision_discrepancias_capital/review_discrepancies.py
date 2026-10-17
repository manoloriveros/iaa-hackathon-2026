"""Revisión de los 12 conflictos numéricos dentro de 587 pendientes; no corrige datos."""
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
REQUEST='Revisemos los 587 capitales restantes, empezando por los 12 con discrepancias numéricas. Compara sus historiales, muestra casos concretos y propón cómo tratarlos sin modificar los datos todavía.'
FIELDS=cap.FIELDS['contents']


def save(frame,out,name):
    frame.to_parquet(out/'tables'/(name+'.parquet'),index=False)
    frame.to_csv(out/'tables'/(name+'.csv'),index=False)


def context(row,reference):
    missing=[];different=[]
    for col in FIELDS:
        if pd.isna(row[col]) or pd.isna(reference[col]):missing.append(col)
        elif row[col]!=reference[col]:different.append(col)
    return {'missing_fields':'|'.join(missing),'different_fields':'|'.join(different),
            'complete':not missing,'same_known_context':not missing and not different}


def main():
    retro_index=c.BASE/'current_retrospective_dataset.json';base_index=c.BASE/'current_dataset.json'
    pointer=json.loads(retro_index.read_text('utf-8'));retro=ROOT/pointer['workspace_relative_run']
    catalog_path=ROOT/pointer['catalog_workspace_relative'];cat=json.loads(catalog_path.read_text('utf-8'))
    assert cap.manifest_ok(retro) and cap.manifest_ok(D48)
    pending=pd.read_parquet(retro/'tables/pending_capitals.parquet')
    q=pending.loc[pending.original_review_route.eq('retrospective_support_only')&pending.nearest_prior_numeric_conflict].copy()
    assert len(pending)==587 and len(q)==q.row_id.nunique()==q.policy_id.nunique()==12 and q.line.eq('contents').all()
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('discrepancies_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['tables','evidence','source_snapshot','figures']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({entry['workspace_relative_path']:entry['sha256'] for entry in cat.values()})
    for p in [retro_index,base_index,catalog_path,retro/'manifest.json',D48/'manifest.json',retro/'tables/pending_capitals.parquet']:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    assert all(c.digest(ROOT/path)==sha for path,sha in protected.items())
    c.dump(out/'protected_hashes_before.json',protected)
    for name,path in {'retrospective_index.json':retro_index,'base_index.json':base_index,
        'dataset_catalog.json':catalog_path,'CAP02R_manifest.json':retro/'manifest.json','D48_manifest.json':D48/'manifest.json',
        'frozen_587_pending.parquet':retro/'tables/pending_capitals.parquet',
        'D48_assessment.parquet':D48/'tables/pending_assessment.parquet',
        'data-description.md':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'}.items():
        shutil.copy2(path,out/'evidence'/name)
    for name in ['review_discrepancies.py','render_discrepancies.py','verify_discrepancies.py','verify_report.js','record_discrepancies.py']:
        if (BASE/name).exists():shutil.copy2(BASE/name,out/'source_snapshot'/name)
    c.dump(out/'request.json',{'messages':[{'role':'user','content':REQUEST}],
        'scope':'Deep review of exact 12 D48 numeric conflicts, inventory of remaining 575; no capital, date, claim, source or dataset-index changes.'})
    save(pending,out,'remaining_587_inventory');save(q,out,'frozen_12_cohort')
    ids=set(q.policy_id);frames=[]
    for prefix in ['policies','test']:
        name=prefix+'_contents';frame=pq.read_table(ROOT/cat[name]['workspace_relative_path']).to_pandas()
        frame['source_table']=name
        for col in ['period_start','period_end']:frame[col]=pd.to_datetime(frame[col]).dt.as_unit('ns')
        raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured']).to_pandas().set_index('row_id')
        frame['original_capital_CU']=frame.row_id.map(raw.sum_insured)
        frames.append(frame)
    allrows=pd.concat(frames,ignore_index=True).sort_values(['policy_id','period_start','row_id']).reset_index(drop=True)
    allrows['year']=allrows.period_start.dt.year
    allrows['covered_days']=(allrows.period_end-allrows.period_start).dt.days+1
    allrows['pending_587']=allrows.row_id.isin(pending.row_id)
    allrows['focus_12']=allrows.row_id.isin(q.row_id)
    history=allrows.loc[allrows.policy_id.isin(ids)].copy()
    save(history,out,'all_12_policy_histories')
    groups={pid:g.sort_values('period_start').reset_index(drop=True) for pid,g in history.groupby('policy_id')}
    assessment=[];trios=[]
    for _,focus in q.iterrows():
        g=groups[focus.policy_id];position=g.index[g.row_id.eq(focus.row_id)][0]
        current=g.loc[position];before=g.loc[position-1];initial=g.loc[position-2];after=g.loc[position+1]
        row={'row_id':focus.row_id,'policy_id':focus.policy_id,'line':'contents','source_table':current.source_table,
            'period_start':current.period_start,'period_end':current.period_end,'reported_capital_CU':current.sum_insured,
            'hypothetical_div1000_CU':current.sum_insured/1000,'initial_row_id':initial.row_id,
            'initial_period_start':initial.period_start,'initial_period_end':initial.period_end,'initial_capital_CU':initial.sum_insured,
            'midterm_row_id':before.row_id,'midterm_period_start':before.period_start,'midterm_period_end':before.period_end,
            'midterm_capital_CU':before.sum_insured,'midterm_days':int(before.covered_days),
            'later_row_id':after.row_id,'later_source_table':after.source_table,'later_period_start':after.period_start,
            'later_capital_CU':after.sum_insured,'test2025_reference':after.source_table=='test_contents' and after.year==2025,
            'midterm_increase_pct':100*(before.sum_insured/initial.sum_insured-1),
            'hypothetical_vs_initial_pct':100*((current.sum_insured/1000)/initial.sum_insured-1),
            'hypothetical_vs_midterm_pct':100*((current.sum_insured/1000)/before.sum_insured-1),
            'later_vs_hypothetical_pct':100*(after.sum_insured/(current.sum_insured/1000)-1),
            'initial_premium_CU':initial.written_premium,'midterm_premium_CU':before.written_premium,
            'focus_premium_CU':current.written_premium,'later_premium_CU':after.written_premium,
            'midterm_premium_change_pct':100*(before.written_premium/initial.written_premium-1),
            'focus_premium_vs_midterm_pct':100*(current.written_premium/before.written_premium-1),
            'initial_decision':initial.renewal_decision,'midterm_decision':before.renewal_decision,
            'focus_renewal_increment':int(current.renewal_count-before.renewal_count),
            'capital_change_applied':False,'actual_contract_reset_confirmed':False}
        for label,reference in [('initial',initial),('midterm',before),('later',after)]:
            for key,value in context(current,reference).items():row[label+'_'+key]=value
        row['review_tier']='A_two_sided_sequence' if row['initial_same_known_context'] else 'B_initial_context_missing'
        row['proposed_treatment']=('Proponer /1000 como reparación exclusiva de escala en otra cohorte retrospectiva autorizada; conservar capitales normales y documentar la reversión de nivel por separado.' if row['review_tier']=='A_two_sided_sequence' else
            'Mantener condicionado: /1000 encaja con la secuencia, pero falta security_level en la referencia inicial; confirmar ese contexto o autorizar explícitamente el supuesto por separado.')
        assessment.append(row)
        for role,part in [('initial',initial),('midterm',before),('focus',current),('later',after)]:
            trios.append({'focus_row_id':focus.row_id,'role':role,**part.to_dict()})
    assessment=pd.DataFrame(assessment);save(assessment,out,'twelve_assessment');save(pd.DataFrame(trios),out,'four_stage_comparisons')
    # Population comparison selected by chronology/context, not by outcome of the 12 or claim amounts.
    prior=allrows.groupby('policy_id',sort=False).shift(1)
    earlier=allrows.groupby('policy_id',sort=False).shift(2)
    eligible=(allrows.period_start.dt.month.eq(1)&allrows.period_start.dt.day.eq(1)&
        prior.period_start.dt.year.eq(allrows.year-1)&earlier.period_start.dt.year.eq(prior.period_start.dt.year)&
        prior.period_start.gt(earlier.period_start)&prior.period_start.eq(earlier.period_end+pd.Timedelta(days=1))&
        prior.period_end.lt(allrows.period_start)&(allrows.period_start-prior.period_end).dt.days.between(1,2)&
        earlier.renewal_decision.eq('mid_term_change')&
        allrows.renewal_count.eq(prior.renewal_count+1)&prior.renewal_count.eq(earlier.renewal_count)&
        ~allrows.policy_id.isin(ids))
    for col in FIELDS:
        eligible &= (allrows[col].notna()&prior[col].notna()&earlier[col].notna()&allrows[col].eq(prior[col])&allrows[col].eq(earlier[col]))
    for frame in [allrows,prior,earlier]:
        eligible &= frame.original_capital_CU.gt(0)&frame.original_capital_CU.le(1_000_000)
    controls=allrows.loc[eligible,['row_id','policy_id','source_table','period_start','year','sum_insured','original_capital_CU','written_premium']].copy()
    for label,frame in [('initial',earlier),('midterm',prior)]:
        for col in ['row_id','period_start','period_end','original_capital_CU','written_premium']:
            controls[label+'_'+col]=frame.loc[eligible,col].to_numpy()
    controls['midterm_increase_pct']=100*(controls.midterm_original_capital_CU/controls.initial_original_capital_CU-1)
    controls['renewal_vs_initial_pct']=100*(controls.original_capital_CU/controls.initial_original_capital_CU-1)
    controls['renewal_vs_midterm_pct']=100*(controls.original_capital_CU/controls.midterm_original_capital_CU-1)
    controls['closer_to_initial_than_midterm']=(np.abs(np.log(controls.original_capital_CU/controls.initial_original_capital_CU))<
                                               np.abs(np.log(controls.original_capital_CU/controls.midterm_original_capital_CU)))
    controls['source']='Uncorrected original normal amounts; exact 12 policy IDs excluded; no claims used.'
    save(controls,out,'independent_normal_control_sequences')
    metrics=[]
    for label,part in [('all_eligible_sequences',controls),('midterm_increase_gt_10pct',controls.loc[controls.midterm_increase_pct.gt(10)]),
                       ('midterm_increase_gt_20pct',controls.loc[controls.midterm_increase_pct.gt(20)])]:
        metrics.append({'group':label,'sequences':len(part),'policies':part.policy_id.nunique(),
            'closer_to_initial_count':int(part.closer_to_initial_than_midterm.sum()),
            'closer_to_initial_pct':float(part.closer_to_initial_than_midterm.mean()*100),
            'renewal_vs_initial_p05_pct':float(part.renewal_vs_initial_pct.quantile(.05)),
            'renewal_vs_initial_median_pct':float(part.renewal_vs_initial_pct.median()),
            'renewal_vs_initial_p95_pct':float(part.renewal_vs_initial_pct.quantile(.95)),
            'renewal_vs_midterm_median_pct':float(part.renewal_vs_midterm_pct.median())})
    c.dump(out/'control_comparison.json',metrics)
    claims=pq.read_table(ROOT/cat['claims']['workspace_relative_path']).to_pandas()
    claims=claims.loc[claims.policy_id.isin(ids)].copy();save(claims,out,'all_12_claim_histories')
    inventory=pending.groupby(['review_group','line','source_table']).size().rename('rows').reset_index()
    save(inventory,out,'remaining_587_groups')
    remainder=pending.loc[~pending.row_id.isin(q.row_id)].copy();save(remainder,out,'other_575_inventory')
    summary={'scope':'Review only, 12 deep reviews and inventory of 575 other pending rows in retrospective branch.',
        'retrospective_pending':587,'focus_rows':12,'focus_policies':12,'line':'contents','focus_history_rows':len(history),
        'focus_claims':len(claims),'focus_by_year':pd.to_datetime(assessment.period_start).dt.year.value_counts().sort_index().to_dict(),
        'known_initial_context_rows':int(assessment.initial_same_known_context.sum()),
        'missing_initial_context_rows':int((~assessment.initial_complete).sum()),
        'test2025_references':int(assessment.test2025_reference.sum()),
        'hypothetical_vs_initial_min_pct':float(assessment.hypothetical_vs_initial_pct.min()),
        'hypothetical_vs_initial_max_pct':float(assessment.hypothetical_vs_initial_pct.max()),
        'hypothetical_vs_midterm_min_pct':float(assessment.hypothetical_vs_midterm_pct.min()),
        'hypothetical_vs_midterm_max_pct':float(assessment.hypothetical_vs_midterm_pct.max()),
        'midterm_increase_min_pct':float(assessment.midterm_increase_pct.min()),
        'midterm_increase_max_pct':float(assessment.midterm_increase_pct.max()),
        'later_vs_hypothetical_min_pct':float(assessment.later_vs_hypothetical_pct.min()),
        'later_vs_hypothetical_max_pct':float(assessment.later_vs_hypothetical_pct.max()),
        'control_sequences':len(controls),'control_policies':controls.policy_id.nunique(),
        'other_pending_not_adjudicated':575,'source_or_derived_values_changed':0,'dataset_indexes_changed':False,
        'models_trained':False,'correction_authorized':False,'source_unit_confirmation':False,
        'actual_contract_reset_confirmation':False,'independent_validation':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'protocol.json',{'cohort':'Exact 12 D48 retrospective group rows with nearest-prior numeric conflict, still present in CAP02R 587 pending file.',
        'four_stage_comparison':'Initial prior-year segment, subsequent midterm segment, Jan1 focus row, immediately later observed segment.',
        'risk_fields':FIELDS,'hypothesis':'Factor-1000 unit error may coexist with a renewal level reversal after a genuine or generated midterm increase.',
        'no_annualization':'Capital is a coverage limit, not an annual flow. Do not divide capital by exposure or infer premium proration.',
        'controls':'Other contents policy sequences with consecutive same-year midterm change then Jan1 renewal, known equal specified risk fields, all three original capitals positive <=1m; no exact-12 policy IDs.',
        'control_purpose':'Descriptive empirical comparison; neither a fitted correction probability nor contractual proof. 10% and 20% strata are project sensitivity choices.',
        'no_claim_selection':True,'all_source_values_preserved':True})
    c.dump(out/'proposal.json',{'status':'review_only_not_authorized_to_apply',
        'proposed_scale_scenario':'Freeze the 11 A_two_sided_sequence rows as a possible separate retrospective /1000 operation, preserving normal midterm values and all other fields. No application now.',
        'conditional_case':'C48613718 / C01596694: initial normal reference lacks security_level. Keep pending or require explicit separate assumption/source clarification; do not fill the field to pass a rule.',
        'test2025_case':'C21091984 / C02362784: later support is test 2025. Any repair stays explicitly retrospective and unavailable at 2024 inception.',
        'level_reversal':'Do not force hypothetical capital to equal the last midterm capital. Keep the normal midterm observation unchanged and investigate whether the level reset reflects a contract change or data generation.',
        'causal_alternative':'A causal row repair cannot be justified by the later reference or retrospective claims. If considered later, define prior-only criteria and cutoff-specific evidence independently.',
        'other575':'Inventory preserved; use prior D48 routes to continue detailed review, starting with 109 later-support/prior-context-change cases. No automatic reclassification using CAP02R-created references.',
        'source_questions':['Can the factor-1000 storage issue be confirmed?','Are midterm capital increases intentionally reset at the next calendar-year renewal?','What capital endorsements and effective dates are contractual?','Can missing security_level for the C48613718 initial segment be recovered?'],
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    assert all(c.digest(ROOT/path)==sha for path,sha in protected.items())
    print(json.dumps({'run':str(out),'summary':summary,'controls':metrics},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
