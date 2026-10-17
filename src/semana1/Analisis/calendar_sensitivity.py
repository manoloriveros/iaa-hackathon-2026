"""Recalcula solo denominadores por fechas; preserva cálculos con exposición original."""
import json
from pathlib import Path
import sys
import numpy as np

import audit_data as audit
import pandas as pd

ROOT=audit.ROOT
BASE=Path(__file__).parent
OUT=ROOT/json.loads((BASE/'current_run.json').read_text(encoding='utf-8'))['run']
segments=pd.read_csv(OUT/'tables/segments.csv')
annual=pd.read_csv(OUT/'tables/annual_summary.csv')
customers,addresses,weather=map(audit.read,['customers','addresses','weather'])
annual['recorded_exposure']=annual.exposure
annual['recorded_cost_per_exposure']=annual.observed_cost_per_exposure
annual['recorded_reported_frequency']=annual.reported_frequency
segments['recorded_exposure']=segments.exposure
segments['recorded_cost_per_exposure']=segments.observed_cost_per_exposure
segments['recorded_reported_frequency']=segments.reported_frequency
for line in audit.LINES:
    frame=audit.read('policies_'+line)
    frame['year']=frame.period_start.dt.year
    frame['calendar_duration_365']=((frame.period_end-frame.period_start).dt.days+1)/365
    frame=frame.merge(customers,on='customer_id',how='left',validate='many_to_one').merge(
        addresses,on='address_id',how='left',validate='many_to_one').merge(
        weather,on=['address_id','year'],how='left',validate='many_to_one')
    frame['customer_age_from_dob']=np.floor((frame.period_start-frame.date_of_birth).dt.days/365.2425)
    frame['property_age']=frame.year-frame.year_built
    for year,group in frame.groupby('year'):
        mask=(annual.line==line)&(annual.year==year)
        annual.loc[mask,'exposure']=group.calendar_duration_365.sum()
    features=segments.loc[segments.line==line,'feature'].unique()
    for feature in features:
        s=frame[feature]
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s) and s.nunique()>12:
            levels=pd.qcut(s,8,duplicates='drop').astype('string').fillna('(faltante)')
        else:
            top=s.value_counts().head(15).index
            levels=s.astype('string').fillna('(faltante)').where(s.isin(top)|s.isna(),'(otros)')
        grouped=frame.calendar_duration_365.groupby(levels,observed=True).sum()
        mask=(segments.line==line)&(segments.feature==feature)
        denominators=segments.loc[mask,'level'].map(grouped)
        assert denominators.notna().all(),feature
        segments.loc[mask,'exposure']=denominators
    print('sensibilidad por fechas '+line,flush=True)
annual['observed_cost_per_exposure']=annual.net_incurred/annual.exposure
annual['reported_frequency']=annual.reported_accepted_claims/annual.exposure
segments['observed_cost_per_exposure']=segments.cost/segments.exposure
segments['reported_frequency']=segments.claims/segments.exposure
annual.to_csv(OUT/'tables/annual_summary_date365.csv',index=False)
segments.to_csv(OUT/'tables/segments_date365.csv',index=False)
(OUT/'denominator_method.json').write_text(json.dumps({'method':'inclusive_date_duration_divided_by_365',
 'status':'diagnostic_sensitivity_not_approved_repair','reason':'Dominant observed convention is ACT365; recorded data also contain day amounts and ACT360 values.',
 'original_denominator_tables':['tables/annual_summary.csv','tables/segments.csv'],
 'date_denominator_tables':['tables/annual_summary_date365.csv','tables/segments_date365.csv'],
 'sources_modified':False,'claims_costs_modified':False},ensure_ascii=False,indent=2),encoding='utf-8')
