"""GLM sobre bases de riesgo por peril aprendidas en la fuente, sin stack in-sample."""
from pathlib import Path
import numpy as np,pandas as pd,joblib
from scipy import sparse,optimize
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from . import modelo_profesor_comun2023 as old
from . import modelo_peril_frecuencia2023 as perilcore
from .desplegar_robustez2023 import TEACHERS
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
PERIL_SOURCE=R/'privado/semana2/robustez2023/ciclo16_20261025_v1/source_models'
KEY=old.KEY;FEATURES=old.FEATURES;guard=old.guard;features=old.features;metrics=old.metrics;unit_deviance=old.unit_deviance
REFERENCE_PERIL={'motor':'own_damage','buildings':'escape_of_water','contents':'theft'}
def basis(frame,line,joint,peril):
 f=features(frame,line);a=old.teacher_rate(joint,f);parts=perilcore.source_components(peril,f,line);prices={p:freq*mark for p,(freq,mark) in parts.items()};ref=prices[REFERENCE_PERIL[line]]
 values={f'log_{p}_over_{REFERENCE_PERIL[line]}':np.log(rate/ref) for p,rate in prices.items() if p!=REFERENCE_PERIL[line]};values['log_sum_perils_over_joint']=np.log(np.stack(list(prices.values())).sum(axis=0)/a)
 z=pd.DataFrame(values,index=f.index);assert np.isfinite(z.to_numpy()).all();return f,a,z
def matrix(f,z,b):
 zz=b['basis_transform'].transform(z[b['basis_columns']]);columns=[sparse.csr_matrix(f.x_new_business.to_numpy(float)[:,None]),b['region'].transform(f[['x_region']]),sparse.csr_matrix(zz)]
 if b['business_interactions']:columns.append(sparse.csr_matrix(zz*f.x_new_business.to_numpy(float)[:,None]))
 return sparse.hstack(columns+[sparse.csr_matrix(np.ones((len(f),1)))],format='csr')
def fit(frame,line,held,recipe):
 guard(frame,line,held)
 if recipe.get('synthetic'):
  assert frame.row_id.str.startswith('s').all();joint=recipe['_joint'];peril=recipe['_peril']
 else:joint=joblib.load(TEACHERS[line]);peril=joblib.load(PERIL_SOURCE/f'{line}.joblib')['W2-COD-R59']
 before=(joblib.hash(joint),joblib.hash(peril));f,a,z=basis(frame,line,joint,peril)
 tr=Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())]);tr.fit(z)
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);b={'line':line,'model_id':recipe['id'],'held_fold':held,'joint':joint,'peril':peril,'basis_transform':tr,'basis_columns':list(z),'region':enc,'business_interactions':recipe['business_interactions']}
 x=matrix(f,z,b);nc=1+enc.transform(f[['x_region']]).shape[1];n_basis=len(z.columns);pen=np.r_[np.ones(nc),np.full(n_basis,10.),np.full(n_basis,100.) if recipe['business_interactions'] else np.array([]),0.]
 assert len(pen)==x.shape[1];e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);coef=np.zeros(x.shape[1]);coef[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*v
 res=optimize.minimize(objective,coef,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(res.x)
 assert res.success and np.abs(g).max()<=1e-4 and before==(joblib.hash(joint),joblib.hash(peril));b['coef']=res.x
 return b,{'line':line,'fold':held,'model_id':recipe['id'],'fit_rows':len(f),'price_estimator_fits':1,'basis_columns':list(z),'business_interactions':recipe['business_interactions'],'basis_ridge':10.,'interaction_ridge':100.,'max_abs_gradient':float(np.abs(g).max()),'source_states_unchanged':True,'basis_models_never_fit_on_emerging_labels':True}
def predict(b,frame,training=True):
 guard(frame,b['line'],training=training);f,a,z=basis(frame,b['line'],b['joint'],b['peril']);return a*np.exp(matrix(f,z,b)@b['coef'])
