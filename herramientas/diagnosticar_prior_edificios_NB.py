"""Diagnostico de una contraccion ya fallida: cohortes, costes y exposicion.

No aprende nuevos parametros, no modifica precios ni produce un candidato.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,importlib.util,json,math,subprocess,sys
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=module('buildings_diag_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
a=module('buildings_diag_arithmetic',R/'herramientas/auditar_evaluacion_documento.py')
BASE=R/'privado/semana2/mision017_fase2'
TRIAL=BASE/'NB_nivel_credibilidad_20261027'
ACTIVE=R/'privado/validacion_cadena_f3c_A1_mezcla/20261027T175434Z'
OUT=BASE/'NB_edificios_prior_diagnostico_20261027'
PLAN=R/'registro/semana2_NB_edificios_prior_diagnostico_plan.json'
INDEX=R/'registro/semana2_NB_edificios_prior_diagnostico_actual.json'
DOC=R/'docs/archivo/semana2/NB_EDIFICIOS_PRIOR_DIAGNOSTICO_20261027.md'
R1OUT=BASE/'produccion_R1_privada_20261027'
F3=R/'privado/semana2/claude_mision017_20261025/F3c_2025.csv'
PARTITIONS=ROOT/w.read(ROOT/'RUTAS_PROYECTO.json')['week_2_validation_partitions']
V=pd.Timestamp('2024-12-31')
def utc():return datetime.now(timezone.utc).isoformat()
def scalar(value):
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,Path):return str(value)
    if isinstance(value,pd.Timestamp):return value.isoformat()
    raise TypeError(type(value).__name__)
def dump(path,obj):
    encoded=json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=scalar)+'\n';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:f.write(encoded)
def post(body,identifier,subject):
    path=OUT/(identifier+'.md');path.write_text(body,encoding='utf8')
    q=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',identifier,'--asunto',subject,'--cuerpo',str(path)],check=True,capture_output=True,text=True,encoding='utf8')
    return json.loads(q.stdout)
def sources():
    return [Path(__file__),Path(a.__file__),TRIAL/'parameters.json',TRIAL/'training_new_layer.parquet',TRIAL/'predictions2024.parquet',TRIAL/'results.json',TRIAL/'verification.json',TRIAL/'completion_receipt.json',
        ACTIVE/'prepared/emerging_buildings.parquet',ACTIVE/'prepared/emerging_claims.parquet',ACTIVE/'parameters_T2b.json',ACTIVE/'scenario_results.json',PARTITIONS,
        R1OUT/'production_quotes.parquet',R1OUT/'quote_receipt.json',R1OUT/'R1_T2b_2025.csv',F3,
        *[ACTIVE/'scenarios'/f'{i:02d}.npz' for i in range(50)]]
def freeze():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists();OUT.mkdir()
    trial=w.read(TRIAL/'completion_receipt.json');assert not trial['adopted'] and trial['new_submissions']==0
    plan={'author':'Codex','utc':utc(),'kind':'diagnostic only, no refit or new quote','reason':'NB-CRED300 damages buildings NB. Need assess whether ramo is a transportable prior rather than selecting a favorable ramo/K after seeing results.',
        'hypotheses':['At fixed prices, uniform7.09%uplift may impose a price-only penalty not offset by observed cost term.','NB train support, exposure and report/reserve maturity differ from renewal and across years; ramo prior may not transport.','Large losses/perils can offset average gradients, so decompose rather than remove them.'],
        'configuration':{'years':'Historical emerging2023/2024 only, valuation2024-12-31. Use existing2023trainingmu and saved2024R1/failedcandidate. No model loaded or adjusted.',
            'cohorts':'ramo buildings by year/NB-renewal; exposure bands<.5,.5-.9,>=.9; startquarter; canonical saved2024fold slices.',
            'covariates':'Report ALL construction, occupancy, channel, priorclaims0/1/2+, daysunoccupied missing/0/1-30/31-60/>60, suminsured<100k/100-300k/300k-1m/1-5m/>5m. Descriptive only, no feature/subgroup selection.',
            'accounting':'Use assigned accepted claims already saved. Net=incurred-recoveries=(paid-recoveries)+(incurred-paid). Reconcile rowT0 cents; preserve rejected claims and unassigned36in originals, no reassignment.',
            'exact_loss_split':'For h=fixedcandidate/R1 onbuildingsNB, gain=4*y/sqrt(mu)*(1-h^-0.5)+4*sqrt(mu)*(1-h^0.5). Separate observedcost/peril/paid/reserve terms from unallocated price-only term. No arbitrary allocation of price penalty to perils.',
            'timing':'Compare actual reportlags, open claims, reserve fractions, lossage and meanexistingq; report-year censoring differs by cohort, so no claim that observedlate fraction is ultimate rate.',
            'tail':'Report fixed top1%positive-cost rows and group gain signs, no deletion or recalibration.',
            'future':'Only saved2025exposure/NB/ramo counts, no prices or labels loaded from that file and no new2025quote.',
            'stress':'Reuse50held2024scenario labels with the unchanged failed prices; compute only new buildingsNBslice. No new source/C0/target learning, no probabilities.'},
        'controls':['Fullclaim/row cents accounting','Exact two-term loss identity and per-claim/peril cost identity','sklearnD2andderivative by another method','Fixedh, parameters and originalCSVhashes preserved','No producedCSV, fittedconstants, resampling or modelinference'],
        'model_status_clarification':'F3c remains reviewed delivered reference, R1 preserved alternative, NB-CRED300 not adopted/not submitted. This does not establish F3c private superiority or manual final selection.',
        'budget':{'new_native_or_closed_fits':0,'new_CDF_fits':0,'new_Booster_inference':0,'new_bootstrap_draws':0,'new_2025_quotes':0,'new_submissions':0},
        'decision':'Use findings to define next mechanistic question; no candidate admission or score/public multiplier rescue.2024alreadyadaptive; computational own review not independentprofessional validation.',
        'sources':{w.rel(path):w.sha(path) for path in sources()}}
    dump(PLAN,plan)
    forum=post('Codex. Continúo con un diagnóstico sin ajustes del fallo de NB-CRED300 en edificios nuevos. Antes de calcular separo cohortes/exposición, fechas de reporte/reserva y peligros; verificaré la identidad exacta de devianza entre término de coste observado y penalización por subir precios. Se conservarán los siniestros grandes y todos los estratos predefinidos. La composición2025 se leerá solo como exposición, sin precios ni etiquetas. Reutilizaré los precios fallidos y las cincuenta etiquetas de escenarios para el corte NB de edificios, sin nuevas curvas o aprendizaje. No seleccionaré K, ramos o covariables por estos resultados. Aclaro el estado solicitado: F3c sigue como referencia enviada, R1 se conserva como alternativa y la contracción no fue adoptada ni enviada; no cambié selección final de Kaggle. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),'COD-S2-20261028-EDIFICIOS-NB-DIAG-PREVIO','Diagnostico de edificios NB y continuidad de F3c como referencia enviada')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':forum});dump(INDEX,{'author':'Codex','utc':utc(),'status':'registered_diagnostic_only','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),'forum':forum,'output':w.rel(OUT),'new_submissions':0})
    print(json.dumps({'registered':True,'plan_sha256':w.sha(PLAN)}),flush=True)
def guard():
    assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    for name,sha in w.read(PLAN)['sources'].items():assert w.sha(ROOT/name)==sha,name
def safe_ratio(x,y):return float(x/y) if y!=0 else None
def describe(g):
    den=a.null_loss(g.y.to_numpy());gain=float(g.loss_gain.sum());mu=g.R1.to_numpy();y=g.y.to_numpy()
    return {'rows':len(g),'positive_periods':int(g.y.gt(0).sum()),'exposure':float(g.exposure.sum()),'mean_exposure':float(g.exposure.mean()),
        'T0':float(g.y.sum()),'R1_observed_price_sum':float(g.R1.sum()),'observed_AE':safe_ratio(g.y.sum(),g.R1.sum()),
        'q_exposure_weighted':float(np.average(g.q,weights=g.exposure)),
        'gain_deviance':gain,'delta_D2':safe_ratio(gain,den),'cost_term':float(g.cost_term.sum()),'price_only_term':float(g.price_term.sum()),
        'gradient_dDeviance_dLogPrice':float(2*np.sum(np.sqrt(mu)-y/np.sqrt(mu)))}
def analyze():
    guard();assert not (OUT/'results.json').exists()
    cols=['row_id','year','line','new_business','customer_id','address_id','period_start','period_end','exposure','y','q','construction','occupancy','channel','prior_claims_5y','days_unoccupied','sum_insured']
    available=pd.read_parquet(ACTIVE/'prepared/emerging_buildings.parquet');cols=[c for c in cols if c in available]
    t=available[cols].copy();del available
    train=pd.read_parquet(TRIAL/'training_new_layer.parquet');train=train[train.line.eq('buildings')].set_index('row_id')
    test=pd.read_parquet(TRIAL/'predictions2024.parquet');test=test[test.line.eq('buildings')].set_index('row_id')
    original=w.read(ACTIVE/'parameters_T2b.json')['recipe'];param=w.read(TRIAL/'parameters.json')['params']['buildings'];h=param['quote_ratio']
    t['R1']=np.nan;t['q']=np.nan;t['candidate']=np.nan
    # Original prepared data has no savedq: read only the saved training/evaluation scopes.
    trq=pd.read_parquet(ACTIVE/'training2023_T2b.parquet',columns=['row_id','q']).set_index('row_id').q
    teq=pd.read_parquet(ACTIVE/'predictions_T2b.parquet',columns=['row_id','q']).set_index('row_id').q
    i=t.year.eq(2023);j=t.year.eq(2024)
    level=t.new_business.astype(int).map({b:original['levels']['sin_factores']['buildings_'+str(b)] for b in [0,1]})
    t.loc[i,'R1']=t.loc[i,'row_id'].map(train.mu_afterF2shape).to_numpy()*level[i].to_numpy();t.loc[i,'q']=t.loc[i,'row_id'].map(trq).to_numpy()
    t.loc[j,'R1']=t.loc[j,'row_id'].map(test.R1).to_numpy();t.loc[j,'q']=t.loc[j,'row_id'].map(teq).to_numpy()
    assert i.sum()==12580 and j.sum()==14867 and t.R1.notna().all() and t.q.notna().all()
    t['candidate']=t.R1*np.where(t.new_business,h,1.);t['loss_gain']=a.loss(t.y,t.R1)-a.loss(t.y,t.candidate)
    rh=np.sqrt(np.where(t.new_business,h,1.));t['cost_term']=4*t.y/np.sqrt(t.R1)*(1-1/rh);t['price_term']=4*np.sqrt(t.R1)*(1-rh)
    identity=float(np.max(np.abs(t.loss_gain-t.cost_term-t.price_term)));assert identity<1e-8
    assert np.allclose(t.loc[j,'candidate'],t.loc[j,'row_id'].map(test.candidate).to_numpy(),rtol=0,atol=0)
    t['exposure_band']=np.where(t.exposure<.5,'short_<.5',np.where(t.exposure<.9,'medium_.5_.9','long_>=.9'))
    t['start_quarter']=pd.to_datetime(t.period_start).dt.quarter.astype(str)
    t['prior_band']=pd.to_numeric(t.prior_claims_5y,errors='coerce').clip(upper=2).fillna(-1).astype(int).astype(str)
    days=pd.to_numeric(t.days_unoccupied,errors='coerce');t['unoccupied_band']=np.select([days.isna(),days.lt(0),days.eq(0),days.le(30),days.le(60)],['missing','negative','0','1-30','31-60'],default='>60')
    si=pd.to_numeric(t.sum_insured,errors='coerce');t['insured_band']=pd.cut(si,[-np.inf,1e5,3e5,1e6,5e6,np.inf],labels=['<100k','100-300k','300k-1m','1-5m','>5m'],right=False).astype(str)
    cohorts=[];bands=[];covariates=[]
    for (year,nb),g in t.groupby(['year','new_business']):cohorts.append({'year':int(year),'NB':int(nb),**describe(g)})
    for fields in [['year','new_business','exposure_band'],['year','new_business','start_quarter']]:
        for keys,g in t.groupby(fields):bands.append({'stratum':dict(zip(fields,[int(x) if isinstance(x,(int,np.integer,bool,np.bool_)) else str(x) for x in keys])),**describe(g)})
    for name in ['construction','occupancy','channel','prior_band','unoccupied_band','insured_band']:
        for (year,nb,value),g in t.groupby(['year','new_business',name],dropna=False):covariates.append({'feature':name,'year':int(year),'NB':int(nb),'value':str(value),**describe(g)})
    claims=pd.read_parquet(ACTIVE/'prepared/emerging_claims.parquet');claims=claims[claims.line.eq('buildings')].copy();assert claims.claim_id.is_unique
    all_claims=len(claims);rejected=int((~claims.accepted).sum());c=claims[claims.accepted].copy()
    # Preserve already assigned claims and originals; no reassignment or exclusion by size.
    mergecols=['row_id','year','new_business','R1'];c=c.merge(t[mergecols],on='row_id',how='left',validate='m:1');assert c.year.notna().all()
    cost=c.groupby('row_id').net.sum();rowcost=t.row_id.map(cost).fillna(0).to_numpy();assert np.array_equal(np.rint(rowcost*100).astype('int64'),np.rint(t.y.to_numpy()*100).astype('int64'))
    for name in ['loss_date','report_date']:c[name]=pd.to_datetime(c[name])
    c['reserve']=c.incurred_to_date-c.paid_to_date;c['net_paid']=c.paid_to_date-c.recoveries
    assert np.max(np.abs(c.net-c.reserve-c.net_paid))<1e-7
    c['lag_days']=(c.report_date-c.loss_date).dt.days;c['loss_age_atV']=(V-c.loss_date).dt.days;c['late_calendar_report']=c.report_date.dt.year.gt(c.loss_date.dt.year)
    coefficient=4/np.sqrt(c.R1)*(1-1/np.sqrt(np.where(c.new_business,h,1.)))
    c['cost_gain']=coefficient*c.net;c['reserve_gain']=coefficient*c.reserve;c['paid_gain']=coefficient*c.net_paid
    timings=[];perils=[]
    for (year,nb),g in c.groupby(['year','new_business']):
        relevant=t[t.year.eq(year)&t.new_business.eq(nb)];observed=float(g.net.sum())
        timings.append({'year':int(year),'NB':int(nb),'accepted_claims':len(g),'positive_claims':int(g.net.gt(0).sum()),'open_claims':int(g.status.eq('open').sum()),
            'cost_T0':observed,'reserve':float(g.reserve.sum()),'reserve_share':safe_ratio(g.reserve.sum(),observed),'net_paid':float(g.net_paid.sum()),
            'late_calendar_report_count':int(g.late_calendar_report.sum()),'late_calendar_report_cost':float(g.loc[g.late_calendar_report,'net'].sum()),
            'median_lag_days':float(g.lag_days.median()),'mean_loss_age_days':float(g.loss_age_atV.mean()),'negative_lag_count':int(g.lag_days.lt(0).sum()),
            'cost_term_from_claims':float(g.cost_gain.sum()),'cost_term_from_periods':float(relevant.cost_term.sum()),'reserve_part_of_gain':float(g.reserve_gain.sum()),'paid_part_of_gain':float(g.paid_gain.sum())})
        assert math.isclose(float(g.cost_gain.sum()),float(relevant.cost_term.sum()),rel_tol=3e-12,abs_tol=1e-8)
        for peril,pc in g.groupby('peril'):
            perils.append({'year':int(year),'NB':int(nb),'peril':str(peril),'claims':len(pc),'T0':float(pc.net.sum()),'reserve':float(pc.reserve.sum()),'cost_gain_term':float(pc.cost_gain.sum())})
    nb24=t[t.year.eq(2024)&t.new_business].copy();positive=nb24[nb24.y.gt(0)];count=max(1,math.ceil(.01*len(positive)));top=positive.sort_values(['y','row_id'],ascending=[False,True]).head(count)
    tail={'positive_periods_NB2024':len(positive),'top1pct_positive_rows':count,'top_T0_share':safe_ratio(top.y.sum(),nb24.y.sum()),'top_gain':float(top.loss_gain.sum()),'rest_gain':float(nb24.loss_gain.sum()-top.loss_gain.sum()),
        'zero_periods':int(nb24.y.eq(0).sum()),'zero_period_gain':float(nb24.loc[nb24.y.eq(0),'loss_gain'].sum()),'positive_period_gain':float(nb24.loc[nb24.y.gt(0),'loss_gain'].sum())}
    groups=a.groups(nb24);bygroup=nb24.assign(diagnostic_group=groups).groupby('diagnostic_group').loss_gain.sum();tail['positive_gain_groups']=int(bygroup.gt(0).sum());tail['negative_gain_groups']=int(bygroup.lt(0).sum())
    folds=pd.read_parquet(PARTITIONS,columns=['row_id','fold']).set_index('row_id')['fold'];nb24['saved_fold']=nb24.row_id.map(folds);assert nb24.saved_fold.notna().all()
    fold_results=[{'fold':int(f),**describe(g)} for f,g in nb24.groupby('saved_fold')]
    future=pd.read_parquet(R1OUT/'production_quotes.parquet',columns=['row_id','line','new_business','exposure']);future=future[future.line.eq('buildings')&future.new_business]
    future['exposure_band']=np.where(future.exposure<.5,'short_<.5',np.where(future.exposure<.9,'medium_.5_.9','long_>=.9'))
    support2025=[{'band':str(b),'rows':len(g),'row_share':len(g)/len(future),'exposure':float(g.exposure.sum()),'exposure_share':float(g.exposure.sum()/future.exposure.sum())} for b,g in future.groupby('exposure_band')]
    stages=[];targetorder=pd.read_parquet(TRIAL/'predictions2024.parquet',columns=['row_id']);selection=targetorder.row_id.isin(nb24.row_id).to_numpy();ordered=targetorder.row_id[selection]
    nbindexed=nb24.set_index('row_id').loc[ordered];old=nbindexed.R1.to_numpy();new=nbindexed.candidate.to_numpy()
    for i,item in enumerate(w.read(ACTIVE/'scenario_results.json')['scenarios']):
        ys=np.load(ACTIVE/'scenarios'/f'{i:02d}.npz')['y'][selection];den=a.null_loss(ys);gain=float(math.fsum((a.loss(ys,old)-a.loss(ys,new)).tolist()))
        stages.append({'scenario':item['scenario'],'delta_D2_buildings_NB':safe_ratio(gain,den),'observed_cost_sum':float(ys.sum())})
    t.to_parquet(OUT/'buildings_period_diagnostic.parquet',index=False);c.to_parquet(OUT/'buildings_claim_diagnostic.parquet',index=False)
    payload={'author':'Codex','utc':utc(),'cohorts':cohorts,'exposure_and_quarters':bands,'covariates_all_predeclared':covariates,'claim_timing':timings,'peril_cost_terms':perils,'tail_and_groups':tail,'saved_2024_NB_folds':fold_results,
        '2025_exposure_only':support2025,'fixed_stress_NB_buildings':stages,'fixed_price_ratio':h,'max_loss_identity_error':identity,
        'claims_accounting':{'assigned_buildings_claims':all_claims,'rejected_preserved_in_source':rejected,'accepted_claims':len(c),'period_T0_cents_exact':True},
        'method_limits':'A/E and gradients are descriptive at frozen prices, not fittedlevels. Pricepenalty left separate, no arbitrary peril attribution. Onevaluation and different loss/report maturity, no private superiority claim.',
        'new_native_or_closed_fits':0,'new_2025_quotes':0,'new_submissions':0,'code_sha256':w.sha(Path(__file__))}
    guard();dump(OUT/'results.json',payload)
    print(json.dumps({'diagnostic_complete':True,'cohorts':cohorts,'tail':tail,'saved_NBfolds':fold_results,'2025_exposure_only':support2025,
        'stress_NB_min':min(z['delta_D2_buildings_NB'] for z in stages),'stress_NB_max':max(z['delta_D2_buildings_NB'] for z in stages)}),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');arg=argparse.ArgumentParser();arg.add_argument('mode',choices=['freeze','analyze']);args=arg.parse_args();globals()[args.mode]()
