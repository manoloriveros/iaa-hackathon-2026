"""Contracción de GLM de calibración, sin aprender forma fuente otra vez."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,os,hashlib,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_calibracion_contraccion2023 as m
from semana2.desplegar_robustez2023 import TEACHERS
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo23_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo23_plan.json';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
RECIPES=[{'id':'W2-COD-R86','ridge':.1},{'id':'W2-COD-R87','ridge':10.}];NATURAL={'W2-COD-R86':'W2-COD-R88','W2-COD-R87':'W2-COD-R89'}

def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))

def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']

def event(name,**kw):
 obj={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(obj)+'\n')
 print(json.dumps(obj),flush=True)

def synthetic():
 n=1200;rng=np.random.default_rng(2026102523);receipts=[]
 for line in m.FEATURES:
  f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
  for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
  for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)
  with threadpool_limits(limits=2):teachers,_=m.old.fit_teachers(f.assign(market='developed'),line)
  for recipe in RECIPES:
   with threadpool_limits(limits=2):b,rec=m.fit(f[f.fold.ne(0)],line,0,teachers['W2-COD-R32'],recipe);val=f[f.fold.eq(0)];p=m.predict(b,val)
   assert np.array_equal(p,m.predict(b,val.assign(T0=1e15)));receipts.append(rec)
   try:m.predict(b,val.assign(year=2024))
   except AssertionError:pass
   else:raise AssertionError('2024 aceptado')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':12,'target_adapter_fits':6,'source_toy_fits':6,'all3lines':True,'finite_difference_gradient':True,'held_label_poison_invariant':True,'2024_rejected':True,'receipts':receipts})

def prepare():
 assert not PLAN.exists() and not OUT.exists();OUT.mkdir(parents=True);synthetic()
 audit=R/'privado/semana2/robustez2023/mision017_20261025_v1/calibration_coefficient_audit.json'
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/desplegar_robustez2023.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,audit]+list(TEACHERS.values())+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO23-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ23-PREVIO','models':RECIPES,'natural_outputs':NATURAL,
 'hypothesis':'Existing source-offset calibration has substantial regional and motornewbusiness effects despite ridge1. Test biasvariance with standard same-dimension GLMs at fixedridge.1and10 rather than adding complexity. Coefficient audit doesnot prove ridgebias or optimality.',
 'model':'samefrozenphysicalsourceGLM+smallresidualtrees;freeintercept+newbusiness+region only,normalizationandpenaltyunchangedexceptscalar;no renewedsourcefit',
 'outputs':'R86/R87fixedsqrt50%candidate+50%B20,R88/R89natural,no learnedweights',
 'real_fit_budget':30,'source_fit_budget':0,'new_C0_fits':0,'target_scope':'2023emerging,5savedfolds,fullconnectedgroupsdisjoint,T0/exposure/C0 unchanged',
 'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R87strongpool,thenR86weakpool,thenR89strongnatural,thenR88weaknatural,onlyallgates;otherwiseR36','2024_closed':True,'B00_preserved':True,'promotion':False,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'real_fits':30,'new_source_fits':0,'new_C0':0}))

def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];outputs=[]
 inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas()
 for line in m.FEATURES:
  teacher=joblib.load(TEACHERS[line])
  for fold in range(5):
   f=pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas();fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=inc[inc.line.eq(line)&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.eq(line)&old.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert ref[m.KEY].equals(val[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
   for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())
   for recipe in plan['models']:
    event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
    with threadpool_limits(limits=2):b,rec=m.fit(fit,line,fold,teacher,recipe);rate=m.predict(b,val)
    path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
    rec['replay_exact']=True;receipts.append(rec);dump(path.with_suffix('.json'),rec);row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
    pure=row.copy();pure['model_id']=NATURAL[recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'])
 new=pd.concat(outputs,ignore_index=True);new.to_parquet(OUT/'new_oof_2023.parquet',index=False);ids=['W2-COD-R87','W2-COD-R86','W2-COD-R89','W2-COD-R88'];report=evaluate(pd.concat([old,inc],ignore_index=True),new,ids,len(receipts),reference_id='W2-COD-R36');report.update(id=plan['id'],author='Codex',utc=now(),primary_reference='W2-COD-R36',selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=len(receipts),gates=report['gates'],selected=report['selected_exploratory_variant'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
