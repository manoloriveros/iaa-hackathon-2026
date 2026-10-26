"""Faltantes como efectos de GLM de destino; comparación con cero sin refit."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_faltantes_destino2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from sklearn.preprocessing import FunctionTransformer
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo36_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo36_plan.json';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet';RECIPES={'id':'W2-COD-R140'};IDS=['W2-COD-R140','W2-COD-R141']
now=lambda:datetime.now(timezone.utc).isoformat();read=lambda p:json.loads(p.read_text(encoding='utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def original_path(line,k):return R/f'privado/semana2/robustez2023/ciclo{7 if line=="buildings" else 6}_20261025_v1/models/W2-COD-R{35 if line=="buildings" else 32}_{line}_fold{k}.joblib'
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as h:json.dump(x,h,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def event(name,**kw):
 row={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf8') as h:h.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)
class FixedRate:
 def predict(self,x):return np.full(len(x),100.)

def synthetic():
 rng=np.random.default_rng(2026102536);notes=[]
 for line in m.FEATURES:
  n=1200;f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
  for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
  for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  for c in m.MISSING[line]:f.loc[rng.random(n)<.12,c]=np.nan
  f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n);teacher={'line':line,'family':'SourceGLM','columns':['x_new_business'],'transformer':FunctionTransformer(),'estimator':FixedRate()};fit=f[f.fold.ne(0)];val=f[f.fold.eq(0)]
  with threadpool_limits(limits=2):original,_=m.old.fit(fit,line,0,{'id':'SYN','synthetic':True,'_teacher':teacher});mapped,note=m.control(fit,line,0,original);a=m.predict(mapped,val);b=m.old.predict(original,val);assert np.allclose(a,b,rtol=1e-12,atol=1e-12);new,rec=m.fit(fit,line,0,{'id':'SYN','synthetic':True,'_teacher':teacher});p=m.predict(new,val)
  assert np.array_equal(p,m.predict(new,val.assign(T0=1e15)));dense=m.old.teacher_rate(teacher,m.features(val,line))*np.exp(m.matrix(m.features(val,line),new).toarray()@new['coef']);assert np.allclose(p,dense,rtol=1e-14,atol=1e-12)
  try:m.predict(new,val.assign(year=2024))
  except AssertionError:pass
  else:raise AssertionError('2024 accepted')
  notes.append(note)
 dump(OUT/'synthetic.json',{'synthetic_price_fits':6,'old_minimal_controls':3,'new_flag_adapters':3,'new_source_fits':0,'zero_flags_embedding_matches_old':True,'dense_formula_checked':True,'held_label_poison_invariant':True,'2024_rejected':True,'controls':notes})

def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/desplegar_robustez2023.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,R/'privado/semana2/robustez2023/ciclo35_20261025_v1/report.json',R/'privado/semana2/robustez2023/mision017_20261025_v1/numeric_overlap2023_v3.json']+list(m.TEACHERS.values())+[original_path(line,k) for line in m.FEATURES for k in range(5)]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO36-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ36-PREVIO','models':[RECIPES],'natural_output':'W2-COD-R141','hypothesis':'C26marginalmasking andC35covariateweightsdidnot improve risk. Originalminimaltargetadapterhasnoexplicitnumericmissingness terms,whilemedian sourceGLM conflatesmissingwithtypical values;nativeNA source trees neednot transportmissingnessmeaning. Testonly2targetmissingflags/line with strongridge10,not extra rawcovariates orsourcecapacity. Marketclassification shift is NOT evidence thatmissingnesspredictsclaims.',
 'flags':m.MISSING,'flag_definition':'isna of existing admitted numeric attrs after originallog derivation/before imputation;no new externalinfo,dates,premium,claims orfutureweather','missing_penalty':10.,'penalty_rationale':'one fixedconservativecorrectionstrength10 already usedinC15;not a sweep or chosenusingnewflaglosses;commonNB/regionridge1 andfreeintercept unchanged',
 'model':'same frozen3physicalsource teachers;minimalTweedie1.5adapter plus2missingindicator coefficients;alllearning excludesheld2023fold;regionencoderfitonly;no source/oldbaseline refit',
 'control':'map stored originalminimaladapter coefficients intoextendeddesignwithtwozeros,0fits. Objectiveandheldpredictions equal;newflaggradients need NOT be zero;then fit15newadapters. Comparealloutputs toR36primary,not mappednatural baseline.',
 'real_fit_budget':15,'new_source_fits':0,'new_C0_fits':0,'new_domain_fits':0,'outputs':'R140fixedsqrt50/50B20;R141natural;no learnedweights','primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'preference_order':IDS,
 'scope':'strict2023/saved5componentfolds,T0/exposure/existingC0 unchanged','availability_limits':'flags use onlyexistingquoteattributeabsence;missingnessmechanism andbitemporalavailability notestablished byclassification. Same retrospective2023inputcontract,notprospectiveavailabilityproof. No use excluded daysunoccupied orfutureattrs.',
 '2024_closed':True,'B00_preserved':True,'promotion':False,'adaptive_exploratory':True,'public_frozen_CSVs_unchanged':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'real_price_fits_max':15,'new_source_fits':0,'new_C0':0,'synthetic_price_fits':6}))

def check(plan):
 for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256'],x['path']

def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];controls=[];outputs=[];inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();natural=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R35')]).to_pandas();old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas()
 for line in m.FEATURES:
  for k in range(5):
   f=pq.read_table(BASE/f'{line}_fold{k}.parquet',filters=[('year','=',2023)]).to_pandas();fit=f[f.fold.ne(k)].copy();val=f[f.fold.eq(k)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   original=joblib.load(original_path(line,k));assert joblib.hash(original['teacher'])==joblib.hash(joblib.load(m.TEACHERS[line]))
   with threadpool_limits(limits=2):mapped,note=m.control(fit,line,k,original);before=m.predict(mapped,val);expected=m.old.predict(original,val)
   assert np.allclose(before,expected,rtol=1e-12,atol=1e-12);prior=natural[natural.line.eq(line)&natural.fold.eq(k)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(prior[m.KEY]) and np.allclose(before*val['e_cost_mix_1.0'].to_numpy(),prior.prediction.to_numpy(),rtol=1e-12,atol=1e-10);note['held_prediction_matches_stored_natural_OOF']=True;controls.append(note);dump(OUT/f'controls/{line}_fold{k}.json',note)
   ref=inc[inc.line.eq(line)&inc.fold.eq(k)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.eq(line)&old.fold.eq(k)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
   for col in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[col].to_numpy(),ref[col].to_numpy())
   with threadpool_limits(limits=2):b,rec=m.fit(fit,line,k,RECIPES);rate=m.predict(b,val)
   path=OUT/f'models/W2-COD-R140_{line}_fold{k}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
   with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
   rec['replay_exact']=True;receipts.append(rec);dump(path.with_suffix('.json'),rec);row=ref.copy();row['model_id']='W2-COD-R140';row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row);pure=row.copy();pure['model_id']='W2-COD-R141';pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fit_complete',line=line,fold=k)
 new=pd.concat(outputs,ignore_index=True);assert len(new)==2*50094 and len(receipts)==15;new.to_parquet(OUT/'new_oof_2023.parquet',index=False);report=evaluate(pd.concat([old,inc],ignore_index=True),new,IDS,len(receipts),reference_id='W2-COD-R36');report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',coordinate_controls=controls,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False);check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=15,gates=report['gates'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
