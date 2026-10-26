"""Añade covariables físicas a la fuente aislada; no recalcula sus etiquetas."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';RAW=ROOT/'Hackaton/Semana 1/Datos'
SRC=R/'privado/semana2/robustez2023/fuente_desarrollado2023_v1';OUT=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.path.insert(0,str(R/'src'))
import pyarrow.parquet as pq
import pandas as pd,numpy as np
from semana2 import modelos_robustos2023 as m
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cols={
 'motor':['years_licensed','engine_size_cc','named_young_driver','driver_assist','voluntary_excess','compulsory_excess','body_type','transmission','fuel_type','overnight_parking','vehicle_use'],
 'buildings':['smoke_alarms','voluntary_excess','compulsory_excess','construction_type','occupancy'],
 'contents':['bicycle_cover','voluntary_excess','compulsory_excess','security_level','tenure']}


def main():
 assert not OUT.exists();OUT.mkdir(parents=True)
 addr=pq.read_table(RAW/'addresses.parquet',columns=['address_id','distance_to_river_km','elevation_m','basement','roof_type','soil_type']).to_pandas()
 assert addr.address_id.is_unique
 sourcehash={};rows=[]
 for line in cols:
  p=SRC/f'{line}_2023.parquet';before=sha(p);base=pq.read_table(p).to_pandas()
  raw=RAW/f'policies_{line}.parquet';sourcehash[str(raw.relative_to(ROOT)).replace('\\','/')]=sha(raw)
  extra=pq.read_table(raw,columns=['row_id','period_start','period_end']+cols[line],filters=[('period_start','>=',datetime(2023,1,1)),('period_start','<',datetime(2024,1,1))]).to_pandas()
  assert pd.to_datetime(extra.period_start).dt.year.eq(2023).all() and pd.to_datetime(extra.period_end).dt.year.eq(2023).all()
  assert extra.row_id.is_unique and base.row_id.is_unique and set(extra.row_id)==set(base.row_id)
  extra=extra.drop(columns=['period_start','period_end']).rename(columns={c:'x_'+c for c in cols[line]})
  f=base.merge(extra,on='row_id',how='left',validate='one_to_one').merge(addr,on='address_id',how='left',validate='many_to_one')
  for c in ['distance_to_river_km','elevation_m','basement','roof_type','soil_type']:f['x_'+c]=f[c]
  if line=='buildings':f['x_construction_type']=f.x_construction_type.replace({'BRK':'brick','STN':'stone','WOD':'timber','MIX':'mixed_or_nonstandard'})
  f=m.features(f,line)
  original=base.sort_values(m.KEY).reset_index(drop=True);ordered=f.sort_values(m.KEY).reset_index(drop=True)
  for c in base.columns:assert original[c].equals(ordered[c]),c
  keep=list(dict.fromkeys(list(base.columns)+m.FEATURES[line]['numeric']+m.FEATURES[line]['categorical']))
  f[keep].to_parquet(OUT/f'{line}_2023.parquet',index=False)
  assert sha(p)==before
  rows.append({'line':line,'rows':len(f),'source_original_sha256':before,'labels_exposure_original_columns_exact':True,'new_physical_columns':sorted(set(keep)-set(base.columns))})
 report={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','source_market':'developed','year':2023,'rows':rows,'source_hashes':sourcehash,
         '2024_policy_rows_read':0,'new_price_fits':0,'C0_reestimated':False,'targets_reassigned':False,'emerging_support_added':False,
         'outputs':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)} for p in sorted(OUT.glob('*.parquet'))]}
 with (OUT/'report.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,ensure_ascii=False)
 print(json.dumps({'source_rows':sum(x['rows'] for x in rows),'labels_exposure_original_columns_exact':True,'2024_policy_rows_read':0,'fits':0}))


if __name__=='__main__':main()
