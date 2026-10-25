"""GLM estándar de despliegue: todo2023 -> cotizaciones2025, jamás2024.

Es un ámbito final propio, no un fold renombrado. C0 se aprende de ocurrencias
2023 con seguimiento al corte histórico; el precio futuro usa exposición nominal.
"""
from pathlib import Path
import hashlib
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from . import c0_estricto2023 as kernel, entradas_g4_2023 as ingress
from .preparar_base import reconcile_exposure

KEY = ingress.KEY
LINES = ['motor', 'buildings', 'contents']
PERILS = {'motor': ['bodily_injury','glass_hail','own_damage','theft','third_party_prop'],
          'buildings': ['accidental_damage','escape_of_water','fire','flood','storm','subsidence'],
          'contents': ['accidental_damage','escape_of_water','flood','theft']}
CAP_LIMIT = {'buildings':10000000., 'contents':1000000.}
SCOPE = 'deployment_all_emerging2023_for2025_not_validation'


def require(ok, message):
    if not bool(ok):
        raise ValueError(message)


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def assert_train(frame, line):
    require(len(frame)>0 and frame.year.eq(2023).all() and frame.line.eq(line).all()
            and frame.market.eq('emerging').all() and frame.is_test.eq(False).all(), 'Solo entrenamiento2023 del ramo')
    require(not frame.duplicated(KEY).any(), 'Claves de entrenamiento repetidas')
    require(frame.x_new_business.isin([0.,1.]).all(), 'Nuevo negocio inválido')
    require(np.isfinite(frame.exposure).all() and frame.exposure.gt(0).all(), 'Exposición inválida')
    dates = pd.to_datetime(frame.period_start),pd.to_datetime(frame.period_end)
    require(dates[0].dt.year.eq(2023).all() and dates[1].dt.year.eq(2023).all(), 'Fechas de cohorte ajena')


def assemble_training(static, coverage, claims, line, block):
    static=static.sort_values(KEY).reset_index(drop=True)
    coverage=coverage.sort_values(KEY).reset_index(drop=True)
    require(static[KEY].equals(coverage[KEY]), 'Fuentes de entrenamiento no alineadas')
    for field in ['policy_id','customer_id','address_id','group_id','fold','year','is_test','exposure','x_new_business']:
        require(static[field].eq(coverage[field]).all(), 'Linaje discrepante: '+field)
    for field in ['period_start','period_end']:
        require(pd.to_datetime(static[field]).eq(pd.to_datetime(coverage[field])).all(), 'Fechas discrepantes')
    f=static.copy()
    cover='cover_type' if line=='motor' else 'accidental_damage_cover'
    if 'x_'+cover in static:
        require(static['x_'+cover].eq(coverage[cover]).all(), 'Cobertura heredada discrepante')
    f['x_'+cover]=coverage[cover].to_numpy()
    cols=ingress.META+['period_start','period_end','exposure','T0']+[x for x in block['all'] if x!='x_log_sum_insured']
    f=f[list(dict.fromkeys(cols))].copy()
    assert_train(f,line)
    require(np.isfinite(f.T0).all() and f.T0.ge(0).all(), 'T0 inválido')
    c=claims.loc[claims.included_in_T0.eq(True)].copy()
    require(c.year.eq(2023).all() and c.line.eq(line).all(), 'Notificación ajena a2023')
    require(not c.duplicated(['market','line','claim_id']).any(), 'Siniestro duplicado')
    j=c.merge(f[KEY+['fold','group_id','policy_id','period_start','period_end']],on=KEY,validate='many_to_one',suffixes=('','_p'),how='left',indicator=True)
    require(j['_merge'].eq('both').all(), 'Siniestro sin periodo')
    for name in ['fold','group_id','policy_id']:
        require(j[name].eq(j[name+'_p']).all(), 'Siniestro con linaje distinto')
    loss,report=pd.to_datetime(j.loss_date),pd.to_datetime(j.report_date)
    require(loss.dt.year.eq(2023).all() and loss.ge(pd.to_datetime(j.period_start)).all()
            and loss.le(pd.to_datetime(j.period_end)).all() and report.ge(loss).all()
            and report.le(pd.Timestamp(kernel.VALUATION)).all(), 'Fechas de siniestro no admisibles')
    require(set(c.peril)==set(PERILS[line]), 'Perils distintos del contrato')
    require(np.isfinite(c.T0_cents).all() and c.T0_cents.ge(0).all()
            and c.T0_cents.eq(np.floor(c.T0_cents)).all(), 'Centavos inválidos')
    expected=c.groupby(KEY).T0_cents.sum().rename('claim_cents').reset_index()
    reconciled=f[KEY+['T0']].merge(expected,on=KEY,how='left',validate='one_to_one')
    cents=np.rint(reconciled.T0.to_numpy()*100)
    require(np.max(np.abs(cents-reconciled.T0.to_numpy()*100),initial=0)<=1e-6
            and np.array_equal(cents,reconciled.claim_cents.fillna(0).to_numpy()), 'T0 y siniestros no concilian')
    return f,c.sort_values(KEY+['claim_id']).reset_index(drop=True)


