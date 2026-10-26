"""Recuento de siniestros de coste positivo para media Poisson por Gamma."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/recuentos_positivos2023_v1';SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';LAYERS=R/'privado/semana2/robustez2023/capas_coste2023_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import numpy as np,pandas as pd
KEY=['market','line','row_id'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
assert not OUT.exists();OUT.mkdir(parents=True)
contract={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'definition':'positivecostcount for Poisson frequency times Gamma meanpositiveclaim;zero cost claims retained in accounting,all zero-cost periods retained in frequency;fullcostandT0 unchanged','source':'only developed policy/loss2023,followup at2024-12-31','no_new_C0':True,'no_trimming_or_losses_deleted':True,'code_sha256':sha(Path(__file__))}
with (OUT/'preparation_contract.json').open('x',encoding='utf-8') as h:json.dump(contract,h,ensure_ascii=False,indent=2)
periods=[];paths=[Path(__file__)]
for line in ['motor','buildings','contents']:
 p=SOURCE/f'{line}_2023.parquet';paths.append(p);periods.append(pq.read_table(p,columns=KEY+['year','policy_id','period_start','period_end','T0_cents'],filters=[('year','=',2023)]).to_pandas())
periods=pd.concat(periods,ignore_index=True);assert periods.year.eq(2023).all() and periods.market.eq('developed').all();p=ROOT/'Hackaton/Semana 1/Datos/claims.parquet';paths.append(p)
c=pq.read_table(p,columns=['claim_id','policy_id','line','loss_date','report_date','status','incurred_to_date','recoveries'],filters=[('loss_date','>=',datetime(2023,1,1)),('loss_date','<',datetime(2024,1,1))]).to_pandas();assert c.claim_id.is_unique and pd.to_datetime(c.report_date).le(pd.Timestamp('2024-12-31')).all()
j=c.merge(periods.drop(columns=['year','T0_cents']),on=['line','policy_id'],how='left');assigned=j[j.loss_date.ge(j.period_start)&j.loss_date.le(j.period_end)].copy();assert assigned.claim_id.is_unique;unassigned=set(c.claim_id)-set(assigned.claim_id);p=R/'privado/semana2/robustez2023/fuente_desarrollado2023_v1/source_claims_without2023_period.parquet';paths.append(p);assert unassigned==set(pq.read_table(p,columns=['claim_id']).column(0).to_pylist())
good=assigned[assigned.status.ne('repudiated')].copy();net=np.rint(good.incurred_to_date.to_numpy()*100)-np.rint(good.recoveries.to_numpy()*100);assert np.isfinite(net).all() and (net>=0).all();good['cost_cents']=net.astype(np.int64);good['N_positive']=good.cost_cents.gt(0).astype(int);good['N_zero']=good.cost_cents.eq(0).astype(int);good['N']=1
g=good.groupby(KEY)[['N','N_positive','N_zero','cost_cents']].sum().reset_index();allrows=periods.merge(g,on=KEY,validate='one_to_one',how='left')
for col in ['N','N_positive','N_zero','cost_cents']:allrows[col]=allrows[col].fillna(0).astype(np.int64)
assert np.array_equal(allrows.N,allrows.N_positive+allrows.N_zero) and np.array_equal(allrows.cost_cents,allrows.T0_cents) and allrows.N_positive.gt(0).eq(allrows.cost_cents.gt(0)).all();checks=[]
for line in ['motor','buildings','contents']:
 f=allrows[allrows.line.eq(line)].sort_values(KEY).reset_index(drop=True);p=LAYERS/f'{line}_layers.parquet';paths.append(p);old=pq.read_table(p,columns=KEY+['N','cost_cents']).to_pandas().sort_values(KEY).reset_index(drop=True);assert f[KEY].equals(old[KEY]) and np.array_equal(f.N,old.N) and np.array_equal(f.cost_cents,old.cost_cents)
 f[KEY+['year','N','N_positive','N_zero','cost_cents']].to_parquet(OUT/f'{line}_counts.parquet',index=False);checks.append({'line':line,'all_periods':len(f),'claims':int(f.N.sum()),'positive_cost_claims':int(f.N_positive.sum()),'zero_cost_claims_retained':int(f.N_zero.sum()),'positive_cost_periods':int(f.N_positive.gt(0).sum()),'zero_cost_periods_retained_in_frequency':int(f.N_positive.eq(0).sum()),'fullcost_cents_exact':True,'original_N_exact':True})
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'unassigned_set_same_original44':len(unassigned),'new_fits':0,'new_C0':0,'new_costs_deleted':0,'policy2024rows_read':0,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
with (OUT/'report.json').open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
print(json.dumps(checks))
