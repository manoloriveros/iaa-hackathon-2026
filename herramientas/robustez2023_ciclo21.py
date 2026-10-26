"""Coste limitado y exceso, con suma completa y calibración mínima 2023."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,sys,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_capas_coste2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo21_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo21_plan.json';SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';LAYERS=R/'privado/semana2/robustez2023/capas_coste2023_v1';BLOCKS=R/'privado/semana2/robustez2023/bloques_fuente2023_v1';BAGS=R/'privado/semana2/robustez2023/ciclo17_20261025_v1/source_bags';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as h:json.dump(obj,h,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']
def event(name,**kw):
 obj={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as h:h.write(json.dumps(obj)+'\n')
 print(json.dumps(obj),flush=True)
def synthetic():
 n=1200;rng=np.random.default_rng(2026102521);line='motor';f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;layers=f[m.KEY].copy();records=[]
 for _ in range(n):
  costs=np.rint(rng.gamma(2,1500000,int(rng.poisson(.6)))).astype(np.int64);limited=np.minimum(costs,1000000);excess=costs-limited;records.append((len(costs),int((excess>0).sum()),int(limited.sum()),int(excess.sum()),int(costs.sum())))
 layers[['N','tail_count','limited_cents','excess_cents','cost_cents']]=np.array(records);assert np.array_equal(layers.cost_cents,layers.limited_cents+layers.excess_cents);f['T0']=layers.cost_cents.to_numpy()/100
 with threadpool_limits(limits=2):source,note=m.train_source(f.assign(market='developed'),layers.assign(market='developed'),line)
 controls=[]
 for ratio in [False,True]:
  with threadpool_limits(limits=2):b,rec=m.fit(f[f.fold.ne(0)],line,0,source,{'id':'SYN','tail_share_effect':ratio});val=f[f.fold.eq(0)];p=m.predict(b,val);poison=m.predict(b,val.assign(T0=1e15))
  assert np.array_equal(p,poison);controls.append(rec)
 a,e=m.components(source,f);assert np.isfinite(a+e).all() and (a+e>0).all()
 dump(OUT/'synthetic.json',{'synthetic_price_fits':note['price_estimator_fits']+2,'integer_cost_identity':True,'both_target_GLMS':True,'held_label_poison_invariant':True,'all_claim_costs_retained':True,'source_receipt':note,'adapter_receipts':controls})
def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,LAYERS/'report.json',LAYERS/'preparation_contract.json']
 paths += [SOURCE/f'{line}_2023.parquet' for line in m.FEATURES]+[LAYERS/f'{line}_layers.parquet' for line in m.FEATURES]+[BLOCKS/f'{line}.parquet' for line in m.FEATURES]+[BAGS/f'{line}_bag0.joblib' for line in m.FEATURES]+[BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO21-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ21-PREVIO',
 'models':[{'id':'W2-COD-R78','tail_share_effect':False},{'id':'W2-COD-R79','tail_share_effect':True}],'natural_outputs':{'W2-COD-R78':'W2-COD-R80','W2-COD-R79':'W2-COD-R81'},
 'hypothesis':'Repeated gains depend on few largecost groups. Model limited claim cost and its excess separately, conserving totalcost, to estimate ordinary-risk shape without letting excess variation set all slopes. This is layer decomposition,not removing or clipping officialtarget.',
 'claim_layer_cap_CU':10000,'cap_chosen_before_layer_statistics':True,'source_cost_identity':'perclaim min(netcost,10000)+max(netcost-10000,0);periodsums match all originalT0cents exactly',
 'source_limited':'Tweedie1.5GLMalpha1 plus original200treesdepth3,min5000,L2500,L1100',
 'source_excess':'Poissonfrequencyalpha.001 on count ofclaims above cap,allperiods;Gamma conditionalmeanmarkalpha.1 on strictlypositiveexcess weightedtailcount;constantmean fallback if<100tailperiods;allcost retained',
 'source_scope':'same2023physicalpredictors,region/buildingconstructionexcluded,source-onlytransforms,observedincurred/nominal exposure remains conditional not independentlyidentifiedultimate',
 'source_veto':'block0components held,allcomponentsfitoutsideblock0;fulltotal netTweedieloss <=1.002C17bag0source200tree reference in all3lines,else stop beforefullsource/target',
 'budget_max':54,'source_pilot_fits_max':12,'full_source_fits_max':12,'target_adapter_fits_max':30,'new_C0_fits':0,
 'adapter':'R78same minimal interceptfree+newbusiness/regionridge1;R79 adds one log(excessrate/limitedrate)basis fitonlyclip/scale withridge10;sourcebasisnever trained onemerginglabels',
 'outputs':'R78/R79fixedsqrt50%candidate+50%B20 exactlyR36;R80/R81naturaloutput;no learned or tunedweights',
 'stress':'fixedsourceexcesslevel times.75and1.25,no refit;eachoverallD2delta vsR36 must remain >=0 as well as allprimarygates;not claim ofcase reservecorrection',
 'primary_reference':'W2-COD-R36','folds':'samefiveemerging2023components,T0/exposure/existingC0 unchanged',
 'criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},
 'preference':'R78minimalpool,thenR79onebasis_pool,thenR80minimalnatural,thenR81onebasisnatural;onlysource+primary+stressgates pass;otherwiseR36',
 '2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'promotion':False,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'fits_max':54,'cap_CU':10000,'C0_new':0}))
def load_source(line):
 f=pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();b=pq.read_table(BLOCKS/f'{line}.parquet').to_pandas();return f.merge(b[m.KEY+['source_group_id','source_fold']],on=m.KEY,validate='one_to_one')
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];pilots=[]
 for line in m.FEATURES:
  f=load_source(line);fit=f[f.source_fold.ne(0)].copy();val=f[f.source_fold.eq(0)].copy();layers=pq.read_table(LAYERS/f'{line}_layers.parquet').to_pandas()
  for key in ['source_group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
  event('source_pilot_started',line=line,fit_rows=len(fit),validation_rows=len(val))
  with threadpool_limits(limits=2):source,rec=m.train_source(fit,layers,line);a,e=m.components(source,val);pred=(a+e)*val.exposure.to_numpy();baseline=m.old.teacher_rate(joblib.load(BAGS/f'{line}_bag0.joblib')['W2-COD-R32'],val)*val.exposure.to_numpy()
  rec['role']='source_pilot';receipts.append(rec);path=OUT/f'pilot_models/{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(source,path,compress=3);dump(path.with_suffix('.json'),rec);oldloss=float(m.unit_deviance(val.T0,baseline).sum());loss=float(m.unit_deviance(val.T0,pred).sum());row={'line':line,'reference_loss':oldloss,'candidate_loss':loss,'relative_difference':loss/oldloss-1,'pass':bool(loss<=oldloss*1.002),'full_unclipped_cost_scored':True,'groups_disjoint':True};pilots.append(row);dump(OUT/f'pilot_metrics/{line}.json',row);event('source_pilot_complete',**row)
 eligible=all(x['pass'] for x in pilots);dump(OUT/'source_veto.json',{'pilots':pilots,'eligible':eligible,'fits_completed':sum(x['price_estimator_fits'] for x in receipts)})
 if not eligible:
  base=read(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json');report={'id':plan['id'],'utc':now(),'author':'Codex','primary_reference':'W2-COD-R36','summaries':[x for x in base['summaries'] if x['model_id'] in ['W2-B00','W2-B20','W2-COD-R36']],'gates':[],'pairs':[],'source_pilots':pilots,'new_price_fits':sum(x['price_estimator_fits'] for x in receipts),'new_C0_fits':0,'stop_reason':'sourcefullcostgatefailed;no fullsource/emerging fits/predictions/scores','selected_exploratory_variant':None,'2024_closed':True,'B00_preserved':True,'promotion':False}
 else:
  incumbent=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();original=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();outputs=[]
  for line in m.FEATURES:
   f=load_source(line);layers=pq.read_table(LAYERS/f'{line}_layers.parquet').to_pandas();event('source_full_started',line=line)
   with threadpool_limits(limits=2):source,rec=m.train_source(f,layers,line)
   rec['role']='source_full';receipts.append(rec);path=OUT/f'teachers/{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(source,path,compress=3);dump(path.with_suffix('.json'),rec);event('source_full_complete',line=line)
   for fold in range(5):
    f=pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas();fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
    for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
    ref=incumbent[incumbent.line.eq(line)&incumbent.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=original[original.model_id.eq('W2-B20')&original.line.eq(line)&original.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and b20[m.KEY].equals(ref[m.KEY])
    for c in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[c].to_numpy(),ref[c].to_numpy())
    for recipe in plan['models']:
     event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
     with threadpool_limits(limits=2):bundle,rec=m.fit(fit,line,fold,source,recipe);rate=m.predict(bundle,val);low=m.predict(bundle,val,tail_level=.75);high=m.predict(bundle,val,tail_level=1.25)
     path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(bundle,path,compress=3)
     with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
     rec['role']='target';rec['replay_exact']=True;receipts.append(rec);dump(path.with_suffix('.json'),rec);row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['unpooled_low']=low*val['e_cost_mix_1.0'].to_numpy();row['unpooled_high']=high*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['tail075_prediction']=(.5*np.sqrt(row.unpooled_low)+.5*np.sqrt(b20.prediction))**2;row['tail125_prediction']=(.5*np.sqrt(row.unpooled_high)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
     pure=row.copy();pure['model_id']=plan['natural_outputs'][recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['tail075_prediction']=pure.unpooled_low;pure['tail125_prediction']=pure.unpooled_high;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'])
  new=pd.concat(outputs,ignore_index=True);new.to_parquet(OUT/'new_oof_2023.parquet',index=False);ids=['W2-COD-R78','W2-COD-R79','W2-COD-R80','W2-COD-R81'];report=evaluate(pd.concat([original,incumbent],ignore_index=True),new,ids,sum(x['price_estimator_fits'] for x in receipts),reference_id='W2-COD-R36');baseD=m.metrics(incumbent)['D2'];stress=[]
  for gate in report['gates']:
   part=new[new.model_id.eq(gate['model_id'])];deltas=[]
   for name in ['tail075_prediction','tail125_prediction']:
    metric=m.metrics(part,prediction=name);delta=metric['D2']-baseD;deltas.append(delta);stress.append({'model_id':gate['model_id'],'stress':name,'metrics':metric,'delta_R36':delta})
   gate['checks']['excess_level_stress']=min(deltas)>=0;gate['all_pass']=all(gate['checks'].values())
  report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',source_pilots=pilots,excess_level_stress=stress,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False)
 report['new_closed_form_constants']=sum(x.get('closed_form_mark_constants',0) for x in receipts);check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=report['new_price_fits'],gates=report['gates'],selected=report['selected_exploratory_variant'],source_eligible=eligible)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
