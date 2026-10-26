"""Robustez de medición: fuente enmascarada, dos vistas de control y CV2023."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,argparse,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_fuente_mascarada2023 as m
from semana2 import mascara_fuente2023_v3 as mask
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo26_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo26_plan.json';MASKED=R/'privado/semana2/robustez2023/fuente_mascarada2023_v3';SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';BLOCKS=R/'privado/semana2/robustez2023/bloques_fuente2023_v1';BAGS=R/'privado/semana2/robustez2023/ciclo17_20261025_v1/source_bags';PREVIOUS=R/'privado/semana2/robustez2023/ciclo24_20261025_v1/pilot_metrics';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
RECIPES=[{'id':'W2-COD-R98','kind':'glm','source_baseline':'W2-COD-R31','old_metric':'W2-COD-R90'},{'id':'W2-COD-R99','kind':'trees','source_baseline':'W2-COD-R32','old_metric':'W2-COD-R91'}];NATURAL={'W2-COD-R98':'W2-COD-R100','W2-COD-R99':'W2-COD-R101'}
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']
def event(name,**kw):
 o={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(o)+'\n')
 print(json.dumps(o),flush=True)
def synthetic():
 rng=np.random.default_rng(2026102526);n=1200;receipts=[]
 for line in m.FEATURES:
  f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'policy_id':['p'+str(i//2) for i in range(n)],'address_id':['a'+str(i//2) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
  for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
  for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  if line!='motor':f['x_distance_to_river_km']=np.expm1(f.x_log_distance_to_river_km)
  f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)
  source,note=mask.apply(f.assign(market='developed'),line);assert np.array_equal(f.T0,source.T0)
  with threadpool_limits(limits=2):
   plain,rec=m.fit_source(source,line,'glm');receipts.append(rec);trees,rec=m.fit_source(source,line,'trees',parent=plain);receipts.append(rec)
   for teacher in [plain,trees]:
    b,rec=m.fit(f[f.fold.ne(0)],line,0,teacher,'SYN');receipts.append(rec);val=f[f.fold.eq(0)];pred=m.predict(b,val);assert np.array_equal(pred,m.predict(b,val.assign(T0=1e15)))
    x=m.old.adapter_matrix(m.features(val,line),b['region_encoder']);other=m.teacher_rate(teacher,val)*np.exp(x.toarray()@b['coef']);assert np.allclose(pred,other,rtol=1e-14,atol=1e-12)
  try:m.predict(b,val.assign(year=2024))
  except AssertionError:pass
  else:raise AssertionError('2024 aceptado')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':12,'all3lines_bothfamilies':True,'source_mask_preserves_cost':True,'held_label_poison_invariant':True,'adapter_formula_other_method':True,'2024_rejected':True,'receipts':receipts})
def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),Path(mask.__file__),R/'herramientas/preparar_fuente_mascarada2023_v3.py',MASKED/'report.json',MASKED/'preparation_contract.json',MASKED/'synthetic_mask.json',R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,R/'registro/semana2_robustez2023_ciclo24_plan.json',R/'privado/semana2/robustez2023/mision017_20261025_v1/numeric_overlap2023_v3.json']
 paths += [folder/f'{line}_2023.parquet' for folder in [SOURCE,MASKED] for line in m.FEATURES]+[BLOCKS/f'{line}.parquet' for line in m.FEATURES]+[BAGS/f'{line}_bag{k}.joblib' for line in m.FEATURES for k in range(5)]+[PREVIOUS/f'{r["old_metric"]}_{line}_fold{k}.json' for r in RECIPES for line in m.FEATURES for k in range(5)]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 old_sources={s['path']:s['sha256'] for s in read(R/'registro/semana2_robustez2023_ciclo24_plan.json')['sources']}
 for folder,pattern in [(SOURCE,'*_2023.parquet'),(BLOCKS,'*.parquet'),(BAGS,'*.joblib')]:
  for p in folder.glob(pattern):assert old_sources[rel(p)]==sha(p)
 ids=[x['id'] for x in RECIPES]+list(NATURAL.values())
 plan={'id':'S2-ROBUSTEZ2023-CICLO26-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ26-PREVIO','models':RECIPES,'natural_outputs':NATURAL,
 'hypothesis':'Source~2.5%missing vs emerging~12% in six numeric line/field pairs may make medianimputation/missingbranches fragile. Test one labelindependent fixed10%additional source masking view with SAME modelcapacity;not proof of MCAR or causal missingness.',
 'mask':{'probability':.10,'seed':mask.SEED,'fields':mask.FIELDS,'stable_entity':'policy_id+line forcontractanswers,address_id shared acrosshomes fordistance','no_replication_no_costdrop':True},
 'source_GLM':'referenceTweedie1.5alpha1,sourceonlymedian/clip.005/.995/scale,OHEmin100max40;region/buildingconstructionexcluded',
 'source_trees':'reference200depth3leaves8lr.025min5000L2500L1100seed2026102506;no newcapacity',
 'source_veto':'all5savedsourceblocks;eachfamily eachline combinedtwoviewloss<=1.002baseline AND eachregimepooledloss<=1.002baseline AND >=4/5combinedfolds<=1.002. Sameoriginalheldrows,originalcost+exposure;viewsarenotindependentsupport. Originalbaseline losses reusedC24 aftersource/BAGhashmatch;maskedbaseline evaluatedoncetothenewview. Sourceblocks adaptivelyseen.',
 'real_fit_budget_max':66,'source_fit_budget':36,'target_fit_budget':30,'new_C0_fits':0,'adapter':'unchangedminimalfreeintercept+newbusiness/regionridge1;5stored2023targetfolds,T0/exposure/C0same',
 'outputs':{'fixed_sqrt_50_50_B20':[x['id'] for x in RECIPES],'natural':NATURAL,'weights_never_learned':True},'preference_order':ids,'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'promotion':False,'2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'previous_goal_turn':'progress:cycles21-25completed,new numericmeasurementaudit changed nextaction;no repeated block','sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'synthetic_fits':12,'real_fits_max':66}))
def load_source(line):
 block=pq.read_table(BLOCKS/f'{line}.parquet').to_pandas()[m.KEY+['source_group_id','source_fold']]
 frames=[]
 for folder in [MASKED,SOURCE]:frames.append(pq.read_table(folder/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas().merge(block,on=m.KEY,validate='one_to_one'))
 assert frames[0][m.KEY].equals(frames[1][m.KEY])
 return frames
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];pilots=[]
 for line in m.FEATURES:
  masked,original=load_source(line)
  for fold in range(5):
   fit=masked[masked.source_fold.ne(fold)].copy();val=masked[masked.source_fold.eq(fold)].copy();complete=original[original.source_fold.eq(fold)].copy();assert val[m.KEY].equals(complete[m.KEY]) and val.T0.equals(complete.T0) and val.exposure.equals(complete.exposure)
   for key in ['source_group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   parents={};reference=joblib.load(BAGS/f'{line}_bag{fold}.joblib')
   for recipe in plan['models']:
    event('source_pilot_started',line=line,fold=fold,model_id=recipe['id'])
    with threadpool_limits(limits=2):t,rec=m.fit_source(fit,line,recipe['kind'],parent=parents.get('glm'));pred=m.teacher_rate(t,val)*val.exposure.to_numpy();pred_full=m.teacher_rate(t,complete)*complete.exposure.to_numpy();base_mask=m.old.teacher_rate(reference[recipe['source_baseline']],val)*val.exposure.to_numpy()
    parents[recipe['kind']]=t;rec.update(role='source_pilot',fold=fold,model_id=recipe['id']);receipts.append(rec);path=OUT/f'pilot_models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);dump(path.with_suffix('.json'),rec)
    with threadpool_limits(limits=2):replayed=joblib.load(path);assert np.array_equal(pred,m.teacher_rate(replayed,val)*val.exposure.to_numpy()) and np.array_equal(pred_full,m.teacher_rate(replayed,complete)*complete.exposure.to_numpy())
    previous=read(PREVIOUS/f'{recipe["old_metric"]}_{line}_fold{fold}.json');assert previous['line']==line and previous['fold']==fold;row={'line':line,'fold':fold,'model_id':recipe['id'],'rows':len(val),'candidate_loss_masked':float(m.unit_deviance(val.T0,pred).sum()),'reference_loss_masked':float(m.unit_deviance(val.T0,base_mask).sum()),'candidate_loss_original':float(m.unit_deviance(complete.T0,pred_full).sum()),'reference_loss_original':previous['reference_loss'],'original_reference_reused_without_inference':True,'groups_disjoint':True,'replay_exact_bothviews':True};row['relative_difference']=(row['candidate_loss_masked']+row['candidate_loss_original'])/(row['reference_loss_masked']+row['reference_loss_original'])-1;pilots.append(row);dump(OUT/f'pilot_metrics/{recipe["id"]}_{line}_fold{fold}.json',row);event('source_pilot_complete',**row)
 summaries=[];eligible=[]
 for recipe in RECIPES:
  good=True
  for line in m.FEATURES:
   rows=[x for x in pilots if x['model_id']==recipe['id'] and x['line']==line];r={v:sum(x['candidate_loss_'+v] for x in rows)/sum(x['reference_loss_'+v] for x in rows)-1 for v in ['masked','original']};combined=sum(x['candidate_loss_masked']+x['candidate_loss_original'] for x in rows)/sum(x['reference_loss_masked']+x['reference_loss_original'] for x in rows)-1;folds=sum(x['relative_difference']<=.002 for x in rows);passed=bool(combined<=.002 and max(r.values())<=.002 and folds>=4);good &= passed;summaries.append({'model_id':recipe['id'],'line':line,'pooled_relative_loss':combined,'pooled_regime_relative_losses':r,'combined_folds_inside_tolerance':folds,'pass':passed})
  if good:eligible.append(recipe['id'])
 dump(OUT/'source_veto.json',{'summaries':summaries,'eligible':eligible})
 if not eligible:
  previous=read(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json');report={'summaries':[x for x in previous['summaries'] if x['model_id'] in ['W2-B00','W2-B20','W2-COD-R36']],'gates':[],'pairs':[],'new_price_fits':len(receipts),'new_C0_fits':0,'stop_reason':'source two-view gate failed;no fullsource/targetfit','selected_exploratory_variant':None,'2024_closed':True,'B00_preserved':True}
 else:
  report=target(plan,eligible,receipts)
 report.update(id=plan['id'],author='Codex',utc=now(),source_gate=summaries,source_eligible=eligible,primary_reference='W2-COD-R36',promotion=False);check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=report['new_price_fits'],gates=report['gates'],selected=report['selected_exploratory_variant'])
def target(plan,eligible,receipts):
 inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();outputs=[]
 for line in m.FEATURES:
  source,_=load_source(line);teachers={}
  for recipe in RECIPES:
   if recipe['id'] not in eligible and recipe['kind']=='trees':continue
   event('source_full_started',line=line,model_id=recipe['id'])
   with threadpool_limits(limits=2):t,rec=m.fit_source(source,line,recipe['kind'],parent=teachers.get('glm'))
   teachers[recipe['kind']]=t;rec.update(role='source_full',model_id=recipe['id']);receipts.append(rec);path=OUT/f'teachers/{recipe["id"]}_{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);dump(path.with_suffix('.json'),rec)
  for fold in range(5):
   f=pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas();fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=inc[inc.line.eq(line)&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.eq(line)&old.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
   for col in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[col].to_numpy(),ref[col].to_numpy())
   for recipe in RECIPES:
    if recipe['id'] not in eligible:continue
    event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
    with threadpool_limits(limits=2):b,rec=m.fit(fit,line,fold,teachers[recipe['kind']],recipe['id']);rate=m.predict(b,val)
    path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
    rec.update(role='target',replay_exact=True);receipts.append(rec);dump(path.with_suffix('.json'),rec);row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row);pure=row.copy();pure['model_id']=NATURAL[recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'])
 new=pd.concat(outputs,ignore_index=True);new.to_parquet(OUT/'new_oof_2023.parquet',index=False);ids=[v for v in plan['preference_order'] if v in set(new.model_id)];report=evaluate(pd.concat([old,inc],ignore_index=True),new,ids,len(receipts),reference_id='W2-COD-R36');report['selected_exploratory_variant']=next((x['model_id'] for x in report['gates'] if x['all_pass']),None);return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
