"""Relee cada CAP04R y concilia diferencias completas, reversión, pendientes y linaje."""
from decimal import Decimal
from pathlib import Path
import json
import sys
import apply_context_capitals as a
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
    read=lambda path:pd.read_parquet(out/path)
    parent=json.loads((out/'evidence/parent_catalog.json').read_text('utf-8'));newcat=json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    frozen=read('evidence/frozen_109_proposal.parquet');ledger=read('ledger/all_capital_changes.parquet')
    previous_pending=read('evidence/frozen_576_pending.parquet');pending=read('tables/pending_capitals.parquet')
    history=read('evidence/policy_histories.parquet').set_index('row_id');sha=c.digest(out/'evidence/frozen_109_proposal.parquet')
    check('Exact 109 D53 frozen row IDs and proposal SHA256',len(ledger)==ledger.row_id.nunique()==109 and set(ledger.row_id)==set(frozen.row_id) and sha==c.digest(a.REVIEW/'tables/proposed_scale_changes_NOT_APPLIED.parquet'))
    check('Authorized CAP04R /1000 only',ledger.rule.eq(a.RULE).all() and ledger.divisor.eq(1000).all() and ledger.operation_authorized.all() and ledger.correction_authorized.all() and ledger.capital_change_applied.all())
    auth=json.loads((out/'authorization.json').read_text('utf-8'))
    check('Full request and exact cohort authorization preserved',auth['messages']==[{'role':'user','content':a.REQUEST}] and auth['cohort_sha256']==sha)
    check('Ledger hashes link every row to cohort and authorization',ledger.authorization_sha256.eq(c.digest(out/'authorization.json')).all() and ledger.cohort_sha256.eq(sha).all())
    check('Exactly 467 unique remaining pending IDs',len(pending)==pending.row_id.nunique()==467 and set(pending.row_id)==set(previous_pending.row_id)-set(frozen.row_id))
    pd.testing.assert_frame_equal(pending.reset_index(drop=True),previous_pending.loc[~previous_pending.row_id.isin(frozen.row_id)].reset_index(drop=True),check_exact=True)
    check('All 467 pending assessment fields and order preserved',True)
    # Frozen review-time flags are historical evidence, not rewritten as current authorization.
    check('Review-time false flags preserved in proposal',not frozen.correction_authorized.any() and not frozen.capital_change_applied.any())
    files={'policies_buildings':75,'policies_contents':34}
    for name,expected in files.items():
        before=pq.read_table(c.ROOT/parent[name]['workspace_relative_path']);after=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'])
        part=ledger.loc[ledger.source_table.eq(name)];pos=part.source_position.to_numpy(dtype=int)
        old=before['sum_insured'].to_numpy();new=after['sum_insured'].to_numpy()
        changed=np.flatnonzero(~np.isclose(old,new,rtol=0,atol=0,equal_nan=True))
        check(name+': exact new file SHA256',c.digest(c.ROOT/newcat[name]['workspace_relative_path'])==newcat[name]['sha256'])
        check(name+': full schema, metadata, column and row order preserved',before.schema.equals(after.schema,check_metadata=True) and before.num_rows==after.num_rows and before.column_names==after.column_names)
        check(name+': every noncapital cell, null and position preserved',before.drop(['sum_insured']).equals(after.drop(['sum_insured']),check_metadata=True))
        check(name+': exactly authorized differences',len(part)==expected and np.array_equal(changed,pos) and before.take(pa.array(pos))['row_id'].to_pylist()==part.row_id.tolist())
        check(name+': all old/new values match actual sources',np.array_equal(old[pos],part.old.to_numpy()) and np.array_equal(new[pos],part.new.to_numpy()))
        check(name+': positive finite corrected values and unchanged null count',np.isfinite(new[pos]).all() and (new[pos]>0).all() and before['sum_insured'].null_count==after['sum_insured'].null_count)
        restored=new.copy();restored[pos]=part.old.to_numpy()
        reverse=after.set_column(after.schema.get_field_index('sum_insured'),after.schema.field('sum_insured'),pa.array(restored,type=after.schema.field('sum_insured').type))
        check(name+': reversal recovers complete parent Arrow table',reverse.equals(before,check_metadata=True))
        again,count=a.cap.apply_frozen(new,pos,part.old.to_numpy(),part.new.to_numpy())
        check(name+': second transform has zero changes',count==0 and np.array_equal(again,new,equal_nan=True))
        bad=new.copy();bad[pos[0]]=part.new.iloc[0]+.5
        try:a.cap.apply_frozen(bad,pos,part.old.to_numpy(),part.new.to_numpy())
        except ValueError:rejected=True
        else:rejected=False
        check(name+': unexpected amount rejected',rejected)
        check(name+': every ledger row records correct source/derived hashes',part.source_sha256.eq(parent[name]['sha256']).all() and part.derived_sha256.eq(newcat[name]['sha256']).all())
        check(name+': all previous lineage metadata inherited',all(newcat[name][k]==v for k,v in parent[name].items() if k not in ['workspace_relative_path','sha256']))
        per_table=read('ledger/'+name+'_sum_insured.parquet')
        # Consolidation of buildings/contents can infer object for fields absent in one line.
        # Values stay exact; actual policy schema/metadata are checked strictly above.
        pd.testing.assert_frame_equal(per_table,part.reset_index(drop=True),check_exact=True,check_dtype=False)
        check(name+': table-specific ledger agrees with consolidated ledger',True)
    for name in sorted(set(parent)-set(files)):
        check(name+': complete reference and file unchanged',newcat[name]==parent[name] and c.digest(c.ROOT/newcat[name]['workspace_relative_path'])==parent[name]['sha256'])
    check('Exactly two new files and no new policy audit columns',set(p.name for p in (out/'data').iterdir())=={name+'.parquet' for name in files})
    # Read every published household reference used by this review from the actual new catalog.
    sources={};original={}
    for name in ['policies_buildings','policies_contents','test_buildings','test_contents']:
        ids=history.loc[history.source_table.eq(name)].index.tolist()
        sources[name]=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'],filters=[('row_id','in',ids)]).to_pandas().set_index('row_id')
        original[name]=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured'],filters=[('row_id','in',ids)]).to_pandas().set_index('row_id').sum_insured
    for row in ledger.itertuples(index=False):
        check(row.row_id+': exact Decimal division and frozen proposal amount',Decimal(str(row.old))/Decimal(1000)==Decimal(str(row.new)) and row.old==frozen.set_index('row_id').loc[row.row_id,'sum_insured'] and row.new==row.hypothetical_div1000_CU)
        cur=history.loc[row.row_id];later=sources[row.later_source_table].loc[row.later_row_id]
        complete=True
        for col in a.cap.FIELDS[row.line]:
            x,y=cur[col],later[col]
            if pd.isna(x) or pd.isna(y):complete=False;continue
            if col=='construction_type':x,y=str(x).strip().casefold(),str(y).strip().casefold()
            complete &= x==y
        gap=(pd.Timestamp(later.period_start)-cur.period_start).days
        g=history.loc[history.policy_id.eq(row.policy_id)].sort_values(['period_start']);order=g.index.tolist()
        check(row.row_id+': original immediate later anchor and exact context criterion',complete and later.policy_id==row.policy_id and order[order.index(row.row_id)+1]==row.later_row_id and pd.Timestamp(later.period_start)>cur.period_end and 1<=gap<=400 and .9<=row.new/later.sum_insured<=1.1 and later.sum_insured==row.later_capital_CU==original[row.later_source_table].loc[row.later_row_id] and 0<later.sum_insured<=1000000)
        for ref in set([row.prior_row_id,row.immediate_prior_row_id,row.later_row_id]):
            source=history.loc[ref,'source_table'];actual=sources[source].loc[ref]
            check(row.row_id+': reference '+ref+' complete source cells preserved',all((pd.isna(actual[col]) and pd.isna(history.loc[ref,col])) or (pd.Timestamp(actual[col])==pd.Timestamp(history.loc[ref,col]) if col in ['period_start','period_end'] else actual[col]==history.loc[ref,col]) for col in actual.index))
        expected_flag=row.later_source_table.startswith('test_') and pd.Timestamp(later.period_start).year==2025
        check(row.row_id+': independently verified temporal audit flag',row.audit_ref_test2025==expected_flag and row.retrospective_only and not row.evidence_available_at_period_start)
    for name,part in pending.groupby('source_table'):
        values=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
        check(name+': every remaining pending capital preserved',np.array_equal(values.loc[part.row_id].to_numpy(),part.sum_insured.to_numpy()))
    check('B192 earlier 377 million remains pending and untouched','B00962235' in set(pending.row_id) and sources['policies_buildings'].loc['B00962235','sum_insured']==377000000 and 'B00962235' not in set(ledger.row_id))
    cv=pq.read_table(c.ROOT/newcat['policies_contents']['workspace_relative_path'],columns=['row_id','sum_insured','security_level'],filters=[('row_id','in',['C01596694','C00970610'])]).to_pandas().set_index('row_id')
    check('C486 pending 29.3 million and original missing security retained','C01596694' in set(pending.row_id) and cv.loc['C01596694','sum_insured']==29300000 and pd.isna(cv.loc['C00970610','security_level']))
    inherited_cap01=read('evidence/CAP01_ledger.parquet');prior=read('evidence/prior_retrospective_ledger.parquet')
    for label,inherited,expected in [('CAP01',inherited_cap01,2073),('CAP02R_CAP03R',prior,878)]:
        valid=True
        for name,part in inherited.groupby('source_table'):
            values=pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'],columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
            valid &= np.array_equal(values.loc[part.row_id].to_numpy(),part.new.to_numpy())
        check('Every inherited '+label+' correction retained without redivision',len(inherited)==expected and not set(inherited.row_id)&set(ledger.row_id) and valid)
    signal=read('ledger/test2025_supported_changes.parquet');cum=read('ledger/cumulative_retrospective_changes.parquet');cum_signal=read('ledger/cumulative_test2025_supported_changes.parquet')
    check('Exactly 17 test2025 audit rows: six buildings, eleven contents',len(signal)==17 and signal.line.value_counts().to_dict()=={'contents':11,'buildings':6} and set(signal.row_id)==set(frozen.loc[frozen.test2025_reference,'row_id']))
    pd.testing.assert_frame_equal(signal.reset_index(drop=True),ledger.loc[ledger.audit_ref_test2025].reset_index(drop=True),check_exact=True)
    check('Signal extraction exactly matches ledger',True)
    check('987 unique retrospective rows and correct rule counts',len(cum)==cum.row_id.nunique()==987 and cum.rule.value_counts().to_dict()=={'CAP02R':867,'CAP04R':109,'CAP03R':11})
    pd.testing.assert_frame_equal(cum.iloc[:878].reset_index(drop=True),prior.reset_index(drop=True),check_exact=True)
    check('All prior cumulative ledger records unchanged',True)
    check('129 cumulative test2025 rows, including all 112 inherited',len(cum_signal)==129 and cum_signal.rule.value_counts().to_dict()=={'CAP02R':111,'CAP04R':17,'CAP03R':1} and set(cum_signal.row_id)==set(cum.loc[cum.audit_ref_test2025,'row_id']))
    check('Originals, parent files, both dataset indexes and prior operation indexes unchanged before activation',all(c.digest(c.ROOT/path)==sha for path,sha in json.loads((out/'protected_hashes_before.json').read_text('utf-8')).items()))
    parent_index=json.loads((out/'evidence/parent_index.json').read_text('utf-8'))
    check('Parent CAP03R and D53 immutable manifests intact',a.cap.manifest_ok(c.ROOT/parent_index['workspace_relative_run']) and a.cap.manifest_ok(a.REVIEW))
    verified=[out/'dataset_catalog.json',*(out/'data').glob('*'),*(out/'ledger').glob('*.parquet'),out/'tables/pending_capitals.parquet']
    result={'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'checks':checks,
        'capital_changes':109,'pending_after':467,'new_test2025_supported_rows':17,'cumulative_test2025_supported_rows':129,
        'total_corrected_capitals':3060,'reversal_verified':True,'idempotence_verified':True,'conflict_rejected':True,
        'independent_validation':False,'verified_files':{p.relative_to(out).as_posix():c.digest(p) for p in verified}}
    c.dump(out/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','verified_files']}))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
