"""REN00 autorizado: añade una marca de cohorte; ninguna celda fuente se corrige o elimina."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import uuid

import clean_data as c
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT, BASE = c.ROOT, c.BASE
REVIEW = ROOT / 'Hackaton/Semana 1/Revision_rechazos/runs/renewals_20261016T202736Z_b0ddd9b5'
FLAG = 'audit_ren00'
ARCHIVE = ROOT / 'Hackaton/Semana 1/Modelado/archivo/pre_REN00_20261016T203338Z'
REQUEST = ('Aplica REN00 como marca de auditoría en los derivados, conservando las pólizas y sus siniestros. '
           'No cambies fechas ni etiquetas; documenta y valida que renewal_decision quede fuera de los predictores.')


def manifest_ok(path):
    m = json.loads((path / 'manifest.json').read_text('utf-8'))
    return all(c.digest(path / e['path']) == e['sha256'] for e in m['files'])


def append_flag(table, policy_ids, cohort_sha):
    if len(policy_ids) != len(set(policy_ids)):
        raise ValueError('La cohorte tiene IDs repetidos.')
    wanted = pc.is_in(table['policy_id'], value_set=pa.array(policy_ids, type=table.schema.field('policy_id').type))
    field = pa.field(FLAG, pa.bool_(), nullable=False, metadata={
        b'role': b'audit_only', b'rule': b'REN00', b'excluded_from_predictors': b'true',
        b'cohort_sha256': cohort_sha.encode('ascii'),
        b'meaning': b'Policy membership in frozen 2024-declined/2025-successor cohort; not a row-level decision.'})
    if FLAG in table.column_names:
        if not table.schema.field(FLAG).equals(field, check_metadata=True) or not table[FLAG].equals(wanted):
            raise ValueError('REN00 parcial, metadato distinto o marca alterada; no reparar automáticamente.')
        return table, False
    return table.append_column(field, wanted), True


def main():
    active = BASE / 'current_dataset.json'
    pointer = json.loads(active.read_text('utf-8'))
    catalog = json.loads((ROOT / pointer['catalog_workspace_relative']).read_text('utf-8'))
    parent = ROOT / pointer['workspace_relative_run']
    assert manifest_ok(parent) and manifest_ok(REVIEW)
    cohort_path = REVIEW / 'tables/frozen_cohort.parquet'
    frozen = pd.read_parquet(cohort_path)
    assert len(frozen) == frozen.policy_id.nunique() == 2742
    cohort_sha = c.digest(cohort_path)
    if 'REN00' in pointer.get('audit_rules', []):
        marked = 0
        for name in c.TABLES:
            entry = catalog[name]; assert c.digest(ROOT / entry['workspace_relative_path']) == entry['sha256']
            table = pq.read_table(ROOT / entry['workspace_relative_path'])
            ids = frozen.loc[frozen.line.eq(name.split('_', 1)[1]), 'policy_id'].tolist()
            again, changed = append_flag(table, ids, cohort_sha)
            assert not changed and again.equals(table, check_metadata=True)
            marked += pc.sum(table[FLAG]).as_py()
        assert marked == 12041
        print(json.dumps({'status': 'already_applied_verified_noop', 'run': str(parent), 'marked_rows': marked, 'new_columns_added': 0})); return
    reviewed_catalog = json.loads((REVIEW / 'evidence/dataset_catalog.json').read_text('utf-8'))
    assert catalog == reviewed_catalog, 'El snapshot revisado cambió; no ampliar ni trasladar la cohorte automáticamente.'
    out = BASE / 'runs' / (datetime.now(timezone.utc).strftime('renaudit_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8])
    for name in ['data', 'ledger', 'evidence', 'source_snapshot', 'tables']:
        (out / name).mkdir(parents=True, exist_ok=False)
    for name in ['apply_renewal_audit.py', 'verify_renewal_audit.py', 'verify_predictor_exclusion.py', 'finalize_renewal_audit.py', 'clean_data.py']:
        shutil.copy2(BASE / name, out / 'source_snapshot' / name)
    for name, path in {'core_data.py': ROOT / 'Preparación/src/iaa_lab/data.py',
        'predictor_guard.py': ROOT / 'Preparación/src/iaa_lab/predictor_guard.py',
        'test_predictor_guard.py': ROOT / 'Preparación/tests/test_predictor_guard.py',
        'core_runner.py': ROOT / 'Preparación/src/iaa_lab/runner.py'}.items():
        shutil.copy2(path, out / 'source_snapshot' / name)
    protected = {p.relative_to(ROOT).as_posix(): c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']: c.digest(ROOT / e['workspace_relative_path']) for e in catalog.values()})
    for p in [active, ROOT / pointer['catalog_workspace_relative'], parent / 'manifest.json', REVIEW / 'manifest.json', cohort_path]:
        protected[p.relative_to(ROOT).as_posix()] = c.digest(p)
    c.dump(out / 'protected_hashes_before.json', protected)
    for e in catalog.values():
        assert c.digest(ROOT / e['workspace_relative_path']) == e['sha256']
    for name, p in {'parent_index.json': active, 'parent_catalog.json': ROOT / pointer['catalog_workspace_relative'],
        'parent_manifest.json': parent / 'manifest.json', 'review_manifest.json': REVIEW / 'manifest.json',
        'review_verification.json': REVIEW / 'verification.json', 'review_proposal.json': REVIEW / 'proposal.json',
        'frozen_cohort.parquet': cohort_path, 'review_summary.json': REVIEW / 'summary.json',
        'parent_claim_assignment.parquet': parent / 'tables/claim_period_assignment.parquet',
        'protocol_before_REN00.json': ROOT / 'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}.items():
        shutil.copy2(p, out / 'evidence' / name)
    for name in ['MEMORIA_PROYECTO.md', 'ESTADO_PROYECTO.json', 'DECISIONES.md']:
        shutil.copy2(ROOT / 'Preparación' / name, out / 'evidence' / ('before_' + name))
    c.dump(out / 'authorization.json', {'status': 'explicit_participant_authorization', 'messages': [{'role': 'user', 'content': REQUEST}],
        'operation': 'Add REN00 as audit-only membership flag in six new derived policy tables; enforce predictor exclusion.',
        'preserve': 'All source columns, rows, dates, decisions, claims and existing preparation rules.',
        'not_authorized': 'Reclassifying decisions, calendar fixes, row/claim exclusion, training or global modeling approval.'})
    newcat = {k: dict(v) for k, v in catalog.items()}
    ledgers, schemas = [], []
    anchors_before = dict(zip(frozen.previous_row_id, frozen.row_id))
    anchors_after = set(frozen.row_id)
    for name in c.TABLES:
        entry = catalog[name]; source = ROOT / entry['workspace_relative_path']
        table = pq.read_table(source)
        ids = frozen.loc[frozen.line.eq(name.split('_', 1)[1]), 'policy_id'].tolist()
        result, added = append_flag(table, ids, cohort_sha)
        assert added and result.drop([FLAG]).equals(table, check_metadata=True)
        dest = out / 'data' / (name + '.parquet')
        pq.write_table(result, dest, compression='zstd')
        mask = result[FLAG].to_numpy()
        meta = table.select(['row_id', 'policy_id', 'period_start', 'period_end']).to_pandas()
        meta['source_position'] = range(len(meta))
        mark = meta.loc[mask].copy()
        mark['source_table'] = name
        mark['role'] = ['declined_2024_anchor' if rid in anchors_before else 'successor_2025_anchor' if rid in anchors_after
                        else 'other_2025_segment' if name.startswith('test_') else 'other_cohort_history' for rid in mark.row_id]
        mark['column'] = FLAG; mark['old_column_present'] = False; mark['new_value'] = True
        mark['rule'] = 'REN00'; mark['cohort_sha256'] = cohort_sha
        mark['source_sha256'] = entry['sha256']; mark['derived_sha256'] = c.digest(dest)
        mark['authorization_sha256'] = c.digest(out / 'authorization.json')
        ledgers.append(mark)
        schemas.append({'table': name, 'rows': table.num_rows, 'original_columns': table.num_columns,
            'derived_columns': result.num_columns, 'flag_true': len(mark), 'flag_false': table.num_rows - len(mark),
            'original_values_changed': 0, 'rows_removed': 0, 'rows_added': 0,
            'original_schema_metadata_preserved': True, 'default_for_every_other_row': False})
        newcat[name] = {**entry, 'workspace_relative_path': dest.relative_to(ROOT).as_posix(), 'sha256': c.digest(dest),
            'layer': 'derived', 'parent_workspace_relative_path': entry['workspace_relative_path'], 'parent_sha256': entry['sha256'],
            'audit_rule': 'REN00', 'audit_columns': [FLAG], 'audit_flag_true': len(mark), 'original_values_changed': 0,
            'inherited_capital_changes_preserved': True, 'audit_only_not_predictor': True}
    ledger = pd.concat(ledgers, ignore_index=True)
    assert len(ledger) == 12041 and ledger.policy_id.nunique() == 2742
    ledger.to_parquet(out / 'ledger/ren00_marked_rows.parquet', index=False)
    ledger.to_csv(out / 'ledger/ren00_marked_rows.csv', index=False)
    pd.DataFrame(schemas).to_csv(out / 'ledger/schema_additions.csv', index=False)
    c.dump(out / 'dataset_catalog.json', newcat)
    c.dump(out / 'rules.json', {'rule': 'REN00', 'column': FLAG, 'type': 'nonnullable_boolean', 'role': 'audit_only',
        'scope': 'All published periods of the 2742 policy IDs in the frozen D44 2024-declined/2025-successor cohort, including prior history and all 2025 segments.',
        'true_means': 'Policy belongs to this reviewed cohort, not that this row was declined.',
        'false_means': 'Outside the frozen cohort, not a clean-data certification.',
        'forward_looking_membership': True, 'prediction_use': 'Forbidden even for historical rows; determined from 2024 outcome and 2025 continuity.',
        'anchor_roles_in_ledger_only': True, 'automatic_expansion': False, 'cohort_sha256': cohort_sha,
        'source_decision_semantics_confirmed': False, 'dates_pending': True,
        'reversal': 'Drop only audit_ren00; all original columns, types, metadata and order reconstruct the parent Arrow table.',
        'ledger_defaults': 'Every row absent from the marked-row ledger receives false; schema_additions and source hashes define every added cell.'})
    c.dump(out / 'lineage.json', {'parent_run': parent.relative_to(ROOT).as_posix(), 'review_run': REVIEW.relative_to(ROOT).as_posix(),
        'archive_before_code_and_docs': ARCHIVE.relative_to(ROOT).as_posix(), 'new_rule': 'REN00', 'existing_claims_rule': 'DUP01',
        'cohort_sha256': cohort_sha, 'rows_or_existing_values_changed': 0, 'claims_catalog_entry_unchanged': True,
        'capital_changes_inherited': 2073, 'pending_capitals_unchanged': 1454, 'CON01_activated': False,
        'professional_references': ['IAA Documentation §2 and §§4–6', 'Governance §2.8', 'Professional considerations §3.2 and §§3.5–3.6']})
    c.dump(out / 'summary.json', {'run': out.relative_to(ROOT).as_posix(), 'frozen_policies': 2742, 'all_policy_rows': sum(x['rows'] for x in schemas),
        'marked_rows': len(ledger), 'marked_train_rows': int(ledger.source_table.str.startswith('policies_').sum()),
        'marked_test_rows': int(ledger.source_table.str.startswith('test_').sum()), 'by_table': schemas,
        'ledger_roles': ledger.role.value_counts().to_dict(), 'new_audit_columns_per_table': 1, 'original_cells_changed': 0,
        'policy_rows_removed': 0, 'claims_records': 162546, 'claims_catalog_entry_unchanged': True,
        'dates_changed': False, 'labels_changed': False, 'exposure_changed': False, 'claims_changed': False,
        'models_trained': False, 'T0_operationally_materialized': False, 'independent_validation': False,
        'participant_authorized_audit_mark': True, 'calendar_dates_pending': True})
    assert all(c.digest(ROOT / p) == sha for p, sha in protected.items())
    print(json.dumps({'run': str(out), 'marked_rows': len(ledger), 'marked_test_rows': 2931, 'active_catalog_not_yet_changed': True}))


if __name__ == '__main__':
    main()
