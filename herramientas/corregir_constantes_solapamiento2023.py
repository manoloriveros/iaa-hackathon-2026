"""Corregir solo la estandarización de columnas constantes, sin releer datos."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,math
R=Path('C:/dev/Hakaton/Hackaton/Repositorio_IAA2026');BASE=R/'privado/semana2/robustez2023/mision017_20261025_v1';p=BASE/'numeric_overlap2023.json';out=BASE/'numeric_overlap2023_v3.json';assert not out.exists();report=json.loads(p.read_text(encoding='utf-8'))
def shifted(a,b):
 a=dict(a);b=dict(b)
 for q in [a,b]:
  if q['minimum']==q['maximum']:q['weighted_mean']=q['minimum'];q['weighted_sd']=0.
 den=math.sqrt((a['weighted_sd']**2+b['weighted_sd']**2)/2)
 if den==0:return a,b,0. if a['weighted_mean']==b['weighted_mean'] else None
 return a,b,(b['weighted_mean']-a['weighted_mean'])/den
toy={'minimum':5.,'maximum':5.,'weighted_mean':5.+1e-14,'weighted_sd':1e-14};assert shifted(toy,dict(toy,weighted_mean=5.-1e-14))[2]==0.
assert shifted(toy,dict(toy,minimum=6.,maximum=6.))[2] is None
assert shifted(dict(toy,minimum=0.,maximum=2.,weighted_mean=1.,weighted_sd=1.),dict(toy,minimum=1.,maximum=3.,weighted_mean=2.,weighted_sd=1.))[2]==1.
corrected=[]
for row in report['findings']:
 a,b,v=shifted(row['source'],row['target'])
 if v!=row['standardized_mean_shift']:corrected.append({'line':row['line'],'column':row['column']})
 row.update(source=a,target=b,standardized_mean_shift=v)
report.update(utc=datetime.now(timezone.utc).isoformat(),reader_version=3,correction='Previous standardizedmean of identical constant compulsoryexcess columns was floatingpointnoise divided by nearzerosd. Set trulyconstant moments exactly,no source/target/model change.',corrected_columns=corrected,corrected_previous_receipt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),correction_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),constant_controls_passed=True,new_data_reads=0)
with out.open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
rows=sorted([x for x in report['findings'] if x['standardized_mean_shift'] is not None],key=lambda x:-abs(x['standardized_mean_shift']))
print(json.dumps({'corrected_columns':corrected,'largest_real_shifts':[{'line':x['line'],'column':x['column'],'standardized_mean_shift':x['standardized_mean_shift']} for x in rows[:8]],'target_numeric_values_outside_source_ranges_total':sum(x['target_finite_rows_outside_source_range'] for x in rows),'new_fits':0,'new_data_reads':0}))
