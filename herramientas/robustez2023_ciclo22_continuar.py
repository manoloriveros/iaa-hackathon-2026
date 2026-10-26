"""Continuación sin repetir los 31 ajustes guardados; enlace2023 preserva originales."""
from pathlib import Path
import robustez2023_ciclo22 as c
import argparse,json,os
import pandas as pd,numpy as np,pyarrow.parquet as pq,joblib
from threadpoolctl import threadpool_limits
m=c.m;OUT=c.OUT;ROOT=c.ROOT;R=c.R

def attach_preserving(frame,extra):
 assert not frame.duplicated(m.KEY).any() and not extra.duplicated(m.KEY).any()
 order=frame[m.KEY].merge(extra,on=m.KEY,validate='one_to_one',how='left',indicator=True);assert order['_merge'].eq('both').all() and len(order)==len(frame)
 for col in extra:
  if col in m.KEY or col not in frame:continue
  a=frame[col].reset_index(drop=True);b=order[col];assert (a.eq(b)|(a.isna()&b.isna())).all(),col
 missing=[v for v in extra if v not in frame]
 out=frame.copy()
 for col in missing:out[col]=order[col].to_numpy()
 for col in frame:assert out[col].equals(frame[col]),col
 return out

def prepare():
 assert not (OUT/'continuation_plan.json').exists()
 # This tests the changed real join path, with no price estimator fitting.
 f=pd.DataFrame({'market':['emerging']*2,'line':['motor']*2,'row_id':['s1','s2'],'T0':[0.,123.],'x_flag':[0.,1.]});extra=f[m.KEY+['x_flag']].iloc[::-1].copy();extra['x_flag']=extra.x_flag.astype(bool)
 assert attach_preserving(f,extra).equals(f)
 for bad in [extra.iloc[:-1],pd.concat([extra,extra.iloc[:1]]),extra.assign(x_flag=False)]:
  try:attach_preserving(f,bad)
  except AssertionError:pass
  else:raise AssertionError('Unión alterada admitida')
 audit=c.read(OUT/'join_overlap_audit.json');assert all(x['all_overlaps_value_identical'] for x in audit['checks'])
 paths=[Path(__file__),OUT/'join_overlap_audit.json']+list((OUT/'pilot_models').glob('*'))+list((OUT/'pilot_metrics').glob('*'))+list((OUT/'teachers').glob('*'))+[OUT/'source_veto.json']
 plan={'id':'C22-CONTINUACION-ENLACE2023-v2','utc':c.now(),'author':'Codex','change':'only join guard;verify identical overlaps and retain all original columns/values/dtypes,addonlymissing;pricingrecipe unchanged','completed_fits_reused_without_refit':31,'new_fits_in_preparation':0,'tests':{'bool_vs_numeric_semantic_equality':True,'all_original_columns_bytevalue_and_dtype_retained':True,'missing_duplicate_and_changed_rejected':True},'sources':[{'path':c.rel(p),'sha256':c.sha(p)} for p in paths]}
 c.dump(OUT/'continuation_plan.json',plan);print(json.dumps({k:v for k,v in plan.items() if k!='sources'}))

