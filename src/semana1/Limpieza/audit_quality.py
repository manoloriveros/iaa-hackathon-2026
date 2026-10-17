"""Controles multitabla y diagnóstico semántico, sin imputación ni entrenamiento."""
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import clean_data as c

DOMAINS={
 'marital_status':'single married divorced widowed','credit_band':'A B C D E','document_preference':'email post app',
 'region':'R01 R02 R03 R04 R05 R06 R07 R08 R09 R10 R11 R12','urban_density':'rural suburban urban dense_urban',
 'soil_type':'clay sand loam chalk rock','property_type':'detached semi_detached terraced flat',
 'roof_type':'pitched flat','energy_rating':'A B C D E F G','channel':'direct comparison_site broker',
 'payment_method':'annual monthly','renewal_decision':'renewed lapsed_by_customer cancelled declined_by_insurer mid_term_change',
 'body_type':'hatchback saloon estate suv coupe','transmission':'manual automatic',
 'fuel_type':'petrol diesel hybrid electric','cover_type':'comprehensive third_party_fire_theft third_party_only',
 'overnight_parking':'garage driveway street','vehicle_use':'social commuting business',
 'construction_type':'brick stone timber non_standard','occupancy':'owner_occupied let','tenure':'owner renter',
 'security_level':'standard locks alarm_and_locks','line':'motor buildings contents','status':'closed open repudiated'}
BOUNDS={'flood_zone':(1,5),'wind_exposure_index':(0,10),'dry_summer_index':(0,1),'wildfire_index':(0,1),
 'vehicle_value_group':(1,20),'telematics_score':(1,100)}
NONNEG='household_size prior_claims_5y licence_points years_at_address distance_to_river_km bedrooms hail_days freezing_days rainfall_mm driver_age years_licensed ncb_years vehicle_age engine_size_cc seats annual_mileage voluntary_excess compulsory_excess missed_payments_12m renewal_count days_quote_to_inception customer_service_contacts policyholder_age sum_insured days_unoccupied high_value_items paid_to_date incurred_to_date recoveries'.split()
COUNTS='household_size prior_claims_5y licence_points bedrooms hail_days freezing_days driver_age years_licensed ncb_years seats missed_payments_12m renewal_count customer_service_contacts policyholder_age high_value_items'.split()
PERILS={'motor':'own_damage third_party_prop bodily_injury theft glass_hail',
 'buildings':'storm flood escape_of_water subsidence fire accidental_damage','contents':'theft escape_of_water accidental_damage flood'}


