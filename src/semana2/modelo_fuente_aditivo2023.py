"""Curvas aditivas de fuente con el contrato físico y alpha1 existentes."""
import warnings
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder,SplineTransformer
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from . import modelo_fuente_penalizacion2023 as previous

KEY=previous.KEY;FEATURES=previous.FEATURES;old=previous.old
guard=previous.guard;features=previous.features;metrics=previous.metrics
unit_deviance=previous.unit_deviance;attach=previous.attach
teacher_rate=previous.teacher_rate;fit=previous.fit;predict=previous.predict
CURVED=old.base.SPLINE

def fit_source(source,line,kind,parent=None):
    if kind=='trees':
        return previous.fit_source(source,line,kind,parent=parent)
    assert kind=='glm'
    old.source_guard(source,line);f=features(source,line)
    curved=CURVED[line];linear=[c for c in FEATURES[line]['numeric'] if c not in curved]
    cats=[c for c in FEATURES[line]['categorical'] if c!='x_region' and (line!='buildings' or c!='x_construction_type')]
    cols=FEATURES[line]['numeric']+cats
    def common():return [('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper())]
    tr=ColumnTransformer([
        ('linear',Pipeline(common()+[('scale',StandardScaler())]),linear),
        ('curved',Pipeline(common()+[('basis',SplineTransformer(n_knots=4,degree=2,knots='quantile',include_bias=False,extrapolation='constant')),('scale',StandardScaler())]),curved),
        ('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),cats)],sparse_threshold=1.)
    x=tr.fit_transform(f[cols]);e=f.exposure.to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e)
    est=TweedieRegressor(power=1.5,alpha=1.,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always');est.fit(x,y,sample_weight=w)
    assert not any(issubclass(n.category,ConvergenceWarning) for n in notes)
    rate=est.predict(x);g=w*(np.sqrt(rate)-y/np.sqrt(rate))/w.sum();gradient=np.r_[np.asarray(x.T@g).ravel()+est.coef_,g.sum()]
    assert np.abs(gradient).max()<=1e-4
    assert np.allclose(rate,np.exp(x@est.coef_+est.intercept_),rtol=1e-12,atol=1e-9)
    return {'line':line,'family':'ExtendedSourceGAM','columns':cols,'transformer':tr,'estimator':est}, {'line':line,'kind':'source_additive_GLM','source_rows':len(f),'price_estimator_fits':1,'source_only':True,'curved':curved,'linear':linear,'alpha':1.,'n_parameters':x.shape[1]+1,'max_abs_gradient':float(np.abs(gradient).max()),'manual_exp_prediction_checked':True,'params':est.get_params()}
