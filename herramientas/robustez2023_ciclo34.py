"""Densidad solo autos: ESS compuesto, pilotos y profesores propios por fold."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_fuente_densidad2023 as m
from semana2.evaluar_robustez2023_v2 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo34_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo34_plan.json';SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/motor_2023.parquet';BLOCKS=R/'privado/semana2/robustez2023/bloques_fuente2023_v1/motor.parquet';BAGS=R/'privado/semana2/robustez2023/ciclo17_20261025_v1/source_bags';DOMAIN=R/'privado/semana2/robustez2023/prefiltro_dominio2023_v3';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
RECIPES=[{'id':'W2-COD-R132','kind':'glm','reference':'W2-COD-R31'},{'id':'W2-COD-R133','kind':'trees','reference':'W2-COD-R32'}];NATURAL={'W2-COD-R132':'W2-COD-R134','W2-COD-R133':'W2-COD-R135'};IDS=[x['id'] for x in RECIPES]+list(NATURAL.values())
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()

def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as h:json.dump(x,h,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))

def event(name,**kw):
 row={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf8') as h:h.write(json.dumps(row)+'\n')
 print(json.dumps(row),flush=True)

def synthetic():
 rng=np.random.default_rng(2026102534);n=1200;f=pd.DataFrame({'market':'emerging','line':'motor','row_id':['s_SYNTHETIC_DENSITY_'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 for c in m.FEATURES['motor']['numeric']:f[c]=rng.uniform(0,5,n)
 for c in m.FEATURES['motor']['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n);domain={'line':'motor','held_fold':0,'_synthetic_constant_odds':1.};src=f.assign(market='developed');parents={};receipts=[]
 with threadpool_limits(limits=2):original,_=m.old.fit_teachers(src,'motor')
 for recipe in RECIPES:
  with threadpool_limits(limits=2):t,rec=m.fit_source(src,domain,recipe['kind'],parent=parents.get('glm'));parents[recipe['kind']]=t;a=m.teacher_rate(t,f);expected=m.old.teacher_rate(original[recipe['reference']],f);assert np.allclose(a,expected,rtol=1e-12,atol=1e-10);b,_=m.fit(f[f.fold.ne(0)],'motor',0,t,'SYN');val=f[f.fold.eq(0)];rate=m.predict(b,val)
  assert np.array_equal(rate,m.predict(b,val.assign(T0=1e15)));receipts.append(rec)
  try:m.predict(b,val.assign(year=2024))
  except AssertionError:pass
  else:raise AssertionError('2024 accepted')
 _,low=m.weights(src,{**domain,'_synthetic_constant_odds':1e-9});_,high=m.weights(src,{**domain,'_synthetic_constant_odds':1e9});assert low['clipped_fraction']==high['clipped_fraction']==1.
 # Nonconstant weights multiply both sides of the period/annual loss identity.
 r=np.tile([.2,1.,5.],400);e=f.exposure.to_numpy();y=f.T0.to_numpy();mu=np.full(n,100.)*e;assert np.allclose(r*m.unit_deviance(y,mu),r*np.sqrt(e)*m.unit_deviance(y/e,mu/e),rtol=1e-12,atol=1e-10)
 dump(OUT/'synthetic.json',{'synthetic_price_fits':6,'old_source_control_fits':2,'weighted_source_fits':2,'target_adapter_fits':2,'constant_odds_recover_original_teachers':True,'nonconstant_weight_loss_identity':True,'clipping_extremes_checked':True,'2024_rejected':True,'held_label_poison_invariant':True,'new_domain_fits':0,'receipts':receipts})

def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic();d=read(DOMAIN/'report.json');assert next(x for x in d['summaries'] if x['line']=='motor')['weighting_recipe_can_be_considered'] and all(not x['weighting_recipe_can_be_considered'] for x in d['summaries'] if x['line']!='motor')
 manifest={x['path']:x['sha256'] for x in read(DOMAIN/'manifest.json')['files']};domain_hash={x['path']:x['sha256'] for x in read(DOMAIN/'plan.json')['sources']};assert domain_hash[rel(Path(m.domain_model.__file__))]==sha(Path(m.domain_model.__file__))
 for k in range(5):
  p=DOMAIN/f'models/motor_fold{k}.joblib';assert manifest[rel(p)]==sha(p);b=joblib.load(p);assert b['held_fold']==k and b['line']=='motor' and '_synthetic_constant_odds' not in b
 paths=[Path(__file__),Path(m.__file__),Path(m.domain_model.__file__),R/'src/semana2/modelo_fuente_penalizacion2023.py',R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',SOURCE,BLOCKS,REF,OLD,DOMAIN/'report.json',DOMAIN/'plan.json',DOMAIN/'manifest.json']+[DOMAIN/f'models/motor_fold{k}.joblib' for k in range(5)]+[BAGS/f'motor_bag{k}.joblib' for k in range(5)]+[BASE/f'motor_fold{k}.parquet' for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO34-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ34-PREVIO','models':RECIPES,'natural_outputs':NATURAL,
 'hypothesis':'Frozen attrdomain prefilter hasmotorAUC.7155-.7226andpassesoverlap;homefails. Investigate whether finite-capacity standard sourceGLM projection transportsbetter when weighting sourceattributes towardouterfit emergingdistribution. This doesnotassumeconditionaloutcomesequality orcausality;C33lossgain alone didnottransfer.',
 'domain':'reuse exactmotorfoldk logistic from domainv3;its sourceblockk andemergingfoldk wereexcluded fromALLclassifierlearning;no newclassifierfits,heldtargetattrs/outcomes neverlearnweights',
 'weight_rule':'r=clip(exp(logit),.2,5);w=sqrt(nominalsourceexposure)*r/weightedmean(r,weights=sqrt(exposure)) on currentpricefitrows;preservebaselineweightsum;alloriginalcases/costs/exposure remain,positiveweights;not claimtrimming ornewtargetsupport',
 'first_gate':'beforeANYpricefit,combined w ESS/n>=.5 onall10plannedpilot/fullsource scopes(5helddomainmodels xfit/full). Anyfailure stopswholepricedrecipewithoutfit;no regrouping/thresholdrelaxation',
 'source_GLM':'same original physical linear Tweedie1.5alpha1 andfitonlymedian/clip.005,.995/scale/OHEmin100max40dropfirst,regionexcluded;sampleweights onlychange',
 'source_trees':'same200depth3leaves8lr.025min5000L2500L1100seed2026102506,Tweedie1.5 residual,parentandcaseweights new;weightsum normalizationpreservesoriginalregularization scale',
 'source_veto':'5pairedsavedsourceblocks,baselineC17samefamily,sameunweightedtotal-periodTweedie1.5costloss;pooledratio<=1.002 and>=4/5foldsinside1.002. Alreadyadaptive sourceblocks,not independentconfirmation;vetoedfamilies nottransferred',
 'target_flow':'perouterfoldkfitfullsourcepriceprofessor(s)withfrozenkdomainmodel,thenminimalTweedie1.5adapteroutsidek. SourcefullteacherisNOTshared acrossouterfolds,becauseitsweightsdependonouterfitattrs. Fitonlynumeric/sourcecategories,unchangedtargetadapter/labels/exposure/C0.',
 'real_fit_budget_max':30,'source_pilot_fits':10,'full_source_fits_max':10,'target_fits_max':10,'new_domain_fits':0,'new_C0_fits':0,'first_gate_fail_price_fits':0,
 'outputs':'R132/R133motorfixedsqrt50/50B20;R134/R135natural;allhomeprices copiedexactR36,no newinference;nooptimizedweights','primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'preference_order':IDS,
 'scope':'strict2023,sourcecomponentblocks/saved5emergingfolds,T0/exposure/C0 preserved;no2024 orweatheradmission','pending_public_CSVs_unchanged':True,'2024_closed':True,'B00_preserved':True,'promotion':False,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'max_price_fits':30,'new_domain_fits':0,'new_C0':0,'synthetic_price_fits':6}))

def check(plan):
 for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256'],x['path']

def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];pilots=[]
 f=pq.read_table(SOURCE,filters=[('year','=',2023)]).to_pandas();blocks=pq.read_table(BLOCKS).to_pandas();f=f.merge(blocks[m.KEY+['source_group_id','source_fold']],on=m.KEY,how='left',validate='one_to_one');assert f.source_fold.notna().all();domains={k:joblib.load(DOMAIN/f'models/motor_fold{k}.joblib') for k in range(5)};weight_checks=[]
 for k in range(5):
  for role,z in [('pilot',f[f.source_fold.ne(k)]),('full',f)]:
   with threadpool_limits(limits=2):_,wr=m.weights(z,domains[k])
   wr.update(role=role,fold=k);weight_checks.append(wr)
 weights_pass=all(x['combined_weight_ESS_fraction']>=.5 for x in weight_checks);dump(OUT/'combined_weight_preflight.json',{'checks':weight_checks,'all_pass':weights_pass,'price_fits_sofar':0})
 if weights_pass:
  for k in range(5):
   fit=f[f.source_fold.ne(k)].copy();val=f[f.source_fold.eq(k)].copy();parents={};ref=joblib.load(BAGS/f'motor_bag{k}.joblib')
   for key in ['source_group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   for recipe in RECIPES:
    event('source_pilot_started',fold=k,model_id=recipe['id'])
    with threadpool_limits(limits=2):t,rec=m.fit_source(fit,domains[k],recipe['kind'],parent=parents.get('glm'));pred=m.teacher_rate(t,val)*val.exposure.to_numpy();baseline=m.old.teacher_rate(ref[recipe['reference']],val)*val.exposure.to_numpy()
    parents[recipe['kind']]=t;rec.update(role='source_pilot',fold=k,model_id=recipe['id']);receipts.append(rec);path=OUT/f'pilot_models/{recipe["id"]}_motor_fold{k}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);dump(path.with_suffix('.json'),rec)
    with threadpool_limits(limits=2):assert np.array_equal(pred,m.teacher_rate(joblib.load(path),val)*val.exposure.to_numpy())
    row={'fold':k,'model_id':recipe['id'],'candidate_loss':float(m.unit_deviance(val.T0,pred).sum()),'reference_loss':float(m.unit_deviance(val.T0,baseline).sum()),'groups_disjoint':True,'replay_exact':True};row['relative_difference']=row['candidate_loss']/row['reference_loss']-1;pilots.append(row);dump(OUT/f'pilot_metrics/{recipe["id"]}_fold{k}.json',row);event('source_pilot_complete',**row)
 summaries=[];eligible=[]
 if weights_pass:
  for recipe in RECIPES:
   rows=[x for x in pilots if x['model_id']==recipe['id']];ratio=sum(x['candidate_loss'] for x in rows)/sum(x['reference_loss'] for x in rows)-1;folds=sum(x['relative_difference']<=.002 for x in rows);passed=bool(ratio<=.002 and folds>=4);summaries.append({'model_id':recipe['id'],'line':'motor','pooled_relative_loss':ratio,'folds_inside_tolerance':folds,'pass':passed})
   if passed:eligible.append(recipe['id'])
 dump(OUT/'source_veto.json',{'summaries':summaries,'eligible':eligible,'combined_weight_preflight_pass':weights_pass})
 if not eligible:
  base=read(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json');report={'summaries':[x for x in base['summaries'] if x['model_id'] in ['W2-B00','W2-B20','W2-COD-R36']],'gates':[],'pairs':[],'new_price_fits':len(receipts),'new_C0_fits':0,'stop_reason':'combined_weights_ESS_failed_before_anypricefit' if not weights_pass else 'sourceweightedfamiliesfailed;no fullsource/targetfits','selected_exploratory_variant':None,'2024_closed':True,'B00_preserved':True}
 else:
  inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();old=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();outputs=[]
  for k in range(5):
   teachers={}
   for recipe in RECIPES:
    if recipe['kind']=='trees' and recipe['id'] not in eligible:continue
    event('source_full_started',fold=k,model_id=recipe['id'])
    with threadpool_limits(limits=2):t,rec=m.fit_source(f,domains[k],recipe['kind'],parent=teachers.get('glm'))
    teachers[recipe['kind']]=t;rec.update(role='source_full',outer_fold=k,model_id=recipe['id']);receipts.append(rec);path=OUT/f'teachers/{recipe["id"]}_motor_outer{k}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);dump(path.with_suffix('.json'),rec)
    with threadpool_limits(limits=2):assert np.array_equal(m.teacher_rate(t,f.iloc[:512]),m.teacher_rate(joblib.load(path),f.iloc[:512]))
   z=pq.read_table(BASE/f'motor_fold{k}.parquet',filters=[('year','=',2023)]).to_pandas();fit=z[z.fold.ne(k)].copy();val=z[z.fold.eq(k)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=inc[inc.line.eq('motor')&inc.fold.eq(k)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.eq('motor')&old.fold.eq(k)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
   for col in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[col].to_numpy(),ref[col].to_numpy())
   for recipe in RECIPES:
    if recipe['id'] not in eligible:continue
    with threadpool_limits(limits=2):b,rec=m.fit(fit,'motor',k,teachers[recipe['kind']],recipe['id']);rate=m.predict(b,val)
    path=OUT/f'models/{recipe["id"]}_motor_fold{k}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
    rec.update(role='target',replay_exact=True,source_teacher_depends_on_outerfit_only=True,domain_held_fold=k);receipts.append(rec);dump(path.with_suffix('.json'),rec);row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row);pure=row.copy();pure['model_id']=NATURAL[recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);event('target_fold_complete',fold=k,model_id=recipe['id'])
  ids=[x for x in IDS if x in eligible or x in [NATURAL[q] for q in eligible]]
  for mid in ids:
   home=inc[inc.line.ne('motor')].copy();home['model_id']=mid;outputs.append(home)
  new=pd.concat(outputs,ignore_index=True);assert len(new)==len(ids)*50094 and not new.duplicated(['model_id']+m.KEY).any();new.to_parquet(OUT/'new_oof_2023.parquet',index=False);report=evaluate(pd.concat([old,inc],ignore_index=True),new,ids,len(receipts),reference_id='W2-COD-R36');report.update(home_exact_R36=True,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None))
 report.update(id=plan['id'],utc=now(),author='Codex',primary_reference='W2-COD-R36',source_eligible=eligible,source_gate=summaries,combined_weight_preflight_pass=weights_pass,new_domain_fits=0,promotion=False);check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=len(receipts),gates=report['gates'],source_eligible=eligible)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
