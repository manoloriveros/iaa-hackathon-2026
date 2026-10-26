"""Edad2023 por fila: comparación sin etiquetas ni ajustes de precios."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/edad2023_auditoria_v1';S=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd,numpy as np,pyarrow.parquet as pq
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def band(a):return pd.cut(a,[16,24,34,49,64,np.inf],labels=['17-24','25-34','35-49','50-64','65+']).astype('string')
def main():
 assert not OUT.exists();OUT.mkdir(parents=True);sources=[Path(__file__)];findings=[]
 for line in ['motor','buildings','contents']:
  sp=S/f'{line}_2023.parquet';sources.append(sp);cols=['market','line','row_id','year','customer_id','address_id','exposure']+(['x_years_licensed','x_driver_age_band'] if line=='motor' else [])
  f=pq.read_table(sp,columns=cols,filters=[('year','=',2023)]).to_pandas();assert f.market.eq('developed').all() and f.year.eq(2023).all() and f.row_id.is_unique
  rp=ROOT/f'Hackaton/Semana 1/Datos/policies_{line}.parquet';sources.append(rp);age='driver_age' if line=='motor' else 'policyholder_age'
  raw=pq.read_table(rp,columns=['row_id','period_start','period_end',age],filters=[('period_start','>=',datetime(2023,1,1)),('period_start','<',datetime(2024,1,1))]).to_pandas();assert raw.row_id.is_unique and set(raw.row_id)==set(f.row_id) and pd.to_datetime(raw.period_end).dt.year.eq(2023).all()
  f=f.merge(raw,on='row_id',validate='one_to_one');f['source_raw_age']=pd.to_numeric(f[age],errors='raise');f['source_raw_band']=band(f.source_raw_age)
  rec={'line':line,'source_rows':len(f),'raw_age_missing':int(f.source_raw_age.isna().sum()),'raw_age_range':[float(f.source_raw_age.min()),float(f.source_raw_age.max())],'raw_age_nunique':int(f.source_raw_age.nunique()),'raw_band_counts':f.source_raw_band.value_counts(dropna=False).to_dict()}
  if line=='motor':
   rec['existing_band_matches_raw_exact']=bool(f.source_raw_band.eq(f.x_driver_age_band).all());assert rec['existing_band_matches_raw_exact']
   valid=f.x_years_licensed.notna();rec['years_licensed_missing']=int((~valid).sum());rec['years_licensed_exceeds_age']=int((f.loc[valid,'x_years_licensed']>f.loc[valid,'source_raw_age']).sum())
   rec['exact_age_not_assumed_from_policyholder_DOB']=True
  else:
   cp=ROOT/'Hackaton/Semana 1/Datos/customers.parquet';sources.append(cp);c=pq.read_table(cp,columns=['customer_id','date_of_birth'],filters=[('customer_id','in',sorted(f.customer_id.unique()))]).to_pandas();assert c.customer_id.is_unique
   f=f.merge(c,on='customer_id',validate='many_to_one',how='left');dob=pd.to_datetime(f.date_of_birth);start=pd.to_datetime(f.period_start);age_dob=start.dt.year-dob.dt.year-((start.dt.month<dob.dt.month)|((start.dt.month==dob.dt.month)&(start.dt.day<dob.dt.day))).astype(int);f['source_DOB_age']=age_dob;f['source_DOB_band']=band(age_dob)
   valid=dob.notna();rec.update(DOB_missing_periods=int((~valid).sum()),DOB_age_range=[float(age_dob.min()),float(age_dob.max())],raw_DOB_age_disagreements=int((f.loc[valid,'source_raw_age']!=age_dob[valid]).sum()),raw_DOB_band_disagreements=int(f.loc[valid,'source_raw_band'].ne(f.loc[valid,'source_DOB_band']).sum()))
  target=BASE/f'{line}_fold0.parquet';sources.append(target);tc='x_driver_age_band' if line=='motor' else 'x_policyholder_age_band';t=pq.read_table(target,columns=['market','line','row_id','year',tc],filters=[('year','=',2023)]).to_pandas();assert t.market.eq('emerging').all() and t.year.eq(2023).all();rec['target_band_counts']=t[tc].astype(str).value_counts(dropna=False).to_dict();rec['target_exact_age_available']=False
  keep=['market','line','row_id','year','customer_id','address_id','exposure','source_raw_age','source_raw_band']+(['x_years_licensed'] if line=='motor' else ['source_DOB_age','source_DOB_band'])
  f[keep].to_parquet(OUT/f'{line}_source_age2023.parquet',index=False);t.to_parquet(OUT/f'{line}_target_band2023.parquet',index=False);findings.append(rec)
 report={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','findings':findings,'labels_read':False,'models_loaded':0,'new_fits':0,'new_scores':0,'2024_policy_rows_read':0,'price_target_exposure_C0_unchanged':True,'corrections_adopted':False,'source_age_is_period_inception_variable_per_official_dictionary':True,'source_DOB_used_only_home_not_motor_main_driver':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in dict.fromkeys(sources)],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
 with (OUT/'report.json').open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2,default=str)
 print(json.dumps(report['findings'],ensure_ascii=False,default=str))
if __name__=='__main__':main()
