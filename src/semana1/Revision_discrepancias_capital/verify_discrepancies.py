"""Validación propia de cohorte, historias, controles y preservación de ambas ramas."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import sys

import review_discrepancies as a
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def normalize(frame):
    frame=frame.copy()
    for col in ['period_start','period_end']:
        if col in frame:frame[col]=pd.to_datetime(frame[col]).dt.as_unit('ns')
    return frame


def main(out):
    if (out/'manifest.json').exists():
        assert a.cap.manifest_ok(out);print(json.dumps({'status':'closed_manifest_intact_no_rewrite'}));return
    checks=[]
    def check(name,ok):
        checks.append({'check':name,'passed':bool(ok)})
        if not ok:
            c.dump(out/'verification_failure.json',{'status':'failed','checks':checks})
            raise AssertionError(name)
    f=pd.read_parquet(out/'tables/twelve_assessment.parquet');h=pd.read_parquet(out/'tables/all_12_policy_histories.parquet')
    pending=pd.read_parquet(out/'tables/remaining_587_inventory.parquet');remainder=pd.read_parquet(out/'tables/other_575_inventory.parquet')
    frozen=pd.read_parquet(out/'evidence/frozen_587_pending.parquet');original=pd.read_parquet(out/'evidence/D48_assessment.parquet')
    expected=original.loc[original.review_group.eq('A_retrospective_D34')&original.nearest_prior_numeric_conflict]
    cat=json.loads((out/'evidence/dataset_catalog.json').read_text('utf-8'))
    check('587 inventory exactly preserves every frozen assessment field',len(pending)==587 and pending.equals(frozen))
    check('Exact 12 D48 numeric conflicts, all still pending',len(f)==f.row_id.nunique()==f.policy_id.nunique()==12 and set(f.row_id)==set(expected.row_id) and set(f.row_id).issubset(set(pending.row_id)))
    check('Twelve plus other 575 exactly partition 587 without expansion',len(remainder)==575 and set(remainder.row_id)==set(pending.row_id)-set(f.row_id) and not set(remainder.row_id)&set(f.row_id))
    check('No correction applied or contract reset claimed',not f.capital_change_applied.any() and not f.actual_contract_reset_confirmed.any())
    check('All 12 belong to contents and corrected branch has no effect on their retained values',f.line.eq('contents').all() and f.set_index('row_id').reported_capital_CU.sort_index().equals(expected.set_index('row_id').sum_insured.rename('reported_capital_CU').sort_index()))
    sources=[]
    for prefix in ['policies','test']:
        name=prefix+'_contents';table=pq.read_table(c.ROOT/cat[name]['workspace_relative_path']);source=table.to_pandas()
        selected=source.loc[source.policy_id.isin(f.policy_id)]
        pd.testing.assert_frame_equal(normalize(selected).sort_values('row_id').reset_index(drop=True),
            normalize(h.loc[h.source_table.eq(name),table.column_names]).sort_values('row_id').reset_index(drop=True),check_dtype=False,check_exact=True)
        check(name+': every original field and complete source history preserved',True)
        source['source_table']=name;sources.append(normalize(source))
    check('Exactly 63 unique history rows in the 12 policies',len(h)==h.row_id.nunique()==63)
    check('All 63 historical current capitals are original uncorrected values',h.sum_insured.equals(h.original_capital_CU.rename('sum_insured')))
    allrows=pd.concat(sources,ignore_index=True).set_index('row_id')
    errors=[]
    for row in f.itertuples(index=False):
        initial=allrows.loc[row.initial_row_id];mid=allrows.loc[row.midterm_row_id];focus=allrows.loc[row.row_id];later=allrows.loc[row.later_row_id]
        valid=(initial.policy_id==mid.policy_id==focus.policy_id==later.policy_id==row.policy_id and
               mid.period_start==initial.period_end+pd.Timedelta(days=1) and mid.period_start.year==initial.period_start.year and
               mid.period_end<focus.period_start and focus.period_start.month==focus.period_start.day==1 and
               focus.period_start.year==mid.period_start.year+1 and focus.period_end<later.period_start and
               initial.renewal_decision=='mid_term_change' and focus.renewal_count==mid.renewal_count+1 and
               initial.sum_insured==row.initial_capital_CU and mid.sum_insured==row.midterm_capital_CU and
               focus.sum_insured==row.reported_capital_CU and later.sum_insured==row.later_capital_CU and
               row.hypothetical_div1000_CU==focus.sum_insured/1000)
        computed={'midterm_increase_pct':100*(mid.sum_insured/initial.sum_insured-1),
            'hypothetical_vs_initial_pct':100*((focus.sum_insured/1000)/initial.sum_insured-1),
            'hypothetical_vs_midterm_pct':100*((focus.sum_insured/1000)/mid.sum_insured-1),
            'later_vs_hypothetical_pct':100*(later.sum_insured/(focus.sum_insured/1000)-1)}
        valid &= all(np.isclose(getattr(row,key),value,atol=1e-12,rtol=0) for key,value in computed.items())
        for label,ref in [('initial',initial),('midterm',mid),('later',later)]:
            missing=[field for field in a.FIELDS if pd.isna(focus[field]) or pd.isna(ref[field])]
            changed=[field for field in a.FIELDS if pd.notna(focus[field]) and pd.notna(ref[field]) and focus[field]!=ref[field]]
            valid &= getattr(row,label+'_missing_fields')=='|'.join(missing) and getattr(row,label+'_different_fields')=='|'.join(changed)
        if not valid:errors.append(row.row_id)
    check('All twelve four-stage timelines, ratios and field comparisons independently reproduce from sources',not errors)
    check('All prior midterm capitals grew, while hypothetical renewal falls against them',f.midterm_increase_pct.gt(0).all() and f.hypothetical_vs_midterm_pct.lt(-10).all() and f.hypothetical_vs_initial_pct.between(0,5).all())
    check('11 complete initial risk comparisons and one missing security_level',
          f.initial_same_known_context.sum()==11 and set(f.loc[~f.initial_complete,'policy_id'])=={'C48613718'} and
          f.loc[~f.initial_complete,'initial_missing_fields'].eq('security_level').all())
    check('All midterm and later risk comparisons are complete and equal',f.midterm_same_known_context.all() and f.later_same_known_context.all())
    check('Only C21091984 uses a 2025 test anchor',set(f.loc[f.test2025_reference,'policy_id'])=={'C21091984'} and f.loc[f.test2025_reference,'later_source_table'].eq('test_contents').all())
    check('Two 2022, nine 2023 and one 2024 focus periods',pd.to_datetime(f.period_start).dt.year.value_counts().to_dict()=={2023:9,2022:2,2024:1})
    check('Every midterm premium increased, without assuming annualization',(f.midterm_premium_CU>f.initial_premium_CU).all())
    c492=f.loc[f.policy_id.eq('C49279780')].iloc[0]
    check('C49279780 seven-day capital retained as limit, not annualized',c492.midterm_days==7 and c492.midterm_capital_CU==101000 and c492.hypothetical_div1000_CU==67300)
    c486=allrows.loc[allrows.policy_id.eq('C48613718')].sort_values('period_start')
    check('C48613718 older complete reference is explicitly 730 days away',
          (pd.Timestamp('2023-01-01')-c486.iloc[0].period_start).days==730 and c486.iloc[0].sum_insured==28200 and c486.iloc[0].security_level=='locks')
    controls=pd.read_parquet(out/'tables/independent_normal_control_sequences.parquet')
    check('9909 unique control sequences in 9702 other policies',len(controls)==controls.row_id.nunique()==9909 and controls.policy_id.nunique()==9702 and not set(controls.policy_id)&set(f.policy_id))
    valid_controls=[]
    for col in ['row_id','initial_row_id','midterm_row_id']:
        check('Every control anchor key exists in source: '+col,controls[col].isin(allrows.index).all())
    ctrl=allrows.loc[controls.row_id].reset_index(drop=True)
    ini=allrows.loc[controls.initial_row_id].reset_index(drop=True)
    mid=allrows.loc[controls.midterm_row_id].reset_index(drop=True)
    check('Control timeline and policy identity are valid in every sequence',
          ctrl.policy_id.equals(ini.policy_id) and ctrl.policy_id.equals(mid.policy_id) and
          (mid.period_start==ini.period_end+pd.Timedelta(days=1)).all() and
          (mid.period_start.dt.year==ini.period_start.dt.year).all() and
          (ctrl.period_start.dt.year==mid.period_start.dt.year+1).all() and
          ctrl.period_start.dt.month.eq(1).all() and ctrl.period_start.dt.day.eq(1).all() and
          (ctrl.period_start-mid.period_end).dt.days.between(1,2).all() and ini.renewal_decision.eq('mid_term_change').all())
    for field in a.FIELDS:
        check('All control risk fields complete and equal: '+field,ctrl[field].notna().all() and ini[field].notna().all() and mid[field].notna().all() and ctrl[field].equals(ini[field]) and ctrl[field].equals(mid[field]))
    for prefix,actual in [('',ctrl),('initial_',ini),('midterm_',mid)]:
        check(prefix+'control capital agrees exactly with source and normal original band',
              actual.sum_insured.gt(0).all() and actual.sum_insured.le(1_000_000).all() and
              np.array_equal(actual.sum_insured.to_numpy(),controls[prefix+'original_capital_CU'].to_numpy()))
    reset=100*(ctrl.sum_insured/ini.sum_insured-1)
    persistence=100*(ctrl.sum_insured/mid.sum_insured-1)
    closer=(np.abs(np.log(ctrl.sum_insured/ini.sum_insured))<np.abs(np.log(ctrl.sum_insured/mid.sum_insured)))
    check('Control ratios recompute and all 9909 are closer to initial capital',
          np.allclose(reset,controls.renewal_vs_initial_pct,rtol=0,atol=1e-12) and
          np.allclose(persistence,controls.renewal_vs_midterm_pct,rtol=0,atol=1e-12) and closer.all())
    check('Control median baseline change is 2%, not inferred from focus cases',abs(reset.median()-2)<1e-10)
    raw_parts=[]
    for name in ['policies_contents','test_contents']:
        raw=pq.read_table(c.RAW/(name+'.parquet'),columns=['row_id','sum_insured']).to_pandas();raw_parts.append(raw)
    raw=pd.concat(raw_parts,ignore_index=True).set_index('row_id')
    all_control_ids=set(controls.row_id)|set(controls.initial_row_id)|set(controls.midterm_row_id)
    check('Every control amount is an uncorrected original, not CAP01 or CAP02R',np.array_equal(allrows.loc[sorted(all_control_ids)].sum_insured.to_numpy(),raw.loc[sorted(all_control_ids)].sum_insured.to_numpy()))
    claim_source=pq.read_table(c.ROOT/cat['claims']['workspace_relative_path'],columns=['policy_id']).to_pandas()
    claim_evidence=pd.read_parquet(out/'tables/all_12_claim_histories.parquet')
    check('No observed claims in exact 12 policies, source checked',len(claim_evidence)==0 and not claim_source.policy_id.isin(f.policy_id).any())
    data=json.loads((out/'explorer_data.json').read_text('utf-8'))
    check('Explorer includes all 12 cases and all 63 history rows',len(data['index'])==len(data['cases'])==12 and sum(len(g) for g in data['histories'].values())==63 and set(data['histories'])==set(f.policy_id))
    report=(out/'informe.html').read_text('utf-8')
    check('Embedded and standalone explorer data agree exactly',json.loads(re.search(r'<script id="reviewData" type="application/json">([\s\S]*?)</script>',report).group(1))==data)
    for ref in re.findall(r'(?:href|src)="([^"]+)"',report):
        check('Report evidence link: '+ref,ref in ['verification.json','interface_verification.json','manifest.json'] or (out/ref).is_file())
    check('No corrected data layer is produced',not (out/'data').exists())
    check('All protected original/derived files and both dataset indexes unchanged',all(c.digest(c.ROOT/path)==sha for path,sha in json.loads((out/'protected_hashes_before.json').read_text('utf-8')).items()))
    retro=json.loads((out/'evidence/retrospective_index.json').read_text('utf-8'))
    check('CAP02R and D48 historical manifests preserved',a.cap.manifest_ok(c.ROOT/retro['workspace_relative_run']) and a.cap.manifest_ok(a.D48))
    result={'status':'passed_own_technical_verification','passed':len(checks),'failed':0,'checks':checks,
        'focus_rows':12,'history_rows':63,'control_sequences':9909,'other_pending_inventory':575,
        'all_587_values_preserved':True,'independent_validation':False,'models_trained':False}
    c.dump(out/'verification.json',result);print(json.dumps({k:v for k,v in result.items() if k!='checks'}))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
