"""CatBoost Ordered fuente, baseline GLM congelado y adaptador emergente mínimo."""
import numpy as np,pandas as pd,joblib
from catboost import CatBoostRegressor,Pool
from scipy import optimize
from sklearn.preprocessing import OneHotEncoder
from . import modelo_profesor_comun2023 as old
from .desplegar_robustez2023 import TEACHERS
KEY=old.KEY;FEATURES=old.FEATURES;features=old.features;guard=old.guard;metrics=old.metrics;unit_deviance=old.unit_deviance

def cb_input(parent,frame):
 f=features(frame,parent['line']);nums=[x for x in parent['columns'] if x in FEATURES[parent['line']]['numeric']];cats=[x for x in parent['columns'] if x not in nums]
 numeric=parent['transformer'].named_transformers_['numeric'].transform(f[nums]);out=pd.DataFrame(numeric,columns=nums,index=f.index)
 for c in cats:out[c]=f[c].astype(str)
 assert np.isfinite(out[nums].to_numpy()).all();return out[nums+cats],cats

def teacher_rate(b,frame):
 a=old.teacher_rate(b['parent'],frame);x,_=cb_input(b['parent'],frame);delta=b['estimator'].predict(Pool(x,cat_features=b['categorical']),prediction_type='RawFormulaVal',thread_count=2)
 rate=a*np.exp(delta);assert np.isfinite(rate).all() and (rate>0).all();return rate

def fit_source(source,line,parent,recipe):
 old.source_guard(source,line);f=source.sort_values('source_group_id',kind='stable').reset_index(drop=True);before=joblib.hash(parent)
 x,cats=cb_input(parent,f);a=old.teacher_rate(parent,f);e=f.exposure.to_numpy(float);y=f.T0.to_numpy(float)/e;scale=max(1000.,float(y.max())/1000.);l2=500./np.sqrt(scale)
 pool=Pool(x,cat_features=cats,label=y/scale,weight=np.sqrt(e),baseline=np.log(a/scale),group_id=f.source_group_id.astype(str).tolist())
 est=CatBoostRegressor(loss_function='Tweedie:variance_power=1.5',iterations=300,depth=recipe['depth'],learning_rate=.025,l2_leaf_reg=l2,boosting_type='Ordered',bootstrap_type='Bayesian',bagging_temperature=1.,sampling_unit='Group',one_hot_max_size=40,random_strength=0.,thread_count=2,random_seed=2026102518,allow_writing_files=False,verbose=False,boost_from_average=False)
 est.fit(pool);assert joblib.hash(parent)==before
 b={'line':line,'model_id':recipe['id'],'family':'SourceCatBoostOrdered','parent':parent,'estimator':est,'categorical':cats,'label_scale':scale}
 delta=est.predict(Pool(x,cat_features=cats),prediction_type='RawFormulaVal',thread_count=2);with_baseline=est.predict(pool,prediction_type='RawFormulaVal',thread_count=2);err=float(np.max(np.abs(with_baseline-delta-np.log(a/scale))))
 assert err<1e-5 and np.isfinite(a*np.exp(delta)).all()
 return b,{'line':line,'model_id':recipe['id'],'source_rows':len(f),'price_estimator_fits':1,'depth':recipe['depth'],'source_groups':int(f.source_group_id.nunique()),'label_scale':scale,'scaled_label_max':float(y.max()/scale),'l2_leaf_reg':l2,'baseline_additivity_error':err,'source_parent_unchanged':True,'params':est.get_all_params()}

def fit(frame,line,held,teacher,model_id):
 guard(frame,line,held);f=features(frame,line);before=joblib.hash(teacher);a=teacher_rate(teacher,f)
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);x=old.adapter_matrix(f,enc)
 e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);pen=np.r_[np.ones(x.shape[1]-1),0.];beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*v
 result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(result.x)
 assert result.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before
 return {'line':line,'held_fold':held,'model_id':model_id,'teacher':teacher,'region_encoder':enc,'coef':result.x},{'line':line,'fold':held,'model_id':model_id,'fit_rows':len(f),'price_estimator_fits':1,'teacher_unchanged':True,'max_abs_gradient':float(np.abs(g).max())}

def predict(b,frame,training=True):
 guard(frame,b['line'],training=training);f=features(frame,b['line']);return teacher_rate(b['teacher'],f)*np.exp(old.adapter_matrix(f,b['region_encoder'])@b['coef'])
