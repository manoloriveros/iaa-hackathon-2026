"""Auditar solo las columnas cambiadas del enlace2023 bloqueado."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import pandas as pd
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023';OUT=R/'privado/semana2/robustez2023/ciclo22_20261025_v1';EXTRA=R/'privado/semana2/robustez2023/contrato_faltante2023_v1'
KEY=['market','line','row_id'];checks=[]
for line in ['motor','buildings','contents']:
 extra=pq.read_table(EXTRA/f'{line}_emerging_extra.parquet').to_pandas().sort_values(KEY).reset_index(drop=True);new=[c for c in extra if c not in KEY]
 for fold in range(5):
  p=BASE/f'{line}_fold{fold}.parquet';cols=[c for c in new if c in pq.ParquetFile(p).schema_arrow.names];f=pq.read_table(p,columns=KEY+cols,filters=[('year','=',2023)]).to_pandas().sort_values(KEY).reset_index(drop=True);assert f[KEY].equals(extra[KEY])
  for c in cols:
   ok=f[c].eq(extra[c])|(f[c].isna()&extra[c].isna());assert ok.all(),(line,fold,c,int((~ok).sum()))
  checks.append({'line':line,'fold':fold,'rows':len(f),'overlap':cols,'missing_columns':[c for c in new if c not in cols],'all_overlaps_value_identical':True,'original_dtypes':{c:str(f[c].dtype) for c in cols},'official_extra_dtypes':{c:str(extra[c].dtype) for c in cols}})
report={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','scope':'only2023keysandnewcontractcolumns,not2024orprices','checks':checks,'new_fits':0,'all_old_columns_to_be_kept':True}
with (OUT/'join_overlap_audit.json').open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
print(json.dumps(report))
