"""Reconstrucción explícita de la fuente histórica común de F2 (2021–2024)."""
from pathlib import Path
from datetime import datetime,timezone
import gc
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from .fase2_2024_datos import sha,dump
from .variables_ultimo import average_completion
RAW=ROOT/'Hackaton/Semana 1/Datos'
PARENT=R/'privado/semana2/mision017_fase2/linaje_T2b_v1'
OUT=R/'privado/semana2/mision017_fase2/fuente_f2_2024_v2'
OLD=ROOT/'Hackaton/Semana 2/Claude/ml_independiente_20261023/preparacion.json'
LINES=['motor','buildings','contents']


def prepare():
    assert not OUT.exists(),'Conciliar producción anterior antes de repetir.'
    OUT.mkdir(parents=True)
    paths=[Path(__file__),OLD]+[RAW/(n+'.parquet') for n in ['claims','customers','addresses','weather',
        'policies_motor','policies_buildings','policies_contents']]
    paths+=list((PARENT/'modelos/prod').glob('T2b_*.txt'))
    versions={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in paths}
    dump(OUT/'sources_before.json',versions)
    previous=json.loads(OLD.read_text(encoding='utf-8-sig'))
    claims=pd.read_parquet(RAW/'claims.parquet')
    dup=claims.duplicated([c for c in claims if c!='claim_id'],keep=False)&claims.claim_id.str.len().eq(11)
    removed=int(dup.sum());assert removed==604
    claims=claims.loc[~dup].copy()
    claims['loss_date']=pd.to_datetime(claims.loss_date);claims['report_date']=pd.to_datetime(claims.report_date)
    # The official source includes 274 precoverage claims in2020. Legacy F2
    # includes their mature delays in the reporting CDF, not in period targets.
    assert claims.loss_date.dt.year.isin([2020,2021,2022,2023,2024]).all()
    assert claims.report_date.ge(claims.loss_date).all() and claims.report_date.le('2024-12-31').all()
    claims['net']=claims.incurred_to_date-claims.recoveries
    claims['net_cents']=np.rint(claims.incurred_to_date*100).astype('int64')-np.rint(claims.recoveries*100).astype('int64')
    assert claims.net_cents.ge(0).all() and np.isfinite(claims.net).all()
    curves={};curve_checks=[]
    for (line,peril),g in claims.loc[claims.status.ne('repudiated')].groupby(['line','peril']):
        ages=(pd.Timestamp('2024-12-31')-g.loss_date).dt.days
        mature=g.loc[ages.ge(1095)].copy();delay=(mature.report_date-mature.loss_date).dt.days.to_numpy()
        keep=delay<=1095;weights=mature.net.to_numpy(float)
        assert keep.sum()>=5 and weights[keep].sum()>0
        cdf=np.clip(np.bincount(delay[keep],weights=weights[keep],minlength=1096).cumsum()/weights[keep].sum(),0,1)
        assert abs(cdf[-1]-1)<1e-12
        original=previous['cdf_coste_desarrollado'][line+'|'+peril]
        error=max(abs(float(cdf[d])-original[str(d)]) for d in [0,30,90,180,365,730])
        assert error<=.0000500001,'Diferencia con curva fuente histórica '+line+' '+peril
        curves[(line,peril)]={'delay_days':list(range(1096)),'cost_cdf':{'1.0':cdf.tolist()}}
        curve_checks.append({'line':line,'peril':peril,'mature_claims':int(keep.sum()),'max_error_vs_rounded_historical':error})
    mappings=[]
    for line in LINES:
        m=pd.read_parquet(RAW/f'policies_{line}.parquet',columns=['policy_id','customer_id'])
        m['customer_id']=m.customer_id.str.zfill(8);m['line']=line;mappings.append(m)
    mapping=pd.concat(mappings,ignore_index=True).drop_duplicates(['policy_id','line'])
    cc=claims[['policy_id','line','report_date']].merge(mapping,on=['policy_id','line'],validate='many_to_one')
    del mapping,mappings,m
    customers=pd.read_parquet(RAW/'customers.parquet')
    customers['occupation']=customers.occupation.str.lower().str.strip()
    addresses=pd.read_parquet(RAW/'addresses.parquet')
    weather=pd.read_parquet(RAW/'weather.parquet',columns=['address_id','year','wind_exposure_index','wildfire_index','rainfall_mm','mean_temperature_c'],filters=[('year','<=',2024)])
    assert weather.year.isin([2021,2022,2023,2024]).all()
    climate=weather.groupby('address_id')[['wind_exposure_index','wildfire_index','rainfall_mm','mean_temperature_c']].mean().add_prefix('clima_').reset_index()
    del weather;gc.collect()
    results=[]
    for line in LINES:
        f=pd.read_parquet(RAW/f'policies_{line}.parquet')
        f['customer_id']=f.customer_id.str.zfill(8)
        f['period_start']=pd.to_datetime(f.period_start);f['period_end']=pd.to_datetime(f.period_end)
        f['year']=f.period_start.dt.year;assert f.year.isin([2021,2022,2023,2024]).all()
        assert f.period_end.dt.year.eq(f.year).all()
        f['exposure']=((f.period_end-f.period_start).dt.days+1)/365.
        f['is_test']=False
        g=claims.loc[claims.line.eq(line)].merge(f[['row_id','policy_id','period_start','period_end']],on='policy_id',how='left')
        assigned=g.loc[g.loss_date.ge(g.period_start)&g.loss_date.le(g.period_end)].copy()
        assert not assigned.claim_id.duplicated().any()
        accepted=assigned.loc[assigned.status.ne('repudiated')].copy()
        claims.loc[claims.line.eq(line)&~claims.claim_id.isin(assigned.claim_id)].to_parquet(OUT/f'unassigned_{line}.parquet',index=False)
        f['T0_cents']=f.row_id.map(accepted.groupby('row_id').net_cents.sum()).fillna(0).astype('int64')
        f['T0']=f.T0_cents/100
        assert f.T0_cents.sum()==accepted.net_cents.sum()
        costs={};q={}
        for peril in sorted(claims.loc[claims.line.eq(line),'peril'].unique()):
            q[peril]=average_completion(f,curves[(line,peril)],'cost',1.)
            cost=accepted.loc[accepted.peril.eq(peril),'net'].sum()
            costs[peril]=float(cost/np.average(q[peril],weights=f.exposure))
        shares={p:z/sum(costs.values()) for p,z in costs.items()}
        share_error=max(abs(shares[p]-previous[f'developed_{line}_pesos_peligro'][p]) for p in shares)
        assert share_error<=.0000500001,'Mezcla fuente histórica diferente.'
        f['e_cost']=f.exposure*sum(shares[p]*q[p] for p in shares)
        observed=f.groupby('year').T0.sum()
        for year,total in observed.items():
            assert abs(total-previous[f'developed_{line}_T0_por_anio'][str(year)])<=.011
        f=f.merge(customers,on='customer_id',validate='many_to_one').merge(addresses,on='address_id',validate='many_to_one').merge(climate,on='address_id',validate='many_to_one')
        f['tenure_years']=f.year-f.customer_since_year;f['property_age']=f.year-f.year_built
        f['start_month']=f.period_start.dt.month;f['full_year']=(f.exposure>=.99).astype(int)
        f['log_days_quote']=np.log1p(f.days_quote_to_inception.clip(lower=0))
        age=f['driver_age' if line=='motor' else 'policyholder_age']
        f['age_band']=pd.cut(age,[-1,24,34,49,64,200],labels=['17-24','25-34','35-49','50-64','65+']).astype(str)
        cap_changed=0
        if line!='motor':
            limit=5e6 if line=='buildings' else 2e6;flag=f.sum_insured>limit;cap_changed=int(flag.sum())
            f['sum_insured']=np.where(flag,f.sum_insured/1000,f.sum_insured);f['log_si']=np.log(f.sum_insured)
        if line=='buildings':
            f['construction']=f.construction_type.str.lower().map({'brick':'brick','brk':'brick','stone':'stone','stn':'stone',
                't':'timber','w':'timber','wod':'timber','non_standard':'non_standard','mix':'non_standard'})
            assert f.construction.notna().all()
        ok=(f.period_start-pd.Timedelta(days=365))>=pd.Timestamp('2021-01-01')
        hp=claims.loc[claims.line.eq(line),['policy_id','report_date']].merge(f[['row_id','policy_id','period_start']],on='policy_id')
        hp=hp.loc[hp.report_date.lt(hp.period_start)&hp.report_date.ge(hp.period_start-pd.Timedelta(days=365))]
        hc=cc[['customer_id','report_date']].merge(f[['row_id','customer_id','period_start']],on='customer_id')
        hc=hc.loc[hc.report_date.lt(hc.period_start)&hc.report_date.ge(hc.period_start-pd.Timedelta(days=365))]
        f['hist_pol_12m']=f.row_id.map(hp.groupby('row_id').size()).fillna(0).where(ok,np.nan)
        f['hist_cli_12m']=f.row_id.map(hc.groupby('row_id').size()).fillna(0).where(ok,np.nan)
        columns=lgb.Booster(model_file=str(PARENT/f'modelos/prod/T2b_{line}.txt')).feature_name()
        out=f[['row_id','customer_id','address_id','policy_id','year','period_start','period_end','exposure','e_cost','T0','T0_cents',*columns]].copy()
        out['market']='developed';out['line']=line
        for col in columns:
            if pd.api.types.is_numeric_dtype(out[col]):out[col]=out[col].astype('float32')
            else:out[col]=out[col].astype('category')
        assert out.row_id.is_unique and out.e_cost.gt(0).all()
        out.to_parquet(OUT/f'{line}.parquet',index=False)
        dump(OUT/f'{line}_link.json',{'mature_cost_CDF':{p:curves[(line,p)] for p in shares},'cost_shares':shares,
             'share_max_error_vs_historical':share_error,'original_source_method_replayed':True})
        results.append({'line':line,'rows':len(out),'years':out.year.value_counts().sort_index().to_dict(),
            'cost_cents':int(out.T0_cents.sum()),'capital_normalization_legacy_replayed':cap_changed,'capital_all_cases_verified':False,
            'source_columns':columns,'new_empirical_reporting_curves':len(shares)})
        print(json.dumps({'source_ready':line,'rows':len(out),'cohort_costs_match_historical':True}),flush=True)
        del f,g,assigned,accepted,hp,hc,out,q;gc.collect()
    assert versions=={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in paths}
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_years':[2021,2022,2023,2024],
        'reporting_history_loss_years':sorted(claims.loss_date.dt.year.unique().tolist()),
        'precoverage2020_claims_count':int(claims.loss_date.dt.year.eq(2020).sum()),
        'precoverage_not_assigned_to_invented_policy_periods':True,
        'source_market':'developed','sources':versions,'rows':results,'curve_replay':curve_checks,'new_price_fits':0,
        'empirical_reporting_CDFs_reconstructed':15,'target_C0_refits':0,'weather2025_loaded':False,
        'snapshot_scope':'available at start of 2025, not a prospective backtest of 2024',
        'conditional_quality_limits':['legacy sum-insured /1000 screen retained for parity; unresolved cases not newly certified',
            'undated master profiles assumed stable','payment/discount fields from supplied snapshot','case-reserve adequacy/long tail not identified'],
        'outputs':{p.name:sha(p) for p in OUT.glob('*.parquet')}}
    dump(OUT/'report.json',report);return report
