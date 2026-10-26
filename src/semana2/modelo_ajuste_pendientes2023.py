"""Correcciones de efectos principales hacia un profesor fuente congelado."""
import warnings
import numpy as np,joblib
from scipy import sparse,optimize
from . import modelo_profesor_comun2023 as old
from .desplegar_robustez2023 import TEACHERS
KEY=old.KEY;FEATURES=old.FEATURES;guard=old.guard;features=old.features;metrics=old.metrics;unit_deviance=old.unit_deviance

def matrix(frame,b):
 x=b['transformer'].transform(frame[b['columns']]);return sparse.hstack([sparse.csr_matrix(x),sparse.csr_matrix(np.ones((len(frame),1)))],format='csr')

def fit(frame,line,held,recipe):
 guard(frame,line,held);f=features(frame,line)
 if recipe.get('synthetic'):
  assert f.row_id.str.startswith('s').all();teacher=recipe['_teacher']
 else:teacher=joblib.load(TEACHERS[line])
 before=joblib.hash(teacher);a=old.teacher_rate(teacher,f)
 tr=old.base.transformer(line,'linear');cols=FEATURES[line]['numeric']+FEATURES[line]['categorical'];tr.fit(f[cols])
 b={'line':line,'held_fold':held,'model_id':recipe['id'],'teacher':teacher,'transformer':tr,'columns':cols,'alpha':recipe['alpha']};x=matrix(f,b)
 e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);pen=np.r_[np.full(x.shape[1]-1,recipe['alpha']),0.]
 coef=np.zeros(x.shape[1]);coef[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*v
 result=optimize.minimize(objective,coef,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});value,g=objective(result.x)
 assert result.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before;b['coef']=result.x
 rec={'line':line,'fold':held,'model_id':recipe['id'],'alpha':recipe['alpha'],'fit_rows':len(f),'price_estimator_fits':1,'teacher_unchanged':True,'max_abs_gradient':float(np.abs(g).max()),'objective':value,'n_iter':int(result.nit),'correction_coef_l2':float(np.linalg.norm(result.x[:-1])),'columns':cols,'transformed_features':x.shape[1]-1,'all_learning_fit_only':True}
 return b,rec

def predict(b,frame,training=True):
 guard(frame,b['line'],training=training);f=features(frame,b['line']);return old.teacher_rate(b['teacher'],f)*np.exp(matrix(f,b)@b['coef'])

def mathematical_check():
 # Independent sklearn loss and finite differences on a synthetic exposure-offset problem.
 from sklearn.metrics import mean_tweedie_deviance
 from scipy.optimize import approx_fprime
 rng=np.random.default_rng(2026102515);x=rng.normal(size=(40,5));x[:,-1]=1.;e=rng.uniform(.1,1.,40);y=rng.poisson(.4,40)*rng.gamma(2,100,40);offset=rng.normal(5,.3,40);v=rng.normal(0,.1,5);pen=np.array([10.,10.,10.,10.,0.]);w=np.sqrt(e);w/=w.sum()
 def objective(c):
  eta=offset+x@c;s=np.exp(eta/2);iv=np.exp(-eta/2);return float(2*np.dot(w,y/e*iv+s-2*np.sqrt(y/e))+.5*np.dot(pen*c,c))
 eta=offset+x@v;grad=x.T@(w*(np.exp(eta/2)-y/e*np.exp(-eta/2)))+pen*v
 numerical=approx_fprime(v,objective,1e-6);mu=e*np.exp(eta);independent=.5*mean_tweedie_deviance(y,mu,power=1.5)*len(y)/np.sqrt(e).sum()+.5*np.dot(pen*v,v)
 assert np.allclose(grad,numerical,rtol=1e-4,atol=1e-4) and np.isclose(objective(v),independent,rtol=1e-12)
 return {'gradient_max_abs_difference':float(np.max(np.abs(grad-numerical))),'row_cost_offset_loss_matches_sklearn':True,'new_fits':0}
