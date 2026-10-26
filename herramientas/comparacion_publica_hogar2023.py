"""Dos salidas de investigación congeladas; no promoción ni sustitución de las cribas."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_region_hogar2023 as m
from semana2.desplegar_robustez2023 import TEACHERS
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OLD=R/'privado/semana2/robustez2023/entrega_20261025_v1';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1';PLAN=R/'registro/semana2_comparacion_publica_hogar_plan_v1.json';BASELINE=R/'privado/semana2/modelo_final_g4_2023/final_20261024_v1/attempt1/submission_g4_glm_2023_2025.csv';INCUMBENT=OLD/'submission_R36_transfer50_GLM50_2025.csv';SAMPLE=R/'privado/semana2/envios/g4_20261025_v1/official_sample_format.csv';REPORT=R/'privado/semana2/robustez2023/ciclo27_20261025_v1/report.json'
VARIANTS=[{'model_id':'W2-COD-R104-HOME-RESEARCH','home_weight':1.,'filename':'submission_home27_natural_motorR36_2025.csv'},{'model_id':'W2-COD-R102-HOME-RESEARCH','home_weight':.5,'filename':'submission_home27_pool50_motorR36_2025.csv'}]
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']
def csv(p):return pd.read_csv(p,dtype=str)
def compose(inc,base,quotes,costs,variants=VARIANTS):
 assert list(inc)==['row_id','prediction'] and list(base)==list(inc) and inc.row_id.is_unique and inc.row_id.equals(base.row_id)
 assert set(quotes)=={'motor','buildings','contents'};allids=[]
 for line,q in quotes.items():
  assert q.row_id.is_unique;allids.extend(q.row_id.tolist())
 assert len(set(allids))==len(allids)==len(inc) and set(allids)==set(inc.row_id)
 basecost=pd.Series(base.prediction.astype(float).to_numpy(),index=base.row_id);outputs={};motor=set(quotes['motor'].row_id)
 for spec in variants:
  out=inc.copy();replacement={}
  for line in m.HOMES:
   q=quotes[line];p=np.asarray(costs[line],float);assert p.shape==(len(q),) and np.isfinite(p).all() and (p>0).all();w=spec['home_weight'];b=basecost.loc[q.row_id].to_numpy();values=p if w==1 else (w*np.sqrt(p)+(1-w)*np.sqrt(b))**2;replacement.update(zip(q.row_id,[repr(float(v)) for v in values]))
  use=out.row_id.isin(replacement);out.loc[use,'prediction']=out.loc[use,'row_id'].map(replacement);assert out.loc[out.row_id.isin(motor),'prediction'].equals(inc.loc[inc.row_id.isin(motor),'prediction']);values=out.prediction.astype(float).to_numpy();assert np.isfinite(values).all() and (values>0).all();outputs[spec['model_id']]=out
 return outputs
def synthetic():
 inc=pd.DataFrame({'row_id':['c1','m1','b1'],'prediction':['3.0000','4.0000000000000001','9.00000']});base=inc.copy();q={line:pd.DataFrame({'row_id':[ident]}) for line,ident in [('motor','m1'),('buildings','b1'),('contents','c1')]};cost={'buildings':np.array([20.]),'contents':np.array([6.])};out=compose(inc,base,q,cost);assert out[VARIANTS[0]['model_id']].prediction.tolist()==['6.0','4.0000000000000001','20.0']
 expected=((np.sqrt(20)+np.sqrt(9))/2)**2;assert abs(float(out[VARIANTS[1]['model_id']].prediction.iloc[2])-expected)<1e-14
 for bad in [dict(cost,buildings=np.array([-1.])),dict(cost,buildings=np.array([np.nan]))]:
  try:compose(inc,base,q,bad)
  except AssertionError:pass
  else:raise AssertionError('Precio inválido admitido')
 try:compose(inc,base,dict(q,contents=pd.DataFrame({'row_id':['bad']})),cost)
 except AssertionError:pass
 else:raise AssertionError('ID ajeno admitido')
 dump(OUT/'synthetic_csv.json',{'cost_pool_formula_independent':True,'allIDs_once_originalorder':True,'motor_decimal_strings_preserved_exact':True,'negative_NaN_unknownID_rejected':True,'new_price_fits':0})
def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic();report=read(REPORT);gates=[x for x in report['gates'] if x['model_id'] in ['W2-COD-R102','W2-COD-R104']];assert len(gates)==2 and not any(x['all_pass'] for x in gates)
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/desplegar_robustez2023.py',REPORT,R/'registro/semana2_robustez2023_ciclo27_plan.json',BASELINE,INCUMBENT,SAMPLE]+[TEACHERS[line] for line in m.HOMES]+[OLD/'training'/f'{line}_2023.parquet' for line in m.HOMES]+[OLD/'quotes'/f'{line}_2025.parquet' for line in ['motor']+m.HOMES]
 assert sha(SAMPLE)=='0a4496eb14d6450bb4583b2e90ae31fde95d71c1629656a03d54ffd1515f666c'
 plan={'id':'S2-COMPARACION-PUBLICA-HOGAR-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-HOGAR-PUBLICO-PREVIO','purpose':'Research-only prospective publicbenchmark of the SAME fixed C27tau20 model under its two preexisting home outputs;measure whether householdregionalpartialpooling transfers to2025 brokerportfolio;not hidden-label probing,publicweight tuning or formalpromotion.',
 'authorization':'User explicitly authorized own KaggleCSVsubmission and autonomous necessary decisions without furtherquestions;operational research exception retains common selectionpolicy and all failedgates.',
 'variants':VARIANTS,'fit_recipe':{'model_id':'HOME27-RESEARCH-FINAL','tau':20.,'source':'unchanged frozen physical source2023teachers fromR36','target':'all28414home2023periods,existing finalscopeC0/exposure/T0','new_joint_price_fits':1,'newsourcefits':0,'newC0fits':0},
 'scope':'train2023only;readfrozen2025quotesafterfit;motor all90521predictionstrings exactlyincumbentR36;official209063IDs/order','selection_status':'NO candidatepassed all2023gates;doNOTpromote,retire,reopen2024orlabelrobustbypublicscore','unresolved_2023_gates':gates,
 'public_protocol':'atmost2submissions,priority R104natural then R102fixed50pool;choose availableprefixbeforeanynewpublicscore;freeze allCSVhashes thenpost selectedbatch beforecheckingnewpublicscores;no reweightingorretrainfromthose scores;ownCOMPLETEreceipts only,private/foreignscoresnotread;no manualfinalselection',
 'success_interpretation':'A processedpublicscore>=.17 proves onlypublicsubgoal;fullgoalremainsunproven while robustlocalevidence missing. ExistingB00/alternatives/referenceandgates unchanged.',
 'validation':'source/inputhashes;fullperiod2023/quote2025roles;sampleIDorder;positivefinite209063;fullindependenthomeformula;nominallevelattribution;exactmotorstrings;separateprocess replaywithallfits/optimizerblocked;skilldryrunbeforePOST',
 'B00_preserved':True,'2024_closed':True,'promotion':False,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'newpricefits_budget':1,'newsource':0,'newC0':0,'research_only_not_approved_model':True}))
def load_quotes():
 result={}
 for line in ['motor']+m.HOMES:
  q=pq.read_table(OLD/'quotes'/f'{line}_2025.parquet',filters=[('year','=',2025)]).to_pandas();assert q.market.eq('emerging').all() and q.line.eq(line).all() and q.year.eq(2025).all() and q.is_test.eq(True).all() and q.row_id.is_unique and pd.to_datetime(q.period_start).dt.year.eq(2025).all() and pd.to_datetime(q.period_end).dt.year.eq(2025).all();result[line]=q
 return result
def forecast(bundle,quotes):
 costs={};checks=[]
 for j,line in enumerate(m.HOMES):
  f=quotes[line]
  with threadpool_limits(limits=2):rate=m.predict(bundle,f,training=False);source=m.core.teacher_rate(bundle['teachers'][line],f)
  r=bundle['region_encoder'].transform(f[['x_region']]).toarray();k=r.shape[1];beta=bundle['coef'];common=beta[2:2+k];contrast=beta[2+k:2+2*k];sign=1 if line=='buildings' else -1;independent=source*np.exp(f.x_new_business.to_numpy(float)*beta[j]+r@(common+sign*contrast)+beta[-2+j]);assert np.allclose(rate,independent,rtol=1e-12,atol=1e-12);costs[line]=rate*f.exposure.to_numpy(float);checks.append({'line':line,'rows':len(f),'independent_dense_formula_allquotes':True,'max_relative_error':float(np.max(np.abs(rate/independent-1)))})
 return costs,checks
def write_csvs(bundle,folder):
 quotes=load_quotes();costs,checks=forecast(bundle,quotes);inc=csv(INCUMBENT);base=csv(BASELINE);sample=csv(SAMPLE);assert len(inc)==209063 and list(sample)==list(inc) and sample.row_id.equals(inc.row_id);outputs=compose(inc,base,quotes,costs);specs=[];levels=[]
 for variant in VARIANTS:
  frame=outputs[variant['model_id']];path=folder/variant['filename'];assert not path.exists();frame.to_csv(path,index=False);specs.append({**variant,'path':rel(path),'sha256':sha(path),'bytes':path.stat().st_size,'rows':len(frame)})
  for line,q in quotes.items():
   ids=set(q.row_id);mask=frame.row_id.isin(ids);total=float(frame.loc[mask,'prediction'].astype(float).sum());current=float(inc.loc[mask,'prediction'].astype(float).sum());levels.append({'model_id':variant['model_id'],'line':line,'total':total,'R36_total':current,'relative_level_change':total/current-1,'change_gt5pct_requires_attribution':abs(total/current-1)>.05})
 return specs,levels,checks
def fit():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'fit_started.json').exists();dump(OUT/'fit_started.json',{'utc':now(),'pid':os.getpid()});frames=[]
 for line in m.HOMES:
  f=pq.read_table(OLD/'training'/f'{line}_2023.parquet',filters=[('year','=',2023)]).to_pandas();m.guard(f);assert f.line.eq(line).all() and pd.to_datetime(f.period_start).dt.year.eq(2023).all() and pd.to_datetime(f.period_end).dt.year.eq(2023).all();frames.append(f)
 f=pd.concat(frames,ignore_index=True);assert len(f)==28414;teachers={line:joblib.load(TEACHERS[line]) for line in m.HOMES}
 with threadpool_limits(limits=2):bundle,receipt=m.fit(f,teachers,None,plan['fit_recipe'])
 receipt.update(utc=now(),scope='final all2023home for2025 researchcomparison,notvalidation',price_estimator_fits=1);joblib.dump(bundle,OUT/'model_home2023.joblib',compress=3);dump(OUT/'training_receipt.json',receipt)
 specs,levels,checks=write_csvs(bundle,OUT);check(plan);dump(OUT/'ready.json',{'utc':now(),'CSV':specs,'level_attribution':levels,'independent_formula':checks,'model_sha256':sha(OUT/'model_home2023.joblib'),'new_price_fits':1,'newsource':0,'newC0':0,'2024_closed':True,'research_only':True,'preexisting_gates_remain_failed':True});print(json.dumps({'CSV':specs,'levels':levels,'new_price_fits':1,'formal_eligibility':False}))
def replay():
 check(read(PLAN));ready=read(OUT/'ready.json');assert sha(OUT/'model_home2023.joblib')==ready['model_sha256'];calls=[]
 def forbidden(*a,**k):calls.append('forbidden_fit');raise AssertionError('Ajuste/optimizador durante replay')
 from sklearn.linear_model import TweedieRegressor,PoissonRegressor,GammaRegressor
 import lightgbm as lgb,scipy.optimize
 for cls in [TweedieRegressor,PoissonRegressor,GammaRegressor,lgb.LGBMRegressor]:cls.fit=forbidden
 scipy.optimize.minimize=forbidden;m.fit=forbidden;folder=OUT/'separate_replay';assert not folder.exists();folder.mkdir();bundle=joblib.load(OUT/'model_home2023.joblib');specs,levels,checks=write_csvs(bundle,folder)
 for a,b in zip(ready['CSV'],specs):assert a['model_id']==b['model_id'] and a['sha256']==b['sha256']
 assert not calls;dump(OUT/'separate_process_replay.json',{'utc':now(),'success':True,'all209063rows_bothCSVs_bitexact':True,'motor_all90521strings_exact_R36':True,'all_fits_optimizer_blocked':True,'forbidden_calls':0,'new_C0':0,'2024_rows_read':0,'independent_formula':checks,'replayed_CSV':specs});print(json.dumps({'success':True,'both_csv_hashes_exact':True,'forbidden_fit_calls':len(calls)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','fit','replay']);a=p.parse_args();{'prepare':prepare,'fit':fit,'replay':replay}[a.action]()
