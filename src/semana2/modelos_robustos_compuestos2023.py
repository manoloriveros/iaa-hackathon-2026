"""Descomposición estándar y corrección pequeña de árboles sobre B20."""
from pathlib import Path
import joblib
import numpy as np,pandas as pd
import lightgbm as lgb
from sklearn.linear_model import PoissonRegressor,GammaRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from . import modelos_robustos2023 as base
FEATURES,KEY=base.FEATURES,base.KEY
guard,features,metrics,unit_deviance=base.guard,base.features,base.metrics,base.unit_deviance
ROOT=Path('C:/dev/Hakaton');REPO=ROOT/'Hackaton/Repositorio_IAA2026'
CORE={
 'motor':{'numeric':['x_new_business','x_ncb_years','x_vehicle_age','x_vehicle_value_group'],'categorical':['x_driver_age_band','x_region','x_cover_type']},
 'buildings':{'numeric':['x_new_business','x_log_sum_insured','x_property_age','x_flood_zone','x_accidental_damage_cover'],'categorical':['x_property_type','x_region']},
 'contents':{'numeric':['x_new_business','x_log_sum_insured','x_bedrooms','x_high_value_items','x_accidental_damage_cover'],'categorical':['x_property_type','x_region']}}


def direct_rate(b,f):
    return b['estimator'].predict(b['transformer'].transform(f[b['columns']]))


def lgb_frame(f,cols,levels):
    x=f[cols].copy()
    for c,v in levels.items():x[c]=pd.Categorical(x[c].astype(str),categories=v)
    return x


def predict(bundle,frame,training=True):
    guard(frame,bundle['line'],training=training);f=features(frame,bundle['line'])
    if bundle['family']=='FrequencySeverity':
        x=bundle['transformer'].transform(f[bundle['columns']])
        rate=bundle['frequency'].predict(x)*bundle['severity'].predict(x)
    elif bundle['family']=='GLMResidualTrees':
        a=direct_rate(bundle['base'],f)
        correction=bundle['estimator'].predict(lgb_frame(f,bundle['columns'],bundle['categories']),raw_score=True)
        rate=a*np.exp(correction)
    else:return base.predict(bundle,frame,training)
    base.require(np.isfinite(rate).all() and (rate>0).all(),'Tasa compuesta inválida')
    return rate


def fit(frame,line,held,recipe):
    import warnings
    from sklearn.exceptions import ConvergenceWarning
    guard(frame,line,held);f=features(frame,line)
    if recipe['shape'] not in ['frequency_severity','residual_boost']:return base.fit(frame,line,held,recipe)
    e=f['e_cost_mix_1.0'].to_numpy(float);base.require(np.isfinite(e).all() and (e>0).all(),'C0inválido')
    if recipe['shape']=='frequency_severity':
        block=CORE[line];cols=block['numeric']+block['categorical']
        tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',base.QuantileClipper()),('scale',StandardScaler())]),block['numeric']),
            ('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),block['categorical'])],sparse_threshold=1.)
        x=tr.fit_transform(f[cols]);n=f.n_positive.to_numpy(float);y=f.T0.to_numpy(float)
        base.require(np.all(n>=0) and np.array_equal(n,n.round()) and np.array_equal(n>0,y>0),'Recuento/importe inconsistente')
        pos=n>0;base.require(pos.sum()>=100,'Soporte mínimo de marca no satisfecho')
        freq=PoissonRegressor(alpha=.01,fit_intercept=True,solver='lbfgs',max_iter=3000,tol=1e-7)
        sev=GammaRegressor(alpha=.1,fit_intercept=True,solver='lbfgs',max_iter=3000,tol=1e-7)
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter('always');freq.fit(x,n/e,sample_weight=e);sev.fit(x[pos],y[pos]/n[pos],sample_weight=n[pos])
        base.require(not any(issubclass(z.category,ConvergenceWarning) for z in seen),'Compuesto no convergió')
        checks=[]
        for est,xx,yy,ww,family in [(freq,x,n/e,e,'Poisson'),(sev,x[pos],y[pos]/n[pos],n[pos],'Gamma')]:
            mu=est.predict(xx);g=ww*((mu-yy) if family=='Poisson' else (1-yy/mu))/ww.sum()
            score=np.r_[np.asarray(xx.T@g).ravel()+est.alpha*est.coef_,g.sum()]
            base.require(np.abs(score).max()<=1e-4,'Gradiente compuesto inválido')
            checks.append({'family':family,'params':est.get_params(),'max_abs_gradient':float(np.abs(score).max()),'n_iter':int(est.n_iter_)})
        bundle={'model_id':recipe['id'],'line':line,'family':'FrequencySeverity','held_fold':held,'columns':cols,'transformer':tr,'frequency':freq,'severity':sev}
        return bundle,{'line':line,'fold':held,'fit_rows':len(f),'positive_rows':int(pos.sum()),'price_estimator_fits':2,'technical':checks,
            'interpretation':'Positive cost-count proxy with existing COST observation exposure, not an independently identified ultimate claim-frequency curve; predictive comparison only.'}
    path=REPO/f'privado/semana2/desarrollo2023/ridge20_20261024_v1/models/{line}_fold{held}/bundle.joblib'
    if recipe.get('synthetic') is True:
        base.require(f.row_id.str.startswith('s').all(),'Sonda sintética con filas reales')
        parent=recipe['_base_bundle'];source='synthetic_parent'
    else:
        parent=joblib.load(path);source=str(path.relative_to(ROOT)).replace('\\','/')
    before=joblib.hash(parent);a=direct_rate(parent,f)
    cols=FEATURES[line]['numeric']+FEATURES[line]['categorical'];levels={c:sorted(f[c].astype(str).unique().tolist()) for c in FEATURES[line]['categorical']}
    x=lgb_frame(f,cols,levels)
    est=lgb.LGBMRegressor(objective='tweedie',tweedie_variance_power=1.5,n_estimators=100,learning_rate=.025,
        num_leaves=4,max_depth=2,min_child_samples=1000,reg_lambda=100.,reg_alpha=10.,max_bin=63,
        min_data_per_group=100,cat_smooth=50.,subsample=1.,colsample_bytree=1.,
        deterministic=True,force_col_wise=True,random_state=2026102503,n_jobs=2,verbosity=-1)
    est.fit(x,f.T0.to_numpy()/e,sample_weight=np.sqrt(e),init_score=np.log(a),categorical_feature=list(levels))
    base.require(joblib.hash(parent)==before,'B20 alterado')
    bundle={'model_id':recipe['id'],'line':line,'family':'GLMResidualTrees','held_fold':held,'columns':cols,'base':parent,'estimator':est,'categories':levels}
    return bundle,{'line':line,'fold':held,'fit_rows':len(f),'price_estimator_fits':1,'base_reused':source,'base_state_unchanged':True,
        'params':est.get_params(),'trees':est.booster_.num_trees(),'no_validation_or_stopping':True,'init_score_semantics':'log(base rate), prediction adds tree raw score to base log-rate'}
