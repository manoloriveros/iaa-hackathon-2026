"""Profesores GLM/aditivo con covariables básicas comunes, adaptación mínima."""
import copy,warnings
import numpy as np,pandas as pd,joblib,lightgbm as lgb
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder,SplineTransformer
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from . import modelo_profesor_comun2023 as old
from .modelos_robustos_compuestos2023 import lgb_frame
KEY=old.KEY;guard=old.guard;metrics=old.metrics;unit_deviance=old.unit_deviance
FEATURES=copy.deepcopy(old.FEATURES)
for block in FEATURES.values():block['categorical'].append('x_urban_density')
for line in ['buildings','contents']:FEATURES[line]['categorical'].append('x_policyholder_age_band')
FEATURES['buildings']['numeric']+=['x_trees_within_5m','x_listed_building']

def attach(frame,extra):
 old.base.require(not extra.duplicated(KEY).any(),'Extras repetidos')
 cols=KEY+[c for c in extra if c.startswith('x_')]
 old.base.require(not set(cols[3:]).intersection(frame.columns),'Covariable sobrescrita')
 out=frame.merge(extra[cols],on=KEY,validate='one_to_one',how='left',indicator=True)
 old.base.require(out['_merge'].eq('both').all() and len(out)==len(frame),'Enlace incompleto')
 return out.drop(columns='_merge')

def features(frame,line):
 f=old.features(frame,line)
 for c in FEATURES[line]['numeric']:f[c]=pd.to_numeric(f[c],errors='coerce')
 for c in FEATURES[line]['categorical']:f[c]=f[c].fillna('__MISSING__').astype(str)
 return f

def teacher_rate(b,frame):
 f=features(frame,b['line'])
 if b['family']=='ExtendedSourceTrees':
  a=teacher_rate(b['parent'],f);r=a*np.exp(b['estimator'].predict(lgb_frame(f,b['columns'],b['categories']),raw_score=True))
 else:r=b['estimator'].predict(b['transformer'].transform(f[b['columns']]))
 old.base.require(np.isfinite(r).all() and (r>0).all(),'Profesor inválido');return r

def fit_source(source,line,kind,parent=None):
 old.source_guard(source,line);f=features(source,line)
 nums=FEATURES[line]['numeric'];cats=[c for c in FEATURES[line]['categorical'] if c!='x_region' and (line!='buildings' or c!='x_construction_type')];cols=nums+cats
 e=f.exposure.to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e)
 if kind=='trees':
  old.base.require(parent is not None,'Falta GLM padre');a=teacher_rate(parent,f);before=joblib.hash(parent)
  levels={c:sorted(f[c].unique().tolist()) for c in cats}
  est=lgb.LGBMRegressor(objective='tweedie',tweedie_variance_power=1.5,n_estimators=200,learning_rate=.025,num_leaves=8,max_depth=3,min_child_samples=5000,reg_lambda=500.,reg_alpha=100.,max_bin=63,min_data_per_group=100,cat_smooth=50.,deterministic=True,force_col_wise=True,random_state=2026102506,n_jobs=2,verbosity=-1)
  est.fit(lgb_frame(f,cols,levels),y,sample_weight=w,init_score=np.log(a),categorical_feature=cats)
  old.base.require(joblib.hash(parent)==before,'Padre alterado')
  return {'line':line,'family':'ExtendedSourceTrees','columns':cols,'categories':levels,'parent':parent,'estimator':est},{'line':line,'kind':kind,'source_rows':len(f),'price_estimator_fits':1,'source_only':True,'params':est.get_params()}
 steps=[('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper())]
 if kind=='gam':steps.append(('basis',SplineTransformer(n_knots=4,degree=2,knots='quantile',include_bias=False,extrapolation='linear')))
 steps.append(('scale',StandardScaler()))
 tr=ColumnTransformer([('numeric',Pipeline(steps),nums),('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),cats)],sparse_threshold=1.)
 x=tr.fit_transform(f[cols]);est=TweedieRegressor(power=1.5,alpha=1.,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
 with warnings.catch_warnings(record=True) as notes:
  warnings.simplefilter('always');est.fit(x,y,sample_weight=w)
 old.base.require(not any(issubclass(n.category,ConvergenceWarning) for n in notes),'Profesor no converge')
 a=est.predict(x);g=w*(np.sqrt(a)-y/np.sqrt(a))/w.sum();grad=np.r_[np.asarray(x.T@g).ravel()+est.coef_,g.sum()]
 old.base.require(np.abs(grad).max()<=1e-4,'Gradiente inválido')
 return {'line':line,'family':'ExtendedSourceGAM' if kind=='gam' else 'ExtendedSourceGLM','columns':cols,'transformer':tr,'estimator':est},{'line':line,'kind':kind,'source_rows':len(f),'price_estimator_fits':1,'source_only':True,'max_abs_gradient':float(np.abs(grad).max()),'params':est.get_params()}

def fit(frame,line,held,teacher,model_id):
 from scipy import optimize
 guard(frame,line,held);f=features(frame,line);before=joblib.hash(teacher);a=teacher_rate(teacher,f)
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);x=old.adapter_matrix(f,enc)
 e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a)
 beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)));penalty=np.r_[np.ones(x.shape[1]-1),0.]
 def objective(b):
  eta=offset+x@b;s=np.exp(eta/2);inv=np.exp(-eta/2)
  return float(2*np.dot(w,y*inv+s-2*np.sqrt(y))+.5*np.dot(penalty*b,b)),np.asarray(x.T@(w*(s-y*inv))).ravel()+penalty*b
 res=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,grad=objective(res.x)
 old.base.require(res.success and np.abs(grad).max()<=1e-4 and joblib.hash(teacher)==before,'Adaptador inválido')
 return {'line':line,'model_id':model_id,'held_fold':held,'teacher':teacher,'region_encoder':enc,'coef':res.x},{'line':line,'model_id':model_id,'fold':held,'fit_rows':len(f),'price_estimator_fits':1,'max_abs_gradient':float(np.abs(grad).max()),'teacher_state_unchanged':True}

def predict(bundle,frame,training=True):
 guard(frame,bundle['line'],training=training);f=features(frame,bundle['line'])
 return teacher_rate(bundle['teacher'],f)*np.exp(old.adapter_matrix(f,bundle['region_encoder'])@bundle['coef'])
