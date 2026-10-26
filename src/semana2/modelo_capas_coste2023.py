"""Media por coste limitado y frecuencia/marca de exceso; total conservado."""
import warnings
import numpy as np,pandas as pd,joblib,lightgbm as lgb
from scipy import sparse,optimize
from sklearn.linear_model import TweedieRegressor,PoissonRegressor,GammaRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from . import modelo_profesor_comun2023 as old
from .modelos_robustos_compuestos2023 import lgb_frame
KEY=old.KEY;FEATURES=old.FEATURES;features=old.features;guard=old.guard;metrics=old.metrics;unit_deviance=old.unit_deviance
def train_source(source,layers,line):
 old.source_guard(source,line);f=features(source,line);layer=f[KEY].merge(layers,on=KEY,validate='one_to_one',how='left');assert layer.cost_cents.notna().all() and np.array_equal(layer.cost_cents.to_numpy()/100,f.T0.to_numpy()) and np.array_equal(layer.cost_cents,layer.limited_cents+layer.excess_cents)
 nums=FEATURES[line]['numeric'];cats=[c for c in FEATURES[line]['categorical'] if c!='x_region' and (line!='buildings' or c!='x_construction_type')];cols=nums+cats
 tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())]),nums),('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),cats)],sparse_threshold=1.)
 x=tr.fit_transform(f[cols]);e=f.exposure.to_numpy(float);limited=layer.limited_cents.to_numpy(float)/100;excess=layer.excess_cents.to_numpy(float)/100;n=layer.tail_count.to_numpy(float);assert n.sum()>0 and excess.sum()>0
 limited_model=TweedieRegressor(power=1.5,alpha=1.,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
 with warnings.catch_warnings(record=True) as notes:
  warnings.simplefilter('always');limited_model.fit(x,limited/e,sample_weight=np.sqrt(e))
 assert not any(issubclass(v.category,ConvergenceWarning) for v in notes);mu=limited_model.predict(x);w=np.sqrt(e);g=w*(np.sqrt(mu)-limited/e/np.sqrt(mu))/w.sum();grad=np.r_[np.asarray(x.T@g).ravel()+limited_model.coef_,g.sum()];assert np.abs(grad).max()<=1e-4
 levels={c:sorted(f[c].astype(str).unique().tolist()) for c in cats};boost=lgb.LGBMRegressor(objective='tweedie',tweedie_variance_power=1.5,n_estimators=200,learning_rate=.025,num_leaves=8,max_depth=3,min_child_samples=5000,reg_lambda=500.,reg_alpha=100.,max_bin=63,min_data_per_group=100,cat_smooth=50.,deterministic=True,force_col_wise=True,random_state=2026102506,n_jobs=2,verbosity=-1)
 boost.fit(lgb_frame(f,cols,levels),limited/e,sample_weight=np.sqrt(e),init_score=np.log(mu),categorical_feature=cats)
 frequency=PoissonRegressor(alpha=.001,fit_intercept=True,solver='lbfgs',max_iter=3000,tol=1e-7)
 with warnings.catch_warnings(record=True) as notes:
  warnings.simplefilter('always');frequency.fit(x,n/e,sample_weight=e)
 assert not any(issubclass(v.category,ConvergenceWarning) for v in notes);fm=frequency.predict(x);g=e*(fm-n/e)/e.sum();fg=np.r_[np.asarray(x.T@g).ravel()+.001*frequency.coef_,g.sum()];assert np.abs(fg).max()<=1e-4
 pos=n>0;mark=None;constant=None;mg=None
 if pos.sum()>=100:
  mark=GammaRegressor(alpha=.1,fit_intercept=True,solver='lbfgs',max_iter=3000,tol=1e-7)
  with warnings.catch_warnings(record=True) as notes:
   warnings.simplefilter('always');mark.fit(x[pos],excess[pos]/n[pos],sample_weight=n[pos])
  assert not any(issubclass(v.category,ConvergenceWarning) for v in notes);mm=mark.predict(x[pos]);g=n[pos]*(1-excess[pos]/n[pos]/mm)/n[pos].sum();mg=np.r_[np.asarray(x[pos].T@g).ravel()+.1*mark.coef_,g.sum()];assert np.abs(mg).max()<=1e-4
 else:constant=float(excess.sum()/n.sum())
 bundle={'line':line,'columns':cols,'transformer':tr,'categories':levels,'limited_model':limited_model,'limited_boost':boost,'frequency':frequency,'mark':mark,'constant_mark':constant}
 return bundle,{'line':line,'source_rows':len(f),'price_estimator_fits':3+int(mark is not None),'closed_form_mark_constants':int(mark is None),'tail_claims':int(n.sum()),'tail_periods':int(pos.sum()),'max_limited_gradient':float(np.abs(grad).max()),'max_frequency_gradient':float(np.abs(fg).max()),'max_mark_gradient':float(np.abs(mg).max()) if mg is not None else None,'all_cost_retained':True,'limited_cap_CU':10000.}
def components(source,frame):
 f=features(frame,source['line']);x=source['transformer'].transform(f[source['columns']]);limited=source['limited_model'].predict(x)*np.exp(source['limited_boost'].predict(lgb_frame(f,source['columns'],source['categories']),raw_score=True));freq=source['frequency'].predict(x);mark=source['mark'].predict(x) if source['mark'] is not None else np.full(len(f),source['constant_mark']);excess=freq*mark
 assert np.isfinite(limited).all() and (limited>0).all() and np.isfinite(excess).all() and (excess>0).all();return limited,excess
def matrix(f,z,b):
 parts=[sparse.csr_matrix(f.x_new_business.to_numpy(float)[:,None]),b['region'].transform(f[['x_region']])]
 if b['tail_share_effect']:parts.append(sparse.csr_matrix(b['tail_transform'].transform(z[:,None])))
 return sparse.hstack(parts+[sparse.csr_matrix(np.ones((len(f),1)))],format='csr')
def fit(frame,line,held,source,recipe):
 guard(frame,line,held);f=features(frame,line);before=joblib.hash(source);limited,excess=components(source,f);a=limited+excess;z=np.log(excess/limited)
 region=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);region.fit(f[['x_region']]);tr=Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())])
 if recipe['tail_share_effect']:tr.fit(z[:,None])
 b={'line':line,'model_id':recipe['id'],'held_fold':held,'source':source,'region':region,'tail_share_effect':recipe['tail_share_effect'],'tail_transform':tr if recipe['tail_share_effect'] else None};x=matrix(f,z,b);pen=np.r_[np.ones(1+region.transform(f[['x_region']]).shape[1]),10. if recipe['tail_share_effect'] else np.array([]),0.];assert len(pen)==x.shape[1]
 e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);coef=np.zeros(x.shape[1]);coef[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*v
 res=optimize.minimize(objective,coef,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(res.x);assert res.success and np.abs(g).max()<=1e-4 and joblib.hash(source)==before;b['coef']=res.x
 return b,{'line':line,'model_id':recipe['id'],'fold':held,'fit_rows':len(f),'price_estimator_fits':1,'tail_share_effect':recipe['tail_share_effect'],'max_abs_gradient':float(np.abs(g).max()),'source_unchanged':True,'all_learning_fit_only':True}
def predict(b,frame,training=True,tail_level=1.):
 guard(frame,b['line'],training=training);f=features(frame,b['line']);limited,excess=components(b['source'],f);excess=excess*tail_level;z=np.log(excess/limited);return (limited+excess)*np.exp(matrix(f,z,b)@b['coef'])
