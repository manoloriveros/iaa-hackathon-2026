"""Auditoría de pendientes y sondeos dirigidos. Lee datos; no corrige ni materializa etiquetas."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from collections import Counter
import sys
import json
import shutil
import uuid

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).parent
sys.path.insert(0,str(ROOT / 'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from review_plan import plan

REQUEST = 'Qué validación de data nos falta, sé muy exhaustivo'


def money(values):
    return str(sum((Decimal(str(x)) for x in values),Decimal('0')).quantize(Decimal('0.01')))


def main():
    active = ROOT / 'Hackaton/Semana 1/Limpieza/current_dataset.json'
    pointer = json.loads(active.read_text(encoding='utf-8'))
    catalog = json.loads((ROOT / pointer['catalog_workspace_relative']).read_text(encoding='utf-8'))
    parent = ROOT / pointer['workspace_relative_run']
    oldmanifest = json.loads((parent/'manifest.json').read_text(encoding='utf-8'))
    assert all(c.digest(parent/e['path']) == e['sha256'] for e in oldmanifest['files'])
    assert json.loads((parent/'verification.json').read_text(encoding='utf-8'))['passed']
    ident = datetime.now(timezone.utc).strftime('gaps_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
    out = BASE / 'runs' / ident
    for folder in ['tables','evidence','source_snapshot']:
        (out/folder).mkdir(parents=True,exist_ok=False)
    for name in ['audit_gaps.py','review_plan.py','render_gaps.py']:
        shutil.copy2(BASE/name,out/'source_snapshot'/name)
    shutil.copy2(Path(c.__file__),out/'source_snapshot/clean_data.py')
    protected = {p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:c.digest(ROOT/e['workspace_relative_path']) for e in catalog.values()})
    protected[active.relative_to(ROOT).as_posix()] = c.digest(active)
    for e in catalog.values():assert c.digest(ROOT/e['workspace_relative_path']) == e['sha256']
    c.dump(out/'protected_hashes_before.json',protected)
    shutil.copy2(active,out/'evidence/active_dataset.json')
    shutil.copy2(ROOT/pointer['catalog_workspace_relative'],out/'evidence/dataset_catalog.json')
    eda = ROOT/'Hackaton/Semana 1/Analisis/runs/eda_20261016T165629Z_ab2a8365'
    sources = {
        'quality_summary':parent/'quality_summary.json', 'quality_checks':parent/'tables/quality_checks.csv',
        'active_profiles':parent/'tables/column_profiles.csv','active_missingness':parent/'tables/missingness.csv',
        'claim_assignment':parent/'tables/claim_period_audit.parquet',
        'old_shift':eda/'tables/train_test_shift.csv','interpreted_dictionary':eda/'tables/dictionary_interpreted.csv',
        'official_dictionary':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md',
        'methodology':ROOT/'Hackaton/Semana 1/Modelado/METODOLOGIA_ACTUARIAL.md',
        'protocol':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        'target_diagnostic':ROOT/'Hackaton/Semana 1/Modelado/diagnosticos/objetivo_20261016T181306Z/evidencia.json',
        'construction_index':ROOT/'Hackaton/Semana 1/Revision_construccion/current_run.json',
        'IAA_priorities':ROOT/'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md'}
    for key,path in sources.items():shutil.copy2(path,out/'evidence'/(key+path.suffix))
    c.dump(out/'evidence_index.json',{k:{'workspace_relative_path':p.relative_to(ROOT).as_posix(),'sha256':c.digest(p)} for k,p in sources.items()})
    frames = {}; global_ids = []; gaps = []; calendars = []; relationship = []; new_checks = []
    def check(name,value):
        new_checks.append({'name':name,'passed':bool(value)})
        if not value:raise AssertionError(name)
    check('all_active_input_hashes_match_catalog',all(c.digest(ROOT/e['workspace_relative_path'])==e['sha256'] for e in catalog.values()))
    for line in ['motor','buildings','contents']:
        parts = []
        common = 'row_id policy_id customer_id address_id period_start period_end exposure voluntary_excess'.split()
        extra = 'driver_age years_licensed fuel_type engine_size_cc make_model cover_type'.split() if line=='motor' else ['sum_insured','accidental_damage_cover']
        for name in ['policies_'+line,'test_'+line]:
            f=pq.read_table(ROOT/catalog[name]['workspace_relative_path'],columns=common+extra).to_pandas()
            parts.append(f.assign(source_table=name))
        f=pd.concat(parts,ignore_index=True)
        f.period_start=pd.to_datetime(f.period_start);f.period_end=pd.to_datetime(f.period_end)
        f['year']=f.period_start.dt.year
        f=f.sort_values(['policy_id','period_start','period_end','row_id']).reset_index(drop=True)
        previous=f.groupby('policy_id')[['row_id','period_start','period_end','address_id']].shift()
        valid=f.policy_id.eq(f.policy_id.shift())
        distance=(f.period_start-previous.period_end).dt.days-1
        mask=valid & distance.gt(0)
        gap=f.loc[mask,['source_table','row_id','policy_id','address_id','period_start','year']].copy()
        gap['previous_row_id']=previous.loc[mask,'row_id'];gap['previous_period_end']=previous.loc[mask,'period_end']
        gap['gap_days']=distance[mask].astype(int);gap['line']=line;gaps.append(gap)
        calendars.append({'line':line,'rows_2024':int(f.year.eq(2024).sum()),
            'ends_2024_12_30':int(f.period_end.eq(pd.Timestamp('2024-12-30')).sum()),
            'ends_2024_12_31':int(f.period_end.eq(pd.Timestamp('2024-12-31')).sum()),
            'covers_2024_12_31':int((f.period_start.le(pd.Timestamp('2024-12-31')) & f.period_end.ge(pd.Timestamp('2024-12-31'))).sum()),
            'gaps_to_2025':int(mask.sum()),'unique_policies_with_gap':int(f.loc[mask,'policy_id'].nunique())})
        relationship.append({'line':line,'rows':len(f),'policies':f.policy_id.nunique(),
            'policies_multiple_policyholders':int(f.groupby('policy_id').customer_id.nunique().gt(1).sum()),
            'voluntary_excess_outside_dictionary':int((~f.voluntary_excess.isin([0,250,500,1000])).sum())})
        global_ids.extend(f.row_id.tolist());frames[line]=f
    gaps=pd.concat(gaps,ignore_index=True)
    gaps.to_parquet(out/'tables/calendar_gaps.parquet',index=False)
    gaps.head(30).to_csv(out/'tables/calendar_gap_examples.csv',index=False)
    pd.DataFrame(calendars).to_csv(out/'tables/calendar_summary.csv',index=False)
    pd.DataFrame(relationship).to_csv(out/'tables/relationship_checks.csv',index=False)
    check('global_policy_period_row_ids_unique',len(global_ids)==len(set(global_ids))==3035950)
    check('gap_cases_all_one_day_at_leap_year_boundary',len(gaps)==500245 and gaps.gap_days.eq(1).all()
          and gaps.previous_period_end.eq(pd.Timestamp('2024-12-30')).all() and gaps.period_start.eq(pd.Timestamp('2025-01-01')).all())
    claims=pq.read_table(ROOT/catalog['claims']['workspace_relative_path']).to_pandas()
    payload=[col for col in claims if col!='claim_id']
    duplicate=claims.duplicated(payload,keep=False);extra=claims.duplicated(payload)
    duplicates=claims.loc[duplicate].copy()
    duplicates['duplicate_group']=duplicates.groupby(payload,dropna=False,sort=False).ngroup().map(lambda i:f'DUP{i+1:04d}')
    duplicates['extra_after_first_in_source']=extra[duplicate]
    # Independent tuple-key calculation handles missing values explicitly.
    counts=Counter(tuple(None if pd.isna(value) else value for value in row) for row in claims[payload].itertuples(index=False,name=None))
    check('duplicate_detection_agrees_with_independent_tuple_counter',sum(n-1 for n in counts.values())==int(extra.sum())==604
          and sum(n for n in counts.values() if n>1)==int(duplicate.sum())==1208)
    check('all_semantic_duplicate_groups_are_pairs',set(counts.values())=={1,2} and duplicates.duplicate_group.nunique()==604)
    check('claim_ids_remain_unique_despite_semantic_duplicates',claims.claim_id.is_unique)
    assignment=pq.read_table(sources['claim_assignment'],columns=['claim_id','row_id','assignment_status']).to_pandas()
    duplicates=duplicates.merge(assignment,on='claim_id',how='left',validate='one_to_one')
    duplicates.to_parquet(out/'tables/claim_duplicate_candidates.parquet',index=False)
    duplicates.to_csv(out/'tables/claim_duplicate_candidates.csv',index=False)
    accepted=duplicates.status.isin(['closed','open'])
    extras=duplicates.extra_after_first_in_source & accepted
    net=duplicates.incurred_to_date-duplicates.recoveries
    duplicate_summary={'groups':604,'all_member_rows':1208,'extra_rows_if_one_per_pair':604,
        'accepted_extra_rows':int(extras.sum()),'repudiated_extra_rows':int((duplicates.extra_after_first_in_source & ~accepted).sum()),
        'hypothetical_net_reduction_all_reported_CU':money(net[extras]),
        'hypothetical_net_reduction_assigned_current_periods_CU':money(net[extras & duplicates.row_id.notna()]),
        'hypothetical_net_reduction_outside_history_CU':money(net[extras & duplicates.row_id.isna()]),
        'interpretation':'Sensitivity if one member of each pair is confirmed duplicate; not an executed deduplication or established overstatement.'}
    check('duplicate_sensitivity_exact_decimal_amount',duplicate_summary['hypothetical_net_reduction_all_reported_CU']=='3174167.49')
    duplicate_agg=duplicates[duplicates.extra_after_first_in_source].copy()
    duplicate_agg['loss_year']=pd.to_datetime(duplicate_agg.loss_date).dt.year
    duplicate_agg['accepted_net']=np.where(duplicate_agg.status.isin(['open','closed']),duplicate_agg.incurred_to_date-duplicate_agg.recoveries,0.)
    duplicate_agg.groupby(['line','loss_year']).agg(extra_rows=('claim_id','size'),accepted_net_CU=('accepted_net','sum')).reset_index().to_csv(out/'tables/duplicate_materiality_by_line_year.csv',index=False)
    current=claims.merge(assignment,on='claim_id',how='left',validate='one_to_one')
    coverage=[]; motor_cross=[]; total_uncovered=[]
    for line in ['motor','buildings','contents']:
        q=current[current.line.eq(line)&current.status.isin(['open','closed'])&current.row_id.notna()].copy()
        cols=['row_id','cover_type'] if line=='motor' else ['row_id','sum_insured','accidental_damage_cover']
        q=q.merge(frames[line][cols],on='row_id',validate='many_to_one')
        if line=='motor':
            q.groupby(['cover_type','peril']).size().reset_index(name='accepted_claims').to_csv(out/'tables/motor_cover_peril.csv',index=False)
            flagged=q.peril.eq('own_damage')&~q.cover_type.eq('comprehensive')
            count=int(flagged.sum());motor_cross=q.loc[flagged].copy()
            motor_cross.to_csv(out/'tables/motor_coverage_candidates.csv',index=False)
            coverage.append({'line':line,'accepted_assigned_claims':len(q),'screen':'own_damage_outside_comprehensive','flagged':count})
        else:
            flagged=q.peril.eq('accidental_damage')&~q.accidental_damage_cover
            q.loc[flagged].to_parquet(out/'tables'/f'{line}_accidental_cover_candidates.parquet',index=False)
            total_uncovered.append(q.loc[flagged].assign(screen='accidental_damage_cover_false'))
            above=(q.incurred_to_date-q.recoveries).gt(q.sum_insured)
            q.loc[above].to_csv(out/'tables'/f'{line}_net_above_capital.csv',index=False)
            coverage.extend([{'line':line,'accepted_assigned_claims':len(q),'screen':'accidental_damage_cover_false','flagged':int(flagged.sum())},
                {'line':line,'accepted_assigned_claims':len(q),'screen':'claim_net_above_period_capital','flagged':int(above.sum())}])
    pd.DataFrame(coverage).to_csv(out/'tables/coverage_screens.csv',index=False)
    check('coverage_screens_reproduce_frozen_counts',[x['flagged'] for x in coverage]==[4,506,8,1090,3])
    # Screens deliberately preserve potentially duplicated records; overlaps are quantified, not added to totals.
    duplicate_ids=set(duplicates.claim_id)
    coverage_overlap={'motor_own_damage_flagged_member_of_duplicate_pair':int(motor_cross.claim_id.isin(duplicate_ids).sum()),
        'home_accidental_flagged_member_of_duplicate_pair':int(pd.concat(total_uncovered).claim_id.isin(duplicate_ids).sum())}
    motor=frames['motor'];electric=motor.fuel_type.eq('electric')
    ev=motor.loc[electric,['source_table','row_id','policy_id','fuel_type','engine_size_cc','make_model']].copy()
    ev.to_parquet(out/'tables/electric_engine_applicability.parquet',index=False)
    engine_summary=[]
    for name,g in ev.groupby('source_table'):
        engine_summary.append({'table':name,'electric_rows':len(g),'engine_cc_positive':int(g.engine_size_cc.gt(0).sum()),
                               'engine_cc_missing':int(g.engine_size_cc.isna().sum()),'engine_cc_zero':int(g.engine_size_cc.eq(0).sum())})
    pd.DataFrame(engine_summary).to_csv(out/'tables/electric_engine_summary.csv',index=False)
    license_mask=(motor.driver_age-motor.years_licensed).lt(16)
    license=motor.loc[license_mask,['source_table','row_id','policy_id','driver_age','years_licensed']].copy()
    license['implied_license_age']=license.driver_age-license.years_licensed
    license.to_parquet(out/'tables/license_age_screen.parquet',index=False)
    license.head(25).to_csv(out/'tables/license_age_examples.csv',index=False)
    check('electric_and_license_counts_reproduce_probe',len(ev)==99376 and int(ev.engine_size_cc.gt(0).sum())==96843 and len(license)==3717)
    weather=pq.read_table(ROOT/catalog['weather']['workspace_relative_path'],columns=['year','hail_days','freezing_days']).to_pandas()
    maxdays=pd.to_datetime(weather.year.astype(str)+'-01-01').dt.is_leap_year.map({True:366,False:365})
    weather_screens={col:int(weather[col].gt(maxdays).sum()) for col in ['hail_days','freezing_days']}
    claims_dec31=int(pd.to_datetime(claims.loss_date).eq(pd.Timestamp('2024-12-31')).sum())
    check('no_observed_loss_on_omitted_day',claims_dec31==0)
    quality=json.loads(sources['quality_summary'].read_text(encoding='utf-8'))
    checks=pd.read_csv(sources['quality_checks'])
    profiles=pd.read_csv(sources['active_profiles'])
    interpreted=pd.read_csv(sources['interpreted_dictionary'])
    controls=plan()
    field_records=[]
    for col,g in profiles.groupby('column',sort=True):
        column_controls=[r['id'] for r in controls if '*' not in r['columns'] and col in r['columns']]
        base=checks[checks.rule.map(lambda rule:rule.endswith('_'+col))]
        occurrences=[]
        for _,record in g.iterrows():
            occurrences.append({'table':record['table'],'rows':int(record['rows']),'missing':int(record['missing']),
                                'dtype':record['dtype'],'distinct':int(record['distinct'])})
        definitions=interpreted[interpreted.column.eq(col)]
        field_records.append({'column':col,'tables':g.table.tolist(),'occurrences':occurrences,
            'meaning':str(definitions.meaning.iloc[0]) if len(definitions) else '',
            'existing_direct_rule_names':sorted(base.rule.unique().tolist()),
            'existing_direct_rule_note':'Suffix matching lists direct field controls; does not imply all relational/temporal controls are covered.',
            'review_control_ids':column_controls or ['VD18','VD41','VD43'],
            'general_contract_ids':['VD01','VD02','VD18','VD29','VD42'],
            'current_technical_profile':'Profiled on active D38; no blanket semantic or modeling approval.'})
    check('field_inventory_covers_105_names_242_occurrences',len(field_records)==105 and sum(len(r['occurrences']) for r in field_records)==242)
    check('review_plan_has_unique_ids_and_every_field_has_review',len(controls)==58 and len({r['id'] for r in controls})==58 and all(r['review_control_ids'] for r in field_records))
    c.dump(out/'review_controls.json',controls);c.dump(out/'field_inventory.json',field_records)
    pd.DataFrame([{**r,'columns':' '.join(r['columns'])} for r in controls]).to_csv(out/'review_controls.csv',index=False)
    pd.DataFrame([{'column':r['column'],'tables':','.join(r['tables']),'meaning':r['meaning'],
        'existing_direct_rules':','.join(r['existing_direct_rule_names']),'review_ids':','.join(r['review_control_ids']),
        'general_contract_ids':','.join(r['general_contract_ids'])} for r in field_records]).to_csv(out/'field_inventory.csv',index=False)
    c.dump(out/'summary.json',{'run_id':ident,'utc':datetime.now(timezone.utc).isoformat(),
        'active_dataset':pointer,'existing_quality_checks':quality['checks'],'existing_strict_checks':int(checks.severity.eq('strict').sum()),
        'existing_strict_failures':len(quality['strict_failures']),'tables':11,'profiled_rows':quality['rows_profiled'],
        'field_names':105,'column_occurrences':242,'review_items':58,
        'review_items_by_status':dict(Counter(r['status'] for r in controls)),
        'review_items_by_priority':dict(Counter(r['priority'] for r in controls)),
        'new_screens':{'semantic_duplicate_claims':duplicate_summary,'calendar':calendars,
            'calendar_gap_rows':len(gaps),'observed_claims_on_2024_12_31':claims_dec31,
            'coverage':coverage,'coverage_overlap':coverage_overlap,'electric_engine':engine_summary,
            'implied_license_age_below_16_rows':len(license),'license_threshold_is_legal_rule':False,
            'weather_day_counts_above_calendar_length':weather_screens},
        'new_alerts_are_not_confirmed_errors':True,'screens_can_overlap_do_not_sum_cases':True,
        'no_corrections_or_deduplication_applied':True,'T0_materialized':False,'models_trained':False,
        'active_dataset_changed':False,'construction_candidate_activated':False,'independent_validation':False,
        'scope':'Evidence coverage review plus directed read-only screens. All 58 pending/control decisions are not automatically executed or closed.'})
    c.dump(out/'task_origin.json',{'messages':[{'role':'user','content':REQUEST}],
        'ai_contribution':'Codex reviewed existing evidence, found coverage gaps, ran targeted deterministic screens, and drafted closure criteria. No other provider was called.',
        'IAA_references':['Documentation §2 and §§4-6','Governance §2.8','Professional considerations §§3.1-3.3 and §§3.5-3.6'],
        'approval_scope':'Review only; no authority inferred to delete claims, change dates, repair additional capitals or activate CON01.'})
    after={path:c.digest(ROOT/path) for path in protected}
    check('all_protected_input_bytes_unchanged',after==protected)
    check('all_source_evidence_unchanged',all(c.digest(path)==json.loads((out/'evidence_index.json').read_text(encoding='utf-8'))[key]['sha256'] for key,path in sources.items()))
    c.dump(out/'protected_hashes_after.json',after)
    c.dump(out/'verification.json',{'passed':True,'checks_count':len(new_checks),'checks':new_checks,
        'verification_type':'Own checks of this review and screen logic; not closure of the 58-item backlog or independent validation.',
        'python':sys.version,'pandas':pd.__version__,'pyarrow':__import__('pyarrow').__version__})
    from render_gaps import render
    render(out)
    c.dump(out/'manifest.json',{'files':[{'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json']})
    c.dump(BASE/'current_run.json',{'workspace_relative_run':out.relative_to(ROOT).as_posix(),
        'report_workspace_relative':(out/'informe.html').relative_to(ROOT).as_posix(),
        'status':'verified_scope_review_not_data_approval','review_items':58,'field_names':105,
        'no_data_changes':True})
    print(json.dumps({'run':str(out),'review_items':58,'field_names':105,'screen_checks':len(new_checks),
                      'duplicates':duplicate_summary,'calendar_gaps':len(gaps),'no_data_changes':True},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
