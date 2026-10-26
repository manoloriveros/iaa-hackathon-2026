"""Modelos físicos regularizados, sin productores multianuales ni datos2024."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import TweedieRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, SplineTransformer

KEY = ['market', 'line', 'row_id']
FEATURES = {
 'motor': {'numeric': ['x_new_business','x_ncb_years','x_vehicle_age','x_vehicle_value_group','x_years_licensed','x_engine_size_cc','x_named_young_driver','x_driver_assist','x_log_voluntary_excess','x_log_compulsory_excess'],
           'categorical': ['x_driver_age_band','x_region','x_cover_type','x_body_type','x_transmission','x_fuel_type','x_overnight_parking','x_vehicle_use']},
 'buildings': {'numeric': ['x_new_business','x_log_sum_insured','x_property_age','x_flood_zone','x_log_distance_to_river_km','x_elevation_m','x_smoke_alarms','x_accidental_damage_cover','x_log_voluntary_excess','x_log_compulsory_excess'],
           'categorical': ['x_property_type','x_region','x_construction_type','x_occupancy','x_roof_type','x_soil_type']},
 'contents': {'numeric': ['x_new_business','x_log_sum_insured','x_bedrooms','x_high_value_items','x_accidental_damage_cover','x_basement','x_log_distance_to_river_km','x_elevation_m','x_bicycle_cover','x_log_voluntary_excess','x_log_compulsory_excess'],
           'categorical': ['x_property_type','x_region','x_security_level','x_tenure','x_roof_type','x_soil_type']}}
SPLINE = {'motor':['x_ncb_years','x_vehicle_age','x_years_licensed','x_vehicle_value_group','x_engine_size_cc'],
          'buildings':['x_log_sum_insured','x_property_age','x_log_distance_to_river_km','x_elevation_m'],
          'contents':['x_log_sum_insured','x_bedrooms','x_log_distance_to_river_km','x_elevation_m']}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def guard(frame, line, held=None, training=True):
    require(len(frame)>0 and frame.line.eq(line).all() and frame.market.eq('emerging').all(), 'Ámbito incorrecto')
    require(frame.year.eq(2023 if training else 2025).all(), 'Año no autorizado')
    require(frame.is_test.eq(not training).all(), 'Rol incorrecto')
    require(not frame.duplicated(KEY).any(), 'Claves duplicadas')
    if held is not None:
        require(frame.fold.ne(held).all(), 'Retenido en entrenamiento')


def features(frame, line):
    f=frame.copy()
    for name in ('voluntary_excess','compulsory_excess','distance_to_river_km'):
        src='x_'+name
        if src in f:
            v=pd.to_numeric(f[src],errors='coerce')
            f['x_log_'+name]=np.log1p(v.where(v.ge(0)))
    for name in FEATURES[line]['numeric']:
        f[name]=pd.to_numeric(f[name],errors='coerce')
        require(not np.isinf(f[name]).any(), 'Predictor infinito: '+name)
    for name in FEATURES[line]['categorical']:
        f[name]=f[name].astype('string').fillna('__MISSING__').astype(str)
    return f


class QuantileClipper(BaseEstimator, TransformerMixin):
    def __init__(self, lower=.005, upper=.995):
        self.lower=lower
        self.upper=upper

    def fit(self, X, y=None):
        x=np.asarray(X,dtype=float)
        require(np.isfinite(x).all(), 'Imputar antes de truncar covariables')
        self.lower_=np.quantile(x,self.lower,axis=0)
        self.upper_=np.quantile(x,self.upper,axis=0)
        return self

    def transform(self,X):
        return np.clip(np.asarray(X,dtype=float),self.lower_,self.upper_)


def transformer(line, shape='linear'):
    block=FEATURES[line]
    numeric=list(block['numeric'])
    branches=[]
    if shape=='spline':
        curved=SPLINE[line]
        numeric=[x for x in numeric if x not in curved]
        branches.append(('spline',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),
            ('clip',QuantileClipper()),('basis',SplineTransformer(n_knots=4,degree=2,knots='quantile',extrapolation='constant',include_bias=False)),
            ('scale',StandardScaler())]),curved))
    branches += [('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),
                 ('clip',QuantileClipper()),('scale',StandardScaler())]),numeric),
                ('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),block['categorical'])]
    return ColumnTransformer(branches,sparse_threshold=1.)


def unit_deviance(y,mu):
    y=np.asarray(y,dtype=float);mu=np.asarray(mu,dtype=float)
    require(np.isfinite(mu).all() and (mu>0).all() and np.isfinite(y).all() and (y>=0).all(), 'Tweedie inválida')
    return np.maximum(4*(y/np.sqrt(mu)+np.sqrt(mu)-2*np.sqrt(y)),0.)


def metrics(frame, prediction='prediction', target='T0'):
    y=frame[target].to_numpy(float);mu=frame[prediction].to_numpy(float)
    loss=unit_deviance(y,mu).sum();null=unit_deviance(y,np.full(len(y),y.mean())).sum()
    return {'rows':len(y),'observed_total':float(y.sum()),'predicted_total':float(mu.sum()),
            'deviance_sum':float(loss),'null_deviance_sum':float(null),
            'D2':float(1-loss/null) if null>0 else None,'AE':float(y.sum()/mu.sum())}


def predict(bundle,frame,training=True):
    guard(frame,bundle['line'],training=training)
    f=features(frame,bundle['line'])
    return bundle['estimator'].predict(bundle['transformer'].transform(f[bundle['columns']]))


def fit(frame,line,held,recipe):
    import warnings
    from sklearn.exceptions import ConvergenceWarning
    guard(frame,line,held)
    f=features(frame,line);cols=FEATURES[line]['numeric']+FEATURES[line]['categorical']
    require(not any(x in cols for x in ['T0','reserve','written_premium','x_days_unoccupied','policy_id','row_id']), 'Predictor excluido')
    tr=transformer(line,recipe['shape']);x=tr.fit_transform(f[cols])
    e=f['e_cost_mix_1.0'].to_numpy(float);require(np.isfinite(e).all() and (e>0).all(),'C0 inválido')
    response=f.T0.to_numpy(float)/e;w=np.sqrt(e)
    est=TweedieRegressor(power=1.5,alpha=recipe['alpha'],fit_intercept=True,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always');est.fit(x,response,sample_weight=w)
    require(not any(issubclass(n.category,ConvergenceWarning) for n in notes),'No convergió')
    rate=est.predict(x)
    g=w*(np.sqrt(rate)-response/np.sqrt(rate))/w.sum()
    score=np.r_[np.asarray(x.T@g).ravel()+est.alpha*est.coef_,g.sum()]
    require(np.max(np.abs(score))<=1e-4,'Gradiente no convergente')
    require(np.allclose(rate,np.exp(x@est.coef_+est.intercept_),rtol=1e-12,atol=1e-9),'Predicción manual discrepante')
    bundle={'model_id':recipe['id'],'line':line,'held_fold':held,'columns':cols,'transformer':tr,'estimator':est,'shape':recipe['shape']}
    return bundle,{'line':line,'held_fold':held,'fit_rows':len(f),'columns':cols,'params':est.get_params(),
        'transformed_features':x.shape[1],'n_iter':int(est.n_iter_),
        'max_abs_penalized_gradient':float(np.max(np.abs(score))),
        'warnings':[{'category':n.category.__name__,'message':str(n.message)} for n in notes]}
