"""Contrasta la capa preparada con originales, sin importar el productor."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import argparse
import hashlib
import json
import sys
import uuid

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args()
    run=args.run.resolve()
    assert run.is_relative_to((REPO/'privado/semana2/preparacion').resolve())
    verification_dir=run/'verifications'
    verification_dir.mkdir(exist_ok=True)
    output=verification_dir/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json')
    assert not output.exists(), 'Conservar las verificaciones anteriores'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report=json.loads((run/'report.json').read_text(encoding='utf-8'))
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    checks=[]
    def check(name, ok, detail=None):
        checks.append({'name':name,'pass':bool(ok),'detail':detail})
    check('Output manifest hashes',all(sha(run/x['path'])==x['sha256'] for x in manifest['files']))
    check('Current code equals run snapshot',sha(REPO/'src/semana2/preparar_base.py')==report['code_sha256']==sha(run/'code_snapshot.py'))
    check('Current plan equals run snapshot',sha(REPO/'registro/semana2_preparacion_plan.json')==report['plan_sha256']==sha(run/'plan_snapshot.json'))
    data=ROOT/'Hackaton/Semana 2/Datos/emerging'
    original=[]
    changed=0
    for line in ['motor','buildings','contents']:
        for kind in ['policies','test']:
            raw=pq.read_table(data/f'{kind}_{line}.parquet').to_pandas()
            clean=pq.read_table(run/f'periods_{kind}_{line}.parquet').to_pandas()
            keep=[x for x in raw if x!='exposure']
            left,right=raw[keep].copy(),clean[keep].copy()
            # La capa tipa las fechas ISO como timestamps. Comparar el mismo día,
            # sin tolerancia temporal ni modificación del calendario original.
            for date_col in ['period_start','period_end']:
                left[date_col]=pd.to_datetime(left[date_col]).astype('datetime64[ns]')
                right[date_col]=pd.to_datetime(right[date_col]).astype('datetime64[ns]')
            try:
                pd.testing.assert_frame_equal(left,right,check_dtype=False)
                same=True
            except AssertionError:
                same=False
            check(f'Raw fields unchanged {kind} {line}',same)
            check(f'Raw exposure retained {kind} {line}',np.array_equal(raw.exposure,clean.exposure_original))
            days=(pd.to_datetime(raw.period_end)-pd.to_datetime(raw.period_start)).dt.days+1
            check(f'Calendar exposure {kind} {line}',np.allclose(clean.exposure,(days/365).round(4),atol=1e-12,rtol=0))
            changed+=int((~np.isclose(raw.exposure,clean.exposure,atol=1e-7,rtol=0)).sum())
            raw['line']=line;raw['is_test']=kind=='test'; original.append(raw)
    check('Exactly 609 exposure changes',changed==609)
    periods=pd.concat(original,ignore_index=True)
    train=periods.loc[~periods.is_test].copy()
    raw=pq.read_table(data/'claims.parquet').to_pandas()
    raw['loss_date']=pd.to_datetime(raw.loss_date)
    candidates=raw.merge(train[['line','policy_id','row_id','period_start','period_end']],on=['line','policy_id'],how='left')
    inside=candidates.loss_date.between(pd.to_datetime(candidates.period_start),pd.to_datetime(candidates.period_end))
    matched=candidates.loc[inside].copy()
    check('Source-derived unique assignments',not matched.claim_id.duplicated().any() and len(matched)==9222)
    audit=pq.read_table(run/'claim_assignment_audit.parquet').to_pandas()
    expected_ids=raw.claim_id.map(matched.set_index('claim_id').row_id)
    got=raw.claim_id.map(audit.set_index('claim_id').row_id)
    check('Every claim mapping matches raw intervals',expected_ids.fillna('__none__').equals(got.fillna('__none__')))
    pre=raw.loc[expected_ids.isna()].copy()
    earliest=train.groupby(['line','policy_id']).period_start.min()
    first=pre.set_index(['line','policy_id']).index.map(earliest)
    check('All excluded claims truly precede coverage',len(pre)==36 and (pre.loss_date.to_numpy()<pd.to_datetime(first).to_numpy()).all())
    accepted=matched.loc[matched.status.ne('repudiated')].copy()
    for col in ['paid_to_date','incurred_to_date','recoveries']:
        accepted[col+'_decimal_cents']=accepted[col].map(lambda x:int(Decimal(str(x))*100))
    accepted['paid_cents']=accepted.paid_to_date_decimal_cents
    accepted['incurred_cents']=accepted.incurred_to_date_decimal_cents
    accepted['recoveries_cents']=accepted.recoveries_decimal_cents
    accepted['reserve_cents']=accepted.incurred_cents-accepted.paid_cents
    accepted['T0_cents']=accepted.incurred_cents-accepted.recoveries_cents
    accepted['n_accepted']=1;accepted['n_positive']=(accepted.T0_cents>0).astype(int);accepted['n_open']=(accepted.status=='open').astype(int)
    cols=['paid_cents','incurred_cents','recoveries_cents','reserve_cents','T0_cents','n_accepted','n_positive','n_open']
    expected=accepted.groupby(['line','row_id'])[cols].sum()
    targets=pq.read_table(run/'target_T0_and_stresses.parquet').to_pandas()
    t=targets.loc[~targets.is_test].set_index(['line','row_id'])
    expected=expected.reindex(t.index,fill_value=0)
    for col in cols:
        check('Raw Decimal row target '+col,np.array_equal(expected[col].to_numpy(),t[col].to_numpy(dtype='int64')))
    check('Null targets in test',targets.loc[targets.is_test,cols+['T0','T1_reserve075','T1_reserve125']].isna().all().all())
    check('Reserve stress arithmetic',np.allclose(t.T1_reserve075.to_numpy(dtype=float),(4*t.T0_cents-t.reserve_cents).to_numpy(dtype=float)/400,atol=1e-12,rtol=0) and np.allclose(t.T1_reserve125.to_numpy(dtype=float),(4*t.T0_cents+t.reserve_cents).to_numpy(dtype=float)/400,atol=1e-12,rtol=0))
    check('All zero claims periods retained',len(t)==109296 and int(t.n_accepted.eq(0).sum())==int(expected.n_accepted.eq(0).sum()))

    partitions=pq.read_table(run/'partitions.parquet').to_pandas()
    check('Partitions contain every raw period once',len(partitions)==len(periods) and not partitions.duplicated(['market','line','row_id']).any() and set(partitions.row_id)==set(periods.row_id))
    graph=pq.read_table(run/'group_membership_training_only.parquet').to_pandas()
    expected_nodes=set('emerging|customer|'+train.customer_id)|set('emerging|address|'+train.address_id)
    check('Graph has training nodes only',set(graph.node)==expected_nodes)
    check('No target columns in partition files',not any(x in partitions for x in ['T0','T0_cents','incurred','n_accepted']))
    p=partitions.set_index('row_id')
    validation_coverage={'development':[], 'cold':[]}
    for file in sorted((run/'splits').glob('*.parquet')):
        s=pq.read_table(file).to_pandas()
        check(file.stem+' row keys valid',not s.row_id.duplicated().any() and s.row_id.isin(p.index).all())
        if file.stem.startswith(('development_','cold_')):
            full=s.merge(partitions[['row_id','customer_id','address_id']],on='row_id',validate='one_to_one')
            fit=full.loc[full.role.eq('train')];val=full.loc[full.role.eq('validation')]
            for entity in ['customer_id','address_id','group_id']:
                check(file.stem+' disjoint '+entity,set(fit[entity]).isdisjoint(val[entity]))
            check(file.stem+' fit year 2023',fit.year.eq(2023).all())
            family='development' if file.stem.startswith('development') else 'cold'
            check(file.stem+' correct validation year',val.year.eq(2023 if family=='development' else 2024).all())
            validation_coverage[family]+=val.row_id.tolist()
        elif file.stem=='temporal_2024':
            check('Temporal train 2023 validation 2024',s.loc[s.role.eq('train'),'year'].eq(2023).all() and s.loc[s.role.eq('validation'),'year'].eq(2024).all() and len(s)==109296)
        elif file.stem=='production_2025':
            check('Production all labels, test separate',s.loc[s.role.eq('train'),'year'].isin([2023,2024]).all() and s.loc[s.role.eq('test_predict'),'year'].eq(2025).all() and int(s.role.eq('test_predict').sum())==209063)
    for family,year in [('development',2023),('cold',2024)]:
        ids=validation_coverage[family]
        check(family+' each validation row exactly once',len(ids)==len(set(ids)) and set(ids)==set(partitions.loc[partitions.year.eq(year),'row_id']))
    check('Raw input hashes still match',all(sha((ROOT/'Hackaton/Semana 2')/k)==v for k,v in manifest['input_sha256'].items()))
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'separate_local_checker_not_professional_independent_validation',
        'producer_imported':False,'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),
        'zero_claim_periods':int(t.n_accepted.eq(0).sum()),'training':False,'code_sha256':sha(Path(__file__))}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'failed':result['failed'],'zero_claim_periods':result['zero_claim_periods'],
        'failures':[x for x in checks if not x['pass']],'output':str(output.relative_to(ROOT))},ensure_ascii=True))
    raise SystemExit(bool(result['failed']))


if __name__=='__main__':
    main()
