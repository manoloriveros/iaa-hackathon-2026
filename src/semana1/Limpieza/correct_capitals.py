"""CAP01: corrección autorizada de una cohorte congelada, en una versión derivada nueva."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import sys
import uuid

import clean_data as c
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT, BASE = c.ROOT, c.BASE
PARENT = BASE / 'runs/clean_20261016T175335Z_a6412ce0'
REVIEW = ROOT / 'Hackaton/Semana 1/Revision_capitales/runs/capital_20261016T180903Z_bceb990c'
EXPECTED = {'policies_buildings': 802, 'test_buildings': 272,
            'policies_contents': 731, 'test_contents': 268}
FIELDS = {
    'buildings': ['customer_id', 'address_id', 'construction_type', 'occupancy',
        'accidental_damage_cover', 'voluntary_excess', 'compulsory_excess', 'smoke_alarms', 'mortgage'],
    'contents': ['customer_id', 'address_id', 'tenure', 'security_level', 'high_value_items',
        'accidental_damage_cover', 'works_from_home', 'lodgers', 'bicycle_cover', 'voluntary_excess', 'compulsory_excess']}
REQUEST = ('Corrijamos la escala de los 2.073 casos con respaldo anterior, dividiendo por mil solo en los datos derivados. '
           'Conserva los originales, documenta y valida cada cambio y deja los demás capitales pendientes.')


def manifest_ok(folder):
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    return all(c.digest(folder / item['path']) == item['sha256'] for item in manifest['files'])


def apply_frozen(values, positions, old, new):
    """Solo acepta old o new: una segunda aplicación a la misma lista es un no-op."""
    result = np.array(values, copy=True)
    actual = result[positions]
    if not ((actual == old) | (actual == new)).all():
        raise ValueError('CAP01 value conflict: abort rather than divide an unexpected amount.')
    todo = actual == old
    result[positions[todo]] = new[todo]
    return result, int(todo.sum())


def main():
    assert manifest_ok(PARENT) and manifest_ok(REVIEW), 'Parent evidence differs from its manifest.'
    assert json.loads((PARENT / 'verification.json').read_text(encoding='utf-8'))['passed']
    assert json.loads((REVIEW / 'verification.json').read_text(encoding='utf-8'))['passed']
    ident = datetime.now(timezone.utc).strftime('capfix_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
    out = BASE / 'runs' / ident
    for name in ['data', 'ledger', 'tables', 'source_snapshot', 'evidence']:
        (out / name).mkdir(parents=True, exist_ok=False)
    parent_catalog = json.loads((PARENT / 'dataset_catalog.json').read_text(encoding='utf-8'))
    protected = {p.relative_to(ROOT).as_posix(): c.digest(p) for p in sorted(c.RAW.glob('*.parquet'))}
    protected.update({entry['workspace_relative_path']: c.digest(ROOT / entry['workspace_relative_path'])
                      for entry in parent_catalog.values()})
    c.dump(out / 'protected_hashes_before.json', protected)
    for name in ['correct_capitals.py', 'verify_capital_correction.py', 'CAPITALES.md', 'clean_data.py']:
        shutil.copy2(BASE / name, out / 'source_snapshot' / name)
    for folder, label in [(PARENT, 'parent'), (REVIEW, 'review')]:
        for name in ['manifest.json', 'verification.json']:
            shutil.copy2(folder / name, out / 'evidence' / f'{label}_{name}')
    shutil.copy2(REVIEW / 'protocol.json', out / 'evidence/review_protocol.json')
    c.dump(out / 'authorization.json', {'status': 'explicit_participant_authorization',
        'source': 'Human user in current Codex conversation, 2026-10-16',
        'messages': [{'role': 'user', 'content': REQUEST}],
        'cohort': 'Exactly the 2073 prior_supported row_ids in frozen D34 evidence.',
        'not_claimed': 'No organizer confirmation of source units, independent validation, or overall modeling approval.'})
    c.dump(out / 'rules.json', {'rule': 'CAP01', 'version': '1.0', 'operation': 'sum_insured / 1000',
        'selection': 'Frozen D34 prior_supported row_id allowlist; never recompute/expand it on corrected data.',
        'expected_changes': EXPECTED, 'inherited': ['D32 ID01', 'D32 EXP01'],
        'scope': 'Only sum_insured in four derived household policy tables; motor byte-copied.',
        'evidence': 'Earlier same-policy non-extreme reference, known unchanged specified context, 1–400 start-date days, corrected/reference ratio 0.90–1.10.',
        'pending': 'All 1454 other D34 extreme rows unchanged; no cascading repairs.',
        'approval': 'Participant approved this cohort and operation, not a source-system confirmation of intended units.',
        'temporal': 'Prior reference only for selected rows. Freeze data version and preserve cutoff-specific preparation for temporal validation.',
        'professional_references': ['IAA Documentation section 2', 'Governance section 2.8', 'Professional Considerations sections 3.5–3.6']})
    candidates, pending = [], []
    for line in ['buildings', 'contents']:
        review_path = REVIEW / 'tables' / f'extreme_review_{line}.parquet'
        frame = pq.read_table(review_path).to_pandas()
        frame['review_file_sha256'] = c.digest(review_path)
        selected = frame[frame.review_route.eq('prior_supported')].copy()
        assert selected.row_id.is_unique
        keep = ['source_table', 'line', 'row_id', 'policy_id', 'customer_id', 'address_id', 'sum_insured',
                'prior_row_id', 'prior_sum_insured', 'prior_period_start', 'prior_period_end',
                'prior_start_gap_days', 'what_if_ratio_to_prior', 'review_route', 'review_file_sha256']
        candidates.append(selected[keep])
        deferred = frame[~frame.review_route.eq('prior_supported')].copy()
        deferred['status'] = 'pending_no_capital_change'
        pending.append(deferred[keep + ['status']])
    allowlist = pd.concat(candidates, ignore_index=True)
    deferred = pd.concat(pending, ignore_index=True)
    assert len(allowlist) == 2073 and allowlist.row_id.is_unique and len(deferred) == 1454
    assert allowlist.groupby('source_table').size().to_dict() == EXPECTED
    allowlist.to_parquet(out / 'evidence/approved_cohort.parquet', index=False)
    allowlist.to_csv(out / 'evidence/approved_cohort.csv', index=False)
    deferred.to_parquet(out / 'tables/pending_capitals.parquet', index=False)
    deferred.to_csv(out / 'tables/pending_capitals.csv', index=False)
    summary, ledgers, catalog = [], [], {}
    for name, entry in parent_catalog.items():
        source = ROOT / entry['workspace_relative_path']
        assert c.digest(source) == entry['sha256']
        if name not in c.TABLES:
            catalog[name] = dict(entry)
            continue
        destination = out / 'data' / f'{name}.parquet'
        if name not in EXPECTED:
            shutil.copy2(source, destination)
            changed_count = 0
        else:
            table = pq.read_table(source)
            positions = pd.Series(np.arange(table.num_rows), index=table['row_id'].to_pylist())
            assert positions.index.is_unique
            approved = allowlist[allowlist.source_table.eq(name)].copy()
            approved['source_row'] = positions.loc[approved.row_id].to_numpy()
            approved = approved.sort_values('source_row').reset_index(drop=True)
            idx = approved.source_row.to_numpy(dtype=int)
            values = table['sum_insured'].to_numpy()
            old = approved.sum_insured.to_numpy(dtype=float)
            new = old / 1000
            assert np.array_equal(values[idx], old), name
            assert np.isfinite(new).all() and (new > 0).all()
            corrected, changed_count = apply_frozen(values, idx, old, new)
            assert changed_count == EXPECTED[name]
            output = table.set_column(table.schema.get_field_index('sum_insured'), table.schema.field('sum_insured'),
                                      pa.array(corrected, type=table.schema.field('sum_insured').type))
            pq.write_table(output, destination, compression='zstd')
            approved = approved.rename(columns={'sum_insured': 'old'})
            approved['new'] = new
            approved['rule'] = 'CAP01'
            approved['divisor'] = 1000
            approved['operation_authorized_by'] = 'explicit_participant_request_20261016'
            approved.to_parquet(out / 'ledger' / f'{name}_sum_insured.parquet', index=False)
            ledgers.append(approved)
            summary.append({'table': name, 'rows': table.num_rows, 'changed_rows': changed_count,
                'selected_capital_before_CU': float(old.sum()), 'selected_capital_after_CU': float(new.sum()),
                'other_extreme_pending': int(deferred.source_table.eq(name).sum())})
            print(json.dumps(summary[-1]), flush=True)
        catalog[name] = {'workspace_relative_path': destination.relative_to(ROOT).as_posix(),
            'layer': 'derived', 'sha256': c.digest(destination), 'parent_workspace_relative_path': entry['workspace_relative_path'],
            'parent_sha256': entry['sha256'], 'capital_changes': changed_count,
            'capital_rule': 'CAP01' if changed_count else 'unchanged_motor_byte_copy'}
    ledger = pd.concat(ledgers, ignore_index=True)
    ledger.to_parquet(out / 'ledger/all_capital_changes.parquet', index=False)
    ledger.to_csv(out / 'ledger/all_capital_changes.csv', index=False)
    pd.DataFrame(summary).to_csv(out / 'tables/change_summary.csv', index=False)
    c.dump(out / 'summary.json', summary)
    c.dump(out / 'dataset_catalog.json', catalog)
    c.dump(out / 'lineage.json', {'parent_run': PARENT.relative_to(ROOT).as_posix(),
        'review_run': REVIEW.relative_to(ROOT).as_posix(),
        'inherited_ledger_paths': [(PARENT / 'ledger').relative_to(ROOT).as_posix()],
        'this_ledger': 'ledger/all_capital_changes.parquet',
        'originals': c.RAW.relative_to(ROOT).as_posix(), 'active_index_published_only_after_verification': True})
    after = {path: c.digest(ROOT / path) for path in protected}
    c.dump(out / 'protected_hashes_after.json', after)
    assert protected == after and manifest_ok(PARENT) and manifest_ok(REVIEW)
    c.dump(out / 'run.json', {'run_id': ident, 'utc': datetime.now(timezone.utc).isoformat(),
        'operation': 'CAP01_frozen_cohort', 'capital_changes': len(ledger), 'pending_capitals': len(deferred),
        'originals_modified': False, 'prior_runs_modified': False, 'other_columns_modified': False,
        'cohort_operation_authorized': True, 'source_units_confirmed_by_organizer': False,
        'independent_validation': False, 'approved_for_modeling': False, 'models_trained': False,
        'python': sys.version, 'pandas': pd.__version__, 'pyarrow': pa.__version__})
    # A dedicated pending index keeps the verified active dataset unchanged until verification succeeds.
    c.dump(BASE / 'current_capital_correction.json', {'workspace_relative_run': out.relative_to(ROOT).as_posix(),
                                                  'status': 'pending_verification'})
    print('RUN=' + str(out), flush=True)


if __name__ == '__main__':
    main()
