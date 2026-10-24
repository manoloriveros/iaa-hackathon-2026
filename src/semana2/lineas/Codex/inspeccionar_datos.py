"""Lectura y diagnóstico descriptivo de Semana 2. No limpia ni entrena."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys
import time

WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE / 'Preparación/.cache/parquet-reader'))
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parent
DATA = BASE.parent / 'Datos'
OLD = WORKSPACE / 'Hackaton/Semana 1/Datos'
START = time.monotonic()

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def counts(series):
    return {str(k):int(v) for k,v in series.value_counts(dropna=False).items()}

def dates(df, col):
    return pd.to_datetime(df[col], errors='coerce')

result = {'autor':'Codex','started_utc':datetime.now(timezone.utc).isoformat(),
          'environment':{'python':platform.python_version(),'pyarrow':pa.__version__,'pandas':pd.__version__,'numpy':np.__version__},
          'local_originals':[], 'emerging_files':[], 'training':False,'data_modified':False}

for p in sorted(DATA.glob('*.parquet')):
    old = OLD / p.name
    schema = pq.ParquetFile(p)
    result['local_originals'].append({'name':p.name,'bytes':p.stat().st_size,'rows':schema.metadata.num_rows,
                                    'sha256':sha(p),'week1_sha256':sha(old) if old.exists() else None,
                                    'same_as_week1':old.exists() and sha(p)==sha(old)})

frames = {}
for p in sorted((DATA / 'emerging').glob('*.parquet')):
    table = pq.read_table(p)
    table.validate(full=True)
    frames[p.stem] = table.to_pandas()
    item = {'name':p.name,'rows':table.num_rows,'columns':table.num_columns,'bytes':p.stat().st_size,
            'sha256':sha(p),'schema':{f.name:str(f.type) for f in table.schema},
            'nulls':{c:table[c].null_count for c in table.column_names}}
    for key in ['row_id','claim_id','customer_id','address_id']:
        if key in table.column_names:
            s = frames[p.stem][key]
            item.setdefault('id_diagnostics',{})[key] = {'unique':int(s.nunique()),'duplicate_rows':int(s.duplicated().sum()),'nulls':int(s.isna().sum())}
    result['emerging_files'].append(item)

assert len(frames)==13, f'Se esperaban 13 tablas emerging, hay {len(frames)}'
result['schema_differences'] = {}
for name, df in frames.items():
    old = OLD / f'{name}.parquet'
    if old.exists():
        cols = set(pq.ParquetFile(old).schema_arrow.names)
        result['schema_differences'][name]={'only_developed':sorted(cols-set(df)), 'only_emerging':sorted(set(df)-cols)}

policy_summaries=[]
trains=[]
tests=[]
customers=frames['customers']
addresses=frames['addresses']
for line in ['motor','buildings','contents']:
    train=frames['policies_'+line].copy()
    test=frames['test_'+line].copy()
    train['line']=line
    test['line']=line
    trains.append(train)
    tests.append(test)
    for kind, df in [('train',train),('test',test)]:
        ds=dates(df,'period_start'); de=dates(df,'period_end')
        years=ds.dt.year
        row={'line':line,'set':kind,'rows':len(df),'policies':int(df.policy_id.nunique()),'customers':int(df.customer_id.nunique()),
             'year_counts':counts(years),'start_min':str(ds.min()),'end_max':str(de.max()),
             'exposure_sum':float(df.exposure.sum()),'exposure_invalid':int(((df.exposure<=0)|(df.exposure>1)|df.exposure.isna()).sum()),
             'end_before_start':int((de<ds).sum()),'period_date_missing':int((ds.isna()|de.isna()).sum()),
             'new_business':counts(df.new_business),'channel':counts(df.channel),
             'missing_customer_rows':int((~df.customer_id.isin(customers.customer_id)).sum()),
             'missing_address_rows':int((~df.address_id.isin(addresses.address_id)).sum()),
             'customers_not_in_training_share':float((~df.customer_id.isin(train.customer_id)).mean()) if kind=='test' else None,
             'policies_not_in_training_share':float((~df.policy_id.isin(train.policy_id)).mean()) if kind=='test' else None}
        row['annual']=[{'year':int(y),'rows':len(g),'exposure':float(g.exposure.sum())} for y,g in df.groupby(years)]
        if 'sum_insured' in df:
            numeric=pd.to_numeric(df.sum_insured,errors='coerce')
            row['sum_insured']={'non_numeric_non_null':int((numeric.isna()&df.sum_insured.notna()).sum()),'nonpositive':int((numeric<=0).sum()),'missing':int(numeric.isna().sum())}
        policy_summaries.append(row)

train=pd.concat(trains,ignore_index=True)
test=pd.concat(tests,ignore_index=True)
sample=frames['sample_submission']
result['policies']=policy_summaries
result['submission_contract']={'test_rows':len(test),'sample_rows':len(sample),'sample_columns':list(sample.columns),
    'unique_test_row_ids':int(test.row_id.nunique()),'unique_sample_row_ids':int(sample.row_id.nunique()),
    'sample_set_equals_test':set(test.row_id)==set(sample.row_id),
    'sample_order_equals_concatenated_tests':sample.row_id.tolist()==test.row_id.tolist(),
    'sample_predictions_finite_nonnegative':bool(np.isfinite(sample.prediction).all() and sample.prediction.ge(0).all()),
    'overlap_developed_sample_row_ids':len(set(sample.row_id)&set(pq.read_table(OLD/'sample_submission.parquet',columns=['row_id'])['row_id'].to_pylist()))}

claims=frames['claims']
net=pd.to_numeric(claims.incurred_to_date,errors='coerce')-pd.to_numeric(claims.recoveries,errors='coerce')
result['claims']={'rows':len(claims),'unique_ids':int(claims.claim_id.nunique()),'duplicate_id_rows':int(claims.claim_id.duplicated().sum()),
    'exact_duplicate_rows':int(claims.duplicated().sum()),'status':counts(claims.status),'line':counts(claims.line),'peril':counts(claims.peril),
    'report_before_loss':int((dates(claims,'report_date')<dates(claims,'loss_date')).sum()),
    'reports_after_valuation':int((dates(claims,'report_date')>pd.Timestamp('2024-12-31')).sum()),
    'incurred_below_paid':int((claims.incurred_to_date<claims.paid_to_date).sum()),
    'negative_net_incurred':int((net<0).sum()),'negative_paid':int((claims.paid_to_date<0).sum()),
    'negative_recoveries':int((claims.recoveries<0).sum()),
    'observed_net_incurred_all_rows':float(net.sum()),
    'warning':'Recuento descriptivo crudo, antes de resolver duplicados y asignación; no es el objetivo último.'}
claims2=claims.assign(_claim_position=np.arange(len(claims)))
joined=claims2.merge(train[['policy_id','line','row_id','period_start','period_end']],on=['policy_id','line'],how='left')
loss=dates(joined,'loss_date')
matches=joined[(loss>=dates(joined,'period_start'))&(loss<=dates(joined,'period_end'))]
assign=matches.groupby('_claim_position').size()
result['claim_assignment_raw']={'exactly_one':int((assign==1).sum()),'ambiguous':int((assign>1).sum()),'unmatched':len(claims)-len(assign),
    'unmatched_status':counts(claims2.loc[~claims2._claim_position.isin(assign.index),'status']),
    'warning':'Se inspeccionan filas originales, sin deduplicar y sin construir etiquetas.'}
result['claims']['by_line_year_status']=[{'line':str(k[0]),'year':int(k[1]),'status':str(k[2]),'rows':len(g),'net_incurred':float((g.incurred_to_date-g.recoveries).sum())} for k,g in claims.groupby(['line',dates(claims,'loss_date').dt.year,'status'])]
result['market_dimensions']={'regions':counts(addresses.region),'gender':counts(customers.gender),
    'occupations_distinct':int(customers.occupation.nunique()),'occupation_top25':{str(k):int(v) for k,v in customers.occupation.value_counts().head(25).items()},
    'construction_train':counts(frames['policies_buildings'].construction_type),'construction_test':counts(frames['test_buildings'].construction_type),
    'weather_years':counts(frames['weather'].year),'weather_duplicate_address_year':int(frames['weather'].duplicated(['address_id','year']).sum()),
    'cross_market_customer_id_overlap':len(set(customers.customer_id)&set(pq.read_table(OLD/'customers.parquet',columns=['customer_id'])['customer_id'].to_pylist())),
    'cross_market_address_id_overlap':len(set(addresses.address_id)&set(pq.read_table(OLD/'addresses.parquet',columns=['address_id'])['address_id'].to_pylist()))}
result['expenses']=frames['expenses'].astype(object).where(pd.notnull(frames['expenses']),None).to_dict(orient='records')
refs=frames['reference_policies']
result['reference_policies']={'rows':len(refs),'line':counts(refs.line),'unique_row_ids':int(refs.row_id.nunique()),
    'all_in_test':bool(refs.row_id.isin(test.row_id).all()),'columns':list(refs.columns)}
result['finished_utc']=datetime.now(timezone.utc).isoformat()
result['elapsed_seconds']=time.monotonic()-START
out=BASE/'diagnostico_inicial.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n',encoding='utf-8')
print(json.dumps({'output':str(out),'old_files_identical':sum(x['same_as_week1'] for x in result['local_originals']),
    'emerging_rows':{x['name']:x['rows'] for x in result['emerging_files']},'submission_contract':result['submission_contract'],
    'claims':{k:v for k,v in result['claims'].items() if k not in ['by_line_year_status','peril']},
    'assignment':result['claim_assignment_raw'],'expenses':result['expenses'],'seconds':result['elapsed_seconds']},ensure_ascii=True))
