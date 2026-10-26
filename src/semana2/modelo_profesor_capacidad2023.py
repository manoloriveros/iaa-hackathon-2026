"""Capacidad fuente fijada, sin mayor flexibilidad en adaptación emergente."""
import hashlib
import numpy as np,pandas as pd,joblib,lightgbm as lgb
from . import modelo_profesor_comun2023 as old
from .desplegar_robustez2023 import TEACHERS
from .modelos_robustos_compuestos2023 import lgb_frame
KEY=old.KEY;FEATURES=old.FEATURES;features=old.features;guard=old.guard;metrics=old.metrics;unit_deviance=old.unit_deviance
RECIPES={'W2-COD-R45':{'num_leaves':16,'max_depth':4,'min_child_samples':2000},'W2-COD-R46':{'num_leaves':24,'max_depth':5,'min_child_samples':1000}}
def split_source(f):
 ids=sorted(f.customer_id.unique());held={x for x in ids if int(hashlib.sha256(('C11-source2023:'+x).encode()).hexdigest()[:8],16)%5==0}
 val=f[f.customer_id.isin(held)].copy();fit=f[~f.customer_id.isin(held)&~f.address_id.isin(set(val.address_id))].copy()
 assert set(fit.customer_id).isdisjoint(val.customer_id) and set(fit.address_id).isdisjoint(val.address_id)
 return fit,val
def fit_source(source,line,model_id,parent):
 old.source_guard(source,line);f=features(source,line);before=joblib.hash(parent);a=old.teacher_rate(parent,f);cols=parent['columns'];cats=[c for c in cols if c in FEATURES[line]['categorical']]
 levels={c:sorted(f[c].astype(str).unique().tolist()) for c in cats};e=f.exposure.to_numpy(float);y=f.T0.to_numpy(float)/e
 est=lgb.LGBMRegressor(objective='tweedie',tweedie_variance_power=1.5,n_estimators=800,learning_rate=.025,**RECIPES[model_id],reg_lambda=500.,reg_alpha=100.,max_bin=63,min_data_per_group=100,cat_smooth=50.,deterministic=True,force_col_wise=True,random_state=2026102511,n_jobs=2,verbosity=-1)
 est.fit(lgb_frame(f,cols,levels),y,sample_weight=np.sqrt(e),init_score=np.log(a),categorical_feature=cats)
 assert joblib.hash(parent)==before
 t={'line':line,'family':'SourceResidualTrees','columns':cols,'categories':levels,'parent':parent,'estimator':est}
 return t,{'line':line,'model_id':model_id,'source_rows':len(f),'price_estimator_fits':1,'teacher_parent_unchanged':True,'params':est.get_params()}
def fit(frame,line,held,teacher,model_id):
 # Preserve the established numerical adapter; only the frozen in-memory teacher changes.
 from scipy import optimize
 from sklearn.preprocessing import OneHotEncoder
 guard(frame,line,held);f=features(frame,line);before=joblib.hash(teacher);a=old.teacher_rate(teacher,f)
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);x=old.adapter_matrix(f,enc)
 e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)));pen=np.r_[np.ones(x.shape[1]-1),0.]
 def objective(b):
  eta=offset+x@b;s=np.exp(eta/2);inv=np.exp(-eta/2)
  return float(2*np.dot(w,y*inv+s-2*np.sqrt(y))+.5*np.dot(pen*b,b)),np.asarray(x.T@(w*(s-y*inv))).ravel()+pen*b
 result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(result.x)
 assert result.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before
 return {'line':line,'model_id':model_id,'held_fold':held,'teacher':teacher,'region_encoder':enc,'coef':result.x},{'line':line,'model_id':model_id,'fold':held,'fit_rows':len(f),'price_estimator_fits':1,'max_abs_gradient':float(np.abs(g).max()),'teacher_unchanged':True}
predict=old.predict
