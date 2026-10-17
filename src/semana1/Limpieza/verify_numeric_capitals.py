"""Comprueba cada CAP03R y preservación íntegra de CAP02R, pendientes y fuentes."""
from decimal import Decimal
from pathlib import Path
import json
import sys

import apply_numeric_capitals as a
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def main(out):
    if (out/'manifest.json').exists():
        assert a.cap.manifest_ok(out);print(json.dumps({'status':'closed_manifest_intact_no_rewrite'}));return
    checks=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:
            c.dump(out/'verification_failure.json',{'status':'failed_not_published','checks':checks});raise AssertionError(name)
    parent=json.loads((out/'evidence/parent_catalog.json').read_text('utf-8'))
    newcat=json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    frozen=pd.read_parquet(out/'evidence/frozen_11_proposal.parquet')
    ledger=pd.read_parquet(out/'ledger/all_capital_changes.parquet')
    original_pending=pd.read_parquet(out/'evidence/frozen_587_pending.parquet')
    pending=pd.read_parquet(out/'tables/pending_capitals.parquet')
    sha=c.digest(out/'evidence/frozen_11_proposal.parquet')
    check('Exact eleven frozen row IDs, matching D51 SHA256',len(frozen)==len(ledger)==ledger.row_id.nunique()==11 and set(ledger.row_id)==set(frozen.row_id) and sha==c.digest(a.REVIEW/'tables/proposed_11_scale_changes_NOT_APPLIED.parquet'))
    check('All operations are authorized CAP03R /1000 only',ledger.operation_authorized.all() and ledger.capital_change_applied.all() and ledger.rule.eq(a.RULE).all() and ledger.divisor.eq(1000).all())
    auth=json.loads((out/'authorization.json').read_text('utf-8'))
    check('Current full user request and cohort authorization preserved',auth['messages']==[{'role':'user','content':a.REQUEST}] and auth['cohort_sha256']==sha)
    check('Every ledger record linked to authorization and frozen cohort',ledger.authorization_sha256.eq(c.digest(out/'authorization.json')).all() and ledger.cohort_sha256.eq(sha).all())
    check('Remaining 576 IDs are exact complement, with C48613718 included',len(pending)==pending.row_id.nunique()==576 and set(pending.row_id)==set(original_pending.row_id)-set(frozen.row_id) and pending.policy_id.eq('C48613718').sum()==1)
    pd.testing.assert_frame_equal(pending.sort_values('row_id').reset_index(drop=True),original_pending.loc[~original_pending.row_id.isin(frozen.row_id)].sort_values('row_id').reset_index(drop=True),check_exact=True)
    check('Every retained pending assessment field preserved',True)
    before=pq.read_table(c.ROOT/parent['policies_contents']['workspace_relative_path'])
    after=pq.read_table(c.ROOT/newcat['policies_contents']['workspace_relative_path'])
    check('New derived file matches catalog SHA256',c.digest(c.ROOT/newcat['policies_contents']['workspace_relative_path'])==newcat['policies_contents']['sha256'])
    check('Full schema, metadata, row count and column order unchanged',before.schema.equals(after.schema,check_metadata=True) and before.num_rows==after.num_rows and before.column_names==after.column_names)
    check('Every value, null and row position outside capital unchanged',before.drop(['sum_insured']).equals(after.drop(['sum_insured']),check_metadata=True))
    old=before['sum_insured'].to_numpy();new=after['sum_insured'].to_numpy();pos=ledger.source_position.to_numpy(dtype=int)
    changed=np.flatnonzero(~np.isclose(old,new,rtol=0,atol=0,equal_nan=True))
    check('Exactly eleven authorized capital positions changed, no others',np.array_equal(changed,pos) and ledger.row_id.tolist()==before.take(pa.array(pos))['row_id'].to_pylist())
    check('All old/new values exactly match source and derived columns',np.array_equal(old[pos],ledger.old.to_numpy()) and np.array_equal(new[pos],ledger.new.to_numpy()))
    check('Every new value is positive and finite, null count preserved',np.isfinite(new[pos]).all() and (new[pos]>0).all() and before['sum_insured'].null_count==after['sum_insured'].null_count)
    restored=new.copy();restored[pos]=ledger.old.to_numpy()
    reverse=after.set_column(after.schema.get_field_index('sum_insured'),after.schema.field('sum_insured'),pa.array(restored,type=after.schema.field('sum_insured').type))
    check('Reversal recovers exact CAP02R parent Arrow table',reverse.equals(before,check_metadata=True))
    second,count=a.cap.apply_frozen(new,pos,ledger.old.to_numpy(),ledger.new.to_numpy())
    check('Second transform is no-op, with no second division',count==0 and np.array_equal(second,new,equal_nan=True))
    bad=new.copy();bad[pos[0]]=ledger.new.iloc[0]+.5
    try:a.cap.apply_frozen(bad,pos,ledger.old.to_numpy(),ledger.new.to_numpy())
    except ValueError:rejected=True
    else:rejected=False
    check('Conflicting amount is rejected without silent repair',rejected)
    check('Every row records correct parent/derived file hashes',ledger.source_sha256.eq(parent['policies_contents']['sha256']).all() and ledger.derived_sha256.eq(newcat['policies_contents']['sha256']).all())
    check('All prior CAP02R lineage metadata inherited without replacement',all(newcat['policies_contents'][key]==value for key,value in parent['policies_contents'].items() if key not in ['workspace_relative_path','sha256']))
    for name in sorted(set(parent)-{'policies_contents'}):
        check(name+': complete reference and file unchanged',newcat[name]==parent[name] and c.digest(c.ROOT/newcat[name]['workspace_relative_path'])==parent[name]['sha256'])
    check('Only one new policy file, no added audit columns',set(p.name for p in (out/'data').iterdir())=={'policies_contents.parquet'} and after.num_columns==before.num_columns)
    history=pd.read_parquet(out/'evidence/twelve_histories.parquet').set_index('row_id')
    sources={}
    for name in ['policies_contents','test_contents']:
        sources[name]=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path']).to_pandas().set_index('row_id')
    exact_by_id=after.to_pandas().set_index('row_id')
    for row in ledger.itertuples(index=False):
        check(row.row_id+': exact Decimal division',Decimal(str(row.old))/Decimal(1000)==Decimal(str(row.new)))
        current=history.loc[row.row_id];initial=history.loc[row.initial_row_id];mid=history.loc[row.midterm_row_id]
        later=sources[row.later_source_table].loc[row.later_row_id]
        known_equal=True
        for ref in [initial,mid,later]:
            for field in a.cap.FIELDS['contents']:
                known_equal &= pd.notna(current[field]) and pd.notna(ref[field]) and current[field]==ref[field]
        valid=(current.policy_id==initial.policy_id==mid.policy_id==later.policy_id==row.policy_id and known_equal and
            initial.sum_insured==row.initial_capital_CU and mid.sum_insured==row.midterm_capital_CU and later.sum_insured==row.later_capital_CU and
            initial.period_end<mid.period_start and mid.period_end<current.period_start and current.period_end<pd.Timestamp(later.period_start) and
            abs(row.new/initial.sum_insured-1)<.05 and abs(later.sum_insured/row.new-1)<.05)
        check(row.row_id+': all four original stages and complete risk context rechecked',valid)
        for reference_id in [row.initial_row_id,row.midterm_row_id,row.later_row_id]:
            source_name=history.loc[reference_id,'source_table']
            check(row.row_id+': reference '+reference_id+' capital preserved',sources[source_name].loc[reference_id,'sum_insured']==history.loc[reference_id,'sum_insured'])
    values=exact_by_id.sum_insured
    for name,part in pending.groupby('source_table'):
        if name=='policies_contents':current_values=values
        else:current_values=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
        check(name+': every remaining pending capital unchanged',np.array_equal(current_values.loc[part.row_id].to_numpy(),part.sum_insured.to_numpy()))
    check('C48613718 capital remains 29300000, no correction',values.loc['C01596694']==29300000 and 'C01596694' not in set(ledger.row_id))
    check('Missing security field in C48613718 initial reference stays null',pd.isna(exact_by_id.loc['C00970610','security_level']))
    for cohort,filename,expected in [('CAP01','CAP01_ledger.parquet',2073),('CAP02R','CAP02R_ledger.parquet',867)]:
        inherited=pd.read_parquet(out/'evidence'/filename);all_ok=True
        for name,part in inherited.groupby('source_table'):
            data=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
            all_ok &= np.array_equal(data.loc[part.row_id].to_numpy(),part.new.to_numpy())
        check('Every '+cohort+' capital retained without redivision',len(inherited)==expected and not set(inherited.row_id)&set(ledger.row_id) and all_ok)
    support=pd.read_parquet(out/'ledger/test2025_supported_changes.parquet')
    check('New test-2025 signal exactly matches frozen proposal',ledger.set_index('row_id').audit_ref_test2025.sort_index().equals(frozen.set_index('row_id').test2025_reference.rename('audit_ref_test2025').sort_index()))
    check('Only C21091984/C02362784 is newly supported by test C02964108',len(support)==1 and support.iloc[0].row_id=='C02362784' and support.iloc[0].policy_id=='C21091984' and support.iloc[0].later_row_id=='C02964108' and support.iloc[0].later_source_table=='test_contents')
    check('2025 dependency independently checked against actual reference date',pd.Timestamp(sources['test_contents'].loc['C02964108','period_start']).year==2025 and support.iloc[0].old==26200000 and support.iloc[0].new==26200)
    cumulative=pd.read_parquet(out/'ledger/cumulative_retrospective_changes.parquet')
    cumulative_support=pd.read_parquet(out/'ledger/cumulative_test2025_supported_changes.parquet')
    check('Cumulative retrospective ledger is 867 inherited plus 11 new, no duplicate row ID',len(cumulative)==cumulative.row_id.nunique()==878 and cumulative.rule.value_counts().to_dict()=={'CAP02R':867,'CAP03R':11})
    check('Cumulative test-2025 extract has 112 rows, 111 inherited plus one new',len(cumulative_support)==112 and cumulative_support.rule.value_counts().to_dict()=={'CAP02R':111,'CAP03R':1} and cumulative_support.audit_ref_test2025.all())
    check('All eleven retain retrospective-only and unavailable-at-inception labels',ledger.retrospective_only.all() and not ledger.evidence_available_at_period_start.any())
    check('Both source layers, originals, baseline index and prior operation index unchanged before publication',all(c.digest(c.ROOT/path)==sha for path,sha in json.loads((out/'protected_hashes_before.json').read_text('utf-8')).items()))
    parent_index=json.loads((out/'evidence/parent_index.json').read_text('utf-8'))
    check('CAP02R and D51 immutable manifests intact',a.cap.manifest_ok(c.ROOT/parent_index['workspace_relative_run']) and a.cap.manifest_ok(a.REVIEW))
    check('No claim, date, exposure or target transformation introduced',newcat['claims']==parent['claims'] and newcat['test_contents']==parent['test_contents'])
    result={'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'checks':checks,
        'capital_changes':11,'pending_unchanged':576,'C48613718_unchanged':True,'new_test2025_supported_rows':1,
        'cumulative_test2025_supported_rows':112,'total_corrected_capitals':2951,'reversal_verified':True,
        'idempotence_verified':True,'conflict_rejected':True,'independent_validation':False,
        'verified_files':{path.relative_to(out).as_posix():c.digest(path) for path in [out/'dataset_catalog.json',
            out/'data/policies_contents.parquet',out/'ledger/all_capital_changes.parquet',out/'tables/pending_capitals.parquet',
            out/'ledger/cumulative_retrospective_changes.parquet',out/'ledger/cumulative_test2025_supported_changes.parquet']}}
    c.dump(out/'verification.json',result)
    print(json.dumps({key:val for key,val in result.items() if key not in ['checks','verified_files']}))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
