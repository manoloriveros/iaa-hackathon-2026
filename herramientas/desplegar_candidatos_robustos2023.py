"""Tres adaptadores finales y dos CSV de pesos predefinidos; no recalcúla C0."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys,os
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import desplegar_robustez2023 as deploy
from semana2 import modelo_profesor_comun2023 as core
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/entrega_20261025_v1';PLAN=R/'registro/semana2_robustez2023_entrega_plan.json'
OLD=R/'privado/semana2/modelo_final_g4_2023/final_20261024_v1/attempt1'
BROAD=R/'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/inputs_2023'
RAW=ROOT/'Hackaton/Semana 2/Datos/emerging';FID='COD-S2-20261025-ROBUSTEZ-ENTREGA-PREVIO'
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,o):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def event(name,**kw):
 d={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(d)+'\n')
 print(json.dumps(d),flush=True)
def check(plan):
 for x in plan['sources']:assert sha(ROOT/x['path'])==x['sha256'],x['path']


class FixedZero:
 def transform(self,frame):return np.zeros((len(frame),1))
class FixedRate:
 def predict(self,matrix):return np.full(len(matrix),100.)


def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
 screening=read(R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json')
 assert all(next(x for x in screening['gates'] if x['model_id']==mid)['all_pass'] for mid in ['W2-COD-R37','W2-COD-R36'])
 n=1200;rng=np.random.default_rng(2026102508);line='motor'
 f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 f['e_cost_mix_1.0']=f.exposure*.98
 for c in core.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 f['x_new_business']=(np.arange(n)%2).astype(float)
 for c in core.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['T0']=rng.poisson(.3,n)*rng.gamma(3,300,n)
 teacher={'family':'SourceGLM','line':line,'columns':['x_new_business'],'transformer':FixedZero(),'estimator':FixedRate()}
 train=f[f.fold.ne(0)].copy();valid=f[f.fold.eq(0)].copy()
 with threadpool_limits(limits=2):
  old,orec=core.fit(train,line,0,{'id':'SYN','synthetic':True,'_teacher':teacher})
  new,nrec=deploy.fit_adapter(train,line,teacher)
  assert np.array_equal(old['coef'],new['coef'])
  assert np.array_equal(core.predict(old,valid),core.predict(new,valid))
 try:deploy.fit_adapter(train.assign(year=2024),line,teacher)
 except AssertionError:pass
 else:raise AssertionError('2024aceptado')
 dump(OUT/'synthetic_consumer.json',{'synthetic_price_fits':2,'real_fits':0,'adapter_core_coefficients_exact':True,'predictions_exact':True,'2024_rejected':True,'new_receipt':nrec,'prior_receipt':orec})
 sources=[Path(__file__),Path(deploy.__file__),Path(core.__file__),Path(core.base.__file__),R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/modelos_robustos_compuestos2023.py',
  R/'privado/semana2/robustez2023/ciclo7_20261025_v1/report.json',R/'registro/semana2_robustez2023_ciclo7_plan.json',
  OLD/'submission_g4_glm_2023_2025.csv',RAW/'sample_submission.parquet',RAW/'addresses.parquet']
 for line in core.FEATURES:
  sources += [deploy.TEACHERS[line],BROAD/f'{line}.parquet',OLD/f'training/{line}_2023.parquet',OLD/f'quotes/{line}_2025.parquet',RAW/f'test_{line}.parquet']
 plan={'id':'S2-ROBUSTEZ-ENTREGA-v1-20261025','utc':now(),'author':'Codex','forum_prior':FID,
  'authorization_context':'User asks autonomous work until materially better robust model after explicit ownCSV submission; no further questions. Research deliveries only; no final selection or2024opening.',
  'models':[{'id':'W2-COD-R37-FINAL','teacher_price_weight':.25,'baseline_price_weight':.75,'filename':'submission_R37_transfer25_GLM75_2025.csv','role':'primary per preregistered conservative preference'},
            {'id':'W2-COD-R36-FINAL','teacher_price_weight':.5,'baseline_price_weight':.5,'filename':'submission_R36_transfer50_GLM50_2025.csv','role':'secondary frozen alternative, no public tuning'}],
  'formula':'(teacher_weight*sqrt(fullR35 price)+(1-teacher_weight)*sqrt(own frozen G4-B20 price))**2',
  'source_teachers':'Frozen source2023 only; buildings construction excluded; other lines exactR32',
  'full_target_scope':'all50094emerging2023; three adapters same CV numerical recipe, no source/C0/capital reestimation',
  'feature_connection':'2023broad+frozenG4core capital/C0;2025frozenG4core+raw physical extras; originalcolumns preserved',
  'real_fit_budget':3,'synthetic_price_fits':2,'price_years_train':[2023],'price_years_predict':[2025],
  'C0_reestimated':False,'B00_preserved':True,'2024_closed':True,'promotion':False,'manual_final_selection':False,
  'public_check_plan':'At most two submissions, both recipes fixed before seeing either score, quota permitting. Record actual status/score; never adjust weights to public score.',
  'baseline_sha256':'e5e30c5921c0494b7c0bebe76fbf33725f45ab392f7bed5ab7f6927a89f394ab',
  'sources':[{'path':rel(p),'sha256':sha(p)} for p in sources]}
 assert sha(OLD/'submission_g4_glm_2023_2025.csv')==plan['baseline_sha256']
 dump(PLAN,plan);dump(OUT/'plan.json',plan)
 print(json.dumps({'plan':rel(PLAN),'models':plan['models'],'new_real_fit_budget':3,'synthetic_exact_consumer':True}))


def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists()
 dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})
 (OUT/'models').mkdir();(OUT/'training').mkdir();(OUT/'quotes').mkdir()
 receipts=[];models={}
 for line in core.FEATURES:
  block=core.FEATURES[line];rawcols=[c.replace('x_log_voluntary_excess','x_voluntary_excess').replace('x_log_compulsory_excess','x_compulsory_excess').replace('x_log_distance_to_river_km','x_distance_to_river_km') for c in block['numeric']+block['categorical']]
  meta=core.KEY+['year','is_test','policy_id','customer_id','address_id','group_id','fold','period_start','period_end','T0','exposure']
  frame=pq.read_table(BROAD/f'{line}.parquet',columns=list(dict.fromkeys(meta+rawcols)),filters=[('year','=',2023)]).to_pandas().sort_values(core.KEY).reset_index(drop=True)
  frozen=pq.read_table(OLD/f'training/{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas().sort_values(core.KEY).reset_index(drop=True)
  assert frame[core.KEY].equals(frozen[core.KEY])
  for c in ['year','is_test','T0','exposure','fold','group_id','policy_id','customer_id','address_id']:assert np.array_equal(frame[c].to_numpy(),frozen[c].to_numpy()),c
  if line!='motor':frame['x_log_sum_insured']=frozen.x_log_sum_insured.to_numpy()
  frame['e_cost_mix_1.0']=frozen.C0.to_numpy();core.guard(frame,line)
  with threadpool_limits(limits=2):b,rec=deploy.fit_final(frame,line)
  path=OUT/f'models/R35_final_{line}.joblib';joblib.dump(b,path,compress=3)
  frame.to_parquet(OUT/f'training/{line}_2023.parquet',index=False)
  with threadpool_limits(limits=2):assert np.array_equal(core.predict(b,frame),core.predict(joblib.load(path),frame))
  rec.update(teacher_sha256=sha(deploy.TEACHERS[line]),training_frame_sha256=sha(OUT/f'training/{line}_2023.parquet'),replay_training_exact=True)
  dump(OUT/f'models/{line}_receipt.json',rec);receipts.append(rec);models[line]=b
  event('final_adapter_fit_complete',line=line,rows=len(frame),real_fits=len(receipts))
 assert len(receipts)==3 and sum(x['fit_rows'] for x in receipts)==50094
 dump(OUT/'all_three_fits_complete.json',{'utc':now(),'real_fits':3,'quote_value_reads_started':False,'receipts':receipts})
 # Las cotizaciones se decodifican después de terminar los tres ajustes.
 addresses=pq.read_table(RAW/'addresses.parquet',columns=['address_id','distance_to_river_km','elevation_m','roof_type','soil_type','basement']).to_pandas();assert addresses.address_id.is_unique
 predictions=[];replay_checks=[]
 for line in core.FEATURES:
  frozen=pq.read_table(OLD/f'quotes/{line}_2025.parquet',filters=[('year','=',2025)]).to_pandas()
  raw=pq.read_table(RAW/f'test_{line}.parquet',columns=['row_id','period_start','period_end']+deploy.POLICY_EXTRAS[line]).to_pandas()
  quotes=deploy.enrich_quotes(frozen,raw,addresses,line)
  before=joblib.hash(models[line])
  with threadpool_limits(limits=2):
   rate=core.predict(models[line],quotes,training=False);again=core.predict(joblib.load(OUT/f'models/R35_final_{line}.joblib'),quotes,training=False)
  assert np.array_equal(rate,again) and joblib.hash(models[line])==before
  quotes.to_parquet(OUT/f'quotes/{line}_2025.parquet',index=False)
  predictions.append(pd.DataFrame({'row_id':quotes.row_id.to_numpy(),'prediction':rate*quotes.exposure.to_numpy()}))
  replay_checks.append({'line':line,'rows':len(quotes),'disk_replay_exact':True,'state_unchanged':True,'original_G4_fields_unchanged':True})
 allpred=pd.concat(predictions,ignore_index=True);assert allpred.row_id.is_unique and len(allpred)==209063
 sample=pq.read_table(RAW/'sample_submission.parquet',columns=['row_id']).to_pandas()
 teacher=sample.merge(allpred,on='row_id',validate='one_to_one',how='left');assert teacher.row_id.equals(sample.row_id)
 baseline=pd.read_csv(OLD/'submission_g4_glm_2023_2025.csv',dtype={'row_id':str},float_precision='round_trip')
 assert baseline.row_id.equals(sample.row_id)
 csvs=[]
 teacher.to_parquet(OUT/'R35_unpooled_predictions2025.parquet',index=False)
 for recipe in plan['models']:
  w=recipe['teacher_price_weight'];out=sample.copy();out['prediction']=(w*np.sqrt(teacher.prediction)+(1-w)*np.sqrt(baseline.prediction))**2
  assert np.isfinite(out.prediction).all() and out.prediction.gt(0).all() and len(out)==209063
  path=OUT/recipe['filename'];out.to_csv(path,index=False,float_format='%.17g',lineterminator='\n')
  disk=pd.read_csv(path,dtype={'row_id':str},float_precision='round_trip');assert disk.equals(out)
  csvs.append({'model_id':recipe['id'],'path':rel(path),'sha256':sha(path),'rows':len(out),'columns':list(out),'weight':w,'CSV_roundtrip_exact':True,'bytes':path.stat().st_size})
 check(plan)
 result={'id':plan['id'],'utc':now(),'author':'Codex','CSV':csvs,'new_price_fits':3,'new_C0_fits':0,'source_teachers_refitted':False,
  'replay_checks':replay_checks,'real_training_rows':50094,'quote_rows':209063,'quote_reads_after_all_three_fits':True,
  '2024_policy_rows_read':0,'2024_scores_read':False,'B00_preserved':True,'baseline_original_sha256_unchanged':sha(OLD/'submission_g4_glm_2023_2025.csv')==plan['baseline_sha256'],
  'promotion':False,'submission_sent':False,'professional_independent_validation':False}
 dump(OUT/'ready.json',result);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]})
 event('CSVs_ready',CSV=csvs,new_price_fits=3)


if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['prepare','run']);args=a.parse_args()
 if args.action=='prepare':prepare()
 else:run()
