"""Siete efectos de B20 o bloque físico, mismo alpha1, sin nuevos profesores."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_correccion_core2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
from sklearn.linear_model import TweedieRegressor
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo30_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo30_plan.json';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet';COREPLAN=R/'registro/semana2_glm_ridge_coberturas_plan_v1.json'
RECIPES=[{'id':'W2-COD-R116','block':'core7'},{'id':'W2-COD-R117','block':'full'}];NATURAL={'W2-COD-R116':'W2-COD-R118','W2-COD-R117':'W2-COD-R119'};IDS=[x['id'] for x in RECIPES]+list(NATURAL.values())
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(plan):
 for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256'],x['path']
def event(name,**kw):
 row={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as h:h.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)
class FixedMatrix:
 def transform(self,f):return np.zeros((len(f),1))
class FixedRate:
 def predict(self,x):return np.full(len(x),500.)
def synthetic():
 n=1200;rng=np.random.default_rng(2026102530);controls=[]
 for line in m.FEATURES:
  f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
  for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
  for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n);teacher={'line':line,'family':'SourceGLM','columns':['x_new_business'],'transformer':FixedMatrix(),'estimator':FixedRate()};fit=f[f.fold.ne(0)];val=f[f.fold.eq(0)]
  for recipe in RECIPES:
   with threadpool_limits(limits=2):b,rec=m.fit(fit,line,0,{**recipe,'synthetic':True,'_teacher':teacher});x=b['transformer'].transform(m.features(fit,line)[b['columns']]);reference=TweedieRegressor(power=1.5,alpha=1.,link='log',max_iter=3000,tol=1e-10);reference.fit(x,fit.T0.to_numpy()/fit['e_cost_mix_1.0'].to_numpy(),sample_weight=np.sqrt(fit['e_cost_mix_1.0']));pred=m.predict(b,val);expected=reference.predict(b['transformer'].transform(m.features(val,line)[b['columns']]))
   assert np.allclose(pred,expected,rtol=2e-5,atol=1e-6) and np.array_equal(pred,m.predict(b,val.assign(T0=1e15)));controls.append({'line':line,'block':recipe['block'],'max_relative_difference_sklearn':float(np.max(np.abs(pred/expected-1))),'held_label_poison_invariant':True})
  try:m.predict(b,val.assign(year=2024))
  except AssertionError:pass
  else:raise AssertionError('2024 aceptado')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':12,'custom_offset_GLMS':6,'independent_sklearn_GLMs':6,'constant_offset_free_intercept_equivalence':True,'controls':controls,'2024_rejected':True})
def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic();old=read(COREPLAN)['recipe']['features_by_line']
 for line in m.CORE:assert m.CORE[line]=={k:old[line][k] for k in ['numeric','categorical']}
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/desplegar_robustez2023.py',R/'src/semana2/evaluar_robustez2023_v2.py',COREPLAN,REF,OLD,R/'registro/semana2_robustez2023_ciclo15_plan.json',R/'privado/semana2/robustez2023/ciclo15_20261025_v1/report.json']+list(m.TEACHERS.values())+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO30-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ30-PREVIO','models':RECIPES,'natural_outputs':NATURAL,'hypothesis':'C15fullphysicalcorrectionswereheavilyshrunk10/100 anddidnotrobustlyimprove. Test standardalpha1alreadyfixedinB20,with either thesame7B20maineffects or fulladmittedphysicalblock,to distinguishlimiteddomainadjustmentfrom extraparameters. Frozen source shape is an offset,not newlyfitted.',
 'source':'same originalfrozen3physicalteachers ofR36;no masks ornewsourcefits','blocks':{'core7':m.CORE,'full':m.FEATURES},'model':'offsetTweedie1.5,interceptfree,alpha1allstandardizednumeric/onehotcorrections;fitonlymedian/clip.005/.995/scale,OHEmin100max40dropfirst',
 'alpha_rationale':'same priorB20alpha1,not new grid orpublictuning;onlyone alpha inthisrecipe','scope':'same5saved2023emergingcomponentfolds;T0/exposure/existingC0 unchanged;no2024orclimateadmission',
 'outputs':'R116/R117fixedsqrt50/50B20;R118/R119natural;fixedweights','real_fit_budget':30,'new_source_fits':0,'new_C0_fits':0,'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'preference_order':IDS,'2024_closed':True,'B00_preserved':True,'promotion':False,'adaptive_exploratory':True,'pending_public_CSVs_unchanged':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'newfits_max':30,'newsource':0,'newC0':0,'synthetic_fits':12}))
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];outputs=[];inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas()
 for line in m.FEATURES:
  for fold in range(5):
   f=pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas();fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=inc[inc.line.eq(line)&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.eq(line)&old.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
   for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())
   for recipe in RECIPES:
    event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
    with threadpool_limits(limits=2):b,rec=m.fit(fit,line,fold,recipe);rate=m.predict(b,val)
    p=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';p.parent.mkdir(exist_ok=True);joblib.dump(b,p,compress=3)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(p),val))
    rec['replay_exact']=True;receipts.append(rec);dump(p.with_suffix('.json'),rec);row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row);pure=row.copy();pure['model_id']=NATURAL[recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'])
 new=pd.concat(outputs,ignore_index=True);new.to_parquet(OUT/'new_oof_2023.parquet',index=False);report=evaluate(pd.concat([old,inc],ignore_index=True),new,IDS,len(receipts),reference_id='W2-COD-R36');report.update(id=plan['id'],author='Codex',utc=now(),primary_reference='W2-COD-R36',selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False);check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=len(receipts),gates=report['gates'],selected=report['selected_exploratory_variant'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
