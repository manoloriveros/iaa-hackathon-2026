"""108 capitales sin referencia habitual original: revisión sin transformación de datos."""
from datetime import datetime,timezone
from pathlib import Path
import json
import shutil
import sys
import uuid
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import correct_capitals as cap
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

BASE=Path(__file__).parent
D48=ROOT/'Hackaton/Semana 1/Revision_capitales_pendientes/runs/pending_20261016T212234Z_3c7bd248'
GROUP='C_no_original_normal_reference'
THRESHOLDS={'buildings':10_000_000,'contents':1_000_000}
REQUEST='Ahora revisemos los 108 capitales sin referencia original habitual. Compara sus historiales, muestra casos concretos y propón cómo tratarlos sin modificar los datos todavía.'

def save(frame,out,name):
    frame.to_parquet(out/'tables'/(name+'.parquet'),index=False)
    frame.to_csv(out/'tables'/(name+'.csv'),index=False)

def main():
    index=c.BASE/'current_retrospective_dataset.json';pointer=json.loads(index.read_text('utf-8'))
    parent=ROOT/pointer['workspace_relative_run'];catpath=ROOT/pointer['catalog_workspace_relative'];catalog=json.loads(catpath.read_text('utf-8'))
    assert pointer['capital_rule']=='CAP04R' and cap.manifest_ok(parent) and cap.manifest_ok(D48)
    pending=pd.read_parquet(parent/'tables/pending_capitals.parquet');cohort=pending.loc[pending.review_group.eq(GROUP)].copy()
    assert len(pending)==467 and len(cohort)==cohort.row_id.nunique()==108 and cohort.policy_id.nunique()==107
    out=BASE/'runs'/(datetime.now(timezone.utc).strftime('noanchor_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['tables','evidence','source_snapshot','figures']:(out/name).mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']:e['sha256'] for e in catalog.values()})
    for p in [index,c.BASE/'current_dataset.json',catpath,parent/'manifest.json',D48/'manifest.json',parent/'tables/pending_capitals.parquet',
        c.BASE/'current_context_capital_correction.json',ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json']:
        protected[p.relative_to(ROOT).as_posix()]=c.digest(p)
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items());c.dump(out/'protected_hashes_before.json',protected)
    copies={'retrospective_index.json':index,'base_index.json':c.BASE/'current_dataset.json','dataset_catalog.json':catpath,
        'CAP04R_manifest.json':parent/'manifest.json','D48_manifest.json':D48/'manifest.json',
        'frozen_467_pending.parquet':parent/'tables/pending_capitals.parquet','D48_assessment.parquet':D48/'tables/pending_assessment.parquet',
        'data-description.md':ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'}
    for name,p in copies.items():shutil.copy2(p,out/'evidence'/name)
    shutil.copy2(__file__,out/'source_snapshot'/Path(__file__).name)
    c.dump(out/'request.json',{'messages':[{'role':'user','content':REQUEST}],'scope':'Exact 108 frozen D48 group C rows on CAP04R, review only. No values, dataset indexes or protocol modified.'})
    save(cohort,out,'frozen_108_cohort');save(pending,out,'remaining_467_inventory');save(pending.loc[~pending.row_id.isin(cohort.row_id)],out,'other_359_inventory')
    pieces=[]
    for line in ['buildings','contents']:
        for prefix in ['policies','test']:
            name=prefix+'_'+line;frame=pq.read_table(ROOT/catalog[name]['workspace_relative_path']).to_pandas()
            frame['source_table']=name;frame['line']=line
            for col in ['period_start','period_end']:frame[col]=pd.to_datetime(frame[col]).dt.as_unit('ns')
            raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured']).to_pandas().set_index('row_id').sum_insured
            frame['original_capital_CU']=frame.row_id.map(raw)
            frame['year']=frame.period_start.dt.year;frame['covered_days']=(frame.period_end-frame.period_start).dt.days+1
            pieces.append(frame)
    allpol=pd.concat(pieces,ignore_index=True)
    history=allpol.loc[allpol.policy_id.isin(cohort.policy_id)].sort_values(['policy_id','period_start','row_id']).reset_index(drop=True)
    history['focus_108']=history.row_id.isin(cohort.row_id);history['pending_467']=history.row_id.isin(pending.row_id)
    assert len(history)==108 and history.focus_108.all() and (history.original_capital_CU==history.sum_insured).all()
    save(history,out,'all_policy_histories')
    others=allpol.loc[~allpol.policy_id.isin(cohort.policy_id)]
    linked=others.loc[others.address_id.isin(history.address_id)|others.customer_id.isin(history.customer_id)]
    linked_full=others.loc[others.policy_id.isin(linked.policy_id)].sort_values(['policy_id','period_start','row_id']).reset_index(drop=True)
    save(linked_full,out,'all_linked_policy_histories')
    pairs=[]
    for row in history.itertuples():
        for peer in linked_full.loc[linked_full.address_id.eq(row.address_id)|linked_full.customer_id.eq(row.customer_id)].itertuples():
            pairs.append({'focus_row_id':row.row_id,'focus_policy_id':row.policy_id,'peer_row_id':peer.row_id,'peer_policy_id':peer.policy_id,
                'focus_line':row.line,'peer_line':peer.line,'same_line':row.line==peer.line,'same_customer':row.customer_id==peer.customer_id,
                'same_address':row.address_id==peer.address_id,'same_interval':row.period_start==peer.period_start and row.period_end==peer.period_end,
                'peer_source_table':peer.source_table,'peer_period_start':peer.period_start,'peer_period_end':peer.period_end,
                'peer_capital_CU':float(peer.sum_insured),'peer_original_capital_CU':float(peer.original_capital_CU),
                'focus_capital_CU':float(row.sum_insured),'focus_hypothetical_div1000_CU':float(row.sum_insured/1000)})
    links=pd.DataFrame(pairs);save(links,out,'linked_comparisons')
    addresses=pq.read_table(ROOT/catalog['addresses']['workspace_relative_path']).to_pandas()
    save(addresses.loc[addresses.address_id.isin(pd.concat([history.address_id,linked_full.address_id]))],out,'address_context')
    # Descriptive peers selected without outcomes, premiums, or requiring a favorable /1000 value.
    normal=others.loc[others.original_capital_CU.gt(0)&others.original_capital_CU.eq(others.sum_insured)&
        others.original_capital_CU.le(others.line.map(THRESHOLDS))].copy()
    keys=history[['source_table','year','new_business']].drop_duplicates()
    peers=normal.merge(keys,on=['source_table','year','new_business'],how='inner',validate='many_to_one')
    peercols=['row_id','policy_id','customer_id','address_id','source_table','line','year','new_business','period_start','period_end',
        'original_capital_CU','sum_insured','written_premium','exposure','covered_days']
    save(peers[peercols],out,'descriptive_peer_population')
    bands=[]
    for key,g in peers.groupby(['source_table','year','new_business'],dropna=False,sort=True):
        v=g.original_capital_CU
        bands.append({'source_table':key[0],'year':int(key[1]),'new_business':bool(key[2]),'rows':len(g),'policies':g.policy_id.nunique(),
            **{'capital_'+label:float(v.quantile(q)) for label,q in [('min',0),('p01',.01),('p05',.05),('p50',.5),('p95',.95),('p99',.99),('max',1)]}})
    bandframe=pd.DataFrame(bands);save(bandframe,out,'peer_bands')
    assessments=[]
    for row in history.itertuples():
        own=history.loc[history.policy_id.eq(row.policy_id)];rels=links.loc[links.focus_row_id.eq(row.row_id)]
        cross=rels.loc[~rels.same_line&rels.same_customer&rels.same_address]
        address_only=rels.loc[rels.same_address&~rels.same_customer]
        peer=peers.loc[peers.source_table.eq(row.source_table)&peers.year.eq(row.year)&peers.new_business.eq(row.new_business)]
        v=np.sort(peer.original_capital_CU.to_numpy());hyp=row.sum_insured/1000
        missing=[col for col in cap.FIELDS[row.line] if pd.isna(getattr(row,col))]
        group='A_two_high_periods' if len(own)>1 else ('B_singleton_crossline_same_customer' if len(cross) else ('C_address_only_other_customer' if len(address_only) else 'D_singleton_no_household_link'))
        rec=row._asdict();rec.pop('Index',None)
        rec.update({'hypothetical_div1000_CU':float(hyp),'history_rows':len(own),'original_normal_reference_rows':int(own.original_capital_CU.le(THRESHOLDS[row.line]).sum()),
            'same_line_same_customer_peer_rows':int((rels.same_line&rels.same_customer&rels.same_address).sum()),
            'crossline_same_customer_address_peer_rows':len(cross),'crossline_same_interval_peer_rows':int(cross.same_interval.sum()),
            'address_only_other_customer_peer_rows':len(address_only),'review_group':group,'context_missing_fields':'|'.join(missing),
            'peer_population_rows':len(v),'peer_original_percentile':float(100*np.searchsorted(v,row.sum_insured,side='right')/len(v)),
            'peer_hypothetical_percentile':float(100*np.searchsorted(v,hyp,side='right')/len(v)),
            'peer_min_CU':float(v[0]),'peer_max_CU':float(v[-1]),'hypothetical_inside_peer_range':bool(v[0]<=hyp<=v[-1]),
            'raw_capital_over_peer_max':float(row.sum_insured/v[-1]),'all_policy_rows_pending':bool(own.pending_467.all()),
            'proposed_action':'KEEP_PENDING_NO_AUTOMATIC_SCALE_REPAIR','hypothesis_only':True,'capital_change_applied':False,
            'correction_authorized':False,'eligible_for_prior_original_anchor_rule':False})
        assessments.append(rec)
    assessment=pd.DataFrame(assessments);save(assessment,out,'noanchor_assessment')
    plan=assessment[['row_id','policy_id','source_table','line','sum_insured','hypothetical_div1000_CU','review_group',
        'context_missing_fields','proposed_action','hypothesis_only','capital_change_applied','correction_authorized']].copy()
    save(plan,out,'proposed_treatment_NOT_APPLIED')
    claims=pq.read_table(ROOT/catalog['claims']['workspace_relative_path']).to_pandas()
    ownclaims=claims.loc[claims.policy_id.isin(history.policy_id)].copy();relatedclaims=claims.loc[claims.policy_id.isin(linked_full.policy_id)].copy()
    save(ownclaims,out,'all_claim_histories');save(relatedclaims,out,'linked_claim_histories')
    counts=assessment.groupby(['review_group','line']).agg(rows=('row_id','size'),policies=('policy_id','nunique')).reset_index();save(counts,out,'group_counts')
    summary={'rows':108,'policies':107,'by_line':assessment.line.value_counts().to_dict(),'by_source':assessment.source_table.value_counts().to_dict(),
        'history_rows':len(history),'history_lengths':history.groupby('policy_id').size().value_counts().to_dict(),
        'years':assessment.year.value_counts().to_dict(),'group_rows':assessment.review_group.value_counts().to_dict(),
        'own_claims':len(ownclaims),'linked_policy_rows':len(linked_full),'linked_policies':linked_full.policy_id.nunique(),'linked_claims':len(relatedclaims),
        'linked_comparison_rows':len(links),'same_line_same_customer_reference_rows':int((links.same_line&links.same_customer&links.same_address).sum()),
        'focus_rows_with_crossline_same_customer_address':int(assessment.crossline_same_customer_address_peer_rows.gt(0).sum()),
        'focus_rows_with_same_interval_crossline':int(assessment.crossline_same_interval_peer_rows.gt(0).sum()),
        'missing_context_rows':int(assessment.context_missing_fields.ne('').sum()),'descriptive_peer_population_rows':len(peers),
        'hypothetical_inside_own_peer_range':int(assessment.hypothetical_inside_peer_range.sum()),
        'automatic_repair_candidates':0,'keep_pending':108,'retrospective_pending_unchanged':467,'other_pending_not_adjudicated':359,
        'base_pending_unchanged':1454,'values_changed':0,'dataset_indexes_changed':False,'models_trained':False,'independent_validation':False}
    c.dump(out/'summary.json',summary)
    c.dump(out/'proposal.json',{'status':'review_only_no_application_authorization','recommendation':'Keep all 108 unresolved; no automatic capital correction from this evidence.',
        'reason':'No original ordinary anchor in the same policy and no other same-line/same-customer/same-address reference. Distributional plausibility and a different coverage line do not identify a contractual limit.',
        'two_high_periods':'B67263929: 435000000 in 2024 and 448000000 in 2025; dividing both preserves the same 2.9885% growth and cannot identify their scale.',
        'paired_coverage':'Buildings insure the structure; contents insure goods. Never copy or force equal limits across these coverages.',
        'address_only':'Different customer at the same address may insure different goods or periods. No ID merge or capital substitution.',
        'sensitivity':'If subsequently authorized, preserve raw values and compare a separate /1000 hypothesis or model-input missing-capital variant. Do not implement a predictor or scenario data layer now.',
        'test_scope':'107 focus rows are test2025, not 107 test anchors supporting a correction. Keep every row and submission ID; no dropping or zeroing targets/predictions.',
        'source_confirmation_needed':['Currency serialization/unit per field','Contract schedule or original unscaled limit for these exact rows','Whether both B67263929 periods share a serialization issue'],
        'IAA':['Documentation §2 and §§4–6','Governance §2.8','Professional considerations §3.2 and §§3.5–3.6']})
    c.dump(out/'protocol.json',{'cohort':'Exact frozen D48 group C still pending in CAP04R; not a re-screened selection.',
        'screen_thresholds_CU':THRESHOLDS,'threshold_role':'Historical anomaly screening only, not legal/contractual maximum or truth label.',
        'history':'All periods of the 107 policies across four current household tables, original capitals separately read.',
        'peers':'All other policies, original=current positive capital below historical screening threshold; same source table/year/new_business. No outcome/premium/favorable-hypothesis filtering. Repeated policies are not independent evidence.',
        'links':'All other household policies sharing any cohort address or customer; full histories retained. Rows compared by exact address/customer/line/interval, no inferred ID merge.',
        'arithmetic':'/1000 hypothetical only, no data transformation or repair list authorized.',
        'master':'Address attributes have no historical effective dates; context only.',
        'no_target_or_premium_selection':True,'no_original_derived_or_index_changes':True})
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    print(json.dumps({'run':str(out),'summary':summary},ensure_ascii=False))

if __name__=='__main__':main()
