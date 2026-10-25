"""Flujo G4 solo sintético: C0, transformaciones, GLM y calibración anidada.

No tiene lectores ni un punto de entrada para datos del concurso. El prefijo y
la marca de fixture previenen conexiones accidentales; no prueban procedencia.
"""
from __future__ import annotations
import hashlib,json,warnings
from itertools import combinations
from numbers import Integral
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from . import c0_estricto2023 as c0

KEY=list(c0.KEY)
NUM=['x_new_business','x_log_sum_insured','x_property_age','x_flood_zone','x_accidental_damage_cover']
CAT=['x_property_type','x_region']
FEATURES=NUM+CAT
FIXTURE='G4-SYNTHETIC-v1'
PARAMS=dict(power=1.5,alpha=1.,fit_intercept=True,link='log',solver='lbfgs',max_iter=2000,tol=1e-6,warm_start=False)
WORK={'scope_attempts':0,'scope_fits':0,'C0_fits':0,'GLM_fits':0,'calibration_fits':0,'cache_hits':0}

def require(ok,message):
    if not bool(ok):raise ValueError(message)

def canonical(value):
    def normal(v):
        if isinstance(v,np.ndarray):return normal(v.tolist())
        if isinstance(v,np.generic):return normal(v.item())
        if isinstance(v,dict):return {str(k):normal(x) for k,x in sorted(v.items())}
        if isinstance(v,(list,tuple)):return [normal(x) for x in v]
        if isinstance(v,float) and np.isnan(v):return '__NaN__'
        return v
    return json.dumps(normal(value),sort_keys=True,separators=(',',':'),allow_nan=False)

def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()

def reset_work():
    for k in WORK:WORK[k]=0

def exclusions(folds):
    f=tuple(folds)
    require(len(f) in (1,2) and len(set(f))==len(f) and all(isinstance(x,Integral) and not isinstance(x,bool) and 0<=x<5 for x in f),'Exclusiones inválidas')
    return tuple(sorted(int(x) for x in f))

def metadata(periods,claims=None):
    meta=c0._metadata(periods)
    require(periods.fixture_id.eq(FIXTURE).all() and periods.row_id.str.startswith('SYN-G4-').all(),'Entrada no marcada como fixture sintético')
    require(meta.line.isin(['buildings','motor','contents']).all(),'Ramo ajeno al fixture')
    if claims is not None:
        require(claims.fixture_id.eq(FIXTURE).all() and claims.claim_id.str.startswith('SYN-G4-CL-').all(),'Notificaciones no sintéticas')
    return meta

def select_training(periods,claims,excluded):
    meta=metadata(periods,claims)
    rows,_=c0.select_scope(meta.to_dict('records'),excluded)
    keys=pd.MultiIndex.from_tuples([tuple(x[k] for k in KEY) for x in rows])
    p=periods.loc[pd.MultiIndex.from_frame(periods[KEY]).isin(keys)].sort_values(KEY).reset_index(drop=True)
    cc=claims.loc[pd.MultiIndex.from_frame(claims[KEY]).isin(keys)].sort_values([*KEY,'claim_id']).reset_index(drop=True)
    # No coste ni predictor protegido se interpreta antes de seleccionar.
    for x in NUM:p[x]=pd.to_numeric(p[x],errors='raise')
    require(not np.isinf(p[NUM].to_numpy(float)).any(),'Predictor infinito')
    for x in CAT:p[x]=p[x].astype('string').fillna('__MISSING__').astype(str)
    values=pd.to_numeric(cc.T0_cents,errors='raise')
    require(np.isfinite(values).all() and values.ge(0).all() and values.eq(np.floor(values)).all(),'Coste no canónico')
    cc=cc.copy();cc['T0_cents']=values
    require(cc.included_in_T0.eq(True).all(),'Siniestro no incluido')
    yy=cc.groupby(KEY).T0_cents.sum().rename('target_cents').reset_index()
    p=p.merge(yy,on=KEY,how='left',validate='one_to_one');p['T0']=p.target_cents.fillna(0).to_numpy(float)/100
    return p,cc

def preprocessor_state(transformer):
    numeric=transformer.named_transformers_['num'];encoder=transformer.named_transformers_['cat']
    return {'median':numeric.named_steps['median'].statistics_,
        'mean':numeric.named_steps['scale'].mean_,'variance':numeric.named_steps['scale'].var_,
        'scale':numeric.named_steps['scale'].scale_,'categories':encoder.categories_,
        'infrequent':encoder.infrequent_categories_,'drop_indices':encoder.drop_idx_,
        'feature_names':transformer.get_feature_names_out().tolist()}

