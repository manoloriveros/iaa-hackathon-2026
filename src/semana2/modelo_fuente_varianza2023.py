"""GLM de fuente con varianza de trabajo1,8; evaluación y destino siguen1,5."""
import warnings,numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_tweedie_deviance
from . import modelo_fuente_penalizacion2023 as previous
old=previous.old;KEY=previous.KEY;FEATURES={'motor':previous.FEATURES['motor']}
guard=previous.guard;features=previous.features;teacher_rate=previous.teacher_rate
unit_deviance=previous.unit_deviance;fit=previous.fit;predict=previous.predict
POWER=1.8

def fit_source(frame,line,kind,parent=None):
 assert line=='motor'
 if kind=='trees':return previous.fit_source(frame,line,kind,parent=parent)
 assert kind=='glm';old.source_guard(frame,line);f=features(frame,line)
 nums=FEATURES[line]['numeric'];cats=[c for c in FEATURES[line]['categorical'] if c!='x_region'];cols=nums+cats
 tr=ColumnTransformer([('numeric',Pipeline([('median',SimpleImputer(strategy='median',keep_empty_features=True)),('clip',old.base.QuantileClipper()),('scale',StandardScaler())]),nums),('categorical',OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=100,max_categories=40,sparse_output=True),cats)],sparse_threshold=1.)
 x=tr.fit_transform(f[cols]);e=f.exposure.to_numpy(float);y=f.T0.to_numpy(float)/e;w=e**(2-POWER);anchor=float(f.T0.sum()/e.sum());assert anchor>0
 # Match expected local curvature of the original p1.5 loss at a fit-only constant mean.
 alpha=anchor**(1.5-POWER)
 est=TweedieRegressor(power=POWER,alpha=alpha,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
 with warnings.catch_warnings(record=True) as notes:
  warnings.simplefilter('always');est.fit(x,y,sample_weight=w)
 assert not any(issubclass(n.category,ConvergenceWarning) for n in notes)
 rate=est.predict(x);v=w*(rate**(2-POWER)-y*rate**(1-POWER))/w.sum();gradient=np.r_[np.asarray(x.T@v).ravel()+alpha*est.coef_,v.sum()];assert np.abs(gradient).max()<=1e-4
 assert np.allclose(rate,np.exp(x@est.coef_+est.intercept_),rtol=1e-12,atol=1e-9)
 # Independent library-deviance finite differences on the fitted objective.
 coef=np.r_[est.coef_,est.intercept_]
 def obj(c):
  mu=np.exp(x@c[:-1]+c[-1]);return .5*mean_tweedie_deviance(y,mu,sample_weight=w,power=POWER)+.5*alpha*np.dot(c[:-1],c[:-1])
 errors=[]
 for j in sorted(set([0,len(coef)//2,len(coef)-1])):
  d=np.zeros(len(coef));d[j]=1e-5;fd=(obj(coef+d)-obj(coef-d))/2e-5;errors.append(abs(fd-gradient[j]));assert np.isclose(fd,gradient[j],rtol=1e-3,atol=1e-6)
 return {'line':line,'family':'ExtendedSourceGLM','columns':cols,'transformer':tr,'estimator':est}, {'line':line,'kind':'source_working_variance_GLM','source_rows':len(f),'price_estimator_fits':1,'working_power':POWER,'exposure_weight_power':2-POWER,'anchor_fit_only_annual_mean':anchor,'alpha_effective':alpha,'alpha_formula':'1*anchor**(1.5-1.8)','max_abs_gradient':float(np.abs(gradient).max()),'max_finite_difference_error':float(max(errors)),'params':est.get_params(),'all_losses_retained':True}
