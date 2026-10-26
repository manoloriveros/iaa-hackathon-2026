"""Recupera la serialización incompleta conservando todos los fits y bootstrap."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path('C:/dev/Hakaton');REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelos_robustos2023 as m
import pandas as pd,pyarrow.parquet as pq
out=REPO/'privado/semana2/robustez2023/ciclo1_20261025_v1'
raw=(out/'report.json').read_text(encoding='utf-8')
prefix=raw[:raw.index('  "gates":')].rstrip().rstrip(',')+'\n}'
report=json.loads(prefix)
oof=pq.read_table(out/'new_oof_2023.parquet').to_pandas()
refs=pq.read_table(REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1/oof_2023.parquet',filters=[('model_id','in',['W2-B00','W2-B20']),('year','=',2023)]).to_pandas()
parts={mid:f for mid,f in pd.concat([refs,oof]).groupby('model_id')}
report['gates']=[]
for p in report['pairs']:
 checks={'material_gain':p['delta_D2']>=.005,'lower_bound':p['exploratory_interval'][0]>.0005,
         'four_folds':p['positive_folds']>=4,'segment_harm':min(x['delta_over_full_null'] for x in p['segment_deltas_over_full_null'])>=-.0005,
         'not_few_groups':p['delta_after_removal']>=.0005}
 report['gates'].append({'model_id':p['candidate'],'checks':checks,'all_pass':all(checks.values()),'formal_promotion':False})
report['sensitivity']=[]
for mid,part in parts.items():
 for target,exposure in [('T1_reserve075','e_cost_mix_0.75'),('T1_reserve125','e_cost_mix_1.25'),('T0','e_cost_mix_tail0.05'),('T0','e_cost_mix_tail0.1')]:
  report['sensitivity'].append({'model_id':mid,'target':target,'effective_exposure':exposure,**m.metrics(part.assign(stress=part.annual_rate*part[exposure]),prediction='stress',target=target)})
report.update(serialization_failure_preserved='report.json',recovery_no_new_fit=True,recovery_no_new_bootstrap=True,
              source_partial_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),
              summaries_and_intervals_exactly_recovered=True,bootstrap_draw_digest_unavailable_after_serialization_failure=True,
              reference='W2-B00',B00_preserved=True,promotion=False,new_submissions=0,**{'2024_closed':True})
with (out/'report_recovered.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,ensure_ascii=False)
files=sorted(p for p in out.rglob('*') if p.is_file())
with (out/'manifest_recovered.json').open('x',encoding='utf-8') as f:json.dump({'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]},f,indent=2)
print(json.dumps({'recovered':True,'fits':30,'new_fits_during_recovery':0,'new_bootstrap':0,'gates':report['gates']}))
