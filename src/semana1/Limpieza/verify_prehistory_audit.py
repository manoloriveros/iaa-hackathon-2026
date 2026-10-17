"""Verifica PRE00 por valores completos, asignación independiente y consumidor real."""
from decimal import Decimal
from pathlib import Path
import json
import sys

import clean_data as c
import apply_prehistory_audit as a
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

sys.path.insert(0,str(c.ROOT/'Hackaton/Semana 1/Modelado'))
sys.path.insert(0,str(c.ROOT/'Preparación/src'))
from diagnostico_objetivo import descriptive_proxy
from target_scope import assert_prehistory_excluded, VERSION as TARGET_GUARD_VERSION
from iaa_lab.data import feature_frames
from iaa_lab.predictor_guard import assert_allowed_predictors, select_predictor_columns


def money(part):
    accepted = part.loc[part.status.isin(['open','closed'])]
    sums = {name:sum((Decimal(str(x)) for x in accepted[col]),Decimal('0.00'))
            for name,col in [('paid_accepted_CU','paid_to_date'),('incurred_accepted_CU','incurred_to_date'),
                             ('recoveries_accepted_CU','recoveries')]}
    sums['case_reserve_accepted_CU']=sums['incurred_accepted_CU']-sums['paid_accepted_CU']
    sums['net_accepted_CU']=sums['incurred_accepted_CU']-sums['recoveries_accepted_CU']
    return {'records':len(part),'accepted':len(accepted),
            **{status:int(part.status.eq(status).sum()) for status in ['closed','open','repudiated']},
            **{k:format(v,'.2f') for k,v in sums.items()}}


