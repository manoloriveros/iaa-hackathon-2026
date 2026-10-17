"""Contrastes dirigidos por incidencias descubiertas; conserva originales y evidencia."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd

BASE=Path(__file__).parent
OUT=ROOT/json.loads((BASE/'current_run.json').read_text(encoding='utf-8'))['run']
DATA=ROOT/'Hackaton/Semana 1/Datos'
exposures=[]; capital=[]; examples=[]; domains=[]
for line in ['motor','buildings','contents']:
    for prefix in ['policies_','test_']:
        name=prefix+line
        cols=['row_id','policy_id','period_start','period_end','exposure']
        if line!='motor': cols+=['sum_insured']
        if line=='buildings': cols+=['construction_type']
        frame=pd.read_parquet(DATA/(name+'.parquet'),columns=cols)
        frame.period_start=pd.to_datetime(frame.period_start)
        frame.period_end=pd.to_datetime(frame.period_end)
        days=(frame.period_end-frame.period_start).dt.days+1
        calendar=days/np.where(frame.period_start.dt.is_leap_year,366,365)
        versions={'ACT365':days/365,'ACT360':days/360,'ACT_actual_year':calendar,'days_not_years':days}
        for year,idx in frame.groupby(frame.period_start.dt.year).groups.items():
            rec={'table':name,'year':int(year),'rows':len(idx),
                 'raw_exposure':float(frame.loc[idx,'exposure'].sum()),
                 'calendar_exposure':float(calendar.loc[idx].sum()),
                 'greater_than_1':int((frame.loc[idx,'exposure']>1).sum())}
            for key,v in versions.items():
                rec[key+'_matches']=int(((frame.loc[idx,'exposure']-v.loc[idx]).abs()<.000051).sum())
            rec['raw_to_calendar_ratio']=rec['raw_exposure']/rec['calendar_exposure']
            exposures.append(rec)
        if line!='motor':
            med=frame.groupby('policy_id').sum_insured.transform('median')
            ratio=frame.sum_insured/med
            near_1000=(ratio.between(900,1100))
            extreme=frame.sum_insured> (1e7 if line=='buildings' else 1e6)
            capital.append({'table':name,'rows':len(frame),'median':float(frame.sum_insured.median()),
                            'p99':float(frame.sum_insured.quantile(.99)),'max':float(frame.sum_insured.max()),
                            'above_screening_amount':int(extreme.sum()),
                            'screening_amount':1e7 if line=='buildings' else 1e6,
                            'near_1000_times_within_policy_median':int(near_1000.sum())})
            for idx,row in frame.loc[near_1000|extreme].head(8).iterrows():
                examples.append({'table':name,'row_id':row.row_id,'policy_id':row.policy_id,
                                 'value':row.sum_insured,'within_policy_median':med.loc[idx],
                                 'ratio':ratio.loc[idx]})
        if 'construction_type' in frame:
            raw=frame.construction_type.astype('string')
            canonical=raw.str.strip().str.casefold().str.replace(r'[ -]+','_',regex=True)
            known=canonical.isin(['brick','stone','timber','non_standard'])
            for (raw_value,canon),n in pd.DataFrame({'raw':raw,'canonical':canonical}).value_counts().items():
                domains.append({'table':name,'raw':raw_value,'canonical_proposed':canon,'rows':int(n),
                                'canonical_in_dictionary':canon in ['brick','stone','timber','non_standard']})
pd.DataFrame(exposures).to_csv(OUT/'tables/exposure_conventions.csv',index=False)
pd.DataFrame(capital).to_csv(OUT/'tables/capital_scale_diagnostics.csv',index=False)
pd.DataFrame(examples).to_csv(OUT/'tables/capital_scale_examples.csv',index=False)
pd.DataFrame(domains).to_csv(OUT/'tables/construction_dictionary.csv',index=False)
(OUT/'additional_checks.json').write_text(json.dumps({'exposure':exposures,'capital':capital,
    'notes':['Conventions may overlap for particular durations; match counts are not mutually exclusive.',
             'A factor near 1000 suggests a unit issue but is not an approved correction.',
             'Calendar exposure is a transparent sensitivity scenario, not an organizer-approved replacement.']},
    ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'capital':capital,'exposure':exposures},ensure_ascii=True),flush=True)
