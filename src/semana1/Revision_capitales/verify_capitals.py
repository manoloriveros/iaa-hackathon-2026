"""Verifica valores originales, referencias y criterios de revisión sin aplicar correcciones."""
import json
import re

import analyze_capitals as a
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def main():
    out = a.ROOT / json.loads((a.BASE / 'current_run.json').read_text(encoding='utf-8'))['workspace_relative_run']
    checks = []
    # The report links to this result. Create an explicit pending result before checking local links.
    a.save(out / 'verification.json', {'passed': False, 'status': 'verification_running'})

    def check(name, passed):
        checks.append({'check': name, 'passed': bool(passed)})
        if not passed:
            a.save(out / 'verification.json', {'passed': False, 'checks': checks})
            raise AssertionError(name)

    protected = json.loads((out / 'protected_hashes_before.json').read_text(encoding='utf-8'))
    check('all_17_protected_original_and_derived_files_unchanged', len(protected) == 17 and all(
        a.sha(a.ROOT / path) == value for path, value in protected.items()))
    total = 0
    for line, threshold in a.THRESHOLDS.items():
        review = pq.read_table(out / 'tables' / f'extreme_review_{line}.parquet').to_pandas()
        histories = pq.read_table(out / 'tables' / f'affected_policy_histories_{line}.parquet').to_pandas()
        cases = pq.read_table(out / 'tables' / f'case_histories_{line}.parquet').to_pandas()
        raw_parts = []
        for prefix in ['policies', 'test']:
            name = f'{prefix}_{line}'
            raw = pq.read_table(a.RAW / f'{name}.parquet').to_pandas()
            raw['period_start'] = pd.to_datetime(raw.period_start)
            raw['period_end'] = pd.to_datetime(raw.period_end)
            raw['source_table'] = name
            for label, frame in [('history', histories), ('case', cases), ('review', review)]:
                part = frame[frame.source_table.eq(name)]
                source = raw.set_index('row_id').loc[part.row_id].reset_index()
                fields = [col for col in raw.columns if col != 'row_id']
                try:
                    pd.testing.assert_frame_equal(source[fields].reset_index(drop=True),
                        part[fields].reset_index(drop=True), check_dtype=False)
                    passed = True
                except AssertionError:
                    passed = False
                check(name + ':' + label + ':every_original_field_preserved', passed)
            raw_parts.append(raw)
        source = pd.concat(raw_parts, ignore_index=True).set_index('row_id')
        check(line + ':all_extreme_rows_covered_once', review.row_id.is_unique
            and set(review.row_id) == set(source[source.sum_insured > threshold].index))
        check(line + ':histories_cover_exactly_affected_policies',
            set(histories.row_id) == set(source[source.policy_id.isin(review.policy_id)].index)
            and histories.row_id.is_unique)
        check(line + ':what_if_separate_original_capital_intact',
            np.array_equal(review.what_if_div1000_CU.to_numpy(), review.sum_insured.to_numpy()/1000))
        check(line + ':review_routes_partition', review.review_route.notna().all()
            and review.review_route.isin(['prior_supported', 'retrospective_support_only',
                'no_normal_same_policy_reference', 'context_or_continuity_review']).all())
        refs_ok, supported_ok, no_reference_ok = True, True, True
        for row in review.itertuples(index=False):
            for direction in ['prior', 'later']:
                ref_id = getattr(row, direction + '_row_id')
                if pd.isna(ref_id):
                    continue
                ref = source.loc[ref_id]
                refs_ok &= ref.policy_id == row.policy_id and ref.sum_insured <= threshold
                refs_ok &= ref.sum_insured == getattr(row, direction + '_sum_insured')
                refs_ok &= (ref.period_end < row.period_start if direction == 'prior' else row.period_end < ref.period_start)
            if row.review_route == 'prior_supported':
                ref = source.loc[row.prior_row_id]
                supported_ok &= 1 <= (row.period_start-ref.period_start).days <= 400
                supported_ok &= .9 <= (row.sum_insured/1000)/ref.sum_insured <= 1.1
                for col in a.FIELDS[line]:
                    x, y = getattr(row, col), ref[col]
                    supported_ok &= pd.notna(x) and pd.notna(y)
                    if pd.isna(x) or pd.isna(y):
                        continue
                    if col == 'construction_type':
                        x, y = str(x).casefold().strip(), str(y).casefold().strip()
                    supported_ok &= x == y
            if row.review_route == 'no_normal_same_policy_reference':
                no_reference_ok &= pd.isna(row.prior_row_id) and pd.isna(row.later_row_id)
        check(line + ':all_references_match_source_and_direction', refs_ok)
        check(line + ':every_prior_supported_row_satisfies_proposal', supported_ok)
        check(line + ':no_history_not_fabricated', no_reference_ok)
        total += len(review)
    cohort = pd.read_csv(out / 'tables/cohorts.csv')
    check('cohorts_reconcile_all_extreme_rows', int(cohort.rows.sum()) == total)
    case_meta = json.loads((out / 'cases.json').read_text(encoding='utf-8'))
    check('case_keys_unique', len({v['case'] for v in case_meta}) == len(case_meta))
    report = out / 'informe.html'
    text = report.read_text(encoding='utf-8')
    check('report_local_links_exist', all((out / link).exists() for link in re.findall(r'href="([^"]+)"', text)
        if not link.startswith(('http', '#'))))
    check('report_has_no_changed_policy_outputs', not (out / 'data').exists())
    a.save(out / 'verification.json', {'passed': True, 'checks_count': len(checks), 'checks': checks,
        'sum_insured_changes': 0, 'scope': 'Own technical verification; human actuarial review pending; no independent validation.'})
    a.save(a.BASE / 'current_run.json', {'workspace_relative_run': out.relative_to(a.ROOT).as_posix(),
                                      'status': 'verified_review_only_no_corrections'})
    entries = [{'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': a.sha(p)}
               for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifest.json']
    a.save(out / 'manifest.json', {'count': len(entries), 'files': entries})
    print(json.dumps({'passed': True, 'checks': len(checks), 'extreme_rows': total, 'case_histories': len(case_meta)}))


if __name__ == '__main__':
    main()
