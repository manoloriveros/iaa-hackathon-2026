"""Enlaces estáticos dentro de mercado y edades al inicio, sin ajuste."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/covariables_basicas2023_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import pandas as pd
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
 assert not OUT.exists();OUT.mkdir(parents=True);sources=[];receipts=[]
 for market,folder in [('emerging',ROOT/'Hackaton/Semana 2/Datos/emerging'),('developed',ROOT/'Hackaton/Semana 1/Datos')]:
  ap=folder/'addresses.parquet';sources.append(ap)
  for line in ['motor','buildings','contents']:
   basepath=R/(f'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/inputs_2023/{line}.parquet' if market=='emerging' else f'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1/{line}_2023.parquet');sources.append(basepath)
   b=pq.read_table(basepath,columns=['market','line','row_id','year','address_id']).to_pandas();assert b.year.eq(2023).all() and b.market.eq(market).all() and b.row_id.is_unique
   ac=['address_id','urban_density']+(['trees_within_5m','listed_building'] if line=='buildings' else [])
   a=pq.read_table(ap,columns=ac,filters=[('address_id','in',sorted(b.address_id.unique()))]).to_pandas();assert a.address_id.is_unique and set(a.address_id)==set(b.address_id)
   f=b.merge(a,on='address_id',how='left',validate='many_to_one')
   f=f.rename(columns={c:'x_'+c for c in ac if c!='address_id'})
   if line!='motor':
    p=folder/f'policies_{line}.parquet';sources.append(p);age='policyholder_age_band' if market=='emerging' else 'policyholder_age'
    raw=pq.read_table(p,columns=['row_id','period_start','period_end',age],filters=[('period_start','>=',datetime(2023,1,1)),('period_start','<',datetime(2024,1,1))]).to_pandas()
    assert raw.row_id.is_unique and set(raw.row_id)==set(b.row_id) and pd.to_datetime(raw.period_end).dt.year.eq(2023).all()
    if market=='developed':raw['x_policyholder_age_band']=pd.cut(pd.to_numeric(raw[age]),[16,24,34,49,64,float('inf')],labels=['17-24','25-34','35-49','50-64','65+']).astype(str)
    else:raw['x_policyholder_age_band']=raw[age].astype(str)
    assert raw.x_policyholder_age_band.isin(['17-24','25-34','35-49','50-64','65+']).all()
    f=f.merge(raw[['row_id','x_policyholder_age_band']],on='row_id',validate='one_to_one')
   assert f.x_urban_density.isin(['rural','suburban','urban','dense_urban']).all()
   keep=['market','line','row_id','year']+[c for c in f if c.startswith('x_')];f[keep].to_parquet(OUT/f'{market}_{line}.parquet',index=False)
   receipts.append({'market':market,'line':line,'rows':len(f),'missing':f[keep].isna().sum().to_dict(),'keys_exact':True})
 report={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','receipts':receipts,'fits':0,'2024_policy_rows_read':0,'historical_master_version_proven':False,
 'availability':'age is expressly at start in official dictionary; urban density and static physical flags supplied address attributes, unversioned master limitation preserved',
 'source_target_never_ID_joined':True,'T0_C0_exposure_unchanged':True,
 'sources':[{'path':rel(p),'sha256':sha(p)} for p in dict.fromkeys(sources)],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
 with (OUT/'report.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print(json.dumps({'rows':receipts,'fits':0}))
if __name__=='__main__':main()
