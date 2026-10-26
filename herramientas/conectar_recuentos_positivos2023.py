"""Añadir recuentos auxiliares a fuente física manteniendo todas sus columnas."""
from pathlib import Path
import sys,json,hashlib
from datetime import datetime,timezone
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';SRC=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';CNT=R/'privado/semana2/robustez2023/recuentos_positivos2023_v1';OUT=R/'privado/semana2/robustez2023/fuente_positivos2023_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import numpy as np
KEY=['market','line','row_id'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();assert not OUT.exists();OUT.mkdir(parents=True);paths=[Path(__file__),CNT/'report.json',CNT/'preparation_contract.json'];checks=[]
for line in ['motor','buildings','contents']:
 p=SRC/f'{line}_2023.parquet';q=CNT/f'{line}_counts.parquet';paths +=[p,q];f=pq.read_table(p,filters=[('year','=',2023)]).to_pandas();counts=pq.read_table(q,columns=KEY+['N','N_positive','N_zero','cost_cents']).to_pandas();assert not set(['N','N_positive','N_zero','cost_cents']).intersection(f.columns)
 joined=f.merge(counts,on=KEY,validate='one_to_one',how='left');assert len(joined)==len(f) and joined.N_positive.notna().all() and np.array_equal(joined.T0.to_numpy(),joined.cost_cents.to_numpy()/100)
 a=f.sort_values(KEY).reset_index(drop=True);b=joined.sort_values(KEY).reset_index(drop=True)
 for c in f:assert a[c].equals(b[c]),c
 joined.to_parquet(OUT/f'{line}_2023.parquet',index=False);checks.append({'line':line,'rows':len(joined),'all_original_values_and_dtypes_unchanged':True,'keys_exact':True,'fullcost_identity':True})
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'new_fits':0,'new_C0':0,'policy2024rows_read':0,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
with (OUT/'report.json').open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
print(json.dumps(checks))
