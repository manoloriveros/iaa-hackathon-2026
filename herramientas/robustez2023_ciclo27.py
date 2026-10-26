"""Corrección regional parcialmente compartida entre dos coberturas de hogar."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_region_hogar2023 as m
from semana2.desplegar_robustez2023 import TEACHERS
from semana2.evaluar_robustez2023_v2 import evaluate
from sklearn.dummy import DummyRegressor
from sklearn.preprocessing import FunctionTransformer
import numpy as np,pandas as pd,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
OUT=R/'privado/semana2/robustez2023/ciclo27_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo27_plan.json';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';REF=R/'privado/semana2/robustez2023/ciclo7_20261025_v1/new_oof_2023.parquet';OLD=R/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet'
RECIPES=[{'id':'W2-COD-R102','tau':20.},{'id':'W2-COD-R103','tau':200.}];NATURAL={'W2-COD-R102':'W2-COD-R104','W2-COD-R103':'W2-COD-R105'}
now=lambda:datetime.now(timezone.utc).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def oldpath(line,fold):return R/f'privado/semana2/robustez2023/{"ciclo7_20261025_v1" if line=="buildings" else "ciclo6_20261025_v1"}/models/{"W2-COD-R35" if line=="buildings" else "W2-COD-R32"}_{line}_fold{fold}.joblib'
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))
def check(plan):
 for s in plan['sources']:assert sha(ROOT/s['path'])==s['sha256'],s['path']
def event(name,**kw):
 obj={'utc':now(),'event':name,**kw}
 with (OUT/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(obj)+'\n')
 print(json.dumps(obj),flush=True)
def synthetic():
 rng=np.random.default_rng(2026102527);frames=[];teachers={};old_models={};receipts=[]
 for line in m.HOMES:
  n=600;f=pd.DataFrame({'market':'emerging','line':line,'row_id':['s'+line+str(i) for i in range(n)],'year':2023,'is_test':False,'fold':np.arange(n)%5,'exposure':rng.uniform(.3,1,n)})
  for c in m.core.FEATURES[line]['numeric']:f[c]=rng.uniform(0,5,n)
  for c in m.core.FEATURES[line]['categorical']:f[c]=np.where(np.arange(n)%2,'A','B')
  f['x_new_business']=(np.arange(n)%2).astype(float);f['e_cost_mix_1.0']=.98*f.exposure;f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)
  est=DummyRegressor(strategy='constant',constant=100. if line=='buildings' else 30.);est.fit(np.zeros((2,1)),[1.,1.]);teachers[line]={'line':line,'family':'SourceGLM','columns':['x_new_business'],'transformer':FunctionTransformer(),'estimator':est}
  with threadpool_limits(limits=2):b,rec=m.core.fit(f[f.fold.ne(0)],line,0,{'id':'SYN','synthetic':True,'_teacher':teachers[line]})
  old_models[line]=b;frames.append(f)
 f=pd.concat(frames,ignore_index=True);fit=f[f.fold.ne(0)];val=f[f.fold.eq(0)]
 with threadpool_limits(limits=2):control,note=m.control(fit,teachers,old_models,0)
 p=m.predict(control,val)
 for line in m.HOMES:
  chosen=val.line.eq(line).to_numpy();assert np.allclose(p[chosen],m.core.predict(old_models[line],val.loc[chosen]),rtol=1e-12,atol=1e-12)
 for recipe in RECIPES:
  with threadpool_limits(limits=2):b,rec=m.fit(fit,teachers,0,recipe);pred=m.predict(b,val)
  assert np.array_equal(pred,m.predict(b,val.assign(T0=1e15)));receipts.append(rec)
  for bad in [val.assign(year=2024),val.assign(market='developed')]:
   try:m.predict(b,bad)
   except AssertionError:pass
   else:raise AssertionError('Ámbito prohibido admitido')
 dump(OUT/'synthetic.json',{'synthetic_price_fits':6,'dummy_source_fits':2,'independent_baseline_adapter_fits':2,'joint_adapter_fits':2,'tau2_no_newfit_control':note,'prediction_matches_independent_baseline':True,'held_label_poison_invariant':True,'closed2024_wrongmarket_rejected':True,'receipts':receipts})
def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True);synthetic()
 paths=[Path(__file__),Path(m.__file__),R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/desplegar_robustez2023.py',R/'src/semana2/evaluar_robustez2023_v2.py',REF,OLD,R/'privado/semana2/robustez2023/mision017_20261025_v1/calibration_coefficient_audit.json']+[TEACHERS[line] for line in m.HOMES]+[oldpath(line,k) for line in m.HOMES for k in range(5)]+[BASE/f'{line}_fold{k}.parquet' for line in m.HOMES for k in range(5)]
 plan={'id':'S2-ROBUSTEZ2023-CICLO27-v1-20261025','author':'Codex','utc':now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ27-PREVIO','models':RECIPES,'home_natural_outputs':NATURAL,'hypothesis':'Noisy independent home region adjustments may be stabilized by partialsharing across buildings/contents of same geography. Perils can differ,so contrast remains estimable;not assumption of identicalrisk or independent cover observations.',
 'offset':'unchanged frozen physical teachers supportingR36,NOTcycle26maskedteachers;0sourcefits',
 'design':'same14parameters as two7parameterGLMs:lineintercepts2free,lineNB2ridge1,regioncommon5ridge2,regioncontrast5ridge tau20or200;beta_build=common+contrast,beta_contents=common-contrast',
 'objective':'sum of perline sqrt(e_cost) normalized halfTweedie1.5loss plus ridge;atcontrasttau2 exactly two existing GLMs,verifiedfromstoredcoefficientswithoutrefit. Newtau20and200 are10xand100xcontrastshrinkage only.',
 'control_required':'mappedtau2 coefficients must match original independent objectives/gradients and heldOOF predictions beforeanyfit perouterfold;commonencnames andembeddedsourcehashes identical',
 'scope':'five saved2023connectedcomponentfolds jointlyacrosshome lines;allgroups/customer/addressdisjoint;T0/exposure/existingC0 unchanged;motor entireOOF heldexactR36 withno newpriceprediction',
 'outputs':{'pooled_home':[x['id'] for x in RECIPES],'home_only_natural':NATURAL,'motor':'exactR36 for all4outputs','fixed_pool':'home sqrt50/50withB20,no learnedweights'},
 'real_fit_budget':10,'source_fit_budget':0,'new_C0_fits':0,'primary_reference':'W2-COD-R36','criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'preference_order':[x['id'] for x in RECIPES]+list(NATURAL.values()),'promotion':False,'2024_closed':True,'B00_preserved':True,'adaptive_exploratory':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 dump(PLAN,plan);dump(OUT/'plan.json',plan);print(json.dumps({'plan':rel(PLAN),'synthetic_fits':6,'real_joint_fits':10,'newsource':0,'newC0':0}))
def run():
 plan=read(PLAN);check(plan);assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()});teachers={line:joblib.load(TEACHERS[line]) for line in m.HOMES};receipts=[];controls=[];outputs=[]
 inc=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();purebase=pq.read_table(REF,filters=[('year','=',2023),('model_id','=','W2-COD-R35'),('line','in',m.HOMES)]).to_pandas();original=pq.read_table(OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas()
 for fold in range(5):
  f=pd.concat([pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas() for line in m.HOMES],ignore_index=True);fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
  for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
  assert f.groupby('group_id').fold.nunique().le(1).all();old_models={line:joblib.load(oldpath(line,fold)) for line in m.HOMES}
  with threadpool_limits(limits=2):control,note=m.control(fit,teachers,old_models,fold);controlrate=m.predict(control,val)
  ref=inc[inc.line.isin(m.HOMES)&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=original[original.model_id.eq('W2-B20')&original.line.isin(m.HOMES)&original.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);base=purebase[purebase.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY]) and ref[m.KEY].equals(base[m.KEY]);assert np.allclose(controlrate,base.annual_rate,rtol=1e-12,atol=1e-12)
  for col in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[col].to_numpy(),ref[col].to_numpy())
  controlcost=(.5*np.sqrt(controlrate*val['e_cost_mix_1.0'])+.5*np.sqrt(b20.prediction))**2;assert np.allclose(controlcost,ref.prediction,rtol=1e-12,atol=1e-12);note.update(held_OOF_matches=True,held_max_relative_error=float(np.max(np.abs(controlrate/base.annual_rate-1))),pooled_incumbent_matches=True);controls.append(note);dump(OUT/f'controls/fold{fold}.json',note);event('unchanged_coordinate_control_passed',fold=fold,**{k:v for k,v in note.items() if k!='held_fold'})
  for recipe in RECIPES:
   event('joint_fit_started',fold=fold,model_id=recipe['id'])
   with threadpool_limits(limits=2):b,rec=m.fit(fit,teachers,fold,recipe);rate=m.predict(b,val)
   path=OUT/f'models/{recipe["id"]}_home_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
   with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
   rec['replay_exact']=True;receipts.append(rec);dump(path.with_suffix('.json'),rec);row=ref.copy();row['model_id']=recipe['id'];row['home_unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.home_unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row);natural=row.copy();natural['model_id']=NATURAL[recipe['id']];natural['prediction']=natural.home_unpooled_prediction;natural['annual_rate']=natural.prediction/natural['e_cost_mix_1.0'];natural['unit_deviance']=m.unit_deviance(natural.T0,natural.prediction);outputs.append(natural);event('joint_fit_complete',fold=fold,model_id=recipe['id'])
 for mid in plan['preference_order']:
  motor=inc[inc.line.eq('motor')].copy();motor['model_id']=mid;outputs.append(motor)
 new=pd.concat(outputs,ignore_index=True);assert len(new)==4*50094 and not new.duplicated(['model_id']+m.KEY).any();new.to_parquet(OUT/'new_oof_2023.parquet',index=False);report=evaluate(pd.concat([original,inc],ignore_index=True),new,plan['preference_order'],len(receipts),reference_id='W2-COD-R36');report.update(id=plan['id'],author='Codex',utc=now(),primary_reference='W2-COD-R36',unchanged_coordinate_controls=controls,motor_exact_incumbent_no_new_inference=True,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False)
 check(plan);dump(OUT/'training_receipts.json',receipts);dump(OUT/'report.json',report);dump(OUT/'manifest.json',{'files':[{'path':rel(p),'sha256':sha(p)} for p in OUT.rglob('*') if p.is_file()]});event('complete',new_price_fits=len(receipts),gates=report['gates'],selected=report['selected_exploratory_variant'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
