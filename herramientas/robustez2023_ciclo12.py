"""Covariables básicas y formas estándar aprendidas solo en fuente2023."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,argparse,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_perfiles_fuente2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
from semana2.modelo_profesor_capacidad2023 import split_source
import pandas as pd,numpy as np,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo12_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo12_plan.json'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';EXTRA=R/'privado/semana2/robustez2023/perfiles_comunes2023_v2'
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
 rng=np.random.default_rng(2026102511);n=1200;line='buildings'
 f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)
 source=f.assign(market='developed');receipts=[]
 with threadpool_limits(limits=2):
  plain,r=m.fit_source(source,line,'glm');receipts.append(r)
  for kind in ['glm','trees']:
   if kind=='glm':t=plain
   else:t,r=m.fit_source(source,line,kind,parent=plain);receipts.append(r)
   b,r=m.fit(f[f.fold.ne(0)],line,0,t,'SYN');receipts.append(r);val=f[f.fold.eq(0)];p=m.predict(b,val)
   assert np.array_equal(p,m.predict(b,val.assign(T0=1e15)))
 for bad in [source.assign(year=2024),source.assign(market='emerging')]:
  try:m.fit_source(bad,line,'glm')
  except AssertionError:pass
  else:raise AssertionError('Ámbito prohibido admitido')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':4,'label_poison_invariant':True,'source2024_rejected':True,'cross_market_rejected':True,'receipts':receipts})
def prepare():
 assert not PLAN.exists() and not OUT.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,EXTRA/'report.json']
 paths+=list(EXTRA.glob('*.parquet'))+[SOURCE/f'{line}_2023.parquet' for line in m.FEATURES]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 paths += [R/f'privado/semana2/robustez2023/ciclo11_20261025_v1/pilot_{line}.json' for line in m.FEATURES]+[R/'src/semana2/modelo_profesor_capacidad2023.py',R/'src/semana2/desplegar_robustez2023.py']
 plan={'id':'S2-ROBUSTEZ2023-CICLO12-v1-20261025','utc':now(),'author':'Codex','forum_prior':'COD-S2-20261025-ROBUSTEZ12-PREVIO',
 'models':[{'id':'W2-COD-R47','kind':'glm'},{'id':'W2-COD-R48','kind':'trees'}],
 'hypothesis':'Cycle9 estimates only weak target prior effect. Transporting source main effects of common provided customer declarations/household/licence/occupation may provide information absent from physical-only model. Test standardGLM and established small200tree residual, no capacity increase.',
 'features':m.FEATURES,'availability':'conditional supplied-data benchmark only, unversioned profiles; joining year<=2023 verified, no dated capture proof; not certified prospective pricing',
 'normalization':'lower/trim/collapse whitespace only,no profession regrouping;log1p prejoin count;missing numeric imputation fitonly;OHEmin100/max40 sourcefitonly',
 'source_missing':'25,571 motor policyperiods lack customer master; retain all periods/targets/exposure and missing profiles; do not infer customer identities',
 'source_pilot':'same source customer-hash holdout and address purge asC11; compare existing saved200tree reference loss, no baseline refit; require eachramo loss<=1.002reference',
 'source_GLM':'Tweedie1.5 alpha1,median/clip.005/.995/scale fitonly;physical predictor setR36 plus five common profile fields',
 'source_trees':'existing200trees depth3 leaves8 lr.025 min5000 L2=500 L1=100,seed2026102506; no tuning',
 'adapter':'same intercept free+new_business+region ridge1;five stored emerging componentfolds',
 'price':'fixed sqrt50%candidate+50%B20 identicalR36 weight, no optimization',
 'real_fit_budget':42,'source_pilot_fits':6,'source_full_fits':6,'target_adapter_fits':30,'new_C0_fits':0,'primary_reference':'W2-COD-R36',
 'criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R47 standardGLM if allpass,elseR48 if allpass,otherwiseR36;no final promotion or auto submission',
 '2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'budget':42,'synthetic':4}))
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
 old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas()
 receipts=[];outputs=[]
 for line in m.FEATURES:
  source=m.attach(pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas(),pq.read_table(EXTRA/f'developed_{line}.parquet').to_pandas())
  sf,sv=split_source(source);reference=read(R/f'privado/semana2/robustez2023/ciclo11_20261025_v1/pilot_{line}.json')[0]
  assert len(sf)==reference['source_fit_rows'] and len(sv)==reference['source_validation_rows']
  base_loss=reference['reference200_loss'];pilot={};pilot_results=[]
  for recipe in plan['models']:
   event('source_pilot_fit_started',line=line,model_id=recipe['id'])
   with threadpool_limits(limits=2):t,rec=m.fit_source(sf,line,recipe['kind'],parent=pilot.get('W2-COD-R47'));prediction=m.teacher_rate(t,sv)*sv.exposure.to_numpy()
   pilot[recipe['id']]=t;rec['role']='source_pilot';rec['model_id']=recipe['id'];receipts.append(rec)
   pp=OUT/f'pilot_models/{recipe["id"]}_{line}.joblib';pp.parent.mkdir(exist_ok=True);joblib.dump(t,pp,compress=3)
   loss=float(m.unit_deviance(sv.T0,prediction).sum());pilot_results.append({'line':line,'model_id':recipe['id'],'source_fit_rows':len(sf),'source_validation_rows':len(sv),'reference200_loss':base_loss,'candidate_loss':loss,'relative_difference':loss/base_loss-1,'passes':bool(loss<=base_loss*1.002),'customer_address_disjoint':True})
  dump(OUT/f'pilot_{line}.json',pilot_results);del sf,sv,pilot
  teachers={}
  for recipe in plan['models']:
   event('source_fit_started',line=line,model_id=recipe['id'])
   with threadpool_limits(limits=2):t,rec=m.fit_source(source,line,recipe['kind'],parent=teachers.get('W2-COD-R47'))
   path=OUT/f'teachers/{recipe["id"]}_{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);teachers[recipe['id']]=t;rec['model_id']=recipe['id'];rec['role']='source_full';receipts.append(rec);dump(path.with_suffix('.json'),rec);event('source_fit_complete',line=line,model_id=recipe['id'],completed=len(receipts))
  del source
  extra=pq.read_table(EXTRA/f'emerging_{line}.parquet').to_pandas()
  for fold in range(5):
   # The strict stored frames contain only 2023. Keep their response/C0 and physical values verbatim.
   f=m.attach(pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas(),extra)
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
 report=evaluate(pd.concat([old,inc],ignore_index=True),new,[x['id'] for x in plan['models']],42,reference_id='W2-COD-R36')
 pilotrows=[row for line in m.FEATURES for row in read(OUT/f'pilot_{line}.json')]
 for gate in report['gates']:
  gate['checks']['source_holdout']=all(x['passes'] for x in pilotrows if x['model_id']==gate['model_id']);gate['all_pass']=all(gate['checks'].values())
 report['source_pilot']=pilotrows
 selected=next((x['model_id'] for x in report['gates'] if x['all_pass']),None);report.update(id=plan['id'],utc=now(),author='Codex',selected_exploratory_variant=selected,primary_reference='W2-COD-R36',source_support_not_emerging=True,formal_promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',summary=report['summaries'],gates=report['gates'],selected=selected)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
