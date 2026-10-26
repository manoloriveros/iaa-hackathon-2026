"""Preparación de fuente2023 con10% adicional fijo; no modelos ni puntuaciones."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import mascara_fuente2023_v3 as mask
import pandas as pd,numpy as np,pyarrow.parquet as pq
SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';OUT=R/'privado/semana2/robustez2023/fuente_mascarada2023_v3';assert not OUT.exists();OUT.mkdir(parents=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();now=lambda:datetime.now(timezone.utc).isoformat()
def dump(p,obj):
 with p.open('x',encoding='utf-8') as h:json.dump(obj,h,ensure_ascii=False,indent=2)
contract={'author':'Codex','utc':now(),'fixed_probability':.10,'seed':mask.SEED,'fields':mask.FIELDS,'mask_before_any_pricefit_or_score':True,'rationale':'six numeric line/field pairs have source~2.5% missing versus target~12%;measurementview,not proof of MCAR or risk caused by missingness','no_replication_or_new_support':True,'scope':'developed2023 covariateview only;all costs,exposure,keys,originalfilespreserved','sources':[{'path':rel(Path(__file__)),'sha256':sha(Path(__file__))},{'path':rel(Path(mask.__file__)),'sha256':sha(Path(mask.__file__))}]};dump(OUT/'preparation_contract.json',contract)
# Changed mechanism controls, without fitting a price estimator.
fixtures={}
for line in mask.FIELDS:
 n=1000;f=pd.DataFrame({'market':'developed','line':line,'row_id':['s'+str(i) for i in range(n)],'policy_id':['p'+str(i//2) for i in range(n)],'address_id':['a'+str(i//2) for i in range(n)],'year':2023,'T0':np.arange(n,dtype=float),'exposure':.8})
 for col in mask.FIELDS[line]:
  f[col]=np.arange(n,dtype=float)%7;f.loc[np.arange(n)%7==0,col]=np.nan
 if line!='motor':f['x_log_distance_to_river_km']=np.log1p(f.x_distance_to_river_km)
 a,_=mask.apply(f,line);b,_=mask.apply(f.sample(frac=1,random_state=1),line);assert a.sort_values(mask.KEY).reset_index(drop=True).equals(b.sort_values(mask.KEY).reset_index(drop=True));poison,_=mask.apply(f.assign(T0=1e15),line)
 for col in mask.FIELDS[line]:assert a[col].equals(poison[col])
 for bad in [f.assign(year=2024),f.assign(market='emerging')]:
  try:mask.apply(bad,line)
  except AssertionError:pass
  else:raise AssertionError('Ámbito prohibido')
 if line!='motor':
  logonly=f.drop(columns=['x_distance_to_river_km']);check,_=mask.apply(logonly,line);assert check.x_log_distance_to_river_km.equals(a.x_log_distance_to_river_km)
 fixtures[line]=a
for line in ['buildings','contents']:
 assert fixtures['buildings'].x_distance_to_river_km.isna().equals(fixtures[line].x_distance_to_river_km.isna())
dump(OUT/'synthetic_mask.json',{'row_order_invariant':True,'labels_poisoned_mask_invariant':True,'shared_address_mask_same_across_home_lines':True,'wrong_market_or2024_rejected':True,'new_price_fits':0})
checks=[];paths=[Path(__file__),Path(mask.__file__)]
for line in mask.FIELDS:
 p=SOURCE/f'{line}_2023.parquet';paths.append(p);f=pq.read_table(p,filters=[('year','=',2023)]).to_pandas();before=sha(p);out,note=mask.apply(f,line);assert sha(p)==before;out.to_parquet(OUT/f'{line}_2023.parquet',index=False);checks.append(note)
dump(OUT/'report.json',{'author':'Codex','utc':now(),'checks':checks,'original_files_unchanged':True,'no_new_rows_or_cost_deletions':True,'new_price_fits':0,'new_C0_fits':0,'2024_policy_rows_read':0,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]})
print(json.dumps({'checks':checks,'new_price_fits':0,'new_C0':0}))
