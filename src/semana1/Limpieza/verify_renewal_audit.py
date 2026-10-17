"""Comprueba preservación completa, marcas congeladas, reversión y conflictos de REN00."""
from pathlib import Path
import json
import sys

import clean_data as c
import apply_renewal_audit as a
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


def main(out):
    if (out / 'manifest.json').exists():
        manifest = json.loads((out / 'manifest.json').read_text('utf-8'))
        assert all(c.digest(out / e['path']) == e['sha256'] for e in manifest['files'])
        print(json.dumps({'status':'closed_verified_run_manifest_intact_no_rewrite'})); return
    checks = []
    def check(name, condition):
        checks.append({'check': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    parent = json.loads((out / 'evidence/parent_catalog.json').read_text('utf-8'))
    new = json.loads((out / 'dataset_catalog.json').read_text('utf-8'))
    frozen_path = out / 'evidence/frozen_cohort.parquet'
    frozen = pd.read_parquet(frozen_path)
    cohort_sha = c.digest(frozen_path)
    ledger = pd.read_parquet(out / 'ledger/ren00_marked_rows.parquet')
    check('Exact approved cohort preserved', len(frozen) == frozen.policy_id.nunique() == 2742 and cohort_sha == c.digest(a.REVIEW / 'tables/frozen_cohort.parquet'))
    all_ids = []; total = marked = 0
    for name in c.TABLES:
        before = pq.read_table(c.ROOT / parent[name]['workspace_relative_path'])
        after = pq.read_table(c.ROOT / new[name]['workspace_relative_path'])
        check(name + ': catalog hash matches', c.digest(c.ROOT / new[name]['workspace_relative_path']) == new[name]['sha256'])
        check(name + ': every original value, schema metadata, row order and null preserved', after.drop([a.FLAG]).equals(before, check_metadata=True))
        check(name + ': only one appended field', after.column_names == before.column_names + [a.FLAG] and after.num_rows == before.num_rows)
        field = after.schema.field(a.FLAG)
        check(name + ': nonnull boolean and explicit audit-only metadata', field.type == pa.bool_() and not field.nullable and after[a.FLAG].null_count == 0 and field.metadata[b'role'] == b'audit_only' and field.metadata[b'excluded_from_predictors'] == b'true')
        keys = set(frozen.loc[frozen.line.eq(name.split('_', 1)[1]), 'policy_id'])
        independent = np.fromiter((pid in keys for pid in before['policy_id'].to_pylist()), dtype=bool, count=before.num_rows)
        check(name + ': all and only frozen policy histories marked, independent set algorithm', np.array_equal(independent, after[a.FLAG].to_numpy()))
        positions = np.flatnonzero(independent)
        book = ledger.loc[ledger.source_table.eq(name)]
        check(name + ': ledger gives exact positions and source row IDs', book.source_position.tolist() == positions.tolist() and book.row_id.tolist() == before.take(pa.array(positions))['row_id'].to_pylist())
        second, changed = a.append_flag(after, sorted(keys), cohort_sha)
        check(name + ': idempotent without adding or changing cells', not changed and second.equals(after, check_metadata=True))
        # A wrong noncohort flag must fail closed, never silently reset it.
        probe = before.slice(0, min(20, before.num_rows))
        once, _ = a.append_flag(probe, sorted(keys), cohort_sha)
        wrong = once.set_column(once.schema.get_field_index(a.FLAG), field, pc.invert(once[a.FLAG]))
        try:
            a.append_flag(wrong, sorted(keys), cohort_sha)
        except ValueError:
            rejected = True
        else:
            rejected = False
        check(name + ': conflicting prior flag rejected', rejected)
        # The live Pandas consumer must actually expose this as a bool and retain all source fields.
        sample = after.slice(0, 20).to_pandas()
        check(name + ': pandas roundtrip reads boolean audit column', pd.api.types.is_bool_dtype(sample[a.FLAG]))
        marked += len(book); total += after.num_rows
        all_ids.extend(after['row_id'].to_pylist())
    check('All 3035950 policy rows and identifiers remain unique', total == 3035950 and len(set(all_ids)) == total)
    check('12041 marked periods, 9110 train and 2931 test', marked == 12041 and ledger.source_table.str.startswith('policies_').sum() == 9110 and ledger.source_table.str.startswith('test_').sum() == 2931)
    check('2742 policies, fixed line counts', ledger.policy_id.nunique() == 2742 and ledger[['policy_id','source_table']].assign(line=lambda x:x.source_table.str.split('_', n=1).str[1]).groupby('line').policy_id.nunique().to_dict() == {'buildings':1010,'contents':219,'motor':1513})
    check('2742 preceding and 2742 successor anchors preserved', ledger.role.eq('declined_2024_anchor').sum() == 2742 and ledger.role.eq('successor_2025_anchor').sum() == 2742)
    for name in set(parent) - set(c.TABLES):
        check('Unchanged complete catalog reference: ' + name, new[name] == parent[name])
        check('Unchanged referenced file: ' + name, c.digest(c.ROOT / new[name]['workspace_relative_path']) == parent[name]['sha256'])
    claims = pq.read_table(c.ROOT / new['claims']['workspace_relative_path'])
    check('All 162546 DUP01 claims retained unchanged', claims.num_rows == 162546 and new['claims'] == parent['claims'])
    for path, sha in json.loads((out / 'protected_hashes_before.json').read_text('utf-8')).items():
        check('Protected source/parent/index unchanged before publication: ' + path, c.digest(c.ROOT / path) == sha)
    s = json.loads((out / 'summary.json').read_text('utf-8'))
    check('No date, decision, exposure or claim correction', s['original_cells_changed'] == 0 and not any(s[k] for k in ['dates_changed','labels_changed','exposure_changed','claims_changed','models_trained']))
    result = {'status': 'passed_own_technical_verification', 'passed': len(checks), 'failed': 0, 'checks': checks,
        'reversal_verified': True, 'idempotence_verified': True, 'conflicting_state_rejected': True, 'independent_validation': False}
    c.dump(out / 'verification.json', result)
    print(json.dumps({'status':result['status'], 'passed':len(checks), 'failed':0}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
