"""GLM de recuentos/marcas por peril; curvas exteriores existentes."""
from pathlib import Path
import json,joblib,copy,lightgbm as lgb
from .modelos_robustos_compuestos2023 import lgb_frame
import numpy as np,pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler,OneHotEncoder
from sklearn.linear_model import PoissonRegressor,TweedieRegressor
from . import modelos_robustos2023 as base
from .modelo_transferencia2023_v2 import source_guard
from . import c0_estricto2023 as kernel
KEY=base.KEY;guard=base.guard;unit_deviance=base.unit_deviance;metrics=base.metrics
CORE={line:{'numeric':block['numeric'],'categorical':[c for c in block['categorical'] if c!='x_construction_type']}
      for line,block in base.FEATURES.items()}
PERILS={'motor':['bodily_injury','glass_hail','own_damage','theft','third_party_prop'],
        'buildings':['accidental_damage','escape_of_water','fire','flood','storm','subsidence'],
        'contents':['accidental_damage','escape_of_water','flood','theft']}


def features(frame,line):
 return base.features(frame,line)


def train_source(periods,counts,line,parent,checkpoint=None):
 import warnings
 from sklearn.exceptions import ConvergenceWarning
 source_guard(periods,line);f=features(periods,line);before=joblib.hash(parent)
 x=parent['transformer'].transform(f[parent['columns']]);e=f.exposure.to_numpy(float);cols=parent['columns'];cats=[c for c in cols if c in CORE[line]['categorical']];levels={c:sorted(f[c].astype(str).unique().tolist()) for c in cats}
 original={'line':line,'transformer':parent['transformer'],'columns':cols,'models':{p:dict(v) for p,v in parent['models'].items()}}
 robust={'line':line,'transformer':parent['transformer'],'columns':cols,'models':{p:dict(v) for p,v in parent['models'].items()}};receipts=[]
 for peril in PERILS[line]:
  row=f[KEY].merge(counts[counts.peril.eq(peril)],on=KEY,how='left',validate='one_to_one');n=row.N.fillna(0).to_numpy(float);cost=row.T0_cents.fillna(0).to_numpy(float)/100
  a=parent['models'][peril]['frequency'].predict(x)
  est=lgb.LGBMRegressor(objective='poisson',n_estimators=200,learning_rate=.025,num_leaves=8,max_depth=3,min_child_samples=5000,reg_lambda=20.,reg_alpha=1.,max_bin=63,min_data_per_group=100,cat_smooth=50.,deterministic=True,force_col_wise=True,random_state=2026102516,n_jobs=2,verbosity=-1)
  est.fit(lgb_frame(f,cols,levels),n/e,sample_weight=e,init_score=np.log(a),categorical_feature=cats)
  for bundle in [original,robust]:bundle['models'][peril].update(frequency_boost=est,frequency_categories=levels)
  if checkpoint is not None:checkpoint(peril,'frequency_boost',original)
  pos=n>0;base.require(pos.sum()>=20,'Fuente insuficiente para marca');mark=TweedieRegressor(power=1.8,alpha=.1,fit_intercept=True,link='log',solver='lbfgs',max_iter=3000,tol=1e-7)
  with warnings.catch_warnings(record=True) as notes:
   warnings.simplefilter('always');mark.fit(x[pos],cost[pos]/n[pos],sample_weight=n[pos])
  base.require(not any(issubclass(v.category,ConvergenceWarning) for v in notes),'Marca1.8 no converge')
  mu=mark.predict(x[pos]);g=n[pos]*(mu**.2-(cost[pos]/n[pos])*mu**(-.8))/n[pos].sum();grad=np.r_[np.asarray(x[pos].T@g).ravel()+.1*mark.coef_,g.sum()];base.require(np.abs(grad).max()<=1e-4,'Gradiente marca1.8 incorrecto')
  robust['models'][peril].update(severity=mark,constant_mark=None)
  rec={'line':line,'peril':peril,'source_rows':len(f),'reported_claims':int(n.sum()),'claim_periods':int(pos.sum()),'zero_mark_periods_retained':int(((n>0)&(cost==0)).sum()),'source_price_fits':2,'max_mark_gradient':float(np.abs(grad).max()),'frequency_params':est.get_params(),'mark_power':1.8,'mark_alpha':.1};receipts.append(rec)
  if checkpoint is not None:checkpoint(peril,'complete',{'original':original,'robust':robust,'receipt':rec})
 base.require(joblib.hash(parent)==before,'Profesor deperil original alterado')
 return {'W2-COD-R58':original,'W2-COD-R59':robust},receipts

