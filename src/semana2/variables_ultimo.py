"""F0 estricto y vínculo de observación a último condicionado. No entrena precios."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import uuid

REPO=Path(__file__).resolve().parents[2]
ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

KEY=['market','line','row_id']
LINES=['motor','buildings','contents']
WEATHER=['hail_days','wind_exposure_index','freezing_days','dry_summer_index','wildfire_index','rainfall_mm','mean_temperature_c']
COMMON_NUM=['voluntary_excess','compulsory_excess','renewal_count','days_quote_to_inception','new_business']
COMMON_CAT=['channel','payment_method']
LINE_NUM={'motor':['years_licensed','ncb_years','vehicle_value_group','vehicle_age','engine_size_cc','seats','driver_assist','named_young_driver'],
    'buildings':['days_unoccupied','smoke_alarms','accidental_damage_cover','mortgage'],
    'contents':['high_value_items','accidental_damage_cover','works_from_home','lodgers','bicycle_cover']}
LINE_CAT={'motor':['driver_age_band','make_model','body_type','transmission','fuel_type','cover_type','overnight_parking','vehicle_use'],
    'buildings':['policyholder_age_band','occupancy'], 'contents':['policyholder_age_band','tenure','security_level']}
ADDRESS_NUM=['flood_zone','distance_to_river_km','elevation_m','bedrooms','basement','trees_within_5m','listed_building','solar_panels']
ADDRESS_CAT=['region','urban_density','soil_type','property_type','roof_type','energy_rating']
CAP_SCREEN={'buildings':10000000.,'contents':1000000.}
BLOCKED={'customer_service_contacts','renewal_decision','written_premium','discount_applied','missed_payments_12m'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item() if hasattr(v,'item') else str(v))+'\n',encoding='utf-8')
def require(ok,msg):
    if not bool(ok):raise ValueError(msg)


def numeric(series):
    result=pd.to_numeric(series,errors='coerce')
    require(not (result.isna()&series.notna()).any(),'Dato numérico no interpretable')
    return result.to_numpy(dtype=float,na_value=np.nan)


def make_features(periods,customers,addresses,line):
    require(customers.customer_id.is_unique and addresses.address_id.is_unique,'Maestro con claves duplicadas')
    f=periods.merge(customers[['customer_id','customer_since_year']],on='customer_id',how='left',validate='many_to_one')
    f=f.merge(addresses,on='address_id',how='left',validate='many_to_one')
    require(len(f)==len(periods),'Join multiplicó periodos')
    meta=[*KEY,'policy_id','customer_id','address_id','period_start','period_end','year','is_test','exposure']
    result=f[meta].copy();numcols=[];catcols=[]
    for col in COMMON_NUM+LINE_NUM[line]+ADDRESS_NUM:
        name='x_'+col;result[name]=numeric(f[col]);numcols.append(name)
    for col in COMMON_CAT+LINE_CAT[line]+ADDRESS_CAT:
        name='x_'+col;result[name]=f[col].astype('string').fillna('__MISSING__');catcols.append(name)
    result['x_start_month']=pd.to_datetime(f.period_start).dt.month.astype(float);numcols.append('x_start_month')
    tenure=numeric(f.year)-numeric(f.customer_since_year)
    require(np.isfinite(tenure).all() and (tenure>=0).all(),'Antigüedad sin referencia válida')
    result['x_customer_tenure_years']=tenure;numcols.append('x_customer_tenure_years')
    age=numeric(f.year)-numeric(f.year_built)
    result['x_property_age']=np.where(age>=0,age,np.nan);numcols.append('x_property_age')
    audit={'rows':len(f),'capital_screened':0,'property_age_unknown':int(np.isnan(result.x_property_age).sum())}
    if line in CAP_SCREEN:
        cap=numeric(f.sum_insured)
        bad=~np.isfinite(cap)|(cap<=0)|(cap>CAP_SCREEN[line])
        result['x_log_sum_insured']=np.log(np.where(bad,np.nan,cap));numcols.append('x_log_sum_insured')
        audit['capital_screened']=int(bad.sum())
        if line=='buildings':
            mapping={'BRK':'brick','STN':'stone','WOD':'timber','MIX':'mixed_or_nonstandard'}
            require(f.construction_type.isin(mapping).all(),'Código de construcción sin revisar')
            result['x_construction_type']=f.construction_type.map(mapping).astype('string');catcols.append('x_construction_type')
    features=numcols+catcols
    require(not any(name.removeprefix('x_') in BLOCKED for name in features),'Variable prohibida en F0')
    require(set(result.columns)==set(meta+features),'Columna de predictor no declarada')
    require(not np.isinf(result[numcols].to_numpy(dtype=float)).any(),'Predictor infinito')
    return result,{'numeric':numcols,'categorical':catcols,'all':features},audit


def historical_weather(periods,weather):
    quote=pd.to_datetime(periods.period_start)-pd.to_timedelta(periods.days_quote_to_inception,unit='D')
    out=periods[KEY+['address_id']].copy()
    out['quote_date']=quote;out['weather_source_year']=quote.dt.year-1
    # No estadístico ni relleno usa las celdas de 2025.
    past=weather.loc[weather.year.le(2024),['address_id','year',*WEATHER]].rename(columns={'year':'weather_source_year',**{x:'wq_'+x for x in WEATHER}})
    require(not past.duplicated(['address_id','weather_source_year']).any(),'Clima duplicado')
    out=out.merge(past,on=['address_id','weather_source_year'],how='left',validate='many_to_one')
    require((out.weather_source_year<out.quote_date.dt.year).all(),'Clima futuro en variante histórica')
    return out


def fit_reporting(delay,age,net,reserve):
    d=np.asarray(delay,dtype=int);r=np.asarray(age,dtype=int)
    y=np.asarray(net,dtype=float);case=np.asarray(reserve,dtype=float)
    require(len(d)>=5,'Menos de cinco notificaciones; no usar validación como fallback')
    require((d>=0).all() and (r>=d).all(),'Retraso o truncamiento imposible')
    values,n=np.unique(d,return_counts=True)
    risk=np.array([np.count_nonzero((d<=v)&(r>=v)) for v in values])
    require((risk>=n).all(),'Conjunto de riesgo incoherente')
    cdf=np.empty(len(values));survival=1.
    for j in range(len(values)-1,-1,-1):
        cdf[j]=survival
        survival*=1-n[j]/risk[j]
    mass=np.diff(np.r_[0.,cdf])
    require(np.all(mass>=-1e-12) and abs(mass.sum()-1)<1e-10,'Masa de conteos incoherente')
    mass=np.maximum(mass,0)
    bucket=np.searchsorted(values,d)
    prob=mass[bucket]/n[bucket]
    require(abs(prob.sum()-1)<1e-10,'Pesos de probabilidad incoherentes')
    result={'delay_days':values.tolist(),'events':n.tolist(),'risk_set':risk.tolist(),'count_cdf':cdf.tolist(),
        'count_mass':mass.tolist(),'n':len(d),'max_delay':int(values.max()),'max_followup':int(r.max()),
        'tail_assumption':'F(max observed delay)=1; no claim of identified mass beyond support','cost_cdf':{},'mean_net_mark':{},'max_individual_cost_share':{}}
    for b in [.75,1.,1.25]:
        mark=y+(b-1)*case
        require(np.isfinite(mark).all() and (mark>=0).all() and mark.sum()>0,'Estrés de reserva con marca negativa o nula')
        costmass=np.array([mass[j]*mark[d==v].mean() for j,v in enumerate(values)])
        total=costmass.sum()
        require(total>0,'Marca media ajustada nula')
        costcdf=np.cumsum(costmass)/total
        result['cost_cdf'][str(b)]=costcdf.tolist()
        result['mean_net_mark'][str(b)]=float(total)
        result['max_individual_cost_share'][str(b)]=float(np.max(prob*mark/total))
    return result,prob*len(d)


def average_completion(periods,model,kind='count',b=1.,tail_mass=0.):
    starts=pd.to_datetime(periods.period_start);ends=pd.to_datetime(periods.period_end)
    a=(pd.Timestamp('2024-12-31')-starts).dt.days.to_numpy()
    z=(pd.Timestamp('2024-12-31')-ends).dt.days.to_numpy()
    active=~periods.is_test.to_numpy(dtype=bool)
    require((a[active]>=z[active]).all() and (z[active]>=0).all(),'Periodo fuera del corte de observación')
    max_age=int(a[active].max(initial=0))
    support=np.asarray(model['delay_days'])
    curve=np.asarray(model['count_cdf'] if kind=='count' else model['cost_cdf'][str(b)])
    positions=np.searchsorted(support,np.arange(max_age+1),side='right')-1
    daily=np.where(positions>=0,curve[np.maximum(positions,0)],0.)
    daily=daily*(1-tail_mass)
    integrated=np.r_[0.,np.cumsum(daily)]
    q=np.ones(len(periods))
    q[active]=(integrated[a[active]+1]-integrated[z[active]])/(a[active]-z[active]+1)
    require(np.isfinite(q).all() and (q>=-1e-10).all() and (q<=1+1e-10).all(),'Completitud fuera de rango')
    return np.clip(q,0,1)


def catalog(data):
    entries=[]
    for path in sorted(data.glob('*.parquet')):
        table=path.stem
        for f in pq.ParquetFile(path).schema_arrow:
            col=f.name
            if col.endswith('_id') or col in ['row_id','surname']:
                role='key_not_predictor' if col!='surname' else 'excluded_name'
            elif table.startswith(('policies_','test_')):
                line=table.split('_',1)[1]
                if col in COMMON_NUM+COMMON_CAT+LINE_NUM[line]+LINE_CAT[line]:role='F0_contractual'
                elif col in ['sum_insured','construction_type']:role='F0_derived_with_quality_rule'
                elif col in ['period_start','period_end']:role='period_metadata'
                elif col=='exposure':role='offset_not_risk_predictor'
                elif col in ['written_premium','discount_applied']:role='excluded_circular_tariff'
                elif col in ['customer_service_contacts','renewal_decision']:role='excluded_post_outcome'
                elif col in ['missed_payments_12m','vehicle_colour']:role='optional_not_in_default'
                else:role='UNREVIEWED'
            elif table=='customers':
                role='F0_derived_tenure' if col=='customer_since_year' else 'conditional_undated_profile_not_default'
            elif table=='addresses':role='F0_physical_under_stability_assumption'
            elif table=='weather':role='weather_metadata' if col=='year' else 'optional_past_only_2025_excluded'
            elif table=='claims':role='claim_outcome_reporting_only_never_F0'
            elif table=='expenses':role='office_premium_only'
            elif table=='reference_policies':role='office_examples_not_model_fit'
            elif table=='sample_submission':role='submission_template_not_model_fit'
            else:role='UNREVIEWED'
            entries.append({'table':table,'column':col,'type':str(f.type),'role':role})
    require(not any(x['role']=='UNREVIEWED' for x in entries),'Campo original sin revisar')
    return entries


def run():
    planpath=REPO/'registro/semana2_variables_ultimo_plan.json'
    plan=json.loads(planpath.read_text(encoding='utf-8'))
    idxpath=REPO/'registro/semana2_preparacion_actual.json'
    index=json.loads(idxpath.read_text(encoding='utf-8'));base=ROOT/index['run']
    data=ROOT/'Hackaton/Semana 2/Datos/emerging'
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
    out=REPO/'privado/semana2/ultimo'/('f0_ultimo_'+stamp);out.mkdir(parents=True,exist_ok=False)
    report={'id':plan['id'],'author':'Codex','started_utc':datetime.now(timezone.utc).isoformat(),'run':out.relative_to(ROOT).as_posix(),
        'pricing_models_trained':0,'pricing_inference':0,'reporting_scope_fits':0,'checks':[],
        'base_index_sha256':sha(idxpath),'base_target_sha256':sha(ROOT/index['target']),'partitions_sha256':sha(ROOT/index['partitions']),
        'plan_sha256':sha(planpath),'code_sha256':sha(Path(__file__)),
        'environment':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pa.__version__}}
    (out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes());(out/'plan_snapshot.json').write_bytes(planpath.read_bytes())
    def check(name,ok,detail=None):
        report['checks'].append({'name':name,'pass':bool(ok),'detail':detail});require(ok,name)
    try:
        check('Base target and partitions unchanged',report['base_target_sha256']==index['target_sha256'] and report['partitions_sha256']==index['partitions_sha256'])
        original_manifest=json.loads((ROOT/'Hackaton/Semana 2/Codex/fuentes/download_manifest.json').read_text(encoding='utf-8'))
        inputs={x['local_path']:x['sha256'] for x in original_manifest['files']}
        check('Original input hashes before',all(sha((ROOT/'Hackaton/Semana 2')/p)==h for p,h in inputs.items()))
        contract={'source_fields':catalog(data),'default':'F0 only','excluded_weather_years':[2025],
            'physical_master_assumption':'Undated physical address fields assumed stable; not historical snapshots',
            'policy_exposure_assumption':'Supplied covered period is conditioning information for challenge total-cost prediction, not a cancellation forecast',
            'capital_screen':CAP_SCREEN,'conditional_gender':'Allowed by synthetic dictionary; excluded default pending explicit fairness/use assessment',
            'encoding':'Categorical strings with explicit missing; no learned imputer, scaler, target or frequency encoder; learn inside fit scope',
            'blocks':{}}
        customers=pq.read_table(data/'customers.parquet').to_pandas();addresses=pq.read_table(data/'addresses.parquet').to_pandas()
        weather=pq.read_table(data/'weather.parquet').to_pandas()
        periods={};feature_stats=[]
        for line in LINES:
            p=pd.concat([pq.read_table(base/f'periods_{kind}_{line}.parquet').to_pandas() for kind in ['policies','test']],ignore_index=True)
            periods[line]=p
            features,spec,stats=make_features(p,customers,addresses,line)
            features.to_parquet(out/f'F0_{line}.parquet',index=False)
            contract['blocks'][line]=spec
            check('F0 no blocked columns '+line,not any(x in spec['all'] for x in [*BLOCKED,*WEATHER,'gender','occupation','fold','group_id','T0']))
            f2=historical_weather(p,weather)
            poisoned=weather.copy();poisoned.loc[poisoned.year.eq(2025),WEATHER]=9.99e99
            again=historical_weather(p,poisoned)
            check('Weather 2025 poisoning invariant '+line,f2.equals(again))
            check('No future weather source '+line,(f2.weather_source_year<f2.quote_date.dt.year).all())
            f2.to_parquet(out/f'optional_weather_quote_{line}.parquet',index=False)
            stats.update({'line':line,'features':len(spec['all']),'numeric':len(spec['numeric']),'categorical':len(spec['categorical']),
                'train_rows':int((~p.is_test).sum()),'test_rows':int(p.is_test.sum()),'weather_history_present':int(f2['wq_hail_days'].notna().sum()),
                'capital_screened_train':int((p.sum_insured>CAP_SCREEN[line]).loc[~p.is_test].sum()) if line in CAP_SCREEN else 0,
                'capital_screened_test':int((p.sum_insured>CAP_SCREEN[line]).loc[p.is_test].sum()) if line in CAP_SCREEN else 0})
            feature_stats.append(stats)
        dump(out/'availability_contract.json',contract);report['features']=feature_stats
        partitions=pq.read_table(ROOT/index['partitions']).to_pandas()
        claims=pq.read_table(base/'claim_assignment_audit.parquet').to_pandas()
        claims=claims.loc[claims.included_in_T0].copy()
        claims=claims.merge(partitions[KEY+['year','fold','group_id']],on=KEY,validate='many_to_one')
        claims['delay']=(pd.to_datetime(claims.report_date)-pd.to_datetime(claims.loss_date)).dt.days
        claims['age']=(pd.Timestamp('2024-12-31')-pd.to_datetime(claims.loss_date)).dt.days
        all_periods=pd.concat(periods.values(),ignore_index=True)
        all_periods=all_periods.merge(partitions[KEY+['fold','group_id']],on=KEY,validate='one_to_one')
        target=pq.read_table(ROOT/index['target']).to_pandas()
        scoped=[];scoped_summaries=[]
        for scope in ['temporal_2024',*[f'exclude_fold{k}' for k in range(5)],'production_2025']:
            if scope=='production_2025':
                fit_mask=~partitions.is_test
            else:
                fit_mask=partitions.year.eq(2023)
                if scope.startswith('exclude_fold'):
                    fold=int(scope[-1]);fit_mask&=partitions.fold.ne(fold).fillna(False)
            fit_ids=set(partitions.loc[fit_mask,'row_id'])
            fit=claims.loc[claims.row_id.isin(fit_ids)].copy()
            check('Reporting fit scope '+scope,set(fit.row_id).issubset(fit_ids) and (scope=='production_2025' or fit.year.eq(2023).all()))
            if scope.startswith('exclude_fold'):
                check('Reporting excludes validation fold '+scope,not fit.fold.eq(int(scope[-1])).any())
            folder=out/scope;folder.mkdir()
            models={};fit_weight_rows=[];offset_summaries=[];scope_models=[]
            for line in LINES:
                ps=all_periods.loc[all_periods.line.eq(line)].copy().reset_index(drop=True)
                obs=ps[KEY+['year','is_test','exposure']].copy()
                group_fit=ps.row_id.isin(fit_ids).to_numpy()
                lg=fit.loc[fit.line.eq(line)]
                rates={b:{} for b in [.75,1.,1.25]}
                longtail=[]
                for peril,g in lg.groupby('peril'):
                    model,weights=fit_reporting(g.delay,g.age,g.T0_cents/100,g.reserve_cents/100)
                    models[line+'|'+peril]=model;scope_models.append({'line':line,'peril':peril,'n':len(g),'max_delay':model['max_delay'],'max_cost_share':model['max_individual_cost_share']['1.0']})
                    qn=average_completion(ps,model)
                    obs['qN_'+peril]=qn;obs['eN_'+peril]=ps.exposure.to_numpy()*qn
                    denom=float(obs.loc[group_fit,'eN_'+peril].sum())
                    require(denom>0,'Denominador nulo del conteo observado')
                    for b in [.75,1.,1.25]:
                        qc=average_completion(ps,model,'cost',b)
                        obs['qC_'+str(b)+'_'+peril]=qc
                        rates[b][peril]=len(g)/denom*model['mean_net_mark'][str(b)]
                    if peril in ['bodily_injury','subsidence']:longtail.append(peril)
                    ww=g[['claim_id',*KEY,'fold','year']].copy();ww['peril']=peril;ww['severity_probability_weight']=weights
                    fit_weight_rows.append(ww)
                    check('CDF monotonic and normalized '+scope+' '+line+' '+peril,all(np.all(np.diff(curve)>=-1e-12) and abs(curve[-1]-1)<1e-10 for curve in [model['count_cdf'],*model['cost_cdf'].values()]))
                    report['reporting_scope_fits']+=1
                shares={}
                for b in [.75,1.,1.25]:
                    total=sum(rates[b].values());require(total>0,'Mezcla de coste nula')
                    shares[str(b)]={k:v/total for k,v in rates[b].items()}
                    qmix=sum(shares[str(b)][peril]*obs['qC_'+str(b)+'_'+peril].to_numpy() for peril in rates[b])
                    obs['q_cost_mix_'+str(b)]=qmix;obs['e_cost_mix_'+str(b)]=ps.exposure.to_numpy()*qmix
                for tail in [.05,.10]:
                    q=obs['q_cost_mix_1.0'].to_numpy().copy()
                    active=~ps.is_test.to_numpy()
                    for peril in longtail:q[active]-=tail*shares['1.0'][peril]*obs.loc[active,'qC_1.0_'+peril].to_numpy()
                    obs['q_cost_mix_tail'+str(tail)]=q;obs['e_cost_mix_tail'+str(tail)]=ps.exposure.to_numpy()*q
                qcols=[x for x in obs if x.startswith('q')]
                check('Completion bounded '+scope+' '+line,np.isfinite(obs[qcols].to_numpy()).all() and obs[qcols].ge(0).all().all() and obs[qcols].le(1+1e-10).all().all())
                check('Positive effective aggregate exposure '+scope+' '+line,obs['e_cost_mix_1.0'].gt(0).all())
                check('Test uses nominal once '+scope+' '+line,np.allclose(obs.loc[obs.is_test,'e_cost_mix_1.0'],obs.loc[obs.is_test,'exposure'],rtol=0,atol=1e-12))
                obs.to_parquet(folder/f'observation_link_{line}.parquet',index=False)
                for year in [2023,2024]:
                    z=obs.loc[obs.year.eq(year)]
                    offset_summaries.append({'line':line,'year':year,'nominal_exposure':float(z.exposure.sum()),'effective_cost_exposure':float(z['e_cost_mix_1.0'].sum()),
                        'cost_completion_exposure_weighted':float(z['e_cost_mix_1.0'].sum()/z.exposure.sum()),'min_row_q':float(z['q_cost_mix_1.0'].min()),
                        'reserve075_effective_exposure':float(z['e_cost_mix_0.75'].sum()),'reserve125_effective_exposure':float(z['e_cost_mix_1.25'].sum())})
                dump(folder/f'peril_cost_shares_{line}.json',shares)
            weights=pd.concat(fit_weight_rows,ignore_index=True)
            weights.to_parquet(folder/'severity_fit_weights.parquet',index=False)
            fit[['claim_id',*KEY,'peril','year','fold']].to_parquet(folder/'reporting_fit_claims.parquet',index=False)
            dump(folder/'reporting_models.json',models)
            scope_summary={'scope':scope,'fitting_periods':len(fit_ids),'fitting_claims':len(fit),'fit_claim_ids_sha256':hashlib.sha256('\n'.join(sorted(fit.claim_id)).encode()).hexdigest(),
                'peril_models':scope_models,'observation_link':offset_summaries,
                'reuse':'exclude_fold k serves both development_2023_fold k and cold_2024_fold k; no duplicate fitting'}
            dump(folder/'summary.json',scope_summary);scoped_summaries.append(scope_summary)
        report['scopes']=scoped_summaries
        check('105 peril reporting fits, zero price models',report['reporting_scope_fits']==105 and report['pricing_models_trained']==0)
        check('Base target and partitions hashes after',sha(ROOT/index['target'])==report['base_target_sha256'] and sha(ROOT/index['partitions'])==report['partitions_sha256'])
        check('Original input hashes after',all(sha((ROOT/'Hackaton/Semana 2')/p)==h for p,h in inputs.items()))
        report['input_sha256']=inputs
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        report['readiness']={'F0_observed_T0_baseline':True,'conditional_ultimate_observation_link':True,'use_weather_2025_default':False,'reserve_adequacy_proven':False,'ultimate_truth_validated':False,'human_general_review_complete':False}
        report['conditions']=['Case reserves and recoveries are conditional best estimates, not independently validated.',
            'Reporting delay and net incurred marks are stationary within peril and independent of truncation calendar under the fitted model.',
            'Unseen tail beyond observed support is not identified; base tail zero and design stresses disclosed.',
            'Aggregate cost mixture is an approximation to row-specific peril composition; per-peril links retained.',
            'Use only frozen feature whitelist; fit encoders/calibration inside split; no double IBNR.',
            'Shared 2024 valuation and physical-master assumptions prevent strict prospective backtest claims.']
        dump(out/'report.json',report)
        files=[{'path':p.relative_to(out).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]
        dump(out/'manifest.json',{'run':report['run'],'files':files,'input_sha256':inputs})
        print(json.dumps({'run':report['run'],'checks':len(report['checks']),'features':report['features'],'reporting_fits':report['reporting_scope_fits'],
            'temporal_observation_links':report['scopes'][0]['observation_link'],'readiness':report['readiness']},ensure_ascii=True))
        return out
    except Exception as exc:
        report['status']='failed_not_promoted';report['error']=str(exc);dump(out/'failed.json',report);raise


if __name__=='__main__':run()
