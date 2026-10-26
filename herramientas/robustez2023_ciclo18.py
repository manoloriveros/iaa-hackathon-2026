"""Nuevo algoritmo fuente con veto previo; no consume fits emergentes si falla."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,argparse,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_catboost_fuente2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib,catboost
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo18_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo18_plan.json'
SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';BLOCKS=R/'privado/semana2/robustez2023/bloques_fuente2023_v1';BAGS=R/'privado/semana2/robustez2023/ciclo17_20261025_v1/source_bags'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']
def event(name,**kw):
 rec={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
 print(json.dumps(rec),flush=True)
def synthetic():
 n=1200;rng=np.random.default_rng(2026102518);line='motor';f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n),'source_group_id':np.repeat(np.arange(n//2),2).astype(str)})
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)
 source=f.assign(market='developed');notes=[]
 with threadpool_limits(limits=2):parents,note=m.old.fit_teachers(source,line)
 notes.append(note)
 for depth in [3,4]:
  with threadpool_limits(limits=2):teacher,rec=m.fit_source(source,line,parents['W2-COD-R31'],{'id':'SYN','depth':depth});b,rec2=m.fit(f[f.fold.ne(0)],line,0,teacher,'SYN')
  val=f[f.fold.eq(0)];before=joblib.hash(b)
  with threadpool_limits(limits=2):pred=m.predict(b,val);poison=m.predict(b,val.assign(T0=1e15))
  assert np.array_equal(pred,poison) and joblib.hash(b)==before;notes.extend([rec,rec2])
 try:m.fit_source(source.assign(year=2024),line,parents['W2-COD-R31'],{'id':'SYN','depth':3})
 except AssertionError:pass
 else:raise AssertionError('2024admitido')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':6,'separate_baseline_toy_fits':1,'CatBoost_version':catboost.__version__,'two_full_flows':True,'prediction_label_poison_invariant':True,'2024_rejected_before_fit':True,'state_unchanged':True,'receipts':notes})
def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/desplegar_robustez2023.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,BLOCKS/'report.json',R/'privado/semana2/robustez2023/mision017_20261025_v1/toy_catboost_baseline.json']
 paths+=list(m.TEACHERS.values())+[BAGS/f'{line}_bag0.joblib' for line in m.FEATURES]+[SOURCE/f'{line}_2023.parquet' for line in m.FEATURES]+[BLOCKS/f'{line}.parquet' for line in m.FEATURES]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO18-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ18-PREVIO',
 'models':[{'id':'W2-COD-R66','depth':3},{'id':'W2-COD-R67','depth':4}],'natural_outputs':{'W2-COD-R66':'W2-COD-R68','W2-COD-R67':'W2-COD-R69'},
 'hypothesis':'Standard GLM/additive,physical corrections,peril decomposition and source bagging fail incremental robustness. Test another standard boosting algorithm, OrderedCatBoost, with small symmetric trees and groupbootstrap around frozen physicalGLM, before increasing LightGBM capacity again.',
 'source':'developed2023 only;same physical features,source region/construction excluded;GLM numeric transforms reused at exact source scope',
 'CatBoost':{'version':catboost.__version__,'loss':'Tweedie:variance_power=1.5','iterations':300,'depths':[3,4],'learning_rate':.025,'boosting_type':'Ordered','bootstrap_type':'Bayesian','sampling_unit':'Group','bagging_temperature':1.,'one_hot_max_size':40,'random_strength':0.,'seed':2026102518,'threads':2,'boost_from_average':False},
 'scale':'max(1000,max(sourceannualresponse)/1000) fitonly,no label clipping;L2=500/sqrt(scale) to match loss-scale homogeneity;baseline log(sourceGLMrate/scale)',
 'source_veto':'source block0 held;reuse C17bag0GLM and200tree reference, no refit. All3line unitTweedie losses<=1.002times200tree baseline for a depth to proceed. If bothdepthsfail stop before full source and targetfits.',
 'budget_max':42,'source_pilot_fits':6,'full_source_fits_max':6,'target_adapter_fits_max':30,'new_C0_fits':0,
 'adapter':'same minimal interceptfree+newbusiness/regionridge1 inside saved five emerging2023componentfolds',
 'output':'R66/R67 fixedsqrt50%candidate+50%B20 exactlyR36;R68/R69 natural correspondingoutput;no optimizedweights',
 'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R66depth3pool,thenR67depth4pool,thenR68depth3natural,thenR69depth4natural;allsource+primarygates required',
 'primary_docs':['https://catboost.ai/docs/en/concepts/loss-functions-regression','https://catboost.ai/docs/en/concepts/python-reference_pool','https://catboost.ai/docs/en/concepts/input-data_baseline'],
 '2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'promotion':False,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'fit_budget_max':42,'synthetic_fits':6,'veto_before_fullfit':True}))
def load_source(line):
 f=pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();blocks=pq.read_table(BLOCKS/f'{line}.parquet').to_pandas();f=f.merge(blocks[m.KEY+['source_group_id','source_fold']],on=m.KEY,how='left',validate='one_to_one');assert f.source_fold.notna().all();return f
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];pilots=[]
 for line in m.FEATURES:
  f=load_source(line);fit=f[f.source_fold.ne(0)].copy();val=f[f.source_fold.eq(0)].copy()
  for key in ['source_group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
  parent=joblib.load(BAGS/f'{line}_bag0.joblib')
  with threadpool_limits(limits=2):oldpred=m.old.teacher_rate(parent['W2-COD-R32'],val)*val.exposure.to_numpy()
  oldloss=float(m.unit_deviance(val.T0,oldpred).sum())
  for recipe in plan['models']:
   event('source_pilot_started',line=line,model_id=recipe['id'],fit_rows=len(fit),validation_rows=len(val))
   with threadpool_limits(limits=2):t,rec=m.fit_source(fit,line,parent['W2-COD-R31'],recipe);pred=m.teacher_rate(t,val)*val.exposure.to_numpy()
   path=OUT/f'pilot_models/{recipe["id"]}_{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);rec['role']='source_pilot';receipts.append(rec);dump(path.with_suffix('.json'),rec)
   loss=float(m.unit_deviance(val.T0,pred).sum());row={'line':line,'model_id':recipe['id'],'fit_rows':len(fit),'validation_rows':len(val),'reference200_loss':oldloss,'candidate_loss':loss,'relative_difference':loss/oldloss-1,'pass':bool(loss<=oldloss*1.002),'groups_customer_address_disjoint':True};pilots.append(row);dump(OUT/f'pilot_metrics/{recipe["id"]}_{line}.json',row);event('source_pilot_complete',**row)
 selected=[x for x in plan['models'] if all(p['pass'] for p in pilots if p['model_id']==x['id'])];dump(OUT/'source_veto.json',{'pilots':pilots,'eligible':selected,'real_fits_completed':len(receipts),'full_target_stopped_if_none':True})
 if not selected:
  base=read(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json');report={'id':plan['id'],'utc':now(),'author':'Codex','primary_reference':'W2-COD-R36','summaries':[x for x in base['summaries'] if x['model_id'] in ['W2-B00','W2-B20','W2-COD-R36']],'gates':[],'pairs':[],'source_pilots':pilots,'new_price_fits':len(receipts),'new_C0_fits':0,'2024_closed':True,'B00_preserved':True,'stop_reason':'bothdepths failed preinscribed source gate;no fullsource or emerging fits/predictions/scoring','selected_exploratory_variant':None,'promotion':False}
 else:
  incumbent=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();original=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();outputs=[]
  for line in m.FEATURES:
   f=load_source(line);parent=joblib.load(m.TEACHERS[line])['parent'];teachers={}
   for recipe in selected:
    event('source_full_started',line=line,model_id=recipe['id'])
    with threadpool_limits(limits=2):t,rec=m.fit_source(f,line,parent,recipe)
    path=OUT/f'teachers/{recipe["id"]}_{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);rec['role']='source_full';receipts.append(rec);dump(path.with_suffix('.json'),rec);teachers[recipe['id']]=t;event('source_full_complete',line=line,model_id=recipe['id'])
   del f
   for fold in range(5):
    frame=pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas();fit=frame[frame.fold.ne(fold)].copy();val=frame[frame.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
    for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
    ref=incumbent[incumbent.line.eq(line)&incumbent.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=original[original.model_id.eq('W2-B20')&original.line.eq(line)&original.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
    assert val[m.KEY].equals(ref[m.KEY]) and b20[m.KEY].equals(ref[m.KEY])
    for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())
    for recipe in selected:
     event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
     with threadpool_limits(limits=2):bundle,rec=m.fit(fit,line,fold,teachers[recipe['id']],recipe['id']);rate=m.predict(bundle,val)
     path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(bundle,path,compress=3)
     with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
     rec['role']='target';rec['replay_exact']=True;receipts.append(rec);dump(path.with_suffix('.json'),rec)
     row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
     pure=row.copy();pure['model_id']=plan['natural_outputs'][recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'])
  new=pd.concat(outputs,ignore_index=True);assert len(new)==len(selected)*2*50094;new.to_parquet(OUT/'new_oof_2023.parquet',index=False)
  ids=[x['id'] for x in selected]+[plan['natural_outputs'][x['id']] for x in selected];report=evaluate(pd.concat([original,incumbent],ignore_index=True),new,ids,len(receipts),reference_id='W2-COD-R36')
  report.update(id=plan['id'],utc=now(),author='Codex',source_pilots=pilots,primary_reference='W2-COD-R36',selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=report['new_price_fits'],gates=report['gates'],selected=report['selected_exploratory_variant'],source_eligible=[x['id'] for x in selected])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