def live_state(bundle):
    return {'contract':bundle['contract'],'C0':bundle['C0'],
        'preprocessor':preprocessor_state(bundle['transformer']),
        'GLM':{'params':bundle['model'].get_params(),'coef':bundle['model'].coef_,
               'intercept':bundle['model'].intercept_,'iterations':bundle['model'].n_iter_}}

def fit_scope(periods,claims,excluded_folds,source_versions,cache=None):
    WORK['scope_attempts']+=1;require(WORK['scope_attempts']<=120,'Presupuesto sintético de ámbitos agotado')
    excluded=exclusions(excluded_folds);p,cc=select_training(periods,claims,excluded)
    payload={'periods':p[KEY+FEATURES+['T0','period_start','period_end','exposure']].astype(object).where(p[KEY+FEATURES+['T0','period_start','period_end','exposure']].notna(),None).to_dict('records'),
             'claims':[[*[str(row[k]) for k in KEY],str(row.claim_id),str(row.peril),
                        pd.Timestamp(row.loss_date).isoformat(),pd.Timestamp(row.report_date).isoformat(),int(row.T0_cents)]
                       for _,row in cc.iterrows()]}
    # Fechas y valores se normalizan para una clave de contenido solo de ajuste.
    payload['periods']=[{k:(v.isoformat() if hasattr(v,'isoformat') else v) for k,v in x.items()} for x in payload['periods']]
    request_key=digest({'excluded':excluded,'sources':source_versions,'training':payload})
    if cache is not None and request_key in cache:
        hit=cache[request_key];require(hit['artifact_sha256']==digest(live_state(hit)),'Caché de flujo modificada')
        WORK['cache_hits']+=1;return hit
    cobj=c0.fit_c0_2023(periods,claims,excluded_folds=excluded,source_versions=source_versions);WORK['C0_fits']+=1
    e=c0.apply_c0_2023(p,cobj,excluded_folds=excluded).C0.to_numpy(float)
    tr=ColumnTransformer([('num',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler())]),NUM),
                          ('cat',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,max_categories=40,sparse_output=True),CAT)],sparse_threshold=1.)
    X=tr.fit_transform(p[FEATURES]);y=p.T0.to_numpy(float)/e;w=np.sqrt(e)
    model=TweedieRegressor(**PARAMS)
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always');model.fit(X,y,sample_weight=w)
    require(not any(issubclass(n.category,ConvergenceWarning) for n in notes) and model.n_iter_<PARAMS['max_iter'],'GLM sintético no convergió')
    rate=model.predict(X);g=w*(np.sqrt(rate)-y/np.sqrt(rate))/w.sum()
    score=np.r_[np.asarray(X.T@g).ravel()+model.alpha*model.coef_,g.sum()]
    require(np.max(np.abs(score))<=1e-4,'Gradiente penalizado fuera del criterio congelado')
    bundle={'contract':{'fixture':FIXTURE,'excluded_folds':list(excluded),'training_keys':p[KEY].to_dict('records'),
        'training_content_sha256':request_key,'features':FEATURES,'source_versions':source_versions},'C0':cobj,'transformer':tr,'model':model}
    bundle['artifact_sha256']=digest(live_state(bundle))
    WORK['scope_fits']+=1;WORK['GLM_fits']+=1
    if cache is not None:cache[request_key]=bundle
    return bundle

def predict_scope(periods,bundle,excluded_folds):
    excluded=exclusions(excluded_folds);metadata(periods)
    require(bundle['contract']['excluded_folds']==list(excluded),'Modelo/caché de ámbito exterior reutilizado como interior')
    require(bundle['artifact_sha256']==digest(live_state(bundle)),'Objeto de flujo modificado')
    require(periods.line.eq('buildings').all(),'Aplicación de GLM solo edificios')
    p=periods.sort_values(KEY).copy()
    for x in NUM:p[x]=pd.to_numeric(p[x],errors='raise')
    for x in CAT:p[x]=p[x].astype('string').fillna('__MISSING__').astype(str)
    X=bundle['transformer'].transform(p[FEATURES]);rate=bundle['model'].predict(X)
    require(np.isfinite(rate).all() and (rate>0).all(),'Tasas no positivas/finitas')
    e=c0.apply_c0_2023(p,bundle['C0'],excluded_folds=excluded).C0.to_numpy(float)
    out=p[KEY+['fold']].copy();out['rate']=rate;out['C0']=e
    return out

