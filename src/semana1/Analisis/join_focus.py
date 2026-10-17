"""Explica claves y siniestros que no cruzan; no fuerza asignaciones."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd

BASE=Path(__file__).parent
OUT=ROOT/json.loads((BASE/'current_run.json').read_text(encoding='utf-8'))['run']
DATA=ROOT/'Hackaton/Semana 1/Datos'
master=pd.read_parquet(DATA/'customers.parquet',columns=['customer_id']).customer_id.astype('string')
motor=pd.read_parquet(DATA/'policies_motor.parquet',columns=['row_id','customer_id'])
bad=motor.loc[~motor.customer_id.isin(master)]
raw=bad.customer_id.astype('string')
diag={'missing_rows':len(bad),'examples':raw.head(15).tolist(),
      'lengths':{str(k):int(v) for k,v in raw.str.len().value_counts().items()}}
for name,candidate in {'strip':raw.str.strip(),'remove_decimal_zero':raw.str.replace(r'\.0$','',regex=True),
                       'digits_leading_zero_removed':raw.str.lstrip('0')}.items():
    diag[name+'_matched_rows']=int(candidate.isin(master).sum())
(OUT/'customer_key_diagnosis.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(diag,ensure_ascii=True),flush=True)
padding_results=[]
for table_name in ['policies_motor','test_motor']:
    source=pd.read_parquet(DATA/(table_name+'.parquet'),columns=['customer_id']).customer_id.astype('string')
    padded=source.str.zfill(8)
    failed=~source.isin(master)
    padding_results.append({'table':table_name,'raw_unmatched_rows':int(failed.sum()),
        'unmatched_after_padding':int((~padded.isin(master)).sum()),
        'recovered_rows':int((failed&padded.isin(master)).sum()),
        'rows_modified_by_candidate':int((source!=padded).sum())})
padding={'master_key_length_counts':{str(k):int(v) for k,v in master.str.len().value_counts().items()},
         'master_unique':master.is_unique,'master_all_digits':bool(master.str.fullmatch(r'[0-9]{8}').all()),
         'checks':padding_results,'candidate':'pad numeric customer_id strings to length 8; no numeric conversion; no originals modified',
         'approval':'candidate backed by lookup consistency, not human-approved production transformation'}
(OUT/'customer_key_padding_check.json').write_text(json.dumps(padding,ensure_ascii=False,indent=2),encoding='utf-8')
example_cols=['row_id','period_start','period_end','exposure','driver_age','years_licensed','cover_type','voluntary_excess','compulsory_excess']
example=pd.read_parquet(DATA/'policies_motor.parquet',columns=example_cols,filters=[('row_id','==','M00000001')]).astype(str).to_dict('records')[0]
example['inclusive_days']=(pd.Timestamp(example['period_end'])-pd.Timestamp(example['period_start'])).days+1
example['date_duration_div_365']=example['inclusive_days']/365
(OUT/'worked_policy_example.json').write_text(json.dumps(example,ensure_ascii=False,indent=2),encoding='utf-8')
claims=pd.read_parquet(DATA/'claims.parquet');claims.loss_date=pd.to_datetime(claims.loss_date)
rows=[];details=[]
for line in ['motor','buildings','contents']:
    p=pd.read_parquet(DATA/('policies_'+line+'.parquet'),columns=['policy_id','row_id','period_start','period_end'])
    p.period_start=pd.to_datetime(p.period_start);p.period_end=pd.to_datetime(p.period_end)
    c=claims[claims.line==line]
    merged=c.merge(p,on='policy_id',how='left')
    found=merged.loc[merged.loss_date.between(merged.period_start,merged.period_end),'claim_id']
    bad=c.loc[~c.claim_id.isin(found)].copy()
    existence=bad.policy_id.isin(p.policy_id)
    periods=p.groupby('policy_id').agg(first_start=('period_start','min'),last_end=('period_end','max'))
    bad=bad.merge(periods,on='policy_id',how='left',validate='many_to_one')
    bad['before_first']=bad.loss_date<bad.first_start
    bad['after_last']=bad.loss_date>bad.last_end
    rec={'line':line,'unmatched':len(bad),'policy_id_not_found':int((~existence).sum()),
         'before_first_period':int(bad.before_first.sum()),'after_last_period':int(bad.after_last.sum()),
         'internal_gap':int((~bad.before_first&~bad.after_last&bad.first_start.notna()).sum()),
         'loss_year_counts':{str(k):int(v) for k,v in bad.loss_date.dt.year.value_counts().items()},
         'net_incurred_excl_declined':float((bad.incurred_to_date-bad.recoveries).where(bad.status!='repudiated',0).sum()),
         'examples':bad[['claim_id','policy_id','loss_date','first_start','last_end']].head(5).astype(str).to_dict('records')}
    rows.append(rec)
    if len(bad):details.append(bad.assign(reason='No inclusive date match'))
pd.concat(details).to_csv(OUT/'tables/unmatched_claims.csv',index=False)
(OUT/'unmatched_claims_diagnosis.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=True),flush=True)
