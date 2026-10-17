"""Revisión forense de capitales. No produce tablas de pólizas corregidas."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

BASE = Path(__file__).parent
RAW = ROOT / 'Hackaton/Semana 1/Datos'
FIELDS = {
    'buildings': ['customer_id', 'address_id', 'construction_type', 'occupancy',
                  'accidental_damage_cover', 'voluntary_excess', 'compulsory_excess', 'smoke_alarms', 'mortgage'],
    'contents': ['customer_id', 'address_id', 'tenure', 'security_level', 'high_value_items',
                 'accidental_damage_cover', 'works_from_home', 'lodgers', 'bicycle_cover',
                 'voluntary_excess', 'compulsory_excess']}
THRESHOLDS = {'buildings': 10_000_000, 'contents': 1_000_000}
CASES = [
    ('E1', 'buildings', 'B00070782', 'Un pico aislado entre capitales de escala habitual'),
    ('C1', 'contents', 'C00010235', 'Un pico aislado en contenidos'),
    ('E2', 'buildings', 'B00270249', 'Capital de test con apoyo de historia anterior'),
    ('E3', 'buildings', 'B19256617', 'Cambio de dirección y dos periodos con escala alta'),
    ('C2', 'contents', 'C67134620', 'Dos periodos altos consecutivos'),
    ('C3', 'contents', 'C00131038', 'Primer periodo alto: el apoyo llega después'),
    ('C4', 'contents', 'C42912460', 'Incremento temporal plausible, sin salto de mil'),
    ('E4', 'buildings', 'B29199704', 'Más de un millón CU, sin pertenecer a la banda extrema')]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False,
        default=lambda v: v.item() if isinstance(v, np.generic) else str(v)), encoding='utf-8')


def main():
    ident = datetime.now(timezone.utc).strftime('capital_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
    out = BASE / 'runs' / ident
    for name in ['tables', 'source_snapshot', 'figures']:
        (out / name).mkdir(parents=True, exist_ok=False)
    paths = list(RAW.glob('*.parquet'))
    clean_pointer = json.loads((ROOT / 'Hackaton/Semana 1/Limpieza/current_run.json').read_text(encoding='utf-8'))
    previous_run = ROOT / clean_pointer['workspace_relative_run']
    paths += list((previous_run / 'data').glob('*.parquet'))
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    save(out / 'protected_hashes_before.json', before)
    for filename in ['analyze_capitals.py', 'render_capitals.py', 'verify_capitals.py', 'README.md']:
        shutil.copy2(BASE / filename, out / 'source_snapshot' / filename)
    save(out / 'protocol.json', {
        'scope': 'Review only. sum_insured is never changed. No corrected policy dataset is written.',
        'screening_thresholds_CU': THRESHOLDS,
        'hypothesis': 'Selected extreme monetary band may contain values stored at 1000 times intended units.',
        'what_if': 'Capital divided by 1000 is diagnostic arithmetic, not an accepted or applied replacement.',
        'proposed_prior_support': 'Nearest earlier non-extreme same-policy capital, within 400 start-date days; same recorded risk, complete specified fields; hypothetical ratio 0.90–1.10.',
        'two_sided': 'Later rows are retrospective evidence only. Never present them as information available at the earlier pricing date.',
        'field_equivalence': 'Case-fold construction labels only; T is not mapped to timber and W is not mapped to wood.',
        'threshold_status': 'Project screening choices, not insurer contract limits, official corrections or learned ground truth.',
        'premium': 'Compare recorded premiums only for long periods of similar duration; no assumption that premium is proportional to capital or exposure.',
        'sensitivity': 'Check hypothetical continuity at 5%, 10%, 20% tolerances; these are evidence bands, not calibrated error probabilities.',
        'references': ['Official archived data-description.md: sum_insured and written_premium',
                       'IAA Documentation section 2; Governance section 2.8; Professional Considerations sections 3.2 and 3.5–3.6'],
        'human_approval': 'pending', 'capital_correction_authorized': False})
    summaries, cohorts, field_changes, sensitivities, growths, bands, cases = [], [], [], [], [], [], []
    addresses = pq.read_table(RAW / 'addresses.parquet').to_pandas().set_index('address_id')
    for line, threshold in THRESHOLDS.items():
        frames = []
        for prefix in ['policies', 'test']:
            name = f'{prefix}_{line}'
            frame = pq.read_table(RAW / f'{name}.parquet').to_pandas()
            frame['source_table'] = name
            frames.append(frame)
        f = pd.concat(frames, ignore_index=True).sort_values(
            ['policy_id', 'period_start', 'period_end', 'row_id']).reset_index(drop=True)
        f['line'] = line
        f['period_start'] = pd.to_datetime(f.period_start)
        f['period_end'] = pd.to_datetime(f.period_end)
        f['year'] = f.period_start.dt.year
        f['covered_days'] = (f.period_end - f.period_start).dt.days + 1
        hi = f.sum_insured > threshold
        f['extreme_band_screen'] = hi
        # This is a hypothesis column, kept separate from the original monetary field.
        f['what_if_div1000_CU'] = (f.sum_insured / 1000).where(hi)
        f['normal_position'] = pd.Series(f.index, index=f.index, dtype='float64').where(~hi)
        g = f.groupby('policy_id', sort=False)
        f['previous_sum_insured'] = g.sum_insured.shift()
        f['next_sum_insured'] = g.sum_insured.shift(-1)
        f['previous_row_id'] = g.row_id.shift()
        f['next_row_id'] = g.row_id.shift(-1)
        f['ratio_to_previous'] = f.sum_insured / f.previous_sum_insured
        f['return_from_extreme'] = ~hi & (f.previous_sum_insured > threshold)
        f['prior_normal_position'] = g.normal_position.ffill().groupby(f.policy_id).shift()
        f['later_normal_position'] = g.normal_position.bfill().groupby(f.policy_id).shift(-1)
        for direction in ['prior', 'later']:
            pos = f[direction + '_normal_position']
            anchor_fields = list(dict.fromkeys(FIELDS[line] + ['row_id', 'sum_insured', 'period_start', 'period_end', 'source_table']))
            anchor = f[anchor_fields].reindex(pos.fillna(-1).astype(int)).reset_index(drop=True)
            exists = pos.notna()
            for field in ['row_id', 'sum_insured', 'period_start', 'period_end', 'source_table', 'address_id', 'customer_id']:
                f[direction + '_' + field] = anchor[field].where(exists)
            known, same = pd.Series(True, index=f.index), pd.Series(True, index=f.index)
            changed_any = pd.Series(False, index=f.index)
            for col in FIELDS[line]:
                a, b = f[col], anchor[col]
                if col == 'construction_type':
                    a, b = a.astype('string').str.casefold().str.strip(), b.astype('string').str.casefold().str.strip()
                pair_known = a.notna() & b.notna() & exists
                changed = pair_known & a.ne(b).fillna(False)
                known &= pair_known
                same &= a.eq(b).fillna(False)
                changed_any |= changed
                if direction == 'prior':
                    field_changes.append({'line': line, 'field': col,
                        'extreme_with_prior_normal_known_pair': int((hi & pair_known).sum()),
                        'changed': int((hi & changed).sum()),
                        'missing_pair': int((hi & exists & ~pair_known).sum())})
            f[direction + '_context_complete'] = known
            f[direction + '_context_same'] = same & exists
            f[direction + '_context_changed'] = changed_any
            delta = f.period_start - anchor.period_start if direction == 'prior' else anchor.period_start - f.period_start
            f[direction + '_start_gap_days'] = delta.dt.days.where(exists)
            if direction == 'prior':
                f['what_if_ratio_to_prior'] = f.what_if_div1000_CU / anchor.sum_insured
                temporal = anchor.period_end < f.period_start
            else:
                f['what_if_ratio_from_later'] = anchor.sum_insured / f.what_if_div1000_CU
                temporal = f.period_end < anchor.period_start
            f[direction + '_eligible_context'] = (known & same & temporal & exists
                & f[direction + '_start_gap_days'].between(1, 400))
        prior_support = hi & f.prior_eligible_context & f.what_if_ratio_to_prior.between(.9, 1.1)
        later_support = hi & f.later_eligible_context & f.what_if_ratio_from_later.between(.9, 1.1)
        contradiction = f.prior_context_changed | f.later_context_changed
        f['review_route'] = np.select([
            hi & prior_support,
            hi & ~prior_support & later_support & ~contradiction,
            hi & f.prior_normal_position.isna() & f.later_normal_position.isna(),
            hi], ['prior_supported', 'retrospective_support_only', 'no_normal_same_policy_reference',
                  'context_or_continuity_review'], default='outside_extreme_screen')
        f['two_sided_stable_10pct'] = prior_support & later_support
        f['later_support_crosses_into_test'] = later_support & f.source_table.str.startswith('policies') & f.later_source_table.str.startswith('test').fillna(False)
        for tolerance in [.05, .10, .20]:
            sensitivities.append({'line': line, 'tolerance': tolerance,
                'prior_stable_supported': int((hi & f.prior_eligible_context & f.what_if_ratio_to_prior.between(1-tolerance, 1+tolerance)).sum()),
                'two_sided_stable_supported': int((hi & f.prior_eligible_context & f.later_eligible_context
                    & f.what_if_ratio_to_prior.between(1-tolerance, 1+tolerance)
                    & f.what_if_ratio_from_later.between(1-tolerance, 1+tolerance)).sum())})
        for name, group in f.groupby('source_table', sort=False):
            h = group.extreme_band_screen
            summaries.append({'table': name, 'rows': len(group), 'policies': group.policy_id.nunique(),
                'extreme_rows': int(h.sum()), 'extreme_pct': float(h.mean()*100),
                'extreme_policies': group.loc[h, 'policy_id'].nunique(),
                'min_extreme_CU': float(group.loc[h, 'sum_insured'].min()),
                'max_non_extreme_CU': float(group.loc[~h, 'sum_insured'].max()),
                'capital_sum_raw_CU': float(group.sum_insured.sum()),
                'extreme_share_of_capital_sum_pct': float(group.loc[h, 'sum_insured'].sum()/group.sum_insured.sum()*100),
                'return_rows_not_to_divide': int(group.return_from_extreme.sum()),
                'two_sided_stable_10pct': int(group.two_sided_stable_10pct.sum())})
            for route, n in group.loc[h, 'review_route'].value_counts().items():
                cohorts.append({'table': name, 'route': route, 'rows': int(n)})
        # Non-extreme within-policy ratios, with similar recorded risk and period spacing.
        normal_stable = ~hi & f.prior_eligible_context & f.previous_row_id.eq(f.prior_row_id)
        for label, mask in [('normal_stable', normal_stable), ('extreme_raw_prior_stable', hi & f.prior_eligible_context),
                            ('extreme_div1000_prior_stable', hi & f.prior_eligible_context)]:
            ratios = f.loc[mask, 'what_if_ratio_to_prior'] if 'div1000' in label else f.loc[mask, 'sum_insured']/f.loc[mask, 'prior_sum_insured']
            growths.append({'line': line, 'group': label, 'n': len(ratios),
                **{f'p{int(q*100):02}': float(ratios.quantile(q)) for q in [.01, .05, .5, .95, .99]}})
        for (table, year), group in f.groupby(['source_table', 'year']):
            bands.append({'table': table, 'year': int(year), 'rows': len(group),
                'extreme_rows': int(group.extreme_band_screen.sum())})
        # Comparable-period premium ratios are corroboration only; quote premium basis is unspecified.
        pos = f.prior_normal_position
        anchor = f[['covered_days', 'written_premium']].reindex(pos.fillna(-1).astype(int)).reset_index(drop=True)
        comparable = hi & f.prior_eligible_context & f.covered_days.ge(300) & anchor.covered_days.ge(300)
        comparable &= (f.covered_days/anchor.covered_days).between(.95, 1.05) & anchor.written_premium.gt(0)
        premium_ratios = f.loc[comparable, 'written_premium']/anchor.loc[comparable, 'written_premium']
        save(out / 'tables' / f'premium_corroboration_{line}.json', {'comparable_long_period_pairs': int(comparable.sum()),
             'ratio_p05': float(premium_ratios.quantile(.05)), 'ratio_median': float(premium_ratios.median()),
             'ratio_p95': float(premium_ratios.quantile(.95)),
             'note': 'Recorded premiums, not loss costs; no assumed linearity or known annualization basis.'})
        affected = set(f.loc[hi, 'policy_id'])
        additional_cases = []
        # Deterministic case showing that distribution alone cannot establish a row-level repair.
        alone = f[hi & f.review_route.eq('no_normal_same_policy_reference') & f.source_table.str.startswith('test')]
        if len(alone):
            additional_cases.append((line[0].upper()+'5', line, alone.iloc[0].policy_id, 'Capital extremo sin referencia normal en la póliza'))
        line_cases = [case for case in CASES + additional_cases if case[1] == line]
        case_ids = {p for _, _, p, _ in line_cases}
        review = f[hi].copy()
        review.to_parquet(out / 'tables' / f'extreme_review_{line}.parquet', index=False)
        review.to_csv(out / 'tables' / f'extreme_review_{line}.csv', index=False)
        f[f.policy_id.isin(affected)].to_parquet(out / 'tables' / f'affected_policy_histories_{line}.parquet', index=False)
        selected = f[f.policy_id.isin(case_ids)].copy()
        for col in ['property_type', 'bedrooms', 'listed_building', 'year_built', 'region']:
            selected[col] = selected.address_id.map(addresses[col])
        selected.to_parquet(out / 'tables' / f'case_histories_{line}.parquet', index=False)
        selected.to_csv(out / 'tables' / f'case_histories_{line}.csv', index=False)
        for key, _, policy, title in line_cases:
            group = selected[selected.policy_id.eq(policy)]
            assert len(group), policy
            cases.append({'case': key, 'line': line, 'policy_id': policy, 'title': title,
                          'rows': len(group), 'extreme_rows': int(group.extreme_band_screen.sum())})
        print(json.dumps({'line': line, 'rows': len(f), 'extreme': int(hi.sum()),
                          'routes': review.review_route.value_counts().to_dict()}), flush=True)
    for name, data in [('summary', summaries), ('cohorts', cohorts), ('field_changes', field_changes),
                        ('sensitivity', sensitivities), ('growth_comparison', growths), ('bands_by_year', bands)]:
        pd.DataFrame(data).to_csv(out / 'tables' / f'{name}.csv', index=False)
        save(out / f'{name}.json', data)
    save(out / 'cases.json', cases)
    after = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    save(out / 'protected_hashes_after.json', after)
    assert before == after
    save(out / 'run.json', {'run': ident, 'utc': datetime.now(timezone.utc).isoformat(),
        'input_originals': 11, 'protected_derived_tables': 6, 'sum_insured_changes': 0,
        'new_corrected_datasets': 0, 'models_trained': False, 'external_ai_calls': False,
        'own_ai_assisted_analysis': True, 'human_review': 'pending', 'independent_validation': False,
        'python': sys.version, 'pandas': pd.__version__, 'pyarrow': pa.__version__,
        'request': 'Revisemos los capitales al detalle: compara el historial de las pólizas, muéstrame casos concretos y definamos cuándo tendría sentido corregir la escala, sin cambiar los valores todavía.'})
    save(BASE / 'current_run.json', {'workspace_relative_run': out.relative_to(ROOT).as_posix(),
                                     'status': 'analysis_complete_verification_pending'})
    print(str(out), flush=True)


if __name__ == '__main__':
    main()
