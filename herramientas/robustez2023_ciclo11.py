"""Covariables básicas y formas estándar aprendidas solo en fuente2023."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,argparse,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_profesor_capacidad2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import pandas as pd,numpy as np,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo11_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo11_plan.json'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';EXTRA=R/'privado/semana2/robustez2023/covariables_basicas2023_v1'
SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def event(name,**kw):
 rec={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
 print(json.dumps(rec),flush=True)
def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']
def synthetic():
 rng=np.random.default_rng(2026102511);n=1500;line='motor'
 f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)
 source=f.assign(market='developed');notes=[]
 with threadpool_limits(limits=2):
  initial,r=m.old.fit_teachers(source,line);plain=initial['W2-COD-R31'];notes.append(r)
  for mid in m.RECIPES:
   t,r=m.fit_source(source,line,mid,plain);notes.append(r);b,r=m.fit(f[f.fold.ne(0)],line,0,t,mid);notes.append(r);val=f[f.fold.eq(0)]
   assert np.array_equal(m.predict(b,val),m.predict(b,val.assign(T0=1e15)))
 dump(OUT/'synthetic.json',{'synthetic_price_fits':6,'held_label_poison_invariant':True,'receipts':notes})
def prepare():
 assert not PLAN.exists() and not OUT.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,EXTRA/'report.json']
 paths+=list(EXTRA.glob('*.parquet'))+[SOURCE/f'{line}_2023.parquet' for line in m.FEATURES]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 paths += list(m.TEACHERS.values())
 plan={'id':'S2-ROBUSTEZ2023-CICLO11-v1-20261025','utc':now(),'author':'Codex','forum_prior':'COD-S2-20261025-ROBUSTEZ11-PREVIO',
 'models':[{'id':mid,'params':params} for mid,params in m.RECIPES.items()],
 'hypothesis':'Target nonlinear fits and enlarged GLM/GAM fail robustness. Source-only small residual trees remain strongest. Test bounded higher source interaction capacity with isolated source holdout and unchanged target adapter.',
 'features':m.FEATURES,'source':'developed2023, same physical predictors excluding source region and building construction; source incurred nominal unchanged',
 'source_holdout':'sha256 C11-source2023:customer_id mod5=0 validation; purge training addresses shared with validation; no parameter tuning or early stopping',
 'source_holdout_gate':'per-line unit Tweedie loss must not exceed the existing200tree recipe by0.2%; all three lines required',
 'source_trees':'800trees lr.025 L2=500 L1=100;R45 depth4 leaves16 min2000;R46 depth5 leaves24 min1000;seed2026102511;no early stopping',
 'adapter':'same intercept free+new_business+region ridge1 in saved five emerging folds',
 'price':'same fixed sqrt50%candidate+50%B20;no weight tuning',
 'real_fit_budget':48,'source_pilot_fits':12,'source_full_boost_fits':6,'target_adapter_fits':30,'new_C0_fits':0,'primary_reference':'W2-COD-R36',
 'criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31favorablegroups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R45 if allprimary+sourceholdout pass;elseR46 if allpass;otherwiseR36 retained;no promotion',
 '2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'budget':48,'synthetic':6}))
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
 old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas()
 receipts=[];outputs=[]
 for line in m.FEATURES:
  source=pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();sf,sv=m.split_source(source)
  event('source_pilot_started',line=line,fit_rows=len(sf),validation_rows=len(sv))
  with threadpool_limits(limits=2):pilot,rec=m.old.fit_teachers(sf,line)
  receipts.append({'line':line,'role':'source_pilot_reference','price_estimator_fits':2,'details':rec})
  with threadpool_limits(limits=2):basepred=m.old.teacher_rate(pilot['W2-COD-R32'],sv)*sv.exposure.to_numpy()
  base_loss=float(m.unit_deviance(sv.T0,basepred).sum());pilot_results=[]
  for recipe in plan['models']:
   with threadpool_limits(limits=2):t,rec=m.fit_source(sf,line,recipe['id'],pilot['W2-COD-R31']);pred=m.old.teacher_rate(t,sv)*sv.exposure.to_numpy()
   loss=float(m.unit_deviance(sv.T0,pred).sum());rec['role']='source_pilot';receipts.append(rec)
   pilot_results.append({'line':line,'model_id':recipe['id'],'source_fit_rows':len(sf),'source_validation_rows':len(sv),'reference200_loss':base_loss,'candidate_loss':loss,'relative_difference':loss/base_loss-1,'passes':bool(loss<=base_loss*1.002),'customer_address_disjoint':True})
  dump(OUT/f'pilot_{line}.json',pilot_results);del sf,sv,pilot
  parent=joblib.load(m.TEACHERS[line])['parent'];teachers={}
  for recipe in plan['models']:
   event('source_fit_started',line=line,model_id=recipe['id'])
   with threadpool_limits(limits=2):t,rec=m.fit_source(source,line,recipe['id'],parent)
   path=OUT/f'teachers/{recipe["id"]}_{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);teachers[recipe['id']]=t;rec['role']='source_full';receipts.append(rec);dump(path.with_suffix('.json'),rec);event('source_fit_complete',line=line,model_id=recipe['id'])
  del source
  for fold in range(5):
   # The strict stored frames contain only 2023. Keep their response/C0 and physical values verbatim.
   f=pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas()
   fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=inc[inc.line.eq(line)&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.eq(line)&old.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   assert val[m.KEY].equals(ref[m.KEY]) and b20[m.KEY].equals(ref[m.KEY])
   for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())
   for recipe in plan['models']:
    event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
    with threadpool_limits(limits=2):b,rec=m.fit(fit,line,fold,teachers[recipe['id']],recipe['id']);rate=m.predict(b,val)
    path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
    rec['replay_exact']=True;receipts.append(rec);dump(path.with_suffix('.json'),rec)
    o=ref.copy();o['model_id']=recipe['id'];o['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();o['prediction']=(.5*np.sqrt(o.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;o['annual_rate']=o.prediction/o['e_cost_mix_1.0'];o['unit_deviance']=m.unit_deviance(o.T0,o.prediction);outputs.append(o)
    event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'],completed=len(receipts))
 new=pd.concat(outputs,ignore_index=True);assert len(new)==2*50094 and not new.duplicated(['model_id']+m.KEY).any();new.to_parquet(OUT/'new_oof_2023.parquet',index=False)
 report=evaluate(pd.concat([old,inc],ignore_index=True),new,[x['id'] for x in plan['models']],48,reference_id='W2-COD-R36')
 pilotrows=[row for line in m.FEATURES for row in read(OUT/f'pilot_{line}.json')]
 for gate in report['gates']:
  gate['checks']['source_holdout']=all(x['passes'] for x in pilotrows if x['model_id']==gate['model_id']);gate['all_pass']=all(gate['checks'].values())
 report['source_pilot']=pilotrows
 selected=next((x['model_id'] for x in report['gates'] if x['all_pass']),None);report.update(id=plan['id'],utc=now(),author='Codex',selected_exploratory_variant=selected,primary_reference='W2-COD-R36',source_support_not_emerging=True,formal_promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',summary=report['summaries'],gates=report['gates'],selected=selected)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
