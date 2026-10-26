"""Fuente de autos ponderada por atributos de destino; todos los casos permanecen."""
import warnings,numpy as np,joblib,lightgbm as lgb
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from . import modelo_fuente_penalizacion2023 as previous
from . import diagnostico_dominio2023 as domain_model
from .modelos_robustos_compuestos2023 import lgb_frame
old=previous.old;KEY=previous.KEY;FEATURES={'motor':previous.FEATURES['motor']}
guard=previous.guard;features=previous.features;teacher_rate=previous.teacher_rate
fit=previous.fit;predict=previous.predict;unit_deviance=previous.unit_deviance

def weights(frame,domain):
 old.source_guard(frame,'motor');assert domain['line']=='motor'
 before=joblib.hash(domain)
 if domain.get('_synthetic_constant_odds') is not None:
  assert frame.row_id.str.startswith('s_SYNTHETIC_DENSITY_').all()
  raw=np.full(len(frame),domain['_synthetic_constant_odds'],dtype=float)
 else:
  logit,_=domain_model.predict(domain,frame);raw=np.exp(np.clip(logit,-700,700))
 assert joblib.hash(domain)==before
 ratio=np.clip(raw,.2,5.);original=np.sqrt(frame.exposure.to_numpy(float))
 normalizer=float(np.average(ratio,weights=original));w=original*ratio/normalizer
 assert np.isfinite(w).all() and (w>0).all() and np.isclose(w.sum(),original.sum(),rtol=1e-14)
 receipt={'rows':len(frame),'domain_held_fold':domain['held_fold'],'normalizer_fit_only':normalizer,'clipped_fraction':float(np.mean((raw<.2)|(raw>5.))),'combined_weight_ESS_fraction':float(w.sum()**2/np.dot(w,w)/len(w)),'baseline_sqrt_exposure_ESS_fraction':float(original.sum()**2/np.dot(original,original)/len(w)),'all_cases_positive_weight':True,'sum_sqrt_exposure_preserved':True,'weights_joblib_hash':joblib.hash(w),'domain_joblib_hash':before}
 return w,receipt

def fit_source(frame,domain,kind,parent=None):
 old.source_guard(frame,'motor');w,wr=weights(frame,domain);assert wr['combined_weight_ESS_fraction']>=.5
 f=features(frame,'motor');nums=FEATURES['motor']['numeric'];cats=[c for c in FEATURES['motor']['categorical'] if c!='x_region'];cols=nums+cats
 e=f.exposure.to_numpy(float);y=f.T0.to_numpy(float)/e;assert np.isfinite(y).all() and (y>=0).all()
 if kind=='trees':
  assert parent is not None;before=joblib.hash(parent);a=teacher_rate(parent,f);levels={c:sorted(f[c].unique().tolist()) for c in cats}
  est=lgb.LGBMRegressor(objective='tweedie',tweedie_variance_power=1.5,n_estimators=200,learning_rate=.025,num_leaves=8,max_depth=3,min_child_samples=5000,reg_lambda=500.,reg_alpha=100.,max_bin=63,min_data_per_group=100,cat_smooth=50.,deterministic=True,force_col_wise=True,random_state=2026102506,n_jobs=2,verbosity=-1)
  est.fit(lgb_frame(f,cols,levels),y,sample_weight=w,init_score=np.log(a),categorical_feature=cats);assert joblib.hash(parent)==before
  return {'line':'motor','family':'ExtendedSourceTrees','columns':cols,'categories':levels,'parent':parent,'estimator':est},{'line':'motor','kind':kind,'price_estimator_fits':1,'source_rows':len(f),'weights':wr,'params':est.get_params(),'parent_unchanged':True}
 assert kind=='glm'
 tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())]),nums),('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),cats)],sparse_threshold=1.)
 x=tr.fit_transform(f[cols]);est=TweedieRegressor(power=1.5,alpha=1.,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
 with warnings.catch_warnings(record=True) as notes:
  warnings.simplefilter('always');est.fit(x,y,sample_weight=w)
 assert not any(issubclass(n.category,ConvergenceWarning) for n in notes)
 rate=est.predict(x);g=w*(np.sqrt(rate)-y/np.sqrt(rate))/w.sum();gradient=np.r_[np.asarray(x.T@g).ravel()+est.coef_,g.sum()];assert np.abs(gradient).max()<=1e-4
 assert np.allclose(rate,np.exp(x@est.coef_+est.intercept_),rtol=1e-12,atol=1e-9)
 return {'line':'motor','family':'ExtendedSourceGLM','columns':cols,'transformer':tr,'estimator':est},{'line':'motor','kind':kind,'price_estimator_fits':1,'source_rows':len(f),'weights':wr,'max_abs_gradient':float(np.abs(gradient).max()),'manual_exp_prediction_checked':True,'params':est.get_params()}
