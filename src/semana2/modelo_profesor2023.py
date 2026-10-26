"""Forma aprendida exclusivamente de fuente2023 y adaptación estándar externa."""
from pathlib import Path
import numpy as np,pandas as pd,joblib,lightgbm as lgb
from scipy import sparse,optimize
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import TweedieRegressor
from . import modelos_robustos2023 as base
from .modelo_transferencia2023_v2 import source_guard
from .modelos_robustos_compuestos2023 import lgb_frame
FEATURES,KEY=base.FEATURES,base.KEY
guard,features,metrics,unit_deviance=base.guard,base.features,base.metrics,base.unit_deviance
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=R/'privado/semana2/robustez2023/ciclo6_20261025_v1'


def teacher_rate(b,frame):
    f=features(frame,b['line'])
    if b['family']=='SourceGLM':
        rate=b['estimator'].predict(b['transformer'].transform(f[b['columns']]))
    else:
        a=teacher_rate(b['parent'],f)
        rate=a*np.exp(b['estimator'].predict(lgb_frame(f,b['columns'],b['categories']),raw_score=True))
    base.require(np.isfinite(rate).all() and (rate>0).all(),'Profesor no finito')
    return rate


def fit_teachers(source,line):
    import warnings
    from sklearn.exceptions import ConvergenceWarning
    source_guard(source,line);f=features(source,line)
    numeric=FEATURES[line]['numeric'];categorical=[c for c in FEATURES[line]['categorical'] if c!='x_region'];cols=numeric+categorical
    tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',base.QuantileClipper()),('scale',StandardScaler())]),numeric),
        ('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),categorical)],sparse_threshold=1.)
    x=tr.fit_transform(f[cols]);e=f.exposure.to_numpy(float);y=f.T0.to_numpy()/e;w=np.sqrt(e)
    est=TweedieRegressor(power=1.5,alpha=1.,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always');est.fit(x,y,sample_weight=w)
    base.require(not any(issubclass(n.category,ConvergenceWarning) for n in notes),'ProfesorGLM no convergió')
    a=est.predict(x);g=w*(np.sqrt(a)-y/np.sqrt(a))/w.sum();score=np.r_[np.asarray(x.T@g).ravel()+est.coef_,g.sum()]
    base.require(np.abs(score).max()<=1e-4,'Gradiente profesor inválido')
    plain={'line':line,'family':'SourceGLM','columns':cols,'transformer':tr,'estimator':est}
    levels={c:sorted(f[c].astype(str).unique().tolist()) for c in categorical}
    boost=lgb.LGBMRegressor(objective='tweedie',tweedie_variance_power=1.5,n_estimators=200,learning_rate=.025,
        num_leaves=8,max_depth=3,min_child_samples=5000,reg_lambda=500.,reg_alpha=100.,max_bin=63,
        min_data_per_group=100,cat_smooth=50.,deterministic=True,force_col_wise=True,random_state=2026102506,n_jobs=2,verbosity=-1)
    boost.fit(lgb_frame(f,cols,levels),y,sample_weight=w,init_score=np.log(a),categorical_feature=categorical)
    curved={'line':line,'family':'SourceResidualTrees','columns':cols,'categories':levels,'parent':plain,'estimator':boost}
    receipt={'line':line,'source_rows':len(f),'source_fits':2,'source_GLM_max_gradient':float(np.abs(score).max()),'source_GLM_params':est.get_params(),
        'source_boost_params':boost.get_params(),'source_boost_trees':boost.booster_.num_trees(),'excluded_region_transport':True,
        'source_target':'observed2023 incurred/nominal exposure; target-only level adapter; no ultimate/source comparability claim'}
    return {'W2-COD-R31':plain,'W2-COD-R32':curved},receipt


def adapter_matrix(frame,encoder):
    return sparse.hstack([sparse.csr_matrix(frame.x_new_business.to_numpy(float)[:,None]),encoder.transform(frame[['x_region']]),
                         sparse.csr_matrix(np.ones((len(frame),1)))],format='csr')


def predict(bundle,frame,training=True):
    guard(frame,bundle['line'],training=training);f=features(frame,bundle['line'])
    return teacher_rate(bundle['teacher'],f)*np.exp(adapter_matrix(f,bundle['region_encoder'])@bundle['coef'])


def fit(frame,line,held,recipe):
    guard(frame,line,held);f=features(frame,line)
    if recipe.get('synthetic') is True:
        base.require(f.row_id.str.startswith('s').all(),'Profesor en memoria solo para sonda')
        teacher=recipe['_teacher']
    else:teacher=joblib.load(RUN/f'teachers/{recipe["id"]}_{line}.joblib')
    original=joblib.hash(teacher);a=teacher_rate(teacher,f)
    encoder=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);encoder.fit(f[['x_region']])
    x=adapter_matrix(f,encoder);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w=w/w.sum()
    offset=np.log(a);beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
    penalty=np.r_[np.ones(x.shape[1]-1),0.]
    def objective(coef):
        eta=offset+x@coef;smu=np.exp(eta/2);inv=np.exp(-eta/2)
        loss=2*np.dot(w,y*inv+smu-2*np.sqrt(y))+.5*np.dot(penalty*coef,coef)
        grad=np.asarray(x.T@(w*(smu-y*inv))).ravel()+penalty*coef
        return float(loss),grad
    result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50})
    value,g=objective(result.x);base.require(result.success and np.abs(g).max()<=1e-4,'Adaptador no convergió')
    base.require(joblib.hash(teacher)==original,'Profesor fue alterado')
    return ({'model_id':recipe['id'],'line':line,'held_fold':held,'teacher':teacher,'region_encoder':encoder,'coef':result.x},
           {'line':line,'fold':held,'fit_rows':len(f),'price_estimator_fits':1,'teacher_state_unchanged':True,
            'n_iter':int(result.nit),'max_abs_gradient':float(np.abs(g).max()),'adapter_columns':'intercept free + new_business + region ridge1',
            'teacher_shape_learned_without_emerging_labels':True,'objective':value})
