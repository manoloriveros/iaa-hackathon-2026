"""Revisión descriptiva de dos capitales con ampliación y renovación; no modifica datos."""
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import sys
import uuid
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import correct_capitals as cap
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

BASE = Path(__file__).parent
PIDS = ['C50633171', 'C56600576']
FOCUS = ['C00502745', 'C00399729']
REQUEST = 'Revisemos al detalle los dos casos pendientes C50633171 y C56600576. Compara sus ampliaciones y renovaciones, muestra sus historiales y propón cómo tratarlos sin modificar los datos todavía.'
REVIEW = ROOT/'Hackaton/Semana 1/Revision_referencias_distantes/runs/distant_20261017T001932Z_e9a0e58f'
FIELDS = cap.FIELDS['contents']


def save(frame, out, name):
    frame.to_parquet(out/'tables'/(name+'.parquet'), index=False)
    frame.to_csv(out/'tables'/(name+'.csv'), index=False)


def dates(frame):
    for col in ['period_start', 'period_end']:
        if col in frame:
            frame[col] = pd.to_datetime(frame[col]).dt.as_unit('ns')
    return frame


def peer_cohort():
    """Exploratory cohort defined after seeing focal histories, entirely ORIGINAL 2022/23."""
    cols = list(dict.fromkeys(['row_id', 'policy_id', 'period_start', 'period_end', 'sum_insured', 'renewal_decision', 'renewal_count', 'new_business', *FIELDS]))
    d = dates(pq.read_table(c.RAW/'policies_contents.parquet', columns=cols).to_pandas()).sort_values(['policy_id', 'period_start', 'period_end', 'row_id']).reset_index(drop=True)
    b, z, prev = d.shift(-1), d.shift(-2), d.shift(1)
    sel = (d.policy_id.eq(b.policy_id) & d.policy_id.eq(z.policy_id) & d.period_start.dt.year.eq(2022) & b.period_start.dt.year.eq(2022)
        & z.period_start.eq(pd.Timestamp('2023-01-01')) & d.renewal_decision.eq('mid_term_change')
        & (b.period_start-d.period_end).dt.days.eq(1) & (z.period_start-b.period_end).dt.days.eq(1)
        & d.sum_insured.between(1, 1000000) & b.sum_insured.between(1, 1000000) & z.sum_insured.between(1, 1000000)
        & d.renewal_count.eq(b.renewal_count) & z.renewal_count.eq(d.renewal_count+1)
        & d.new_business.eq(False) & b.new_business.eq(False) & z.new_business.eq(False))
    known, complete = pd.Series(True, index=d.index), pd.Series(True, index=d.index)
    for col in FIELDS:
        for left, right in [(d, b), (d, z), (b, z)]:
            known &= left[col].isna() | right[col].isna() | left[col].eq(right[col])
        complete &= d[col].notna() & b[col].notna() & z[col].notna()
    sel &= known
    result = pd.DataFrame({
        'policy_id': d.loc[sel, 'policy_id'].to_numpy(), 'baseline_row_id': d.loc[sel, 'row_id'].to_numpy(),
        'endorsed_row_id': b.loc[sel, 'row_id'].to_numpy(), 'renewed_row_id': z.loc[sel, 'row_id'].to_numpy(),
        'baseline_CU': d.loc[sel, 'sum_insured'].to_numpy(), 'endorsed_CU': b.loc[sel, 'sum_insured'].to_numpy(),
        'renewed_CU': z.loc[sel, 'sum_insured'].to_numpy(), 'all_D34_fields_known_all_three': complete.loc[sel].to_numpy(),
        'baseline_start': d.loc[sel, 'period_start'].to_numpy(), 'endorsed_start': b.loc[sel, 'period_start'].to_numpy(),
        'renewed_start': z.loc[sel, 'period_start'].to_numpy()})
    result['endorsement_growth_pct'] = 100*(result.endorsed_CU/result.baseline_CU-1)
    result['renewal_vs_endorsed_pct'] = 100*(result.renewed_CU/result.endorsed_CU-1)
    result['renewal_vs_baseline_pct'] = 100*(result.renewed_CU/result.baseline_CU-1)
    result['focus_policy'] = result.policy_id.isin(PIDS)
    prior_normal = (d.policy_id.eq(prev.policy_id) & prev.period_start.dt.year.eq(2021) & prev.period_end.eq(pd.Timestamp('2021-12-31'))
        & d.period_start.eq(pd.Timestamp('2022-01-01')) & prev.sum_insured.between(1, 1000000) & prev[FIELDS].notna().all(axis=1))
    for col in FIELDS:
        for right in [d, b, z]:
            prior_normal &= prev[col].isna() | right[col].isna() | prev[col].eq(right[col])
    result['original_complete_normal_2021_predecessor'] = prior_normal.loc[sel].to_numpy()
    result['predecessor_2021_row_id'] = prev.loc[sel, 'row_id'].to_numpy()
    result['predecessor_2021_CU'] = prev.loc[sel, 'sum_insured'].to_numpy()
    result['baseline2022_vs_original2021_pct'] = np.where(result.original_complete_normal_2021_predecessor, 100*(result.baseline_CU/result.predecessor_2021_CU-1), np.nan)
    return result


