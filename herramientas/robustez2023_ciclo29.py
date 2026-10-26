"""Hogar enmascarado que pasó fuente: independientes y GLM conjunto, autos intacto."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_region_hogar_mascarado2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from sklearn.dummy import DummyRegressor
from sklearn.preprocessing import FunctionTransformer
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo29_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo29_plan.json';SOURCE=R/'privado/semana2/robustez2023/fuente_mascarada2023_v3';C26=R/'privado/semana2/robustez2023/ciclo26_20261025_v1';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
RECIPES=[{'id':'W2-COD-R110','tau':20.},{'id':'W2-COD-R111','tau':200.}];NATURAL={'W2-COD-R110':'W2-COD-R112','W2-COD-R111':'W2-COD-R113'};IDS=[x['id'] for x in RECIPES]+list(NATURAL.values())+['W2-COD-R115','W2-COD-R114']
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));parentpath=lambda line:C26/f'teachers/W2-COD-R98_{line}.joblib'
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as h:json.dump(obj,h,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(plan):
 for row in plan['sources']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
def event(name,**kw):
 row={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as h:h.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)
def synthetic():
 rng=np.random.default_rng(2026102529);frames=[];teachers={};independent={};receipts=[]
 for line in m.HOMES:
  n=600;f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+line+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
  for c in m.core.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
  for c in m.core.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n);est=DummyRegressor(strategy='constant',constant=100. if line=='buildings' else 30.);est.fit(np.zeros((2,1)),[1.,1.]);teachers[line]={'line':line,'family':'ExtendedSourceGLM','columns':['x_new_business'],'transformer':FunctionTransformer(),'estimator':est}
  with threadpool_limits(limits=2):b,rec=m.core.fit(f[f.fold.ne(0)],line,0,teachers[line],'SYN')
  independent[line]=b;frames.append(f)
 f=pd.concat(frames,ignore_index=True);fit=f[f.fold.ne(0)];val=f[f.fold.eq(0)]
 with threadpool_limits(limits=2):control,note=m.control(fit,teachers,independent,0)
 rate=m.predict(control,val)
 for line in m.HOMES:
  chosen=val.line.eq(line).to_numpy();assert np.allclose(rate[chosen],m.core.predict(independent[line],val.loc[chosen]),rtol=1e-12,atol=1e-12)
 for recipe in RECIPES:
  with threadpool_limits(limits=2):b,rec=m.fit(fit,teachers,0,recipe);p=m.predict(b,val)
  assert np.array_equal(p,m.predict(b,val.assign(T0=1e15)));receipts.append(rec)
  try:m.predict(b,val.assign(year=2024))
  except AssertionError:pass
  else:raise AssertionError('2024 aceptado')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':6,'toy_constant_sources':2,'independent_adapters':2,'joint_adapters':2,'changed_provider_control':note,'held_label_poison_invariant':True,'2024_rejected':True,'receipts':receipts})
def prepare():
 assert not PLAN.exists() and not OUT.exists();OUT.mkdir(parents=True);synthetic();oldplan=read(R/'registro/semana2_robustez2023_ciclo26_plan.json');oldhash={x['path']:x['sha256'] for x in oldplan['sources']};manifest={x['path']:x['sha256'] for x in read(C26/'manifest.json')['files']};passed=[]
 for line in m.HOMES:
  gate=next(x for x in read(C26/'source_veto.json')['summaries'] if x['line']==line and x['model_id']=='W2-COD-R99');assert gate['pass'] and max(gate['pooled_regime_relative_losses'].values())<=.002;passed.append(gate)
  for p in [SOURCE/f'{line}_2023.parquet',R/'src/semana2/modelo_fuente_mascarada2023.py']:assert oldhash[rel(p)]==sha(p)
  assert manifest[rel(parentpath(line))]==sha(parentpath(line));assert read(parentpath(line).with_suffix('.json'))['role']=='source_full'
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_fuente_mascarada2023.py',R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',C26/'source_veto.json',C26/'manifest.json',SOURCE/'report.json',SOURCE/'preparation_contract.json',REF,OLD]+[parentpath(line) for line in m.HOMES]+[parentpath(line).with_suffix('.json') for line in m.HOMES]+[SOURCE/f'{line}_2023.parquet' for line in m.HOMES]+[BASE/f'{line}_fold{k}.parquet' for line in m.HOMES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO29-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ29-PREVIO','models':RECIPES,'home_natural_outputs':NATURAL,'independent_natural':'W2-COD-R114','independent_pool':'W2-COD-R115','preference_order':IDS,
 'hypothesis':'C26maskedsource price trees passed both home sourceviews but failed motor;C27regionalsharing improves home but uncertainty/influence unresolved. Test SAMEjointGLM with maskedhome rateprovider only,keepmotorR36. Postadaptive new scope,not reinterpretation of globallyvetoed C26 aspassed.',
 'source':'reuse C26fullmaskedGLMparents and already-passedhome5blocktwo-viewchecks,hashmatched;fit exactlyone200depth3leaves8lr.025min5000L2500L1100seed2026102506residual perhome;no newGLMsourceor newcapacity',
 'source_checks_reused':passed,'target':'5saved2023connectedcomponentfolds,unchangedT0/exposure/C0,14parameterhomejointGLM tau20/200;newbusinessridge1,commonregionridge2,freeintercepts',
 'controls':'Need10newindependenthomeadapters because these sourcefullresiduals didnotexist;maptheircoefficients tojointtau2without EXTRAfit,andverify objectives,gradientandheldprediction. Independentpricefitscounted and outputsretained,not treatedashistoricalrefit.',
 'real_fit_budget':22,'source_new_residual_fits':2,'source_GLM_fits_reused':2,'independent_target_fits':10,'joint_target_fits':10,'new_C0_fits':0,
 'outputs':'homefixedsqrt50/50B20andhomenatural;motor exactR36copied,no newinference;independenthomeoutputsR114/R115also retained;no newweights',
 'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'2024_closed':True,'B00_preserved':True,'promotion':False,'adaptive_exploratory':True,'public_queue_unchanged':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'newfits_max':22,'reusedGLMsource':2,'newC0':0}))
def outputs_for(ref,b20,rate,mixed,natural):
 row=ref.copy();row['model_id']=mixed;row['home_unpooled_prediction']=rate*row['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.home_unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);pure=row.copy();pure['model_id']=natural;pure['prediction']=pure.home_unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);return [row,pure]
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];teachers={};controls=[];outputs=[]
 for line in m.HOMES:
  source=pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();parent=joblib.load(parentpath(line));event('source_residual_started',line=line)
  with threadpool_limits(limits=2):teacher,rec=m.core.fit_source(source,line,'trees',parent=parent)
  rec.update(role='source_full_residual',reused_GLM_parent=True);receipts.append(rec);teachers[line]=teacher;p=OUT/f'teachers/{line}.joblib';p.parent.mkdir(exist_ok=True);joblib.dump(teacher,p,compress=3);dump(p.with_suffix('.json'),rec);event('source_residual_complete',line=line)
 inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas()
 for fold in range(5):
  f=pd.concat([pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas() for line in m.HOMES],ignore_index=True);fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
  for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
  assert f.groupby('group_id').fold.nunique().le(1).all();independent={}
  for line in m.HOMES:
   event('independent_fit_started',line=line,fold=fold)
   with threadpool_limits(limits=2):b,rec=m.core.fit(fit[fit.line.eq(line)],line,fold,teachers[line],'W2-COD-R114-SEP')
   rec.update(role='new_independent_target_control');receipts.append(rec);independent[line]=b;p=OUT/f'models/independent_{line}_fold{fold}.joblib';p.parent.mkdir(exist_ok=True);joblib.dump(b,p,compress=3);dump(p.with_suffix('.json'),rec)
  with threadpool_limits(limits=2):control,note=m.control(fit,teachers,independent,fold);controlrate=m.predict(control,val)
  for line in m.HOMES:
   chosen=val.line.eq(line).to_numpy()
   with threadpool_limits(limits=2):sep=m.core.predict(independent[line],val.loc[chosen]);replayed=m.core.predict(joblib.load(OUT/f'models/independent_{line}_fold{fold}.joblib'),val.loc[chosen])
   assert np.array_equal(sep,replayed) and np.allclose(controlrate[chosen],sep,rtol=1e-12,atol=1e-12)
  note.update(independent_models_new_fits_thiscycle=2,mapping_only_newfits=0,held_prediction_equivalent=True);controls.append(note);dump(OUT/f'controls/fold{fold}.json',note)
  ref=inc[inc.line.isin(m.HOMES)&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.isin(m.HOMES)&old.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
  for col in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[col].to_numpy(),ref[col].to_numpy())
  outputs+=outputs_for(ref,b20,controlrate,'W2-COD-R115','W2-COD-R114');event('independent_controls_complete',fold=fold)
  for recipe in RECIPES:
   event('joint_fit_started',fold=fold,model_id=recipe['id'])
   with threadpool_limits(limits=2):b,rec=m.fit(fit,teachers,fold,recipe);rate=m.predict(b,val)
   p=OUT/f'models/{recipe["id"]}_fold{fold}.joblib';joblib.dump(b,p,compress=3)
   with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(p),val))
   rec.update(role='joint_target',replay_exact=True);receipts.append(rec);dump(p.with_suffix('.json'),rec);outputs+=outputs_for(ref,b20,rate,recipe['id'],NATURAL[recipe['id']]);event('joint_fit_complete',fold=fold,model_id=recipe['id'])
 for mid in IDS:
  motor=inc[inc.line.eq('motor')].copy();motor['model_id']=mid;outputs.append(motor)
 new=pd.concat(outputs,ignore_index=True);assert len(new)==6*50094 and not new.duplicated(['model_id']+m.KEY).any();new.to_parquet(OUT/'new_oof_2023.parquet',index=False);assert len(receipts)==22;report=evaluate(pd.concat([old,inc],ignore_index=True),new,IDS,len(receipts),reference_id='W2-COD-R36');report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',coordinate_controls=controls,source_GLM_fits_reused=2,old_global_C26_veto_preserved=True,motor_exact_R36=True,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=len(receipts),gates=report['gates'],selected=report['selected_exploratory_variant'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
