"""Comprobaciones propias de fuentes, cohorte, pares y propuesta; no aplica reglas."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import sys

import review_pending as r
import clean_data as c
import pandas as pd
import numpy as np
import pyarrow.parquet as pq


def normalize_dates(frame):
    result=frame.copy()
    for col in ['period_start','period_end','loss_date','report_date']:
        if col in result:result[col]=pd.to_datetime(result[col]).dt.as_unit('ns')
    return result


def main(out):
    if (out/'manifest.json').exists():
        assert r.cap.manifest_ok(out);print(json.dumps({'status':'closed_verified_manifest_intact_no_rewrite'}));return
    checks=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    f=pd.read_parquet(out/'tables/pending_assessment.parquet');h=pd.read_parquet(out/'tables/all_affected_policy_histories.parquet')
    cl=pd.read_parquet(out/'tables/claim_assignment_and_capital_diagnostic.parquet')
    refs=pd.read_parquet(out/'tables/all_original_normal_references.parquet')
    frozen=pd.read_parquet(out/'evidence/frozen_pending_capitals.parquet')
    cat=json.loads((out/'evidence/dataset_catalog.json').read_text('utf-8'))
    summary=json.loads((out/'summary.json').read_text('utf-8'))
    check('Exact 1454 frozen row IDs, no expansion',len(f)==f.row_id.nunique()==1454 and set(f.row_id)==set(frozen.row_id))
    check('1452 policies, 691 buildings and 763 contents',f.policy_id.nunique()==1452 and f.line.value_counts().to_dict()=={'contents':763,'buildings':691})
    check('Frozen original amounts exactly retained in assessment',f.set_index('row_id').sum_insured.sort_index().equals(frozen.set_index('row_id').sum_insured.sort_index()))
    check('All hypothesis amounts exactly capital/1000, never applied',np.array_equal(f.what_if_div1000_CU.to_numpy(),f.sum_insured.to_numpy()/1000) and not f.capital_change_applied.any() and not f.correction_authorized.any())
    check('Every frozen pending row appears once in complete histories',h.loc[h.pending_frozen].row_id.is_unique and set(h.loc[h.pending_frozen,'row_id'])==set(f.row_id))
    check('5587 unique complete history rows',len(h)==h.row_id.nunique()==5587)
    source_hist=[]
    for line in ['buildings','contents']:
        wanted=set(f.loc[f.line.eq(line),'policy_id'])
        for prefix in ['policies','test']:
            name=prefix+'_'+line;table=pq.read_table(c.ROOT/cat[name]['workspace_relative_path'])
            source=table.to_pandas();source=source.loc[source.policy_id.isin(wanted)]
            subset=h.loc[h.source_table.eq(name),table.column_names]
            pd.testing.assert_frame_equal(normalize_dates(source).sort_values('row_id').reset_index(drop=True),
                normalize_dates(subset).sort_values('row_id').reset_index(drop=True),check_dtype=False,check_exact=True)
            check(name+': complete source rows and every field preserved in analytical history',True)
            raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured']).to_pandas().set_index('row_id')
            check(name+': original capital traces agree exactly',np.array_equal(h.loc[h.source_table.eq(name),'original_sum_insured_CU'].to_numpy(),h.loc[h.source_table.eq(name),'row_id'].map(raw.sum_insured).to_numpy()))
            source_hist.append(normalize_dates(source))
    fixed=pd.read_parquet(out/'evidence/CAP01_ledger.parquet')
    check('No pending row is in the already applied 2073-row CAP01 cohort',len(fixed)==2073 and not set(f.row_id)&set(fixed.row_id))
    check('CAP01 dependence distinguished from original references',h.cap01_applied.equals(h.row_id.isin(fixed.row_id)) and
          np.array_equal(h.sum_insured.to_numpy(),np.where(h.cap01_applied,h.original_sum_insured_CU/1000,h.original_sum_insured_CU)))
    policy_groups={pid:g.sort_values('period_start') for pid,g in h.groupby('policy_id')}
    nearest_errors=[];all_ref_errors=[];pair_errors=[];actual_prior_support=actual_later_support=0
    for _,row in f.iterrows():
        group=policy_groups[row.policy_id]
        normal=group.loc[~group.extreme_screen&~group.cap01_applied]
        for direction in ['prior','later']:
            options=normal.loc[normal.period_start.lt(row.period_start)] if direction=='prior' else normal.loc[normal.period_start.gt(row.period_start)]
            actual=refs.loc[refs.pending_row_id.eq(row.row_id)&refs.direction.eq(direction)]
            if set(options.row_id)!=set(actual.row_id):all_ref_errors.append(row.row_id)
            exists=bool(row['original_'+direction+'_exists'])
            if bool(len(options))!=exists:nearest_errors.append(row.row_id)
            if not exists:continue
            nearest=options.iloc[-1 if direction=='prior' else 0]
            if row['original_'+direction+'_row_id']!=nearest.row_id:nearest_errors.append(row.row_id)
            for _,anchor in options.iterrows():
                rec=actual.loc[actual.row_id.eq(anchor.row_id)].iloc[0]
                missing=[];changed=[]
                for field in r.cap.FIELDS[row.line]:
                    x,y=row[field],anchor[field]
                    if pd.isna(x) or pd.isna(y):missing.append(field)
                    else:
                        if field=='construction_type':x,y=str(x).strip().lower(),str(y).strip().lower()
                        if x!=y:changed.append(field)
                delta=abs((row.period_start-anchor.period_start).days)
                nonoverlap=anchor.period_end<row.period_start if direction=='prior' else row.period_end<anchor.period_start
                ratio=row.sum_insured/(1000*anchor.sum_insured)
                eligible=not missing and not changed and nonoverlap and 1<=delta<=400 and .9<=ratio<=1.1
                okay=(str(rec.changed_fields or '')=='|'.join(changed) and str(rec.missing_fields or '')=='|'.join(missing)
                       and rec.start_gap_days==delta and abs(rec.what_if_div1000_over_reference-ratio)<1e-12 and bool(rec.strict_support_10pct)==eligible)
                if not okay:pair_errors.append((row.row_id,anchor.row_id))
                if anchor.row_id==nearest.row_id:
                    if bool(row['strict_'+direction+'_support'])!=eligible:pair_errors.append((row.row_id,'nearest'))
                    if direction=='prior':actual_prior_support+=int(eligible)
                    else:actual_later_support+=int(eligible)
    check('Every nearest reference is temporally nearest original normal value',not nearest_errors)
    check('All normal references, including unfavorable ones, are retained',not all_ref_errors)
    check('Every reference pair independently agrees on context, missingness, dates and ratio',not pair_errors)
    check('No new nearest original prior support; 988 nearest future supported',actual_prior_support==0 and actual_later_support==988)
    check('Prepared prior support requires CAP01 and consists of exact 3 IDs',
        set(f.loc[f.CAP01_prior_dependency,'row_id'])=={'B02718543','B02755900','C02237105'})
    check('Every one of 109 additional later-supported rows has a known prior context change',
          len(f.loc[f.review_group.eq('B_later_with_prior_conflict')])==109 and f.loc[f.review_group.eq('B_later_with_prior_conflict'),'original_prior_changed_fields'].fillna('').ne('').all())
    expected={'A_retrospective_D34':879,'B_later_with_prior_conflict':109,'C_no_original_normal_reference':108,
              'D_CAP01_dependency_only':2,'E_TW_dependency':16,'F_incomplete_context':202,'G_other_conflicts':138}
    check('Seven exclusive groups partition 1454 rows exactly',f.review_group.value_counts().to_dict()==expected and sum(expected.values())==1454)
    check('Original D34 retrospective routes remain frozen as 879 rows',set(f.loc[f.review_group.eq('A_retrospective_D34'),'row_id'])==set(frozen.loc[frozen.review_route.eq('retrospective_support_only'),'row_id']))
    numeric=f.original_prior_exists&f.original_prior_context_same.fillna(False)&f.original_prior_nonoverlap.fillna(False)&f.original_prior_start_gap_days.between(1,400)&~f.original_prior_what_if_div1000_over_reference.between(.9,1.1)
    check('All numeric conflicts independently identified',f.nearest_prior_numeric_conflict.equals(numeric))
    a=f.review_group.eq('A_retrospective_D34')
    proposed=pd.read_parquet(out/'tables/proposed_retrospective_scenario_NOT_APPLIED.parquet')
    check('Scenario excludes 12 numeric conflicts from 879, leaving 867, all unapproved',
          (a&numeric).sum()==12 and len(proposed)==867 and set(proposed.row_id)==set(f.loc[a&~numeric,'row_id']) and not proposed.capital_change_applied.any() and not proposed.correction_authorized.any())
    check('867 scenario has 111 future-2025 references; 879 group has 112',
          proposed.later_reference_2025_only_evidence.sum()==111 and (a&f.later_reference_2025_only_evidence).sum()==112)
    check('All 20 older-prior favorable references retain nearest contradiction flag',f.older_prior_cherry_pick_risk.sum()==20 and not (f.older_prior_cherry_pick_risk&f.strict_prior_support).any())
    source_claims=pq.read_table(c.ROOT/cat['claims']['workspace_relative_path']).to_pandas()
    wanted=source_claims.loc[source_claims.policy_id.isin(set(h.policy_id))]
    pd.testing.assert_frame_equal(normalize_dates(wanted).sort_values('claim_id').reset_index(drop=True),
        normalize_dates(cl[wanted.columns]).sort_values('claim_id').reset_index(drop=True),check_dtype=False,check_exact=True)
    check('All 128 source claim rows and every original field including PRE00 preserved',len(cl)==cl.claim_id.nunique()==128)
    assignment_errors=[]
    for _,claim in cl.iterrows():
        covered=policy_groups[claim.policy_id]
        covered=covered.loc[covered.period_start.le(claim.loss_date)&covered.period_end.ge(claim.loss_date)]
        if len(covered)>1:assignment_errors.append(claim.claim_id)
        elif len(covered)==0:
            if pd.notna(claim.row_id) or not claim.audit_pre00:assignment_errors.append(claim.claim_id)
        elif covered.iloc[0].row_id!=claim.row_id:assignment_errors.append(claim.claim_id)
    check('Every claim assignment independently matches policy occurrence interval',not assignment_errors)
    check('One PRE00 prehistory claim retained outside period diagnostic',cl.audit_pre00.sum()==cl.row_id.isna().sum()==1)
    check('24 claims in 23 pending periods; no observed accepted individual incurred exceeds hypothetical capital',
          cl.pending_frozen.fillna(False).sum()==24 and cl.loc[cl.pending_frozen.fillna(False),'row_id'].nunique()==23 and not cl.accepted_incurred_gt_hypothetical_capital.any())
    check('Claim results never select a proposed repair',cl.diagnostic_only_not_used_for_correction_selection.all())
    cases=json.loads((out/'cases.json').read_text('utf-8'))
    check('14 actual cases with valid focus IDs, no fictional histories',len(cases)==len({x['focus_row_id'] for x in cases})==14 and all(x['focus_row_id'] in set(f.row_id) and x['policy_id'] in policy_groups for x in cases))
    data=json.loads((out/'explorer_data.json').read_text('utf-8'))
    check('Explorer contains exactly every assessment and 1452 complete policy histories',len(data['index'])==1454 and set(x['row_id'] for x in data['index'])==set(f.row_id) and set(data['histories'])==set(h.policy_id))
    check('Explorer history counts preserve all 5587 periods and 128 claims',sum(len(g['policies']) for g in data['histories'].values())==5587 and sum(len(g['claims']) for g in data['histories'].values())==128)
    report=(out/'informe.html').read_text('utf-8')
    check('Embedded explorer JSON exactly matches standalone data',json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',report).group(1))==data)
    for ref in re.findall(r'(?:href|src)="([^"]+)"',report):
        check('Local report evidence link: '+ref,ref in ['verification.json','interface_verification.json','manifest.json'] or (out/ref).is_file())
    check('Report has no external script or data call',not re.search(r'<(?:script|img)[^>]+(?:src|href)="https?://|fetch\(|XMLHttpRequest',report))
    check('All source and active index hashes remain unchanged',all(c.digest(c.ROOT/p)==sha for p,sha in json.loads((out/'protected_hashes_before.json').read_text('utf-8')).items()))
    check('Original D34, CAP01 and active PRE00 manifests remain intact',r.cap.manifest_ok(r.ORIGINAL_REVIEW) and r.cap.manifest_ok(r.CAP) and r.cap.manifest_ok(c.ROOT/json.loads((out/'evidence/active_index.json').read_text('utf-8'))['workspace_relative_run']))
    check('No corrected dataset, model, feature or global approval is produced',not (out/'data').exists() and not summary['active_dataset_changed'] and summary['original_values_changed']==0 and not summary['models_trained'] and not summary['CON01_activated'])
    result={'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'checks':checks,
            'all_reference_pairs_checked':len(refs),'pending_rows_checked':1454,'independent_validation':False,
            'source_and_prepared_values_changed':0,'figure_visual_inspection_separate':True}
    c.dump(out/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
