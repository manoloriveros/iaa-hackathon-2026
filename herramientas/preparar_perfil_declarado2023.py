"""Perfil suministrado anterior a incorporación; solo clientes de cohorte2023."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/perfil_declarado2023_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import pandas as pd,numpy as np
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
 assert not OUT.exists();OUT.mkdir(parents=True)
 parts=[];paths=[]
 for line in ['motor','buildings','contents']:
  p=R/f'privado/semana2/desarrollo2023/dev6_20261023T234239Z_fdab9f0b/inputs_2023/{line}.parquet';paths.append(p)
  f=pq.read_table(p,columns=['market','line','row_id','customer_id','year','period_start'],filters=[('year','=',2023)]).to_pandas();assert f.year.eq(2023).all() and f.market.eq('emerging').all();parts.append(f)
 periods=pd.concat(parts,ignore_index=True);ids=sorted(periods.customer_id.unique().tolist())
 raw=ROOT/'Hackaton/Semana 2/Datos/emerging/customers.parquet';paths.append(raw)
 c=pq.read_table(raw,columns=['customer_id','gender','prior_claims_5y','customer_since_year'],filters=[('customer_id','in',ids)]).to_pandas()
 assert c.customer_id.is_unique and set(c.customer_id)==set(ids)
 n=pd.to_numeric(c.prior_claims_5y,errors='raise');assert np.isfinite(n).all() and n.ge(0).all() and n.eq(np.floor(n)).all()
 assert c.gender.isin(['M','F']).all()
 c['market']='emerging';c=c.rename(columns={'prior_claims_5y':'x_declared_prior_claims_5y','gender':'x_declared_gender'})
 joined=periods.merge(c,on=['market','customer_id'],validate='many_to_one',how='left');assert len(joined)==50094 and joined.customer_since_year.le(joined.year).all()
 c.to_parquet(OUT/'customer_profile2023.parquet',index=False)
 fields=R/'registro/semana2_perfil_declarado_admision_v1.json'
 admission={'id':'S2-PERFIL-DECLARADO-ADMISSION-v1-20261025','utc':datetime.now(timezone.utc).isoformat(),'author':'Codex',
 'fields':['customers.prior_claims_5y','customers.gender'],'old_role':'conditional_undated_profile_not_default','new_role':'experimental supplied-data conditional benchmark covariates, not historical-asof verified',
 'official_dictionary':'prior_claims5y refers to self-declaration before joining;genderM/F explicitly permitted for emerging pricing',
 'public_source':'KaggleMCP live official pages archived ciclo8/official_pages_live_20261025.json; no claim of new publication/change',
 'no_actual_claim_history_derived':True,'source_market':'emerging only, never cross-market ID join',
 'year_consistency_check':'customer_since_year <= policy year2023 for every matched row; joining day/capture version unavailable',
 'scope':'2023 CV;2025 given profiles only after frozen final fits','historical_quote_timestamp_proven':False,
 'all_clauses_of_prior_F0_not_rewritten':True,'hard_BLOCKED_fields_unchanged':['written_premium','renewal_decision','customer_service_contacts','discount_applied','missed_payments_12m'],
 'not_automatic_production_admission':True,'authority':'User authorizes necessary autonomous model improvement; this is Codex experimental scope decision, not human technical approval',
 '2024_policy_rows_read':0,'new_fits':0,'B00_preserved':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths]}
 with fields.open('x',encoding='utf-8') as f:json.dump(admission,f,ensure_ascii=False,indent=2)
 report={'utc':admission['utc'],'customers2023':len(c),'policy_periods2023':len(periods),'all_keys_matched':True,'duplicate_customers':0,'joined_after2023':0,'prior_claims_missing':0,'prior_min':int(n.min()),'prior_max':int(n.max()),'gender_counts':c.x_declared_gender.value_counts().to_dict(),
 'new_fits':0,'2024_policy_rows_read':0,'admission':{'path':rel(fields),'sha256':sha(fields)},'lookup_sha256':sha(OUT/'customer_profile2023.parquet')}
 with (OUT/'report.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
