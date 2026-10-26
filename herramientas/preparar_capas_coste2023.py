"""Descompone cada coste fuente en limitado+exceso, sin eliminar siniestros."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/capas_coste2023_v1';SOURCE=R/'privado/semana2/robustez2023/fuente_desarrollado2023_fisica_v1';RAW=ROOT/'Hackaton/Semana 1/Datos'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
import numpy as np,pandas as pd
KEY=['market','line','row_id'];CAP_CENTS=1000000
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
assert not OUT.exists();OUT.mkdir(parents=True)
prep={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'fixed_cap_CU':10000.,'cap_cents':CAP_CENTS,'threshold_chosen_before_cost_split_statistics':True,'hypothesis':'Limited claim cost plus excess may permit separate stable mean models while conserving all net incurred cost;not winsorizing official target','source_scope':'developed policy/lossyear2023 only','source_valuation':'2024-12-31 followup of occurrence2023','no_target_or_C0_change':True,'code_sha256':sha(Path(__file__))}
with (OUT/'preparation_contract.json').open('x',encoding='utf-8') as h:json.dump(prep,h,ensure_ascii=False,indent=2)
frames=[];paths=[Path(__file__)]
for line in ['motor','buildings','contents']:
 p=SOURCE/f'{line}_2023.parquet';paths.append(p);f=pq.read_table(p,columns=KEY+['year','policy_id','period_start','period_end','T0_cents'],filters=[('year','=',2023)]).to_pandas();assert f.year.eq(2023).all() and f.market.eq('developed').all();frames.append(f)
periods=pd.concat(frames,ignore_index=True);p=RAW/'claims.parquet';paths.append(p)
c=pq.read_table(p,columns=['claim_id','policy_id','line','loss_date','report_date','status','incurred_to_date','recoveries'],filters=[('loss_date','>=',datetime(2023,1,1)),('loss_date','<',datetime(2024,1,1))]).to_pandas();assert c.claim_id.is_unique and pd.to_datetime(c.report_date).le(pd.Timestamp('2024-12-31')).all()
j=c.merge(periods.drop(columns=['year','T0_cents']),on=['line','policy_id'],how='left');assigned=j[j.loss_date.ge(j.period_start)&j.loss_date.le(j.period_end)].copy();assert assigned.claim_id.is_unique
unassigned=set(c.claim_id)-set(assigned.claim_id);prior=R/'privado/semana2/robustez2023/fuente_desarrollado2023_v1/source_claims_without2023_period.parquet';paths.append(prior);assert unassigned==set(pq.read_table(prior,columns=['claim_id']).column(0).to_pylist())
good=assigned[assigned.status.ne('repudiated')].copy();inc=np.rint(good.incurred_to_date.to_numpy()*100);rec=np.rint(good.recoveries.to_numpy()*100);net=inc-rec;assert np.isfinite(net).all() and (net>=0).all();good['cost_cents']=net.astype(np.int64);good['limited_cents']=np.minimum(good.cost_cents,CAP_CENTS);good['excess_cents']=good.cost_cents-good.limited_cents;good['tail_count']=good.excess_cents.gt(0).astype(int)
assert np.array_equal(good.cost_cents,good.limited_cents+good.excess_cents);good['N']=1
totals=good.groupby(KEY)[['N','tail_count','limited_cents','excess_cents','cost_cents']].sum().reset_index();allrows=periods.merge(totals,on=KEY,validate='one_to_one',how='left')
for col in ['N','tail_count','limited_cents','excess_cents','cost_cents']:allrows[col]=allrows[col].fillna(0).astype(np.int64)
assert np.array_equal(allrows.cost_cents,allrows.T0_cents) and np.array_equal(allrows.cost_cents,allrows.limited_cents+allrows.excess_cents) and (allrows.tail_count.gt(0)==allrows.excess_cents.gt(0)).all()
checks=[]
for line in ['motor','buildings','contents']:
 f=allrows[allrows.line.eq(line)];f[KEY+['year','N','tail_count','limited_cents','excess_cents','cost_cents']].to_parquet(OUT/f'{line}_layers.parquet',index=False)
 checks.append({'line':line,'rows':len(f),'claims':int(f.N.sum()),'tail_claims':int(f.tail_count.sum()),'tail_periods':int(f.tail_count.gt(0).sum()),'limited_cost_CU':float(f.limited_cents.sum()/100),'excess_cost_CU':float(f.excess_cents.sum()/100),'original_net_cost_CU':float(f.cost_cents.sum()/100),'cent_identity_exact':True,'same_original_unassigned_claims':len(unassigned)})
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'preparation_contract':prep,'checks':checks,'new_claims_deleted':0,'existing_unassigned_preserved':len(unassigned),'new_fits':0,'new_C0':0,'2024_policy_rows_read':0,'official_target_not_changed':True,'sources':[{'path':rel(p),'sha256':sha(p)} for p in paths],'outputs':[{'path':rel(p),'sha256':sha(p)} for p in OUT.glob('*.parquet')]}
with (OUT/'report.json').open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
print(json.dumps(checks))
