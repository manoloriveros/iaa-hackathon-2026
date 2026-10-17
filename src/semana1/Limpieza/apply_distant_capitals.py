"""CAP05R: aplica únicamente las 46 propuestas D57 autorizadas, sobre CAP04R."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import uuid
import clean_data as c
import correct_capitals as cap
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT, BASE = c.ROOT, c.BASE
REVIEW = ROOT/'Hackaton/Semana 1/Revision_referencias_distantes/runs/distant_20261017T001932Z_e9a0e58f'
INDEX = BASE/'current_retrospective_dataset.json'
OP_INDEX = BASE/'current_distant_capital_correction.json'
RULE = 'CAP05R'
COUNTS = {'policies_buildings': 11, 'policies_contents': 22, 'test_buildings': 7, 'test_contents': 6}
REQUEST = ('Aplica la división por mil a las 46 filas propuestas en una nueva capa retrospectiva. '
           'Conserva originales y los otros 421 pendientes; señala los 7 respaldos de test 2025 y documenta y valida cada cambio.')
SCRIPTS = ['apply_distant_capitals.py', 'verify_distant_capitals.py', 'finalize_distant_capitals.py', 'clean_data.py', 'correct_capitals.py']


def save(frame, path):
    frame.to_parquet(path.with_suffix('.parquet'), index=False)
    frame.to_csv(path.with_suffix('.csv'), index=False)


def main():
    assert cap.manifest_ok(REVIEW)
    proposal = REVIEW/'tables/proposed_scale_changes_NOT_APPLIED.parquet'
    frozen = pd.read_parquet(proposal)
    cohort_sha = c.digest(proposal)
    assert cohort_sha == 'c0c1e6c9a9aa173020ad71c07e583681cdc83a3c609ba675e63006dae5d6f0d3'
    assert len(frozen) == frozen.row_id.nunique() == 46
    assert frozen.source_table.value_counts().to_dict() == COUNTS
    assert frozen.selected_reference_test2025.sum() == 7
    pointer = json.loads(INDEX.read_text('utf-8'))
    parent = ROOT/pointer['workspace_relative_run']
    catalog_path = ROOT/pointer['catalog_workspace_relative']
    catalog = json.loads(catalog_path.read_text('utf-8'))
    assert cap.manifest_ok(parent)
    assert all(c.digest(ROOT/e['workspace_relative_path']) == e['sha256'] for e in catalog.values())
    if pointer.get('capital_rule') == RULE:
        assert pointer['cohort_sha256'] == cohort_sha and pointer['capital_changes_this_layer'] == 46
        assert c.digest(BASE/'current_dataset.json') == pointer['base_catalog_index_sha256']
        assert pointer['pending_capitals'] == 421 and pointer['later_test2025_supported_rows'] == 136
        assert json.loads(OP_INDEX.read_text('utf-8'))['workspace_relative_run'] == pointer['workspace_relative_run']
        for name, part in frozen.groupby('source_table'):
            values = pq.read_table(ROOT/catalog[name]['workspace_relative_path'], columns=['row_id', 'sum_insured']).to_pandas().set_index('row_id').sum_insured
            assert np.array_equal(values.loc[part.row_id].to_numpy(), part.hypothetical_div1000_CU.to_numpy())
        print(json.dumps({'status': 'already_applied_verified_noop', 'run': str(parent), 'new_changes': 0, 'CAP05R_changes': 46}))
        return
    if pointer.get('capital_rule') != 'CAP04R' or catalog != json.loads((REVIEW/'evidence/dataset_catalog.json').read_text('utf-8')):
        raise ValueError('La capa difiere del padre D57: no trasladar o ampliar la cohorte.')
    assert c.digest(INDEX) == c.digest(REVIEW/'evidence/retrospective_index.json')
    pending = pd.read_parquet(parent/'tables/pending_capitals.parquet')
    assert len(pending) == 467 and set(frozen.row_id).issubset(set(pending.row_id))
    out = BASE/'runs'/(datetime.now(timezone.utc).strftime('capdistant_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['data', 'ledger', 'tables', 'evidence', 'source_snapshot']:
        (out/name).mkdir(parents=True, exist_ok=False)
    protected = {p.relative_to(ROOT).as_posix(): c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']: e['sha256'] for e in catalog.values()})
    for path in [*BASE.glob('current*.json'), catalog_path, parent/'manifest.json', REVIEW/'manifest.json', proposal, REVIEW.parent.parent/'current_run.json', ROOT/'Preparación/src/iaa_lab/predictor_guard.py', ROOT/'Hackaton/Semana 1/Modelado/target_scope.py']:
        if path.exists():
            protected[path.relative_to(ROOT).as_posix()] = c.digest(path)
    c.dump(out/'protected_hashes_before.json', protected)
    copies = {
        'parent_index.json': INDEX, 'base_index.json': BASE/'current_dataset.json', 'parent_catalog.json': catalog_path,
        'parent_manifest.json': parent/'manifest.json', 'review_manifest.json': REVIEW/'manifest.json',
        'review_verification.json': REVIEW/'verification.json', 'review_proposal.json': REVIEW/'proposal.json',
        'review_protocol.json': REVIEW/'protocol.json', 'frozen_46_proposal.parquet': proposal,
        'frozen_467_pending.parquet': parent/'tables/pending_capitals.parquet',
        'assessment_48.parquet': REVIEW/'tables/assessment_48.parquet',
        'policy_histories.parquet': REVIEW/'tables/all_policy_histories.parquet',
        'direction_evaluations.parquet': REVIEW/'tables/direction_evaluations.parquet',
        'intermediate_nodes.parquet': REVIEW/'tables/intermediate_nodes.parquet',
        'chain_edges.parquet': REVIEW/'tables/chain_edges.parquet',
        'held_numeric_conflicts.parquet': REVIEW/'tables/held_numeric_conflicts.parquet',
        'CAP01_ledger.parquet': parent/'evidence/CAP01_ledger.parquet',
        'prior_retrospective_ledger.parquet': parent/'ledger/cumulative_retrospective_changes.parquet',
        'protocol_before_CAP05R.json': ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json'}
    for name, path in copies.items():
        shutil.copy2(path, out/'evidence'/name)
    for name in SCRIPTS:
        shutil.copy2(BASE/name, out/'source_snapshot'/name)
    c.dump(out/'authorization.json', {
        'status': 'explicit_participant_authorization', 'rule': RULE, 'decision_criterion': 'DIST01-R v1, frozen D57 list only',
        'messages': [{'role': 'user', 'content': REQUEST}], 'cohort_sha256': cohort_sha,
        'scope': 'Exact 46 D57 rows: sum_insured /1000 only; four new derived household tables on CAP04R, including 13 test rows.',
        'preserve': 'Originals, prior runs, other cells, all 421 remaining pending including 108 no-anchor and two D57 numeric conflicts.',
        'historical_flags': 'False authorization/application flags in the frozen proposal remain review-time evidence; this later request authorizes this operation.',
        'not_approved': 'General extension of 400-day criterion, cascading, imputation, dates, claims, T/W merge, causal backtests or training.'})
    assessment = pd.read_parquet(out/'evidence/assessment_48.parquet')
    selected = assessment.loc[assessment.row_id.isin(frozen.row_id)].copy()
    assert len(selected) == 46 and selected.candidate_NOT_APPLIED.all()
    ledgers = []
    newcat = {k: dict(v) for k, v in catalog.items()}
    for name, part in selected.groupby('source_table', sort=True):
        entry = catalog[name]
        before = pq.read_table(ROOT/entry['workspace_relative_path'])
        positions = pd.Series(range(before.num_rows), index=before['row_id'].to_pylist())
        part = part.copy()
        part['source_position'] = positions.loc[part.row_id].to_numpy()
        part = part.sort_values('source_position').reset_index(drop=True)
        pos = part.source_position.to_numpy(dtype=int)
        old, new = part.sum_insured.to_numpy(), part.hypothetical_div1000_CU.to_numpy()
        assert len(part) == COUNTS[name] and np.array_equal(before['sum_insured'].to_numpy()[pos], old)
        assert np.array_equal(old/1000, new)
        result, count = cap.apply_frozen(before['sum_insured'].to_numpy(), pos, old, new)
        assert count == len(part)
        after = before.set_column(before.schema.get_field_index('sum_insured'), before.schema.field('sum_insured'), pa.array(result, type=before.schema.field('sum_insured').type))
        dest = out/'data'/(name+'.parquet')
        pq.write_table(after, dest, compression='zstd')
        part['old'], part['new'], part['rule'], part['divisor'] = old, new, RULE, 1000
        part['audit_ref_test2025'] = part.selected_reference_test2025
        part['corrected_row_is_test2025'] = name.startswith('test_')
        part['reference_is_future_at_focus_start'] = part.selected_reference_future
        part['historical_availability_confirmed'] = False
        part['retrospective_only'], part['operation_authorized'] = True, True
        part['correction_authorized'], part['capital_change_applied'] = True, True
        part['source_sha256'], part['derived_sha256'] = entry['sha256'], c.digest(dest)
        part['cohort_sha256'], part['authorization_sha256'] = cohort_sha, c.digest(out/'authorization.json')
        save(part, out/'ledger'/(name+'_sum_insured'))
        ledgers.append(part)
        newcat[name] = {**entry, 'workspace_relative_path': dest.relative_to(ROOT).as_posix(), 'sha256': c.digest(dest),
            'distant_capital_parent_workspace_relative_path': entry['workspace_relative_path'], 'distant_capital_parent_sha256': entry['sha256'],
            'distant_capital_rule': RULE, 'distant_capital_changes': len(part),
            'distant_capital_test2025_supported_changes': int(part.audit_ref_test2025.sum()),
            'distant_capital_ledger_workspace_relative_path': (out/'ledger'/(name+'_sum_insured.parquet')).relative_to(ROOT).as_posix()}
    ledger = pd.concat(ledgers, ignore_index=True)
    save(ledger, out/'ledger/all_capital_changes')
    save(ledger.loc[ledger.audit_ref_test2025], out/'ledger/test2025_supported_changes')
    save(ledger.loc[ledger.corrected_row_is_test2025], out/'ledger/corrected_test2025_rows')
    remaining = pending.loc[~pending.row_id.isin(frozen.row_id)].copy()
    assert len(remaining) == 421
    save(remaining, out/'tables/pending_capitals')
    inherited = pd.read_parquet(out/'evidence/prior_retrospective_ledger.parquet')
    current = ledger[['row_id', 'policy_id', 'line', 'source_table', 'old', 'new', 'rule', 'audit_ref_test2025', 'selected_reference_row_id', 'selected_reference_source_table', 'selected_reference_period_start']].rename(columns={
        'selected_reference_row_id': 'reference_row_id', 'selected_reference_source_table': 'reference_source_table', 'selected_reference_period_start': 'reference_period_start'})
    current['reference_period_start'] = pd.to_datetime(current.reference_period_start).dt.strftime('%Y-%m-%d')
    cumulative = pd.concat([inherited, current], ignore_index=True)
    save(cumulative, out/'ledger/cumulative_retrospective_changes')
    save(cumulative.loc[cumulative.audit_ref_test2025], out/'ledger/cumulative_test2025_supported_changes')
    c.dump(out/'dataset_catalog.json', newcat)
    c.dump(out/'rules.json', {
        'rule': RULE, 'version': '1.0', 'decision_criterion': 'DIST01-R v1 from D57', 'operation': 'sum_insured /1000',
        'cohort_sha256': cohort_sha, 'cohort_rows': 46, 'selection': 'Frozen authorized proposal; never reselect or use newly repaired references.',
        'D34_context': cap.FIELDS, 'reference_selection': 'Nearest complete ORIGINAL ordinary reference in each direction before comparing context or amount; no skipping contradictory complete references.',
        'distant_exception': 'More than 400 days and at most two calendar years between starts; exactly one original ordinary intermediate row with missing context and no known changes; endpoint and each monetary step within 0.90–1.10.',
        'calendar': 'No overlaps or new gaps; retain known CAL00 Dec30-2024 to Jan1-2025 gap as pending.',
        'general_400day_rule_changed': False, 'automatic_expansion': False, 'retrospective_only': True,
        'anchor_direction_counts': {'prior': 21, 'later': 25}, 'test2025_anchors': 7, 'corrected_test2025_rows': 13,
        'audit_marker': 'audit_ref_test2025 only in ledger; seven anchors (one building, six contents), distinct from thirteen corrected test rows.',
        'pending_preserved': 421, 'held_policies': ['C50633171', 'C56600576'], 'all_other_source_cells_preserved': True,
        'reversal': 'Restore old at source_position in each table to recover the exact parent Arrow table with metadata.',
        'source_unit_confirmation': False, 'T_W_semantic_merge': False, 'approved_for_cutoff_specific_backtesting': False,
        'IAA': ['Documentation §2 and §§4–6', 'Governance §2.8', 'Professional considerations §3.2 and §§3.5–3.6']})
    summary = {'rule': RULE, 'capital_changes': 46, 'changes_by_table': COUNTS, 'changes_by_line': {'buildings': 18, 'contents': 28},
        'test2025_supported_changes': 7, 'test2025_by_line': {'buildings': 1, 'contents': 6}, 'corrected_test2025_rows': 13,
        'prior_anchors': 21, 'later_anchors': 25, 'CAP01_inherited': 2073, 'CAP02R_inherited': 867, 'CAP03R_inherited': 11, 'CAP04R_inherited': 109,
        'cumulative_retrospective_changes': 1033, 'cumulative_test2025_supported_changes': 136, 'total_capital_changes_including_CAP01': 3106,
        'pending_before': 467, 'pending_after': 421, 'pending_by_table': remaining.source_table.value_counts().to_dict(),
        'base_pending_unchanged': 1454, 'originals_modified': False, 'other_fields_changed': 0, 'new_columns': 0, 'rows_removed': 0,
        'base_catalog_changed': False, 'claims_changed': False, 'test_tables_changed': True, 'models_trained': False,
        'retrospective_only': True, 'independent_validation': False, 'approved_for_modeling': False}
    c.dump(out/'summary.json', summary)
    c.dump(out/'lineage.json', {'new_rule': RULE, 'parent_rule': 'CAP04R', 'parent_run': parent.relative_to(ROOT).as_posix(), 'review_run': REVIEW.relative_to(ROOT).as_posix(), 'summary': summary})
    assert all(c.digest(ROOT/path) == sha for path, sha in protected.items())
    print(json.dumps({'run': str(out), 'status': 'created_not_published', 'capital_changes': 46, 'pending': 421}, ensure_ascii=False))


if __name__ == '__main__':
    main()
