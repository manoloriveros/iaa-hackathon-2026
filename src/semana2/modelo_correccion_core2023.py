"""Corrección estándar de siete efectos o bloque físico hacia profesor congelado."""
import numpy as np,joblib
from scipy import sparse,optimize
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from . import modelo_profesor_comun2023 as old
from .desplegar_robustez2023 import TEACHERS
KEY=old.KEY;FEATURES=old.FEATURES;guard=old.guard;features=old.features;metrics=old.metrics;unit_deviance=old.unit_deviance
CORE={'motor':{'numeric':['x_new_business','x_ncb_years','x_vehicle_age','x_vehicle_value_group'],'categorical':['x_driver_age_band','x_region','x_cover_type']},'buildings':{'numeric':['x_new_business','x_log_sum_insured','x_property_age','x_flood_zone','x_accidental_damage_cover'],'categorical':['x_property_type','x_region']},'contents':{'numeric':['x_new_business','x_log_sum_insured','x_bedrooms','x_high_value_items','x_accidental_damage_cover'],'categorical':['x_property_type','x_region']}}
def matrix(f,b):
 x=b['transformer'].transform(f[b['columns']]);return sparse.hstack([sparse.csr_matrix(x),sparse.csr_matrix(np.ones((len(f),1)))],format='csr')
def fit(frame,line,held,recipe):
 guard(frame,line,held);f=features(frame,line)
 if recipe.get('synthetic'):
  assert f.row_id.str.startswith('s').all();teacher=recipe['_teacher']
 else:teacher=joblib.load(TEACHERS[line])
 before=joblib.hash(teacher);a=old.teacher_rate(teacher,f);block=CORE[line] if recipe['block']=='core7' else FEATURES[line];nums=block['numeric'];cats=block['categorical'];cols=nums+cats
 tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())]),nums),('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),cats)],sparse_threshold=1.);tr.fit(f[cols]);b={'line':line,'held_fold':held,'model_id':recipe['id'],'block':recipe['block'],'teacher':teacher,'transformer':tr,'columns':cols};x=matrix(f,b);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);pen=np.r_[np.ones(x.shape[1]-1),0.];coef=np.zeros(x.shape[1]);coef[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2);return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*v
 res=optimize.minimize(objective,coef,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});value,g=objective(res.x);assert res.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before;b['coef']=res.x
 return b,{'line':line,'fold':held,'model_id':recipe['id'],'block':recipe['block'],'alpha':1.,'fit_rows':len(f),'n_parameters':len(res.x),'price_estimator_fits':1,'teacher_unchanged':True,'max_abs_gradient':float(np.abs(g).max()),'objective':value,'n_iter':int(res.nit),'all_learning_fit_only':True}
def predict(b,frame,training=True):
 guard(frame,b['line'],training=training);f=features(frame,b['line']);return old.teacher_rate(b['teacher'],f)*np.exp(matrix(f,b)@b['coef'])
