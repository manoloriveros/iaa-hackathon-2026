"""Prueba preinscrita de marginalización de edad; veto fuente y folds2023."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,sys,json,hashlib,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_edad_marginal2023_v2 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo20_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo20_plan_v2.json'
SOURCE=R/'privado/semana2/robustez2023/edad2023_inputs_v1';BLOCKS=R/'privado/semana2/robustez2023/bloques_fuente2023_v1';BAGS=R/'privado/semana2/robustez2023/ciclo17_20261025_v1/source_bags';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
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
 n=1200;rng=np.random.default_rng(2026102520);line='motor';age=rng.integers(17,91,n)
 f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n),'x_exact_age':age})
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_transport_band']=pd.cut(age,[16,24,34,49,64,np.inf],labels=m.BANDS).astype(str);f['x_driver_age_band']=f.x_transport_band;f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n);source=f.assign(market='developed')
 with threadpool_limits(limits=2):teachers,source_note=m.train_source(source,line)
 notes=[];checks=[]
 for kind,t in teachers.items():
  coarse=f.drop(columns='x_exact_age');fit=coarse[coarse.fold.ne(0)];val=coarse[coarse.fold.eq(0)]
  with threadpool_limits(limits=2):b,note=m.fit(fit,line,0,t,'SYN');pred=m.predict(b,val);poison=m.predict(b,val.assign(x_exact_age=1e15,T0=1e15));assert np.array_equal(pred,poison)
  row=val.iloc[[0]].copy();band=row.x_transport_band.iloc[0];tab=t['density']['tables'][band];cell=str(m.licence_cell(row,line)[0]);p=tab['cells'].get(cell,tab['fallback_probabilities']);manual=0.
  with threadpool_limits(limits=2):
   for a,w in zip(tab['ages'],p):manual+=w*m.fine_rate(t['price'],row.assign(x_exact_age=a))[0]
   automatic=m.marginal_rate(t,row)[0]
  assert np.isclose(manual,automatic,rtol=1e-12);notes.append(note);checks.append({'kind':kind,'arithmetic_mean_exact':True,'hidden_age_poison_invariant':True,'held_outcome_poison_invariant':True})
 try:m.marginal_rate(teachers['glm'],coarse.iloc[:2].assign(x_transport_band='unknown'))
 except AssertionError:pass
 else:raise AssertionError('Banda desconocida admitida')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':4,'source_note':source_note,'target_notes':notes,'checks':checks,'unknown_band_rejected':True,'new_real_fits':0})
def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,SOURCE/'report.json',BLOCKS/'report.json',R/'privado/semana2/robustez2023/edad2023_auditoria_v1/report.json']
 paths += list(SOURCE.glob('*.parquet'))+[BLOCKS/f'{line}.parquet' for line in m.FEATURES]+[BAGS/f'{line}_bag0.joblib' for line in m.FEATURES]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO20-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ20-PREVIO',
 'models':[{'id':'W2-COD-R74','kind':'glm'},{'id':'W2-COD-R75','kind':'trees'}],'natural_outputs':{'W2-COD-R74':'W2-COD-R76','W2-COD-R75':'W2-COD-R77'},
 'hypothesis':'Developed age is exact,emerging age is banded. Fit source fine-age risk then integrate its annual mean over a source-only age distribution conditional on band/licencecell,instead of midpoint imputation or discarding exact source measurement. Test standardGLM plus originalsmalltree form.',
 'age_rule':'retain supplied source inception-age,no DOB replacement or correction;no target exactage exists;home DOB audit discrepancies remain disclosed',
 'source_age_effect':'six quantile knots degree2 additive spline of exactage,ridge1;other physical main effects same;source region/buildingconstruction excluded;optional same200treesdepth3 residual',
 'density':'source exposure-weighted integer-age distribution in each observed band;20exposure-year uniform prior for band and20global-band prior for licencecell;licencebins(-inf,1,4,9,19,39,inf),unknown fallbackband;no outcomes used;homeconditionbandonly',
 'marginalization':'exact arithmetic conditionalmean ofsource annualrates over all observed integer-age support,not meanroots and not one imputed age;source65+ support17to90 overall is empirical,transportability notproven',
 'source_veto':'hold block0sourcecomponents,fit price/density excludingblock0;validation exactage removed. Compare GLM to C17bag0coarseGLM,andtrees tocoarsetrees;eachline loss<=1.002reference. If nofamilypasses all3 stop beforefullsource/target.',
 'budget_max':42,'source_pilot_fits':6,'full_source_fits_max':6,'target_adapter_fits_max':30,'density_objects_max':6,'new_C0_fits':0,
 'adapter':'same minimal interceptfree+newbusiness/regionridge1 in five saved emerging2023componentfolds',
 'outputs':'R74/R75 fixedsqrt50%candidate+50%B20 exactlyR36;R76/R77 natural output;samefits;no learnedweights',
 'age_distribution_stress':'fixedmodel,no refit;50%conditionalageprobabilities+50%unconditionalbandprobabilities. Requires nonnegative overallD2gain vsR36 under stress in addition to allprimarygates.',
 'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R74standardGLMpool,thenR75smalltreespool,thenR76standardnatural,thenR77smalltreesnatural;allsource+primary+agestressgates required;otherwiseR36',
 '2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'promotion':False,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'fit_budget_max':42,'synthetic_fits':4,'source_veto_before_fullfit':True}))
def load_source(line):
 f=pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();blocks=pq.read_table(BLOCKS/f'{line}.parquet').to_pandas();f=f.merge(blocks[m.KEY+['source_group_id','source_fold']],on=m.KEY,validate='one_to_one');assert f.source_fold.notna().all();return f
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];pilots=[]
 for line in m.FEATURES:
  f=load_source(line);fit=f[f.source_fold.ne(0)].copy();val=f[f.source_fold.eq(0)].drop(columns='x_exact_age').copy()
  for key in ['source_group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
  event('source_pilot_started',line=line,fit_rows=len(fit),validation_rows=len(val))
  with threadpool_limits(limits=2):teachers,note=m.train_source(fit,line)
  note['role']='source_pilot';receipts.append(note);path=OUT/f'pilot_models/{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(teachers,path,compress=3);dump(path.with_suffix('.json'),note);baseline=joblib.load(BAGS/f'{line}_bag0.joblib')
  for recipe in plan['models']:
   kind=recipe['kind'];reference='W2-COD-R31' if kind=='glm' else 'W2-COD-R32'
   with threadpool_limits(limits=2):oldpred=m.old.teacher_rate(baseline[reference],val)*val.exposure.to_numpy();pred=m.marginal_rate(teachers[kind],val)*val.exposure.to_numpy()
   oldloss=float(m.unit_deviance(val.T0,oldpred).sum());loss=float(m.unit_deviance(val.T0,pred).sum());rec={'line':line,'model_id':recipe['id'],'reference_family':reference,'fit_rows':len(fit),'validation_rows':len(val),'reference_loss':oldloss,'candidate_loss':loss,'relative_difference':loss/oldloss-1,'pass':bool(loss<=oldloss*1.002),'exact_validation_age_removed':True,'groups_customer_address_disjoint':True};pilots.append(rec);dump(OUT/f'pilot_metrics/{recipe["id"]}_{line}.json',rec);event('source_pilot_complete',**rec)
 selected=[x for x in plan['models'] if all(p['pass'] for p in pilots if p['model_id']==x['id'])];dump(OUT/'source_veto.json',{'pilots':pilots,'eligible':selected,'real_fits_completed':sum(x['price_estimator_fits'] for x in receipts)})
 if not selected:
  base=read(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json');report={'id':plan['id'],'utc':now(),'author':'Codex','primary_reference':'W2-COD-R36','summaries':[x for x in base['summaries'] if x['model_id'] in ['W2-B00','W2-B20','W2-COD-R36']],'gates':[],'pairs':[],'new_price_fits':sum(x['price_estimator_fits'] for x in receipts),'new_C0_fits':0,'source_pilots':pilots,'stop_reason':'all families failed source coarsened-age gate;nofullsource or emergingfits/predictions/scores','selected_exploratory_variant':None,'2024_closed':True,'B00_preserved':True,'promotion':False}
 else:
  incumbent=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();original=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();outputs=[]
  for line in m.FEATURES:
   f=load_source(line);event('source_full_started',line=line)
   with threadpool_limits(limits=2):teachers,note=m.train_source(f,line,include_trees=any(x['kind']=='trees' for x in selected))
   note['role']='source_full';receipts.append(note);path=OUT/f'teachers/{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(teachers,path,compress=3);dump(path.with_suffix('.json'),note);event('source_full_complete',line=line);lookup=pq.read_table(SOURCE/f'{line}_emerging_bands.parquet',columns=m.KEY+['x_transport_band']).to_pandas()
   for fold in range(5):
    frame=pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas().merge(lookup,on=m.KEY,validate='one_to_one',how='left');assert frame.x_transport_band.notna().all();fit=frame[frame.fold.ne(fold)].copy();val=frame[frame.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
    assert 'x_exact_age' not in frame.columns
    for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
    ref=incumbent[incumbent.line.eq(line)&incumbent.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=original[original.model_id.eq('W2-B20')&original.line.eq(line)&original.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and b20[m.KEY].equals(ref[m.KEY])
    for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())
    for recipe in selected:
     event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
     with threadpool_limits(limits=2):bundle,note=m.fit(fit,line,fold,teachers[recipe['kind']],recipe['id']);rate=m.predict(bundle,val);stressrate=m.predict(bundle,val,stress=True)
     path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(bundle,path,compress=3)
     with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
     note['role']='target';note['replay_exact']=True;receipts.append(note);dump(path.with_suffix('.json'),note);row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['unpooled_age_stress']=stressrate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['age_stress_prediction']=(.5*np.sqrt(row.unpooled_age_stress)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
     pure=row.copy();pure['model_id']=plan['natural_outputs'][recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['age_stress_prediction']=pure.unpooled_age_stress;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'])
  new=pd.concat(outputs,ignore_index=True);new.to_parquet(OUT/'new_oof_2023.parquet',index=False);ids=[x['id'] for x in selected]+[plan['natural_outputs'][x['id']] for x in selected];report=evaluate(pd.concat([original,incumbent],ignore_index=True),new,ids,sum(x['price_estimator_fits'] for x in receipts),reference_id='W2-COD-R36');baseD=m.metrics(incumbent)['D2'];stress=[]
  for gate in report['gates']:
   row=new[new.model_id.eq(gate['model_id'])];metric=m.metrics(row,prediction='age_stress_prediction');delta=metric['D2']-baseD;gate['checks']['age_distribution_stress']=delta>=0;gate['all_pass']=all(gate['checks'].values());stress.append({'model_id':gate['model_id'],'fixed_model_stress':metric,'delta_R36':delta})
  report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',source_pilots=pilots,age_distribution_stress=stress,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=report['new_price_fits'],gates=report['gates'],selected=report['selected_exploratory_variant'],source_eligible=[x['id'] for x in selected])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
