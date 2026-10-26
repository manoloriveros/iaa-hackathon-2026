"""Interacciones transportadas de capacidad fija, base R27 por fold."""
from pathlib import Path
import numpy as np,pandas as pd,joblib,lightgbm as lgb
from . import modelos_robustos2023 as base
from . import modelo_transferencia2023_v2 as transport
from .modelos_robustos_compuestos2023 import lgb_frame
FEATURES,KEY=base.FEATURES,base.KEY
guard,features,metrics,unit_deviance=base.guard,base.features,base.metrics,base.unit_deviance
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'


def parent_rate(frame,parent):
    return np.exp(transport.design(frame,parent)@parent['coef'])


def predict(bundle,frame,training=True):
    guard(frame,bundle['line'],training=training);f=features(frame,bundle['line']);f['x_market']='emerging'
    a=parent_rate(f,bundle['parent']);raw=bundle['estimator'].predict(lgb_frame(f,bundle['columns'],bundle['categories']),raw_score=True)
    rate=a*np.exp(raw);base.require(np.isfinite(rate).all() and (rate>0).all(),'Tasa inválida')
    return rate


def fit(frame,line,held,recipe):
    guard(frame,line,held);target=features(frame,line)
    if recipe.get('synthetic') is True:
        base.require(target.row_id.str.startswith('s').all(),'Solo sintético puede pasar fuente')
        source=recipe['_source_frame'].copy();parent=recipe['_base_bundle'];parent_path='synthetic'
    else:
        import pyarrow.parquet as pq
        source=pq.read_table(R/f'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas()
        parent_path=f'privado/semana2/robustez2023/ciclo4_20261025_v1/models/W2-COD-R27_{line}_fold{held}.joblib'
        parent=joblib.load(R/parent_path)
        base.require(parent['model_id']=='W2-COD-R27' and parent['held_fold']==held,'Base de ámbito equivocado')
    transport.source_guard(source,line);source=features(source,line)
    basehash=joblib.hash(parent)
    target['x_market']='emerging';source['x_market']='developed'
    joined=pd.concat([target,source],ignore_index=True)
    et=target['e_cost_mix_1.0'].to_numpy(float);es=source.exposure.to_numpy(float)
    e=np.r_[et,es];wtarget=np.sqrt(et);wsource=np.sqrt(es)
    w=np.r_[wtarget,.25*wtarget.sum()*wsource/wsource.sum()]
    a=np.r_[parent_rate(target,parent),parent_rate(source,parent)]
    cols=FEATURES[line]['numeric']+FEATURES[line]['categorical']+['x_market']
    cats=FEATURES[line]['categorical']+['x_market'];levels={c:sorted(joined[c].astype(str).unique().tolist()) for c in cats}
    x=lgb_frame(joined,cols,levels)
    params={'objective':'tweedie','tweedie_variance_power':1.5,'n_estimators':recipe['trees'],
        'learning_rate':.025,'num_leaves':recipe['leaves'],'max_depth':recipe['depth'],
        'min_child_samples':recipe['min_rows'],'reg_lambda':recipe['lambda'],'reg_alpha':recipe['l1'],
        'max_bin':63,'min_data_per_group':100,'cat_smooth':50.,'subsample':1.,'colsample_bytree':1.,
        'deterministic':True,'force_col_wise':True,'random_state':2026102505,'n_jobs':2,'verbosity':-1}
    estimator=lgb.LGBMRegressor(**params)
    estimator.fit(x,joined.T0.to_numpy()/e,sample_weight=w,init_score=np.log(a),categorical_feature=cats)
    base.require(joblib.hash(parent)==basehash,'Base alterada')
    bundle={'model_id':recipe['id'],'line':line,'held_fold':held,'family':'TransportedResidualTrees','parent':parent,
            'columns':cols,'categories':levels,'estimator':estimator}
    return bundle,{'line':line,'fold':held,'fit_rows':len(target),'source_rows':len(source),'price_estimator_fits':1,
       'source_weight_ratio':float(w[len(target):].sum()/w[:len(target)].sum()),'params':params,
       'base':parent_path,'base_state_unchanged':True,'trees':estimator.booster_.num_trees(),
       'no_validation_or_stopping':True,'source_observation_exposure':'nominal; source observed incurred with own base intercept',
       'emerging_support_not_pooled':True}
