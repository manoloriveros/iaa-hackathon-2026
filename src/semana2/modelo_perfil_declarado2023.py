"""Adapta profesores físicos con declaración previa y género opcional."""
from pathlib import Path
import numpy as np,pandas as pd,joblib
from scipy import sparse,optimize
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from . import modelo_profesor_comun2023 as parent
from .modelos_robustos2023 import QuantileClipper
from .desplegar_robustez2023 import TEACHERS
KEY=parent.KEY;guard=parent.guard;metrics=parent.metrics;unit_deviance=parent.unit_deviance;FEATURES=parent.FEATURES


def attach(frame,profiles):
 parent.base.require(profiles.market.eq('emerging').all() and not profiles.duplicated(['market','customer_id']).any(),'Perfil no aislado o repetido')
 out=frame.merge(profiles,on=['market','customer_id'],how='left',validate='many_to_one',indicator=True)
 parent.base.require(out['_merge'].eq('both').all() and len(out)==len(frame),'Perfil sin correspondencia')
 parent.base.require(out.customer_since_year.le(out.year).all(),'Perfil posterior al periodo')
 n=pd.to_numeric(out.x_declared_prior_claims_5y,errors='raise')
 parent.base.require(np.isfinite(n).all() and n.ge(0).all() and n.eq(np.floor(n)).all(),'Declaración de recuento inválida')
 parent.base.require(out.x_declared_gender.isin(['M','F']).all(),'Género distinto del diccionario')
 return out.drop(columns='_merge')


def features(frame,line):
 f=parent.features(frame,line);f['x_log_declared_prior']=np.log1p(pd.to_numeric(f.x_declared_prior_claims_5y))
 f['x_declared_gender']=f.x_declared_gender.astype(str)
 return f


def matrix(f,bundle):
 return sparse.hstack([sparse.csr_matrix(f.x_new_business.to_numpy(float)[:,None]),
  sparse.csr_matrix(bundle['prior_transform'].transform(f[['x_log_declared_prior']])),
  bundle['categorical'].transform(f[bundle['categorical_columns']]),sparse.csr_matrix(np.ones((len(f),1)))],format='csr')


def predict(bundle,frame,training=True):
 guard(frame,bundle['line'],training=training);f=features(frame,bundle['line'])
 return parent.teacher_rate(bundle['teacher'],f)*np.exp(matrix(f,bundle)@bundle['coef'])


def fit(frame,line,held,recipe):
 guard(frame,line,held);f=features(frame,line)
 if recipe.get('synthetic') is True:
  parent.base.require(f.row_id.str.startswith('s').all(),'Profesor en memoria solo sintético');teacher=recipe['_teacher']
 else:teacher=joblib.load(TEACHERS[line])
 original=joblib.hash(teacher);a=parent.teacher_rate(teacher,f)
 prior_transform=Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',QuantileClipper()),('scale',StandardScaler())])
 prior_transform.fit(f[['x_log_declared_prior']])
 cats=['x_region']+(['x_declared_gender'] if recipe['gender'] else [])
 categorical=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,max_categories=40,sparse_output=True);categorical.fit(f[cats])
 bundle={'model_id':recipe['id'],'line':line,'held_fold':held,'teacher':teacher,'prior_transform':prior_transform,'categorical':categorical,'categorical_columns':cats,'gender_used':recipe['gender']}
 x=matrix(f,bundle);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w=w/w.sum();offset=np.log(a)
 beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)));penalty=np.r_[np.ones(x.shape[1]-1),0.]
 def objective(coef):
  eta=offset+x@coef;smu=np.exp(eta/2);inv=np.exp(-eta/2)
  value=2*np.dot(w,y*inv+smu-2*np.sqrt(y))+.5*np.dot(penalty*coef,coef)
  grad=np.asarray(x.T@(w*(smu-y*inv))).ravel()+penalty*coef
  return float(value),grad
 result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50})
 value,g=objective(result.x);parent.base.require(result.success and np.abs(g).max()<=1e-4,'Adaptador perfil no converge')
 parent.base.require(joblib.hash(teacher)==original,'Profesor alterado');bundle['coef']=result.x
 return bundle,{'line':line,'fold':held,'fit_rows':len(f),'price_estimator_fits':1,'gender_used':recipe['gender'],'n_iter':int(result.nit),
  'max_abs_gradient':float(np.abs(g).max()),'objective':value,'prior_raw_fit_range':[float(f.x_declared_prior_claims_5y.min()),float(f.x_declared_prior_claims_5y.max())],
  'prior_clip_log_bounds':[float(prior_transform.named_steps['clip'].lower_[0]),float(prior_transform.named_steps['clip'].upper_[0])],
  'prior_standardized_coefficient':float(result.x[1]),'teacher_state_unchanged':True,'all_profile_learning_fit_only':True,
  'availability':'self-declaration before joining per dictionary; static master not historical capture version'}
