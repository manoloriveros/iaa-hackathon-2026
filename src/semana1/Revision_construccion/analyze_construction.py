"""Revisión CON01 y candidato reversible; nunca activa ni sustituye el catálogo preparado."""
from pathlib import Path
from datetime import datetime, timezone
import sys
import json
import shutil
import uuid

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'Hackaton/Semana 1/Limpieza'))
import clean_data as c
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

REQUEST = 'Revisemos al detalle si T y W representan el mismo tipo de construcción, comparando el historial de las pólizas antes y después de 2023, y decidamos si podemos unificarlos sin tocar los originales.'
MAP = {'t': 'tw_code', 'w': 'tw_code'}
FIELD = 'construction_type_harmonized'
KNOWN = ['brick', 'non_standard', 'stone', 't', 'w']
BUILDINGS = ['policies_buildings', 'test_buildings']
CONTEXT = ['customer_id', 'address_id', 'occupancy', 'days_unoccupied', 'smoke_alarms',
           'accidental_damage_cover', 'mortgage', 'voluntary_excess', 'compulsory_excess',
           'channel', 'payment_method', 'sum_insured', 'written_premium', 'exposure']


def harmonize(values):
    if values.isna().any() or not values.isin(KNOWN + ['tw_code']).all():
        raise ValueError('Unreviewed or missing code: stop instead of guessing its material.')
    return values.replace(MAP)


def load_frames(catalog):
    frames = []
    for name in BUILDINGS:
        f = pq.read_table(ROOT / catalog[name]['workspace_relative_path']).to_pandas()
        f['source_row'] = np.arange(len(f))
        f['source_table'] = name
        frames.append(f)
    f = pd.concat(frames, ignore_index=True)
    f['period_start'] = pd.to_datetime(f.period_start)
    f['period_end'] = pd.to_datetime(f.period_end)
    f['year'] = f.period_start.dt.year
    return f.sort_values(['policy_id', 'period_start', 'period_end', 'row_id']).reset_index(drop=True)


