"""Verificación propia de CAP05R: diferencias completas, DIST01-R, reversión y linaje."""
from decimal import Decimal
from pathlib import Path
import json
import sys
import apply_distant_capitals as a
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def equal(x, y, col):
    if pd.isna(x) or pd.isna(y):
        return pd.isna(x) and pd.isna(y)
    if col in ['period_start', 'period_end']:
        return pd.Timestamp(x) == pd.Timestamp(y)
    if col == 'construction_type':
        return str(x).strip().casefold() == str(y).strip().casefold()
    return x == y


def main(out):
    if (out/'manifest.json').exists():
        assert a.cap.manifest_ok(out)
        print(json.dumps({'status': 'closed_manifest_intact_no_rewrite'}))
        return
    checks = []
    def check(name, ok):
        checks.append({'check': name, 'passed': bool(ok)})
        if not ok:
            c.dump(out/'verification_failure.json', {'status': 'failed_not_published', 'checks': checks})
            raise AssertionError(name)
    read = lambda path: pd.read_parquet(out/path)
    parent = json.loads((out/'evidence/parent_catalog.json').read_text('utf-8'))
    newcat = json.loads((out/'dataset_catalog.json').read_text('utf-8'))
    frozen = read('evidence/frozen_46_proposal.parquet')
    ledger = read('ledger/all_capital_changes.parquet')
    prior_pending, pending = read('evidence/frozen_467_pending.parquet'), read('tables/pending_capitals.parquet')
    history = read('evidence/policy_histories.parquet').set_index('row_id')
    sha = c.digest(out/'evidence/frozen_46_proposal.parquet')
    check('Exact frozen D57 cohort hash, 46 row IDs, 18 buildings and 28 contents',
        sha == c.digest(a.REVIEW/'tables/proposed_scale_changes_NOT_APPLIED.parquet') and len(ledger) == ledger.row_id.nunique() == 46 and set(ledger.row_id) == set(frozen.row_id) and ledger.line.value_counts().to_dict() == {'contents': 28, 'buildings': 18})
    check('Authorized CAP05R /1000 only', ledger.rule.eq(a.RULE).all() and ledger.divisor.eq(1000).all() and ledger.operation_authorized.all() and ledger.correction_authorized.all() and ledger.capital_change_applied.all())
    auth = json.loads((out/'authorization.json').read_text('utf-8'))
    check('Exact participant request and cohort preserved', auth['messages'] == [{'role': 'user', 'content': a.REQUEST}] and auth['cohort_sha256'] == sha)
    check('Every ledger row records cohort and authorization SHA256', ledger.cohort_sha256.eq(sha).all() and ledger.authorization_sha256.eq(c.digest(out/'authorization.json')).all())
    check('Historical review false flags remain unchanged', not frozen.correction_authorized.any() and not frozen.capital_change_applied.any())
    check('421 unique remaining pending IDs, exact complement', len(pending) == pending.row_id.nunique() == 421 and set(pending.row_id) == set(prior_pending.row_id)-set(frozen.row_id))
    pd.testing.assert_frame_equal(pending.reset_index(drop=True), prior_pending.loc[~prior_pending.row_id.isin(frozen.row_id)].reset_index(drop=True), check_exact=True)
    check('Every pending inventory field, null and row order preserved', True)
    for name, expected in a.COUNTS.items():
        before = pq.read_table(c.ROOT/parent[name]['workspace_relative_path'])
        after = pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'])
        part = ledger.loc[ledger.source_table.eq(name)]
        pos = part.source_position.to_numpy(dtype=int)
        old, new = before['sum_insured'].to_numpy(), after['sum_insured'].to_numpy()
        changed = np.flatnonzero(~np.isclose(old, new, rtol=0, atol=0, equal_nan=True))
        check(name+': file matches catalog SHA256', c.digest(c.ROOT/newcat[name]['workspace_relative_path']) == newcat[name]['sha256'])
        check(name+': schema, metadata, column and row order unchanged', before.schema.equals(after.schema, check_metadata=True) and before.num_rows == after.num_rows and before.column_names == after.column_names)
        check(name+': every noncapital cell and null unchanged', before.drop(['sum_insured']).equals(after.drop(['sum_insured']), check_metadata=True))
        check(name+': exact authorized positions and row IDs', len(part) == expected and np.array_equal(changed, pos) and before.take(pa.array(pos))['row_id'].to_pylist() == part.row_id.tolist())
        check(name+': old/new actual values match ledger', np.array_equal(old[pos], part.old.to_numpy()) and np.array_equal(new[pos], part.new.to_numpy()))
        check(name+': positive finite new capitals and original null count', np.isfinite(new[pos]).all() and (new[pos] > 0).all() and before['sum_insured'].null_count == after['sum_insured'].null_count)
        restored = new.copy()
        restored[pos] = part.old.to_numpy()
        reverse = after.set_column(after.schema.get_field_index('sum_insured'), after.schema.field('sum_insured'), pa.array(restored, type=after.schema.field('sum_insured').type))
        check(name+': reversal recovers full parent Arrow table and metadata', reverse.equals(before, check_metadata=True))
        again, count = a.cap.apply_frozen(new, pos, part.old.to_numpy(), part.new.to_numpy())
        check(name+': second transformation is a no-op', count == 0 and np.array_equal(again, new, equal_nan=True))
        bad = new.copy()
        bad[pos[0]] = part.new.iloc[0]+.5
        try:
            a.cap.apply_frozen(bad, pos, part.old.to_numpy(), part.new.to_numpy())
        except ValueError:
            rejected = True
        else:
            rejected = False
        check(name+': unexpected value rejected', rejected)
        check(name+': ledger source and derived hashes correct', part.source_sha256.eq(parent[name]['sha256']).all() and part.derived_sha256.eq(newcat[name]['sha256']).all())
        check(name+': previous lineage metadata inherited', all(newcat[name][k] == val for k, val in parent[name].items() if k not in ['workspace_relative_path', 'sha256']))
        pd.testing.assert_frame_equal(read('ledger/'+name+'_sum_insured.parquet'), part.reset_index(drop=True), check_exact=True, check_dtype=False)
        check(name+': table ledger agrees with consolidated values', True)
    for name in sorted(set(parent)-set(a.COUNTS)):
        check(name+': full catalog reference and file unchanged', newcat[name] == parent[name] and c.digest(c.ROOT/newcat[name]['workspace_relative_path']) == parent[name]['sha256'])
    check('Four new derived files, no new columns', {p.name for p in (out/'data').iterdir()} == {name+'.parquet' for name in a.COUNTS})
    sources, original = {}, {}
    for name in a.COUNTS:
        ids = history.loc[history.source_table.eq(name)].index.tolist()
        sources[name] = pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'], filters=[('row_id', 'in', ids)]).to_pandas().set_index('row_id')
        original[name] = pq.read_table(c.RAW/(name+'.parquet'), columns=['row_id', 'sum_insured'], filters=[('row_id', 'in', ids)]).to_pandas().set_index('row_id').sum_insured
    # Re-read all 210 rows: only authorized capital cells can differ from review history.
    by_id = ledger.set_index('row_id')
    for row_id, frozen_row in history.iterrows():
        actual = sources[frozen_row.source_table].loc[row_id]
        expected_capital = by_id.loc[row_id, 'new'] if row_id in by_id.index else frozen_row.sum_insured
        check(row_id+': full published historical row preserved except authorized capital', actual.sum_insured == expected_capital and all(equal(actual[col], frozen_row[col], col) for col in actual.index if col != 'sum_insured'))
        check(row_id+': review history matched original published capital', frozen_row.sum_insured == original[frozen_row.source_table].loc[row_id])
    frozen_by_id = frozen.set_index('row_id')
    evaluations = read('evidence/direction_evaluations.parquet')
    for row in ledger.itertuples(index=False):
        check(row.row_id+': exact Decimal division and frozen proposal', Decimal(str(row.old))/Decimal(1000) == Decimal(str(row.new)) and row.old == frozen_by_id.loc[row.row_id, 'sum_insured'] and row.new == frozen_by_id.loc[row.row_id, 'hypothetical_div1000_CU'])
        focus = history.loc[row.row_id]
        ref = history.loc[row.selected_reference_row_id]
        actual_ref = sources[row.selected_reference_source_table].loc[row.selected_reference_row_id]
        fields = a.cap.FIELDS[row.line]
        same = all(pd.notna(focus[col]) and pd.notna(ref[col]) and equal(focus[col], ref[col], col) for col in fields)
        gap = abs((pd.Timestamp(ref.period_start)-pd.Timestamp(focus.period_start)).days)
        earlier, later = sorted([pd.Timestamp(ref.period_start), pd.Timestamp(focus.period_start)])
        within_two_years = later <= earlier+pd.DateOffset(years=2)
        g = history.loc[history.policy_id.eq(row.policy_id) & history.line.eq(row.line)].sort_values(['period_start', 'period_end'])
        threshold = 10000000 if row.line == 'buildings' else 1000000
        complete_normal = g.loc[(g.sum_insured > 0) & (g.sum_insured <= threshold) & g[fields].notna().all(axis=1)]
        if row.selected_reference_direction == 'prior':
            side = complete_normal.loc[complete_normal.period_start < focus.period_start].sort_values('period_start', ascending=False)
        else:
            side = complete_normal.loc[complete_normal.period_start > focus.period_start].sort_values('period_start')
        check(row.row_id+': nearest complete ORIGINAL anchor chosen before amount/context', len(side) > 0 and side.index[0] == row.selected_reference_row_id and ref.policy_id == row.policy_id and ref.line == row.line)
        check(row.row_id+': D34 endpoints complete/equal, original capital, exact authorized distance', same and actual_ref.sum_insured == ref.sum_insured == row.selected_reference_capital_CU and gap == row.selected_start_gap_days and gap > 400 and within_two_years and .9 <= row.new/ref.sum_insured <= 1.1)
        segment = g.loc[(g.period_start >= earlier) & (g.period_start <= later)]
        middle = segment.loc[~segment.index.isin([row.row_id, row.selected_reference_row_id])]
        middle_ok = len(middle) == 1
        if middle_ok:
            mid = middle.iloc[0]
            missing = [col for col in fields if pd.isna(mid[col])]
            changes = [col for col in fields if pd.notna(mid[col]) and not equal(mid[col], focus[col], col)]
            middle_ok = bool(missing) and not changes and 0 < mid.sum_insured <= threshold
        check(row.row_id+': exactly one original ordinary incomplete intermediate, no known changes', middle_ok)
        values = [row.new if rid == row.row_id else x.sum_insured for rid, x in segment.iterrows()]
        ratios = [values[i+1]/values[i] for i in range(len(values)-1)]
        edges = list(zip(segment.index.tolist()[:-1], segment.index.tolist()[1:]))
        calendar_ok = True
        for left, right in edges:
            lend, rstart = pd.Timestamp(history.loc[left, 'period_end']), pd.Timestamp(history.loc[right, 'period_start'])
            uncovered = (rstart-lend).days-1
            calendar_ok &= uncovered == 0 or (uncovered == 1 and lend == pd.Timestamp('2024-12-30') and rstart == pd.Timestamp('2025-01-01'))
        check(row.row_id+': every monetary step compatible and original calendar retained', len(ratios) == 2 and all(.9 <= ratio <= 1.1 for ratio in ratios) and calendar_ok)
        prior = pd.Timestamp(ref.period_start) < pd.Timestamp(focus.period_start)
        flag = row.selected_reference_source_table.startswith('test_') and pd.Timestamp(ref.period_start).year == 2025
        check(row.row_id+': anchor temporal flag and corrected-test flag independently checked', row.audit_ref_test2025 == flag and row.reference_is_future_at_focus_start == (not prior) and row.corrected_row_is_test2025 == row.source_table.startswith('test_') and row.retrospective_only and not row.historical_availability_confirmed)
        d = evaluations.loc[evaluations.focus_row_id.eq(row.row_id) & evaluations.direction.eq(row.selected_reference_direction)]
        check(row.row_id+': selected D57 review decision matches actual anchor', len(d) == 1 and d.iloc[0].reference_row_id == row.selected_reference_row_id and d.iloc[0].candidate_NOT_APPLIED)
    for name, part in pending.groupby('source_table'):
        values = pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'], columns=['row_id', 'sum_insured']).to_pandas().set_index('row_id').sum_insured
        check(name+': all pending actual capitals preserved', np.array_equal(values.loc[part.row_id].to_numpy(), part.sum_insured.to_numpy()))
    check('Both D57 numeric conflicts still pending, no skipped endorsements', {'C00502745', 'C00399729'}.issubset(set(pending.row_id)) and sources['policies_contents'].loc['C00502745', 'sum_insured'] == 27200000 and sources['policies_contents'].loc['C00399729', 'sum_insured'] == 25700000 and sources['policies_contents'].loc['C01153989', 'sum_insured'] == 39400 and sources['policies_contents'].loc['C01147928', 'sum_insured'] == 37700)
    no_anchor_ids = set(prior_pending.loc[prior_pending.review_group.str.startswith('C_'), 'row_id'])
    check('All 108 no-original-anchor cases remain pending', len(no_anchor_ids) == 108 and no_anchor_ids.issubset(set(pending.row_id)))
    check('C486 and B192 earlier capitals stay pending, no cascades', {'C01596694', 'B00962235'}.issubset(set(pending.row_id)))
    inherited_cap01 = read('evidence/CAP01_ledger.parquet')
    inherited = read('evidence/prior_retrospective_ledger.parquet')
    for label, frame, expected in [('CAP01', inherited_cap01, 2073), ('CAP02R_CAP03R_CAP04R', inherited, 987)]:
        valid = True
        for name, part in frame.groupby('source_table'):
            values = pq.read_table(c.ROOT/newcat[name]['workspace_relative_path'], columns=['row_id', 'sum_insured']).to_pandas().set_index('row_id').sum_insured
            valid &= np.array_equal(values.loc[part.row_id].to_numpy(), part.new.to_numpy())
        check('Every inherited '+label+' capital preserved without redivision', len(frame) == expected and not set(frame.row_id)&set(ledger.row_id) and valid)
    signal = read('ledger/test2025_supported_changes.parquet')
    corrected_test = read('ledger/corrected_test2025_rows.parquet')
    cumulative = read('ledger/cumulative_retrospective_changes.parquet')
    cumulative_signal = read('ledger/cumulative_test2025_supported_changes.parquet')
    check('Exactly seven test anchors: one building, six contents', len(signal) == 7 and signal.line.value_counts().to_dict() == {'contents': 6, 'buildings': 1} and set(signal.row_id) == set(frozen.loc[frozen.selected_reference_test2025, 'row_id']))
    pd.testing.assert_frame_equal(signal.reset_index(drop=True), ledger.loc[ledger.audit_ref_test2025].reset_index(drop=True), check_exact=True)
    check('Seven-anchor extraction matches ledger exactly', True)
    check('Thirteen corrected test rows separately identified', len(corrected_test) == 13 and corrected_test.source_table.value_counts().to_dict() == {'test_buildings': 7, 'test_contents': 6})
    check('21 prior and 25 later anchors; 427–731 days', ledger.selected_reference_direction.value_counts().to_dict() == {'later': 25, 'prior': 21} and ledger.selected_start_gap_days.min() == 427 and ledger.selected_start_gap_days.max() == 731)
    check('1033 unique retrospective changes, correct rule counts', len(cumulative) == cumulative.row_id.nunique() == 1033 and cumulative.rule.value_counts().to_dict() == {'CAP02R': 867, 'CAP04R': 109, 'CAP05R': 46, 'CAP03R': 11})
    pd.testing.assert_frame_equal(cumulative.iloc[:987].reset_index(drop=True), inherited.reset_index(drop=True), check_exact=True)
    check('All prior cumulative records preserved', True)
    check('136 cumulative test anchors including 129 inherited', len(cumulative_signal) == 136 and cumulative_signal.rule.value_counts().to_dict() == {'CAP02R': 111, 'CAP04R': 17, 'CAP05R': 7, 'CAP03R': 1} and set(cumulative_signal.row_id) == set(cumulative.loc[cumulative.audit_ref_test2025, 'row_id']))
    check('Originals, parent files and all preexisting indexes unchanged before activation', all(c.digest(c.ROOT/path) == digest for path, digest in json.loads((out/'protected_hashes_before.json').read_text('utf-8')).items()))
    parent_index = json.loads((out/'evidence/parent_index.json').read_text('utf-8'))
    check('Immutable CAP04R and D57 manifests intact', a.cap.manifest_ok(c.ROOT/parent_index['workspace_relative_run']) and a.cap.manifest_ok(a.REVIEW))
    verified = [p for p in out.rglob('*') if p.is_file() and p.name not in ['verification.json', 'verification_failure.json']]
    result = {'status': 'passed_own_technical_verification', 'passed': len(checks), 'failed': 0, 'checks': checks,
        'capital_changes': 46, 'pending_after': 421, 'new_test2025_supported_rows': 7, 'corrected_test_rows': 13,
        'cumulative_test2025_supported_rows': 136, 'total_corrected_capitals': 3106,
        'reversal_verified': True, 'idempotence_verified': True, 'unexpected_value_rejected': True, 'independent_validation': False,
        'verified_files': {p.relative_to(out).as_posix(): c.digest(p) for p in verified}}
    c.dump(out/'verification.json', result)
    print(json.dumps({k: val for k, val in result.items() if k not in ['checks', 'verified_files']}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
