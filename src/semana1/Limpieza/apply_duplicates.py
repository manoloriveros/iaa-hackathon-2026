"""DUP01 autorizado: excluye solo los 604 IDs congelados y conserva sus gemelos de ocho dígitos."""
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import json
import shutil
import uuid

import clean_data as c
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT,BASE=c.ROOT,c.BASE
REVIEW=ROOT/'Hackaton/Semana 1/Revision_duplicados/runs/duplicates_20261016T194858Z_9bbf501d'
REQUEST='Aplica DUP01 a los 604 pares en una nueva capa derivada, conservando el ID de ocho dígitos. Guarda la bitácora y los alias, documenta y valida el cambio, sin tocar los originales ni los demás siniestros.'


def manifest_ok(path):
    m=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
    return all(c.digest(path/e['path'])==e['sha256'] for e in m['files'])


def same_payload(table,left,right):
    fields=[name for name in table.column_names if name!='claim_id']
    return table.slice(left,1).select(fields).equals(table.slice(right,1).select(fields),check_metadata=True)


def apply_frozen(table,selection):
    """Filtro de IDs cerrado. La segunda aplicación es un no-op; estado parcial o conflicto se rechaza."""
    ids=table['claim_id'].to_pylist()
    if len(ids)!=len(set(ids)) or len(selection)!=604:
        raise ValueError('DUP01 requires unique source IDs and the frozen 604-pair selection.')
    positions={claim:i for i,claim in enumerate(ids)}
    keeps=selection.proposed_keep_claim_id.tolist();excludes=selection.proposed_exclude_claim_id.tolist()
    if len(set(keeps))!=604 or len(set(excludes))!=604 or set(keeps)&set(excludes):
        raise ValueError('Invalid alias cohort.')
    if not selection.proposed_keep_claim_id.str.fullmatch(r'CL[0-9]{8}').all() or not selection.proposed_exclude_claim_id.str.fullmatch(r'CL[0-9]{9}').all():
        raise ValueError('Unexpected reviewed ID pattern.')
    if not set(keeps).issubset(positions):raise ValueError('Missing retained representative.')
    for row in selection.itertuples():
        for field in [name for name in table.column_names if name!='claim_id']:
            actual=table[field][positions[row.proposed_keep_claim_id]].as_py();expected=getattr(row,field)
            if pd.isna(actual) and pd.isna(expected):continue
            if pd.isna(actual) or pd.isna(expected) or actual!=expected:
                raise ValueError('Retained payload differs from the frozen review.')
    present=set(excludes)&set(positions)
    if not present:
        if table.num_rows!=162546:raise ValueError('Not a recognized complete DUP01 result.')
        return table,0
    if present!=set(excludes) or table.num_rows!=163150:
        raise ValueError('Partial/changed DUP01 source: no automatic expansion or partial repair.')
    for keep,exclude in zip(keeps,excludes):
        if not same_payload(table,positions[keep],positions[exclude]):
            raise ValueError('Payload conflict; stop instead of merging different claims.')
    mask=pc.invert(pc.is_in(table['claim_id'],value_set=pa.array(excludes,type=table.schema.field('claim_id').type)))
    return table.filter(mask),604


def assign_claims(claims,catalog):
    frames=[]
    for line in ['motor','buildings','contents']:
        p=pq.read_table(ROOT/catalog['policies_'+line]['workspace_relative_path'],columns=['row_id','policy_id','period_start','period_end']).to_pandas()
        q=claims[claims.line.eq(line)].copy()
        joined=q[['claim_id','policy_id','loss_date']].merge(p,on='policy_id',how='left',validate='many_to_many')
        hits=joined[joined.loss_date.between(joined.period_start,joined.period_end)][['claim_id','row_id']]
        if not hits.claim_id.is_unique:raise ValueError('Ambiguous interval assignment.')
        result=q[['claim_id','policy_id','line','loss_date','status']].merge(hits,on='claim_id',how='left',validate='one_to_one')
        first=p.groupby('policy_id').period_start.min()
        before=result.loss_date.lt(result.policy_id.map(first))
        result['assignment_status']=np.where(result.row_id.notna(),'unique_period',np.where(before,'before_first_observed_period','unresolved_other'))
        if result.assignment_status.eq('unresolved_other').any():raise ValueError('Unexpected unmatched claim.')
        frames.append(result)
    return pd.concat(frames,ignore_index=True)


