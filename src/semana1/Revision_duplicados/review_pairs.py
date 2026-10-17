"""Revisa DUP01 como propuesta; no escribe una tabla de siniestros depurada ni cambia índices de datos."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from collections import defaultdict
import hashlib
import json
import shutil
import sys
import uuid

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REQUEST='Empecemos por los 604 pares de siniestros potencialmente duplicados. Revisa sus historiales, muéstrame casos concretos y propón una regla de depuración, sin modificar los datos todavía.'
REVIEW=ROOT/'Hackaton/Semana 1/Validacion_datos/runs/gaps_20261016T193906Z_70462cf9'
STANDARD=r'CL[0-9]{8}'
LONG=r'CL[0-9]{9}'


def amount(values):
    return str(sum((Decimal(str(v)) for v in values),Decimal('0')).quantize(Decimal('.01')))


def normalize(value):
    if pd.isna(value):return None
    if hasattr(value,'isoformat'):return value.isoformat()
    if isinstance(value,np.generic):return value.item()
    return value


def signature(row,fields):
    return json.dumps([normalize(row[col]) for col in fields],ensure_ascii=False,separators=(',',':'),allow_nan=False)


def main():
    active=ROOT/'Hackaton/Semana 1/Limpieza/current_dataset.json'
    pointer=json.loads(active.read_text(encoding='utf-8'))
    catalog=json.loads((ROOT/pointer['catalog_workspace_relative']).read_text(encoding='utf-8'))
    parent=ROOT/pointer['workspace_relative_run']
    for directory in [parent,REVIEW]:
        m=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
        assert all(c.digest(directory/e['path'])==e['sha256'] for e in m['files'])
    ident=datetime.now(timezone.utc).strftime('duplicates_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8]
    out=BASE/'runs'/ident
    for name in ['tables','evidence','source_snapshot','figures']:(out/name).mkdir(parents=True,exist_ok=False)
    for name in ['review_pairs.py','render_pairs.py','verify_pairs.py']:shutil.copy2(BASE/name,out/'source_snapshot'/name)
    shutil.copy2(Path(c.__file__),out/'source_snapshot/clean_data.py')
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:c.digest(ROOT/e['workspace_relative_path']) for e in catalog.values()})
    protected[active.relative_to(ROOT).as_posix()]=c.digest(active)
    c.dump(out/'protected_hashes_before.json',protected)
    for name,source in {'active_index.json':active,'dataset_catalog.json':ROOT/pointer['catalog_workspace_relative'],
        'D40_manifest.json':REVIEW/'manifest.json','D38_manifest.json':parent/'manifest.json',
        'D40_frozen_pairs.parquet':REVIEW/'tables/claim_duplicate_candidates.parquet',
        'D40_summary.json':REVIEW/'summary.json',
        'official_data_description.md':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md',
        'IAA_priorities.md':ROOT/'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md'}.items():
        shutil.copy2(source,out/'evidence'/name)
    for name in ['MEMORIA_PROYECTO.md','ESTADO_PROYECTO.json','DECISIONES.md']:
        shutil.copy2(ROOT/'Preparación'/name,out/'evidence'/('before_'+name))
    claims=pq.read_table(ROOT/catalog['claims']['workspace_relative_path']).to_pandas()
    original_fields=claims.columns.tolist();payload=[col for col in original_fields if col!='claim_id']
    claims['source_row']=np.arange(len(claims))
    frozen=pq.read_table(out/'evidence/D40_frozen_pairs.parquet').to_pandas()
    group_map=frozen.set_index('claim_id').duplicate_group
    claims['duplicate_group']=claims.claim_id.map(group_map)
    # Full-payload equality is calculated independently of the frozen ID selection.
    exact=claims.duplicated(payload,keep=False)
    assert set(claims.loc[exact,'claim_id'])==set(frozen.claim_id) and exact.sum()==1208
    assignment=pq.read_table(parent/'tables/claim_period_audit.parquet',columns=['claim_id','row_id','assignment_status']).to_pandas()
    claims=claims.merge(assignment,on='claim_id',how='left',validate='one_to_one')
    claims['loss_year']=pd.to_datetime(claims.loss_date).dt.year
    claims['report_year']=pd.to_datetime(claims.report_date).dt.year
    claims['accepted']=claims.status.isin(['open','closed'])
    claims['observed_net_CU']=np.where(claims.accepted,claims.incurred_to_date-claims.recoveries,0.)
    claims['case_reserve_CU']=np.where(claims.accepted,claims.incurred_to_date-claims.paid_to_date,0.)
    pairs=claims[claims.duplicate_group.notna()].copy()
    records=[]
    for group,g in pairs.groupby('duplicate_group',sort=True):
        assert len(g)==2
        first,second=g.iloc[0],g.iloc[1]
        equal=[col for col in payload if (pd.isna(first[col]) and pd.isna(second[col])) or first[col]==second[col]]
        assert len(equal)==len(payload)
        standard=g[g.claim_id.str.fullmatch(STANDARD)];long=g[g.claim_id.str.fullmatch(LONG)]
        assert len(standard)==len(long)==1
        keep,exclude=standard.iloc[0],long.iloc[0]
        assert keep.assignment_status==exclude.assignment_status
        assert (pd.isna(keep.row_id) and pd.isna(exclude.row_id)) or keep.row_id==exclude.row_id
        text=signature(keep,payload)
        records.append({'duplicate_group':group,'payload_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'proposed_keep_claim_id':keep.claim_id,'proposed_exclude_claim_id':exclude.claim_id,
            'keep_source_row':int(keep.source_row),'exclude_source_row':int(exclude.source_row),
            'policy_id':keep.policy_id,'line':keep.line,'peril':keep.peril,'loss_date':keep.loss_date,
            'report_date':keep.report_date,'loss_year':int(keep.loss_year),'report_year':int(keep.report_year),'status':keep.status,
            'paid_to_date':keep.paid_to_date,'incurred_to_date':keep.incurred_to_date,'recoveries':keep.recoveries,
            'observed_net_CU':keep.observed_net_CU,'case_reserve_CU':keep.case_reserve_CU,
            'repairer_id':keep.repairer_id,'third_party_id':keep.third_party_id,'row_id':keep.row_id,
            'assignment_status':keep.assignment_status,'equal_fields':len(equal),'group_size':2,
            'all_source_payload_fields_equal':True,'proposed_operation':'exclude_exact_copy_in_future_derived_claims_only',
            'operation_applied':False,'retention_basis':'Dominant CL+8-digit source format, only after full equality; no chronology inferred.'})
    proposal=pd.DataFrame(records)
    proposal.to_parquet(out/'tables/proposed_pair_actions.parquet',index=False)
    proposal.to_csv(out/'tables/proposed_pair_actions.csv',index=False)
    pairs['proposed_role']=np.where(pairs.claim_id.str.fullmatch(STANDARD),'keep_if_approved','exclude_if_approved')
    pairs.to_parquet(out/'tables/frozen_pair_members.parquet',index=False)
    pairs.to_csv(out/'tables/frozen_pair_members.csv',index=False)
    # Controls deliberately preserve different claims sharing coarser event keys.
    canonical=claims[claims.claim_id.str.fullmatch(STANDARD)].copy()
    collision_summaries=[];collisions=[]
    for kind,keys in [('same_loss_and_report',['policy_id','line','peril','loss_date','report_date']),
                       ('same_peril_loss',['policy_id','line','peril','loss_date']),
                       ('same_policy_loss',['policy_id','line','loss_date'])]:
        mask=canonical.duplicated(keys,False)
        collision_summaries.append({'scope':'Diagnostic view selecting only the standard-format member of each exact pair',
            'key':kind,'groups':int(canonical.loc[mask].groupby(keys,dropna=False).ngroups),'member_rows':int(mask.sum())})
        g=canonical.loc[mask].copy();g['collision_kind']=kind;collisions.append(g)
    near=pd.concat(collisions,ignore_index=True)
    near.to_parquet(out/'tables/nonidentical_collision_controls.parquet',index=False)
    near.to_csv(out/'tables/nonidentical_collision_controls.csv',index=False)
    pd.DataFrame(collision_summaries).to_csv(out/'tables/collision_key_sensitivity.csv',index=False)
    # Every affected policy history is reviewed; training periods only, no test-X discovery.
    affected_keys=set(zip(proposal.line,proposal.policy_id))
    controls_keys={('motor','M83268515'),('motor','M63592395')}
    history_keys=affected_keys|controls_keys
    policy_frames=[]
    for line in ['motor','buildings','contents']:
        name='policies_'+line
        fields=['row_id','policy_id','customer_id','address_id','period_start','period_end','exposure',
            'voluntary_excess','compulsory_excess','new_business','renewal_count','renewal_decision']
        fields+=['cover_type','make_model','driver_age'] if line=='motor' else ['sum_insured','accidental_damage_cover']
        f=pq.read_table(ROOT/catalog[name]['workspace_relative_path'],columns=fields).to_pandas()
        f=f[f.policy_id.isin([policy for ramo,policy in history_keys if ramo==line])].copy()
        policy_frames.append(f.assign(line=line,source_table=name))
    policy_history=pd.concat(policy_frames,ignore_index=True).sort_values(['line','policy_id','period_start','period_end'])
    claim_history=claims[[key in history_keys for key in zip(claims.line,claims.policy_id)]].copy()
    policy_history.to_parquet(out/'tables/affected_policy_histories.parquet',index=False)
    claim_history.to_parquet(out/'tables/affected_claim_histories.parquet',index=False)
    policy_summary=[]
    for (line,policy),g in proposal.groupby(['line','policy_id']):
        h=claims[claims.line.eq(line)&claims.policy_id.eq(policy)]
        p=policy_history[policy_history.line.eq(line)&policy_history.policy_id.eq(policy)]
        policy_summary.append({'line':line,'policy_id':policy,'duplicate_groups':len(g),'provided_claim_records':len(h),
            'other_claim_records_preserved':int(h.duplicate_group.isna().sum()),'training_periods':len(p),
            'first_observed_period':p.period_start.min(),'last_observed_period':p.period_end.max(),
            'proposed_accepted_net_reduction_CU':amount(g.observed_net_CU),
            'status':'All periods and claims retained in review; no source row removed.'})
    pd.DataFrame(policy_summary).to_csv(out/'tables/all_affected_policy_summary.csv',index=False)
    grouped=[]
    for dims in [['line'],['loss_year'],['status'],['assignment_status'],['line','loss_year']]:
        label='_'.join(dims)
        for key,g in proposal.groupby(dims,dropna=False):
            key=key if isinstance(key,tuple) else (key,)
            rec={'dimension':label,**{dim:normalize(value) for dim,value in zip(dims,key)},'groups':len(g),
                 'hypothetical_net_reduction_CU':amount(g.observed_net_CU),
                 'hypothetical_paid_reduction_CU':amount(np.where(g.status.isin(['open','closed']),g.paid_to_date,0.)),
                 'hypothetical_reserve_reduction_CU':amount(g.case_reserve_CU),
                 'hypothetical_recovery_reduction_CU':amount(np.where(g.status.isin(['open','closed']),g.recoveries,0.))}
            grouped.append(rec)
    c.dump(out/'tables/materiality.json',grouped)
    pd.DataFrame(grouped).to_csv(out/'tables/materiality.csv',index=False)
    # Deterministic examples include each ramo, material cases, boundary and counterexamples.
    selected=[]
    def choose(case,subset,reason,sort=None):
        if sort:subset=subset.sort_values(sort,ascending=False)
        row=subset.iloc[0];selected.append({'case_id':case,'duplicate_group':row.duplicate_group,
            'line':row.line,'policy_id':row.policy_id,'reason':reason})
    choose('theft_motor',proposal[proposal.policy_id.eq('M27706820')],'Robo cerrado de autos: pareja exacta y demás siniestros de la póliza.')
    choose('largest_pair',proposal[proposal.status.ne('repudiated')],'Mayor efecto monetario individual del conjunto.', 'observed_net_CU')
    choose('building_fire',proposal[proposal.line.eq('buildings')&proposal.peril.eq('fire')],'Incendio de edificios de mayor importe.', 'observed_net_CU')
    choose('contents',proposal[proposal.line.eq('contents')&proposal.status.eq('closed')],'Contenidos: mayor efecto neto entre cerrados.', 'observed_net_CU')
    choose('open_reserve',proposal[proposal.status.eq('open')&proposal.case_reserve_CU.gt(0)],'Abierto: copiar pago y reserva duplicaría ambos componentes.', 'case_reserve_CU')
    choose('recoveries',proposal[proposal.recoveries.gt(0)],'Recuperaciones: el efecto neto es incurrido menos recuperación, no el pago bruto.', 'recoveries')
    choose('before_history',proposal[proposal.row_id.isna()],'Ocurrencia anterior al primer periodo observado: sin efecto en T0 de los periodos actuales.')
    choose('repudiated',proposal[proposal.status.eq('repudiated')],'Rechazado: altera número de expedientes brutos, no coste aceptado.')
    choose('two_pairs_one_policy',proposal[proposal.policy_id.eq('M77733416')],'Dos parejas de eventos distintos en una misma póliza: conservar un registro de cada evento.')
    selected.extend([{'case_id':'same_dates_different_claims','duplicate_group':None,'line':'motor','policy_id':'M83268515',
        'reason':'Control: igual póliza, peligro, ocurrencia y reporte; distinto estado, importes y reparador. Conservar ambos.'},
        {'case_id':'different_third_parties','duplicate_group':None,'line':'motor','policy_id':'M63592395',
        'reason':'Control: mismo peligro y ocurrencia, pero terceros, reportes e importes distintos. No colapsar por evento supuesto.'}])
    c.dump(out/'case_selection.json',selected)
    # Enrich each event with its actual period, without requiring existence for prehistory.
    context=policy_history[['row_id','customer_id','address_id','period_start','period_end','exposure','cover_type',
        'sum_insured','accidental_damage_cover','voluntary_excess','compulsory_excess']]
    pair_context=pairs.merge(context,on='row_id',how='left',validate='many_to_one')
    pair_context.to_parquet(out/'tables/pair_period_context.parquet',index=False)
    profile={
        'source_rows':len(claims),'pairs':len(proposal),'pair_members':len(pairs),'affected_policies':len(affected_keys),
        'by_line':proposal.line.value_counts().to_dict(),'by_status':proposal.status.value_counts().to_dict(),
        'loss_years':{str(k):int(v) for k,v in proposal.loss_year.value_counts().sort_index().items()},
        'report_years':{str(k):int(v) for k,v in proposal.report_year.value_counts().sort_index().items()},
        'assigned_groups':int(proposal.row_id.notna().sum()),'prehistory_groups':int(proposal.row_id.isna().sum()),
        'affected_assigned_periods':int(proposal.row_id.nunique()),
        'accepted_assigned_groups':int((proposal.status.isin(['open','closed'])&proposal.row_id.notna()).sum()),
        'accepted_assigned_periods':int(proposal.loc[proposal.status.isin(['open','closed'])&proposal.row_id.notna(),'row_id'].nunique()),
        'pairs_with_repairer':int(proposal.repairer_id.notna().sum()),'pairs_with_third_party':int(proposal.third_party_id.notna().sum()),
        'pairs_with_recoveries':int(proposal.recoveries.gt(0).sum()),'full_equality_fields':payload,
        'source_id_length_distribution':{str(k):int(v) for k,v in claims.claim_id.str.len().value_counts().sort_index().items()},
        'all_long_ids_exactly_the_proposed_exclusions':set(claims.loc[claims.claim_id.str.fullmatch(LONG),'claim_id'])==set(proposal.proposed_exclude_claim_id),
        'standard_is_first_in_file':int(proposal.keep_source_row.lt(proposal.exclude_source_row).sum()),
        'long_is_first_in_file':int(proposal.keep_source_row.gt(proposal.exclude_source_row).sum()),
        'hypothetical_accepted_net_reduction_all_CU':amount(proposal.observed_net_CU),
        'hypothetical_accepted_net_reduction_assigned_CU':amount(proposal.loc[proposal.row_id.notna(),'observed_net_CU']),
        'hypothetical_accepted_net_reduction_prehistory_CU':amount(proposal.loc[proposal.row_id.isna(),'observed_net_CU']),
        'hypothetical_claim_rows_after':len(claims)-len(proposal),'nonidentical_control_collision_groups':collision_summaries,
        'histories_scope':'All training periods 2021-2024 and all provided claims for all 601 affected policies, plus two control policies; no test X used.',
        'policy_history_rows':len(policy_history),'claim_history_rows':len(claim_history),
        'other_claim_records_on_affected_policies':int(sum(r['other_claim_records_preserved'] for r in policy_summary)),
        'operation_applied':False,'originals_modified':False,'active_dataset_modified':False,'models_trained':False,
        'source_errors_confirmed_by_organizer':False,'independent_validation':False}
    c.dump(out/'summary.json',profile)
    c.dump(out/'proposed_rule.json',{'id':'DUP01','status':'proposed_only_not_authorized_for_application',
        'scope':'Exactly the frozen D40 604 pairs, identified by full content and source hashes. No automatic expansion.',
        'claims_source':catalog['claims'],'D40_cohort_sha256':c.digest(out/'evidence/D40_frozen_pairs.parquet'),
        'group_fields':payload,'numeric_comparison':'Exact source values, tolerance zero, no rounding or monetary normalization.',
        'missing_comparison':'Both absent compares equal for payload grouping; absence is not evidence that the underlying third party/repairer did not exist.',
        'gates':['Exactly two members','Full equality of every non-ID source field','Unique distinct claim_id values',
                 'Same covered row or same explicit prehistory status','Exactly one CL+8 digits and one CL+9 digits in this cohort',
                 'Current source/schema/cohort hashes match the reviewed version'],
        'proposed_survivor':'CL+8-digit identifier after all gates; dominant format is a deterministic alias choice, not proof of earlier registration.',
        'proposed_exclusion':'CL+9-digit exact twin only; never delete or truncate an ID merely for length.',
        'future_storage':'New derived claims layer, keep original claims, frozen exclusion ledger and long→retained alias map; never overwrite a source claim or policy.',
        'not_allowed':['Merge by policy/date/peril only','Approximate amount matching','Replace open with closed','Pick latest report date as a snapshot',
                       'Keep one claim per policy','Filter all nine-digit IDs without full twin match','Use score or target impact to choose cohorts'],
        'exceptions':'Different dates, status, amount, recovery, repairer/third-party ID, present-vs-missing value, ambiguous assignment, groups other than two, new schema or ID pattern go to review and remain untouched.',
        'temporal_limit':'Rule reviewed on the provided 2024-12-31 valuation snapshot. Historical creation/version timestamps are absent; do not claim duplicate knowledge at an earlier cutoff.',
        'source_uncertainty':'Strong empirical evidence of duplicate records; no event/invoice IDs or external confirmation to prove every pair is one real event.',
        'human_instruction':REQUEST,'models_trained':False,'correction_applied':False})
    c.dump(out/'task_origin.json',{'messages':[{'role':'user','content':REQUEST}],
        'ai_contribution':'Codex traced every frozen pair through claim and policy histories, designed exact-match exclusions and counterexamples, and computed a hypothetical ledger. No external service call.',
        'human_review':'Participant requested review and proposal, explicitly prohibited modifying data at this stage.',
        'IAA_references':['Documentation §2 and §§4-6','Governance §2.8','Professional considerations §3.2 and §§3.5-3.6']})
    after={p:c.digest(ROOT/p) for p in protected};assert after==protected
    c.dump(out/'protected_hashes_after.json',after)
    c.dump(BASE/'current_run.json',{'workspace_relative_run':out.relative_to(ROOT).as_posix(),'status':'pending_verification_proposal_only'})
    print(json.dumps({'run':str(out),'pairs':len(proposal),'affected_policies':len(affected_keys),'operation_applied':False},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
