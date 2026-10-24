"""Inspección de disponibilidad, clima, retraso y reservas; sin modelos de precio."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import uuid

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

index=json.loads((REPO/'registro/semana2_preparacion_actual.json').read_text(encoding='utf-8'))
base=ROOT/index['run']
data=ROOT/'Hackaton/Semana 2/Datos/emerging'
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=REPO/'privado/semana2/ultimo'/('diagnostico_'+stamp+'_'+uuid.uuid4().hex[:8])
out.mkdir(parents=True,exist_ok=False)
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'run':out.relative_to(ROOT).as_posix(),'pricing_models_trained':0,'schema':{},'delays':[],'weather':{},'operational_covariates':[]}
for p in sorted(data.glob('*.parquet')):
    report['schema'][p.stem]={f.name:str(f.type) for f in pq.ParquetFile(p).schema_arrow}
c=pq.read_table(base/'claim_assignment_audit.parquet').to_pandas()
c=c.loc[c.included_in_T0].copy()
c['loss_date']=pd.to_datetime(c.loss_date);c['report_date']=pd.to_datetime(c.report_date)
c['delay_days']=(c.report_date-c.loss_date).dt.days
c['age_days']=(pd.Timestamp('2024-12-31')-c.loss_date).dt.days
c['loss_year']=c.loss_date.dt.year
c['net']=c.T0_cents/100;c['reserve']=c.reserve_cents/100
for k,g in c.groupby(['line','peril','loss_year']):
    row={'line':k[0],'peril':k[1],'loss_year':int(k[2]),'n':len(g),'net':float(g.net.sum()),'reserve':float(g.reserve.sum()),
        'open':int(g.status.eq('open').sum()),'delay_quantiles':{str(a):float(b) for a,b in g.delay_days.quantile([0,.5,.9,.95,.99,1]).items()},
        'age_min':int(g.age_days.min()),'age_max':int(g.age_days.max()),'after_365_n':int(g.delay_days.gt(365).sum()),
        'after_365_cost':float(g.loc[g.delay_days.gt(365),'net'].sum()),'after_90_n':int(g.delay_days.gt(90).sum()),
        'mean_cost_early90':float(g.loc[g.delay_days.le(90),'net'].mean()) if g.delay_days.le(90).any() else None,
        'mean_cost_late90':float(g.loc[g.delay_days.gt(90),'net'].mean()) if g.delay_days.gt(90).any() else None}
    report['delays'].append(row)
c[['claim_id','line','peril','loss_year','delay_days','age_days','net','reserve','status']].to_parquet(out/'claim_delay_reserve_audit.parquet',index=False)
w=pq.read_table(data/'weather.parquet').to_pandas()
weathercols=[x for x in w if x not in ['address_id','year']]
report['weather']['years']={str(a):int(b) for a,b in w.year.value_counts().items()}
report['weather']['comparison']=[]
for a,b in [(2023,2024),(2024,2025)]:
    m=w.loc[w.year.eq(a)].merge(w.loc[w.year.eq(b)],on='address_id',validate='one_to_one',suffixes=('_a','_b'))
    for col in weathercols:
        x=m[col+'_a'].to_numpy();y=m[col+'_b'].to_numpy()
        report['weather']['comparison'].append({'from':a,'to':b,'column':col,'rows':len(m),'exact_equal_share':float((x==y).mean()),
            'correlation':float(np.corrcoef(x,y)[0,1]) if np.std(x)>0 and np.std(y)>0 else None,
            'mean_from':float(x.mean()),'mean_to':float(y.mean())})
customers=pq.read_table(data/'customers.parquet').to_pandas()
for line in ['motor','buildings','contents']:
    for kind in ['policies','test']:
        f=pq.read_table(base/f'periods_{kind}_{line}.parquet').to_pandas()
        t=pq.read_table(base/'target_T0_and_stresses.parquet',columns=['line','row_id','n_accepted']).to_pandas()
        f=f.merge(customers[['customer_id','customer_since_year']],on='customer_id',validate='many_to_one')
        f=f.merge(t.loc[t.line.eq(line),['row_id','n_accepted']],on='row_id',validate='one_to_one')
        row={'line':line,'set':kind,'rows':len(f),'customer_since_after_period_year':int(f.customer_since_year.gt(f.year).sum()),
             'quote_to_inception_negative':int(f.days_quote_to_inception.lt(0).sum()),
             'service_contacts_mean':float(f.customer_service_contacts.mean()),'service_contacts_ge3':int(f.customer_service_contacts.ge(3).sum()),
             'capital_min':float(f.sum_insured.min()) if 'sum_insured' in f else None,'capital_max':float(f.sum_insured.max()) if 'sum_insured' in f else None}
        if kind=='policies':
            row['claims_by_contact']=[{'contacts':str(k),'rows':len(g),'accepted_claims':int(g.n_accepted.sum())} for k,g in f.groupby('customer_service_contacts')]
        report['operational_covariates'].append(row)
        qdate=pd.to_datetime(f.period_start)-pd.to_timedelta(f.days_quote_to_inception,unit='D')
        report['weather'].setdefault('availability',[]).append({'line':line,'set':kind,'previous_calendar_year_available_at_inception':int(f.year.sub(1).isin(w.year.unique()).sum()),
            'last_full_calendar_year_at_quote_available':int(qdate.dt.year.sub(1).isin(w.year.unique()).sum()),
            'last_full_year_at_quote_counts':{str(a):int(b) for a,b in qdate.dt.year.sub(1).value_counts().items()}})
report['source_hashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [data/'weather.parquet',data/'customers.parquet',base/'claim_assignment_audit.parquet']}
(out/'diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary={'run':report['run'],'weather':report['weather'],'delays':report['delays'],'operational_covariates':[{k:v for k,v in r.items() if k!='claims_by_contact'} for r in report['operational_covariates']]}
print(json.dumps(summary,ensure_ascii=True))
