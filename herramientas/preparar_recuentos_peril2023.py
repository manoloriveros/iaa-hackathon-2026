"""Recuentos y marcas2023 por periodo/peril, preservando el T0 existente."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/recuentos_peril2023_v2'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.path.insert(0,str(R/'src'))
import pyarrow.parquet as pq
import pandas as pd,numpy as np
KEY=['market','line','row_id'];RAW=ROOT/'Hackaton/Semana 1/Datos'
SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_v1'
CLAIMS=R/'privado/semana2/desarrollo2023/coberturas_20261024T011932Z_14b50ca9/inputs_2023'
BASE=R/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def eligible(frame,line,peril):
 if line=='motor':
  if peril in ['own_damage','glass_hail']:return frame.x_cover_type.eq('comprehensive').to_numpy()
  if peril=='theft':return frame.x_cover_type.isin(['comprehensive','third_party_fire_theft']).to_numpy()
 if peril=='accidental_damage':return frame.x_accidental_damage_cover.eq(1).to_numpy()
 return np.ones(len(frame),bool)
def aggregate(claims):
 return claims.groupby(KEY+['peril']).agg(N=('claim_id','size'),T0_cents=('T0_cents','sum')).reset_index()
def validate(periods,counts,line):
 actual=counts.groupby(KEY).T0_cents.sum().rename('claims_cents').reset_index()
 joined=periods[KEY+['T0']].merge(actual,on=KEY,how='left',validate='one_to_one')
 assert np.array_equal(np.rint(joined.T0*100).to_numpy(),joined.claims_cents.fillna(0).to_numpy())
 violations=[]
 for peril in counts.peril.unique():
  c=counts[counts.peril.eq(peril)].merge(periods[KEY+['x_cover_type' if line=='motor' else 'x_accidental_damage_cover']],on=KEY,how='left',validate='one_to_one')
  mask=eligible(c,line,peril)
  if not mask.all():violations.append({'peril':peril,'policies_with_claim_outside_expected_cover':int((~mask).sum()),'cost_cents':int(c.loc[~mask,'T0_cents'].sum())})
 return violations
def main():
 assert not OUT.exists();OUT.mkdir(parents=True);sources=[];results=[];sourceperiods=[]
 for line in ['motor','buildings','contents']:
  p=SOURCE/f'{line}_2023.parquet';f=pq.read_table(p,filters=[('year','=',2023)]).to_pandas();sourceperiods.append(f);sources.append(p)
 cpath=RAW/'claims.parquet';sources.append(cpath)
 c=pq.read_table(cpath,columns=['claim_id','policy_id','line','peril','loss_date','report_date','status','incurred_to_date','recoveries'],filters=[('loss_date','>=',datetime(2023,1,1)),('loss_date','<',datetime(2024,1,1))]).to_pandas()
 assert pd.to_datetime(c.loss_date).dt.year.eq(2023).all() and pd.to_datetime(c.report_date).le(pd.Timestamp('2024-12-31')).all()
 p=pd.concat([f[KEY+['policy_id','period_start','period_end']] for f in sourceperiods])
 j=c.merge(p,on=['line','policy_id'],how='left');j=j[j.loss_date.ge(j.period_start)&j.loss_date.le(j.period_end)].copy()
 assert not j.claim_id.duplicated().any()
 assert len(c)-j.claim_id.nunique()==44
 j=j[j.status.ne('repudiated')].copy();j['T0_cents']=(np.rint(j.incurred_to_date.to_numpy()*100)-np.rint(j.recoveries.to_numpy()*100)).astype(np.int64)
 assert (j.T0_cents>=0).all()
 sourcecounts=aggregate(j)
 for line,f in zip(['motor','buildings','contents'],sourceperiods):
  counts=sourcecounts[sourcecounts.line.eq(line)].copy();bad=validate(f,counts,line);counts.to_parquet(OUT/f'developed_{line}_counts.parquet',index=False)
  results.append({'market':'developed','line':line,'periods':len(f),'claims':int(counts.N.sum()),'net_cents':int(counts.T0_cents.sum()),'coverage_conflicts':bad,'perils':counts.groupby('peril').agg(claims=('N','sum'),net_cents=('T0_cents','sum')).reset_index().to_dict('records')})
  cp=CLAIMS/f'claims_{line}.parquet';fp=BASE/f'{line}_fold0.parquet';sources += [cp,fp]
  cc=pq.read_table(cp,columns=KEY+['claim_id','peril','T0_cents','year','fold','included_in_T0']).to_pandas();cc=cc[cc.included_in_T0.eq(True)]
  assert cc.year.eq(2023).all();counts=aggregate(cc)
  cols=KEY+['year','T0','x_cover_type' if line=='motor' else 'x_accidental_damage_cover']
  ff=pq.read_table(fp,columns=cols,filters=[('year','=',2023)]).to_pandas();bad=validate(ff,counts,line)
  counts.to_parquet(OUT/f'emerging_{line}_counts.parquet',index=False)
  results.append({'market':'emerging','line':line,'periods':len(ff),'claims':int(counts.N.sum()),'net_cents':int(counts.T0_cents.sum()),'coverage_conflicts':bad,'perils':counts.groupby('peril').agg(claims=('N','sum'),net_cents=('T0_cents','sum')).reset_index().to_dict('records')})
 conflicts=[{'market':x['market'],'line':x['line'],**b} for x in results for b in x['coverage_conflicts']]
 report={'utc':datetime.now(timezone.utc).isoformat(),'author':'Codex','year':2023,'results':results,'coverage_conflicts':conflicts,
  'all_T0_cent_totals_reconciled':True,'new_fits':0,'2024_policy_rows_read':0,'source_claims_without2023_period_preserved':44,
  'sources':[{'path':rel(p),'sha256':sha(p)} for p in sources]}
 with (OUT/'report.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print(json.dumps({'cent_reconciliation':True,'coverage_conflicts':conflicts,'market_claim_counts':[{k:v for k,v in x.items() if k in ['market','line','claims']} for x in results]}))
if __name__=='__main__':main()