def audit(catalog,out):
    checks=[];missing=[];profiles=[];core={};tele=[];exceptions=[];age_stats=[];construction=[]
    customers=pq.read_table(c.ROOT/catalog['customers']['workspace_relative_path']).to_pandas()
    addresses=pq.read_table(c.ROOT/catalog['addresses']['workspace_relative_path']).to_pandas()
    customer_ids=set(customers.customer_id);address_ids=set(addresses.address_id)
    dob=customers.set_index('customer_id').date_of_birth
    acquisition=customers.set_index('customer_id').customer_since_year
    built=addresses.set_index('address_id').year_built
    def add(table,rule,affected,rows,severity='strict',note=''):
        checks.append({'table':table,'rule':rule,'affected':int(affected),'rows':int(rows),
                       'severity':severity,'passed':int(affected)==0,'note':note})
    total_rows=0
    for name,e in catalog.items():
        f=pq.read_table(c.ROOT/e['workspace_relative_path']).to_pandas();n=len(f);total_rows+=n
        for col in f:
            s=f[col];count=int(s.isna().sum())
            profiles.append({'table':name,'column':col,'dtype':str(s.dtype),'rows':n,'missing':count,'distinct':int(s.nunique())})
            if count:missing.append({'table':name,'column':col,'missing':count,'rows':n,'fraction':count/n,'action':'preserve_null_no_imputation'})
            if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
                add(name,'finite_'+col,np.isinf(s.to_numpy(dtype=float)).sum(),n)
                if col in NONNEG:add(name,'nonnegative_'+col,(s.dropna()<0).sum(),n)
                if col in BOUNDS:
                    lo,hi=BOUNDS[col];add(name,'dictionary_range_'+col,(~s.dropna().between(lo,hi)).sum(),n)
                if col in COUNTS:add(name,'integer_count_'+col,(s.dropna()%1!=0).sum(),n)
            if col in DOMAINS:
                bad=s.notna()&~s.isin(DOMAINS[col].split())
                add(name,'dictionary_vocabulary_'+col,bad.sum(),n,'review' if col=='construction_type' else 'strict',
                    't/w retained as undefined codes; case normalization does not resolve material.' if col=='construction_type' else '')
        if name=='weather':
            add(name,'unique_address_year',f.duplicated(['address_id','year']).sum(),n)
            add(name,'weather_address_master',(~f.address_id.isin(address_ids)).sum(),n)
            add(name,'weather_year_2021_2025',(~f.year.between(2021,2025)).sum(),n)
            complete=n==len(address_ids)*5 and not f.duplicated(['address_id','year']).any() and f.address_id.isin(address_ids).all() and f.year.between(2021,2025).all()
            add(name,'complete_address_year_cartesian',0 if complete else 1,n)
        else:
            key='row_id' if name in c.TABLES or name=='sample_submission' else {'customers':'customer_id','addresses':'address_id','claims':'claim_id'}[name]
            add(name,'unique_'+key,f[key].duplicated().sum(),n);add(name,'nonnull_'+key,f[key].isna().sum(),n)
        if name in c.TABLES:
            start,end=pd.to_datetime(f.period_start),pd.to_datetime(f.period_end)
            add(name,'customer_master_join',(~f.customer_id.isin(customer_ids)).sum(),n)
            add(name,'address_master_join',(~f.address_id.isin(address_ids)).sum(),n)
            add(name,'valid_covered_dates',(start.isna()|end.isna()|(end<start)).sum(),n)
            expected=((end-start).dt.days+1)/365
            add(name,'exposure_ACT365_4dec',f.exposure.ne(expected.round(4)).sum(),n)
            add(name,'policy_year_in_weather',(~start.dt.year.between(2021,2025)).sum(),n)
            add(name,'new_business_matches_renewal_zero',f.new_business.ne(f.renewal_count.eq(0)).sum(),n)
            add(name,'customer_acquired_after_policy_year',f.customer_id.map(acquisition).gt(start.dt.year).sum(),n,'review')
            if 'policyholder_age'in f:
                birth=pd.to_datetime(f.customer_id.map(dob));ages=start.dt.year-birth.dt.year-((start.dt.month<birth.dt.month)|((start.dt.month==birth.dt.month)&(start.dt.day<birth.dt.day))).astype(int)
                add(name,'policyholder_age_completed_years',f.policyholder_age.ne(ages).sum(),n)
                age_stats.append({'table':name,'rows':n,'post_refinement_mismatches':int(f.policyholder_age.ne(ages).sum())})
                add(name,'property_built_after_policy_start_year',f.address_id.map(built).gt(start.dt.year).sum(),n,'review')
            if 'ncb_years'in f:
                mask=f.ncb_years.gt(f.years_licensed)
                add(name,'NCB_greater_than_license_tenure',mask.sum(),n,'review','Definition/carry-over needs review; no cap or replacement.')
                exceptions.append(f.loc[mask,['row_id','policy_id','driver_age','years_licensed','ncb_years']].assign(source_table=name,issue='NCB_gt_license_preserved'))
                add(name,'license_tenure_greater_than_driver_age',f.years_licensed.gt(f.driver_age).sum(),n)
                bad=(f.telematics_opt_in&f.telematics_score.isna())|(~f.telematics_opt_in&f.telematics_score.notna())
                add(name,'telematics_score_applicability',bad.sum(),n)
                tele.append({'table':name,'rows':n,'score_missing':int(f.telematics_score.isna().sum()),'opted_out':int((~f.telematics_opt_in).sum()),'inconsistencies':int(bad.sum())})
            cols=['row_id','policy_id','customer_id','address_id','period_start','period_end','exposure']
            core[name]=f[cols].assign(period_start=start,period_end=end)
            if 'construction_type'in f:construction.append(f[['row_id','policy_id','address_id','construction_type']].assign(period_start=start,period_end=end,year=start.dt.year,source_table=name))
        if name=='claims':
            claims=f.copy();claims['loss_date']=pd.to_datetime(claims.loss_date);claims['report_date']=pd.to_datetime(claims.report_date)
            add(name,'report_before_loss',claims.report_date.lt(claims.loss_date).sum(),n)
            add(name,'report_after_valuation',claims.report_date.gt(pd.Timestamp('2024-12-31')).sum(),n)
            add(name,'loss_after_valuation',claims.loss_date.gt(pd.Timestamp('2024-12-31')).sum(),n)
            add(name,'incurred_below_paid',claims.incurred_to_date.lt(claims.paid_to_date).sum(),n)
            accepted=claims.status.isin(['open','closed']);net=claims.incurred_to_date-claims.recoveries
            add(name,'accepted_negative_observed_net',int((accepted&net.lt(0)).sum()),n)
            for line,perils in PERILS.items():add(name,'perils_'+line,int((claims.line.eq(line)&~claims.peril.isin(perils.split())).sum()),n)
        if name=='sample_submission':sample_ids=set(f.row_id)
        print('audit '+name,flush=True)
    for line in ['motor','buildings','contents']:
        combined=pd.concat([core['policies_'+line],core['test_'+line]],ignore_index=True).sort_values(['policy_id','period_start','period_end'])
        prev=combined.groupby('policy_id').period_end.shift()
        add(line,'overlapping_policy_periods',combined.period_start.le(prev).sum(),len(combined))
    all_test=pd.concat([core['test_'+line].row_id for line in ['motor','buildings','contents']],ignore_index=True)
    add('test','duplicate_ids_across_lines',all_test.duplicated().sum(),len(all_test))
    add('test','sample_id_coverage_symmetric_difference',len(set(all_test)^sample_ids),len(all_test))
    assignments=[]
    for line in ['motor','buildings','contents']:
        q=claims[claims.line.eq(line)].copy();p=core['policies_'+line]
        joined=q[['claim_id','policy_id','loss_date']].merge(p[['policy_id','row_id','period_start','period_end']],on='policy_id',how='left')
        valid=joined.loss_date.between(joined.period_start,joined.period_end)
        hits=joined[valid][['claim_id','row_id']]
        add(line,'claims_multiple_covering_periods',hits.claim_id.duplicated().sum(),len(q))
        assert hits.claim_id.is_unique
        result=q[['claim_id','policy_id','line','loss_date','status']].merge(hits,on='claim_id',how='left',validate='one_to_one')
        first=p.groupby('policy_id').period_start.min();unmatched=result.row_id.isna()
        before=result.loss_date.lt(result.policy_id.map(first))
        result['assignment_status']=np.where(~unmatched,'unique_period',np.where(before,'before_first_observed_period','unresolved_other'))
        add(line,'claims_unmatched_other_than_before_first',int((unmatched&~before).sum()),len(q))
        add(line,'claims_before_first_observed_period',int((unmatched&before).sum()),len(q),'review','Preserve event date; do not force into first policy period.')
        assignments.append(result)
    assignments=pd.concat(assignments,ignore_index=True);assignments.to_parquet(out/'tables/claim_period_audit.parquet',index=False)
    assignments[assignments.row_id.isna()].to_csv(out/'tables/claims_before_observed_history.csv',index=False)
    con=pd.concat(construction,ignore_index=True).sort_values(['policy_id','period_start','period_end'])
    con['prior_code']=con.groupby('policy_id').construction_type.shift();con['prior_address']=con.groupby('policy_id').address_id.shift()
    same=con.address_id.eq(con.prior_address)&con.prior_code.notna()
    transitions=con.loc[same].groupby(['prior_code','construction_type']).size().rename('rows').reset_index()
    transitions.to_csv(out/'tables/construction_transitions.csv',index=False)
    con.groupby(['year','construction_type']).size().rename('rows').reset_index().to_csv(out/'tables/construction_by_year.csv',index=False)
    con[con.construction_type.isin(['t','w'])].to_parquet(out/'tables/unresolved_construction_codes.parquet',index=False)
    con.loc[same&con.prior_code.ne(con.construction_type)].head(30).to_csv(out/'tables/construction_transition_examples.csv',index=False)
    pd.concat(exceptions,ignore_index=True).to_parquet(out/'tables/NCB_review.parquet',index=False)
    pd.DataFrame(missing).to_csv(out/'tables/missingness.csv',index=False)
    pd.DataFrame(profiles).to_csv(out/'tables/column_profiles.csv',index=False)
    pd.DataFrame(checks).to_csv(out/'tables/quality_checks.csv',index=False)
    pd.DataFrame(tele).to_csv(out/'tables/telematics_applicability.csv',index=False)
    summary={'tables':len(catalog),'rows_profiled':total_rows,'checks':len(checks),
        'strict_failures':[x for x in checks if x['severity']=='strict' and not x['passed']],
        'review_findings':[x for x in checks if x['severity']=='review' and not x['passed']],
        'age_reconciliation':age_stats,'unresolved_construction_rows':int(con.construction_type.isin(['t','w']).sum()),
        'same_address_t_to_w_transitions':int((same&con.prior_code.eq('t')&con.construction_type.eq('w')).sum()),
        'claims_before_observed_history':int(assignments.row_id.isna().sum()),'NCB_review_rows':int(sum(len(x) for x in exceptions)),
        'missing_values_imputed':0,'additional_capital_changes':0,'ultimate_target_constructed':False}
    c.dump(out/'quality_summary.json',summary)
    assert not summary['strict_failures'],summary['strict_failures']
