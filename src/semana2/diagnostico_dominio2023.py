"""Clasificación de mercados por atributos, sin costes, C0, exposición o precios."""
import warnings,numpy as np,pandas as pd
from scipy.special import expit
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from . import modelos_robustos2023 as physical
KEY=physical.KEY

def block(line):
 return {'numeric':physical.FEATURES[line]['numeric'],'categorical':[c for c in physical.FEATURES[line]['categorical'] if c!='x_region' and (line!='buildings' or c!='x_construction_type')]}

def columns(line):
 b=block(line);return b['numeric']+b['categorical']

def guard(f,line,held=None):
 assert len(f)>0 and f.line.eq(line).all() and f.market.isin(['developed','emerging']).all() and f.year.eq(2023).all() and f.is_test.eq(False).all() and not f.duplicated(KEY).any()
 if held is not None:assert f.fold.ne(held).all()

def attrs(f,line):
 # Explicit allow-list drops labels and identifiers even if a caller supplies them.
 out=f[columns(line)].copy();b=block(line)
 for c in b['numeric']:
  out[c]=pd.to_numeric(out[c],errors='coerce');assert not np.isinf(out[c]).any()
 for c in b['categorical']:out[c]=out[c].astype('string').fillna('__MISSING__').astype(str)
 return out

def predict(b,f):
 guard(f,b['line']);x=b['transformer'].transform(attrs(f,b['line']));logit=b['estimator'].decision_function(x);prob=b['estimator'].predict_proba(x)[:,1]
 assert np.allclose(prob,expit(logit),rtol=1e-14,atol=1e-15)
 return logit,prob

def fit(f,line,held):
 guard(f,line,held);assert set(f.market)=={'developed','emerging'};b=block(line)
 tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True,add_indicator=True)),('clip',physical.QuantileClipper()),('scale',StandardScaler())]),b['numeric']),('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),b['categorical'])],sparse_threshold=1.)
 x=tr.fit_transform(attrs(f,line));y=f.market.eq('emerging').to_numpy(int);n=len(y)
 est=LogisticRegression(C=1.,solver='lbfgs',class_weight='balanced',max_iter=1500,tol=1e-7,random_state=2026102534)
 with warnings.catch_warnings(record=True) as notes:
  warnings.simplefilter('always');est.fit(x,y)
 assert not any(issubclass(z.category,ConvergenceWarning) for z in notes)
 prob=expit(est.decision_function(x));w=np.where(y,n/(2*y.sum()),n/(2*(n-y.sum())));g=np.r_[(np.asarray(x.T@(w*(prob-y))).ravel()+est.coef_.ravel()/est.C)/n,np.sum(w*(prob-y))/n];assert np.abs(g).max()<=1e-4
 return {'line':line,'held_fold':held,'transformer':tr,'estimator':est,'columns':columns(line)}, {'line':line,'fold':held,'diagnostic_classifier_fits':1,'price_fits':0,'rows_by_market':f.groupby('market').size().to_dict(),'n_parameters':x.shape[1]+1,'max_abs_normalized_gradient':float(np.abs(g).max()),'n_iter':est.n_iter_.tolist(),'params':est.get_params(),'outcome_cost_C0_exposure_not_inputs':True}
