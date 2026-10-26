"""Frecuencia Poisson de costes positivos por marca Gamma; todos los ceros en frecuencia."""
import warnings
import numpy as np,pandas as pd,joblib,lightgbm as lgb
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import PoissonRegressor,GammaRegressor
from sklearn.exceptions import ConvergenceWarning
from . import modelo_profesor_comun2023 as old
from .modelos_robustos_compuestos2023 import lgb_frame
KEY=old.KEY;FEATURES=old.FEATURES;guard=old.guard;features=old.features;metrics=old.metrics;unit_deviance=old.unit_deviance

def attach(frame,extra):
 assert not extra.duplicated(KEY).any() and not set(extra.columns[3:]).intersection(frame.columns)
 out=frame.merge(extra,on=KEY,how='left',validate='one_to_one',indicator=True);assert len(out)==len(frame) and out['_merge'].eq('both').all();return out.drop(columns='_merge')

def components(b,frame):
 f=features(frame,b['line'])
 if b['family']=='PositiveFreqTrees':
  freq,mark=components(b['parent'],f);freq=freq*np.exp(b['boost'].predict(lgb_frame(f,b['columns'],b['categories']),raw_score=True))
 else:
  x=b['transformer'].transform(f[b['columns']]);freq=b['frequency'].predict(x);mark=b['mark'].predict(x)
 assert np.isfinite(freq).all() and (freq>0).all() and np.isfinite(mark).all() and (mark>0).all();return freq,mark

def teacher_rate(b,frame):
 freq,mark=components(b,frame);return freq*mark

def fit_source(source,line,kind,parent=None):
 old.source_guard(source,line);f=features(source,line);e=f.exposure.to_numpy(float);n=f.N_positive.to_numpy(float);cost=f.cost_cents.to_numpy(float)/100;assert np.array_equal(cost,f.T0.to_numpy(float)) and np.array_equal(f.N,f.N_positive+f.N_zero) and ((n>0)==(cost>0)).all()
 nums=FEATURES[line]['numeric'];cats=[c for c in FEATURES[line]['categorical'] if c!='x_region' and (line!='buildings' or c!='x_construction_type')];cols=nums+cats
 if kind=='trees':
  assert parent is not None;before=joblib.hash(parent);freq,_=components(parent,f);levels={c:sorted(f[c].astype(str).unique().tolist()) for c in cats}
  est=lgb.LGBMRegressor(objective='poisson',n_estimators=200,learning_rate=.025,num_leaves=8,max_depth=3,min_child_samples=5000,reg_lambda=20.,reg_alpha=1.,max_bin=63,min_data_per_group=100,cat_smooth=50.,deterministic=True,force_col_wise=True,random_state=2026102516,n_jobs=2,verbosity=-1)
  est.fit(lgb_frame(f,cols,levels),n/e,sample_weight=e,init_score=np.log(freq),categorical_feature=cats);assert joblib.hash(parent)==before
  return {'line':line,'family':'PositiveFreqTrees','parent':parent,'boost':est,'columns':cols,'categories':levels},{'line':line,'kind':kind,'source_rows':len(f),'price_estimator_fits':1,'parent_unchanged':True,'params':est.get_params()}
 assert kind=='glm';tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())]),nums),('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),cats)],sparse_threshold=1.);x=tr.fit_transform(f[cols]);frequency=PoissonRegressor(alpha=.001,max_iter=3000,tol=1e-7);pos=n>0;assert pos.sum()>=100;mark=GammaRegressor(alpha=.1,max_iter=3000,tol=1e-7)
 with warnings.catch_warnings(record=True) as notes:
  warnings.simplefilter('always');frequency.fit(x,n/e,sample_weight=e);mark.fit(x[pos],cost[pos]/n[pos],sample_weight=n[pos])
 assert not any(issubclass(v.category,ConvergenceWarning) for v in notes);mu=frequency.predict(x);g=e*(mu-n/e)/e.sum();fg=np.r_[np.asarray(x.T@g).ravel()+.001*frequency.coef_,g.sum()];mm=mark.predict(x[pos]);g=n[pos]*(1-cost[pos]/n[pos]/mm)/n[pos].sum();mg=np.r_[np.asarray(x[pos].T@g).ravel()+.1*mark.coef_,g.sum()];assert np.abs(fg).max()<=1e-4 and np.abs(mg).max()<=1e-4
 return {'line':line,'family':'PositiveFreqGamma','transformer':tr,'columns':cols,'frequency':frequency,'mark':mark},{'line':line,'kind':kind,'source_rows':len(f),'price_estimator_fits':2,'positivecost_claims':int(n.sum()),'zero_cost_claims_retained':int(f.N_zero.sum()),'all_periods_in_frequency':True,'fullcost_retained':True,'max_frequency_gradient':float(np.abs(fg).max()),'max_mark_gradient':float(np.abs(mg).max()),'source_only':True}

def fit(frame,line,held,teacher,model_id):
 # Same existing offset GLM, with the new rate product evaluated before calibration.
 from scipy import optimize
 guard(frame,line,held);f=features(frame,line);before=joblib.hash(teacher);a=teacher_rate(teacher,f);enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);x=old.adapter_matrix(f,enc);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);coef=np.zeros(x.shape[1]);coef[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)));penalty=np.r_[np.ones(x.shape[1]-1),0.]
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2);return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(penalty*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+penalty*v
 res=optimize.minimize(objective,coef,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(res.x);assert res.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before
 return {'line':line,'model_id':model_id,'held_fold':held,'teacher':teacher,'region_encoder':enc,'coef':res.x},{'line':line,'model_id':model_id,'fold':held,'fit_rows':len(f),'price_estimator_fits':1,'max_abs_gradient':float(np.abs(g).max()),'teacher_unchanged':True,'all_learning_fit_only':True}

def predict(b,frame,training=True):
 guard(frame,b['line'],training=training);f=features(frame,b['line']);return teacher_rate(b['teacher'],f)*np.exp(old.adapter_matrix(f,b['region_encoder'])@b['coef'])
