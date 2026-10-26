"""Preflight nuevo de diferencia conjunta de atributos; ningún ajuste de precios."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import diagnostico_dominio2023 as m
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/prefiltro_dominio2023_v3';PLAN=R/'registro/semana2_dominio2023_prefiltro_plan_v3.json';SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';BLOCKS=R/'privado/semana2/robustez2023/bloques_fuente2023_v1';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';LINES=['motor','buildings','contents']
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()

def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf8') as h:json.dump(x,h,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))

META=m.KEY+['year','is_test','customer_id','address_id']
def projection(path,line,extra):
 names=set(pq.ParquetFile(path).schema_arrow.names);mapping={}
 for c in META+extra+m.columns(line):
  raw='x_'+c.removeprefix('x_log_')
  if c in names:mapping[c]=c
  elif c.startswith('x_log_') and raw in names:mapping[c]=raw
  else:raise AssertionError('Missing allowed attribute '+c+' in '+str(path))
 assert not set(mapping.values()).intersection(['T0','reserve','exposure','e_cost_mix_1.0'])
 return mapping

def read_allowed(path,line,extra):
 mapping=projection(path,line,extra);f=pq.read_table(path,columns=list(dict.fromkeys(mapping.values())),filters=[('year','=',2023)]).to_pandas();out=pd.DataFrame(index=f.index)
 for target,stored in mapping.items():
  if target==stored:out[target]=f[stored]
  else:
   raw=pd.to_numeric(f[stored],errors='coerce');out[target]=np.log1p(raw.where(raw.ge(0)))
 return out

def synthetic_projection():
 line='motor';n=4;f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'customer_id':['c'+str(i) for i in range(n)],'address_id':['a'+str(i) for i in range(n)],'fold':range(n),'group_id':['g'+str(i) for i in range(n)]})
 for c in m.block(line)['numeric']:f[c]=1.
 for c in m.block(line)['categorical']:f[c]='A'
 raw=f.copy()
 for c in ['x_log_voluntary_excess','x_log_compulsory_excess']:
  values=pd.Series([0.,10.,np.nan,-1.]);f[c]=np.log1p(values.where(values.ge(0)));raw=raw.drop(columns=c);raw['x_'+c.removeprefix('x_log_')]=values
 for frame in [f,raw]:frame['T0']=1e15;frame['exposure']=1e15;frame['reserve']=1e15;frame['e_cost_mix_1.0']=1e15
 a=OUT/'fixtures/prelogged_2023.parquet';b=OUT/'fixtures/raw_2023.parquet';a.parent.mkdir();f.to_parquet(a,index=False);raw.to_parquet(b,index=False);left=read_allowed(a,line,['fold','group_id']);right=read_allowed(b,line,['fold','group_id']);assert left.equals(right) and not set(left).intersection(['T0','reserve','exposure','e_cost_mix_1.0'])
 dump(OUT/'synthetic_projection.json',{'raw_vs_prelogged_exact':True,'negative_raw_to_missing':True,'forbidden_columns_not_projected':True,'classifier_fits':0,'price_fits':0})

def synthetic():
 rng=np.random.default_rng(2026102534);rows=[]
 for market in ['developed','emerging']:
  n=800;f=pd.DataFrame({'market':market,'line':'motor','row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5})
  for c in m.block('motor')['numeric']:f[c]=rng.normal(size=n)+(market=='emerging')*.2
  for c in m.block('motor')['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  f['x_new_business']=(np.arange(n)%2).astype(float);rows.append(f)
 f=pd.concat(rows,ignore_index=True);fit=f[f.fold.ne(0)];val=f[f.fold.eq(0)]
 with threadpool_limits(limits=2):b,rec=m.fit(fit,'motor',0);before=joblib.hash(b);score,prob=m.predict(b,val);s2,p2=m.predict(b,val.assign(**{'T0':1e15,'reserve':1e15,'exposure':1e15,'e_cost_mix_1.0':1e15}))
 assert np.array_equal(score,s2) and np.array_equal(prob,p2) and joblib.hash(b)==before
 for bad in [fit.assign(year=2024),pd.concat([fit,fit.iloc[:1]]),f]:
  try:m.fit(bad,'motor',0)
  except AssertionError:pass
  else:raise AssertionError('Adverse fit guard accepted')
 dump(OUT/'synthetic.json',{'diagnostic_classifier_fits':1,'price_fits':0,'adverse_year_duplicate_held_rejected':True,'outcome_C0_exposure_poison_ignored':True,'teacher_immutable_on_prediction':True,'manual_logistic_probability_checked':True,'receipt':rec})

def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
 previous=R/'privado/semana2/robustez2023/prefiltro_dominio2023_v2';oldhash={x['path']:x['sha256'] for x in read(previous/'plan.json')['sources']};assert oldhash[rel(Path(m.__file__))]==sha(Path(m.__file__))
 dump(OUT/'synthetic_classifier_reused.json',{'receipt':rel(previous/'synthetic.json'),'sha256':sha(previous/'synthetic.json'),'unchanged_classifier_module_sha256':sha(Path(m.__file__)),'new_classifier_fits':0});synthetic_projection()
 projections=[]
 for line in LINES:
  for path,extra in [(SOURCE/f'{line}_2023.parquet',[])]+[(BASE/f'{line}_fold{k}.parquet',['fold','group_id']) for k in range(5)]:projections.append({'path':rel(path),'mapping':projection(path,line,extra)})
 dump(OUT/'input_projection.json',{'files':projections,'all18_schemas_checked_before_real_fit':True,'rule':'read allowed storedattrs only;log1p(nonnegative raw) whereprelognotstored;negative raw tomissing;nooutcome/exposure/C0read'})
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelos_robustos2023.py',R/'privado/semana2/robustez2023/mision017_20261025_v1/numeric_overlap2023_v3.json',R/'privado/semana2/robustez2023/ciclo33_20261025_v1/report.json']+[SOURCE/f'{line}_2023.parquet' for line in LINES]+[BLOCKS/f'{line}.parquet' for line in LINES]+[BASE/f'{line}_fold{k}.parquet' for line in LINES for k in range(5)]
 paths+=[OUT/'input_projection.json',previous/'plan.json',previous/'synthetic.json',previous/'failure_before_real_fit.json']
 plan={'id':'S2-DOMINIO2023-PREFILTRO-v3-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-DOMINIO-PREVIO-V3','hypothesis':'C26 marginalmissingness matching and C33 source loss improvements didnot robustlytransfer. Numeric overlapv3 explicitly didnot measure joint attributes. Before more sourceprice fits,measure whether standardlinearclassifier separates markets and whether prospectivefitonlydensityweights would have adequate empiricaloverlap. This cannot establish equality of conditionalclaimmeans.',
 'model':'logisticL2 C1,class_weightbalanced,lbfgs1500tol1e-7;fitonlymedian+missingindicators/clip.005,.995/scale/OHEmin100max40dropfirst;samephysicalcolumns asprice teachers,exclude source region/buildingconstruction;no claim outcomes,exposure,C0,premiums,IDs ormarket asinputs',
 'columns':{line:m.block(line) for line in LINES},'scope':'15 classifiers,3linesx5pairedexistingcomponentfolds;sourceheldblocks andemergingheldfoldboth excludedfromalllearning;no2024 or2025 consumed;row densities,notexposure densities',
 'budget':{'real_diagnostic_classifier_fits':15,'price_fits':0,'C0_fits':0,'new_price_inference':0},'diagnostic_only':True,'fixed_density_ratio':'balanced-prior odds exp(logit);prospectivecandidate clip[.2,5] onlydiagnosed onsourceheld;not applied to prices orcase inclusion',
 'need_screen':'perline heldAUC>=.65 inatleast4/5folds;withoutthis no weightingrecipe justified bythisscreen','overlap_screen':'inall5sourceheldfolds,clippedratioESS/n>=.5 andclippedfraction<=.2;inall5targetheldfolds,P(domain|X)>.95 fraction<=.05;thresholdsnotselectedfromresults',
 'consequences':'only ifneed+overlappassmay a separate priceweightrecipe beconsidered,with fullpreregistration/sourcecontrols/primaryR36gates;no automatic fit/promotion. Failedscreen doesnot provejointdomainsequality or that weightingcannothelp.',
 'limits':'linear densitydiagnosticmissesnonlinearshift,oddsapproximationnotidentifiedtruedensity,outcomesmaydiffer,2023 adaptive foldsnotindependentconfirmation;no newemergingsupport orsafeultimateinference',
 '2024_closed':True,'B00_preserved':True,'promotion':False,'pending_public_CSVs_unchanged':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'diagnostic_fits':15,'price_fits':0,'C0_fits':0}))

def check(plan):
 for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256'],x['path']

def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});receipts=[];metrics=[]
 for line in LINES:
  source=read_allowed(SOURCE/f'{line}_2023.parquet',line,[]);blocks=pq.read_table(BLOCKS/f'{line}.parquet',columns=m.KEY+['source_fold','source_group_id']).to_pandas();source=source.merge(blocks,on=m.KEY,how='left',validate='one_to_one');assert source.source_fold.notna().all();source['fold']=source.source_fold
  for fold in range(5):
   target=read_allowed(BASE/f'{line}_fold{fold}.parquet',line,['fold','group_id']);sf=source[source.fold.ne(fold)].copy();sv=source[source.fold.eq(fold)].copy();tf=target[target.fold.ne(fold)].copy();tv=target[target.fold.eq(fold)].copy()
   for a,b,group in [(sf,sv,'source_group_id'),(tf,tv,'group_id')]:
    for key in [group,'customer_id','address_id']:assert set(a[key]).isdisjoint(b[key])
   fit=pd.concat([sf,tf],ignore_index=True);val=pd.concat([sv,tv],ignore_index=True)
   with threadpool_limits(limits=2):b,rec=m.fit(fit,line,fold);before=joblib.hash(b);logit,prob=m.predict(b,val)
   path=OUT/f'models/{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
   with threadpool_limits(limits=2):logit2,prob2=m.predict(joblib.load(path),val)
   assert np.array_equal(logit,logit2) and np.array_equal(prob,prob2) and joblib.hash(b)==before
   chosen=val.market.eq('developed').to_numpy();raw=np.exp(np.clip(logit[chosen],-700,700));weights=np.clip(raw,.2,5.);ess=float(weights.sum()**2/np.dot(weights,weights));row={'line':line,'fold':fold,'AUC':float(roc_auc_score(val.market.eq('emerging'),logit)),'source_held_rows':int(chosen.sum()),'target_held_rows':int((~chosen).sum()),'weight_clip_fraction':float(np.mean((raw<.2)|(raw>5.))),'clipped_weight_ESS_fraction':ess/chosen.sum(),'target_domain_probability_above95_fraction':float(np.mean(prob[~chosen]>.95)),'replay_exact':True,'groups_disjoint':True,'price_fits':0}
   metrics.append(row);rec.update(replay_exact=True,model_sha256=sha(path));receipts.append(rec);dump(path.with_suffix('.json'),rec);dump(OUT/f'metrics/{line}_fold{fold}.json',row);print(json.dumps(row),flush=True)
 summaries=[]
 for line in LINES:
  rows=[x for x in metrics if x['line']==line];need=sum(x['AUC']>=.65 for x in rows)>=4;overlap=all(x['clipped_weight_ESS_fraction']>=.5 and x['weight_clip_fraction']<=.2 and x['target_domain_probability_above95_fraction']<=.05 for x in rows);summaries.append({'line':line,'AUC_min':min(x['AUC'] for x in rows),'AUC_max':max(x['AUC'] for x in rows),'folds_AUC_at_least65':sum(x['AUC']>=.65 for x in rows),'minimum_ESS_fraction':min(x['clipped_weight_ESS_fraction'] for x in rows),'maximum_clip_fraction':max(x['weight_clip_fraction'] for x in rows),'need_screen_pass':need,'overlap_screen_pass':overlap,'weighting_recipe_can_be_considered':bool(need and overlap),'price_recipe_authorized_by_this_report':False})
 check(plan);assert len(receipts)==15;report={'id':plan['id'],'author':'Codex','utc':now(),'summaries':summaries,'metrics':metrics,'diagnostic_classifier_fits':15,'price_fits':0,'C0_fits':0,'new_price_inference':0,'new_Kaggle_submissions':0,'2024_closed':True,'B00_preserved':True,'promotion':False,'adaptive_exploratory':True,'outcome_cost_exposure_C0_columns_never_loaded':True}
 dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});print(json.dumps({'complete':True,'summary':summaries,'price_fits':0}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