def deviance(y,mu):
    y=np.asarray(y,float);mu=np.asarray(mu,float)
    require(np.isfinite(y).all() and (y>=0).all() and np.isfinite(mu).all() and (mu>0).all(),'Argumentos de devianza inválidos')
    # Identidad equivalente que evita cancelación cerca de y==mu.
    return 4*np.square(np.sqrt(y)-np.sqrt(mu))/np.sqrt(mu)

def fit_calibrator(frame,mode):
    WORK['calibration_fits']+=1;require(WORK['calibration_fits']<=80,'Presupuesto de calibradores sintéticos agotado')
    require(mode in ['L','S'],'Modo de calibración inválido')
    y=frame.T0.to_numpy(float);e=frame.C0.to_numpy(float);r=frame.rate.to_numpy(float)
    require(len(y)>0 and np.isfinite(y).all() and (y>=0).all() and y.sum()>0,'Objetivo de calibración nulo/inválido')
    require(np.isfinite(e).all() and (e>0).all() and np.isfinite(r).all() and (r>0).all(),'C0/tasa de calibración inválida')
    m=float(np.sum(e*np.log(r))/e.sum());z=np.log(r)-m
    require(np.ptp(z)>1e-10,'Pendiente no identificable con tasas empatadas')
    def profile(b):
        h=e*np.exp(m+b*z);a=float(np.log(np.sum(y/np.sqrt(h)))-np.log(np.sum(np.sqrt(h))))
        mu=np.exp(a)*h;return float(np.sum(deviance(y,mu))),a,mu
    if mode=='L':b=1.
    else:
        opt=minimize_scalar(lambda b:profile(b)[0],bounds=(0.,1.),method='bounded',options={'xatol':1e-10,'maxiter':500})
        require(opt.success,'Perfil de calibración no convergió')
        b=min([0.,float(opt.x),1.],key=lambda b:profile(b)[0])
    loss,a,mu=profile(b);g=np.sqrt(mu)-y/np.sqrt(mu)
    ga=float(g.sum());gb=float(g@z)
    projected=gb if mode=='L' else (min(gb,0.) if b==0 else max(gb,0.) if b==1 else gb)
    norm=max(1.,float(np.sum(np.sqrt(mu)+y/np.sqrt(mu))))
    residual=abs(ga)/norm if mode=='L' else max(abs(ga),abs(projected))/norm
    require(residual<=1e-6,'KKT perfilado fuera del criterio congelado')
    return {'mode':mode,'a':a,'b':b,'m':m,'loss':loss,'normalized_KKT':residual,'rows':len(frame),
            'training_keys':frame[KEY].to_dict('records'),'fit_input_sha256':digest(frame[KEY+['T0','C0','rate']].to_dict('records'))}

def apply_calibrator(predictions,calibrator):
    e=predictions.C0.to_numpy(float);r=predictions.rate.to_numpy(float)
    mu=e*np.exp(calibrator['a']+calibrator['m']+calibrator['b']*(np.log(r)-calibrator['m']))
    require(np.isfinite(mu).all() and (mu>0).all(),'Predicción calibrada inválida')
    return mu

def fit_outer(periods,claims,outer,source_versions,cache=None):
    exclusions([outer]);metadata(periods,claims)
    cache={} if cache is None else cache
    inner=[];ancestors={}
    for fold in range(5):
        if fold==outer:continue
        obj=fit_scope(periods,claims,[outer,fold],source_versions,cache)
        query=periods.loc[periods.line.eq('buildings')&periods.fold.eq(fold)]
        pred=predict_scope(query,obj,[outer,fold])
        p,_=select_training(periods,claims,[outer])
        pred=pred.merge(p[KEY+['T0']],on=KEY,validate='one_to_one')
        inner.append(pred);ancestors[str(fold)]=obj
    inner=pd.concat(inner,ignore_index=True).sort_values(KEY).reset_index(drop=True)
    require(not inner.fold.eq(outer).any() and not inner.duplicated(KEY).any(),'OOF interior inválida')
    base=fit_scope(periods,claims,[outer],source_versions,cache)
    cal={mode:fit_calibrator(inner,mode) for mode in ['L','S']}
    state={'outer':outer,'ancestors':{k:live_state(v) for k,v in ancestors.items()},'base':live_state(base),'calibrators':cal,'inner_keys':inner[KEY+['fold']].to_dict('records')}
    return {'outer':outer,'inner':ancestors,'base':base,'calibrators':cal,'inner_keys':state['inner_keys'],'state':state,'artifact_sha256':digest(state)}

