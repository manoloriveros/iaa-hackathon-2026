"""Agregación de profesores por bloques fuente y adaptador GLM mínimo."""
import numpy as np,joblib
from scipy import optimize
from sklearn.preprocessing import OneHotEncoder
from . import modelo_profesor_comun2023 as old
KEY=old.KEY;FEATURES=old.FEATURES;features=old.features;guard=old.guard;metrics=old.metrics;unit_deviance=old.unit_deviance;fit_teachers=old.fit_teachers
def teacher_rate(b,frame):
 rates=np.stack([old.teacher_rate(member,frame) for member in b['members']]);assert np.isfinite(rates).all() and (rates>0).all();return np.square(np.sqrt(rates).mean(axis=0))
def fit(frame,line,held,teacher,model_id):
 guard(frame,line,held);f=features(frame,line);before=joblib.hash(teacher);a=teacher_rate(teacher,f)
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);x=old.adapter_matrix(f,enc)
 e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);pen=np.r_[np.ones(x.shape[1]-1),0.];beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*v
 result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(result.x)
 assert result.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before
 return {'line':line,'held_fold':held,'model_id':model_id,'teacher':teacher,'region_encoder':enc,'coef':result.x},{'line':line,'fold':held,'model_id':model_id,'fit_rows':len(f),'price_estimator_fits':1,'source_bags':len(teacher['members']),'teacher_unchanged':True,'max_abs_gradient':float(np.abs(g).max())}
def predict(b,frame,training=True):
 guard(frame,b['line'],training=training);f=features(frame,b['line']);return teacher_rate(b['teacher'],f)*np.exp(old.adapter_matrix(f,b['region_encoder'])@b['coef'])
