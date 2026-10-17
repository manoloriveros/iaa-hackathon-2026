"""CAP02R: aplica la cohorte retrospectiva autorizada sin sustituir el catálogo base."""
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
REVIEW=ROOT/'Hackaton/Semana 1/Revision_capitales_pendientes/runs/pending_20261016T212234Z_3c7bd248'
RULE='CAP02R'
EXPECTED={'policies_buildings':430,'policies_contents':437}
TEST_ANCHORS={'policies_buildings':50,'policies_contents':61}
INDEX=BASE/'current_retrospective_dataset.json'
REQUEST=('Aplica la división por mil a las 867 filas propuestas en una capa derivada retrospectiva. '
         'Conserva originales y los otros 587 capitales pendientes; documenta y valida cada cambio '
         'y señala las 111 con respaldo de test 2025.')


def main():
    active=BASE/'current_dataset.json'
    parent_pointer=json.loads(active.read_text('utf-8'));parent=ROOT/parent_pointer['workspace_relative_run']
    parent_catalog_path=ROOT/parent_pointer['catalog_workspace_relative']
    parent_catalog=json.loads(parent_catalog_path.read_text('utf-8'))
    assert cap.manifest_ok(parent) and cap.manifest_ok(REVIEW)
    frozen_path=REVIEW/'tables/proposed_retrospective_scenario_NOT_APPLIED.parquet'
    frozen=pd.read_parquet(frozen_path);sha=c.digest(frozen_path)
    assert len(frozen)==frozen.row_id.nunique()==867 and frozen.source_table.value_counts().to_dict()==EXPECTED
    assert frozen.later_reference_2025_only_evidence.sum()==111
    if INDEX.exists():
        existing=json.loads(INDEX.read_text('utf-8'));closed=ROOT/existing['workspace_relative_run']
        if existing.get('capital_rule')!=RULE or existing.get('cohort_sha256')!=sha:
            raise ValueError('Existe un catálogo retrospectivo distinto; no sustituirlo automáticamente.')
        assert existing['base_catalog_index_sha256']==c.digest(active) and cap.manifest_ok(closed)
        catalog=json.loads((ROOT/existing['catalog_workspace_relative']).read_text('utf-8'))
        for name,entry in catalog.items():
            assert c.digest(ROOT/entry['workspace_relative_path'])==entry['sha256']
            if name in EXPECTED:
                table=pq.read_table(ROOT/entry['workspace_relative_path'],columns=['row_id','sum_insured'])
                q=frozen.loc[frozen.source_table.eq(name)]
                values=pd.Series(table['sum_insured'].to_numpy(),index=table['row_id'].to_pylist())
                assert np.array_equal(values.loc[q.row_id].to_numpy(),q.what_if_div1000_CU.to_numpy())
        print(json.dumps({'status':'already_applied_verified_noop','run':str(closed),'new_changes':0,'retrospective_changes':867}));return
    reviewed=json.loads((REVIEW/'evidence/dataset_catalog.json').read_text('utf-8'))
    assert parent_catalog==reviewed,'El catálogo revisado cambió; no trasladar la reparación sin revisar.'
    assert c.digest(active)==c.digest(REVIEW/'evidence/active_index.json')
    assert all(c.digest(ROOT/e['workspace_relative_path'])==e['sha256'] for e in parent_catalog.values())
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('capretro_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['data','ledger','tables','evidence','source_snapshot']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:e['sha256'] for e in parent_catalog.values()})
    for p in [active,parent_catalog_path,parent/'manifest.json',REVIEW/'manifest.json',frozen_path,
              BASE/'current_prehistory_audit_application.json',BASE/'current_capital_correction.json']:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    c.dump(out/'protected_hashes_before.json',protected)
    for name,p in {'base_index.json':active,'base_catalog.json':parent_catalog_path,'base_manifest.json':parent/'manifest.json',
        'review_manifest.json':REVIEW/'manifest.json','review_verification.json':REVIEW/'verification.json',
        'review_proposal.json':REVIEW/'proposal.json','frozen_867_proposal.parquet':frozen_path,
        'frozen_1454_pending_assessment.parquet':REVIEW/'tables/pending_assessment.parquet',
        'review_policy_histories.parquet':REVIEW/'tables/all_affected_policy_histories.parquet',
        'CAP01_ledger.parquet':REVIEW/'evidence/CAP01_ledger.parquet',
        'protocol_before_CAP02R.json':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}.items():
        shutil.copy2(p,out/'evidence'/name)
    for name in ['apply_retrospective_capitals.py','verify_retrospective_capitals.py','finalize_retrospective_capitals.py','clean_data.py','correct_capitals.py']:
        shutil.copy2(BASE/name,out/'source_snapshot'/name)
    c.dump(out/'authorization.json',{'status':'explicit_participant_authorization','messages':[{'role':'user','content':REQUEST}],
        'rule':RULE,'cohort_sha256':sha,'scope':'Exactly 867 frozen D48 rows, sum_insured /1000 in a separate retrospective derived layer.',
        'source_proposal_flags':'The frozen D48 file correctly retains correction_authorized=false and capital_change_applied=false at review time. This later authorization approves the operation recorded here.',
        'preserve':'Originals, prior runs, baseline catalog, other 587 pending capitals, all other source fields, test tables and claims.',
        'not_approved':'Automatic cohort expansion, current-date availability of later references, source-unit confirmation, training or global modeling approval.'})
    assessment=pd.read_parquet(out/'evidence/frozen_1454_pending_assessment.parquet')
    assert len(assessment)==1454 and set(frozen.row_id).issubset(set(assessment.row_id))
    pending=assessment.loc[~assessment.row_id.isin(frozen.row_id)].copy()
    pending['status_in_retrospective_layer']='pending_no_capital_change'
    pending.to_parquet(out/'tables/pending_capitals.parquet',index=False)
    pending.to_csv(out/'tables/pending_capitals.csv',index=False)
    catalog={k:dict(v) for k,v in parent_catalog.items()};ledgers=[];counts=[]
    for name in EXPECTED:
        entry=parent_catalog[name];source=ROOT/entry['workspace_relative_path'];before=pq.read_table(source)
        q=assessment.loc[assessment.row_id.isin(frozen.row_id)&assessment.source_table.eq(name)].copy()
        positions=pd.Series(range(before.num_rows),index=before['row_id'].to_pylist())
        q['source_position']=positions.loc[q.row_id].to_numpy()
        q=q.sort_values('source_position').reset_index(drop=True)
        idx=q.source_position.to_numpy(dtype=int);old=q.sum_insured.to_numpy();new=old/1000
        values=before['sum_insured'].to_numpy();assert np.array_equal(values[idx],old)
        corrected,count=cap.apply_frozen(values,idx,old,new);assert count==EXPECTED[name]
        result=before.set_column(before.schema.get_field_index('sum_insured'),before.schema.field('sum_insured'),
                                 pa.array(corrected,type=before.schema.field('sum_insured').type))
        dest=out/'data'/(name+'.parquet');pq.write_table(result,dest,compression='zstd')
        book=q[['source_table','line','row_id','policy_id','customer_id','address_id','period_start','period_end','source_position',
            'original_later_row_id','original_later_source_table','original_later_period_start','original_later_period_end',
            'original_later_sum_insured_CU','original_later_start_gap_days','original_later_changed_fields','original_later_missing_fields',
            'original_later_what_if_div1000_over_reference','nearest_prior_numeric_conflict']].copy()
        book['old']=old;book['new']=new;book['divisor']=1000;book['rule']=RULE
        book['audit_ref_test2025']=q.later_reference_2025_only_evidence.to_numpy(dtype=bool)
        book['retrospective_only']=True;book['evidence_available_at_period_start']=False
        book['operation_authorized']=True;book['source_sha256']=entry['sha256'];book['derived_sha256']=c.digest(dest)
        book['cohort_sha256']=sha;book['authorization_sha256']=c.digest(out/'authorization.json')
        book.to_parquet(out/'ledger'/(name+'_sum_insured.parquet'),index=False)
        ledgers.append(book)
        catalog[name]={**entry,'workspace_relative_path':dest.relative_to(ROOT).as_posix(),'sha256':c.digest(dest),
            'retrospective_parent_workspace_relative_path':entry['workspace_relative_path'],
            'retrospective_parent_sha256':entry['sha256'],'retrospective_capital_rule':RULE,
            'retrospective_capital_changes':count,'retrospective_test2025_supported_changes':int(book.audit_ref_test2025.sum()),
            'temporal_scope':'retrospective_reconstruction_using_later_policy_information',
            'not_approved_for_cutoff_specific_backtesting':True,
            'retrospective_ledger_workspace_relative_path':(out/'ledger'/(name+'_sum_insured.parquet')).relative_to(ROOT).as_posix()}
        counts.append({'table':name,'rows_preserved':before.num_rows,'capital_changes':count,
                       'test2025_supported_changes':int(book.audit_ref_test2025.sum()),
                       'pending_unchanged':int(pending.source_table.eq(name).sum()),'other_columns_changed':0,'new_columns':0})
    ledger=pd.concat(ledgers,ignore_index=True)
    ledger.to_parquet(out/'ledger/all_capital_changes.parquet',index=False);ledger.to_csv(out/'ledger/all_capital_changes.csv',index=False)
    supported=ledger.loc[ledger.audit_ref_test2025]
    supported.to_parquet(out/'ledger/test2025_supported_changes.parquet',index=False)
    supported.to_csv(out/'ledger/test2025_supported_changes.csv',index=False)
    pd.DataFrame(counts).to_csv(out/'tables/change_summary.csv',index=False)
    c.dump(out/'dataset_catalog.json',catalog)
    c.dump(out/'rules.json',{'rule':RULE,'version':'1.0','operation':'sum_insured /1000','selection':'Frozen D48 867-row proposal only; no recomputation or cascading.',
        'cohort_sha256':sha,'expected':EXPECTED,'test2025_anchor_counts':TEST_ANCHORS,'retrospective_only':True,
        'later_references':'All 867 references are later than the corrected period; 111 are test 2025. Evidence is not known at corrected-period inception.',
        'test2025_marker':'audit_ref_test2025 is audit-only metadata in the ledger and a separate 111-row extract; no new column is added to policy data.',
        'default_catalog':'current_dataset.json stays byte-identical; explicit retrospective use via current_retrospective_dataset.json.',
        'other_pending':587,'automatic_expansion':False,'source_unit_confirmation':False,
        'reversal':'Restore old capital at source_position; recover exact parent Arrow table including original schema metadata and row order.',
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    c.dump(out/'lineage.json',{'base_run':parent.relative_to(ROOT).as_posix(),'review_run':REVIEW.relative_to(ROOT).as_posix(),
        'base_catalog_index_sha256':c.digest(active),'base_catalog_unchanged':True,'new_rule':RULE,
        'CAP01_inherited_changes':2073,'CAP02R_new_changes':867,'retrospective_total_capital_changes':2940,
        'pending_in_base':1454,'pending_in_retrospective_layer':587,'claims_rule_inherited':'DUP01',
        'audit_rules_inherited':parent_pointer.get('audit_rules',[]),'CON01_activated':False,'calendar_dates_pending':True})
    c.dump(out/'summary.json',{'run':out.relative_to(ROOT).as_posix(),'capital_changes':867,'test2025_supported_changes':111,
        'by_table':counts,'by_period_start_year':pd.to_datetime(ledger.period_start).dt.year.value_counts().sort_index().to_dict(),
        'pending_unchanged':587,'pending_by_table':pending.source_table.value_counts().to_dict(),
        'retrospective_only':True,'base_catalog_changed':False,'originals_modified':False,'rows_removed':0,'new_columns':0,
        'other_fields_changed':0,'claims_catalog_entry_unchanged':True,'dates_changed':False,'models_trained':False,
        'independent_validation':False,'approved_for_modeling':False})
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    print(json.dumps({'run':str(out),'status':'created_not_published','capital_changes':867,'pending':587},ensure_ascii=False))


if __name__=='__main__':main()
