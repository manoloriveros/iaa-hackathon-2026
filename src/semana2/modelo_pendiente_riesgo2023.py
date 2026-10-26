"""Una pendiente de transporte para el índice de riesgo fuente, GLM estándar."""
import numpy as np,joblib
from scipy import sparse,optimize
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from . import modelo_profesor_comun2023 as old
from .desplegar_robustez2023 import TEACHERS
KEY=old.KEY;FEATURES=old.FEATURES;features=old.features;guard=old.guard;metrics=old.metrics;unit_deviance=old.unit_deviance
def matrix(f,b,a):
 z=b['risk_scaler'].transform(np.log(a)[:,None])
 return sparse.hstack([sparse.csr_matrix(f.x_new_business.to_numpy(float)[:,None]),b['region'].transform(f[['x_region']]),sparse.csr_matrix(z),sparse.csr_matrix(np.ones((len(f),1)))],format='csr')
def fit(frame,line,held,recipe):
 guard(frame,line,held);f=features(frame,line)
 if recipe.get('synthetic'):
  assert f.row_id.str.startswith('s').all();teacher=recipe['_teacher']
 else:
  teacher=joblib.load(TEACHERS[line]);teacher=teacher if recipe['source_trees'] else teacher['parent']
 before=joblib.hash(teacher);a=old.teacher_rate(teacher,f);scaler=StandardScaler().fit(np.log(a)[:,None]);scale=float(scaler.scale_[0])
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']])
 b={'line':line,'held_fold':held,'model_id':recipe['id'],'teacher':teacher,'risk_scaler':scaler,'region':enc};x=matrix(f,b,a)
 e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);pen=np.r_[np.ones(x.shape[1]-1),0.]
 beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*v
 bounds=[(None,None)]*len(beta);bounds[-2]=(-scale,scale)
 result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(result.x)
 projected=g.copy()
 if result.x[-2]<=-scale+1e-8 and g[-2]>0:projected[-2]=0
 if result.x[-2]>=scale-1e-8 and g[-2]<0:projected[-2]=0
 assert result.success and np.abs(projected).max()<=1e-4 and joblib.hash(teacher)==before;b['coef']=result.x
 return b,{'line':line,'fold':held,'model_id':recipe['id'],'fit_rows':len(f),'price_estimator_fits':1,'source_trees':recipe.get('source_trees',False),'teacher_unchanged':True,'max_abs_projected_gradient':float(np.abs(projected).max()),'teacher_log_rate_sd_fit':scale,'teacher_risk_power':float(1+result.x[-2]/scale),'fit_only_risk_standardization':True}
def predict(b,frame,training=True):
 guard(frame,b['line'],training=training);f=features(frame,b['line']);a=old.teacher_rate(b['teacher'],f);return a*np.exp(matrix(f,b,a)@b['coef'])