def source_components(source,frame,line):
 f=features(frame,line);x=source['transformer'].transform(f[source['columns']]);result={}
 for peril,obj in source['models'].items():
  freq=obj['frequency'].predict(x)
  if 'frequency_boost' in obj:freq=freq*np.exp(obj['frequency_boost'].predict(lgb_frame(f,source['columns'],obj['frequency_categories']),raw_score=True))
  mark=obj['severity'].predict(x) if obj['severity'] is not None else np.full(len(f),obj['constant_mark'])
  base.require(np.isfinite(freq).all() and (freq>0).all() and np.isfinite(mark).all() and (mark>0).all(),'Componentes inválidos')
  result[peril]=(freq,mark)
 return result


def completion(frame,curve,kind):
 base.require(frame.year.eq(2023).all(),'Curvas retrospectivas solo2023')
 model={**curve,'cost_cdf':curve['cost_cdf']['1.0'] if isinstance(curve['cost_cdf'],dict) else curve['cost_cdf']}
 q=kernel._completion(frame,model,kind)
 # Integración diaria por otro método en tres periodos; el objeto exterior no se reajusta.
 for i in np.unique(np.linspace(0,len(frame)-1,min(3,len(frame)),dtype=int)):
  row=frame.iloc[i];ages=(pd.Timestamp(kernel.VALUATION)-pd.date_range(row.period_start,row.period_end)).days.to_numpy()
  positions=np.searchsorted(model['delay_days'],ages,side='right')-1;arr=np.asarray(model[kind+'_cdf'])
  brute=np.where(positions>=0,arr[np.maximum(positions,0)],0.).mean()
  base.require(abs(float(brute)-q[i])<=1e-12,'Curva no coincide con calendario')
 return q


def adapt(frame,counts,line,held,source,curves,existing_frequency=None):
 guard(frame,line,held);f=features(frame,line);base.require(set(curves)==set(PERILS[line]),'Curvas incompletas')
 comp=source_components(source,f,line);scalars={};receipts=[]
 for peril,(freq,mark) in comp.items():
  row=f[KEY].merge(counts[counts.peril.eq(peril)],on=KEY,how='left',validate='one_to_one')
  observed_N=float(row.N.fillna(0).sum());observed_cost=float(row.T0_cents.fillna(0).sum()/100)
  qn=completion(f,curves[peril],'count');qc=completion(f,curves[peril],'cost');e=f.exposure.to_numpy(float)
  expected_N=float(np.sum(e*qn*freq))
  if existing_frequency is None:freq_factor=(observed_N+20)/(expected_N+20)
  else:
   freq_factor=existing_frequency[peril]['frequency_factor'];base.require(abs(freq_factor-(observed_N+20)/(expected_N+20))<=1e-12,'Frecuencia compartida discrepante')
  avg_mark=float(np.sum(e*freq*mark)/np.sum(e*freq));prior_cost=50*avg_mark
  expected_cost=float(np.sum(e*qc*freq*freq_factor*mark));mark_factor=(observed_cost+prior_cost)/(expected_cost+prior_cost)
  base.require(np.isfinite(freq_factor) and freq_factor>0 and np.isfinite(mark_factor) and mark_factor>0,'Factor inválido')
  scalars[peril]={'frequency_factor':freq_factor,'mark_factor':mark_factor}
  receipts.append({'line':line,'fold':held,'peril':peril,'observed_count':observed_N,'observed_cost':observed_cost,
   'expected_N_before_adapter':expected_N,'expected_cost_after_count_adapter':expected_cost,'prior_count':20,'prior_marks':50,
   'frequency_factor':freq_factor,'mark_factor':mark_factor,'new_closed_form_parameters':2 if existing_frequency is None else 1,'frequency_parameter_reused':existing_frequency is not None,'curve_calendar_checks':6})
 return {'line':line,'held_fold':held,'source':source,'curves':curves,'scalars':scalars},receipts


def predict(bundle,frame,future=False):
 line=bundle['line'];guard(frame,line,training=not future);f=features(frame,line);comp=source_components(bundle['source'],f,line)
 nominal=np.zeros(len(f));observed=np.zeros(len(f));components=[]
 for peril,(freq,mark) in comp.items():
  factors=bundle['scalars'][peril];rate=freq*mark*factors['frequency_factor']*factors['mark_factor']
  qc=np.ones(len(f)) if future else completion(f,bundle['curves'][peril],'cost')
  nominal+=rate;observed+=f.exposure.to_numpy(float)*qc*rate
  components.append({'peril':peril,'nominal_annual_rate':rate,'completion':qc})
 base.require(np.isfinite(observed).all() and (observed>0).all(),'Predicción porperil inválida')
 return observed,nominal,components