def main():
    index = c.BASE/'current_retrospective_dataset.json'
    idx = json.loads(index.read_text('utf-8'))
    assert idx['capital_rule'] == 'CAP05R'
    parent = ROOT/idx['workspace_relative_run']
    catpath = ROOT/idx['catalog_workspace_relative']
    cat = json.loads(catpath.read_text('utf-8'))
    assert cap.manifest_ok(parent) and cap.manifest_ok(REVIEW)
    pending = pd.read_parquet(parent/'tables/pending_capitals.parquet')
    assert len(pending) == 421 and set(FOCUS).issubset(set(pending.row_id))
    out = BASE/'runs'/(datetime.now(timezone.utc).strftime('endorsements_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
    for name in ['tables', 'evidence', 'source_snapshot', 'figures']:
        (out/name).mkdir(parents=True, exist_ok=False)
    protected = {p.relative_to(ROOT).as_posix(): c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']: e['sha256'] for e in cat.values()})
    for path in [*c.BASE.glob('current*.json'), catpath, parent/'manifest.json', parent/'tables/pending_capitals.parquet', REVIEW/'manifest.json',
        REVIEW.parent.parent/'current_run.json', ROOT/'Hackaton/Semana 1/Modelado/protocolo_metodologico.json',
        ROOT/'Preparación/src/iaa_lab/predictor_guard.py', ROOT/'Hackaton/Semana 1/Modelado/target_scope.py']:
        protected[path.relative_to(ROOT).as_posix()] = c.digest(path)
    c.dump(out/'protected_hashes_before.json', protected)
    for name, path in {'retrospective_index.json': index, 'base_index.json': c.BASE/'current_dataset.json', 'dataset_catalog.json': catpath,
        'CAP05R_manifest.json': parent/'manifest.json', 'D57_manifest.json': REVIEW/'manifest.json',
        'D57_held_numeric_conflicts.parquet': REVIEW/'tables/held_numeric_conflicts.parquet',
        'frozen_421_pending.parquet': parent/'tables/pending_capitals.parquet',
        'data-description.md': ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'}.items():
        shutil.copy2(path, out/'evidence'/name)
    shutil.copy2(__file__, out/'source_snapshot'/Path(__file__).name)
    c.dump(out/'request.json', {'messages': [{'role': 'user', 'content': REQUEST}], 'scope': 'Review and propose only; no data, dataset-index, methodological-protocol, guard or target changes.'})
    histories, originals = [], []
    for name in ['policies_contents', 'test_contents']:
        for original, parts in [(False, histories), (True, originals)]:
            path = c.RAW/(name+'.parquet') if original else ROOT/cat[name]['workspace_relative_path']
            f = dates(pq.read_table(path, filters=[('policy_id', 'in', PIDS)]).to_pandas())
            f['source_table'] = name
            parts.append(f)
    h = pd.concat(histories, ignore_index=True).sort_values(['policy_id', 'period_start']).reset_index(drop=True)
    raw = pd.concat(originals, ignore_index=True).sort_values(['policy_id', 'period_start']).reset_index(drop=True)
    assert len(h) == 8 and h.policy_id.nunique() == 2 and h.source_table.eq('policies_contents').all()
    save(h, out, 'all_policy_histories')
    save(raw, out, 'all_original_policy_histories')
    customers = h.customer_id.unique().tolist()
    linked, counts = [], []
    for name in ['policies_motor', 'policies_buildings', 'policies_contents', 'test_motor', 'test_buildings', 'test_contents']:
        f = dates(pq.read_table(ROOT/cat[name]['workspace_relative_path'], columns=['row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end'], filters=[('customer_id', 'in', customers)]).to_pandas())
        f['source_table'] = name
        linked.append(f)
        counts.append({'source_table': name, 'rows': len(f), 'policies': f.policy_id.nunique()})
    save(pd.concat(linked, ignore_index=True), out, 'customer_linked_periods')
    save(pd.DataFrame(counts), out, 'linked_source_counts')
    claims = pq.read_table(ROOT/cat['claims']['workspace_relative_path'], filters=[('policy_id', 'in', PIDS)]).to_pandas()
    raw_claims = pq.read_table(c.RAW/'claims.parquet', filters=[('policy_id', 'in', PIDS)]).to_pandas()
    save(claims, out, 'all_claim_histories')
    save(raw_claims, out, 'all_original_claim_histories')
    save(pq.read_table(ROOT/cat['addresses']['workspace_relative_path'], filters=[('address_id', 'in', h.address_id.unique().tolist())]).to_pandas(), out, 'address_context')
    save(pq.read_table(ROOT/cat['customers']['workspace_relative_path'], columns=['customer_id', 'household_size', 'customer_since_year', 'prior_claims_5y'], filters=[('customer_id', 'in', customers)]).to_pandas(), out, 'customer_context')
    deltas, comparisons, assessments, scenarios = [], [], [], []
    for pid, g in h.groupby('policy_id', sort=True):
        g = g.sort_values('period_start').reset_index(drop=True)
        first, start22, endorsed, renew = [g.iloc[i] for i in range(4)]
        hypothesis = first.sum_insured/1000
        for i in range(1, 4):
            left, right = g.iloc[i-1], g.iloc[i]
            for col in h.columns:
                if col in ['row_id', 'policy_id', 'source_table']: continue
                x, y = left[col], right[col]
                same = (pd.isna(x) and pd.isna(y)) or (pd.notna(x) and pd.notna(y) and x == y)
                if not same:
                    deltas.append({'policy_id': pid, 'from_row_id': left.row_id, 'to_row_id': right.row_id,
                        'field': col, 'old_display': None if pd.isna(x) else str(x), 'new_display': None if pd.isna(y) else str(y),
                        'missing_in_pair': bool(pd.isna(x) or pd.isna(y)), 'D34_field': col in FIELDS})
            base = hypothesis if i == 1 else left.sum_insured
            comparisons.append({'policy_id': pid, 'from_row_id': left.row_id, 'to_row_id': right.row_id,
                'transition': ['renewal_2022_if_2021_scaled', 'midterm_2022_observed', 'renewal_2023_observed'][i-1],
                'left_capital_CU': float(base), 'right_capital_CU': float(right.sum_insured),
                'left_is_hypothetical': i == 1, 'capital_change_pct': float(100*(right.sum_insured/base-1)),
                'written_premium_change_pct_descriptive': float(100*(right.written_premium/left.written_premium-1)),
                'uncovered_days': int((right.period_start-left.period_end).days-1), 'renewal_count_change': int(right.renewal_count-left.renewal_count),
                'known_D34_changes': '|'.join(col for col in FIELDS if pd.notna(left[col]) and pd.notna(right[col]) and left[col] != right[col]),
                'unknown_D34_fields': '|'.join(col for col in FIELDS if pd.isna(left[col]) or pd.isna(right[col]))})
        a = {'row_id': first.row_id, 'policy_id': pid, 'source_table': first.source_table, 'line': 'contents',
            'sum_insured': float(first.sum_insured), 'hypothetical_div1000_CU': float(hypothesis),
            'immediate_2022_row_id': start22.row_id, 'immediate_2022_CU': float(start22.sum_insured),
            'immediate_2022_missing_fields': '|'.join(col for col in FIELDS if pd.isna(start22[col])),
            'endorsed_2022_row_id': endorsed.row_id, 'endorsed_2022_CU': float(endorsed.sum_insured),
            'nearest_complete_reference_gap_days': int((endorsed.period_start-first.period_start).days),
            'renewal_2023_row_id': renew.row_id, 'renewal_2023_CU': float(renew.sum_insured),
            'renewal_2023_gap_days': int((renew.period_start-first.period_start).days),
            'hypothesis_to_endorsed_ratio': float(hypothesis/endorsed.sum_insured),
            'growth_2021hyp_to_2022_pct': float(100*(start22.sum_insured/hypothesis-1)),
            'midterm_growth_pct': float(100*(endorsed.sum_insured/start22.sum_insured-1)),
            'renewal_vs_endorsed_pct': float(100*(renew.sum_insured/endorsed.sum_insured-1)),
            'renewal_vs_2022_baseline_pct': float(100*(renew.sum_insured/start22.sum_insured-1)),
            'two_year_base_growth_pct': float(100*(renew.sum_insured/hypothesis-1)),
            'total_observed_covered_days': int(((g.period_end-g.period_start).dt.days+1).sum()),
            'claims_observed': int(claims.policy_id.eq(pid).sum()), 'test2025_reference': False,
            'ordinary_endorsement_preserved': True, 'missing_fields_imputed': False,
            'new_proposal': 'MANUAL_ENDORSE01-R: review exact 2021 row for /1000 only; retain all 2022/2023 limits and nulls.',
            'review_status': 'PROPOSE_MANUAL_RETROSPECTIVE_SCALE_ONLY_NOT_APPLIED', 'correction_authorized': False, 'capital_change_applied': False}
        assessments.append(a)
        for scenario, value, rationale in [
            ('KEEP_CURRENT_PENDING', first.sum_insured, 'Conserva observación literal, pero mantiene posible error de unidad.'),
            ('DIV1000_2021_ONLY_NOT_APPLIED', hypothesis, 'Hipótesis de escala con ampliación y renovación separadas; propuesta manual retrospectiva.'),
            ('COPY_2022_ENDORSEMENT_REJECTED', endorsed.sum_insured, 'Copiaría el nivel de otro periodo y alteraría cobertura histórica sin soporte.'),
            ('INTERPOLATE_OR_SMOOTH_REJECTED', (start22.sum_insured+renew.sum_insured)/2, 'Inventaría un importe contractual e ignoraría la ampliación observada.')]:
            scenarios.append({'row_id': first.row_id, 'policy_id': pid, 'scenario': scenario, 'illustrative_2021_CU': float(value),
                'rationale': rationale, 'applied': False})
    assessment = pd.DataFrame(assessments)
    save(pd.DataFrame(deltas), out, 'all_adjacent_field_changes')
    save(pd.DataFrame(comparisons), out, 'transition_comparisons')
    save(assessment, out, 'assessment_2')
    save(assessment, out, 'proposed_manual_scale_changes_NOT_APPLIED')
    save(pd.DataFrame(scenarios), out, 'scenarios_NOT_APPLIED')
    peers = peer_cohort()
    save(peers, out, 'original_2022_2023_triads_including_focus')
    peers = peers.loc[~peers.focus_policy].reset_index(drop=True)
    save(peers, out, 'other_original_2022_2023_triads')
    stats = []
    for metric in ['endorsement_growth_pct', 'renewal_vs_endorsed_pct', 'renewal_vs_baseline_pct']:
        x = peers[metric]
        for stat, val in [('count', len(x)), ('minimum', x.min()), ('q25', x.quantile(.25)), ('median', x.median()), ('q75', x.quantile(.75)), ('maximum', x.max())]:
            stats.append({'metric': metric, 'statistic': stat, 'value': float(val)})
    save(pd.DataFrame(stats), out, 'peer_statistics')
    save(peers.head(6), out, 'other_policy_examples')
    summary = {'policies': 2, 'focus_rows': 2, 'history_rows': 8, 'training_rows': 8, 'test_rows': 0,
        'claims': len(claims), 'raw_claims': len(raw_claims), 'other_customer_policies': int(pd.concat(linked).loc[lambda x: ~x.policy_id.isin(PIDS)].policy_id.nunique()),
        'ordinary_triads_including_focus': len(peers)+2, 'other_original_triads': len(peers),
        'other_triads_all_D34_known': int(peers.all_D34_fields_known_all_three.sum()),
        'other_triads_endorsement_above20pct': int(peers.endorsement_growth_pct.gt(20).sum()),
        'other_triads_growth20_drop10_return_within10pct': int((peers.endorsement_growth_pct.gt(20) & peers.renewal_vs_endorsed_pct.lt(-10) & peers.renewal_vs_baseline_pct.abs().le(10)).sum()),
        'other_triads_original_complete_normal_2021': int(peers.original_complete_normal_2021_predecessor.sum()),
        'proposed_manual_scale_rows_NOT_APPLIED': 2, 'current_pending_unchanged': 421, 'other_pending_not_adjudicated': 419,
        'base_pending_unchanged': 1454, 'capital_changes': 0, 'correction_authorized': False,
        'methodology_version_unchanged': '1.9', 'dataset_indexes_changed': False, 'models_trained': False, 'independent_validation': False}
    c.dump(out/'summary.json', summary)
    c.dump(out/'protocol.json', {'status': 'REVIEW_ONLY_NO_OPERATION_AUTHORIZED', 'candidate_rule': 'MANUAL_ENDORSE01-R proposal v1, exact two rows only',
        'fields': FIELDS, 'reference_logic': 'Separate start-of-year baseline transitions from observed midterm endorsement and later renewal. Keep nearest complete endorsement explicitly; do not claim DIST01-R passed.',
        'cohort': 'Original contents 2022 baseline with mid_term_change, next contiguous 2022 segment, next contiguous Jan1-2023 renewal; ordinary capitals 1..1m in three rows; same policy, no known pairwise D34 change, all not new business, renewal_count constant within2022 and +1 in2023. No capital-change-size or reversion criterion used to select.',
        'cohort_origin': 'Exploratory criteria chosen after inspecting focal histories; excludes the two focal policies from peer statistics. Not an independent validation sample, representativeness proof, statistical probability or insurer contract rule.',
        'original_ordinary_screen': '1m CU is historical contents anomaly screen, not contractual maximum.',
        'missing': 'Unknown context remains unknown; no fill by equal neighbors.',
        'temporal': '2021 scale proposal relies on future 2022/2023 train evidence; no test2025 evidence. Retrospective only, no causal backtest approval.',
        'premium': 'Source describes charged premium, not annual/prorated convention. Compare descriptive amounts only, do not infer unit or annualize to prove limits.',
        'labels': 'renewal_decision describes observed row outcome and is diagnostic only, blocked as predictor; no new feature created.',
        'uncertainty': 'No endorsement document, inventory, unit confirmation or explanation for renewal reversion. Repeated peer pattern supports internal consistency only.'})
    c.dump(out/'proposal.json', {'status': 'proposed_only_no_data_change', 'recommendation': 'Propose two manual retrospective /1000 corrections of 2021 rows only under a separate authorization. Preserve 39400/37700 endorsements, 28300/26700 renewals, every null, date, claim and other pending row.',
        'why': 'Each /1000 baseline gives small start-of-year increases; actual 2022 increase and 2023 reduction are present in a broad original-data peer cohort. A temporary capital level can coexist with a scale error in another period.',
        'current_status': 'Both remain pending among421; current DIST01-R and the general400-day rule still fail/not expanded. No layer or audit flag applied.',
        'reject': ['Copying 2022 endorsement into2021', 'Correcting/smoothing the 2022 endorsement or2023 renewal', 'Imputing the two missing context values', 'Claiming lower premium or zero claims proves capital', 'Global automatic expansion'],
        'IAA': ['Documentation §2 and §§4–6', 'Governance §2.8', 'Professional considerations §3.2 and §§3.5–3.6']})
    assert all(c.digest(ROOT/path) == digest for path, digest in protected.items())
    print(json.dumps({'run': str(out), 'summary': summary, 'assessment': assessment.to_dict('records')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