def fit_capital_final(periods,raw,line,versions):
    assert_train(periods,line)
    limit=CAP_LIMIT[line]
    raw=raw.sort_values('row_id').reset_index(drop=True)
    p=periods.sort_values('row_id').reset_index(drop=True)
    require(p.row_id.equals(raw.row_id) and not raw.row_id.duplicated().any(), 'Capital raw no alineado')
    for name in ['period_start','period_end']:
        require(pd.to_datetime(raw[name]).eq(pd.to_datetime(p[name])).all(), 'Fechas raw distintas')
    cap=raw.sum_insured.to_numpy(float);prem=raw.written_premium.to_numpy(float)
    normal=np.isfinite(cap)&(cap>0)&(cap<=limit)
    require(normal.any(), 'Sin población normal de capital')
    ratio=1000*prem[normal]/cap[normal]
    require(np.isfinite(ratio).all() and (ratio>0).all(), 'Prima por mil normal inválida')
    population=p.loc[normal,KEY].copy()
    population['capital']=cap[normal];population['premium_audit_only']=prem[normal];population['ppm']=ratio
    obj={'recipe':'CAPS2-01-FINAL-v1','scope':SCOPE,'line':line,'year':2023,'excluded_folds':[],
        'threshold':limit,'ppm_min':float(ratio.min()),'ppm_max':float(ratio.max()),'normal_rows':int(normal.sum()),
        'population_sha256':digest(population.to_dict('records')),'source_versions':versions}
    obj['sha256']=digest(obj)
    return obj,population


def apply_capital(frame,raw,artifact):
    require(artifact['sha256']==digest({k:v for k,v in artifact.items() if k!='sha256'}), 'Capital modificado')
    require(artifact['scope']==SCOPE and artifact['year']==2023 and artifact['excluded_folds']==[], 'Capital de ámbito ajeno')
    require(artifact['line'] in CAP_LIMIT and artifact['threshold']==CAP_LIMIT[artifact['line']], 'Ramo/umbral de capital ajeno')
    require('line' in frame and frame.line.eq(artifact['line']).all(), 'Capital de otro ramo')
    require('year' in frame and 'is_test' in frame and
            ((frame.year.eq(2023)&frame.is_test.eq(False)) | (frame.year.eq(2025)&frame.is_test.eq(True))).all(),
            'Aplicación de capital solo ajuste2023 o cotización2025')
    f=frame.merge(raw[['row_id','sum_insured','written_premium']],on='row_id',validate='one_to_one',how='left')
    cap=f.sum_insured.to_numpy(float);prem=f.written_premium.to_numpy(float)
    valid=np.isfinite(cap)&(cap>0);suspect=valid&(cap>artifact['threshold'])
    ratio=np.divide(1000*prem,cap,out=np.full(len(cap),np.nan),where=valid)
    accepted=suspect&(ratio<artifact['ppm_min'])&(1000*ratio>=artifact['ppm_min'])&(1000*ratio<=artifact['ppm_max'])
    cleaned=np.where(valid,np.where(suspect,np.where(accepted,cap/1000,np.nan),cap),np.nan)
    out=frame.copy();out['x_log_sum_insured']=np.log(cleaned)
    return out,{'suspect':int(suspect.sum()),'corrected':int(accepted.sum()),'missing':int(np.isnan(cleaned).sum())}


