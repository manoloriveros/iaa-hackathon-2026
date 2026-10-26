"""Varianza de trabajo de fuente solo autos, cinco bloques antes de transferir."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_fuente_varianza2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo33_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo33_plan.json';SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/motor_2023.parquet';BLOCKS=R/'privado/semana2/robustez2023/bloques_fuente2023_v1/motor.parquet';BAGS=R/'privado/semana2/robustez2023/ciclo17_20261025_v1/source_bags';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
RECIPES=[{'id':'W2-COD-R128','kind':'glm','reference':'W2-COD-R31'},{'id':'W2-COD-R129','kind':'trees','reference':'W2-COD-R32'}];NATURAL={'W2-COD-R128':'W2-COD-R130','W2-COD-R129':'W2-COD-R131'};IDS=[x['id'] for x in RECIPES]+list(NATURAL.values())
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()

def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as h:json.dump(x,h,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))

def event(name,**kw):
 row={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf8') as h:h.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)

def synthetic():
 rng=np.random.default_rng(2026102533);n=1200;f=pd.DataFrame({'market':'emerging','line':'motor','row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 for c in m.FEATURES['motor']['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES['motor']['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n);val=f[f.fold.eq(0)];parents={};notes=[]
 for recipe in RECIPES:
  with threadpool_limits(limits=2):t,rec=m.fit_source(f.assign(market='developed'),'motor',recipe['kind'],parent=parents.get('glm'));parents[recipe['kind']]=t;b,_=m.fit(f[f.fold.ne(0)],'motor',0,t,'SYN');p=m.predict(b,val)
  assert np.array_equal(p,m.predict(b,val.assign(T0=1e15)));notes.append(rec)
  try:m.predict(b,val.assign(year=2024))
  except AssertionError:pass
  else:raise AssertionError('2024 accepted')
 # Annual-rate p-loss weighted by e**(2-p) equals total-period p-loss exactly.
 e=f.exposure.to_numpy();y=f.T0.to_numpy();mu=np.full(n,100.)*e;p=m.POWER
 def dev(y,mu):return 2*(y**(2-p)/((1-p)*(2-p))-y*mu**(1-p)/(1-p)+mu**(2-p)/(2-p))
 assert np.allclose(dev(y,mu),e**(2-p)*dev(y/e,mu/e),rtol=1e-12,atol=1e-10)
 dump(OUT/'synthetic.json',{'synthetic_price_fits':4,'source_working_power':1.8,'evaluation_and_target_power_unchanged':1.5,'exposure_homogeneity_identity':True,'held_label_poison_invariant':True,'2024_rejected':True,'source_receipts':notes})

def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_fuente_penalizacion2023.py',R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',SOURCE,BLOCKS,REF,OLD,R/'privado/semana2/robustez2023/ciclo30_20261025_v1/report.json',R/'privado/semana2/robustez2023/ciclo31_20261025_v1/report.json']+[BAGS/f'motor_bag{k}.joblib' for k in range(5)]+[BASE/f'motor_fold{k}.parquet' for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO33-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ33-PREVIO','models':RECIPES,'natural_outputs':NATURAL,
 'hypothesis':'Motornewbusiness remains weak underR36. Expanded targetcorrectionsC30 and sourceadditivesC31 didnotresolveit;C31sourcecurvesincreasedmotor loss. Test one standardGLM workingvariance1.8 with SAMElinearphysicalmean to change variance weighting without more mean parameters or trimming claims. No guarantee that sourceworkingvariance transports.',
 'source_GLM':'Tweedie1.8,weights exposure**.2;alpha=1*fitonlyannualconstantmean**(1.5-1.8),matchingexpectedlocalcurvature of oldridge1 atfitonlyanchor;samelinearphysicalpredictors/median/clip.005,.995/scale/OHEmin100max40dropfirst,regionexcluded',
 'source_tree':'optional ORIGINAL200depth3Tweedie1.5 residual withsqrt(exposure)weights andsamecapacity,seed2026102506;onlyparent changes',
 'evaluation':'allsourceveto andprimarytargetmetrics remain total-periodTweedie1.5;targetminimaladapter remains1.5. Workingvariance is NOT a change in target,T0,exposure,C0,evaluationmetric orcase inclusion',
 'source_veto':'five fixedsourcecomponentfolds,sameheldrows/referenceC17samefamily;pooledloss<=1.002 and>=4/5folds withrelative loss<=.002;failfamily nottransferred;already adaptivelyseenblocks',
 'budget_max':22,'source_pilot_fits':10,'source_full_fits_max':2,'target_adapter_fits_max':10,'new_C0_fits':0,
 'outputs':'motorR128/R129fixedsqrt50/50B20;R130/R131natural;allhome rows copiedR36 exactly,no newinference;no optimizedweights',
 'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'preference_order':IDS,
 'scope':'strict2023 only,five savedemergingcomponentfolds,fulloriginallosses/exposure retained;noC0refit,climate orpremium predictors','limits':'propermeanloss doesnot proveequalbestprojectedmean or transportability;incurredto ultimateandtail uncertaintyremain;no2024confirmation','pending_public_CSVs_unchanged':True,'2024_closed':True,'B00_preserved':True,'promotion':False,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'real_fit_budget':22,'synthetic_fits':4}))

def check(plan):
 for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256'],x['path']

def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];pilots=[]
 f=pq.read_table(SOURCE,filters=[('year','=',2023)]).to_pandas();blocks=pq.read_table(BLOCKS).to_pandas();f=f.merge(blocks[m.KEY+['source_group_id','source_fold']],on=m.KEY,how='left',validate='one_to_one');assert f.source_fold.notna().all()
 for fold in range(5):
  fit=f[f.source_fold.ne(fold)].copy();val=f[f.source_fold.eq(fold)].copy();parents={};ref=joblib.load(BAGS/f'motor_bag{fold}.joblib')
  for key in ['source_group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
  for recipe in RECIPES:
   event('source_pilot_started',fold=fold,model_id=recipe['id'])
   with threadpool_limits(limits=2):t,rec=m.fit_source(fit,'motor',recipe['kind'],parent=parents.get('glm'));a=m.teacher_rate(t,val)*val.exposure.to_numpy();b=m.old.teacher_rate(ref[recipe['reference']],val)*val.exposure.to_numpy()
   parents[recipe['kind']]=t;rec.update(role='source_pilot',fold=fold,model_id=recipe['id']);receipts.append(rec);path=OUT/f'pilot_models/{recipe["id"]}_motor_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);dump(path.with_suffix('.json'),rec)
   with threadpool_limits(limits=2):assert np.array_equal(a,m.teacher_rate(joblib.load(path),val)*val.exposure.to_numpy())
   row={'fold':fold,'model_id':recipe['id'],'candidate_loss':float(m.unit_deviance(val.T0,a).sum()),'reference_loss':float(m.unit_deviance(val.T0,b).sum()),'replay_exact':True,'groups_disjoint':True};row['relative_difference']=row['candidate_loss']/row['reference_loss']-1;pilots.append(row);dump(OUT/f'pilot_metrics/{recipe["id"]}_fold{fold}.json',row);event('source_pilot_complete',**row)
 summaries=[];eligible=[]
 for recipe in RECIPES:
  rows=[x for x in pilots if x['model_id']==recipe['id']];ratio=sum(x['candidate_loss'] for x in rows)/sum(x['reference_loss'] for x in rows)-1;folds=sum(x['relative_difference']<=.002 for x in rows);passed=bool(ratio<=.002 and folds>=4);summaries.append({'model_id':recipe['id'],'line':'motor','pooled_relative_loss':ratio,'folds_inside_tolerance':folds,'pass':passed})
  if passed:eligible.append(recipe['id'])
 dump(OUT/'source_veto.json',{'summaries':summaries,'eligible':eligible})
 if not eligible:
  base=read(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json');report={'summaries':[x for x in base['summaries'] if x['model_id'] in ['W2-B00','W2-B20','W2-COD-R36']],'gates':[],'pairs':[],'new_price_fits':len(receipts),'new_C0_fits':0,'stop_reason':'sourceworkingvariancefamiliesfailed;notargetfits','selected_exploratory_variant':None,'2024_closed':True,'B00_preserved':True}
 else:
  teachers={}
  for recipe in RECIPES:
   if recipe['kind']=='trees' and recipe['id'] not in eligible:continue
   event('source_full_started',model_id=recipe['id'])
   with threadpool_limits(limits=2):t,rec=m.fit_source(f,'motor',recipe['kind'],parent=teachers.get('glm'))
   teachers[recipe['kind']]=t;rec.update(role='source_full',model_id=recipe['id']);receipts.append(rec);path=OUT/f'teachers/{recipe["id"]}_motor.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);dump(path.with_suffix('.json'),rec)
  inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();outputs=[]
  for fold in range(5):
   z=pq.read_table(BASE/f'motor_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas();fit=z[z.fold.ne(fold)].copy();val=z[z.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=inc[inc.line.eq('motor')&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.eq('motor')&old.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
   for col in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[col].to_numpy(),ref[col].to_numpy())
   for recipe in RECIPES:
    if recipe['id'] not in eligible:continue
    with threadpool_limits(limits=2):b,rec=m.fit(fit,'motor',fold,teachers[recipe['kind']],recipe['id']);rate=m.predict(b,val)
    rec.update(role='target',replay_exact=True);receipts.append(rec);path=OUT/f'models/{recipe["id"]}_motor_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3);dump(path.with_suffix('.json'),rec)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
    row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row);pure=row.copy();pure['model_id']=NATURAL[recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fold_complete',model_id=recipe['id'],fold=fold)
  ids=[x for x in IDS if x in eligible or x in [NATURAL[q] for q in eligible]]
  for mid in ids:
   home=inc[inc.line.ne('motor')].copy();home['model_id']=mid;outputs.append(home)
  new=pd.concat(outputs,ignore_index=True);assert len(new)==len(ids)*50094 and not new.duplicated(['model_id']+m.KEY).any();new.to_parquet(OUT/'new_oof_2023.parquet',index=False);report=evaluate(pd.concat([old,inc],ignore_index=True),new,ids,len(receipts),reference_id='W2-COD-R36');report.update(home_exact_R36=True,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None))
 report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',source_eligible=eligible,source_gate=summaries,promotion=False);check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=len(receipts),gates=report['gates'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
