"""Verifica F0 y curvas desde fuentes sin importar el productor."""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import argparse
import hashlib
import json
import sys
import uuid

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(REPO/'privado/semana2/ultimo')
    report=json.loads((run/'report.json').read_text(encoding='utf-8'))
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    index=json.loads((REPO/'registro/semana2_preparacion_actual.json').read_text(encoding='utf-8'));base=ROOT/index['run']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)})
    check('Output manifest hashes',all(sha(run/x['path'])==x['sha256'] for x in manifest['files']))
    check('Producer snapshot exact',sha(REPO/'src/semana2/variables_ultimo.py')==sha(run/'code_snapshot.py')==report['code_sha256'])
    check('Target and folds preserved',sha(ROOT/index['target'])==report['base_target_sha256'] and sha(ROOT/index['partitions'])==report['partitions_sha256'])
    contract=json.loads((run/'availability_contract.json').read_text(encoding='utf-8'))
    check('Every source field reviewed',not any(x['role']=='UNREVIEWED' for x in contract['source_fields']))
    blocked={'row_id','policy_id','customer_id','address_id','T0','n_accepted','fold','group_id','gender','occupation','prior_claims_5y','licence_points','marketing_segment',
        'customer_service_contacts','renewal_decision','written_premium','discount_applied','missed_payments_12m','hail_days','wind_exposure_index','freezing_days','dry_summer_index','wildfire_index','rainfall_mm','mean_temperature_c'}
    periods={};capital=[]
    for line,count in [('motor',40),('buildings',32),('contents',33)]:
        raw=pd.concat([pq.read_table(base/f'periods_{kind}_{line}.parquet').to_pandas() for kind in ['policies','test']],ignore_index=True)
        periods[line]=raw
        f=pq.read_table(run/f'F0_{line}.parquet').to_pandas()
        spec=contract['blocks'][line];names=spec['all']
        check('F0 row identity '+line,raw.row_id.tolist()==f.row_id.tolist() and len(f)==len(raw) and f.row_id.is_unique)
        check('Exact default whitelist '+line,len(names)==count and set(c for c in f if c.startswith('x_'))==set(names) and not any(x.removeprefix('x_') in blocked for x in names))
        check('Metadata not in default features '+line,set(names).isdisjoint({'market','line','year','is_test','exposure','period_start','period_end'}))
        check('No infinities in F0 '+line,not np.isinf(f[spec['numeric']].to_numpy(dtype=float)).any())
        check('Missing categories explicit '+line,f[spec['categorical']].notna().all().all())
        if line!='motor':
            threshold=1e7 if line=='buildings' else 1e6
            bad=raw.sum_insured.gt(threshold)|raw.sum_insured.le(0)|raw.sum_insured.isna()
            expected=np.log(raw.sum_insured.where(~bad))
            check('Capital value/mask exact '+line,np.allclose(f.x_log_sum_insured,expected,equal_nan=True,rtol=0,atol=1e-12))
            z=raw.loc[bad,['market','line','row_id','policy_id','is_test','sum_insured']].copy();z['action']='log_capital_unknown_no_auto_division';capital.append(z)
        h=pq.read_table(run/f'optional_weather_quote_{line}.parquet').to_pandas()
        quote=pd.to_datetime(raw.period_start)-pd.to_timedelta(raw.days_quote_to_inception,unit='D')
        check('Past-weather asof exact '+line,h.quote_date.tolist()==quote.tolist() and h.weather_source_year.tolist()==quote.dt.year.sub(1).tolist())
        check('No weather source 2025 '+line,h.weather_source_year.le(2024).all())
        check('2023 has no fabricated past weather '+line,h.loc[raw.year.eq(2023),[x for x in h if x.startswith('wq_')]].isna().all().all())
    pd.concat(capital,ignore_index=True).to_parquet(run/'capital_uncertainty_audit.parquet',index=False)
    claims=pq.read_table(base/'claim_assignment_audit.parquet').to_pandas()
    claims=claims.loc[claims.included_in_T0].copy()
    claims['delay']=(pd.to_datetime(claims.report_date)-pd.to_datetime(claims.loss_date)).dt.days
    claims['age']=(pd.Timestamp('2024-12-31')-pd.to_datetime(claims.loss_date)).dt.days
    checks_of_positive_exposure=[]

    def average(raw,support,curve):
        starts=(pd.Timestamp('2024-12-31')-pd.to_datetime(raw.period_start)).dt.days.to_numpy()
        ends=(pd.Timestamp('2024-12-31')-pd.to_datetime(raw.period_end)).dt.days.to_numpy()
        mask=~raw.is_test.to_numpy()
        ages=np.arange(starts[mask].max()+1)
        pos=np.searchsorted(support,ages,side='right')-1
        daily=np.where(pos>=0,np.asarray(curve)[np.maximum(pos,0)],0.)
        cumulative=np.r_[0,np.cumsum(daily)]
        out=np.ones(len(raw));out[mask]=(cumulative[starts[mask]+1]-cumulative[ends[mask]])/(starts[mask]-ends[mask]+1)
        return np.clip(out,0,1)

    for scope in report['scopes']:
        name=scope['scope'];folder=run/name
        split='production_2025' if name=='production_2025' else ('development_2023_fold'+name[-1] if name.startswith('exclude_fold') else 'temporal_2024')
        roles=pq.read_table(base/'splits'/f'{split}.parquet').to_pandas()
        fit_ids=set(roles.loc[roles.role.eq('train'),'row_id'])
        fitted=claims.loc[claims.row_id.isin(fit_ids)].copy()
        saved=pq.read_table(folder/'reporting_fit_claims.parquet').to_pandas()
        check('Fitted claims exact scope '+name,set(saved.claim_id)==set(fitted.claim_id) and len(saved)==len(fitted))
        models=json.loads((folder/'reporting_models.json').read_text(encoding='utf-8'))
        weights=pq.read_table(folder/'severity_fit_weights.parquet').to_pandas()
        check('Severity weights exact fitting IDs '+name,set(weights.claim_id)==set(fitted.claim_id) and weights.claim_id.is_unique)
        for line in ['motor','buildings','contents']:
            raw=periods[line];obs=pq.read_table(folder/f'observation_link_{line}.parquet').to_pandas()
            check('Observation rows identity '+name+' '+line,obs.row_id.tolist()==raw.row_id.tolist())
            for peril,g in fitted.loc[fitted.line.eq(line)].groupby('peril'):
                m=models[line+'|'+peril]
                d=g.delay.to_numpy();r=g.age.to_numpy();support=np.unique(d)
                counts=[int((d==t).sum()) for t in support]
                risks=[int(((d<=t)&(r>=t)).sum()) for t in support]
                value=Fraction(1);cdf=[0.]*len(support)
                for j in range(len(support)-1,-1,-1):
                    cdf[j]=float(value);value*=Fraction(risks[j]-counts[j],risks[j])
                mass=np.diff(np.r_[0,cdf])
                tag=name+' '+line+' '+peril
                check('Count CDF exact rational '+tag,np.allclose(m['count_cdf'],cdf,rtol=0,atol=1e-12) and m['risk_set']==risks and m['events']==counts)
                check('Count observation link '+tag,np.allclose(obs['qN_'+peril],average(raw,support,cdf),rtol=0,atol=1e-10))
                for b in [.75,1.,1.25]:
                    mark=(g.T0_cents+(b-1)*g.reserve_cents).to_numpy()/100
                    cmass=np.array([mass[j]*mark[d==t].mean() for j,t in enumerate(support)])
                    expected=np.cumsum(cmass)/cmass.sum()
                    check('Reserve/cost CDF '+str(b)+' '+tag,np.allclose(m['cost_cdf'][str(b)],expected,rtol=0,atol=1e-12))
                    check('Cost observation link '+str(b)+' '+tag,np.allclose(obs['qC_'+str(b)+'_'+peril],average(raw,support,expected),rtol=0,atol=1e-10))
                n_by_delay=dict(zip(support,counts));mass_by_delay=dict(zip(support,mass))
                expected_weight=g.delay.map(mass_by_delay).to_numpy()/g.delay.map(n_by_delay).to_numpy()*len(g)
                actual=g.claim_id.map(weights.set_index('claim_id').severity_probability_weight)
                check('Truncation weights '+tag,np.allclose(actual,expected_weight,rtol=0,atol=1e-12))
                positives=claims.loc[claims.line.eq(line)&claims.peril.eq(peril),'row_id'].unique()
                z=obs.set_index('row_id').loc[positives,'eN_'+peril]
                checks_of_positive_exposure.append({'scope':name,'line':line,'peril':peril,'positive_rows_with_zero_count_exposure':int(z.le(0).sum())})
            shares=json.loads((folder/f'peril_cost_shares_{line}.json').read_text(encoding='utf-8'))
            for b in [.75,1.,1.25]:
                sh=shares[str(b)];mixed=sum(v*obs['qC_'+str(b)+'_'+p].to_numpy() for p,v in sh.items())
                check('Cost mixture '+name+' '+line+' '+str(b),abs(sum(sh.values())-1)<1e-12 and np.allclose(obs['q_cost_mix_'+str(b)],mixed,rtol=0,atol=1e-12) and np.allclose(obs['e_cost_mix_'+str(b)],raw.exposure*mixed,rtol=0,atol=1e-12))
            for tail in [.05,.1]:
                expected=obs['q_cost_mix_1.0'].to_numpy().copy();active=~raw.is_test.to_numpy()
                for peril,share in shares['1.0'].items():
                    if peril in ['bodily_injury','subsidence']:expected[active]-=tail*share*obs.loc[active,'qC_1.0_'+peril].to_numpy()
                check('Tail mass once '+name+' '+line+' '+str(tail),np.allclose(obs['q_cost_mix_tail'+str(tail)],expected,rtol=0,atol=1e-12))
            qcols=[x for x in obs if x.startswith('q')]
            check('Test completion is one '+name+' '+line,np.allclose(obs.loc[raw.is_test,qcols],1,rtol=0,atol=1e-12))
    check('No positive claim has zero effective count exposure',all(x['positive_rows_with_zero_count_exposure']==0 for x in checks_of_positive_exposure))
    check('Original hashes stable',all(sha((ROOT/'Hackaton/Semana 2')/p)==v for p,v in report['input_sha256'].items()))
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'separate_checker_not_independent_professional_review',
        'producer_imported':False,'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),
        'zero_count_exposure_checks':checks_of_positive_exposure,'code_sha256':sha(Path(__file__)),'pricing_models_trained':0}
    folder=run/'verifications';folder.mkdir(exist_ok=True)
    output=folder/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]+'.json')
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'passed':result['passed'],'failed':result['failed'],'output':str(output.relative_to(ROOT)),
        'failures':[x for x in checks if not x['pass']]},ensure_ascii=True))
    raise SystemExit(bool(result['failed']))


if __name__=='__main__':main()
