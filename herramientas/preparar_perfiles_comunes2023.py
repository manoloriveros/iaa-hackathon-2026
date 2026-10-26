"""Covariables de cliente suministradas, admisión experimental condicional."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/perfiles_comunes2023_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import pandas as pd,numpy as np
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
 assert not OUT.exists();OUT.mkdir(parents=True);sources=[];checks=[]
 for market,folder in [('emerging',ROOT/'Hackaton/Semana 2/Datos/emerging'),('developed',ROOT/'Hackaton/Semana 1/Datos')]:
  parts=[]
  for line in ['motor','buildings','contents']:
   p=R/(f'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/inputs_2023/{line}.parquet' if market=='emerging' else f'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/{line}_2023.parquet');sources.append(p)
   b=pq.read_table(p,columns=['market','line','row_id','year','customer_id'],filters=[('year','=',2023)]).to_pandas();assert b.year.eq(2023).all() and b.market.eq(market).all();parts.append(b)
  ids=sorted(pd.concat(parts).customer_id.unique());p=folder/'customers.parquet';sources.append(p)
  c=pq.read_table(p,columns=['customer_id','customer_since_year','prior_claims_5y','licence_points','household_size','occupation','marital_status'],filters=[('customer_id','in',ids)]).to_pandas();assert c.customer_id.is_unique and set(c.customer_id)==set(ids) and c.customer_since_year.le(2023).all()
  n=pd.to_numeric(c.prior_claims_5y,errors='raise');assert np.isfinite(n).all() and n.ge(0).all() and n.eq(np.floor(n)).all();c['x_prejoin_prior_log']=np.log1p(n)
  for raw,new in [('licence_points','x_licence_points_profile'),('household_size','x_household_size_profile')]:c[new]=pd.to_numeric(c[raw],errors='raise');assert c[new].dropna().ge(0).all()
  for raw,new in [('occupation','x_occupation_profile'),('marital_status','x_marital_status_profile')]:c[new]=c[raw].astype('string').str.strip().str.lower().str.replace(r'\s+',' ',regex=True).fillna('__MISSING__').astype(str)
  keep=['customer_id']+[x for x in c if x.startswith('x_')]
  for b in parts:
   j=b.merge(c[keep],on='customer_id',how='left',validate='many_to_one',indicator=True);assert j['_merge'].eq('both').all();line=b.line.iloc[0]
   j[['market','line','row_id','year']+[x for x in c if x.startswith('x_')]].to_parquet(OUT/f'{market}_{line}.parquet',index=False);checks.append({'market':market,'line':line,'rows':len(j),'keys_exact':True})
 report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'rows':checks,'fits':0,'2024_policy_rows_read':0,'source_support_not_emerging':True,
 'admission':'experimental conditional supplied-data benchmark only; static profiles have no dated capture versions; joining year <=2023 checked, not sufficient for historical-asof certification',
 'hypothesis':'Unlike cycle9 target-only prior adaptation, estimate common declaration/household/licence/occupation main effects in large source; no gender or actual claims-derived profiles',
 'normalization':'literal lower/trim/collapse whitespace, no semantic profession regrouping; log1p prejoining count; missing numeric values retained for training-only imputation',
 'blocked_fields_unchanged':['written_premium','renewal_decision','customer_service_contacts','discount_applied','missed_payments_12m'],'T0_C0_exposure_unchanged':True,
 'sources':[{'path':rel(p),'sha256':sha(p)} for p in dict.fromkeys(sources)],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
 with (OUT/'report.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print(json.dumps({'rows':checks,'historical_capture_unproven':True,'fits':0}))
if __name__=='__main__':main()
