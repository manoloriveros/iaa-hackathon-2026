"""Genera y verifica continuación material de lector, conservando tres fits fuente."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/ciclo10_20261025_v1'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_basicas_fuente2023_v2 as m
import pyarrow.parquet as pq
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
original=R/'herramientas/robustez2023_ciclo10.py';new=R/'herramientas/robustez2023_ciclo10_v2.py'
assert not new.exists();text=original.read_text(encoding='utf-8')
text=text.replace('modelo_basicas_fuente2023 as m','modelo_basicas_fuente2023_v2 as m')
text=text.replace("assert (OUT/'forum_prior_receipt.json').exists() and not (OUT/'started.json').exists();dump(OUT/'started.json',{'utc':now(),'pid':os.getpid()})","assert (OUT/'forum_correction_receipt.json').exists() and (OUT/'started.json').exists() and not (OUT/'continuation_started.json').exists();correction=read(OUT/'continuation_plan.json');check(correction);dump(OUT/'continuation_started.json',{'utc':now(),'pid':os.getpid()})")
old="""   event('source_fit_started',line=line,model_id=recipe['id'])
   with threadpool_limits(limits=2):t,rec=m.fit_source(source,line,recipe['kind'],parent=teachers.get('W2-COD-R42'))
   path=OUT/f'teachers/{recipe["id"]}_{line}.joblib';path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);teachers[recipe['id']]=t;rec['model_id']=recipe['id'];receipts.append(rec);dump(path.with_suffix('.json'),rec);event('source_fit_complete',line=line,model_id=recipe['id'],completed=len(receipts))"""
repl="""   path=OUT/f'teachers/{recipe["id"]}_{line}.joblib'
   if line=='motor':
    t=joblib.load(path);rec=read(path.with_suffix('.json'));event('accepted_source_reused_without_fit',line=line,model_id=recipe['id'])
   else:
    event('source_fit_started',line=line,model_id=recipe['id'])
    with threadpool_limits(limits=2):t,rec=m.fit_source(source,line,recipe['kind'],parent=teachers.get('W2-COD-R42'))
    path.parent.mkdir(exist_ok=True);joblib.dump(t,path,compress=3);rec['model_id']=recipe['id'];dump(path.with_suffix('.json'),rec);event('source_fit_complete',line=line,model_id=recipe['id'])
   teachers[recipe['id']]=t;receipts.append(rec)"""
assert old in text;text=text.replace(old,repl)
text=text.replace("report.update(id=plan['id']","report.update(reused_price_fits=3,new_fits_in_continuation=51,reader_correction_only=True,id=plan['id']")
text=text.replace(" check(plan);dump(OUT/'training_receipts.json'"," check(plan);check(correction);dump(OUT/'training_receipts.json'")
with new.open('x',encoding='utf-8') as f:f.write(text)
checks=[]
for line in m.FEATURES:
 extra=pq.read_table(R/f'privado/semana2/robustez2023/covariables_basicas2023_v1/emerging_{line}.parquet').to_pandas()
 for k in range(5):
  frame=pq.read_table(R/f'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023/{line}_fold{k}.parquet').to_pandas();joined=m.attach(frame,extra);assert frame.equals(joined[frame.columns]);checks.append({'line':line,'fold':k,'original_values_exact':True})
 if line=='motor':
  bad=extra.copy();bad.loc[0,'x_urban_density']='wrong'
  try:m.attach(frame,bad)
  except AssertionError:pass
  else:raise AssertionError('Valor distinto admitido')
paths=[new,Path(m.__file__),Path(__file__)]+list((OUT/'teachers').glob('*'))
plan={'id':'S2-ROBUSTEZ2023-CICLO10-LECTOR-v2','author':'Codex','original_plan_unchanged':True,'failure':'join control rejects already-existing physical columns; three valid source fits saved, no target fits attempted',
 'change':'validate exact existing values by key, preserve them; reject divergent duplicates; no change to features/objective/config/criteria',
 'accepted_fits_reused_without_retraining':3,'remaining_fits':51,'total_cycle_fits':54,'C0_fits':0,'2024_closed':True,'checks':checks,'synthetic_divergence_rejected':True,
 'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
with (OUT/'continuation_plan.json').open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2)
print(json.dumps({'three_fits_preserved':True,'unchanged_frames_checked':15,'remaining_fits':51}))
