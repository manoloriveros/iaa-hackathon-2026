"""Enlace de atributos contractuales omitidos; no usa resultados para elegir valores."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/contrato_faltante2023_v1';SRC=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import pandas as pd
KEY=['market','line','row_id'];COLS={'motor':['make_model'],'buildings':['mortgage'],'contents':['works_from_home','lodgers']};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
assert not OUT.exists();OUT.mkdir(parents=True);paths=[Path(__file__)];checks=[];levels={}
contract=R/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/availability_contract.json';paths.append(contract);roles=json.loads(contract.read_text(encoding='utf-8-sig'))['source_fields']
for line,cols in COLS.items():
 for c in cols:assert next(x['role'] for x in roles if x['table']=='policies_'+line and x['column']==c)=='F0_contractual'
 for market,folder in [('developed',ROOT/'Hackaton/Semana 1/Datos'),('emerging',ROOT/'Hackaton/Semana 2/Datos/emerging')]:
  p=folder/f'policies_{line}.parquet';paths.append(p);f=pq.read_table(p,columns=['row_id','period_start','period_end']+cols,filters=[('period_start','>=',datetime(2023,1,1)),('period_start','<',datetime(2024,1,1))]).to_pandas();assert f.row_id.is_unique and pd.to_datetime(f.period_end).dt.year.eq(2023).all() and not f[cols].isna().any().any();f['market']=market;f['line']=line;f=f.rename(columns={c:'x_'+c for c in cols});extra=f[KEY+['x_'+c for c in cols]]
  if market=='developed':
   p=SRC/f'{line}_2023.parquet';paths.append(p);original=pq.read_table(p,filters=[('year','=',2023)]).to_pandas();joined=original.merge(extra,on=KEY,validate='one_to_one',how='left');assert len(joined)==len(original)
   a=original.sort_values(KEY).reset_index(drop=True);b=joined.sort_values(KEY).reset_index(drop=True)
   for c in original:assert a[c].equals(b[c])
   assert not joined[['x_'+c for c in cols]].isna().any().any();joined.to_parquet(OUT/f'{line}_2023.parquet',index=False)
  else:
   p=BASE/f'{line}_fold0.parquet';paths.append(p);ids=pq.read_table(p,columns=KEY,filters=[('year','=',2023)]).to_pandas();assert ids.merge(extra,on=KEY,validate='one_to_one').shape[0]==len(ids)==len(extra);extra.to_parquet(OUT/f'{line}_emerging_extra.parquet',index=False)
  levels[market+'_'+line]={c:set(extra['x_'+c].astype(str)) for c in cols};checks.append({'line':line,'market':market,'rows':len(extra),'F0_contractual_only':True,'all_keys_exact':True,'missing':0})
assert levels['developed_motor']['make_model']==levels['emerging_motor']['make_model']
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'motor_make_codes_shared':len(levels['developed_motor']['make_model']),'source_target_ID_records_never_joined':True,'same_column_definition_not_proof_of_same_risk_effect':True,'price_labels_unchanged':True,'new_fits':0,'2024_rows_read':0,'sources':[{'path':rel(p),'sha256':sha(p)} for p in dict.fromkeys(paths)],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
with (OUT/'report.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['sources','outputs']}))
