"""GLM mínimo de adquisición contractual con profesores físicos congelados."""
import numpy as np,pandas as pd,joblib
from scipy import sparse,optimize
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from . import modelo_profesor_comun2023 as old
from .modelo_basicas_fuente2023_v2 import attach
from .desplegar_robustez2023 import TEACHERS
KEY=old.KEY;FEATURES=old.FEATURES;guard=old.guard;metrics=old.metrics;unit_deviance=old.unit_deviance
def features(f,line):
 f=old.features(f,line);f['x_log_quote_delay']=np.log1p(pd.to_numeric(f.x_days_quote_to_inception));return f
def matrix(f,b):
 return sparse.hstack([sparse.csr_matrix(f.x_new_business.to_numpy(float)[:,None]),sparse.csr_matrix(b['numeric'].transform(f[['x_log_quote_delay','x_renewal_count']])),b['categorical'].transform(f[['x_region','x_channel','x_payment_method']]),sparse.csr_matrix(np.ones((len(f),1)))],format='csr')
def fit(frame,line,held,recipe):
 guard(frame,line,held);f=features(frame,line)
 if recipe.get('synthetic'):
  assert f.row_id.str.startswith('s').all();teacher=recipe['_teacher']
 else:
  teacher=joblib.load(TEACHERS[line]);teacher=teacher if recipe['source_trees'] else teacher['parent']
 before=joblib.hash(teacher);a=old.teacher_rate(teacher,f)
 numeric=Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())]);numeric.fit(f[['x_log_quote_delay','x_renewal_count']])
 cat=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);cat.fit(f[['x_region','x_channel','x_payment_method']])
 b={'model_id':recipe['id'],'line':line,'held_fold':held,'teacher':teacher,'numeric':numeric,'categorical':cat};x=matrix(f,b);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a)
 beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)));pen=np.r_[np.ones(x.shape[1]-1),0.]
 def objective(coef):
  eta=offset+x@coef;s=np.exp(eta/2);inv=np.exp(-eta/2)
  return float(2*np.dot(w,y*inv+s-2*np.sqrt(y))+.5*np.dot(pen*coef,coef)),np.asarray(x.T@(w*(s-y*inv))).ravel()+pen*coef
 result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(result.x)
 assert result.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before;b['coef']=result.x
 return b,{'line':line,'fold':held,'model_id':recipe['id'],'fit_rows':len(f),'price_estimator_fits':1,'source_trees':recipe.get('source_trees',False),'teacher_unchanged':True,'max_abs_gradient':float(np.abs(g).max()),'columns':['new_business','quote_delay','renewal_count','region','channel','payment_method'],'all_learning_fit_only':True}
def predict(bundle,frame,training=True):
 guard(frame,bundle['line'],training=training);f=features(frame,bundle['line']);return old.teacher_rate(bundle['teacher'],f)*np.exp(matrix(f,bundle)@bundle['coef'])
