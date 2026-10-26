"""GLM conjunto con contraste regional penalizado; dimensión de dos GLM independientes."""
import numpy as np,pandas as pd,joblib
from scipy import sparse,optimize
from sklearn.preprocessing import OneHotEncoder
from . import modelo_fuente_mascarada2023 as core
KEY=core.KEY;HOMES=['buildings','contents'];unit_deviance=core.unit_deviance

def guard(f,held=None,training=True):
 assert len(f)>0 and f.market.eq('emerging').all() and f.line.isin(HOMES).all() and f.year.eq(2023 if training else 2025).all() and f.is_test.eq(not training).all() and not f.duplicated(KEY).any()
 assert f.x_new_business.isin([0.,1.]).all()
 if held is not None:assert f.fold.ne(held).all()

def rates(teachers,f):
 result=np.zeros(len(f))
 for line in HOMES:
  chosen=f.line.eq(line).to_numpy()
  if chosen.any():result[chosen]=core.teacher_rate(teachers[line],f.loc[chosen])
 assert np.isfinite(result).all() and (result>0).all();return result

def matrix(f,enc):
 b=f.line.eq('buildings').to_numpy(float);c=1-b;nb=f.x_new_business.to_numpy(float);reg=enc.transform(f[['x_region']]);sign=b-c
 return sparse.hstack([sparse.csr_matrix(np.c_[nb*b,nb*c]),reg,sparse.diags(sign)@reg,sparse.csr_matrix(np.c_[b,c])],format='csr')

def problem(f,b,tau):
 x=matrix(f,b['region_encoder']);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e)
 for line in HOMES:
  chosen=f.line.eq(line).to_numpy();assert chosen.any();w[chosen]/=w[chosen].sum()
 assert abs(w.sum()-2)<1e-12;a=rates(b['teachers'],f);offset=np.log(a);k=b['region_encoder'].transform(f[['x_region']]).shape[1];penalty=np.r_[1.,1.,np.full(k,2.),np.full(k,tau),0.,0.]
 assert len(penalty)==x.shape[1]
 def objective(coef):
  eta=offset+x@coef;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(penalty*coef,coef)),np.asarray(x.T@(w*(s-y*iv))).ravel()+penalty*coef
 return x,y,w,a,objective

def structure(f,teachers):
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);return {'teachers':teachers,'region_encoder':enc}

def control(f,teachers,old_models,held):
 guard(f,held);b=structure(f,teachers);names=list(b['region_encoder'].get_feature_names_out())
 for line in HOMES:
  assert names==list(old_models[line]['region_encoder'].get_feature_names_out());assert joblib.hash(teachers[line])==joblib.hash(old_models[line]['teacher'])
 left=old_models['buildings']['coef'];right=old_models['contents']['coef'];coef=np.r_[left[0],right[0],(left[1:-1]+right[1:-1])/2,(left[1:-1]-right[1:-1])/2,left[-1],right[-1]];b.update(coef=coef,tau=2.,model_id='UNCHANGED_BASELINE_COORDINATES',held_fold=held)
 _,_,_,_,objective=problem(f,b,2.);value,g=objective(coef);assert np.abs(g).max()<=2.1e-4
 # Independent sum of the original two GLM objectives and their ridge penalties.
 old_objective=0.
 for line in HOMES:
  part=f[f.line.eq(line)];model=old_models[line];p=core.predict(model,part);e=part['e_cost_mix_1.0'].to_numpy(float);w=np.sqrt(e);w/=w.sum();old_objective+=float(.5*np.dot(w,unit_deviance(part.T0.to_numpy()/e,p))+.5*np.sum(model['coef'][:-1]**2))
 assert abs(value-old_objective)<=1e-9*max(1.,abs(value));return b,{'held_fold':held,'tau2_matches_independent_GLMS_without_fit':True,'objective_value':value,'separate_objective_value':old_objective,'max_mapped_gradient':float(np.abs(g).max()),'price_estimator_fits':0}

def fit(f,teachers,held,recipe):
 guard(f,held);before=joblib.hash(teachers);b=structure(f,teachers);x,y,w,a,objective=problem(f,b,recipe['tau']);coef=np.zeros(x.shape[1])
 for j,line in enumerate(HOMES):
  chosen=f.line.eq(line).to_numpy();coef[-2+j]=np.log(np.sum(w[chosen]*y[chosen]/np.sqrt(a[chosen]))/np.sum(w[chosen]*np.sqrt(a[chosen])))
 _,g=objective(coef);fd=[]
 for j in range(len(coef)):
  d=np.zeros(len(coef));d[j]=1e-5;fd.append((objective(coef+d)[0]-objective(coef-d)[0])/2e-5)
 assert np.allclose(g,fd,rtol=1e-4,atol=1e-6)
 res=optimize.minimize(objective,coef,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});value,g=objective(res.x);assert res.success and np.abs(g).max()<=1e-4 and joblib.hash(teachers)==before;b.update(coef=res.x,tau=recipe['tau'],model_id=recipe['id'],held_fold=held)
 return b,{'fold':held,'model_id':recipe['id'],'rows':len(f),'rows_by_line':f.groupby('line').size().to_dict(),'tau':recipe['tau'],'price_estimator_fits':1,'source_fits':0,'new_C0':0,'max_abs_gradient':float(np.abs(g).max()),'finite_difference_gradient':True,'teachers_unchanged':True,'all_learning_fit_only':True,'objective':value,'n_parameters':len(coef)}

def predict(b,f,training=True):
 guard(f,training=training);return rates(b['teachers'],f)*np.exp(matrix(f,b['region_encoder'])@b['coef'])