def run():
 plan=c.read(c.PLAN);correction=c.read(OUT/'continuation_plan.json');c.check(plan);c.check(correction);assert (OUT/'forum_correction_receipt.json').exists() and not (OUT/'continuation_started.json').exists();c.dump(OUT/'continuation_started.json',{'utc':c.now(),'pid':os.getpid()})
 receipts=[c.read(p) for p in (OUT/'pilot_models').glob('*.json')];assert len(receipts)==30
 source_gate=c.read(OUT/'source_veto.json');eligible=source_gate['eligible'];assert eligible==['W2-COD-R82']
 old=pq.read_table(c.OLD,filters=[('year','=',2023),('model_id','in',['W2-B00','W2-B20'])]).to_pandas();inc=pq.read_table(c.REF,filters=[('year','=',2023),('model_id','=','W2-COD-R36')]).to_pandas();outputs=[]
 for line in m.FEATURES:
  source=c.load_source(line);teachers={}
  for recipe in plan['models']:
   if recipe['id'] not in eligible and recipe['kind']=='trees':continue
   path=OUT/f'teachers/{recipe["id"]}_{line}.joblib'
   if path.exists():
    t=joblib.load(path);rec=c.read(path.with_suffix('.json'));c.event('source_reused_without_fit',line=line,model_id=recipe['id'])
   else:
    c.event('source_full_started',line=line,model_id=recipe['id'])
    with threadpool_limits(limits=2):t,rec=m.fit_source(source,line,recipe['kind'],parent=teachers.get('glm'))
    rec.update(role='source_full',model_id=recipe['id']);path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);c.dump(path.with_suffix('.json'),rec);c.event('source_full_complete',line=line,model_id=recipe['id'])
   teachers[recipe['kind']]=t;receipts.append(rec)
  extra=pq.read_table(c.EXTRA/f'{line}_emerging_extra.parquet').to_pandas()
  for fold in range(5):
   f=attach_preserving(pq.read_table(c.BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas(),extra);fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)
   for key in ['group_id','customer_id','address_id']:assert set(fit[key]).isdisjoint(val[key])
   ref=inc[inc.line.eq(line)&inc.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);b20=old[old.model_id.eq('W2-B20')&old.line.eq(line)&old.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True);assert val[m.KEY].equals(ref[m.KEY]) and ref[m.KEY].equals(b20[m.KEY])
   for col in ['T0','fold','group_id','exposure','e_cost_mix_1.0']:assert np.array_equal(val[col].to_numpy(),ref[col].to_numpy())
   for recipe in plan['models']:
    if recipe['id'] not in eligible:continue
    c.event('target_fit_started',line=line,fold=fold,model_id=recipe['id'])
    with threadpool_limits(limits=2):b,rec=m.fit(fit,line,fold,teachers[recipe['kind']],recipe['id']);rate=m.predict(b,val)
    path=OUT/f'models/{recipe["id"]}_{line}_fold{fold}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(b,path,compress=3)
    with threadpool_limits(limits=2):assert np.array_equal(rate,m.predict(joblib.load(path),val))
    rec.update(role='target',replay_exact=True);receipts.append(rec);c.dump(path.with_suffix('.json'),rec);row=ref.copy();row['model_id']=recipe['id'];row['unpooled_prediction']=rate*val['e_cost_mix_1.0'].to_numpy();row['prediction']=(.5*np.sqrt(row.unpooled_prediction)+.5*np.sqrt(b20.prediction))**2;row['annual_rate']=row.prediction/row['e_cost_mix_1.0'];row['unit_deviance']=m.unit_deviance(row.T0,row.prediction);outputs.append(row)
    pure=row.copy();pure['model_id']=c.NATURAL[recipe['id']];pure['prediction']=pure.unpooled_prediction;pure['annual_rate']=pure.prediction/pure['e_cost_mix_1.0'];pure['unit_deviance']=m.unit_deviance(pure.T0,pure.prediction);outputs.append(pure);c.event('target_fit_complete',line=line,fold=fold,model_id=recipe['id'])
 new=pd.concat(outputs,ignore_index=True);assert len(new)==2*50094;new.to_parquet(OUT/'new_oof_2023.parquet',index=False);ids=['W2-COD-R82','W2-COD-R84'];report=c.evaluate(pd.concat([old,inc],ignore_index=True),new,ids,len(receipts),reference_id='W2-COD-R36');report.update(id=plan['id'],utc=c.now(),author='Codex',primary_reference='W2-COD-R36',source_gate=source_gate['summaries'],source_eligible=eligible,source_fits_reused_without_refitting=31,new_fits_in_continuation=17,join_only_correction=True,selected_exploratory_variant=next((x['model_id'] for x in report['gates'] if x['all_pass']),None),promotion=False)
 c.check(plan);c.check(correction);c.dump(OUT/'training_receipts.json',receipts);c.dump(OUT/'report.json',report);c.dump(OUT/'manifest.json',{'files':[{'path':c.rel(p),'sha256':c.sha(p)} for p in OUT.rglob('*') if p.is_file()]});c.event('complete',new_price_fits=report['new_price_fits'],gates=report['gates'],selected=report['selected_exploratory_variant'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else run()
