"""Mismo GLM de offset, contracción fijada antes de observar validación."""
import numpy as np,joblib
from scipy import optimize
from sklearn.preprocessing import OneHotEncoder
from . import modelo_profesor_comun2023 as old
KEY=old.KEY;FEATURES=old.FEATURES;guard=old.guard;features=old.features;metrics=old.metrics;unit_deviance=old.unit_deviance

def fit(frame,line,held,teacher,recipe):
 guard(frame,line,held);f=features(frame,line);original=joblib.hash(teacher);a=old.teacher_rate(teacher,f)
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);x=old.adapter_matrix(f,enc)
 e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a)
 coef=np.zeros(x.shape[1]);coef[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)));penalty=np.r_[np.full(x.shape[1]-1,recipe['ridge']),0.]
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(penalty*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+penalty*v
 # A central finite difference checks the actual penalized objective independently.
 _,g0=objective(coef);fd=[]
 for j in range(len(coef)):
  delta=np.zeros(len(coef));delta[j]=1e-5;fd.append((objective(coef+delta)[0]-objective(coef-delta)[0])/2e-5)
 assert np.allclose(g0,fd,rtol=1e-4,atol=1e-6)
 res=optimize.minimize(objective,coef,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(res.x);assert res.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==original
 return {'line':line,'model_id':recipe['id'],'held_fold':held,'teacher':teacher,'region_encoder':enc,'coef':res.x,'ridge':recipe['ridge']},{'line':line,'model_id':recipe['id'],'fold':held,'fit_rows':len(f),'price_estimator_fits':1,'ridge':recipe['ridge'],'max_abs_gradient':float(np.abs(g).max()),'finite_difference_objective_gradient':True,'teacher_unchanged':True,'all_learning_fit_only':True}

def predict(bundle,frame,training=True):
 guard(frame,bundle['line'],training=training);f=features(frame,bundle['line']);return old.teacher_rate(bundle['teacher'],f)*np.exp(old.adapter_matrix(f,bundle['region_encoder'])@bundle['coef'])
