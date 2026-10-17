"""Verifica CAP02R sin publicar: cohorte exacta, valores completos, reversión y pendientes."""
from decimal import Decimal
from pathlib import Path
import json
import sys

import apply_retrospective_capitals as a
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def main(out):
    if (out/'manifest.json').exists():
        assert a.cap.manifest_ok(out)
        print(json.dumps({'status':'closed_verified_manifest_intact_no_rewrite'}));return
    checks=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:
            c.dump(out/'verification_failure.json',{'status':'failed_not_published','checks':checks})
            raise AssertionError(name)
    oldcat=json.loads((out/'evidence/base_catalog.json').read_text('utf-8'))
    newcat=json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    frozen=pd.read_parquet(out/'evidence/frozen_867_proposal.parquet')
    assessment=pd.read_parquet(out/'evidence/frozen_1454_pending_assessment.parquet')
    ledger=pd.read_parquet(out/'ledger/all_capital_changes.parquet')
    pending=pd.read_parquet(out/'tables/pending_capitals.parquet')
    support=pd.read_parquet(out/'ledger/test2025_supported_changes.parquet')
    sha=c.digest(out/'evidence/frozen_867_proposal.parquet')
    check('Frozen approved proposal exactly matches immutable D48 SHA256',sha==c.digest(a.REVIEW/'tables/proposed_retrospective_scenario_NOT_APPLIED.parquet'))
    check('Exact 867 row IDs and 430/437 table counts in ledger',len(ledger)==ledger.row_id.nunique()==867 and
          set(ledger.row_id)==set(frozen.row_id) and ledger.source_table.value_counts().to_dict()==a.EXPECTED)
    check('Exactly 587 remaining IDs, no deletion or implicit correction',len(pending)==pending.row_id.nunique()==587 and
          set(pending.row_id)==set(assessment.row_id)-set(frozen.row_id) and not set(pending.row_id)&set(ledger.row_id))
    pd.testing.assert_frame_equal(pending[assessment.columns].sort_values('row_id').reset_index(drop=True),
        assessment.loc[~assessment.row_id.isin(frozen.row_id)].sort_values('row_id').reset_index(drop=True),check_exact=True)
    check('All assessment fields of every remaining pending row preserved',True)
    check('All ledger operations explicitly authorized and solely CAP02R /1000',ledger.rule.eq(a.RULE).all() and ledger.divisor.eq(1000).all() and ledger.operation_authorized.all())
    authorization=json.loads((out/'authorization.json').read_text('utf-8'))
    check('Full current user authorization retained',authorization['messages']==[{'role':'user','content':a.REQUEST}] and authorization['cohort_sha256']==sha)
    check('Every change linked to cohort and authorization hashes',ledger.cohort_sha256.eq(sha).all() and ledger.authorization_sha256.eq(c.digest(out/'authorization.json')).all())
    changed_ids=[]
    for name in a.EXPECTED:
        before=pq.read_table(c.ROOT/oldcat[name]['workspace_relative_path'])
        after=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'])
        check(name+': derived SHA256 agrees with catalog',c.digest(c.ROOT/newcat[name]['workspace_relative_path'])==newcat[name]['sha256'])
        check(name+': full schema metadata, row count and column order unchanged',before.schema.equals(after.schema,check_metadata=True) and before.num_rows==after.num_rows and before.column_names==after.column_names)
        check(name+': every other column, null and position exactly unchanged',before.drop(['sum_insured']).equals(after.drop(['sum_insured']),check_metadata=True))
        book=ledger.loc[ledger.source_table.eq(name)].reset_index(drop=True)
        tablebook=pd.read_parquet(out/'ledger'/(name+'_sum_insured.parquet'))
        check(name+': consolidated and per-table ledgers agree exactly',book.equals(tablebook))
        original=before['sum_insured'].to_numpy();actual=after['sum_insured'].to_numpy()
        changed=np.flatnonzero(~np.isclose(original,actual,atol=0,rtol=0,equal_nan=True))
        positions=book.source_position.to_numpy(dtype=int)
        check(name+': all and only authorized positions changed',np.array_equal(changed,positions) and len(changed)==a.EXPECTED[name] and
              book.row_id.tolist()==before.take(pa.array(positions))['row_id'].to_pylist())
        check(name+': every old/new value exactly recorded',np.array_equal(original[positions],book.old) and np.array_equal(actual[positions],book.new))
        check(name+': every new value is exact old/1000 by Decimal',all(Decimal(str(old))/Decimal(1000)==Decimal(str(new)) for old,new in zip(book.old,book.new)))
        check(name+': new capitals positive finite, source null count unchanged',np.isfinite(actual[positions]).all() and (actual[positions]>0).all() and before['sum_insured'].null_count==after['sum_insured'].null_count)
        restored=actual.copy();restored[positions]=book.old.to_numpy()
        reverse=after.set_column(after.schema.get_field_index('sum_insured'),after.schema.field('sum_insured'),pa.array(restored,type=after.schema.field('sum_insured').type))
        check(name+': reversal recovers exact parent Arrow table',reverse.equals(before,check_metadata=True))
        second,count=a.cap.apply_frozen(actual,positions,book.old.to_numpy(),book.new.to_numpy())
        check(name+': second transformation does not divide again',count==0 and np.array_equal(actual,second,equal_nan=True))
        altered=actual.copy();altered[positions[0]]=book.new.iloc[0]+.1
        try:a.cap.apply_frozen(altered,positions,book.old.to_numpy(),book.new.to_numpy())
        except ValueError:conflict_rejected=True
        else:conflict_rejected=False
        check(name+': unrecognized input amount rejected',conflict_rejected)
        check(name+': source/derived hashes included for every changed row',book.source_sha256.eq(oldcat[name]['sha256']).all() and book.derived_sha256.eq(newcat[name]['sha256']).all())
        check(name+': retrospective provenance added without overwriting REN00 lineage',all(newcat[name][key]==value for key,value in oldcat[name].items() if key not in ['workspace_relative_path','sha256']) and newcat[name]['retrospective_capital_rule']==a.RULE)
        p=pending.loc[pending.source_table.eq(name)]
        by_id=pd.Series(actual,index=after['row_id'].to_pylist())
        check(name+': all remaining pending amounts unchanged',np.array_equal(by_id.loc[p.row_id].to_numpy(),p.sum_insured.to_numpy()))
        changed_ids.extend(book.row_id.tolist())
    for name in sorted(set(oldcat)-set(a.EXPECTED)):
        check(name+': complete catalog reference and bytes unchanged',oldcat[name]==newcat[name] and c.digest(c.ROOT/newcat[name]['workspace_relative_path'])==oldcat[name]['sha256'])
    check('Only two derived policy files written, no extra files in data layer',set(p.name for p in (out/'data').iterdir())=={name+'.parquet' for name in a.EXPECTED})
    check('Only sum_insured changed in exactly 867 distinct retained rows',len(changed_ids)==len(set(changed_ids))==867 and set(changed_ids)==set(frozen.row_id))
    expected_flags=frozen.set_index('row_id').later_reference_2025_only_evidence
    check('111 flags agree exactly with frozen review, 756 false',ledger.audit_ref_test2025.sum()==111 and (~ledger.audit_ref_test2025).sum()==756 and
          ledger.set_index('row_id').audit_ref_test2025.sort_index().equals(expected_flags.rename('audit_ref_test2025').sort_index()))
    check('Dedicated 111-row audit extract exactly matches ledger subset',support.reset_index(drop=True).equals(ledger.loc[ledger.audit_ref_test2025].reset_index(drop=True)) and support.source_table.value_counts().to_dict()==a.TEST_ANCHORS)
    check('Marker is only audit metadata in ledger; every actual policy schema unchanged',not any(col.startswith('audit_cap02') for name in a.EXPECTED for col in pq.read_schema(c.ROOT/newcat[name]['workspace_relative_path']).names))
    history=pd.read_parquet(out/'evidence/review_policy_histories.parquet').set_index('row_id')
    # Recheck every anchor against unchanged original policy data, not only the saved review arithmetic.
    fields=set(['row_id','policy_id','period_start','period_end','sum_insured'])
    for flds in a.cap.FIELDS.values():fields.update(flds)
    source_rows={}
    for name in ['policies_buildings','policies_contents','test_buildings','test_contents']:
        schema=pq.read_schema(c.ROOT/newcat[name]['workspace_relative_path'])
        cols=[col for col in schema.names if col in fields]
        source_rows[name]=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'],columns=cols).to_pandas().set_index('row_id')
    errors=[];reference_flags=[]
    for row in ledger.itertuples(index=False):
        curr=history.loc[row.row_id];anchor=source_rows[row.original_later_source_table].loc[row.original_later_row_id]
        start=pd.Timestamp(anchor.period_start);end=pd.Timestamp(anchor.period_end)
        valid=(curr.policy_id==anchor.policy_id==row.policy_id and anchor.sum_insured==row.original_later_sum_insured_CU and
               anchor.sum_insured==history.loc[row.original_later_row_id,'original_sum_insured_CU'] and
               not history.loc[row.original_later_row_id,'cap01_applied'] and
               curr.period_end<start and 1<=(start-curr.period_start).days<=400 and .9<=row.new/anchor.sum_insured<=1.1)
        for col in a.cap.FIELDS[row.line]:
            x,y=curr[col],anchor[col]
            if pd.isna(x) or pd.isna(y):valid=False;continue
            if col=='construction_type':x,y=str(x).casefold().strip(),str(y).casefold().strip()
            valid &= x==y
        flag=row.original_later_source_table.startswith('test_') and start.year==2025
        reference_flags.append(flag)
        if not valid:errors.append(row.row_id)
    check('Every later original anchor, context, nonoverlap, 1-400 days and ratio rechecked',not errors)
    check('111 flags independently identified by actual test table and 2025 date',np.array_equal(reference_flags,ledger.audit_ref_test2025.to_numpy()))
    check('All 111 corrected rows belong to 2024 train, no test policy corrected',ledger.loc[ledger.audit_ref_test2025,'source_table'].str.startswith('policies_').all() and
          pd.to_datetime(ledger.loc[ledger.audit_ref_test2025,'period_start']).dt.year.eq(2024).all() and ledger.source_table.str.startswith('policies_').all())
    check('All 867 operations remain labeled retrospective and unavailable at inception',ledger.retrospective_only.all() and not ledger.evidence_available_at_period_start.any())
    numeric_conflict_ids=set(assessment.loc[assessment.review_group.eq('A_retrospective_D34')&assessment.nearest_prior_numeric_conflict,'row_id'])
    check('All twelve excluded D48 numeric conflicts remain in 587 pending',len(numeric_conflict_ids)==12 and numeric_conflict_ids.issubset(set(pending.row_id)))
    inherited=pd.read_parquet(out/'evidence/CAP01_ledger.parquet')
    preserved=True
    for name,q in inherited.groupby('source_table'):
        values=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
        preserved &= np.array_equal(values.loc[q.row_id].to_numpy(),q.new.to_numpy())
    check('All 2073 CAP01 capitals retained with no repeated division',len(inherited)==2073 and not set(inherited.row_id)&set(ledger.row_id) and preserved)
    check('2940 distinct corrected capitals only in retrospective branch',len(set(inherited.row_id)|set(ledger.row_id))==2940)
    for name in ['test_buildings','test_contents']:
        p=pending.loc[pending.source_table.eq(name)];values=source_rows[name].sum_insured
        check(name+': every remaining pending test capital unchanged',np.array_equal(values.loc[p.row_id].to_numpy(),p.sum_insured.to_numpy()))
    check('No dates, exposure, claims, target components, REN00 or PRE00 changed',
          newcat['claims']==oldcat['claims'] and newcat['policies_motor']==oldcat['policies_motor'] and newcat['test_motor']==oldcat['test_motor'])
    check('Baseline active catalog and every protected original, parent or review hash unchanged',
          all(c.digest(c.ROOT/p)==sha for p,sha in json.loads((out/'protected_hashes_before.json').read_text('utf-8')).items()))
    check('Prior PRE00 and D48 manifests remain intact',a.cap.manifest_ok(a.REVIEW) and a.cap.manifest_ok(c.ROOT/json.loads((out/'evidence/base_index.json').read_text('utf-8'))['workspace_relative_run']))
    check('Summary reconciles 867 changes, 111 flags, 587 pending',json.loads((out/'summary.json').read_text('utf-8'))['capital_changes']==867 and len(support)==111 and len(pending)==587)
    result={'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'checks':checks,
        'capital_changes':867,'pending_unchanged':587,'test2025_supported_changes':111,'reversal_verified':True,
        'idempotence_verified':True,'conflicting_amount_rejected':True,'retrospective_only':True,
        'baseline_catalog_unchanged':True,'independent_validation':False,
        'verified_files':{p.relative_to(out).as_posix():c.digest(p) for p in [out/'dataset_catalog.json',
            out/'data/policies_buildings.parquet',out/'data/policies_contents.parquet',out/'ledger/all_capital_changes.parquet',
            out/'ledger/test2025_supported_changes.parquet',out/'tables/pending_capitals.parquet']}}
    c.dump(out/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','verified_files']},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
