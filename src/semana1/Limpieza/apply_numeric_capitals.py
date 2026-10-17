"""CAP03R: once reparaciones retrospectivas de escala sobre CAP02R, sin expansión."""
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
REVIEW=ROOT/'Hackaton/Semana 1/Revision_discrepancias_capital/runs/discrepancies_20261016T214010Z_fd80a8ba'
INDEX=BASE/'current_retrospective_dataset.json'
OP_INDEX=BASE/'current_numeric_capital_correction.json'
RULE='CAP03R'
REQUEST=('Aplica la división por mil a las 11 filas propuestas en una nueva capa retrospectiva. '
         'Conserva originales y los otros 576 pendientes, incluido C48613718; señala el respaldo '
         'de test 2025 y documenta y valida cada cambio.')


def save(frame,path):
    frame.to_parquet(path.with_suffix('.parquet'),index=False)
    frame.to_csv(path.with_suffix('.csv'),index=False)


def main():
    assert cap.manifest_ok(REVIEW)
    proposal=REVIEW/'tables/proposed_11_scale_changes_NOT_APPLIED.parquet'
    frozen=pd.read_parquet(proposal);cohort_sha=c.digest(proposal)
    assert len(frozen)==frozen.row_id.nunique()==11 and frozen.source_table.eq('policies_contents').all()
    assert frozen.test2025_reference.sum()==1 and not frozen.policy_id.eq('C48613718').any()
    pointer=json.loads(INDEX.read_text('utf-8'));parent=ROOT/pointer['workspace_relative_run']
    catalog_path=ROOT/pointer['catalog_workspace_relative'];catalog=json.loads(catalog_path.read_text('utf-8'))
    assert cap.manifest_ok(parent)
    if pointer.get('capital_rule')==RULE:
        assert pointer['cohort_sha256']==cohort_sha and pointer['capital_changes_this_layer']==11
        assert c.digest(BASE/'current_dataset.json')==pointer['base_catalog_index_sha256']
        assert all(c.digest(ROOT/e['workspace_relative_path'])==e['sha256'] for e in catalog.values())
        values=pq.read_table(ROOT/catalog['policies_contents']['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
        assert np.array_equal(values.loc[frozen.row_id].to_numpy(),frozen.hypothetical_div1000_CU.to_numpy())
        print(json.dumps({'status':'already_applied_verified_noop','run':str(parent),'new_changes':0,'CAP03R_changes':11}));return
    if pointer.get('capital_rule')!='CAP02R' or catalog!=json.loads((REVIEW/'evidence/dataset_catalog.json').read_text('utf-8')):
        raise ValueError('La capa retrospectiva difiere de la revisión D51; no trasladar ni ampliar automáticamente.')
    assert c.digest(INDEX)==c.digest(REVIEW/'evidence/retrospective_index.json')
    assert all(c.digest(ROOT/e['workspace_relative_path'])==e['sha256'] for e in catalog.values())
    pending=pd.read_parquet(parent/'tables/pending_capitals.parquet')
    assert len(pending)==587 and set(frozen.row_id).issubset(set(pending.row_id))
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('capnumeric_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['data','ledger','tables','evidence','source_snapshot']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:e['sha256'] for e in catalog.values()})
    for p in [INDEX,BASE/'current_dataset.json',catalog_path,parent/'manifest.json',REVIEW/'manifest.json',proposal,
              BASE/'current_retrospective_capital_correction.json']:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    c.dump(out/'protected_hashes_before.json',protected)
    copies={'parent_index.json':INDEX,'base_index.json':BASE/'current_dataset.json','parent_catalog.json':catalog_path,
        'parent_manifest.json':parent/'manifest.json','review_manifest.json':REVIEW/'manifest.json',
        'review_verification.json':REVIEW/'verification.json','review_proposal.json':REVIEW/'proposal.json',
        'frozen_11_proposal.parquet':proposal,'frozen_587_pending.parquet':parent/'tables/pending_capitals.parquet',
        'twelve_assessment.parquet':REVIEW/'tables/twelve_assessment.parquet',
        'twelve_histories.parquet':REVIEW/'tables/all_12_policy_histories.parquet',
        'CAP01_ledger.parquet':parent/'evidence/CAP01_ledger.parquet',
        'CAP02R_ledger.parquet':parent/'ledger/all_capital_changes.parquet',
        'protocol_before_CAP03R.json':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}
    for name,path in copies.items():shutil.copy2(path,out/'evidence'/name)
    for name in ['apply_numeric_capitals.py','verify_numeric_capitals.py','finalize_numeric_capitals.py','clean_data.py','correct_capitals.py']:
        shutil.copy2(BASE/name,out/'source_snapshot'/name)
    c.dump(out/'authorization.json',{'status':'explicit_participant_authorization','rule':RULE,
        'messages':[{'role':'user','content':REQUEST}],'cohort_sha256':cohort_sha,
        'scope':'Exact eleven D51 frozen rows, capital /1000 only, in a new retrospective layer on CAP02R.',
        'preserve':'Originals, prior runs, all other source cells, 576 pending including C48613718, original normal midterm capitals.',
        'historical_flags':'The frozen proposal retains its correct review-time false authorization/application flags. This new request authorizes only this later operation.',
        'not_approved':'Actual contract-level reset correction, missing-field imputation, source-unit confirmation, causal backtest use, training or cohort expansion.'})
    name='policies_contents';entry=catalog[name];before=pq.read_table(ROOT/entry['workspace_relative_path'])
    assessment=pd.read_parquet(out/'evidence/twelve_assessment.parquet')
    selected=assessment.loc[assessment.row_id.isin(frozen.row_id)].copy()
    positions=pd.Series(range(before.num_rows),index=before['row_id'].to_pylist())
    selected['source_position']=positions.loc[selected.row_id].to_numpy()
    selected=selected.sort_values('source_position').reset_index(drop=True)
    idx=selected.source_position.to_numpy(dtype=int);old=selected.reported_capital_CU.to_numpy();new=old/1000
    assert np.array_equal(before['sum_insured'].to_numpy()[idx],old)
    result,count=cap.apply_frozen(before['sum_insured'].to_numpy(),idx,old,new);assert count==11
    after=before.set_column(before.schema.get_field_index('sum_insured'),before.schema.field('sum_insured'),
                            pa.array(result,type=before.schema.field('sum_insured').type))
    dest=out/'data/policies_contents.parquet';pq.write_table(after,dest,compression='zstd')
    ledger=selected.drop(columns=['capital_change_applied']).copy()
    ledger['old']=old;ledger['new']=new;ledger['rule']=RULE;ledger['divisor']=1000
    ledger['audit_ref_test2025']=ledger.test2025_reference
    ledger['retrospective_only']=True;ledger['evidence_available_at_period_start']=False
    ledger['operation_authorized']=True;ledger['capital_change_applied']=True
    ledger['source_sha256']=entry['sha256'];ledger['derived_sha256']=c.digest(dest)
    ledger['cohort_sha256']=cohort_sha;ledger['authorization_sha256']=c.digest(out/'authorization.json')
    save(ledger,out/'ledger/all_capital_changes');save(ledger.loc[ledger.audit_ref_test2025],out/'ledger/test2025_supported_changes')
    remaining=pending.loc[~pending.row_id.isin(frozen.row_id)].copy()
    assert len(remaining)==576 and remaining.policy_id.eq('C48613718').sum()==1
    save(remaining,out/'tables/pending_capitals')
    inherited=pd.read_parquet(out/'evidence/CAP02R_ledger.parquet')
    prior=inherited[['row_id','policy_id','line','source_table','old','new','rule','audit_ref_test2025',
        'original_later_row_id','original_later_source_table','original_later_period_start']].rename(columns={
        'original_later_row_id':'reference_row_id','original_later_source_table':'reference_source_table',
        'original_later_period_start':'reference_period_start'})
    current=ledger[['row_id','policy_id','line','source_table','old','new','rule','audit_ref_test2025',
        'later_row_id','later_source_table','later_period_start']].rename(columns={
        'later_row_id':'reference_row_id','later_source_table':'reference_source_table','later_period_start':'reference_period_start'})
    current['reference_period_start']=pd.to_datetime(current.reference_period_start).dt.strftime('%Y-%m-%d')
    prior['reference_period_start']=pd.to_datetime(prior.reference_period_start).dt.strftime('%Y-%m-%d')
    cumulative=pd.concat([prior,current],ignore_index=True)
    save(cumulative,out/'ledger/cumulative_retrospective_changes')
    save(cumulative.loc[cumulative.audit_ref_test2025],out/'ledger/cumulative_test2025_supported_changes')
    newcat={k:dict(v) for k,v in catalog.items()}
    newcat[name]={**entry,'workspace_relative_path':dest.relative_to(ROOT).as_posix(),'sha256':c.digest(dest),
        'numeric_capital_parent_workspace_relative_path':entry['workspace_relative_path'],'numeric_capital_parent_sha256':entry['sha256'],
        'numeric_capital_rule':RULE,'numeric_capital_changes':11,'numeric_capital_test2025_supported_changes':1,
        'numeric_capital_ledger_workspace_relative_path':(out/'ledger/all_capital_changes.parquet').relative_to(ROOT).as_posix()}
    c.dump(out/'dataset_catalog.json',newcat)
    c.dump(out/'rules.json',{'rule':RULE,'version':'1.0','operation':'sum_insured /1000','cohort_sha256':cohort_sha,
        'selection':'Frozen eleven-row D51 proposal; no recomputation, cascading or level-reset correction.',
        'retrospective_only':True,'audit_marker':'audit_ref_test2025 in ledger only; one new C21091984/C02362784 record.',
        'test2025_reference':'test_contents/C02964108, observed capital 26700 CU, future relative to corrected 2024 period.',
        'pending_preserved':576,'conditional_policy_unchanged':'C48613718/C01596694, capital 29300000 CU; initial security_level null unchanged.',
        'normal_midterm_capitals':'Preserve every normal segment, including all preceding midterm increases; scale correction only.',
        'reversal':'Set old at source_position to recover exact parent Arrow table and schema metadata.',
        'base_catalog_unchanged':True,'source_unit_confirmation':False,'actual_contract_reset_confirmation':False,
        'automatic_expansion':False,'approved_for_cutoff_specific_backtesting':False,
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    c.dump(out/'lineage.json',{'new_rule':RULE,'parent_rule':'CAP02R','parent_run':parent.relative_to(ROOT).as_posix(),
        'review_run':REVIEW.relative_to(ROOT).as_posix(),'CAP01_inherited_changes':2073,'CAP02R_inherited_changes':867,
        'CAP03R_new_changes':11,'total_corrected_capitals':2951,'retrospective_corrections_total':878,
        'test2025_supported_inherited':111,'test2025_supported_new':1,'test2025_supported_total':112,
        'pending_before':587,'pending_after':576,'base_pending_unchanged':1454,'CON01_activated':False,'calendar_dates_pending':True})
    c.dump(out/'summary.json',{'rule':RULE,'capital_changes':11,'source_table':'policies_contents','test2025_supported_changes':1,
        'cumulative_retrospective_changes':878,'cumulative_test2025_supported_changes':112,'total_capital_changes_including_CAP01':2951,
        'pending_unchanged':576,'pending_by_table':remaining.source_table.value_counts().to_dict(),
        'C48613718_preserved':True,'originals_modified':False,'other_fields_changed':0,'new_columns':0,'rows_removed':0,
        'base_catalog_changed':False,'claims_changed':False,'test_tables_changed':False,'models_trained':False,
        'retrospective_only':True,'independent_validation':False,'approved_for_modeling':False})
    assert all(c.digest(ROOT/path)==sha for path,sha in protected.items())
    print(json.dumps({'run':str(out),'status':'created_not_published','capital_changes':11,'pending':576},ensure_ascii=False))


if __name__=='__main__':main()
