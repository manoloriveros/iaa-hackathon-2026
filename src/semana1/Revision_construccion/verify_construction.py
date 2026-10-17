"""Verificación propia CON01, con emparejamiento independiente por fechas y códigos originales."""
from datetime import date
from pathlib import Path
import json
from html.parser import HTMLParser
from urllib.parse import unquote

import analyze_construction as a
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main():
    pointer = json.loads((a.BASE / 'current_run.json').read_text(encoding='utf-8'))
    out = a.ROOT / pointer['workspace_relative_run']
    checks = []

    def check(name, passed):
        item = {'name':name, 'passed':bool(passed)}
        checks.append(item)
        if not passed:
            a.c.dump(out / 'verification_failed.json', {'passed':False, 'checks':checks})
            raise AssertionError(name)

    parent = json.loads((out / 'evidence/parent_catalog.json').read_text(encoding='utf-8'))
    cat = json.loads((out / 'candidate/dataset_catalog.json').read_text(encoding='utf-8'))
    summary = json.loads((out / 'summary.json').read_text(encoding='utf-8'))
    protected = json.loads((out / 'protected_hashes_before.json').read_text(encoding='utf-8'))
    parentrun = a.ROOT / summary['parent_run']
    parent_manifest = json.loads((out / 'evidence/parent_manifest.json').read_text(encoding='utf-8'))
    check('parent_manifest_still_matches_every_historical_file', all(a.c.digest(parentrun / x['path']) == x['sha256'] for x in parent_manifest['files']))
    check('parent_manifest_itself_unchanged', a.c.digest(parentrun / 'manifest.json') == a.c.digest(out / 'evidence/parent_manifest.json'))
    for path, digest in protected.items():
        check('protected_hash:' + path, a.c.digest(a.ROOT / path) == digest)
    check('protected_before_after_equal', protected == json.loads((out / 'protected_hashes_after.json').read_text(encoding='utf-8')))
    old_raw = json.loads((parentrun / 'protected_hashes_after.json').read_text(encoding='utf-8'))
    check('original_hashes_also_match_prior_verified_run', all(protected[p.relative_to(a.ROOT).as_posix()] == old_raw[p.relative_to(a.ROOT).as_posix()] for p in a.c.RAW.glob('*.parquet')))
    raw_frames = []
    candidate_ids = []
    counts = {}
    for name, entry in cat.items():
        check(name + ':catalog_hash', a.c.digest(a.ROOT / entry['workspace_relative_path']) == entry['sha256'])
        if name not in a.BUILDINGS:
            check(name + ':catalog_reference_exactly_unchanged', entry == parent[name])
            continue
        before = pq.read_table(a.ROOT / parent[name]['workspace_relative_path'])
        after = pq.read_table(a.ROOT / entry['workspace_relative_path'])
        check(name + ':only_one_added_field', after.column_names == before.column_names + [a.FIELD])
        check(name + ':all_preexisting_fields_types_metadata_and_values_identical', after.drop([a.FIELD]).equals(before, check_metadata=True))
        check(name + ':new_field_nonmissing_string', after[a.FIELD].null_count == 0 and str(after.schema.field(a.FIELD).type) == 'string')
        # This direct mapping uses original, unnormalized source codes, not the production helper.
        raw = pq.read_table(a.c.RAW / (name + '.parquet'), columns=['row_id','policy_id','address_id','period_start','period_end','construction_type']).to_pandas()
        source = raw.construction_type.str.casefold()
        expected = ['tw_code' if code in ('t','w') else code for code in source]
        check(name + ':candidate_matches_direct_original_code_mapping', after['row_id'].to_pylist() == raw.row_id.tolist() and after[a.FIELD].to_pylist() == expected)
        check(name + ':literal_normalized_column_preserved', before['construction_type'].to_pylist() == source.tolist() and after['construction_type'].equals(before['construction_type']))
        check(name + ':drop_added_field_reverses_every_value', after.drop([a.FIELD]).equals(before, check_metadata=True))
        check(name + ':map_idempotent', a.harmonize(after[a.FIELD].to_pandas()).tolist() == expected)
        ledger = pq.read_table(out / 'candidate/ledger' / (name + '.parquet')).to_pandas()
        idx = np.flatnonzero(source.isin(['t','w']))
        check(name + ':ledger_exhaustive_positions_ids_and_source_codes', ledger.source_row.tolist() == idx.tolist()
              and ledger.row_id.tolist() == raw.row_id.iloc[idx].tolist() and ledger.source_code.tolist() == source.iloc[idx].tolist())
        check(name + ':ledger_records_addition_not_overwrite', ledger.harmonized_code.eq('tw_code').all() and not ledger.source_value_overwritten.any()
              and ledger.source_field.eq('construction_type').all() and ledger.new_field.eq(a.FIELD).all())
        counts[name] = len(idx)
        check(name + ':counts_match_summary', summary['candidate_counts'][name]['grouped_t_w_rows'] == len(idx))
        check(name + ':other_three_classes_not_merged', all(e == s for e,s in zip(expected,source) if s not in ('t','w')))
        raw['source_table'] = name
        raw_frames.append(raw)
        candidate_ids.extend(after['row_id'].to_pylist())
    raw = pd.concat(raw_frames, ignore_index=True)
    check('all_building_row_ids_unique', len(candidate_ids) == len(set(candidate_ids)) == 891881)
    check('exact_85556_training_and_22261_test_grouped_rows', counts == {'policies_buildings':85556,'test_buildings':22261})
    train = raw[raw.source_table.eq('policies_buildings')].copy()
    train['code'] = train.construction_type.str.casefold()
    check('2022_pre_and_2023_post_data_exist_in_training_only', train.period_start.map(lambda d:d.year).min() == 2021 and train.period_start.map(lambda d:d.year).max() == 2024)
    pre = train[train.period_end.eq(date(2022,12,31))]
    post = train[train.period_start.eq(date(2023,1,1))]
    paired = pre.merge(post, on=['policy_id','address_id'], suffixes=('_pre','_post'), validate='one_to_one')
    tw = paired[paired.code_pre.eq('t')]
    check('independent_date_join_reproduces_149887_boundary_pairs', len(paired) == summary['boundary_pairs'] == 149887)
    check('independent_date_join_reproduces_18218_distinct_t_to_w', len(tw) == tw.policy_id.nunique() == summary['boundary_t_to_w_pairs'] == 18218 and tw.code_post.eq('w').all())
    check('independent_join_other_construction_classes_unchanged', paired.loc[~paired.code_pre.eq('t'),'code_pre'].tolist() == paired.loc[~paired.code_pre.eq('t'),'code_post'].tolist())
    all_direct = pq.read_table(out / 'tables/boundary_2022_2023.parquet').to_pandas()
    check('sequence_and_independent_date_join_same_row_pairs', set(zip(paired.row_id_pre,paired.row_id_post)) == set(zip(all_direct.previous_row_id,all_direct.row_id)))
    check('no_t_period_reaches_2023', raw.loc[raw.construction_type.str.casefold().eq('t'),'period_end'].max() == date(2022,12,31))
    check('no_w_period_precedes_2023', raw.loc[raw.construction_type.str.casefold().eq('w'),'period_start'].min() == date(2023,1,1))
    check('no_w_before_cut_or_t_after_cut', not ((raw.period_start.map(lambda d:d.year).lt(2023) & raw.construction_type.str.casefold().eq('w')) |
         (raw.period_start.map(lambda d:d.year).ge(2023) & raw.construction_type.str.casefold().eq('t'))).any())
    canonical = raw.construction_type.str.casefold().map(lambda s:'tw_code' if s in ('t','w') else s)
    check('original_codes_independent_address_level_no_contradictions', raw.assign(canonical=canonical).groupby('address_id').canonical.nunique().eq(1).all())
    check('address_is_nested_in_policy_not_independent_corroboration', raw.groupby('address_id').policy_id.nunique().eq(1).all() and summary['addresses_multiple_policies'] == 0)
    check('all_292112_address_histories_examined', raw.address_id.nunique() == summary['addresses'] == 292112)
    allpairs = pq.read_table(out / 'tables/all_adjacent_pairs.parquet').to_pandas()
    check('all_599769_same_address_transitions_examined', int(allpairs.same_address.sum()) == summary['same_address_all_transitions'] == 599769)
    check('all_449658_training_same_address_transitions_examined', int((allpairs.same_address & allpairs.source_table.eq('policies_buildings')).sum()) == summary['same_address_train_transitions'] == 449658)
    check('no_same_address_counterexample_saved', not (allpairs.same_address & allpairs.harmonized_code_changed).any()
          and pq.read_table(out / 'tables/same_address_contradictions.parquet').num_rows == 0)
    cohorts = pd.read_csv(out / 'tables/cohort_reconciliation.csv')
    check('cohort_totals_do_not_drop_noncontinuing_rows', cohorts.groupby('cohort').rows.sum().to_dict() == {'t_2022':22274,'w_2023':22353})
    check('no_unclassified_cohort', not cohorts.status.eq('unclassified').any())
    stable = pd.read_csv(out / 'tables/paired_context_stability.csv')
    structural = ['customer_id','address_id','occupancy','accidental_damage_cover','mortgage','voluntary_excess','compulsory_excess','channel','payment_method']
    check('all_18218_t_w_pairs_stable_on_nine_listed_context_fields', stable[stable.cohort.eq('t_to_w') & stable.field.isin(structural)].different.eq(0).all())
    histories = pq.read_table(out / 'tables/case_histories.parquet').to_pandas()
    check('six_real_cases_with_complete_histories', histories.case_id.nunique() == 6 and histories.policy_id.nunique() == 6)
    for case, group in histories.groupby('case_id'):
        original = raw[raw.policy_id.eq(group.policy_id.iloc[0])]
        check('case:' + case + ':all_real_rows_preserved', set(group.row_id) == set(original.row_id))
    pending = pq.read_table(a.ROOT / 'Hackaton/Semana 1/Limpieza/runs/capfix_20261016T184904Z_099a22b1/tables/pending_capitals.parquet').to_pandas()
    for name, group in pending.groupby('source_table'):
        data = pq.read_table(a.ROOT / cat[name]['workspace_relative_path'], columns=['row_id','sum_insured']).to_pandas().set_index('row_id')
        check(name + ':pending_capitals_exactly_frozen', np.array_equal(data.loc[group.row_id,'sum_insured'].to_numpy(),group.sum_insured.to_numpy()))
    check('all_1454_pending_capitals_verified', len(pending) == 1454)
    check('rules_do_not_claim_organizer_material_confirmation', 'Unconfirmed' in json.loads((out / 'rules.json').read_text(encoding='utf-8'))['material_name'])
    rejected = False
    try:
        a.harmonize(pd.Series(['wood_unknown']))
    except ValueError:
        rejected = True
    check('unexpected_code_requires_review', rejected)
    result = {'passed':True, 'checks_count':len(checks), 'checks':checks,
        'independent_algorithm_used':True, 'independent_validation':False,
        'review_type':'Own verification assisted by AI; a different algorithm is not an independent reviewer.',
        'preexisting_cells_changed':0, 'active_catalog_changed':False, 'candidate_grouped_rows':107817,
        'originals_modified':False, 'models_trained':False}
    # File exists before rendering/link verification; the final result replaces it before manifest closure.
    a.c.dump(out / 'verification.json', result)
    from render_construction import render
    render(out, summary, result)

    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.paths = []
        def handle_starttag(self, tag, attrs):
            for key,value in attrs:
                if key in ('href','src') and value and not value.startswith(('data:', '#','https:','http:')):
                    self.paths.append(unquote(value.split('#')[0]))
    html = (out / 'informe.html').read_text(encoding='utf-8')
    parser = Links(); parser.feed(html)
    check('report_local_links_resolve', all((out / p).is_file() for p in parser.paths))
    check('report_includes_six_cases_and_two_figures', all(item in html for item in histories.policy_id.unique()) and html.count('data:image/png;base64,') == 2)
    check('active_pointer_still_byte_identical_at_end', a.c.digest(a.ROOT / 'Hackaton/Semana 1/Limpieza/current_dataset.json') == a.c.digest(out / 'evidence/active_dataset_before.json'))
    result.update(checks=checks, checks_count=len(checks))
    a.c.dump(out / 'verification.json', result)
    # Report needs the final count; figures are deterministic, no model or data processing repeated.
    render(out, summary, result)
    manifest = [{'path':p.relative_to(out).as_posix(), 'bytes':p.stat().st_size, 'sha256':a.c.digest(p)}
                for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    a.c.dump(out / 'manifest.json', {'count':len(manifest), 'files':manifest})
    a.c.dump(a.BASE / 'current_run.json', {'workspace_relative_run':out.relative_to(a.ROOT).as_posix(),
        'status':'verified_review_candidate_not_active', 'report_workspace_relative':(out / 'informe.html').relative_to(a.ROOT).as_posix(),
        'candidate_catalog_workspace_relative':(out / 'candidate/dataset_catalog.json').relative_to(a.ROOT).as_posix(),
        'active_dataset_unchanged':True, 'candidate_grouped_t_w_rows':107817})
    print(json.dumps({'passed':True, 'checks':len(checks), 'manifest_files':len(manifest), 'run':str(out)}), flush=True)


if __name__ == '__main__':
    main()
