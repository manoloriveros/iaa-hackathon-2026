"""PRE00 autorizado: añade auditoría a 413 IDs congelados en una nueva capa."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import uuid

import clean_data as c
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT, BASE = c.ROOT, c.BASE
REVIEW = ROOT / 'Hackaton/Semana 1/Revision_prehistoria/runs/prehistory_20261016T210357Z_13161fac'
FLAG = 'audit_pre00'
REQUEST = ('Aplica PRE00 como marca de auditoría a los 413 siniestros en una nueva capa derivada. '
           'Conserva originales, fechas e importes; mantén su coste fuera del objetivo de los periodos actuales '
           'y documenta y valida cada cambio.')


def manifest_ok(path):
    m = json.loads((path / 'manifest.json').read_text('utf-8'))
    return all(c.digest(path / e['path']) == e['sha256'] for e in m['files'])


def append_flag(table, claim_ids, cohort_sha):
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError('La cohorte tiene IDs repetidos.')
    if not set(claim_ids).issubset(set(table['claim_id'].to_pylist())):
        raise ValueError('Faltan IDs de la cohorte congelada; no aplicar parcialmente.')
    wanted = pc.is_in(table['claim_id'], value_set=pa.array(claim_ids, type=table.schema.field('claim_id').type))
    field = pa.field(FLAG, pa.bool_(), nullable=False, metadata={
        b'role': b'audit_only', b'rule': b'PRE00', b'excluded_from_predictors': b'true',
        b'excluded_from_current_period_target': b'true', b'cohort_sha256': cohort_sha.encode('ascii'),
        b'meaning': b'Frozen pre-first-observed-period claim list; not a coverage or repudiation decision.'})
    if FLAG in table.column_names:
        if not table.schema.field(FLAG).equals(field, check_metadata=True) or not table[FLAG].equals(wanted):
            raise ValueError('PRE00 parcial, metadato distinto o marca alterada; no reparar automáticamente.')
        return table, False
    return table.append_column(field, wanted), True


def main():
    active = BASE / 'current_dataset.json'
    pointer = json.loads(active.read_text('utf-8'))
    catalog_path = ROOT / pointer['catalog_workspace_relative']
    catalog = json.loads(catalog_path.read_text('utf-8'))
    parent = ROOT / pointer['workspace_relative_run']
    assert manifest_ok(parent) and manifest_ok(REVIEW)
    cohort_path = REVIEW / 'tables/frozen_prehistory_cohort.parquet'
    frozen = pd.read_parquet(cohort_path)
    assert len(frozen) == frozen.claim_id.nunique() == 413
    cohort_sha = c.digest(cohort_path)
    source = ROOT / catalog['claims']['workspace_relative_path']
    assert c.digest(source) == catalog['claims']['sha256']
    before = pq.read_table(source)
    if 'PRE00' in pointer.get('audit_rules', []):
        again, changed = append_flag(before, frozen.claim_id.tolist(), cohort_sha)
        assert not changed and again.equals(before, check_metadata=True)
        print(json.dumps({'status':'already_applied_verified_noop', 'run':str(parent),
                          'marked_claims':pc.sum(before[FLAG]).as_py(), 'new_columns_added':0})); return
    reviewed = json.loads((REVIEW / 'evidence/dataset_catalog.json').read_text('utf-8'))
    assert catalog == reviewed, 'El catálogo revisado cambió; requiere nueva revisión, no expansión automática.'
    assert before.num_rows == 162546 and before.num_columns == 12
    for entry in catalog.values():
        assert c.digest(ROOT / entry['workspace_relative_path']) == entry['sha256']
    after, added = append_flag(before, frozen.claim_id.tolist(), cohort_sha)
    assert added and after.drop([FLAG]).equals(before, check_metadata=True)
    out = BASE / 'runs' / (datetime.now(timezone.utc).strftime('preaudit_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8])
    for name in ['data','ledger','evidence','tables','source_snapshot']:
        (out/name).mkdir(parents=True, exist_ok=False)
    protected = {p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:e['sha256'] for e in catalog.values()})
    for p in [active,catalog_path,parent/'manifest.json',REVIEW/'manifest.json',cohort_path]:
        protected[p.relative_to(ROOT).as_posix()] = c.digest(p)
    c.dump(out/'protected_hashes_before.json',protected)
    files = {'parent_index.json':active,'parent_catalog.json':catalog_path,'parent_manifest.json':parent/'manifest.json',
        'review_manifest.json':REVIEW/'manifest.json','review_verification.json':REVIEW/'verification.json',
        'review_proposal.json':REVIEW/'proposal.json','review_summary.json':REVIEW/'summary.json',
        'frozen_cohort.parquet':cohort_path,'review_assignment.parquet':REVIEW/'tables/fresh_assignment.parquet',
        'review_financial_reconciliation.json':REVIEW/'financial_reconciliation.json',
        'review_all_affected_claim_histories.parquet':REVIEW/'tables/all_affected_claim_histories.parquet',
        'previous_duplicate_alias_context.parquet':REVIEW/'tables/previous_duplicate_alias_context.parquet',
        'protocol_before_PRE00.json':ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}
    for name,p in files.items():
        shutil.copy2(p,out/'evidence'/name)
    for name in ['apply_prehistory_audit.py','verify_prehistory_audit.py','finalize_prehistory_audit.py','clean_data.py']:
        shutil.copy2(BASE/name,out/'source_snapshot'/name)
    for name,p in {'target_scope.py':ROOT/'Hackaton/Semana 1/Modelado/target_scope.py',
        'diagnostico_objetivo.py':ROOT/'Hackaton/Semana 1/Modelado/diagnostico_objetivo.py',
        'predictor_guard.py':ROOT/'Preparación/src/iaa_lab/predictor_guard.py',
        'core_data.py':ROOT/'Preparación/src/iaa_lab/data.py'}.items():
        shutil.copy2(p,out/'source_snapshot'/name)
    c.dump(out/'authorization.json',{'status':'explicit_participant_authorization',
        'messages':[{'role':'user','content':REQUEST}], 'rule':'PRE00',
        'operation':'Append one audit-only flag to exact frozen 413 claim IDs; retain their costs outside currently provided period targets.',
        'preserve':'All original and retained source cells, amounts, dates, status, IDs, order, DUP01 and REN00 lineage.',
        'not_authorized':'New coverage, date or amount correction, claim/policy removal, training or global modeling approval.'})
    dest = out/'data/claims.parquet'
    pq.write_table(after,dest,compression='zstd')
    src_df = before.to_pandas()
    mark = src_df.loc[after[FLAG].to_numpy()].copy()
    mark['source_position'] = src_df.index[after[FLAG].to_numpy()]
    context = ['claim_id','review_class','first_row_id','first_period_start','first_period_end',
               'days_before_first_observed','assignment_status','classification_is_coverage_confirmation']
    mark = mark.merge(frozen[context],on='claim_id',how='left',sort=False,validate='one_to_one')
    mark['column']=FLAG; mark['old_column_present']=False; mark['new_value']=True; mark['rule']='PRE00'
    mark['cohort_sha256']=cohort_sha; mark['source_sha256']=catalog['claims']['sha256']
    mark['derived_sha256']=c.digest(dest); mark['authorization_sha256']=c.digest(out/'authorization.json')
    mark.to_parquet(out/'ledger/pre00_marked_claims.parquet',index=False)
    mark.to_csv(out/'ledger/pre00_marked_claims.csv',index=False)
    schema = {'table':'claims','rows':162546,'original_columns':12,'derived_columns':13,
        'flag_true':413,'flag_false':162133,'original_cells_changed':0,'rows_removed':0,'rows_added':0,
        'original_types_metadata_order_and_nulls_preserved':True,'default_for_every_other_row':False}
    pd.DataFrame([schema]).to_csv(out/'ledger/schema_additions.csv',index=False)
    newcat = {k:dict(v) for k,v in catalog.items()}
    old = catalog['claims']
    # Keep the DUP01 transformation, alias and exclusion lineage distinct from this audit annotation.
    newcat['claims'] = {**old,'workspace_relative_path':dest.relative_to(ROOT).as_posix(),'sha256':c.digest(dest),
        'audit_parent_workspace_relative_path':old['workspace_relative_path'],'audit_parent_sha256':old['sha256'],
        'audit_rule':'PRE00','audit_columns':[FLAG],'audit_flag_true':413,'audit_only_not_predictor':True,
        'audit_original_values_changed':0,'audit_ledger_workspace_relative_path':(out/'ledger/pre00_marked_claims.parquet').relative_to(ROOT).as_posix()}
    c.dump(out/'dataset_catalog.json',newcat)
    c.dump(out/'rules.json',{'rule':'PRE00','column':FLAG,'type':'nonnullable_boolean','role':'audit_only',
        'scope':'Exact frozen 413 claim IDs reviewed in D46; no automatic cohort expansion.',
        'true_means':'Before first observed period for this policy and line in the reviewed snapshot, without deciding actual historical coverage.',
        'false_means':'Outside this frozen list; not a quality or eligibility certification.',
        'target':'Keep every marked claim outside current-period target cost, with source economics in separate reconciliation.',
        'assignment':'policy_id + line + period_start <= loss_date <= period_end, unique interval only; never report_date or forced first row.',
        'guard':'Modelado.target_scope.assert_prehistory_excluded; reject marked/assigned conflicts before aggregation.',
        'prediction_use':'audit_* blocked by existing predictor guard; prior-report feature use not approved by this operation.',
        'cohort_sha256':cohort_sha,'automatic_expansion':False,'coverage_confirmed':False,
        'classes_in_ledger_only':True,'reversal':'Drop only audit_pre00 to recover every parent Arrow value, type, metadata and row order.',
        'ledger_defaults':'All rows absent from the true-row ledger receive false; schema additions and source hashes define every added cell.'})
    c.dump(out/'lineage.json',{'new_rule':'PRE00','parent_run':parent.relative_to(ROOT).as_posix(),
        'review_run':REVIEW.relative_to(ROOT).as_posix(),'cohort_sha256':cohort_sha,
        'claims_rule_inherited':'DUP01','audit_rules_inherited':pointer.get('audit_rules',[]),
        'other_catalog_entries_unchanged':True,'original_cells_changed':0,'CAP01_inherited':2073,
        'pending_capitals_unchanged':1454,'CON01_activated':False,'calendar_dates_pending':True,
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    c.dump(out/'summary.json',{'run':out.relative_to(ROOT).as_posix(),'rule':'PRE00','claims_preserved':162546,
        'marked_claims':413,'unmarked_claims':162133,'marked_policies':413,'new_columns':1,
        'by_line':mark.line.value_counts().to_dict(),'review_classes':mark.review_class.value_counts().to_dict(),
        'original_cells_changed':0,'dates_changed':False,'amounts_changed':False,'statuses_changed':False,
        'claims_removed':0,'policy_tables_unchanged':True,'operational_T0_materialized':False,
        'models_trained':False,'independent_validation':False})
    print(json.dumps({'run':str(out),'status':'created_not_yet_published','marked_claims':413},ensure_ascii=False))


if __name__ == '__main__':
    main()