def fit_c0_final(periods,claims,line,versions):
    assert_train(periods,line)
    require(set(claims.peril)==set(PERILS[line]), 'Perils no completos')
    curves,frequencies,levels={},{},{}
    for peril in PERILS[line]:
        cc=claims.loc[claims.peril.eq(peril)]
        loss=pd.to_datetime(cc.loss_date);report=pd.to_datetime(cc.report_date)
        curve,_=kernel._reporting_base((report-loss).dt.days.to_numpy(),
            (pd.Timestamp(kernel.VALUATION)-loss).dt.days.to_numpy(),cc.T0_cents.to_numpy(float)/100)
        effective=float(np.sum(periods.exposure.to_numpy()*kernel._completion(periods,curve,'count')))
        require(np.isfinite(effective) and effective>0, 'Exposición C0 inválida')
        frequency=len(cc)/effective
        curves[peril]=curve
        frequencies[peril]={'notifications':len(cc),'effective_count_exposure':effective,'frequency':frequency}
        levels[peril]=frequency*curve['mean_net_mark']
    shares={k:levels[k]/sum(levels.values()) for k in levels}
    payload={'periods':[[*[str(r[k]) for k in KEY],pd.Timestamp(r.period_start).isoformat(),pd.Timestamp(r.period_end).isoformat(),float(r.exposure)] for _,r in periods.iterrows()],
        'claims':[[*[str(r[k]) for k in KEY],str(r.claim_id),str(r.peril),pd.Timestamp(r.loss_date).isoformat(),pd.Timestamp(r.report_date).isoformat(),int(r.T0_cents)] for _,r in claims.iterrows()]}
    obj={'recipe':'C0-ALL2023-FINAL-rho1-tail0-v1','scope':SCOPE,'line':line,'year':2023,'excluded_folds':[],
        'valuation':kernel.VALUATION,'reserve_factor':1.,'tail_mass':0.,'source_versions':versions,
        'training_content_sha256':digest(payload),'training_rows':len(periods),'curves':curves,
        'frequencies':frequencies,'cost_shares':shares,'reporting_fits':len(curves),
        'ultimate_limit':'Conditional on rho=1 and no unobserved tail mass; not independently identified ultimate.'}
    obj['sha256']=digest(obj)
    return obj


def training_c0(periods,obj):
    require(obj['sha256']==digest({k:v for k,v in obj.items() if k!='sha256'}) and obj['scope']==SCOPE, 'C0 ajeno/modificado')
    assert_train(periods,obj['line'])
    q=np.zeros(len(periods))
    errors=[]
    for peril,curve in obj['curves'].items():
        values=kernel._completion(periods,curve,'cost')
        q+=obj['cost_shares'][peril]*values
        for i in np.unique(np.linspace(0,len(periods)-1,min(8,len(periods)),dtype=int)):
            r=periods.iloc[i]
            ages=(pd.Timestamp(kernel.VALUATION)-pd.date_range(r.period_start,r.period_end)).days.to_numpy()
            positions=np.searchsorted(curve['delay_days'],ages,side='right')-1
            brute=np.where(positions>=0,np.asarray(curve['cost_cdf'])[np.maximum(positions,0)],0.).mean()
            errors.append(abs(float(brute)-float(values[i])))
    require(max(errors,default=0)<=1e-12, 'Integración C0 no coincide con calendario directo')
    e=periods.exposure.to_numpy(float)*q
    require(np.isfinite(e).all() and (e>0).all() and (q<=1+1e-12).all(), 'C0 inválido')
    return e,{'direct_calendar_checks':len(errors),'max_abs_calendar_error':max(errors,default=0),
              'minimum_completion':float(q.min()),'maximum_completion':float(q.max())}


