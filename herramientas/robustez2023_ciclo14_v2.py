"""Perfiles declarados: dos adaptadores GLM estándar y pool fijo del incumbente."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,sys,hashlib,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_pendiente_riesgo2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo14_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo14_plan_v2.json'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023'
PROFILE=R/'privado/semana2/robustez2023/contrato_comercial2023_v1'
REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
FID='COD-S2-20261025-ROBUSTEZ14-PREVIO'
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
 def transform(self,f):return f[['x_ncb_years']].to_numpy(float)
class FixedRate:
 def predict(self,x):return 500.*np.exp(.2*x[:,0])


def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
 n=600;rng=np.random.default_rng(2026102513);line='motor'
 f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 f['e_cost_mix_1.0']=f.exposure*.98
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['T0']=rng.poisson(.3,n)*rng.gamma(3,300,n);f['x_days_quote_to_inception']=rng.integers(0,90,n);f['x_renewal_count']=rng.integers(0,8,n);f['x_channel']=np.where(np.arange(n)%2,'direct','broker');f['x_payment_method']=np.where(np.arange(n)%3,'annual','monthly')
 teacher={'line':line,'family':'SourceGLM','columns':['x_ncb_years'],'transformer':FixedMatrix(),'estimator':FixedRate()}
 receipts=[]
 for boosted in [False,True]:
  with threadpool_limits(limits=2):b,rec=m.fit(f[f.fold.ne(0)],line,0,{'id':'SYN','source_trees':boosted,'synthetic':True,'_teacher':teacher})
  val=f[f.fold.eq(0)];assert np.array_equal(m.predict(b,val),m.predict(b,val.assign(T0=1e12)));receipts.append(rec)
 dump(OUT/'synthetic.json',{'synthetic_price_fits':2,'held_labels_not_predictors':True,'receipts':receipts})
 sources=list(PROFILE.glob('*'))+[REF,OLD,Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelo_basicas_fuente2023_v2.py',R/'src/semana2/modelo_basicas_fuente2023.py',R/'src/semana2/desplegar_robustez2023.py',R/'src/semana2/evaluar_robustez2023_v2.py']
 sources+=list(m.TEACHERS.values())+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO14-v1-20261025','author':'Codex','utc':now(),'forum_prior':FID,
 'models':[{'id':'W2-COD-R51','source_trees':False},{'id':'W2-COD-R52','source_trees':True}],'extra_output_model':'W2-COD-R53',
 'hypothesis':'Transported relative risk is forced to power1 in R35/R36. Fit one bounded risk-index slope perline/fold to test dispersion transport, without more physical predictors or trees.',
 'new_features':[],'risk_slope':'log source rate standardized fitonly;delta slope ridge1 toward power1, bounded power0to2;intercept free and newbusiness/region ridge1',
 'adapter':'same minimal target GLM with one additional transported risk slope;fitonly scaling, no future outcomes',
 'R49':'standard sourceGLM teacher, no boostedtrees','R50':'original source200tree teacher, no more capacity',
 'price':'R51/R52 fixed sqrt50%candidate+50%B20 asR36;R53 is natural unpooled R52 output using same fits;no weights optimized',
 'primary_reference':'W2-COD-R36','2023_folds':'same five saved connected groups;exact T0/C0/exposure',
 'real_fit_budget':30,'source_fits':0,'new_C0_fits':0,
 'criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R49 GLM if allpass,elseR50 if allpass,otherwiseR36;no finalpromotion or auto submission',
 '2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in sources]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'new_fits':30,'source_fits':0,'C0':0}))


def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})

 incumbent=pq.read_table(REF,filters=[('model_id','=', 'W2-COD-R36'),('year','=',2023)]).to_pandas().sort_values(m.KEY).reset_index(drop=True)
 original=pq.read_table(OLD,filters=[('model_id','in',['W2-B00','W2-B20']),('year','=',2023)]).to_pandas()
 outputs=[];receipts=[];demographics=[]
 for line in m.FEATURES:
  for fold in range(5):
   rawcols=[c.replace('x_log_voluntary_excess','x_voluntary_excess').replace('x_log_compulsory_excess','x_compulsory_excess').replace('x_log_distance_to_river_km','x_distance_to_river_km') for c in m.FEATURES[line]['numeric']+m.FEATURES[line]['categorical']]
   cols=list(dict.fromkeys(m.KEY+['year','is_test','fold','group_id','customer_id','address_id','T0','exposure','e_cost_mix_1.0']+rawcols))
   frame=pq.read_table(BASE/f'{line}_fold{fold}.parquet',columns=cols,filters=[('year','=',2023)]).to_pandas()
   fit=frame[frame.fold.ne(fold)].copy();val=frame[frame.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=incumbent[incumbent.line.eq(line)&incumbent.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   b20=original[original.model_id.eq('W2-B20')&original.line.eq(line)&original.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   assert val[m.KEY].equals(ref[m.KEY]) and b20[m.KEY].equals(ref[m.KEY])
   for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())

   for recipe in plan['models']:
    event('fit_started',model_id=recipe['id'],line=line,fold=fold)
    with threadpool_limits(limits=2):bundle,rec=m.fit(fit,line,fold,recipe);rate=m.predict(bundle,val)
    path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(bundle,path,compress=3)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
    rec.update(replay_exact=True,model_id=recipe['id']);dump(path.with_suffix('.json'),rec);receipts.append(rec)
    row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy()
    row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2
    row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
    if recipe['id']=='W2-COD-R52':
     pure=row.copy();pure['model_id']='W2-COD-R53';pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure)
    event('fit_complete',model_id=recipe['id'],line=line,fold=fold,completed_fits=len(receipts))
 new=pd.concat(outputs,ignore_index=True);assert len(new)==3*50094 and not new.duplicated(['model_id']+m.KEY).any();new.to_parquet(OUT/'new_oof_2023.parquet',index=False)
 report=evaluate(pd.concat([original,incumbent],ignore_index=True),new,['W2-COD-R51','W2-COD-R52','W2-COD-R53'],30,reference_id='W2-COD-R36')
 selected=next((g['model_id'] for g in report['gates'] if g['all_pass']),None)
 report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',source_models_refitted=False,risk_slope_calibrated=True,selected_exploratory_variant=selected,formal_promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report)
 dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]})
 event('complete',summary=report['summaries'],gates=report['gates'],selected=selected)


if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['prepare','run']);args=a.parse_args()
 if args.action=='prepare':prepare()
 else:run()
