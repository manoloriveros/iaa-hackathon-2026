"""Menor riesgo de transporte: suprime construcción ambigua y pooling fijo."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_profesor_comun2023 as m
from semana2.evaluar_robustez2023 import evaluate
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
from sklearn.metrics import mean_tweedie_deviance
OUT=R/'privado/semana2/robustez2023/ciclo7_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo7_plan.json'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023'
PARENT=R/'privado/semana2/robustez2023/ciclo6_20261025_v1/new_oof_2023.parquet'
OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/buildings_2023.parquet'
FID='COD-S2-20261025-ROBUSTEZ7-PREVIO'
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,o):
 p.parent.mkdir(exist_ok=True,parents=True)
 with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']


def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
 # Prueba de la propiedad convexa en v=sqrt(mu); no se presume convexidad en mu.
 y=np.r_[0.,1.,100.,1e6];a=np.r_[.01,1.,1000.,1e4];b=np.r_[100.,10.,5.,1e6]
 for w in [.25,.5]:
  mu=(w*np.sqrt(a)+(1-w)*np.sqrt(b))**2
  assert np.all(m.unit_deviance(y,mu)<=w*m.unit_deviance(y,a)+(1-w)*m.unit_deviance(y,b)+1e-8)
 n=12000;rng=np.random.default_rng(2026102507);line='buildings'
 f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
 f['e_cost_mix_1.0']=f.exposure*.98
 for c in m.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
 f['x_new_business']=(np.arange(n)%2).astype(float)
 for c in m.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
 f['x_construction_type']='timber';f['T0']=rng.poisson(.3,n)*rng.gamma(3,300,n)
 s=f.copy();s['market']='developed';s['x_construction_type']='W';s['T0']=rng.poisson(.3,n)*rng.gamma(3,500,n)
 with threadpool_limits(limits=2):
  teachers,source_receipt=m.fit_teachers(s,line);teacher=teachers['W2-COD-R32']
  assert 'x_construction_type' not in teacher['columns'] and 'x_construction_type' not in teacher['parent']['columns']
  bundle,adapter=m.fit(f[f.fold.ne(0)],line,0,{'id':'SYN','synthetic':True,'_teacher':teacher})
  val=f[f.fold.eq(0)];pred=m.predict(bundle,val);assert np.array_equal(pred,m.predict(bundle,val.assign(T0=1e12)))
 dump(OUT/'synthetic.json',{'synthetic_price_fits':3,'real_fits':0,'construction_excluded':True,'held_label_invariance_predict':True,'sqrt_pool_Jensen_verified':True,'source_receipt':source_receipt,'adapter':adapter})
 sources=[SOURCE,PARENT,OLD,*[BASE/f'buildings_fold{fold}.parquet' for fold in range(5)],Path(__file__),Path(m.__file__),Path(m.base.__file__),
  R/'src/semana2/evaluar_robustez2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/modelos_robustos_compuestos2023.py',
  ROOT/'Hackaton/Semana 1/Revision_construccion/analyze_construction.py',
  ROOT/'Hackaton/Semana 1/Revision_construccion/runs/construction_20261016T192514Z_779b361e/evidence/official_data_description.md']
 plan={'id':'S2-ROBUSTEZ2023-CICLO7-v1-20261025','utc':now(),'author':'Codex','forum_prior':FID,
  'models':[{'id':'W2-COD-R35','building_teacher':'source physical, exclude construction, other lines exactR32'},
            {'id':'W2-COD-R36','formula':'square(0.5*sqrt(R35)+0.5*sqrt(B20))'},
            {'id':'W2-COD-R37','formula':'square(0.25*sqrt(R35)+0.75*sqrt(B20))'}],
  'hypothesis':'Remove unsupported construction-code transport without guessing W=timber; fixed sqrt-price pooling dampens uncertain transfer while preserving a p1.5 per-row Jensen bound. No weights fitted or level probes.',
  'semantic_evidence':'official developed dictionary says timber/non-standard; historic code explicitly says W material unconfirmed. Case aliases and opaqueW are not silently mapped to emerging timber.',
  'price_fit_budget':7,'source_fits':2,'target_building_adapter_fits':5,'other_line_models_reused':10,
  'source_params':'same sourceGLM and source-only residual teacherR32, only remove building construction column',
  'adapter_params':'same intercept+new_business+region ridge1,source shapes fixed',
  'folds':'existing five connected groups;only2023','C0':'exact inherited, no recalculation',
  'criteria':{'delta_B20':.005,'lower_bound':.0005,'positive_folds':4,'segment_harm_full_null':.0005,'after31groups':.0005},
  'bootstrap':{'seed':2026102501,'replicates':2000,'quantiles':[.0041666666667,.9958333333333]},
  'preference_if_multiple_pass':['W2-COD-R37','W2-COD-R36','W2-COD-R35'],
  'status':'exploratory;no formal promotion;prior adaptive search remains','2024_closed':True,'B00_preserved':True,
  'sources':[{'path':rel(p),'sha256':sha(p)} for p in sources]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan)
 print(json.dumps({'plan':rel(PLAN),'fits':7,'three_candidates_fixed':True}))


def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists()
 dump(OUT/'started.json',{'utc':now(),'real_fit_budget':7})
 f=pq.read_table(SOURCE,filters=[('year','=',2023)]).to_pandas()
 with threadpool_limits(limits=2):teachers,source_receipt=m.fit_teachers(f,'buildings')
 assert 'x_construction_type' not in teachers['W2-COD-R32']['columns']
 dst=OUT/'teachers/W2-COD-R35_buildings.joblib';dst.parent.mkdir();joblib.dump(teachers['W2-COD-R32'],dst,compress=3)
 dump(OUT/'source_teacher_receipt.json',source_receipt)
 parent=pq.read_table(PARENT,filters=[('model_id','=', 'W2-COD-R32'),('year','=',2023)]).to_pandas()
 assert len(parent)==50094 and parent.year.eq(2023).all()
 inherited=parent[parent.line.ne('buildings')].copy();inherited['model_id']='W2-COD-R35';outputs=[inherited];receipts=[]
 for fold in range(5):
  block=m.FEATURES['buildings'];raw=[c.replace('x_log_voluntary_excess','x_voluntary_excess').replace('x_log_compulsory_excess','x_compulsory_excess').replace('x_log_distance_to_river_km','x_distance_to_river_km') for c in block['numeric']+block['categorical']]
  cols=list(dict.fromkeys(m.KEY+['year','is_test','fold','group_id','customer_id','address_id','T0','exposure','e_cost_mix_1.0']+raw))
  frame=pq.read_table(BASE/f'buildings_fold{fold}.parquet',columns=cols,filters=[('year','=',2023)]).to_pandas()
  fit=frame[frame.fold.ne(fold)].copy();val=frame[frame.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
  for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
  ref=parent[parent.line.eq('buildings')&parent.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
  assert val[m.KEY].equals(ref[m.KEY]) and np.array_equal(val.T0,ref.T0) and np.array_equal(val['e_cost_mix_1.0'],ref['e_cost_mix_1.0'])
  with threadpool_limits(limits=2):bundle,rec=m.fit(fit,'buildings',fold,{'id':'W2-COD-R35'});rate=m.predict(bundle,val)
  path=OUT/f'models/W2-COD-R35_buildings_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(bundle,path,compress=3)
  with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
  rec['replay_exact']=True;dump(path.with_suffix('.json'),rec);receipts.append(rec)
  row=ref.copy();row['model_id']='W2-COD-R35';row['annual_rate']=rate;row['prediction']=rate*row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
 fresh=pd.concat(outputs,ignore_index=True).sort_values(m.KEY).reset_index(drop=True)
 old=pq.read_table(OLD,filters=[('model_id','in',['W2-B00','W2-B20']),('year','=',2023)]).to_pandas()
 b20=old[old.model_id.eq('W2-B20')].sort_values(m.KEY).reset_index(drop=True);assert fresh[m.KEY].equals(b20[m.KEY])
 variants=[fresh];jensen=[]
 for mid,w in [('W2-COD-R36',.5),('W2-COD-R37',.25)]:
  x=fresh.copy();x['model_id']=mid;x['prediction']=(w*np.sqrt(fresh.prediction)+(1-w)*np.sqrt(b20.prediction))**2
  x['annual_rate']=x.prediction/x['e_cost_mix_1.0'];x['unit_deviance']=m.unit_deviance(x.T0,x.prediction)
  bound=w*fresh.unit_deviance+(1-w)*b20.unit_deviance
  assert np.all(x.unit_deviance<=bound+1e-7)
  assert np.isclose(x.unit_deviance.sum(),len(x)*mean_tweedie_deviance(x.T0,x.prediction,power=1.5),rtol=1e-12)
  variants.append(x);jensen.append({'model_id':mid,'per_row_Jensen':True,'metric_other_method':True})
 new=pd.concat(variants,ignore_index=True);new.to_parquet(OUT/'new_oof_2023.parquet',index=False)
 report=evaluate(old,new,['W2-COD-R35','W2-COD-R36','W2-COD-R37'],7)
 report.update(id=plan['id'],utc=now(),author='Codex',source_fits=2,target_building_adapter_fits=5,other_lines_exact_R32=True,
   construction_transport_removed=True,jensen_checks=jensen,source_observation_limit='observed source target + nominal exposure, not independently identified ultimate')
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report)
 dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]})
 print(json.dumps({'summaries':report['summaries'],'gates':report['gates'],'pairs':report['pairs']}),flush=True)


if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('action',choices=['prepare','run']);args=a.parse_args()
 if args.action=='prepare':prepare()
 else:run()
