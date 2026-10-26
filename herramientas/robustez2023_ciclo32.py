"""GLM aditivo de hogar: dos fuentes y controles independientes/conjunto."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_fuente_aditivo2023 as source
from semana2 import modelo_region_hogar2023 as joint
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo32_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo32_plan.json'
C31=R/'privado/semana2/robustez2023/ciclo31_20261025_v1';SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
JOINT={'id':'W2-COD-R124','tau':20.};IDS=['W2-COD-R124','W2-COD-R125','W2-COD-R126','W2-COD-R127']
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()

def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as h:json.dump(x,h,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))

def event(name,**kw):
 row={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf8') as h:h.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)

def compatible(t,f):
 # GAM is a GLM over a spline design; this base-family alias changes no numbers.
 b={**t,'family':'SourceGLM','source_shape':'additive_spline','original_family':t['family']}
 a=source.teacher_rate(t,f);other=joint.core.teacher_rate(b,f);assert np.array_equal(a,other)
 return b

def synthetic():
 rng=np.random.default_rng(2026102532);frames=[];teachers={};models={}
 for line in joint.HOMES:
  n=1200;f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+line+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
  for c in source.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
  for c in source.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)
  with threadpool_limits(limits=2):t,_=source.fit_source(f.assign(market='developed'),line,'glm');teachers[line]=compatible(t,f);models[line],_=source.fit(f[f.fold.ne(0)],line,0,teachers[line],'SYN')
  frames.append(f)
 f=pd.concat(frames,ignore_index=True);fit=f[f.fold.ne(0)];val=f[f.fold.eq(0)]
 with threadpool_limits(limits=2):control,note=joint.control(fit,teachers,models,0);b,_=joint.fit(fit,teachers,0,JOINT);p=joint.predict(b,val)
 for line in joint.HOMES:
  chosen=val.line.eq(line).to_numpy();assert np.allclose(joint.predict(control,val)[chosen],source.predict(models[line],val.loc[chosen]),rtol=1e-12,atol=1e-12)
 assert np.array_equal(p,joint.predict(b,val.assign(T0=1e15)))
 independent=joint.rates(teachers,val)*np.exp(joint.matrix(val,b['region_encoder']).toarray()@b['coef']);assert np.allclose(p,independent,rtol=1e-14,atol=1e-12)
 try:joint.predict(b,val.assign(year=2024))
 except AssertionError:pass
 else:raise AssertionError('2024 accepted')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':5,'source_GAMs':2,'independent_adapters':2,'joint_adapters':1,'family_alias_prediction_exact':True,'mapped_independent_control':note,'dense_formula_checked':True,'held_label_poison_invariant':True,'2024_rejected':True})

def prepare():
 assert not PLAN.exists() and not OUT.exists();OUT.mkdir(parents=True);synthetic();previous=read(C31/'plan.json');oldhash={x['path']:x['sha256'] for x in previous['sources']};veto=read(C31/'source_veto.json');assert veto['eligible']==[]
 gates=[]
 for line in joint.HOMES:
  g=next(x for x in veto['summaries'] if x['line']==line and x['model_id']=='W2-COD-R120');assert g['pass'] and g['folds_inside_tolerance']==5;gates.append(g)
  for p in [SOURCE/f'{line}_2023.parquet',Path(source.__file__),R/'src/semana2/modelo_fuente_penalizacion2023.py']:assert oldhash[rel(p)]==sha(p)
 paths=[Path(__file__),Path(source.__file__),Path(joint.__file__),R/'src/semana2/modelo_fuente_penalizacion2023.py',R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',C31/'plan.json',C31/'report.json',C31/'source_veto.json',REF,OLD]+[SOURCE/f'{line}_2023.parquet' for line in joint.HOMES]+[BASE/f'{line}_fold{k}.parquet' for line in joint.HOMES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO32-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ32-PREVIO','hypothesis':'Global C31 sourceGAM failed motor but standardGLM passed allfive sourceblocks separately for buildings and contents. Test home-only additive source without residualtrees,with independent and jointregionalminimaladapters;motor copiedR36. GlobalC31veto remains,not reinterpreted aspassed.',
 'source':'sameC31alpha1 physicalGAM,4quantileknots degree2,constantclippedboundaries;two fullhome sourcefits;reuseall5heldsourcechecks/hashes,norepeatpilots;incurred2023/exposure remainsnotidentifiedultimate',
 'source_checks_reused':gates,'joint':JOINT,'independent_outputs':{'mixed':'W2-COD-R126','natural':'W2-COD-R127'},'joint_outputs':{'mixed':'W2-COD-R124','natural':'W2-COD-R125'},
 'tau_rationale':'single fixed20 as originalC27partiallysharedrecipe;no newgrid oroptimization ofweights','controls':'10newindependenthomeadapters countaspricefits;maptau2coordinates without extraadjustment andcheckobjectives/heldpredictions;sourcefamilyalias changesno coefficients,design orrates',
 'real_fit_budget':17,'source_fits':2,'independent_target_fits':10,'joint_target_fits':5,'new_C0_fits':0,
 'outputs':'homefixedsqrt50/50B20 or natural;allmotor predictions exactR36;no newmotorinference','primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},
 'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'preference_order':IDS,'scope':'saved2023componentfolds,T0/exposure/existingC0 unchanged;no2024 orweather admission',
 'limits':'adaptive sourceblocks,missingnessshift,sourceincurredtransport and raregrouptail unresolved;globalGTrecipe31stillvetoed;comparisonpublicCSVunchanged','B00_preserved':True,'2024_closed':True,'promotion':False,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'synthetic_fits':5,'real_fits_max':17}))

def check(plan):
 for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256'],x['path']

def outputs_for(ref,b20,rate,mixed,natural):
 row=ref.copy();row['model_id']=mixed;row['unpooled_prediction']=rate*row['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=joint.unit_deviance(row.T0,row.prediction);pure=row.copy();pure['model_id']=natural;pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=joint.unit_deviance(pure.T0,pure.prediction);return [row,pure]

def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];teachers={};controls=[];outputs=[]
 for line in joint.HOMES:
  f=pq.read_table(SOURCE/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();event('source_GAM_started',line=line)
  with threadpool_limits(limits=2):t,rec=source.fit_source(f,line,'glm');teacher=compatible(t,f)
  rec.update(role='source_full',family_alias_exact=True);receipts.append(rec);teachers[line]=teacher;p=OUT/f'teachers/{line}.joblib';p.parent.mkdir(exist_ok=True);joblib.dump(teacher,p,compress=3);dump(p.with_suffix('.json'),rec)
  with threadpool_limits(limits=2):assert np.array_equal(source.teacher_rate(teacher,f),source.teacher_rate(joblib.load(p),f))
  event('source_GAM_complete',line=line)
 inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas()
 for fold in range(5):
  f=pd.concat([pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas() for line in joint.HOMES],ignore_index=True);fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(joint.KEY).reset_index(drop=True)
  for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
  assert f.groupby('group_id').fold.nunique().le(1).all();models={}
  for line in joint.HOMES:
   with threadpool_limits(limits=2):b,rec=source.fit(fit[fit.line.eq(line)],line,fold,teachers[line],'W2-COD-R127-SEP')
   rec.update(role='new_independent_target_control');receipts.append(rec);models[line]=b;p=OUT/f'models/independent_{line}_fold{fold}.joblib';p.parent.mkdir(exist_ok=True);joblib.dump(b,p,compress=3);dump(p.with_suffix('.json'),rec)
  with threadpool_limits(limits=2):control,note=joint.control(fit,teachers,models,fold);rate=joint.predict(control,val)
  for line in joint.HOMES:
   chosen=val.line.eq(line).to_numpy()
   with threadpool_limits(limits=2):a=source.predict(models[line],val.loc[chosen]);replay=source.predict(joblib.load(OUT/f'models/independent_{line}_fold{fold}.joblib'),val.loc[chosen])
   assert np.array_equal(a,replay) and np.allclose(a,rate[chosen],rtol=1e-12,atol=1e-12)
  note.update(independent_price_fits=2,extra_mapping_fits=0,held_prediction_equivalent=True);controls.append(note);dump(OUT/f'controls/fold{fold}.json',note)
  ref=inc[inc.line.isin(joint.HOMES)&inc.fold.eq(fold)].sort_values(joint.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.isin(joint.HOMES)&old.fold.eq(fold)].sort_values(joint.KEY).reset_index(drop=True);assert val[joint.KEY].equals(ref[joint.KEY]) and ref[joint.KEY].equals(b20[joint.KEY])
  for col in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[col].to_numpy(),ref[col].to_numpy())
  outputs+=outputs_for(ref,b20,rate,'W2-COD-R126','W2-COD-R127')
  with threadpool_limits(limits=2):b,rec=joint.fit(fit,teachers,fold,JOINT);rate=joint.predict(b,val)
  p=OUT/f'models/W2-COD-R124_fold{fold}.joblib';joblib.dump(b,p,compress=3)
  with threadpool_limits(limits=2):assert np.array_equal(rate,joint.predict(joblib.load(p),val))
  rec.update(role='joint_target',replay_exact=True);receipts.append(rec);dump(p.with_suffix('.json'),rec);outputs+=outputs_for(ref,b20,rate,'W2-COD-R124','W2-COD-R125');event('target_fold_complete',fold=fold)
 for mid in IDS:
  motor=inc[inc.line.eq('motor')].copy();motor['model_id']=mid;outputs.append(motor)
 new=pd.concat(outputs,ignore_index=True);assert len(new)==4*50094 and not new.duplicated(['model_id']+joint.KEY).any() and len(receipts)==17;new.to_parquet(OUT/'new_oof_2023.parquet',index=False);report=evaluate(pd.concat([old,inc],ignore_index=True),new,IDS,len(receipts),reference_id='W2-COD-R36');report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',coordinate_controls=controls,old_global_C31_veto_preserved=True,motor_exact_R36=True,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=len(receipts),gates=report['gates'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
