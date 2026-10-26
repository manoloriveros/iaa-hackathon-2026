"""Edad fina fuente y media condicional de tarifas al observar solo una banda."""
import copy,warnings
import numpy as np,pandas as pd,joblib,lightgbm as lgb
from scipy import sparse,optimize
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder,SplineTransformer
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from . import modelo_profesor_comun2023 as old
from .modelos_robustos_compuestos2023 import lgb_frame
KEY=old.KEY;FEATURES=old.FEATURES;features=old.features;guard=old.guard;metrics=old.metrics;unit_deviance=old.unit_deviance
BANDS=['17-24','25-34','35-49','50-64','65+']
LICENSE_BINS=[-np.inf,1,4,9,19,39,np.inf]
def licence_cell(f,line):
 if line!='motor':return np.full(len(f),'all',dtype=object)
 raw=pd.to_numeric(f.x_years_licensed,errors='coerce');out=pd.cut(raw,LICENSE_BINS,labels=False).astype('Int64').astype('string').fillna('unknown').to_numpy();return out
def fit_density(source,line):
 old.source_guard(source,line);age=pd.to_numeric(source.x_exact_age);band=source.x_transport_band.astype(str);cell=licence_cell(source,line);e=source.exposure.to_numpy(float)
 assert np.isfinite(age).all() and age.eq(np.floor(age)).all() and band.isin(BANDS).all();tables={}
 for name in BANDS:
  support=np.sort(age[band.eq(name)].unique()).astype(float);assert len(support)>0
  global_weights=np.array([e[(band.eq(name)&age.eq(a)).to_numpy()].sum() for a in support]);global_p=(global_weights+20/len(support))/(global_weights.sum()+20)
  tables[name]={'ages':support,'fallback_probabilities':global_p,'cells':{}}
  for label in np.unique(cell[band.eq(name)]):
   weights=np.array([e[(band.eq(name)&age.eq(a)).to_numpy()&(cell==label)].sum() for a in support]);p=(weights+20*global_p)/(weights.sum()+20)
   tables[name]['cells'][str(label)]=p
 return {'line':line,'tables':tables,'fit_rows':len(source),'prior_exposure_years':20.,'weights':'source nominal exposure;no outcomes used','source_only':True}