def live_outer_state(bundle):
    return {'outer':bundle['outer'],'ancestors':{k:live_state(v) for k,v in bundle['inner'].items()},
        'base':live_state(bundle['base']),'calibrators':bundle['calibrators'],'inner_keys':bundle['inner_keys']}

def apply_outer(periods,bundle):
    outer=bundle['outer'];metadata(periods)
    require(bundle['artifact_sha256']==digest(live_outer_state(bundle)),'Objeto exterior/calibrador modificado')
    require(periods.fold.eq(outer).all(),'Consulta de otro fold')
    p=periods.loc[periods.line.eq('buildings')];pred=predict_scope(p,bundle['base'],[outer])
    pred['raw']=pred.C0*pred.rate
    for mode in ['L','S']:pred[mode]=apply_calibrator(pred,bundle['calibrators'][mode])
    # Motor/contenidos son únicamente controles sintéticos de paso directo.
    other=periods.loc[~periods.line.eq('buildings'),KEY+['fold','synthetic_base_prediction']].copy()
    for col in ['raw','L','S']:other[col]=other.synthetic_base_prediction.to_numpy(float)
    return pd.concat([pred[KEY+['fold','raw','L','S']],other[KEY+['fold','raw','L','S']]],ignore_index=True).sort_values(KEY).reset_index(drop=True)

def fixture(seed=20261024):
    rng=np.random.default_rng(seed);periods=[];claims=[]
    for fold in range(5):
        block=[]
        for j in range(80):
            month=[1,3,6,9][j%4];start=f'2023-{month:02d}-01'
            logcap=float(np.log(80000+5000*j)+.02*fold)
            row={'fixture_id':FIXTURE,'market':'emerging','line':'buildings','row_id':f'SYN-G4-B-{fold}-{j}',
                'year':2023,'is_test':False,'fold':fold,'group_id':f'SYN-G4-G-{fold}-{j}',
                'customer_id':f'SYN-G4-C-{fold}-{j}','address_id':f'SYN-G4-A-{fold}-{j}',
                'period_start':start,'period_end':'2023-12-31','exposure':(pd.Timestamp('2023-12-31')-pd.Timestamp(start)).days/365+1/365,
                'x_new_business':float(j%3==0),'x_log_sum_insured':np.nan if j%17==0 else logcap,
                'x_property_age':np.nan if j%19==0 else float(j%65),'x_flood_zone':float(j%5+1),
                'x_accidental_damage_cover':float(j%2),'x_property_type':['detached','semi_detached','terraced','flat'][j%4],
                'x_region':['SYN-E-A','SYN-E-B'][j%2],'synthetic_base_prediction':100.}
            periods.append(row);block.append(row)
        for p,peril in enumerate(c0.PERILS):
            for j in range(12):
                row=block[p*4 if j==0 else (p*9+j*7)%80]
                loss=pd.Timestamp(row['period_start'])+pd.Timedelta(days=2+j%12)
                delay=600 if j==0 else 25*j+4*p
                risk=np.exp(.6*row['x_new_business']+.25*row['x_accidental_damage_cover']+.08*row['x_flood_zone'])
                amount=int(round((100+p*90+j*12)*risk*rng.uniform(.8,1.2)*100))
                claims.append({'fixture_id':FIXTURE,'market':'emerging','line':'buildings','row_id':row['row_id'],
                    'claim_id':f'SYN-G4-CL-{fold}-{p}-{j}','year':2023,'is_test':False,'fold':fold,
                    'included_in_T0':True,'loss_date':loss,'report_date':loss+pd.Timedelta(days=delay),'T0_cents':amount,'peril':peril})
        for line in ['motor','contents']:
            for j in range(4):
                row=block[j].copy();row['line']=line;row['synthetic_base_prediction']=123.456+fold+j
                periods.append(row)
    return pd.DataFrame(periods),pd.DataFrame(claims)
