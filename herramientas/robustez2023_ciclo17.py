"""Covariables básicas y formas estándar aprendidas solo en fuente2023."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,argparse,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_profesor_bloques2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import pandas as pd,numpy as np,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo17_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo17_plan.json'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';EXTRA=R/'privado/semana2/robustez2023/bloques_fuente2023_v1'
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
class FixedMatrix:
 def transform(self,f):return np.zeros((len(f),1))
class FixedRate:
 def __init__(self,r):self.r=r
 def predict(self,x):return np.full(len(x),self.r)
def synthetic():
 n=600;rng=np.random.default_rng(2026102517);line='motor';f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n);notes=[]
 teacher={'line':line,'members':[{'line':line,'family':'SourceGLM','columns':['x_new_business'],'transformer':FixedMatrix(),'estimator':FixedRate(v)} for v in [100.,200.,300.,400.,500.]]}
 expected=np.mean(np.sqrt([100.,200.,300.,400.,500.]))**2;assert np.all(m.teacher_rate(teacher,f)==expected)
 # Convexity in root-price, independent direct numeric verification.
 y=f.T0.to_numpy();p=np.array([100.,200.,300.,400.,500.])[:,None]*np.ones((5,n));combined=np.sqrt(p).mean(axis=0)**2
 assert np.all(m.unit_deviance(y,combined)<=np.mean([m.unit_deviance(y,q) for q in p],axis=0)+1e-8)
 for mid in ['SYN-GLM','SYN-TREES']:
  b,note=m.fit(f[f.fold.ne(0)],line,0,teacher,mid);val=f[f.fold.eq(0)];assert np.array_equal(m.predict(b,val),m.predict(b,val.assign(T0=1e15)));notes.append(note)
 dump(OUT/'synthetic.json',{'synthetic_price_fits':2,'five_member_root_identity':True,'root_loss_Jensen_check':True,'held_labels_invariant':True,'receipts':notes})
def prepare():
 assert not PLAN.exists() and not OUT.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,EXTRA/'report.json']
 paths+=list(EXTRA.glob('*.parquet'))+[SOURCE/f'{line}_2023.parquet' for line in m.FEATURES]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO17-v1-20261025','utc':now(),'author':'Codex','forum_prior':'COD-S2-20261025-ROBUSTEZ17-PREVIO',
 'models':[{'id':'W2-COD-R62','kind':'glm'},{'id':'W2-COD-R63','kind':'trees'}],'extra_outputs':['W2-COD-R64','W2-COD-R65'],
 'hypothesis':'Source estimator uncertainty was not averaged. Five leave-one-source-component-block-out teachers aggregated in root-rate may reduce dependence on a few source groups while leaving target adapter minimal; compare standardGLM and originalsmall200tree forms.',
 'source_blocks':'saved source2023customer/address components,5hashblocks;eachrowusedin4teachers;no sourcegroupcrossesblock;no emergingfoldchanges',
 'source_estimators':'exact original sourceGLM alpha1 plus200tree depth3 residual, sourcebuildingconstructionexcluded;no newvariables/capacity',
 'aggregation':'mean sqrt(source annualrates) then square, equal1/5fixed;targetGLM interceptfree/newbiz/regionridge1',
 'output':'R62/R63 fixed sqrt50%teacher-adapter+50%B20;R64/R65 natural unpooled correspondingoutputs;no optimizedweights',
 'real_fit_budget':60,'source_price_fits':30,'target_price_fits':30,'new_C0_fits':0,'primary_reference':'W2-COD-R36',
 'criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R62 standardGLM pooled,thenR63smalltrees pooled,thenR64standardGLM natural,thenR65smalltrees natural;onlyifallgatespass;otherwiseR36',
 '2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'budget':60,'synthetic':2}))
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
 old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas()
 receipts=[];outputs=[]
 for line in m.FEATURES:
  source=pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();blocks=pq.read_table(EXTRA/f'{line}.parquet').to_pandas();source=source.merge(blocks[m.KEY+['source_group_id','source_fold']],on=m.KEY,validate='one_to_one',how='left');assert source.source_fold.notna().all()
  memberdict={'glm':[],'trees':[]}
  for bag in range(5):
   fit_source=source[source.source_fold.ne(bag)].copy();held_source=source[source.source_fold.eq(bag)]
   for key in ['source_group_id','customer_id','address_id']:assert set(fit_source[key]).isdisjoint(held_source[key])
   event('source_bag_fit_started',line=line,bag=bag,rows=len(fit_source))
   with threadpool_limits(limits=2):result,rec=m.fit_teachers(fit_source,line)
   memberdict['glm'].append(result['W2-COD-R31']);memberdict['trees'].append(result['W2-COD-R32']);rec.update(bag=bag,role='source_bag',price_estimator_fits=2);receipts.append(rec)
   path=OUT/f'source_bags/{line}_bag{bag}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(result,path,compress=3);dump(path.with_suffix('.json'),rec);event('source_bag_fit_complete',line=line,bag=bag)
  teachers={recipe['id']:{'line':line,'family':'SourceComponentBags','members':memberdict[recipe['kind']]} for recipe in plan['models']};del source
  for mid,t in teachers.items():
   path=OUT/f'teachers/{mid}_{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3)
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
    pure=o.copy();pure['model_id']='W2-COD-R64' if recipe['kind']=='glm' else 'W2-COD-R65';pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure)
    event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'],completed=len(receipts))
 new=pd.concat(outputs,ignore_index=True);assert len(new)==4*50094 and not new.duplicated(['model_id']+m.KEY).any();new.to_parquet(OUT/'new_oof_2023.parquet',index=False)
 report=evaluate(pd.concat([old,inc],ignore_index=True),new,['W2-COD-R62','W2-COD-R63','W2-COD-R64','W2-COD-R65'],60,reference_id='W2-COD-R36')
 selected=next((x['model_id'] for x in report['gates'] if x['all_pass']),None);report.update(id=plan['id'],utc=now(),author='Codex',selected_exploratory_variant=selected,primary_reference='W2-COD-R36',source_support_not_emerging=True,formal_promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',summary=report['summaries'],gates=report['gates'],selected=selected)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
