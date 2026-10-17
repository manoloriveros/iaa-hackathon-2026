"""Verificación propia por comparación íntegra y aritmética de fechas independiente."""
from datetime import date
from pathlib import Path
import json
import sys
import numpy as np

import clean_data as c
import pandas as pd
import pyarrow.parquet as pq


def main():
    out = c.ROOT / json.loads((c.BASE / 'current_run.json').read_text(encoding='utf-8'))['workspace_relative_run']
    checks = []

    def check(name, passed, detail=None):
        checks.append({'check': name, 'passed': bool(passed), 'detail': detail})
        if not passed:
            c.dump(out / 'verification.json', {'passed': False, 'checks': checks})
            raise AssertionError(name)

    original_hashes = json.loads((out / 'original_hashes_before.json').read_text(encoding='utf-8'))
    check('11_original_files_unchanged', len(original_hashes) == 11 and all(
        c.digest(c.RAW / n) == h for n, h in original_hashes.items()))
    master = set(pq.read_table(c.RAW / 'customers.parquet', columns=['customer_id']).column(0).to_pylist())
    test_ids = []
    for name in c.TABLES:
        raw = pq.read_table(c.RAW / f'{name}.parquet')
        clean = pq.read_table(out / 'data' / f'{name}.parquet')
        check(name + ':rows_schema_metadata', raw.num_rows == clean.num_rows and raw.schema.equals(clean.schema, check_metadata=True))
        untouched = [col for col in raw.column_names if col not in ['customer_id', 'exposure']]
        check(name + ':every_other_value_unchanged_including_capitals', all(raw[col].equals(clean[col]) for col in untouched))
        row_ids = clean['row_id'].to_pylist()
        check(name + ':unique_row_ids', len(set(row_ids)) == len(row_ids))
        ids = clean['customer_id'].to_pylist()
        check(name + ':customer_keys_exist_and_text', all(isinstance(v, str) and len(v) == 8 and v in master for v in ids))
        # Python date subtraction (not production pandas formula) checks every interval, including leap days.
        starts = raw['period_start'].to_pylist()
        ends = raw['period_end'].to_pylist()
        expected = np.array([round(((b - a).days + 1) / 365, 4) for a, b in zip(starts, ends)])
        actual = clean['exposure'].to_numpy()
        check(name + ':every_exposure_matches_inclusive_dates', np.array_equal(actual, expected) and (actual > 0).all())
        for column in ['customer_id', 'exposure']:
            ledger = pd.read_parquet(out / 'ledger' / f'{name}_{column}.parquet')
            old, new = raw[column].to_pandas(), clean[column].to_pandas()
            changed = old.ne(new)
            indices = ledger.source_row.to_numpy(dtype=int)
            check(name + ':' + column + ':ledger_complete_unique',
                  np.array_equal(indices, np.flatnonzero(changed)) and ledger.source_row.is_unique)
            check(name + ':' + column + ':ledger_values_and_row_ids',
                  ledger.old.tolist() == old.iloc[indices].tolist() and ledger.new.tolist() == new.iloc[indices].tolist()
                  and ledger.row_id.tolist() == [row_ids[i] for i in indices])
            restored = new.copy()
            restored.iloc[indices] = ledger.old.to_numpy()
            check(name + ':' + column + ':exact_reversal', restored.equals(old))
        if name.startswith('test_'):
            test_ids.extend(row_ids)
            check(name + ':test_exposure_unchanged', raw['exposure'].equals(clean['exposure']))
        check(name + ':idempotent', c.canonical_ids(pd.Series(ids), master).tolist() == ids
              and np.array_equal(actual, c.date_exposure(pd.Series(starts), pd.Series(ends))[1].to_numpy()))
    sample = pq.read_table(c.RAW / 'sample_submission.parquet', columns=['row_id']).column(0).to_pylist()
    check('test_id_coverage_and_no_cross_line_duplicates', len(test_ids) == len(set(test_ids)) == len(sample)
          and set(test_ids) == set(sample))
    # Boundary checks: leap year, one-day cover, invalid date order and malformed identifiers.
    d, e = c.date_exposure(pd.Series([date(2024, 1, 1), date(2025, 1, 1)]),
                           pd.Series([date(2024, 12, 31), date(2025, 1, 1)]))
    check('date_boundaries_leap_and_single_day', d.tolist() == [366, 1] and e.tolist() == [1.0027, .0027])
    for label, action in [
        ('invalid_date_rejected', lambda: c.date_exposure(pd.Series([date(2025, 2, 1)]), pd.Series([date(2025, 1, 1)]))),
        ('nonnumeric_id_rejected', lambda: c.canonical_ids(pd.Series(['12A']), master)),
        ('overlength_id_rejected', lambda: c.canonical_ids(pd.Series(['123456789']), master)),
        ('missing_id_rejected', lambda: c.canonical_ids(pd.Series([None]), master)),
        ('unknown_master_key_rejected', lambda: c.canonical_ids(pd.Series(['00000000']), set()))]:
        rejected = False
        try:
            action()
        except ValueError:
            rejected = True
        check(label, rejected)
    result = {'passed': True, 'checks_count': len(checks), 'checks': checks,
              'scope': 'Own technical checks assisted by AI; not independent actuarial validation.',
              'human_review': 'pending', 'modeling_approval': False}
    c.dump(out / 'verification.json', result)
    c.dump(c.BASE / 'current_run.json', {'workspace_relative_run': out.relative_to(c.ROOT).as_posix(),
                                        'status': 'verified_technical_human_review_pending'})
    print(json.dumps({'passed': True, 'checks': len(checks), 'run': str(out)}))


if __name__ == '__main__':
    main()
