"""GLM de pendientes compartidas e interceptos propios, fuente2023 explícita."""
from pathlib import Path
import numpy as np,pandas as pd
from scipy import sparse,optimize
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.pipeline import Pipeline
from . import modelos_robustos2023 as base
from .modelos_robustos_compuestos2023 import CORE
FEATURES=CORE;KEY=base.KEY
guard,metrics,unit_deviance=base.guard,base.metrics,base.unit_deviance
ROOT=Path('C:/dev/Hakaton');REPO=ROOT/'Hackaton/Repositorio_IAA2026'


def features(frame,line):
    f=frame.copy()
    for c in CORE[line]['numeric']:
        f[c]=pd.to_numeric(f[c],errors='coerce');base.require(not np.isinf(f[c]).any(),'Predictor infinito')
    for c in CORE[line]['categorical']:f[c]=f[c].astype('string').fillna('__MISSING__').astype(str)
    return f


def source_guard(frame,line):
    base.require(len(frame)>0 and frame.market.eq('developed').all() and frame.line.eq(line).all(),'Fuente de otro mercado/ramo')
    base.require(frame.year.eq(2023).all() and frame.is_test.eq(False).all(),'Fuente no2023')
    base.require(not frame.duplicated(KEY).any(),'Fuente repetida')
    base.require(np.isfinite(frame.exposure).all() and frame.exposure.gt(0).all(),'Exposición fuente inválida')


def design(frame,bundle):
    line=bundle['line'];f=features(frame,line)
    num=bundle['numeric'].transform(f[CORE[line]['numeric']]);cat=bundle['categorical'].transform(f[CORE[line]['categorical']])
    source=f.market.eq('developed').to_numpy(dtype=float)
    return sparse.hstack([sparse.csr_matrix(num),cat,sparse.csr_matrix(np.c_[1-source,source])],format='csr')


def predict(bundle,frame,training=True):
    guard(frame,bundle['line'],training=training)
    eta=design(frame,bundle)@bundle['coef'];rate=np.exp(eta)
    base.require(np.isfinite(rate).all() and (rate>0).all(),'Transferencia no finita')
    return rate


def fit(frame,line,held,recipe):
    guard(frame,line,held);f=features(frame,line)
    if recipe.get('synthetic') is True:
        source=recipe['_source_frame'].copy();base.require(f.row_id.str.startswith('s').all(),'Solo sonda puede pasar fuente en memoria')
    else:
        import pyarrow.parquet as pq
        source=pq.read_table(REPO/f'privado/semana2/robustez2023/fuente_desarrollado2023_v1/{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas()
    source_guard(source,line);source=features(source,line)
    # Las claves se califican por mercado; nunca se unen pólizas o siniestros entre mercados.
    joined=pd.concat([f,source],ignore_index=True)
    numeric=Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('scale',StandardScaler())])
    numeric.fit(f[CORE[line]['numeric']])
    categorical=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,max_categories=40,sparse_output=True)
    categorical.fit(joined[CORE[line]['categorical']])
    b={'model_id':recipe['id'],'line':line,'family':'SharedSlopeTwoMarketGLM','held_fold':held,
       'numeric':numeric,'categorical':categorical,'columns':CORE[line]['numeric']+CORE[line]['categorical'],
       'source_weight':recipe['source_weight'],'source_intercept_is_not_emerging_support':True}
    x=design(joined,b);et=f['e_cost_mix_1.0'].to_numpy(float);es=source.exposure.to_numpy(float)
    yt=f.T0.to_numpy(float)/et;ys=source.T0.to_numpy(float)/es
    wt=np.sqrt(et);ws=np.sqrt(es)
    y=np.r_[yt,ys];w=np.r_[wt/wt.sum(),recipe['source_weight']*ws/ws.sum()]
    beta=np.zeros(x.shape[1]);beta[-2:]=np.log([np.average(yt,weights=wt),np.average(ys,weights=ws)])
    penalty=np.r_[np.ones(x.shape[1]-2),0.,0.]
    def objective(coef):
        eta=x@coef;sqrtmu=np.exp(eta/2);inv=np.exp(-eta/2)
        value=2*np.dot(w,y*inv+sqrtmu-2*np.sqrt(y))+.5*np.dot(penalty*coef,coef)
        gradient=np.asarray(x.T@(w*(sqrtmu-y*inv))).ravel()+penalty*coef
        return float(value),gradient
    result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50})
    value,g=objective(result.x)
    base.require(result.success and np.max(np.abs(g))<=1e-4,'Transferencia no converge: '+str(result.message))
    b['coef']=result.x
    return b,{'line':line,'fold':held,'fit_rows':len(f),'source_rows':len(source),'price_estimator_fits':1,
       'source_weight':recipe['source_weight'],'source_normalized_weight_sum':float(w[len(f):].sum()),'emerging_normalized_weight_sum':float(w[:len(f)].sum()),
       'numeric_transform_fit_on':'emerging outer training rows only','categorical_vocabulary_fit_on':'emerging outer training + developed2023 source',
       'separate_unpenalized_market_intercepts':True,'n_iter':int(result.nit),'objective':value,'max_abs_gradient':float(np.max(np.abs(g))),
       'source_target':'observed net incurred, nominal exposure; level differs freely; no claim of source ultimate identification',
       'emerging_support_not_pooled':True,'success':True}
