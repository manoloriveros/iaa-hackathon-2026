"""Comprueba propuesta e historias sin aplicar depuración a ningún dataset."""
from datetime import date
from collections import defaultdict
from decimal import Decimal
import json

import review_pairs as a
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main():
    ptr=json.loads((a.BASE/'current_run.json').read_text(encoding='utf-8'));out=a.ROOT/ptr['workspace_relative_run']
    catalog=json.loads((out/'evidence/dataset_catalog.json').read_text(encoding='utf-8'))
    s=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    proposed=pq.read_table(out/'tables/proposed_pair_actions.parquet').to_pandas()
    pairs=pq.read_table(out/'tables/frozen_pair_members.parquet').to_pandas()
    original=pq.read_table(a.ROOT/catalog['claims']['workspace_relative_path']).to_pandas()
    fields=[col for col in original if col!='claim_id']
    checks=[]
    def check(name,condition):
        checks.append({'name':name,'passed':bool(condition)})
        if not condition:
            a.c.dump(out/'verification_failed.json',{'passed':False,'checks':checks});raise AssertionError(name)
    protected=json.loads((out/'protected_hashes_before.json').read_text(encoding='utf-8'))
    for path,digest in protected.items():check('protected_hash:'+path,a.c.digest(a.ROOT/path)==digest)
    check('before_after_protected_hashes_equal',protected==json.loads((out/'protected_hashes_after.json').read_text(encoding='utf-8')))
    for name,folder in [('D40',a.REVIEW),('D38',a.ROOT/json.loads((out/'evidence/active_index.json').read_text(encoding='utf-8'))['workspace_relative_run'])]:
        m=json.loads((out/'evidence'/f'{name}_manifest.json').read_text(encoding='utf-8'))
        check(name+':prior_run_all_files_and_manifest_unchanged',a.c.digest(folder/'manifest.json')==a.c.digest(out/'evidence'/f'{name}_manifest.json')
              and all(a.c.digest(folder/e['path'])==e['sha256'] for e in m['files']))
    # This verifier keys raw source tuples rather than using pandas duplicated/groupby.
    groups=defaultdict(list)
    for position,values in enumerate(original[fields].itertuples(index=False,name=None)):
        key=tuple(None if pd.isna(v) else v for v in values)
        groups[key].append(position)
    duplicate_groups=[indices for indices in groups.values() if len(indices)>1]
    expected_ids={original.claim_id.iloc[i] for indices in duplicate_groups for i in indices}
    check('independent_source_tuple_groups_604_pairs_1208_members',len(duplicate_groups)==604 and all(len(x)==2 for x in duplicate_groups)
          and len(expected_ids)==1208 and expected_ids==set(pairs.claim_id))
    frozen=pq.read_table(out/'evidence/D40_frozen_pairs.parquet').to_pandas()
    check('frozen_D40_cohort_exact_no_expansion',set(frozen.claim_id)==expected_ids and pairs.set_index('claim_id').duplicate_group.to_dict()==frozen.set_index('claim_id').duplicate_group.to_dict())
    check('all_11_non_id_source_fields_used',len(fields)==11 and fields==json.loads((out/'proposed_rule.json').read_text(encoding='utf-8'))['group_fields'])
    ids=original.set_index('claim_id');positions={claim:i for i,claim in enumerate(original.claim_id)}
    for row in proposed.itertuples():
        before,after=ids.loc[row.proposed_keep_claim_id],ids.loc[row.proposed_exclude_claim_id]
        assert all((pd.isna(before[col]) and pd.isna(after[col])) or before[col]==after[col] for col in fields)
        assert positions[row.proposed_keep_claim_id]==row.keep_source_row and positions[row.proposed_exclude_claim_id]==row.exclude_source_row
    check('every_proposed_pair_exact_typed_values_and_source_positions',len(proposed)==604 and proposed.equal_fields.eq(11).all())
    check('one_standard_and_one_long_id_per_pair',proposed.proposed_keep_claim_id.str.fullmatch(a.STANDARD).all() and proposed.proposed_exclude_claim_id.str.fullmatch(a.LONG).all())
    check('proposed_alias_ids_all_unique_disjoint_and_full_cohort',proposed.proposed_keep_claim_id.is_unique and proposed.proposed_exclude_claim_id.is_unique
          and not set(proposed.proposed_keep_claim_id)&set(proposed.proposed_exclude_claim_id)
          and set(proposed.proposed_keep_claim_id)|set(proposed.proposed_exclude_claim_id)==expected_ids)
    check('all_long_source_ids_have_verified_twin',set(original.loc[original.claim_id.str.fullmatch(a.LONG),'claim_id'])==set(proposed.proposed_exclude_claim_id))
    check('order_not_claimed_as_creation_time',s['standard_is_first_in_file']==303 and s['long_is_first_in_file']==301)
    check('occurrence_report_concentration_reproduced',s['loss_years']=={'2020':1,'2021':3,'2022':600} and s['report_years']=={'2022':572,'2023':32})
    check('all_ramos_and_states_reconciled',s['by_line']=={'motor':411,'buildings':109,'contents':84} and s['by_status']=={'closed':586,'open':12,'repudiated':6})
    # Recompute period assignment directly from provided training intervals, not D38 audit output.
    histories=pq.read_table(out/'tables/affected_policy_histories.parquet').to_pandas()
    assigned=pairs[['claim_id','line','policy_id','loss_date']].merge(histories[['row_id','line','policy_id','period_start','period_end']],
        on=['line','policy_id'],how='left',validate='many_to_many')
    hits=assigned[assigned.loss_date.between(assigned.period_start,assigned.period_end)]
    check('independent_interval_assignment_unique_for_1206_members',len(hits)==1206 and hits.claim_id.is_unique)
    previous=pairs.set_index('claim_id').row_id
    check('independent_interval_assignment_matches_audit_every_member',hits.set_index('claim_id').row_id.to_dict()==previous.dropna().to_dict())
    check('only_one_pair_explicitly_before_history',proposed.assignment_status.value_counts().to_dict()=={'unique_period':603,'before_first_observed_period':1})
    check('both_members_share_assignment_or_same_prehistory',pairs.groupby('duplicate_group').row_id.nunique(dropna=False).eq(1).all()
          and pairs.groupby('duplicate_group').assignment_status.nunique().eq(1).all())
    # Monetary sensitivity uses Decimal on original fields; no filtered claims table is written.
    total=Decimal('0');assigned_total=Decimal('0');pre_total=Decimal('0')
    for row in proposed.itertuples():
        source=ids.loc[row.proposed_exclude_claim_id]
        value=(Decimal(str(source.incurred_to_date))-Decimal(str(source.recoveries))) if source.status in ('closed','open') else Decimal('0')
        total+=value
        if pd.isna(row.row_id):pre_total+=value
        else:assigned_total+=value
    check('exact_decimal_net_3174167_49',str(total.quantize(Decimal('.01')))==s['hypothetical_accepted_net_reduction_all_CU']=='3174167.49')
    check('exact_decimal_current_periods_3173808_61_and_prehistory_358_88',str(assigned_total.quantize(Decimal('.01')))=='3173808.61'
          and str(pre_total.quantize(Decimal('.01')))=='358.88')
    check('net_decomposes_into_paid_plus_reserve_minus_recovery',all(abs(r.observed_net_CU-(r.paid_to_date+r.case_reserve_CU-r.recoveries))<1e-8
        for r in proposed.itertuples() if r.status!='repudiated'))
    check('repudiated_pair_net_zero_preserved_not_accepted_count',proposed.loc[proposed.status.eq('repudiated'),'observed_net_CU'].eq(0).all())
    affected=set(zip(proposed.line,proposed.policy_id))
    check('601_affected_policies_and_three_double_pair_histories',len(affected)==601 and proposed.groupby(['line','policy_id']).size().value_counts().to_dict()=={1:598,2:3})
    claimhist=pq.read_table(out/'tables/affected_claim_histories.parquet').to_pandas()
    expected_keys=affected|{('motor','M83268515'),('motor','M63592395')}
    expected=original[[key in expected_keys for key in zip(original.line,original.policy_id)]]
    check('all_claim_histories_complete_source_fields_unchanged',claimhist.claim_id.tolist()==expected.claim_id.tolist()
          and all(claimhist[col].reset_index(drop=True).equals(expected[col].reset_index(drop=True)) for col in original.columns))
    for line in ['motor','buildings','contents']:
        raw=pq.read_table(a.ROOT/catalog['policies_'+line]['workspace_relative_path'],columns=['row_id','policy_id','period_start','period_end']).to_pandas()
        keys={policy for ramo,policy in expected_keys if ramo==line}
        check(line+':all_training_policy_periods_present',set(histories.loc[histories.line.eq(line),'row_id'])==set(raw.loc[raw.policy_id.isin(keys),'row_id']))
    collision=pd.read_csv(out/'tables/collision_key_sensitivity.csv')
    check('nonidentical_collisions_preserved_1_17_57',collision.groups.tolist()==[1,17,57] and collision.member_rows.tolist()==[2,34,114])
    check('same_dates_control_excluded_from_proposal',not proposed.policy_id.eq('M83268515').any()
          and set(claimhist.loc[claimhist.policy_id.eq('M83268515'),'claim_id'])==set(original.loc[original.policy_id.eq('M83268515'),'claim_id']))
    check('different_third_parties_preserved',not proposed.policy_id.eq('M63592395').any()
          and {'TP8386915','TP2577127'}.issubset(set(claimhist.loc[claimhist.policy_id.eq('M63592395'),'third_party_id'].dropna())))
    cases=json.loads((out/'case_selection.json').read_text(encoding='utf-8'))
    check('11_cases_cover_three_ramos_and_two_counterexamples',len(cases)==11 and {x['line'] for x in cases}=={'motor','buildings','contents'}
          and sum(x['duplicate_group'] is None for x in cases)==2)
    check('no_cleaned_dataset_or_active_catalog_written',not (out/'data').exists() and not (out/'dataset_catalog.json').exists()
          and proposed.operation_applied.eq(False).all() and s['operation_applied'] is False)
    check('active_dataset_index_still_byte_identical',a.c.digest(a.ROOT/'Hackaton/Semana 1/Limpieza/current_dataset.json')==a.c.digest(out/'evidence/active_index.json'))
    result={'passed':True,'checks_count':len(checks),'checks':checks,'operation_applied':False,'data_modified':False,
        'independent_validation':False,'type':'Own verification with independent tuple-key and interval algorithms; no independent reviewer.'}
    a.c.dump(out/'verification.json',result)
    from render_pairs import render
    render(out,result)
    entries=[{'path':p.relative_to(out).as_posix(),'sha256':a.c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json']
    a.c.dump(out/'manifest.json',{'count':len(entries),'files':entries})
    a.c.dump(a.BASE/'current_run.json',{'workspace_relative_run':out.relative_to(a.ROOT).as_posix(),
        'report_workspace_relative':(out/'informe.html').relative_to(a.ROOT).as_posix(),'status':'verified_proposal_only_no_data_changes',
        'proposed_rule':'DUP01','pairs':604,'affected_policies':601,'proposal_workspace_relative':(out/'tables/proposed_pair_actions.parquet').relative_to(a.ROOT).as_posix(),
        'operation_applied':False,'active_dataset_changed':False})
    print(json.dumps({'passed':True,'checks':len(checks),'run':str(out),'operation_applied':False}),flush=True)


if __name__=='__main__':main()
