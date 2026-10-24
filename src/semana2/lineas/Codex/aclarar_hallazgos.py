"""Amplía incidencias iniciales con agregados. No modifica datos."""
from pathlib import Path
import json
import sys
from datetime import datetime, timezone
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd
import pyarrow.parquet as pq

DATA=BASE.parent/'Datos/emerging'
out={'autor':'Codex','utc':datetime.now(timezone.utc).isoformat(),'exposure':{},'unmatched_claims':{},'fixed_expense_questions':{},'data_modified':False}
pols=[]
for line in ['motor','buildings','contents']:
    p=pq.read_table(DATA/f'policies_{line}.parquet').to_pandas()
    p['line']=line; pols.append(p)
    e=p.exposure
    start=pd.to_datetime(p.period_start); end=pd.to_datetime(p.period_end)
    calendar=(end-start).dt.days.add(1)/365.25
    out['exposure'][line]={'nonpositive':int((e<=0).sum()),'above_one':int((e>1).sum()),'quantiles':{str(k):float(v) for k,v in e.quantile([0,.5,.95,.99,1]).items()},
        'calendar_exposure_sum_365_25':float(calendar.sum()),'stored_sum':float(e.sum()),
        'discrepancies_above_0_01':int((e.sub(calendar).abs()>.01).sum()),
        'sum_exposure_for_above_one':float(e[e>1].sum()),'max_period_days':int((end-start).dt.days.add(1).max()),
        'common_above_one_values':{str(k):int(v) for k,v in e[e>1].value_counts().head(12).items()}}
train=pd.concat(pols,ignore_index=True)
c=pq.read_table(DATA/'claims.parquet').to_pandas().reset_index(names='_pos')
j=c.merge(train[['policy_id','line','period_start','period_end']],on=['policy_id','line'],how='left')
match=j[(pd.to_datetime(j.loss_date)>=pd.to_datetime(j.period_start))&(pd.to_datetime(j.loss_date)<=pd.to_datetime(j.period_end))]
un=c[~c._pos.isin(match._pos)]
out['unmatched_claims']={'rows':len(un),'loss_year_counts':{str(k):int(v) for k,v in pd.to_datetime(un.loss_date).dt.year.value_counts().items()},
    'policy_key_not_in_training':int((~un.policy_id.isin(train.policy_id)).sum()),'loss_date_min':str(un.loss_date.min()),'loss_date_max':str(un.loss_date.max()),
    'line':{str(k):int(v) for k,v in un.line.value_counts().items()},'net_incurred_raw':float((un.incurred_to_date-un.recoveries).sum())}
r=pq.read_table(DATA/'reference_policies.parquet').to_pandas()
out['fixed_expense_questions']={'reference_channels':{str(k):int(v) for k,v in r.channel.value_counts().items()},
    'reference_repeated_policy_ids':int(r.policy_id.duplicated().sum()),'reference_exposure_min':float(r.exposure.min()),'reference_exposure_max':float(r.exposure.max()),
    'reference_partial_periods':int((r.exposure<.99).sum())}
(BASE/'hallazgos_ampliados.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=True))