def main():
    active = ROOT / 'Hackaton/Semana 1/Limpieza/current_dataset.json'
    pointer = json.loads(active.read_text(encoding='utf-8'))
    parent = ROOT / pointer['workspace_relative_run']
    catalog = json.loads((ROOT / pointer['catalog_workspace_relative']).read_text(encoding='utf-8'))
    manifest = json.loads((parent / 'manifest.json').read_text(encoding='utf-8'))
    assert all(c.digest(parent / item['path']) == item['sha256'] for item in manifest['files'])
    assert json.loads((parent / 'verification.json').read_text(encoding='utf-8'))['passed']
    ident = datetime.now(timezone.utc).strftime('construction_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
    out = BASE / 'runs' / ident
    for name in ['tables', 'candidate/data', 'candidate/ledger', 'evidence', 'source_snapshot', 'figures']:
        (out / name).mkdir(parents=True, exist_ok=False)
    for name in ['analyze_construction.py', 'verify_construction.py', 'render_construction.py', 'README.md']:
        shutil.copy2(BASE / name, out / 'source_snapshot' / name)
    shutil.copy2(Path(c.__file__), out / 'source_snapshot/clean_data.py')
    for name in ['MEMORIA_PROYECTO.md', 'ESTADO_PROYECTO.json', 'DECISIONES.md', 'AGENTS.md']:
        shutil.copy2(ROOT / 'Preparación' / name, out / 'evidence' / ('before_' + name))
    shutil.copy2(active, out / 'evidence/active_dataset_before.json')
    shutil.copy2(ROOT / pointer['catalog_workspace_relative'], out / 'evidence/parent_catalog.json')
    shutil.copy2(parent / 'manifest.json', out / 'evidence/parent_manifest.json')
    dictionary = ROOT / 'Preparación/artifacts/verification/iaa_launch_20261016/pages/data-description.md'
    shutil.copy2(dictionary, out / 'evidence/official_data_description.md')
    protected = {p.relative_to(ROOT).as_posix(): c.digest(p) for p in c.RAW.glob('*.parquet')}
    protected.update({e['workspace_relative_path']: c.digest(ROOT / e['workspace_relative_path']) for e in catalog.values()})
    protected[active.relative_to(ROOT).as_posix()] = c.digest(active)
    c.dump(out / 'protected_hashes_before.json', protected)
    for entry in catalog.values():
        assert c.digest(ROOT / entry['workspace_relative_path']) == entry['sha256']
    f = load_frames(catalog)
    prev = f.groupby('policy_id', sort=False).shift()
    nxt = f.groupby('policy_id', sort=False).shift(-1)
    valid = f.policy_id.eq(f.policy_id.shift())
    same = f.address_id.eq(prev.address_id)
    train = f.source_table.eq('policies_buildings')
    boundary = valid & same & f.year.eq(2023) & prev.year.eq(2022)
    matched = boundary & prev.construction_type.eq('t') & f.construction_type.eq('w')
    same_train = valid & same & train
    pairs = f.loc[valid, ['source_table', 'source_row', 'policy_id', 'row_id', 'address_id',
                           'period_start', 'period_end', 'year', 'construction_type']].copy()
    for col in ['source_table', 'source_row', 'row_id', 'address_id', 'period_start', 'period_end', 'year', 'construction_type']:
        pairs['previous_' + col] = prev.loc[valid, col]
    pairs['same_address'] = same[valid]
    pairs['gap_days'] = ((f.period_start - prev.period_end).dt.days - 1)[valid].astype('int64')
    pairs['harmonized_code_changed'] = harmonize(f.loc[valid, 'construction_type']).ne(harmonize(prev.loc[valid, 'construction_type']))
    pairs.to_parquet(out / 'tables/all_adjacent_pairs.parquet', index=False)
    pairs[pairs.previous_year.eq(2022) & pairs.year.eq(2023)].to_parquet(out / 'tables/boundary_2022_2023.parquet', index=False)
    transitions = pairs.groupby(['previous_year', 'year', 'same_address', 'previous_construction_type', 'construction_type']).size().reset_index(name='transitions')
    transitions.to_csv(out / 'tables/transitions_by_year.csv', index=False)
    contradictory = pairs[pairs.same_address & pairs.harmonized_code_changed]
    contradictory.to_parquet(out / 'tables/same_address_contradictions.parquet', index=False)
    moved = pairs[~pairs.same_address]
    moved.groupby(['previous_construction_type', 'construction_type']).size().reset_index(name='transitions').to_csv(out / 'tables/moved_address_transitions.csv', index=False)
    year = f.groupby(['year', 'source_table', 'construction_type']).agg(rows=('row_id', 'size'),
             policies=('policy_id', 'nunique'), exposure=('exposure', 'sum')).reset_index()
    year['row_share_pct'] = 100 * year.rows / year.groupby('year').rows.transform('sum')
    year['exposure_share_pct'] = 100 * year.exposure / year.groupby('year').exposure.transform('sum')
    year.to_csv(out / 'tables/codes_by_year.csv', index=False)
    stability = []
    for group, mask in [('t_to_w', matched), ('brick_control', boundary & f.construction_type.eq('brick')),
                        ('stone_control', boundary & f.construction_type.eq('stone')),
                        ('non_standard_control', boundary & f.construction_type.eq('non_standard'))]:
        for col in CONTEXT:
            eq = f[col].eq(prev[col]) | (f[col].isna() & prev[col].isna())
            stability.append({'cohort': group, 'field': col, 'pairs': int(mask.sum()),
                              'equal_including_both_missing': int(eq[mask].sum()),
                              'different': int((~eq[mask]).sum())})
    pd.DataFrame(stability).to_csv(out / 'tables/paired_context_stability.csv', index=False)
    pending_path = ROOT / 'Hackaton/Semana 1/Limpieza/runs/capfix_20261016T184904Z_099a22b1/tables/pending_capitals.parquet'
    pending = pq.read_table(pending_path).to_pandas()
    pending_ids = set(pending[pending.source_table.isin(BUILDINGS)].row_id)
    ratios = []
    for code in ['brick', 'non_standard', 'stone', 'w']:
        mask = boundary & f.construction_type.eq(code)
        eligible = mask & ~f.row_id.isin(pending_ids) & ~prev.row_id.isin(pending_ids)
        ratio = (f.sum_insured / prev.sum_insured)[eligible]
        ratios.append({'current_code': code, 'pairs': int(mask.sum()), 'pairs_excluding_frozen_pending_capitals': int(eligible.sum()),
                       'excluded_pending': int((mask & ~eligible).sum()), 'ratio_q25': float(ratio.quantile(.25)),
                       'ratio_median': float(ratio.median()), 'ratio_q75': float(ratio.quantile(.75))})
    pd.DataFrame(ratios).to_csv(out / 'tables/capital_ratios_descriptive.csv', index=False)
    t22 = f.year.eq(2022) & f.construction_type.eq('t')
    tstatus = pd.Series('unclassified', index=f.index)
    tstatus[nxt.year.isna()] = 'no_later_observed_period'
    tstatus[nxt.year.eq(2022)] = 'later_2022_new_address'
    tstatus[nxt.year.eq(2023)] = 'continues_2023_same_address_as_w'
    w23 = f.year.eq(2023) & f.construction_type.eq('w')
    wstatus = pd.Series('unclassified', index=f.index)
    wstatus[prev.year.isna()] = 'first_observed_policy'
    wstatus[prev.year.eq(2023)] = '2023_new_address'
    wstatus[prev.year.eq(2022)] = 'continues_2022_same_address_from_t'
    cohorts = []
    for label, mask, status in [('t_2022', t22, tstatus), ('w_2023', w23, wstatus)]:
        for state, rows in status[mask].value_counts().items():
            cohorts.append({'cohort': label, 'status': state, 'rows': int(rows)})
        f.loc[mask, ['policy_id', 'row_id', 'address_id', 'period_start', 'construction_type']].assign(
            cohort_status=status[mask]).to_parquet(out / 'tables' / (label + '_cohort.parquet'), index=False)
    pd.DataFrame(cohorts).to_csv(out / 'tables/cohort_reconciliation.csv', index=False)
    address_records = []
    for scope, subset in [('train_only', f[train]), ('train_plus_test_confirmation', f)]:
        before = subset[subset.year.lt(2023)].groupby('address_id').construction_type.agg(['first', 'nunique']).rename(columns={'first':'before_code','nunique':'before_unique'})
        after = subset[subset.year.ge(2023)].groupby('address_id').construction_type.agg(['first', 'nunique']).rename(columns={'first':'after_code','nunique':'after_unique'})
        a = before.join(after, how='inner').reset_index()
        a['scope'] = scope
        a.to_parquet(out / 'tables' / (scope + '_address_pairs.parquet'), index=False)
        address_records.extend(a.groupby(['before_code','after_code']).size().reset_index(name='addresses').assign(scope=scope).to_dict('records'))
    pd.DataFrame(address_records).to_csv(out / 'tables/address_before_after.csv', index=False)
    f['harmonized_code'] = harmonize(f.construction_type)
    address_profile = f.groupby('address_id').agg(policies=('policy_id','nunique'), years=('year','nunique'),
                          original_unique_codes=('construction_type','nunique'), harmonized_unique_codes=('harmonized_code','nunique'))
    address_profile.reset_index().to_parquet(out / 'tables/address_consistency.parquet', index=False)
    # Examples selected by explicit conditions, with deterministic policy-id order; no invented cases.
    ids = f[f.construction_type.isin(['t','w'])].groupby('policy_id').year.agg(list)
    full_ids = ids[ids.apply(lambda years: years == [2021,2022,2023,2024,2025])].index
    examples = [
        ('history_1', str(full_ids[0]), 'Historia T,T,W,W,W; se conserva dirección.'),
        ('history_2', str(full_ids[1]), 'Segunda historia completa; capital y prima varían entre años.'),
        ('history_3', str(full_ids[2]), 'Tercer control longitudinal con el mismo inmueble.'),
        ('move_into_w', str(f.loc[w23 & prev.year.eq(2023) & prev.construction_type.eq('brick'),'policy_id'].iloc[0]),
         'Brick a W dentro de 2023, acompañado de cambio de dirección: cambio de riesgo conservado.'),
        ('move_out_of_t', str(f.loc[t22 & nxt.year.eq(2022) & nxt.construction_type.eq('brick'),'policy_id'].iloc[0]),
         'T a brick dentro de 2022 con nueva dirección: la regla no agrupa brick.'),
        ('new_w', str(f.loc[w23 & prev.year.isna(),'policy_id'].iloc[0]),
         'Primera observación W en 2023; no tiene T anterior en esta póliza.')]
    selected = []
    addresses = pq.read_table(ROOT / catalog['addresses']['workspace_relative_path']).to_pandas()
    for name, policy, reason in examples:
        rows = f[f.policy_id.eq(policy)].copy()
        rows['case_id'] = name; rows['reason_selected'] = reason
        selected.append(rows)
    examples_frame = pd.concat(selected, ignore_index=True).merge(addresses, on='address_id', how='left', validate='many_to_one')
    examples_frame.to_parquet(out / 'tables/case_histories.parquet', index=False)
    examples_frame.to_csv(out / 'tables/case_histories.csv', index=False)
    c.dump(out / 'case_selection.json', [{'case_id': x, 'policy_id': y, 'reason': z} for x,y,z in examples])
    newcat = {name: dict(entry) for name, entry in catalog.items()}
    candidate_counts = {}
    for name in BUILDINGS:
        source = ROOT / catalog[name]['workspace_relative_path']
        table = pq.read_table(source)
        source_codes = table['construction_type'].to_pandas()
        values = harmonize(source_codes)
        assert FIELD not in table.column_names
        candidate = table.append_column(pa.field(FIELD, pa.string(), nullable=False), pa.array(values, type=pa.string()))
        dest = out / 'candidate/data' / (name + '.parquet')
        pq.write_table(candidate, dest, compression='zstd')
        group = source_codes.isin(MAP)
        ledger = pd.DataFrame({'source_table': name, 'source_row': np.flatnonzero(group),
            'row_id': table['row_id'].to_pandas()[group], 'source_code': source_codes[group],
            'harmonized_code': values[group], 'rule': 'CON01', 'source_field': 'construction_type',
            'new_field': FIELD, 'source_value_overwritten': False})
        ledger.to_parquet(out / 'candidate/ledger' / (name + '.parquet'), index=False)
        ledger.to_csv(out / 'candidate/ledger' / (name + '.csv'), index=False)
        candidate_counts[name] = {'rows': len(values), 'grouped_t_w_rows': len(ledger), 'preexisting_cells_changed': 0}
        newcat[name] = {'workspace_relative_path': dest.relative_to(ROOT).as_posix(), 'layer': 'candidate_not_active',
            'sha256': c.digest(dest), 'parent_workspace_relative_path': catalog[name]['workspace_relative_path'],
            'parent_sha256': catalog[name]['sha256'], 'added_field': FIELD, 'rule': 'CON01',
            'source_fields_preserved': True, 'grouped_t_w_rows': len(ledger)}
    c.dump(out / 'candidate/dataset_catalog.json', newcat)
    c.dump(out / 'rules.json', {'rule':'CON01', 'map':MAP, 'output_field':FIELD, 'input_field_preserved':True,
        'known_other_classes_unchanged':['brick','stone','non_standard'], 'material_name':'Unconfirmed; do not label timber as source-confirmed.',
        'status':'Technical recommendation with a verified isolated candidate; active catalog unchanged; human activation review pending.',
        'mapping_discovery_inputs':'Training X 2021-2024 only; no claim outcomes or test X to select mapping.',
        'availability_reference':'2024-12-31', 'test_X_role':'2025 confirmation only',
        'historical_backtest_limit':'Do not claim mapping known before 2023 without prior source confirmation. Retain literal-code ablation and declare X-validation schema adaptation.',
        'predictor_use_if_adopted':'Use harmonized construction instead of both literal and harmonized codes; literal t/w identifies calendar regime.',
        'capital_scope':'No changes; CAP01 2073 inherited; all 1454 pending preserved.', 'human_instruction':REQUEST,
        'no_inferred_tariff_effect':'No model or causal estimate; no premium annualization assumption.'})
    firstpost = f[f.year.eq(2023) & prev.year.isna() & f.construction_type.eq('w')]
    summary = {'rows':len(f), 'train_rows':int(train.sum()), 'test_rows':int((~train).sum()),
        'train_t_rows':int((train & f.construction_type.eq('t')).sum()),
        'train_w_rows':int((train & f.construction_type.eq('w')).sum()),
        'test_w_rows':int((~train & f.construction_type.eq('w')).sum()),
        't_w_total':int(f.construction_type.isin(MAP).sum()), 'boundary_pairs':int(boundary.sum()),
        'boundary_t_to_w_pairs':int(matched.sum()), 'boundary_t_to_w_unique_policies':int(f.loc[matched,'policy_id'].nunique()),
        'all_t_2022_continuations_to_other_code_or_address':int((t22 & nxt.year.eq(2023) & (~nxt.construction_type.eq('w') | ~f.address_id.eq(nxt.address_id))).sum()),
        'same_address_train_transitions':int(same_train.sum()),
        'same_address_all_transitions':int((valid & same).sum()), 'same_address_contradictions_after_merge':len(contradictory),
        'all_address_moves':int((valid & ~same).sum()),
        'changed_classes_with_address_move_after_merge':int((valid & ~same & f.harmonized_code.ne(prev.construction_type.replace(MAP))).sum()),
        'addresses':len(address_profile), 'addresses_multiple_policies':int(address_profile.policies.gt(1).sum()),
        'addresses_with_more_than_one_harmonized_class':int(address_profile.harmonized_unique_codes.gt(1).sum()),
        'first_observed_w_policies_2023':int(firstpost.policy_id.nunique()), 'full_ttw_w_w_histories':len(full_ids),
        't_latest_period_end':f.loc[f.construction_type.eq('t'),'period_end'].max().date().isoformat(),
        'w_earliest_period_start':f.loc[f.construction_type.eq('w'),'period_start'].min().date().isoformat(),
        'all_boundary_t_w_start_on_2023_01_01':bool(f.loc[matched,'period_start'].eq(pd.Timestamp('2023-01-01')).all()),
        'all_boundary_t_w_gap_zero':bool(((f.period_start-prev.period_end).dt.days-1)[matched].eq(0).all()),
        'candidate_counts':candidate_counts, 'parent_run':parent.relative_to(ROOT).as_posix(),
        'active_catalog_unchanged':True, 'models_trained':False, 'independent_validation':False}
    c.dump(out / 'summary.json', summary)
    c.dump(out / 'task_origin.json', {'messages':[{'role':'user','content':REQUEST}],
        'ai_contribution':'Codex formulated and checked the temporal recoding hypothesis, generated local analysis, candidate and verification. No external model service call.',
        'human_review':'Requested detailed review; no approval of physical material name or activation claimed.',
        'IAA_references':['Documentation §2 and §§4-6','Governance §2.8','Professional considerations §3.2 and §§3.5-3.6'],
        'excluded_scope':'No claim outcomes, tariff calibration, imputation, additional capital changes, remote compute or submissions.'})
    after = {path: c.digest(ROOT / path) for path in protected}
    assert after == protected
    c.dump(out / 'protected_hashes_after.json', after)
    c.dump(out / 'run.json', {'run_id':ident, 'utc':datetime.now(timezone.utc).isoformat(),
        'python':sys.version, 'pandas':pd.__version__, 'pyarrow':pa.__version__, 'status':'pending_verification',
        'originals_modified':False, 'historical_runs_modified':False, 'active_dataset_modified':False})
    c.dump(BASE / 'current_run.json', {'workspace_relative_run':out.relative_to(ROOT).as_posix(), 'status':'pending_verification'})
    print(json.dumps({'run':str(out), **summary}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
