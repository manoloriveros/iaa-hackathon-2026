"""Dos indicadores de faltantes por ramo, contracción10 y profesor inalterado."""
import numpy as np,joblib
from scipy import sparse,optimize
from sklearn.preprocessing import OneHotEncoder
from . import modelo_profesor_comun2023 as old
from .desplegar_robustez2023 import TEACHERS
KEY=old.KEY;FEATURES=old.FEATURES;guard=old.guard;features=old.features;unit_deviance=old.unit_deviance
MISSING={'motor':['x_vehicle_age','x_engine_size_cc'],'buildings':['x_smoke_alarms','x_log_distance_to_river_km'],'contents':['x_high_value_items','x_log_distance_to_river_km']}

def matrix(f,b):
 core=old.adapter_matrix(f,b['region_encoder']);flags=f[MISSING[b['line']]].isna().to_numpy(float)
 return sparse.hstack([core[:,:-1],sparse.csr_matrix(flags),core[:,-1:]],format='csr')

def problem(f,b):
 x=matrix(f,b);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();a=old.teacher_rate(b['teacher'],f);offset=np.log(a);pen=np.r_[np.ones(x.shape[1]-3),10.,10.,0.]
 def objective(c):
  eta=offset+x@c;s=np.exp(eta/2);iv=np.exp(-eta/2);return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*c,c)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*c
 return x,a,y,w,objective

def control(frame,line,held,original):
 guard(frame,line,held);f=features(frame,line);b={'line':line,'held_fold':held,'teacher':original['teacher'],'region_encoder':original['region_encoder'],'coef':np.r_[original['coef'][:-1],0.,0.,original['coef'][-1]]};_,_,y,w,obj=problem(f,b);value,g=obj(b['coef']);p=old.predict(original,f);expected=float(.5*np.dot(w,unit_deviance(y,p))+.5*np.sum(original['coef'][:-1]**2));assert np.isclose(value,expected,rtol=1e-12,atol=1e-10)
 return b,{'line':line,'fold':held,'embedding_price_fits':0,'old_objective':expected,'embedded_objective':value,'objective_equal':True,'new_indicator_gradients_not_required_zero':g[-3:-1].tolist()}

def fit(frame,line,held,recipe):
 guard(frame,line,held);f=features(frame,line)
 if recipe.get('synthetic'):
  assert f.row_id.str.startswith('s').all();teacher=recipe['_teacher']
 else:teacher=joblib.load(TEACHERS[line])
 before=joblib.hash(teacher);enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);b={'line':line,'held_fold':held,'model_id':recipe['id'],'teacher':teacher,'region_encoder':enc,'missing_fields':MISSING[line],'missing_penalty':10.};x,a,y,w,obj=problem(f,b);coef=np.zeros(x.shape[1]);coef[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)));_,g=obj(coef)
 for j in [0,len(coef)-3,len(coef)-1]:
  d=np.zeros(len(coef));d[j]=1e-5;fd=(obj(coef+d)[0]-obj(coef-d)[0])/2e-5;assert np.isclose(g[j],fd,rtol=1e-4,atol=1e-6)
 result=optimize.minimize(obj,coef,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});value,g=obj(result.x);assert result.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before;b['coef']=result.x
 return b,{'line':line,'fold':held,'model_id':recipe['id'],'fit_rows':len(f),'price_estimator_fits':1,'source_fits':0,'new_C0':0,'missing_fields':MISSING[line],'missing_penalty':10.,'fit_missing_rates':f[MISSING[line]].isna().mean().to_dict(),'missing_coefficients':result.x[-3:-1].tolist(),'n_parameters':len(coef),'max_abs_gradient':float(np.abs(g).max()),'finite_difference_checked':True,'objective':value,'teacher_unchanged':True,'all_learning_fit_only':True}

def predict(b,frame):
 guard(frame,b['line']);f=features(frame,b['line']);return old.teacher_rate(b['teacher'],f)*np.exp(matrix(f,b)@b['coef'])
