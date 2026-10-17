"""CAP04R: cohorte D53 autorizada, solo escala y sin cascadas."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import uuid
import clean_data as c
import correct_capitals as cap
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT,BASE=c.ROOT,c.BASE
REVIEW=ROOT/'Hackaton/Semana 1/Revision_contexto_capital/runs/context_20261016T215509Z_0cb0ff53'
INDEX=BASE/'current_retrospective_dataset.json'
OP_INDEX=BASE/'current_context_capital_correction.json'
RULE='CAP04R'
REQUEST=('Aplica la división por mil a las 109 filas propuestas en una nueva capa retrospectiva. '
         'Conserva originales y los otros 467 pendientes; señala los 17 respaldos de test 2025 y documenta y valida cada cambio.')

def save(frame,path):
    frame.to_parquet(path.with_suffix('.parquet'),index=False)
    frame.to_csv(path.with_suffix('.csv'),index=False)

def main():
    assert cap.manifest_ok(REVIEW)
    proposal=REVIEW/'tables/proposed_scale_changes_NOT_APPLIED.parquet'
    frozen=pd.read_parquet(proposal);cohort_sha=c.digest(proposal)
    assert len(frozen)==frozen.row_id.nunique()==109 and frozen.source_table.value_counts().to_dict()=={'policies_buildings':75,'policies_contents':34}
    assert frozen.test2025_reference.sum()==17
    pointer=json.loads(INDEX.read_text('utf-8'));parent=ROOT/pointer['workspace_relative_run']
    catalog_path=ROOT/pointer['catalog_workspace_relative'];catalog=json.loads(catalog_path.read_text('utf-8'))
    assert cap.manifest_ok(parent) and all(c.digest(ROOT/e['workspace_relative_path'])==e['sha256'] for e in catalog.values())
    if pointer.get('capital_rule')==RULE:
        assert pointer['cohort_sha256']==cohort_sha and pointer['capital_changes_this_layer']==109
        assert c.digest(BASE/'current_dataset.json')==pointer['base_catalog_index_sha256']
        for name,part in frozen.groupby('source_table'):
            values=pq.read_table(ROOT/catalog[name]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
            assert np.array_equal(values.loc[part.row_id].to_numpy(),part.hypothetical_div1000_CU.to_numpy())
        print(json.dumps({'status':'already_applied_verified_noop','run':str(parent),'new_changes':0,'CAP04R_changes':109}));return
    if pointer.get('capital_rule')!='CAP03R' or catalog!=json.loads((REVIEW/'evidence/dataset_catalog.json').read_text('utf-8')):
        raise ValueError('La capa difiere de D53: no trasladar ni ampliar la cohorte.')
    assert c.digest(INDEX)==c.digest(REVIEW/'evidence/retrospective_index.json')
    pending=pd.read_parquet(parent/'tables/pending_capitals.parquet')
    assert len(pending)==576 and set(frozen.row_id).issubset(set(pending.row_id))
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('capcontext_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['data','ledger','tables','evidence','source_snapshot']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:e['sha256'] for e in catalog.values()})
    for p in [INDEX,BASE/'current_dataset.json',catalog_path,parent/'manifest.json',REVIEW/'manifest.json',proposal,
              BASE/'current_retrospective_capital_correction.json',BASE/'current_numeric_capital_correction.json',
              REVIEW.parent.parent/'current_run.json']:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    c.dump(out/'protected_hashes_before.json',protected)
    copies={'parent_index.json':INDEX,'base_index.json':BASE/'current_dataset.json','parent_catalog.json':catalog_path,
        'parent_manifest.json':parent/'manifest.json','review_manifest.json':REVIEW/'manifest.json',
        'review_verification.json':REVIEW/'verification.json','review_proposal.json':REVIEW/'proposal.json',
        'frozen_109_proposal.parquet':proposal,'frozen_576_pending.parquet':parent/'tables/pending_capitals.parquet',
        'context_assessment.parquet':REVIEW/'tables/context_assessment.parquet',
        'policy_histories.parquet':REVIEW/'tables/all_policy_histories.parquet',
        'claim_histories.parquet':REVIEW/'tables/all_claim_histories.parquet',
        'CAP01_ledger.parquet':parent/'evidence/CAP01_ledger.parquet',
        'prior_retrospective_ledger.parquet':parent/'ledger/cumulative_retrospective_changes.parquet',
        'protocol_before_CAP04R.json':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}
    for name,path in copies.items():shutil.copy2(path,out/'evidence'/name)
    failed=BASE/'runs/capcontext_20261016T220832Z_e36a6047'
    assert cap.manifest_ok(failed)
    shutil.copy2(failed/'failed_attempt.json',out/'evidence/failed_attempt.json')
    c.dump(out/'evidence/failed_attempt_reference.json',{'workspace_relative_run':failed.relative_to(ROOT).as_posix(),
        'manifest_sha256':c.digest(failed/'manifest.json'),'status':'closed_failed_verification_not_activated'})
    for name in ['apply_context_capitals.py','verify_context_capitals.py','finalize_context_capitals.py','clean_data.py','correct_capitals.py']:
        shutil.copy2(BASE/name,out/'source_snapshot'/name)
    c.dump(out/'authorization.json',{'status':'explicit_participant_authorization','rule':RULE,
        'messages':[{'role':'user','content':REQUEST}],'cohort_sha256':cohort_sha,
        'scope':'Exact 109 frozen D53 rows: sum_insured /1000 only, new retrospective layer on CAP03R.',
        'preserve':'Originals, prior runs, all other cells, 467 other pending including C48613718 and B19256617/B00962235.',
        'historical_flags':'False authorization/application flags in the frozen D53 proposal remain review-time evidence; this later request authorizes this operation.',
        'not_approved':'Source-unit confirmation, T/W merge, imputation, date or claim changes, causal backtest use, training, cascading or cohort expansion.'})
    assessment=pd.read_parquet(out/'evidence/context_assessment.parquet');ledgers=[];newcat={k:dict(v) for k,v in catalog.items()}
    for name,part in assessment.groupby('source_table',sort=True):
        entry=catalog[name];before=pq.read_table(ROOT/entry['workspace_relative_path'])
        positions=pd.Series(range(before.num_rows),index=before['row_id'].to_pylist())
        part=part.copy();part['source_position']=positions.loc[part.row_id].to_numpy();part=part.sort_values('source_position').reset_index(drop=True)
        pos=part.source_position.to_numpy(dtype=int);old=part.sum_insured.to_numpy();new=part.hypothetical_div1000_CU.to_numpy()
        assert np.array_equal(before['sum_insured'].to_numpy()[pos],old) and np.array_equal(old/1000,new)
        result,count=cap.apply_frozen(before['sum_insured'].to_numpy(),pos,old,new);assert count==len(part)
        after=before.set_column(before.schema.get_field_index('sum_insured'),before.schema.field('sum_insured'),pa.array(result,type=before.schema.field('sum_insured').type))
        dest=out/'data'/(name+'.parquet');pq.write_table(after,dest,compression='zstd')
        part['old']=old;part['new']=new;part['rule']=RULE;part['divisor']=1000
        part['audit_ref_test2025']=part.test2025_reference;part['retrospective_only']=True
        part['evidence_available_at_period_start']=False;part['operation_authorized']=True
        part['correction_authorized']=True;part['capital_change_applied']=True
        part['source_sha256']=entry['sha256'];part['derived_sha256']=c.digest(dest)
        part['cohort_sha256']=cohort_sha;part['authorization_sha256']=c.digest(out/'authorization.json')
        save(part,out/'ledger'/(name+'_sum_insured'));ledgers.append(part)
        newcat[name]={**entry,'workspace_relative_path':dest.relative_to(ROOT).as_posix(),'sha256':c.digest(dest),
            'context_capital_parent_workspace_relative_path':entry['workspace_relative_path'],'context_capital_parent_sha256':entry['sha256'],
            'context_capital_rule':RULE,'context_capital_changes':len(part),'context_capital_test2025_supported_changes':int(part.audit_ref_test2025.sum()),
            'context_capital_ledger_workspace_relative_path':(out/'ledger'/(name+'_sum_insured.parquet')).relative_to(ROOT).as_posix()}
    ledger=pd.concat(ledgers,ignore_index=True)
    save(ledger,out/'ledger/all_capital_changes');save(ledger.loc[ledger.audit_ref_test2025],out/'ledger/test2025_supported_changes')
    remaining=pending.loc[~pending.row_id.isin(frozen.row_id)].copy();assert len(remaining)==467
    save(remaining,out/'tables/pending_capitals')
    inherited=pd.read_parquet(out/'evidence/prior_retrospective_ledger.parquet')
    current=ledger[['row_id','policy_id','line','source_table','old','new','rule','audit_ref_test2025','later_row_id','later_source_table','later_period_start']].rename(columns={
        'later_row_id':'reference_row_id','later_source_table':'reference_source_table','later_period_start':'reference_period_start'})
    current['reference_period_start']=pd.to_datetime(current.reference_period_start).dt.strftime('%Y-%m-%d')
    cumulative=pd.concat([inherited,current],ignore_index=True)
    save(cumulative,out/'ledger/cumulative_retrospective_changes');save(cumulative.loc[cumulative.audit_ref_test2025],out/'ledger/cumulative_test2025_supported_changes')
    c.dump(out/'dataset_catalog.json',newcat)
    c.dump(out/'rules.json',{'rule':RULE,'version':'1.0','operation':'sum_insured /1000','cohort_sha256':cohort_sha,
        'selection':'Frozen 109-row D53 proposal, no reselection or cascade. Prior context is preserved; later D34 context complete/equal.',
        'audit_marker':'audit_ref_test2025 in ledger only: 17 new (6 buildings, 11 contents).',
        'retrospective_only':True,'pending_preserved':467,'B19256617_B00962235_unchanged_CU':377000000,
        'C48613718_C01596694_unchanged_CU':29300000,'all_other_source_cells_preserved':True,
        'reversal':'Restore old at source_position for each table to recover exact parent Arrow table and schema metadata.',
        'source_unit_confirmation':False,'T_W_semantic_merge':False,'automatic_expansion':False,
        'approved_for_cutoff_specific_backtesting':False,'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    summary={'rule':RULE,'capital_changes':109,'changes_by_table':{'policies_buildings':75,'policies_contents':34},
        'test2025_supported_changes':17,'test2025_by_line':{'buildings':6,'contents':11},
        'CAP01_inherited':2073,'CAP02R_inherited':867,'CAP03R_inherited':11,'cumulative_retrospective_changes':987,
        'cumulative_test2025_supported_changes':129,'total_capital_changes_including_CAP01':3060,
        'pending_before':576,'pending_after':467,'pending_by_table':remaining.source_table.value_counts().to_dict(),
        'base_pending_unchanged':1454,'originals_modified':False,'other_fields_changed':0,'new_columns':0,'rows_removed':0,
        'base_catalog_changed':False,'claims_changed':False,'test_tables_changed':False,'models_trained':False,
        'retrospective_only':True,'independent_validation':False,'approved_for_modeling':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'lineage.json',{'new_rule':RULE,'parent_rule':'CAP03R','parent_run':parent.relative_to(ROOT).as_posix(),
        'review_run':REVIEW.relative_to(ROOT).as_posix(),'summary':summary})
    assert all(c.digest(ROOT/path)==sha for path,sha in protected.items())
    print(json.dumps({'run':str(out),'status':'created_not_published','capital_changes':109,'pending':467},ensure_ascii=False))

if __name__=='__main__':main()
