"""Una nueva hipótesis de recuentos/marcas por peril, comparada con R36."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,argparse,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_peril2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
from sklearn.metrics import mean_poisson_deviance,mean_tweedie_deviance
OUT=R/'privado/semana2/robustez2023/ciclo8_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo8_plan.json'
SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1'
COUNTS=R/'privado/semana2/robustez2023/recuentos_peril2023_v2'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023'
REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet'
OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
OBS=R/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766'
CLAIMS=R/'privado/semana2/desarrollo2023/coberturas_20261024T011932Z_14b50ca9/inputs_2023'
FID='COD-S2-20261025-ROBUSTEZ8-PREVIO'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()
def dump(p,o):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(p):
 for x in p['sources']:assert sha(ROOT/x['path'])==x['sha256'],x['path']
def event(name,**kw):
 obj={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(obj)+'\n')
 print(json.dumps(obj),flush=True)
class FakeMatrix:
 def transform(self,f):return np.zeros((len(f),1))
class FakeFrequency:
 def predict(self,x):return np.full(len(x),.1)


def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
 n=400;rng=np.random.default_rng(2026102509);line='motor'
 f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'period_start':pd.Timestamp('2023-01-01'),'period_end':pd.Timestamp('2023-12-31'),'exposure':1.})
 for c in m.base.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 f['x_new_business']=(np.arange(n)%2).astype(float)
 for c in m.base.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 cc=[]
 for peril in m.PERILS[line]:
  x=f[m.KEY].copy();x['peril']=peril;x['N']=rng.poisson(.1,n);x['T0_cents']=x.N*100000;cc.append(x)
 counts=pd.concat(cc,ignore_index=True)
 source={'line':line,'transformer':FakeMatrix(),'columns':['x_new_business'],'models':{p:{'frequency':FakeFrequency(),'severity':None,'constant_mark':1000.} for p in m.PERILS[line]}}
 curves={p:{'delay_days':[0,450,900],'count_cdf':[.1,.7,1.],'cost_cdf':{'1.0':[.05,.6,1.]}} for p in m.PERILS[line]}
 train=f[f.fold.ne(0)].copy();valid=f[f.fold.eq(0)].copy()
 b,receipt=m.adapt(train,counts,line,0,source,curves)
 poison=counts.copy();poison.loc[poison.row_id.isin(valid.row_id),'T0_cents']=10**14;poison.loc[poison.row_id.isin(valid.row_id),'N']=10**8
 b2,_=m.adapt(train,poison,line,0,source,curves);assert b['scalars']==b2['scalars']
 p,nom,comp=m.predict(b,valid);assert np.isclose(m.unit_deviance(np.ones(len(p))*100,p).sum(),mean_tweedie_deviance(np.ones(len(p))*100,p,power=1.5)*len(p),rtol=1e-12)
 future=valid.assign(year=2025,is_test=True,period_start=pd.Timestamp('2025-01-01'),period_end=pd.Timestamp('2025-12-31'));fp,fn,_=m.predict(b,future,future=True);assert np.array_equal(fp,fn*future.exposure)
 e=np.r_[.1,.5,1.];num=np.r_[0.,1.,5.];rate=np.r_[1.,3.,4.]
 assert np.isclose(mean_poisson_deviance(num,e*rate)*3,mean_poisson_deviance(num/e,rate,sample_weight=e)*e.sum(),rtol=1e-12)
 try:m.adapt(train.assign(year=2024),counts,line,0,source,curves)
 except AssertionError:pass
 else:raise AssertionError('2024admitido')
 dump(OUT/'synthetic.json',{'source_price_fits':0,'synthetic_closed_form_adapters':20,'held_label_full_learning_invariance':True,'calendar_direct_checks':True,'Poisson_exposure_identity':True,'Tweedie_other_method':True,'future_nominal_equals_complete_cost':True,'2024_rejected':True})
 sources=[SOURCE/f'{line}_2023.parquet' for line in m.PERILS]+[COUNTS/f'{market}_{line}_counts.parquet' for market in ['developed','emerging'] for line in m.PERILS]
 sources += [COUNTS/'report.json',REF,OLD,Path(__file__),Path(m.__file__),Path(m.base.__file__),R/'src/semana2/evaluar_robustez2023_v2.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/c0_estricto2023.py']
 sources += [BASE/f'{line}_fold{fold}.parquet' for line in m.PERILS for fold in range(5)]
 sources += [OBS/f'exclude_fold{fold}'/name for fold in range(5) for name in ['reporting_models.json','reporting_fit_claims.parquet']]
 sources += [CLAIMS/f'claims_{line}.parquet' for line in m.PERILS]
 plan={'id':'S2-ROBUSTEZ2023-CICLO8-v1-20261025','utc':now(),'author':'Codex','forum_prior':FID,
  'models':[{'id':'W2-COD-R38','recipe':'peril SourcePoisson + SourceTweedie mark, target-only count/mark credibility constants'},
            {'id':'W2-COD-R39','recipe':'fixed sqrt pool 50% R38 observed forecast +50%R36 incumbent'}],
  'primary_reference':'W2-COD-R36','B00_reference_preserved':True,'secondary_reference':'W2-B20',
  'hypothesis':'Source/target peril mixture and count-versus-mark heterogeneity may be lost by aggregate pricing. Existing outer count/cost curves enable coherent separate denominators without a new observation-model fit.',
  'source_counts':'all included nonrepudiated2023 notifications, including zero net marks; source mark responses T0/N weightedN; no positive-cost deletion',
  'source_frequency_params':{'Poisson_alpha':.001,'max_iter':3000,'tol':1e-7},'source_mark_params':{'Tweedie_power':1.5,'alpha':1.,'max_iter':3000,'tol':1e-7,'fallback_constant_if_claim_periods_below':100},
  'source_features':'physical F0 blocks,exclude region and unsupported construction;source-only transforms',
  'target_adapter':{'frequency_prior_claims':20,'mark_prior_claims':50,'all_fold_training_only':True,'closed_form_parameters':150},
  'source_price_fit_budget_max':30,'new_observation_C0_fits':0,'existing_mix_C0_unchanged':True,
  'denominators':'all reconciled policytime;coverage as predictor,NO structural-zero assumption;positive claims outside expected flags preserved',
  'observation_forecast':'sum_peril exposure*q_cost*rate;rate=freq*mark*training-adapters. Count adapter uses own q_count. Future ultimate conditional q=1,tail0 remains assumed.',
  'primary_gates_vs_R36':{'delta':.005,'lower_exploratory':.0005,'positive_folds':4,'segment_harm_full_null':.0005,'after31groups_delta':.0005},
  'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
  'sensitivity':'fixed prediction versus reserve stresses; uniform q_cost tail downscales. Not recalculated reserve ultimate model.',
  'no_public_weight_tuning':True,'2024_closed':True,'promotion':False,'no_auto_submission':True,
  'sources':[{'path':rel(p),'sha256':sha(p)} for p in sources]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan)
 print(json.dumps({'plan':rel(PLAN),'new_C0_fits':0,'primary_reference':'W2-COD-R36','max_source_price_fits':30,'target_closed_form_parameters':150}))


def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
 (OUT/'source_models').mkdir();(OUT/'models').mkdir();source_models={};source_receipts=[]
 for line in m.PERILS:
  f=pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();c=pq.read_table(COUNTS/f'developed_{line}_counts.parquet').to_pandas()
  def checkpoint(peril,stage,state):
   joblib.dump(state,OUT/f'source_models/{line}_{peril}_{stage}.joblib',compress=3)
   event('source_checkpoint',line=line,peril=peril,stage=stage)
  with threadpool_limits(limits=2):bundle,receipts=m.train_source(f,c,line,checkpoint)
  joblib.dump(bundle,OUT/f'source_models/{line}.joblib',compress=3);dump(OUT/f'source_models/{line}_receipt.json',receipts)
  source_models[line]=bundle;source_receipts+=receipts
 source_fits=sum(x['source_price_fits'] for x in source_receipts);source_constants=sum(x['closed_form_mark_constants'] for x in source_receipts)
 dump(OUT/'source_models_ready.json',{'source_price_fits':source_fits,'source_closed_form_constants':source_constants,'source_receipts':source_receipts})
 incumbent=pq.read_table(REF,filters=[('model_id','=', 'W2-COD-R36'),('year','=',2023)]).to_pandas().sort_values(m.KEY).reset_index(drop=True)
 original=pq.read_table(OLD,filters=[('model_id','in',['W2-B00','W2-B20']),('year','=',2023)]).to_pandas()
 outputs=[];adaptation=[];curve_checks=[]
 targetclaims=pd.concat([pq.read_table(CLAIMS/f'claims_{line}.parquet',columns=m.KEY+['claim_id','year','fold','included_in_T0']).to_pandas() for line in m.PERILS]);targetclaims=targetclaims[targetclaims.included_in_T0.eq(True)]
 for fold in range(5):
  fitted=pq.read_table(OBS/f'exclude_fold{fold}/reporting_fit_claims.parquet').to_pandas();assert fitted.year.eq(2023).all() and fitted.fold.ne(fold).all()
  expected=set(targetclaims.loc[targetclaims.fold.ne(fold),'claim_id']);assert set(fitted.claim_id)==expected
  allcurves=read(OBS/f'exclude_fold{fold}/reporting_models.json')
  for line in m.PERILS:
   featurecols=m.base.FEATURES[line]['numeric']+m.base.FEATURES[line]['categorical'];raw=[c.replace('x_log_voluntary_excess','x_voluntary_excess').replace('x_log_compulsory_excess','x_compulsory_excess').replace('x_log_distance_to_river_km','x_distance_to_river_km') for c in featurecols]
   cols=list(dict.fromkeys(m.KEY+['year','is_test','fold','group_id','customer_id','address_id','period_start','period_end','T0','exposure','e_cost_mix_1.0']+raw))
   f=pq.read_table(BASE/f'{line}_fold{fold}.parquet',columns=cols,filters=[('year','=',2023)]).to_pandas();fit=f[f.fold.ne(fold)].copy();valid=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(valid[key])
   counts=pq.read_table(COUNTS/f'emerging_{line}_counts.parquet').to_pandas();curves={p:allcurves[line+'|'+p] for p in m.PERILS[line]}
   with threadpool_limits(limits=2):bundle,receipt=m.adapt(fit,counts,line,fold,source_models[line],curves);pred,nominal,components=m.predict(bundle,valid)
   path=OUT/f'models/{line}_fold{fold}.joblib';joblib.dump(bundle,path,compress=3)
   with threadpool_limits(limits=2):again,_,_=m.predict(joblib.load(path),valid)
   assert np.array_equal(pred,again)
   adaptation+=receipt
   ref=incumbent[incumbent.line.eq(line)&incumbent.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   assert valid[m.KEY].equals(ref[m.KEY]) and np.array_equal(valid.T0,ref.T0) and np.array_equal(valid['e_cost_mix_1.0'],ref['e_cost_mix_1.0'])
   row=ref.copy();row['model_id']='W2-COD-R38';row['prediction']=pred;row['annual_rate']=pred/row['e_cost_mix_1.0'];row['nominal_annual_rate']=nominal;row['unit_deviance']=m.unit_deviance(row.T0,pred);outputs.append(row)
   curve_checks.append({'line':line,'fold':fold,'outer_reported_claim_membership_exact':True,'replay_exact':True,'peril_curves_reused':len(curves)})
   event('target_adapter_complete',line=line,fold=fold,closed_form_parameters=len(adaptation)*2)
 fresh=pd.concat(outputs,ignore_index=True).sort_values(m.KEY).reset_index(drop=True);assert fresh[m.KEY].equals(incumbent[m.KEY])
 pool=fresh.copy();pool['model_id']='W2-COD-R39';pool['prediction']=(.5*np.sqrt(fresh.prediction)+.5*np.sqrt(incumbent.prediction))**2
 pool['annual_rate']=pool.prediction/pool['e_cost_mix_1.0'];pool['nominal_annual_rate']=np.nan;pool['unit_deviance']=m.unit_deviance(pool.T0,pool.prediction)
 assert np.all(pool.unit_deviance<=.5*fresh.unit_deviance+.5*incumbent.unit_deviance+1e-7)
 new=pd.concat([fresh,pool],ignore_index=True);new.to_parquet(OUT/'new_oof_2023.parquet',index=False)
 report=evaluate(pd.concat([original,incumbent],ignore_index=True),new,['W2-COD-R38','W2-COD-R39'],source_fits,reference_id='W2-COD-R36')
 # Anula la aproximación de sensibilidad de un vínculo agregado: aquí cada peril tiene su q_cost.
 sensitivity=[]
 for mid,part in pd.concat([original,incumbent,new],ignore_index=True).groupby('model_id'):
  for y in ['T1_reserve075','T1_reserve125']:sensitivity.append({'model_id':mid,'stress':'fixed forecast versus '+y,**m.metrics(part,target=y)})
  for factor in [.95,.9]:sensitivity.append({'model_id':mid,'stress':'all q_cost times '+str(factor),**m.metrics(part.assign(stress=part.prediction*factor),prediction='stress')})
 report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',source_price_fits=source_fits,
  new_closed_form_constants=len(adaptation)*2+source_constants,source_mark_fallbacks=source_constants,target_closed_form_constants=len(adaptation)*2,
  source_C0_fits=0,target_C0_fits=0,curve_checks=curve_checks,sensitivity=sensitivity,
  source_and_contract_limits='source observed/nominal;fullpolicytime denominator,not certified covered-peril exposure;no zero coverage or claim deletion')
 check(plan);dump(OUT/'adaptation_receipts.json',adaptation);dump(OUT/'report.json',report)
 dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]})
 event('complete',summary=report['summaries'],gates=report['gates'],source_price_fits=source_fits,closed_form_constants=report['new_closed_form_constants'])


if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['prepare','run']);args=a.parse_args()
 if args.action=='prepare':prepare()
 else:run()
