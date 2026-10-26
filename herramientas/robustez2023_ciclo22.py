"""Aporte de atributos contractuales omitidos, cinco bloques fuente y CV2023."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,argparse,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_contrato_fuente2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo22_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo22_plan.json'
EXTRA=R/'privado/semana2/robustez2023/contrato_faltante2023_v1';BLOCKS=R/'privado/semana2/robustez2023/bloques_fuente2023_v1';BAGS=R/'privado/semana2/robustez2023/ciclo17_20261025_v1/source_bags'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
RECIPES=[{'id':'W2-COD-R82','kind':'glm','source_baseline':'W2-COD-R31'},{'id':'W2-COD-R83','kind':'trees','source_baseline':'W2-COD-R32'}]
NATURAL={'W2-COD-R82':'W2-COD-R84','W2-COD-R83':'W2-COD-R85'}
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))

def event(name,**kw):
 o={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(o)+'\n')
 print(json.dumps(o),flush=True)

def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']

def synthetic():
 rng=np.random.default_rng(2026102522);n=1200;receipts=[]
 for line in m.FEATURES:
  f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
  for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
  for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)
  with threadpool_limits(limits=2):
   plain,r=m.fit_source(f.assign(market='developed'),line,'glm');receipts.append(r)
   trees,r=m.fit_source(f.assign(market='developed'),line,'trees',parent=plain);receipts.append(r)
   for t in [plain,trees]:
    b,r=m.fit(f[f.fold.ne(0)],line,0,t,'SYN');receipts.append(r);val=f[f.fold.eq(0)];p=m.predict(b,val)
    assert np.array_equal(p,m.predict(b,val.assign(T0=1e15)))
    x=m.old.adapter_matrix(m.features(val,line),b['region_encoder']);independent=m.teacher_rate(t,val)*np.exp(np.asarray(x.toarray())@b['coef']);assert np.allclose(p,independent,rtol=1e-14,atol=1e-12)
  for bad in [f.assign(market='developed',year=2024),f]:
   try:m.fit_source(bad,line,'glm')
   except AssertionError:pass
   else:raise AssertionError('Fuente prohibida admitida')
  try:m.predict(b,val.assign(year=2024))
  except AssertionError:pass
  else:raise AssertionError('Cotización2024 admitida')
  extra=f[m.KEY].copy();extra['x_synthetic_extra']=1;joined=m.attach(f,extra);assert np.array_equal(joined.T0,f.T0)
  try:m.attach(f,extra.iloc[:-1])
  except AssertionError:pass
  else:raise AssertionError('Enlace incompleto admitido')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':len(receipts),'all_three_lines':True,'held_label_poison_invariant':True,'adapter_formula_other_method':True,'closed2024_rejected':True,'wrong_market_rejected':True,'join_guard':True,'receipts':receipts})

def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,EXTRA/'report.json',R/'herramientas/preparar_variables_contrato_faltantes2023.py']
 paths+=list(EXTRA.glob('*.parquet'))+[BLOCKS/f'{line}.parquet' for line in m.FEATURES]+[BAGS/f'{line}_bag{k}.joblib' for line in m.FEATURES for k in range(5)]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO22-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ22-PREVIO','models':RECIPES,'natural_outputs':NATURAL,
 'hypothesis':'Physical teachers omit contractual make_model,mortgage,works_from_home,lodgers. Shared definitions and300code levels are not proof of transported effects. Test source incremental signal across all5savedsourceblocks before target CV.',
 'availability':'F0_contractual at policyinception,only2023 rows;source-target records never joined;KEY links within each market,alloldcolumnsunchanged',
 'new_features':{'motor':['make_model categorical300levels'],'buildings':['mortgage'],'contents':['works_from_home','lodgers']},
 'source_GLM':'sameTweedie1.5alpha1 main effects;median/clip.005,.995/standardscale;OHEmin100max400dropfirst;region/buildingconstructionexcluded',
 'source_trees':'same200depth3leaves8lr.025,min5000L2500L1100,seed2026102506 residual onextendedGLM;no capacity increase',
 'source_veto':'eachfamily eachline pooled5sourcefoldfullcostloss <=1.002savedC17samefamily;>=4/5folds relative loss <=1.002. Allsourcegroup/customer/address disjoint and sameheldrows/denominator. Blocks previouslyseen adaptively,notindependentconfirmation.',
 'source_fit_budget':36,'target_fit_budget':30,'real_fit_budget_max':66,'new_C0_fits':0,
 'adapter':'unchangedminimalfreeintercept+newbusiness/regionridge1;source shape only,alltargettransform/coef fitoutsideheldfold',
 'outputs':'R82/R83fixedsqrt50/50withB20,R84/R85natural;no optimizedweights',
 'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R82standardGLMpool,thenR83smalltreespool,thenR84naturalGLM,thenR85naturaltrees,onlysourceandalltargetgates;otherwiseR36',
 'target_scope':'five saved2023emergingcomponents,T0/exposure/existingC0 unchanged;no2024,realizedweather,premium or newtargetsupport',
 '2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'promotion':False,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'synthetic_price_fits':12,'real_fits_max':66}))

def load_source(line):
 f=pq.read_table(EXTRA/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();b=pq.read_table(BLOCKS/f'{line}.parquet').to_pandas();return f.merge(b[m.KEY+['source_group_id','source_fold']],on=m.KEY,validate='one_to_one')

def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];pilots=[]
 for line in m.FEATURES:
  f=load_source(line)
  for fold in range(5):
   fit=f[f.source_fold.ne(fold)].copy();val=f[f.source_fold.eq(fold)].copy();assert len(fit)+len(val)==len(f)
   for key in ['source_group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   parents={};reference=joblib.load(BAGS/f'{line}_bag{fold}.joblib')
   for recipe in plan['models']:
    event('source_pilot_started',line=line,fold=fold,model_id=recipe['id'])
    with threadpool_limits(limits=2):t,rec=m.fit_source(fit,line,recipe['kind'],parent=parents.get('glm'));pred=m.teacher_rate(t,val)*val.exposure.to_numpy();base=m.old.teacher_rate(reference[recipe['source_baseline']],val)*val.exposure.to_numpy()
    parents[recipe['kind']]=t;rec.update(role='source_pilot',fold=fold,model_id=recipe['id']);receipts.append(rec);path=OUT/f'pilot_models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);dump(path.with_suffix('.json'),rec)
    with threadpool_limits(limits=2):assert np.array_equal(pred,m.teacher_rate(joblib.load(path),val)*val.exposure.to_numpy())
    row={'line':line,'fold':fold,'model_id':recipe['id'],'rows':len(val),'candidate_loss':float(m.unit_deviance(val.T0,pred).sum()),'reference_loss':float(m.unit_deviance(val.T0,base).sum()),'groups_disjoint':True,'replay_exact':True};row['relative_difference']=row['candidate_loss']/row['reference_loss']-1;pilots.append(row);dump(OUT/f'pilot_metrics/{recipe["id"]}_{line}_fold{fold}.json',row);event('source_pilot_complete',**row)
 summaries=[];eligible=[]
 for recipe in plan['models']:
  good=True
  for line in m.FEATURES:
   rows=[x for x in pilots if x['model_id']==recipe['id'] and x['line']==line];ratio=sum(x['candidate_loss'] for x in rows)/sum(x['reference_loss'] for x in rows)-1;folds=sum(x['relative_difference']<=.002 for x in rows);passed=bool(ratio<=.002 and folds>=4);good &= passed;summaries.append({'model_id':recipe['id'],'line':line,'pooled_relative_loss':ratio,'folds_inside_tolerance':folds,'pass':passed})
  if good:eligible.append(recipe['id'])
 dump(OUT/'source_veto.json',{'summaries':summaries,'eligible':eligible})
 if not eligible:
  base=read(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json');report={'summaries':[x for x in base['summaries'] if x['model_id'] in ['W2-B00','W2-B20','W2-COD-R36']],'gates':[],'pairs':[],'new_price_fits':len(receipts),'new_C0_fits':0,'stop_reason':'bothsourcefamiliesfailedfiveblockgate;no fullsource/targetfit','selected_exploratory_variant':None,'2024_closed':True,'B00_preserved':True}
 else:
  inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();original=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();outputs=[]
  for line in m.FEATURES:
   source=load_source(line);teachers={}
   # The tree family needs its GLM parent even when the GLM output is vetoed.
   for recipe in plan['models']:
    if recipe['id'] not in eligible and recipe['kind']=='trees':continue
    event('source_full_started',line=line,model_id=recipe['id'])
    with threadpool_limits(limits=2):t,rec=m.fit_source(source,line,recipe['kind'],parent=teachers.get('glm'))
    teachers[recipe['kind']]=t;rec.update(role='source_full',model_id=recipe['id']);receipts.append(rec);path=OUT/f'teachers/{recipe["id"]}_{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);dump(path.with_suffix('.json'),rec);event('source_full_complete',line=line,model_id=recipe['id'])
   extra=pq.read_table(EXTRA/f'{line}_emerging_extra.parquet').to_pandas()
   for fold in range(5):
    f=m.attach(pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas(),extra);fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
    for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
    ref=inc[inc.line.eq(line)&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=original[original.model_id.eq('W2-B20')&original.line.eq(line)&original.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
    for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())
    for recipe in plan['models']:
     if recipe['id'] not in eligible:continue
     event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
     with threadpool_limits(limits=2):b,rec=m.fit(fit,line,fold,teachers[recipe['kind']],recipe['id']);rate=m.predict(b,val)
     path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
     with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
     rec.update(role='target',replay_exact=True);receipts.append(rec);dump(path.with_suffix('.json'),rec);row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
     pure=row.copy();pure['model_id']=NATURAL[recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'])
  new=pd.concat(outputs,ignore_index=True);new.to_parquet(OUT/'new_oof_2023.parquet',index=False);ids=[x for x in [r['id'] for r in RECIPES]+list(NATURAL.values()) if x in set(new.model_id)];report=evaluate(pd.concat([original,inc],ignore_index=True),new,ids,len(receipts),reference_id='W2-COD-R36');report['selected_exploratory_variant']=next((x['model_id'] for x in report['gates'] if x['all_pass']),None)
 report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',source_gate=summaries,source_eligible=eligible,promotion=False);check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=report['new_price_fits'],gates=report['gates'],selected=report['selected_exploratory_variant'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
