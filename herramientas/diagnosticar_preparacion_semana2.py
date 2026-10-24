"""Diagnóstico previo a las reglas de exposición y asignación de semana 2."""
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

data=ROOT/'Hackaton/Semana 2/Datos/emerging'
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=REPO/'privado/semana2/preparacion'/f'diagnostico_{stamp}_{uuid.uuid4().hex[:8]}'
out.mkdir(parents=True,exist_ok=False)
report={'autor':'Codex','utc':datetime.now(timezone.utc).isoformat(),'run':out.relative_to(ROOT).as_posix(),'exposure':[],'input_sha256':{},'training':False}
frames=[]
for line in ['motor','buildings','contents']:
    for kind in ['policies','test']:
        p=data/f'{kind}_{line}.parquet'
        report['input_sha256'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
        f=pq.read_table(p).to_pandas()
        f['line']=line;f['set']=kind
        f['period_start']=pd.to_datetime(f.period_start);f['period_end']=pd.to_datetime(f.period_end)
        days=(f.period_end-f.period_start).dt.days.add(1)
        calendar=(days/365).round(4)
        x=f.exposure
        bad=~np.isclose(x,calendar,rtol=0,atol=0.0000001)
        daysunit=bad&np.isclose(x,days,rtol=0,atol=0.0000001)
        basis360=bad&np.isclose(x,(days/360).round(4),rtol=0,atol=0.0000001)
        g=f.assign(covered_days=days,exposure_calendar=calendar,exposure_delta=x-calendar,
                   exposure_day_unit=daysunit,exposure_basis360=basis360)
        g.loc[bad].to_parquet(out/f'exposure_review_{kind}_{line}.parquet',index=False)
        report['exposure'].append({'line':line,'set':kind,'rows':len(f),'mismatches_round4':int(bad.sum()),'stored_days_units':int(daysunit.sum()),
            'basis360_matches':int(basis360.sum()),'other':int((bad&~daysunit&~basis360).sum()),
            'stored_exposure':float(x.sum()),'calendar_exposure':float(calendar.sum()),'days_min':int(days.min()),'days_max':int(days.max()),
            'negative_or_zero':int((days<=0).sum()),'start_year':{str(k):int(v) for k,v in f.period_start.dt.year.value_counts().items()},
            'row_id_duplicates':int(f.row_id.duplicated().sum()),
            'examples':g.loc[bad,['row_id','policy_id','period_start','period_end','exposure','covered_days','exposure_calendar','exposure_day_unit','exposure_basis360']].head(8).astype(str).to_dict('records')})
        frames.append(f)
periods=pd.concat(frames,ignore_index=True)
train=periods[periods.set.eq('policies')].copy()
report['period_overlap']={}
for kind,g in periods.groupby('set'):
    h=g.sort_values(['line','policy_id','period_start','period_end']).copy()
    h['prev_end']=h.groupby(['line','policy_id']).period_end.shift()
    overlap=h.prev_end.ge(h.period_start)
    report['period_overlap'][kind]={'overlap_rows':int(overlap.sum()),'row_id_duplicates':int(h.row_id.duplicated().sum())}
    h.loc[overlap].to_parquet(out/f'period_overlap_{kind}.parquet',index=False)
c=pq.read_table(data/'claims.parquet').to_pandas().reset_index(names='_claim_pos')
c['loss_date']=pd.to_datetime(c.loss_date)
joined=c.merge(train[['row_id','policy_id','line','period_start','period_end']],on=['policy_id','line'],how='left')
valid=joined.loss_date.ge(joined.period_start)&joined.loss_date.le(joined.period_end)
matches=joined.loc[valid]
matched=matches._claim_pos.unique()
un=c.loc[~c._claim_pos.isin(matched)].copy()
bounds=train.groupby(['line','policy_id']).agg(first_start=('period_start','min'),last_end=('period_end','max'))
un=un.merge(bounds,on=['line','policy_id'],how='left')
un['before_first_start']=un.loss_date.lt(un.first_start)
un['after_last_end']=un.loss_date.gt(un.last_end)
un['days_before_first_start']=(un.first_start-un.loss_date).dt.days
un.to_parquet(out/'unassigned_claims_36.parquet',index=False)
report['unassigned_claims']={
    'rows':len(un),'before_first_start':int(un.before_first_start.sum()),'after_last_end':int(un.after_last_end.sum()),
    'within_gap':int((~un.before_first_start&~un.after_last_end).sum()),
    'candidates':un[['claim_id','policy_id','line','loss_date','report_date','status','paid_to_date','incurred_to_date','recoveries','first_start','last_end','days_before_first_start']].astype(str).to_dict('records')}
report['assignment']={'unique_claims_matched':len(matched),'ambiguous':int((matches.groupby('_claim_pos').size()>1).sum())}
report['accepted_claims_by_peril']={str(k):int(v) for k,v in c.loc[c.status.ne('repudiated')].groupby(['line','peril']).size().items()}
(out/'diagnostico.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'run':report['run'],'exposure':[{k:v for k,v in x.items() if k!='examples'} for x in report['exposure']],
    'unassigned_summary':{k:v for k,v in report['unassigned_claims'].items() if k!='candidates'},
    'unassigned_2023':[x for x in report['unassigned_claims']['candidates'] if x['loss_date'].startswith('2023')],
    'period_overlap':report['period_overlap'],'assignment':report['assignment']},ensure_ascii=True))