def money(values):
    return sum((Decimal(str(x)) for x in values),Decimal('0')).quantize(Decimal('.01'))


def stats(frame):
    accepted=frame.status.isin(['open','closed']);q=frame[accepted]
    paid,incurred,recovery=money(q.paid_to_date),money(q.incurred_to_date),money(q.recoveries)
    return {'records':len(frame),'accepted':int(accepted.sum()),'closed':int(frame.status.eq('closed').sum()),
        'open':int(frame.status.eq('open').sum()),'repudiated':int(frame.status.eq('repudiated').sum()),
        'paid_accepted_CU':str(paid),'incurred_accepted_CU':str(incurred),'recoveries_accepted_CU':str(recovery),
        'reserve_accepted_CU':str(incurred-paid),'net_accepted_CU':str(incurred-recovery)}


def reconcile(before,after,removed,before_assignment,after_assignment):
    b=before.merge(before_assignment[['claim_id','assignment_status']],on='claim_id',validate='one_to_one')
    a=after.merge(after_assignment[['claim_id','assignment_status']],on='claim_id',validate='one_to_one')
    e=removed.merge(before_assignment[['claim_id','assignment_status']],on='claim_id',validate='one_to_one')
    records=[]
    for dimension,values in [('all',['all']),('line',['motor','buildings','contents']),
                             ('assignment_status',['unique_period','before_first_observed_period'])]:
        for value in values:
            parts=[x if dimension=='all' else x[x[dimension].eq(value)] for x in [b,a,e]]
            counts=[stats(x) for x in parts]
            entry={'dimension':dimension,'value':value}
            for stage,book in zip(['before','after','excluded'],counts):entry.update({stage+'_'+k:v for k,v in book.items()})
            records.append(entry)
    return records