def main(out):
    if (out/'manifest.json').exists():
        assert a.manifest_ok(out)
        print(json.dumps({'status':'closed_verified_run_manifest_intact_no_rewrite'})); return
    checks=[]
    def check(name,condition):
        checks.append({'check':name,'passed':bool(condition)})
        if not condition:
            raise AssertionError(name)
    def rejects(name,callback):
        try:
            callback()
        except ValueError:
            rejected=True
        else:
            rejected=False
        check(name,rejected)
    parent=json.loads((out/'evidence/parent_catalog.json').read_text('utf-8'))
    new=json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    frozen_path=out/'evidence/frozen_cohort.parquet'
    frozen=pd.read_parquet(frozen_path); ids=set(frozen.claim_id); sha=c.digest(frozen_path)
    ledger=pd.read_parquet(out/'ledger/pre00_marked_claims.parquet')
    before=pq.read_table(c.ROOT/parent['claims']['workspace_relative_path'])
    after=pq.read_table(c.ROOT/new['claims']['workspace_relative_path'])
    check('Exact reviewed cohort: 413 unique claims, matching frozen SHA256',
          len(frozen)==len(ids)==413 and sha==c.digest(a.REVIEW/'tables/frozen_prehistory_cohort.parquet'))
    check('Claims file SHA256 agrees with new catalog',c.digest(c.ROOT/new['claims']['workspace_relative_path'])==new['claims']['sha256'])
    check('Every original value, type, schema metadata, null and row order preserved',after.drop([a.FLAG]).equals(before,check_metadata=True))
    check('Only one column appended, all 162546 rows preserved',after.num_rows==before.num_rows==162546 and after.column_names==before.column_names+[a.FLAG])
    field=after.schema.field(a.FLAG)
    check('Nonnullable Boolean with no missing flags',field.type==pa.bool_() and not field.nullable and after[a.FLAG].null_count==0)
    check('Explicit audit-only, target-exclusion, predictor-exclusion and cohort metadata',
          field.metadata[b'role']==b'audit_only' and field.metadata[b'rule']==b'PRE00' and
          field.metadata[b'excluded_from_predictors']==b'true' and field.metadata[b'excluded_from_current_period_target']==b'true' and
          field.metadata[b'cohort_sha256'].decode()==sha)
    independent=np.fromiter((cid in ids for cid in before['claim_id'].to_pylist()),dtype=bool,count=before.num_rows)
    check('All and only frozen claim IDs marked, independent set-membership algorithm',np.array_equal(independent,after[a.FLAG].to_numpy()))
    check('Exactly 413 true, 162133 false',independent.sum()==413 and (~independent).sum()==162133)
    positions=np.flatnonzero(independent)
    check('Ledger gives exact source positions and IDs in retained order',
          ledger.source_position.tolist()==positions.tolist() and ledger.claim_id.tolist()==before.take(pa.array(positions))['claim_id'].to_pylist())
    check('Ledger preserves every original claim field',
          ledger[before.column_names].reset_index(drop=True).equals(before.take(pa.array(positions)).to_pandas().reset_index(drop=True)))
    frozen_payload=frozen.set_index('claim_id')[before.column_names[1:]].sort_index().copy()
    source_payload=before.to_pandas().set_index('claim_id').loc[sorted(ids)].copy()
    # D46 parsed date32 into timestamps for analysis; normalize only these comparison views.
    for frame in [frozen_payload,source_payload]:
        for col in ['loss_date','report_date']:
            frame[col]=pd.to_datetime(frame[col]).dt.as_unit('ns')
    check('Frozen original claim payload agrees with retained source, with diagnostic date parsing only',frozen_payload.equals(source_payload))
    check('Ledger diagnostic classes preserved, not coverage confirmations',
          ledger.review_class.value_counts().to_dict()=={'legacy_at_dataset_boundary':244,'before_recorded_new_business':169} and
          not ledger.classification_is_coverage_confirmation.any())
    check('Ledger captures authorization, parent and derived SHA256 for every marked row',
          ledger.authorization_sha256.eq(c.digest(out/'authorization.json')).all() and
          ledger.source_sha256.eq(parent['claims']['sha256']).all() and ledger.derived_sha256.eq(new['claims']['sha256']).all())
    again,added=a.append_flag(after,frozen.claim_id.tolist(),sha)
    check('Second application is exact no-op',not added and again.equals(after,check_metadata=True))
    wrong=after.set_column(after.schema.get_field_index(a.FLAG),field,pc.invert(after[a.FLAG]))
    rejects('Conflicting existing values fail closed',lambda:a.append_flag(wrong,frozen.claim_id.tolist(),sha))
    badmeta=field.with_metadata({**field.metadata,b'role':b'predictor'})
    rejects('Conflicting existing metadata fail closed',lambda:a.append_flag(after.set_column(after.schema.get_field_index(a.FLAG),badmeta,after[a.FLAG]),frozen.claim_id.tolist(),sha))
    rejects('Partial cohort cannot be applied',lambda:a.append_flag(before.slice(0,1),frozen.claim_id.tolist(),sha))
    rejects('Repeated cohort ID cannot be applied',lambda:a.append_flag(before,frozen.claim_id.tolist()+[frozen.claim_id.iloc[0]],sha))
    for name in set(parent)-{'claims'}:
        check(name+': complete catalog entry and referenced file unchanged',
              new[name]==parent[name] and c.digest(c.ROOT/new[name]['workspace_relative_path'])==parent[name]['sha256'])
    for key,value in parent['claims'].items():
        if key not in ['workspace_relative_path','sha256']:
            check('DUP01 inherited claim lineage: '+key,new['claims'][key]==value)
    check('DUP01 alias and exclusion ledgers remain hashed in immutable parent run',
          a.manifest_ok(c.ROOT/'Hackaton/Semana 1/Limpieza/runs/dupfix_20261016T195843Z_fc0bb423'))
    claims=after.to_pandas(); source=before.to_pandas()
    for frame in [claims,source]:
        for col in ['loss_date','report_date']:
            frame[col]=pd.to_datetime(frame[col]).dt.as_unit('ns')
    claims['net']=claims.incurred_to_date-claims.recoveries
    source['net']=source.incurred_to_date-source.recoveries
    check('Claim IDs unique and retained representative CL85711436 appears exactly once',
          claims.claim_id.is_unique and claims.claim_id.eq('CL85711436').sum()==1)
    assignments=[]; consumer_rows=[]
    for line in ['motor','buildings','contents']:
        parts=[]
        for partition in ['policies','test']:
            name=partition+'_'+line
            p=pq.read_table(c.ROOT/new[name]['workspace_relative_path'],
                            columns=['row_id','policy_id','period_start','period_end','exposure']).to_pandas()
            for col in ['period_start','period_end']:
                p[col]=pd.to_datetime(p[col]).dt.as_unit('ns')
            parts.append(p)
        periods=pd.concat(parts,ignore_index=True)
        ordered=periods.sort_values(['policy_id','period_start'],kind='stable')
        previous_end=ordered.groupby('policy_id',sort=False).period_end.shift()
        check(line+': intervals do not overlap, unique matching is identifiable',
              not (ordered.period_start.le(previous_end)&previous_end.notna()).any() and periods.row_id.is_unique)
        q=claims.loc[claims.line.eq(line),['claim_id','line','policy_id','loss_date']].copy()
        # Different algorithm from the reviewed many-to-many interval join: backward as-of on non-overlapping intervals.
        result=pd.merge_asof(q.sort_values('loss_date',kind='stable'),periods.sort_values('period_start',kind='stable'),
                             left_on='loss_date',right_on='period_start',by='policy_id',direction='backward',allow_exact_matches=True)
        result.loc[~result.loss_date.between(result.period_start,result.period_end),'row_id']=None
        first=periods.groupby('policy_id').period_start.min()
        is_before=result.loss_date.lt(result.policy_id.map(first))
        result['assignment_status']=np.where(result.row_id.notna(),'unique_period',np.where(is_before,'before_first_observed_period','unresolved_other'))
        check(line+': no unresolved other claim assignments',not result.assignment_status.eq('unresolved_other').any())
        assignments.append(result[['claim_id','line','policy_id','loss_date','row_id','assignment_status']])
        oldproxy,oldcounts=descriptive_proxy(source,periods,line)
        newproxy,newcounts=descriptive_proxy(claims,periods,line)
        pd.testing.assert_frame_equal(oldproxy,newproxy,check_exact=True)
        check(line+': real descriptive consumer returns identical cost/count on every current period',oldcounts==newcounts and len(newproxy)==len(periods))
        consumer_rows.append({'line':line,'periods':len(periods),'exact_dataframe_equality':True,
                              'accepted_claims':int(newproxy.accepted_claims.sum()),
                              'net_observed_float_diagnostic_CU':float(newproxy.observed_net_incurred.sum()),'assignment_counts':newcounts})
        positive=claims.loc[claims.line.eq(line)&claims[a.FLAG],'claim_id']
        rejects(line+': target guard rejects a forced first-row/report-date assignment',
                lambda:assert_prehistory_excluded(claims.loc[claims.line.eq(line)],pd.concat([result.loc[result.row_id.notna(),'claim_id'],positive.iloc[:1]])))
        covered_id=result.loc[result.row_id.notna(),'claim_id'].iloc[0]
        poisoned=claims.copy(); poisoned.loc[poisoned.claim_id.eq(covered_id),a.FLAG]=True
        rejects(line+': real consumer stops if a marked claim is placed in a covered interval',
                lambda:descriptive_proxy(poisoned,periods,line))
        del oldproxy,newproxy,periods,parts,result
    assigned=pd.concat(assignments,ignore_index=True)
    reviewed=pd.read_parquet(out/'evidence/review_assignment.parquet')
    reviewed['loss_date']=pd.to_datetime(reviewed.loss_date).dt.as_unit('ns')
    keys=['claim_id','line','policy_id','loss_date','row_id','assignment_status']
    pd.testing.assert_frame_equal(assigned[keys].sort_values('claim_id').reset_index(drop=True),
                                  reviewed[keys].sort_values('claim_id').reset_index(drop=True),check_dtype=False)
    check('Independent assignment exactly matches all 162546 reviewed assignments',True)
    annotation=claims[['claim_id',a.FLAG]].merge(assigned[['claim_id','row_id','assignment_status']],on='claim_id',validate='one_to_one')
    check('Every marked claim remains unassigned before first observed period',
          annotation.loc[annotation[a.FLAG],'row_id'].isna().all() and
          annotation.loc[annotation[a.FLAG],'assignment_status'].eq('before_first_observed_period').all())
    check('No unmarked claim is silently added to PRE00',
          set(annotation.loc[annotation.assignment_status.eq('before_first_observed_period'),'claim_id'])==ids)
    assert_prehistory_excluded(claims,assigned.loc[assigned.row_id.notna(),'claim_id'])
    assigned.to_parquet(out/'tables/claim_period_assignment.parquet',index=False)
    annotation.to_parquet(out/'tables/target_scope_reconciliation.parquet',index=False)
    annotation.loc[annotation[a.FLAG]].to_csv(out/'tables/pre00_target_exclusion.csv',index=False)
    selected=annotation.loc[annotation.row_id.notna(),'claim_id']
    books=[]
    for scope,part in [('all',claims),('assigned',claims.loc[claims.claim_id.isin(selected)]),('prehistory',claims.loc[claims[a.FLAG]])]:
        books.append({'scope':scope,**money(part)})
    prior=json.loads((out/'evidence/review_financial_reconciliation.json').read_text('utf-8'))
    for book in books:
        check('Financial counts and every monetary component unchanged: '+book['scope'],book==next(x for x in prior if x['scope']==book['scope']))
    by_scope={x['scope']:x for x in books}
    for name,value in by_scope['all'].items():
        if name=='scope':continue
        if name.endswith('_CU'):
            reconciled=Decimal(value)==Decimal(by_scope['assigned'][name])+Decimal(by_scope['prehistory'][name])
        else:
            reconciled=value==by_scope['assigned'][name]+by_scope['prehistory'][name]
        check('Assigned plus PRE00 equals all: '+name,reconciled)
    owner_hist=pd.read_parquet(out/'evidence/review_all_affected_claim_histories.parquet')
    other_ids=set(owner_hist.claim_id)-ids
    check('All 221 other claims on affected policies preserved and still assigned',
          len(other_ids)==221 and other_ids.issubset(set(selected)) and not claims.loc[claims.claim_id.isin(other_ids),a.FLAG].any())
    check('409 accepted marked claims, 15 open, 4 repudiated, 1721459.84 CU isolated',
          by_scope['prehistory']['accepted']==409 and by_scope['prehistory']['open']==15 and
          by_scope['prehistory']['repudiated']==4 and by_scope['prehistory']['net_accepted_CU']=='1721459.84')
    check('Current accepted observed net cost remains 741156868.43 CU',by_scope['assigned']['net_accepted_CU']=='741156868.43')
    roles={f.name:(f.metadata or {}).get(b'role',b'').decode() for f in after.schema}
    check('Schema-wide predictor guard excludes audit_pre00',a.FLAG not in select_predictor_columns(after.column_names,roles=roles))
    rejects('Explicit request to predict from audit_pre00 is rejected',lambda:assert_allowed_predictors(['exposure',a.FLAG],roles))
    # Exercise actual feature_frames with real source claims solely as an exclusion-control probe, not an approved model matrix.
    probe=pd.concat([claims.loc[claims[a.FLAG]].head(10),claims.loc[~claims[a.FLAG]].head(10)],ignore_index=True)
    config={'id_column':'claim_id','target_column':'__T0_not_materialized__','split':{'group_column':'policy_id','time_column':'loss_date'}}
    x,xt=feature_frames(probe,probe.copy(),config)
    poisoned=probe.copy();poisoned[a.FLAG]=~poisoned[a.FLAG]
    px,pt=feature_frames(poisoned,poisoned.copy(),config)
    pd.testing.assert_frame_equal(x,px);pd.testing.assert_frame_equal(xt,pt)
    check('Actual predictor consumer excludes PRE00; changing its values cannot change selected input',a.FLAG not in x and a.FLAG not in xt and len(x)==len(probe))
    for label,value in [('nullable',probe[a.FLAG].astype('boolean').mask(probe.index==0)),('string',probe[a.FLAG].astype(str))]:
        invalid=probe.copy();invalid[a.FLAG]=value
        rejects('Target guard rejects '+label+' audit flag',lambda:assert_prehistory_excluded(invalid,[]))
    for path,hash_before in json.loads((out/'protected_hashes_before.json').read_text('utf-8')).items():
        check('Protected original/parent/review/index unchanged: '+path,c.digest(c.ROOT/path)==hash_before)
    c.dump(out/'financial_reconciliation.json',books)
    pd.DataFrame(books).to_csv(out/'tables/financial_reconciliation.csv',index=False)
    c.dump(out/'consumer_verification.json',{'status':'passed_real_consumer_checks','periods_checked':sum(x['periods'] for x in consumer_rows),
        'by_line':consumer_rows,'target_guard_version':TARGET_GUARD_VERSION,
        'operational_T0_materialized':False,'models_trained':False,
        'files':{p.relative_to(c.ROOT).as_posix():c.digest(p) for p in [
            c.ROOT/'Hackaton/Semana 1/Modelado/target_scope.py',c.ROOT/'Hackaton/Semana 1/Modelado/diagnostico_objetivo.py',
            c.ROOT/'Preparación/src/iaa_lab/predictor_guard.py',c.ROOT/'Preparación/src/iaa_lab/data.py']}})
    c.dump(out/'verification.json',{'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'checks':checks,
        'full_original_value_and_schema_equality':True,'reversal_verified':True,'idempotence_verified':True,
        'assignment_algorithm':'Backward as-of over proven non-overlapping intervals, compared to reviewed interval join.',
        'financial_sums':'Decimal from source decimal strings; no monetary values rewritten.',
        'target_consumer_checked':True,'predictor_consumer_checked':True,'independent_validation':False})
    print(json.dumps({'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'periods_checked':sum(x['periods'] for x in consumer_rows)}))


if __name__=='__main__':
    main(Path(sys.argv[1]).resolve())