def fit_glm_final(periods,e,recipe,line,capital,c0_object):
    assert_train(periods,line)
    require(c0_object['scope']==SCOPE and c0_object['line']==line and c0_object['excluded_folds']==[], 'C0 de ámbito ajeno')
    require(len(e)==len(periods) and np.isfinite(e).all() and (e>0).all(), 'Exposición C0 inválida para GLM')
    if line in CAP_LIMIT:
        require(capital['scope']==SCOPE and capital['line']==line and capital['excluded_folds']==[], 'Capital de otro ámbito')
    block=recipe['features_by_line'][line]
    cols=block['all']
    require(len(cols)==7 and not any(c in cols for c in ['T0','written_premium','exposure']), 'Predictores inválidos')
    tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler())]),block['numeric']),
        ('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,max_categories=40,sparse_output=True),block['categorical'])],sparse_threshold=1.)
    X=tr.fit_transform(periods[cols])
    y=periods.T0.to_numpy(float)/e;w=np.sqrt(e)
    estimator=TweedieRegressor(**recipe['params'])
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always');estimator.fit(X,y,sample_weight=w)
    require(not any(issubclass(n.category,ConvergenceWarning) for n in notes) and estimator.n_iter_<recipe['params']['max_iter'], 'GLM no convergió')
    rate=estimator.predict(X)
    g=w*(np.sqrt(rate)-y/np.sqrt(rate))/w.sum()
    gradient=np.r_[np.asarray(X.T@g).ravel()+estimator.alpha*estimator.coef_,g.sum()]
    require(np.abs(gradient).max()<=1e-4, 'Gradiente penalizado fuera de criterio')
    manual=np.exp(np.asarray(X@estimator.coef_).ravel()+estimator.intercept_)
    require(np.allclose(rate,manual,rtol=1e-12,atol=1e-9), 'Predicción manual no coincide')
    observed=e*rate
    d1=4*np.square(np.sqrt(periods.T0.to_numpy())-np.sqrt(observed))/np.sqrt(observed)
    d2=np.sqrt(e)*4*np.square(np.sqrt(y)-np.sqrt(rate))/np.sqrt(rate)
    require(np.allclose(d1,d2,rtol=1e-12,atol=1e-9), 'Identidad de pesos Tweedie no coincide')
    bundle={'id':'G4-GLM2023-FINAL-v1','scope':SCOPE,'training_year':2023,'line':line,'recipe':recipe,
        'columns':cols,'transformer':tr,'estimator':estimator,'capital':capital,'C0':c0_object}
    receipt={'line':line,'fit_rows':len(periods),'params':estimator.get_params(),'iterations':int(estimator.n_iter_),
        'max_abs_penalized_gradient':float(np.abs(gradient).max()),'manual_prediction_max_abs_error':float(np.max(np.abs(rate-manual))),
        'weight_identity_max_abs_error':float(np.max(np.abs(d1-d2))),'warnings':[str(n.message) for n in notes],
        'fit_observed_total':float(periods.T0.sum()),'fit_prediction_total':float(observed.sum()),
        'scope_note':'Training diagnostics only,not validation or independent performance evidence.'}
    return bundle,receipt


def quote_features(raw,addresses,line,block,capital):
    f=reconcile_exposure(raw)
    require(pd.to_datetime(f.period_start).dt.year.eq(2025).all() and pd.to_datetime(f.period_end).dt.year.eq(2025).all(), 'Solo cotizaciones2025')
    require(not f.row_id.duplicated().any() and addresses.address_id.is_unique, 'Claves de cotizaciones/maestro repetidas')
    f=f.merge(addresses,on='address_id',how='left',validate='many_to_one',indicator=True)
    require(f['_merge'].eq('both').all(), 'Dirección sin maestro')
    f['market']='emerging';f['line']=line;f['year']=2025;f['is_test']=True
    out=f[KEY+['policy_id','customer_id','address_id','period_start','period_end','year','is_test','exposure']].copy()
    out['x_new_business']=pd.to_numeric(f.new_business)
    if line=='motor':
        for name in ['ncb_years','vehicle_age','vehicle_value_group','driver_age_band','cover_type','region']:
            out['x_'+name]=f[name].to_numpy()
        require(out.x_cover_type.isin(['comprehensive','third_party_fire_theft','third_party_only']).all(), 'Cobertura motor no prevista')
    else:
        age=2025-pd.to_numeric(f.year_built)
        out['x_property_age']=np.where(age>=0,age,np.nan)
        for name in ['accidental_damage_cover','property_type','region']:
            out['x_'+name]=f[name].to_numpy()
        for name in (['flood_zone'] if line=='buildings' else ['bedrooms','high_value_items']):
            out['x_'+name]=f[name].to_numpy()
        out,audit=apply_capital(out,raw,capital)
    require(out.x_new_business.isin([0.,1.]).all(), 'Nuevo negocio2025 inválido')
    for name in block['categorical']:
        out[name]=out[name].astype('string').fillna('__MISSING__')
    require(not np.isinf(out[block['numeric']].to_numpy(float)).any(), 'Predictor2025 infinito')
    exposure_audit=f.audit_exposure_rule.value_counts().to_dict()
    return out,{'exposure_rules':{str(k):int(v) for k,v in exposure_audit.items()},
        'capital':audit if line!='motor' else None,'raw_premium_not_predictor':True}


def predict_quotes(bundle,frame):
    require(bundle['scope']==SCOPE and bundle['training_year']==2023, 'Modelo de otro ámbito')
    require(frame.year.eq(2025).all() and frame.is_test.eq(True).all() and frame.line.eq(bundle['line']).all(), 'Consulta no2025')
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always')
        X=bundle['transformer'].transform(frame[bundle['columns']])
        rate=bundle['estimator'].predict(X)
    manual=np.exp(np.asarray(X@bundle['estimator'].coef_).ravel()+bundle['estimator'].intercept_)
    require(np.allclose(rate,manual,rtol=1e-12,atol=1e-9), 'Predicción2025 manual discrepante')
    price=frame.exposure.to_numpy(float)*rate
    require(np.isfinite(price).all() and (price>0).all(), 'Precio no finito o no positivo')
    out=frame[['row_id']].copy();out['prediction']=price
    return out,{'rows':len(out),'prediction_sum':float(price.sum()),'minimum':float(price.min()),'maximum':float(price.max()),
        'manual_rate_max_abs_error':float(np.max(np.abs(rate-manual))), 'warnings':[str(n.message) for n in notes],
        'future_observation_completion_applied':False,'quote_exposure':'Nominal reconciled exposure; conditional ultimate rate'}


def learned_state_digest(bundle):
    tr=bundle['transformer'];numeric=tr.named_transformers_['numeric'];cat=tr.named_transformers_['categorical']
    payload={'scope':bundle['scope'],'year':bundle['training_year'],'line':bundle['line'],
        'params':bundle['estimator'].get_params(),'coef':bundle['estimator'].coef_.tolist(),
        'intercept':float(bundle['estimator'].intercept_),
        'median':numeric.named_steps['median'].statistics_.tolist(),
        'mean':numeric.named_steps['scale'].mean_.tolist(),'variance':numeric.named_steps['scale'].var_.tolist(),
        'scale':numeric.named_steps['scale'].scale_.tolist(),'categories':[list(map(str,c)) for c in cat.categories_],
        'feature_names':tr.get_feature_names_out().tolist(),'capital':bundle['capital'],'C0':bundle['C0']}
    return digest(payload)