def train_source(source,line,include_trees=True):
 old.source_guard(source,line);f=features(source,line);f['x_exact_age']=pd.to_numeric(f.x_exact_age);nums=FEATURES[line]['numeric'];cats=[c for c in FEATURES[line]['categorical'] if c!='x_region' and (line!='buildings' or c!='x_construction_type')];cols=nums+cats+['x_exact_age']
 tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())]),nums),
  ('age',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('spline',SplineTransformer(n_knots=6,degree=2,knots='quantile',include_bias=False,extrapolation='constant')),('scale',StandardScaler())]),['x_exact_age']),
  ('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),cats)],sparse_threshold=1.)
 x=tr.fit_transform(f[cols]);e=f.exposure.to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);est=TweedieRegressor(power=1.5,alpha=1.,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
 with warnings.catch_warnings(record=True) as notes:
  warnings.simplefilter('always');est.fit(x,y,sample_weight=w)
 assert not any(issubclass(n.category,ConvergenceWarning) for n in notes);a=est.predict(x);g=w*(np.sqrt(a)-y/np.sqrt(a))/w.sum();grad=np.r_[np.asarray(x.T@g).ravel()+est.coef_,g.sum()];assert np.abs(grad).max()<=1e-4
 plain={'line':line,'family':'FineAgeGLM','columns':cols,'transformer':tr,'estimator':est};levels={c:sorted(f[c].astype(str).unique().tolist()) for c in cats}
 density=fit_density(source,line);result={'glm':{'line':line,'price':plain,'density':density}};boost=None
 if include_trees:
  boost=lgb.LGBMRegressor(objective='tweedie',tweedie_variance_power=1.5,n_estimators=200,learning_rate=.025,num_leaves=8,max_depth=3,min_child_samples=5000,reg_lambda=500.,reg_alpha=100.,max_bin=63,min_data_per_group=100,cat_smooth=50.,deterministic=True,force_col_wise=True,random_state=2026102506,n_jobs=2,verbosity=-1)
  boost.fit(lgb_frame(f,cols,levels),y,sample_weight=w,init_score=np.log(a),categorical_feature=cats);curved={'line':line,'family':'FineAgeTrees','columns':cols,'categories':levels,'parent':plain,'estimator':boost};result['trees']={'line':line,'price':curved,'density':density}
 rec={'line':line,'source_rows':len(f),'price_estimator_fits':1+int(include_trees),'max_GLM_gradient':float(np.abs(grad).max()),'source_exact_age_used_only_in_source_fit':True,'age_spline_knots':6,'density_fit_rows':len(f),'density_uses_no_outcomes':True,'price_params':est.get_params(),'tree_params':boost.get_params() if boost is not None else None}
 return result,rec
def fine_rate(price,frame):
 f=features(frame,price['line'])
 if price['family']=='FineAgeGLM':out=price['estimator'].predict(price['transformer'].transform(f[price['columns']]))
 else:out=fine_rate(price['parent'],f)*np.exp(price['estimator'].predict(lgb_frame(f,price['columns'],price['categories']),raw_score=True))
 assert np.isfinite(out).all() and (out>0).all();return out
def marginal_rate(teacher,frame,stress=False):
 line=teacher['line'];f=features(frame,line).reset_index(drop=True);band=f.x_transport_band.astype(str);assert band.isin(BANDS).all();cells=licence_cell(f,line);result=np.zeros(len(f));total=np.zeros(len(f))
 for name,tab in teacher['density']['tables'].items():
  indices=np.flatnonzero(band.eq(name));
  if len(indices)==0:continue
  sub=f.iloc[indices].copy();probs=np.stack([tab['cells'].get(str(c),tab['fallback_probabilities']) for c in cells[indices]])
  if stress:probs=.5*probs+.5*tab['fallback_probabilities'][None,:]
  # No assumed legal licensing age. The field only supplies its empirical source conditioning.
  for j,a in enumerate(tab['ages']):
   row=sub.copy();row['x_exact_age']=a;rate=fine_rate(teacher['price'],row);result[indices]+=probs[:,j]*rate;total[indices]+=probs[:,j]
 assert np.allclose(total,1.,rtol=0,atol=1e-12) and np.isfinite(result).all() and (result>0).all();return result
def fit(frame,line,held,teacher,model_id):
 guard(frame,line,held);f=features(frame,line);before=joblib.hash(teacher);a=marginal_rate(teacher,f)
 enc=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);enc.fit(f[['x_region']]);x=old.adapter_matrix(f,enc);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w/=w.sum();offset=np.log(a);pen=np.r_[np.ones(x.shape[1]-1),0.];beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
 def objective(v):
  eta=offset+x@v;s=np.exp(eta/2);iv=np.exp(-eta/2)
  return float(2*np.dot(w,y*iv+s-2*np.sqrt(y))+.5*np.dot(pen*v,v)),np.asarray(x.T@(w*(s-y*iv))).ravel()+pen*v
 res=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50});_,g=objective(res.x);assert res.success and np.abs(g).max()<=1e-4 and joblib.hash(teacher)==before
 return {'line':line,'held_fold':held,'model_id':model_id,'teacher':teacher,'region_encoder':enc,'coef':res.x},{'line':line,'fold':held,'model_id':model_id,'fit_rows':len(f),'price_estimator_fits':1,'max_abs_gradient':float(np.abs(g).max()),'source_density_and_price_unchanged':True,'unknown_target_age_marginalized':True}
def predict(b,frame,training=True,stress=False):
 guard(frame,b['line'],training=training);f=features(frame,b['line']);return marginal_rate(b['teacher'],f,stress=stress)*np.exp(old.adapter_matrix(f,b['region_encoder'])@b['coef'])