def main():
    active=BASE/'current_dataset.json';pointer=json.loads(active.read_text(encoding='utf-8'))
    parent=ROOT/pointer['workspace_relative_run']
    catalog=json.loads((ROOT/pointer['catalog_workspace_relative']).read_text(encoding='utf-8'))
    assert manifest_ok(parent) and manifest_ok(REVIEW)
    assert json.loads((parent/'verification.json').read_text(encoding='utf-8'))['passed']
    assert json.loads((REVIEW/'verification.json').read_text(encoding='utf-8'))['passed']
    selection=pq.read_table(REVIEW/'tables/proposed_pair_actions.parquet').to_pandas()
    source=ROOT/catalog['claims']['workspace_relative_path'];assert c.digest(source)==catalog['claims']['sha256']
    raw=pq.read_table(source)
    if catalog['claims'].get('rule')=='DUP01':
        again,changed=apply_frozen(raw,selection);assert changed==0 and again.equals(raw,check_metadata=True)
        print(json.dumps({'status':'already_applied_verified_catalog_unchanged','excluded_now':0,'run':str(parent)}),flush=True);return
    rule=json.loads((REVIEW/'proposed_rule.json').read_text(encoding='utf-8'))
    assert catalog['claims']['sha256']==rule['claims_source']['sha256'], 'Reviewed claims snapshot changed.'
    assert c.digest(source)==rule['claims_source']['sha256']
    ident=datetime.now(timezone.utc).strftime('dupfix_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8]
    out=BASE/'runs'/ident
    for name in ['data','ledger','tables','evidence','source_snapshot']:(out/name).mkdir(parents=True,exist_ok=False)
    for name in ['apply_duplicates.py','verify_duplicate_application.py','clean_data.py']:
        shutil.copy2(BASE/name,out/'source_snapshot'/name)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({entry['workspace_relative_path']:c.digest(ROOT/entry['workspace_relative_path']) for entry in catalog.values()})
    protected[active.relative_to(ROOT).as_posix()]=c.digest(active)
    c.dump(out/'protected_hashes_before.json',protected)
    for entry in catalog.values():assert c.digest(ROOT/entry['workspace_relative_path'])==entry['sha256']
    for name,path in {'parent_index.json':active,'parent_catalog.json':ROOT/pointer['catalog_workspace_relative'],
        'parent_manifest.json':parent/'manifest.json','review_manifest.json':REVIEW/'manifest.json',
        'review_verification.json':REVIEW/'verification.json','review_rule.json':REVIEW/'proposed_rule.json',
        'approved_pair_actions.parquet':REVIEW/'tables/proposed_pair_actions.parquet',
        'review_pair_members.parquet':REVIEW/'tables/frozen_pair_members.parquet',
        'review_near_controls.parquet':REVIEW/'tables/nonidentical_collision_controls.parquet',
        'parent_claim_assignment.parquet':parent/'tables/claim_period_audit.parquet'}.items():
        shutil.copy2(path,out/'evidence'/name)
    for name in ['MEMORIA_PROYECTO.md','ESTADO_PROYECTO.json','DECISIONES.md']:
        shutil.copy2(ROOT/'Preparación'/name,out/'evidence'/('before_'+name))
    c.dump(out/'authorization.json',{'status':'explicit_participant_authorization','source':'Human user in this conversation, 2026-10-16',
        'messages':[{'role':'user','content':REQUEST}],'operation':'DUP01 frozen 604 pairs; preserve CL+8 digits',
        'scope':'New derived claims only; originals and every other retained record unchanged.',
        'approval_is_not':'Organizer confirmation of source events, independent validation or global modeling approval.'})
    corrected,changed=apply_frozen(raw,selection);assert changed==604
    dest=out/'data/claims.parquet';pq.write_table(corrected,dest,compression='zstd')
    ids=raw['claim_id'].to_pylist();position={claim:i for i,claim in enumerate(ids)}
    removed_positions=sorted(position[x] for x in selection.proposed_exclude_claim_id)
    removed=raw.take(pa.array(removed_positions,type=pa.int64()))
    pq.write_table(removed,out/'ledger/excluded_rows.parquet',compression='zstd')
    after_positions={claim:i for i,claim in enumerate(corrected['claim_id'].to_pylist())}
    aliases=selection[['duplicate_group','proposed_exclude_claim_id','proposed_keep_claim_id','payload_sha256']].rename(
        columns={'proposed_exclude_claim_id':'excluded_claim_id','proposed_keep_claim_id':'retained_claim_id'}).copy()
    aliases['excluded_source_row']=aliases.excluded_claim_id.map(position)
    aliases['retained_source_row']=aliases.retained_claim_id.map(position)
    aliases['retained_derived_row']=aliases.retained_claim_id.map(after_positions)
    aliases['rule']='DUP01';aliases['action']='exclude_exact_copy';aliases['authorization_sha256']=c.digest(out/'authorization.json')
    aliases['alias_use']='Resolve an old reference only; do not join aliases as additional claims.'
    aliases.to_parquet(out/'ledger/claim_id_aliases.parquet',index=False);aliases.to_csv(out/'ledger/claim_id_aliases.csv',index=False)
    ledger=removed.to_pandas().merge(aliases,left_on='claim_id',right_on='excluded_claim_id',validate='one_to_one')
    ledger['source_workspace_relative_path']=source.relative_to(ROOT).as_posix();ledger['source_sha256']=c.digest(source)
    ledger['derived_workspace_relative_path']=dest.relative_to(ROOT).as_posix();ledger['operation_applied']=True
    ledger['net_accepted_excluded_CU']=np.where(ledger.status.isin(['open','closed']),ledger.incurred_to_date-ledger.recoveries,0.)
    ledger=ledger.sort_values('excluded_source_row').reset_index(drop=True)
    ledger.to_parquet(out/'ledger/exclusion_ledger.parquet',index=False);ledger.to_csv(out/'ledger/exclusion_ledger.csv',index=False)
    original=raw.to_pandas();after=corrected.to_pandas()
    before_assignment=pq.read_table(out/'evidence/parent_claim_assignment.parquet').to_pandas()
    after_assignment=assign_claims(after,catalog)
    after_assignment.to_parquet(out/'tables/claim_period_assignment.parquet',index=False)
    books=reconcile(original,after,removed.to_pandas(),before_assignment,after_assignment)
    c.dump(out/'reconciliation.json',books);pd.DataFrame(books).to_csv(out/'tables/financial_reconciliation.csv',index=False)
    newcat={name:dict(entry) for name,entry in catalog.items()}
    newcat['claims']={'workspace_relative_path':dest.relative_to(ROOT).as_posix(),'layer':'derived','sha256':c.digest(dest),
        'rule':'DUP01','parent_workspace_relative_path':source.relative_to(ROOT).as_posix(),'parent_sha256':c.digest(source),
        'rows_before':163150,'rows_after':162546,'excluded_records':604,'retained_values_changed':0,
        'aliases_workspace_relative_path':(out/'ledger/claim_id_aliases.parquet').relative_to(ROOT).as_posix(),
        'ledger_workspace_relative_path':(out/'ledger/exclusion_ledger.parquet').relative_to(ROOT).as_posix()}
    c.dump(out/'dataset_catalog.json',newcat)
    c.dump(out/'lineage.json',{'parent_run':parent.relative_to(ROOT).as_posix(),'review_run':REVIEW.relative_to(ROOT).as_posix(),
        'inherited_rules':['ID01','EXP01','CAP01','CAT01','AGE01'],'new_rule':'DUP01',
        'cohort_file':'evidence/approved_pair_actions.parquet','cohort_sha256':c.digest(out/'evidence/approved_pair_actions.parquet'),
        'exclusion_ledger':'ledger/exclusion_ledger.parquet','typed_excluded_rows':'ledger/excluded_rows.parquet',
        'aliases':'ledger/claim_id_aliases.parquet','restore':'Insert typed excluded rows at excluded_source_row, preserving all retained source positions.',
        'other_catalog_entries_unchanged':True,'active_index_publish_only_after_verification':True})
    c.dump(out/'rules.json',{'rule':'DUP01','version':'1.0','mode':'participant_authorized_frozen_cohort',
        'excluded_records':604,'selection_discovery_rerun':False,'keep':'CL+8 digits after all reviewed gates',
        'no_changes_to_other_claim_values':True,'capital_scope':'2073 CAP01 inherited; 1454 pending unchanged',
        'CON01_activated':False,'source_confirmation':False,'independent_validation':False,
        'professional_references':['IAA Documentation §2 and §§4–6','Governance §2.8','Professional considerations §§3.5–3.6']})
    c.dump(out/'summary.json',{'rows_before':163150,'rows_after':162546,'excluded_records':604,'retained_values_changed':0,
        'excluded_by_line':ledger.line.value_counts().to_dict(),'excluded_by_status':ledger.status.value_counts().to_dict(),
        'affected_policies':int(selection.groupby(['line','policy_id']).ngroups),
        'accepted_net_excluded_all_CU':books[0]['excluded_net_accepted_CU'],
        'accepted_net_excluded_assigned_CU':next(x['excluded_net_accepted_CU'] for x in books if x['value']=='unique_period'),
        'accepted_net_excluded_prehistory_CU':next(x['excluded_net_accepted_CU'] for x in books if x['value']=='before_first_observed_period'),
        'prehistory_claims_before':414,'prehistory_claims_after':int(after_assignment.assignment_status.eq('before_first_observed_period').sum()),
        'other_claims_preserved':161942,'standard_representatives_preserved':604,'capital_changes_inherited':2073,
        'pending_capitals_unchanged':1454,'models_trained':False,'T0_operationally_materialized':False,
        'operation_authorized':True,'independent_validation':False,'originals_modified':False})
    protected_after={path:c.digest(ROOT/path) for path in protected};assert protected_after==protected
    c.dump(out/'protected_hashes_after.json',protected_after)
    c.dump(BASE/'current_duplicate_application.json',{'workspace_relative_run':out.relative_to(ROOT).as_posix(),'status':'pending_verification'})
    print(json.dumps({'run':str(out),'excluded':604,'rows_after':162546,'active_index_not_yet_changed':True}),flush=True)


if __name__=='__main__':main()
