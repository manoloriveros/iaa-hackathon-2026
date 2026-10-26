"""Datos contractuales al inicio; excluye primas y comportamiento posterior."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/contrato_comercial2023_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import pandas as pd,numpy as np
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
assert not OUT.exists();OUT.mkdir(parents=True);sources=[];checks=[]
contract=R/'privado/semana2/ultimo/f0_ultimo_20261023T170841Z_82038766/availability_contract.json';sources.append(contract);d=json.loads(contract.read_text(encoding='utf-8-sig'))
cols=['channel','payment_method','days_quote_to_inception','renewal_count']
for line in ['motor','buildings','contents']:
 for c in cols:assert next(x['role'] for x in d['source_fields'] if x['table']=='policies_'+line and x['column']==c)=='F0_contractual'
 p=ROOT/f'Hackaton/Semana 2/Datos/emerging/policies_{line}.parquet';sources.append(p)
 f=pq.read_table(p,columns=['row_id','period_start','period_end']+cols,filters=[('period_start','>=',datetime(2023,1,1)),('period_start','<',datetime(2024,1,1))]).to_pandas();assert f.row_id.is_unique and pd.to_datetime(f.period_end).dt.year.eq(2023).all()
 assert f.channel.isin(['direct','comparison_site','broker']).all() and f.payment_method.isin(['annual','monthly']).all()
 for c in ['days_quote_to_inception','renewal_count']:assert np.isfinite(f[c]).all() and f[c].ge(0).all()
 f['market']='emerging';f['line']=line;f['year']=2023;f=f.rename(columns={c:'x_'+c for c in cols});f[['market','line','row_id','year']+['x_'+c for c in cols]].to_parquet(OUT/f'{line}.parquet',index=False)
 checks.append({'line':line,'rows':len(f),'all_F0_contractual':True,'missing':0})
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'new_fits':0,'2024_policy_rows_read':0,'hard_blocked_fields_excluded':True,'historical_quote_reconstruction_certified':False,
 'sources':[{'path':rel(p),'sha256':sha(p)} for p in sources],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
with (OUT/'report.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(checks))
