"""Perfiles declarados: dos adaptadores GLM estándar y pool fijo del incumbente."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,sys,hashlib,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_perfil_declarado2023 as m
from semana2.evaluar_robustez2023_v3 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo9_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo9_plan.json'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023'
PROFILE=R/'privado/semana2/robustez2023/perfil_declarado2023_v1/customer_profile2023.parquet'
REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
FID='COD-S2-20261025-ROBUSTEZ9-PREVIO'
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,o):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(p):
 for s in p['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']
def event(name,**kw):
 rec={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
 print(json.dumps(rec),flush=True)
class FixedMatrix:
 def transform(self,f):return np.zeros((len(f),1))
class FixedRate:
 def predict(self,x):return np.full(len(x),500.)


def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
 n=600;rng=np.random.default_rng(2026102510);line='motor'
 f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'customer_id':['u'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 f['e_cost_mix_1.0']=f.exposure*.98
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['T0']=rng.poisson(.3,n)*rng.gamma(3,300,n)
 profiles=f[['market','customer_id']].copy();profiles['customer_since_year']=2020;profiles['x_declared_prior_claims_5y']=rng.integers(0,6,n);profiles['x_declared_gender']=np.where(np.arange(n)%2,'M','F')
 attached=m.attach(f,profiles);teacher={'line':line,'family':'SourceGLM','columns':['x_new_business'],'transformer':FixedMatrix(),'estimator':FixedRate()}
 receipts=[]
 for gender in [False,True]:
  with threadpool_limits(limits=2):b,receipt=m.fit(attached[attached.fold.ne(0)],line,0,{'id':'SYN','gender':gender,'synthetic':True,'_teacher':teacher})
  pred=m.predict(b,attached[attached.fold.eq(0)]);assert np.array_equal(pred,m.predict(b,attached[attached.fold.eq(0)].assign(T0=1e12)));receipts.append(receipt)
 for bad in [profiles.assign(customer_since_year=2024),pd.concat([profiles,profiles.iloc[:1]])]:
  try:m.attach(f,bad)
  except AssertionError:pass
  else:raise AssertionError('Perfil inválido admitido')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':2,'real_fits':0,'both_profile_GLM_flows':True,'held_labels_not_predictors':True,'future_join_rejected':True,'duplicate_profile_rejected':True,'receipts':receipts})
 sources=[PROFILE,REF,OLD,Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/desplegar_robustez2023.py',R/'src/semana2/evaluar_robustez2023_v3.py',
  R/'registro/semana2_perfil_declarado_admision_v1.json',R/'privado/semana2/robustez2023/perfil_declarado2023_v1/report.json',R/'privado/semana2/robustez2023/ciclo8_20261025_v1/official_pages_live_20261025.json']
 sources += list(m.TEACHERS.values())+[BASE/f'{line}_fold{fold}.parquet' for line in m.FEATURES for fold in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO9-v1-20261025','utc':now(),'author':'Codex','forum_prior':FID,
  'models':[{'id':'W2-COD-R40','gender':False,'declaration':'prior_claims5y only'}, {'id':'W2-COD-R41','gender':True,'declaration':'prior_claims5y plus genderM/F'}],
  'hypothesis':'Pre-joining self-declared claims may explain risk not captured by physical teacher. Optional gender explicitly permitted by host is tested as additional simple effect, only if incremental benefit justifies it.',
  'primary_reference':'W2-COD-R36','C0':'same outer fold cost mixture,T0/exposure unchanged','source_teachers_refitted':False,
  'adapter':'same fixed physical teacher; intercept free+newbusiness+region+log1p declared prior;gender optional. Ridge1 all except intercept.',
  'prior_transform':'fit-only median,clip0.005/0.995,StandardScaler after log1p;no actual claim histories derived',
  'categorical':'OHE dropfirst,min50,max40 fit-only;region and optional providedM/F',
  'price':'fixed sqrt pool50%newprofile-adapted teacher+50%B20 exactly as incumbentR36; no new weights',
  'real_fit_budget':30,'source_fits':0,'new_C0_fits':0,
  'primary_gates':{'delta_R36':.005,'lower_exploratory':.0005,'folds_min':4,'segment_harm_full_null':.0005,'after31groups':.0005},
  'extra_gender_veto':'both gender subgroup losses may not degrade >0.0005of full null relativeR36',
  'gender_increment_required_for_complexity':{'delta_R41_vs_R40':.002,'lower_exploratory':.0005},
  'choice':'R41 only if all primary+gender veto+increment pass,otherwise R40 if allprimary+gender veto pass;otherwise incumbentR36 retained',
  'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
  'availability':'experimental supplied-data benchmark, official pre-joining definition and permittedM/F;year consistency verified,capture versions/days not proven',
  'old_F0_default_and_hard_blocklist_not_rewritten':True,'2024_closed':True,'B00_preserved':True,'promotion':False,'no_auto_submission':True,
  'sources':[{'path':rel(p),'sha256':sha(p)} for p in sources]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan)
 print(json.dumps({'plan':rel(PLAN),'new_price_fits':30,'source_fits':0,'new_C0_fits':0,'profiles_admitted_conditionally':True}))


def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
 profiles=pq.read_table(PROFILE).to_pandas()
 incumbent=pq.read_table(REF,filters=[('model_id','=', 'W2-COD-R36'),('year','=',2023)]).to_pandas().sort_values(m.KEY).reset_index(drop=True)
 original=pq.read_table(OLD,filters=[('model_id','in',['W2-B00','W2-B20']),('year','=',2023)]).to_pandas()
 outputs=[];receipts=[];demographics=[]
 for line in m.FEATURES:
  for fold in range(5):
   rawcols=[c.replace('x_log_voluntary_excess','x_voluntary_excess').replace('x_log_compulsory_excess','x_compulsory_excess').replace('x_log_distance_to_river_km','x_distance_to_river_km') for c in m.FEATURES[line]['numeric']+m.FEATURES[line]['categorical']]
   cols=list(dict.fromkeys(m.KEY+['year','is_test','fold','group_id','customer_id','address_id','T0','exposure','e_cost_mix_1.0']+rawcols))
   frame=pq.read_table(BASE/f'{line}_fold{fold}.parquet',columns=cols,filters=[('year','=',2023)]).to_pandas();frame=m.attach(frame,profiles)
   fit=frame[frame.fold.ne(fold)].copy();val=frame[frame.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=incumbent[incumbent.line.eq(line)&incumbent.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   b20=original[original.model_id.eq('W2-B20')&original.line.eq(line)&original.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   assert val[m.KEY].equals(ref[m.KEY]) and b20[m.KEY].equals(ref[m.KEY])
   for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())
   demographics.append(val[m.KEY+['x_declared_gender']])
   for recipe in plan['models']:
    event('fit_started',model_id=recipe['id'],line=line,fold=fold)
    with threadpool_limits(limits=2):bundle,rec=m.fit(fit,line,fold,recipe);rate=m.predict(bundle,val)
    path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(bundle,path,compress=3)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
    rec.update(replay_exact=True,model_id=recipe['id']);dump(path.with_suffix('.json'),rec);receipts.append(rec)
    row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy()
    row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2
    row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
    event('fit_complete',model_id=recipe['id'],line=line,fold=fold,completed_fits=len(receipts))
 new=pd.concat(outputs,ignore_index=True);assert len(new)==2*50094 and not new.duplicated(['model_id']+m.KEY).any();new.to_parquet(OUT/'new_oof_2023.parquet',index=False)
 report=evaluate(pd.concat([original,incumbent],ignore_index=True),new,['W2-COD-R40','W2-COD-R41'],30,reference_id='W2-COD-R36')
 demo=pd.concat(demographics,ignore_index=True);assert len(demo)==50094 and not demo.duplicated(m.KEY).any()
 joined=pd.concat([original,incumbent,new],ignore_index=True).merge(demo,on=m.KEY,validate='many_to_one')
 fullnull=m.metrics(incumbent)['null_deviance_sum'];gender=[]
 for mid in ['W2-COD-R36','W2-COD-R40','W2-COD-R41']:
  for label,part in joined[joined.model_id.eq(mid)].groupby('x_declared_gender'):
   gender.append({'model_id':mid,'gender':str(label),**m.metrics(part)})
 for gate in report['gates']:
  deltas=[]
  for label in ['M','F']:
   candidate=next(x for x in gender if x['model_id']==gate['model_id'] and x['gender']==label)
   reference=next(x for x in gender if x['model_id']=='W2-COD-R36' and x['gender']==label)
   deltas.append({'gender':label,'delta_over_full_null':(reference['deviance_sum']-candidate['deviance_sum'])/fullnull})
  gate['gender_deltas']=deltas;gate['checks']['gender_harm']=min(x['delta_over_full_null'] for x in deltas)>=-.0005;gate['all_pass']=all(gate['checks'].values())
 increment=report['pairwise_between_new_models'][0];increment_ok=increment['delta_D2']>=.002 and increment['exploratory_interval'][0]>.0005
 g40=next(x for x in report['gates'] if x['model_id']=='W2-COD-R40')['all_pass'];g41=next(x for x in report['gates'] if x['model_id']=='W2-COD-R41')['all_pass']
 selected='W2-COD-R41' if g41 and increment_ok else ('W2-COD-R40' if g40 else None)
 report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',source_models_refitted=False,profile_availability_conditional=True,
  gender_diagnostics=gender,gender_incremental_criterion_passed=increment_ok,selected_exploratory_variant=selected,formal_promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report)
 dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]})
 event('complete',summary=report['summaries'],gates=report['gates'],gender_increment=increment,selected=selected)


if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['prepare','run']);args=a.parse_args()
 if args.action=='prepare':prepare()
 else:run()
