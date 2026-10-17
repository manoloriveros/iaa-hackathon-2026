"""Limpieza reversible v1. Conserva originales y crea una corrida nueva por ejecución."""
from pathlib import Path
from datetime import datetime, timezone
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
TABLES = [f'{prefix}_{line}' for prefix in ['policies', 'test']
          for line in ['motor', 'buildings', 'contents']]
RULES = {
    'version': '1.0',
    'ID01': {'action': 'Pad customer_id ASCII numeric strings on the left to eight characters.',
             'conditions': 'Master unique; exactly eight ASCII digits; every candidate exists in master.',
             'reason': 'Restores lost leading zeros without numeric conversion or ambiguous master keys.'},
    'EXP01': {'action': 'exposure = round(inclusive covered days / 365, 4)',
              'conditions': 'Nonmissing dates, end >= start; raw predominant ACT365; all test matches.',
              'reason': 'Observed mixture of day amounts and ACT360 in training. ACT365 matches test.',
              'status': 'Project preparation assumption supported by data, not organizer confirmation.',
              'leap_year': '366 covered days gives 1.0027; never cap exposure at one.'},
    'CAP00': {'action': 'Review only; preserve all sum_insured values.',
              'screening': 'buildings > 10 million CU; contents > 1 million CU; or 900–1100x consecutive jumps in either direction.',
              'status': 'Screening thresholds are diagnostic, not policy limits or correction rules.'},
    'scope': 'Only customer_id and exposure may change, in six derived policy tables.'
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def canonical_ids(values, master):
    s = values.astype('string')
    if not s.str.fullmatch(r'[0-9]{1,8}').fillna(False).all():
        raise ValueError('Invalid customer_id: stop rather than strip, truncate, or impute.')
    candidate = s.str.zfill(8)
    if not candidate.isin(master).all():
        raise ValueError('Customer absent from master after padding: stop.')
    return candidate


def date_exposure(start, end):
    a, b = pd.to_datetime(start), pd.to_datetime(end)
    if a.isna().any() or b.isna().any() or (b < a).any():
        raise ValueError('Invalid coverage dates: stop.')
    days = (b - a).dt.days + 1
    return days, (days / 365).round(4)


def main():
    run_id = datetime.now(timezone.utc).strftime('clean_%Y%m%dT%H%M%SZ_') + uuid.uuid4().hex[:8]
    out = BASE / 'runs' / run_id
    for child in ['data', 'ledger', 'tables', 'source_snapshot']:
        (out / child).mkdir(parents=True, exist_ok=False)
    before = {p.name: digest(p) for p in sorted(RAW.glob('*.parquet'))}
    dump(out / 'original_hashes_before.json', before)
    dump(out / 'rules.json', RULES)
    for name in ['clean_data.py', 'verify_cleaning.py', 'README.md', 'render_report.py']:
        shutil.copy2(BASE / name, out / 'source_snapshot' / name)
    master = pq.read_table(RAW / 'customers.parquet', columns=['customer_id']).column(0).to_pandas().astype('string')
    assert master.is_unique and master.str.fullmatch(r'[0-9]{8}').all()
    summaries, annual, catalog = [], [], {}
    for name in TABLES:
        raw = pq.read_table(RAW / f'{name}.parquet')
        cols = ['row_id', 'customer_id', 'period_start', 'period_end', 'exposure']
        df = raw.select(cols).to_pandas()
        ids = canonical_ids(df.customer_id, master)
        days, exp = date_exposure(df.period_start, df.period_end)
        assert np.isfinite(df.exposure).all() and (exp > 0).all()
        id_change = ids.ne(df.customer_id)
        exp_change = exp.ne(df.exposure)
        modes = np.select([
            np.abs(df.exposure - days) <= .000051,
            np.abs(df.exposure - days / 360) <= .000051,
            np.abs(df.exposure - days / 365) <= .000051,
        ], ['day_amount', 'ACT360', 'ACT365_rounding'], default='other_mismatch')
        id_ledger = pd.DataFrame({'source_row': df.index[id_change], 'row_id': df.loc[id_change, 'row_id'],
                                  'old': df.loc[id_change, 'customer_id'], 'new': ids[id_change], 'rule': 'ID01'})
        exp_ledger = pd.DataFrame({'source_row': df.index[exp_change], 'row_id': df.loc[exp_change, 'row_id'],
                                   'old': df.loc[exp_change, 'exposure'], 'new': exp[exp_change],
                                   'covered_days': days[exp_change], 'source_convention': modes[exp_change], 'rule': 'EXP01'})
        id_ledger.to_parquet(out / 'ledger' / f'{name}_customer_id.parquet', index=False)
        exp_ledger.to_parquet(out / 'ledger' / f'{name}_exposure.parquet', index=False)
        clean = raw.set_column(raw.schema.get_field_index('customer_id'), raw.schema.field('customer_id'),
                               pa.array(ids, type=pa.string()))
        clean = clean.set_column(raw.schema.get_field_index('exposure'), raw.schema.field('exposure'),
                                 pa.array(exp, type=pa.float64()))
        pq.write_table(clean, out / 'data' / f'{name}.parquet', compression='zstd')
        summary = {'table': name, 'rows': len(df), 'id_changes': int(id_change.sum()),
                   'unmatched_before': int((~df.customer_id.isin(master)).sum()),
                   'unmatched_after': int((~ids.isin(master)).sum()), 'exposure_changes': int(exp_change.sum()),
                   'exposure_before': float(df.exposure.sum()), 'exposure_after': float(exp.sum()),
                   'changed_exposure_modes': pd.Series(modes[exp_change]).value_counts().to_dict()}
        summaries.append(summary)
        grouping = pd.DataFrame({'year': pd.to_datetime(df.period_start).dt.year,
                                  'before': df.exposure, 'after': exp}).groupby('year')[['before', 'after']].sum()
        for year, row in grouping.iterrows():
            annual.append({'table': name, 'year': int(year), **row.to_dict()})
        print(json.dumps(summary), flush=True)
        del raw, clean, df
    # Catalog references untouched masters and claims; no unnecessary copies or overwritten originals.
    for filename in before:
        name = Path(filename).stem
        path = out / 'data' / filename if name in TABLES else RAW / filename
        catalog[name] = {'workspace_relative_path': path.relative_to(ROOT).as_posix(),
                         'layer': 'derived' if name in TABLES else 'original_unchanged', 'sha256': digest(path)}
    dump(out / 'dataset_catalog.json', catalog)
    dump(out / 'summary.json', summaries)
    pd.DataFrame(annual).to_csv(out / 'tables/exposure_by_year.csv', index=False)
    pd.DataFrame([{k: v for k, v in row.items() if k != 'changed_exposure_modes'} for row in summaries]).to_csv(
        out / 'tables/change_summary.csv', index=False)
    capital_summary = []
    for line, threshold in [('buildings', 10_000_000), ('contents', 1_000_000)]:
        parts = []
        for prefix in ['policies', 'test']:
            name = f'{prefix}_{line}'
            data = pq.read_table(RAW / f'{name}.parquet', columns=[
                'row_id', 'policy_id', 'address_id', 'period_start', 'period_end', 'sum_insured']).to_pandas()
            data['table'] = name
            parts.append(data)
        hist = pd.concat(parts, ignore_index=True).sort_values(['policy_id', 'period_start', 'period_end', 'row_id'])
        prev = hist.groupby('policy_id', sort=False)
        hist['previous_row_id'] = prev.row_id.shift()
        hist['previous_sum_insured'] = prev.sum_insured.shift()
        hist['previous_period_end'] = prev.period_end.shift()
        hist['previous_address_id'] = prev.address_id.shift()
        valid_prev = (hist.previous_period_end < hist.period_start) & (hist.previous_sum_insured > 0)
        hist['ratio_to_previous'] = (hist.sum_insured / hist.previous_sum_insured).where(valid_prev)
        hist['high_amount_screen'] = hist.sum_insured > threshold
        hist['jump_up_1000_screen'] = hist.ratio_to_previous.between(900, 1100)
        hist['jump_down_1000_screen'] = (1 / hist.ratio_to_previous).between(900, 1100)
        hist['same_address_as_previous'] = (hist.address_id == hist.previous_address_id) & valid_prev
        hist['decision'] = 'pending_review_no_correction'
        selected = hist[hist.high_amount_screen | hist.jump_up_1000_screen | hist.jump_down_1000_screen]
        selected.to_parquet(out / 'tables' / f'capital_review_{line}.parquet', index=False)
        selected.to_csv(out / 'tables' / f'capital_review_{line}.csv', index=False)
        for name, g in hist.groupby('table'):
            capital_summary.append({'table': name, 'rows': len(g), 'median': float(g.sum_insured.median()),
                'p99': float(g.sum_insured.quantile(.99)), 'max': float(g.sum_insured.max()),
                'high_amount_screen': int(g.high_amount_screen.sum()),
                'jump_up_1000_screen': int(g.jump_up_1000_screen.sum()),
                'jump_down_1000_screen': int(g.jump_down_1000_screen.sum()),
                'review_rows': int(g.row_id.isin(selected.row_id).sum()), 'modified': 0})
    dump(out / 'capital_summary.json', capital_summary)
    after = {p.name: digest(p) for p in sorted(RAW.glob('*.parquet'))}
    dump(out / 'original_hashes_after.json', after)
    assert before == after, 'Original files changed during processing.'
    dump(out / 'run.json', {'run_id': run_id, 'utc': datetime.now(timezone.utc).isoformat(),
         'originals_modified': False, 'capital_modified': False, 'human_review': 'pending',
         'independent_validation': False, 'ai_provider_used_for_corrections': False,
         'python': sys.version, 'pandas': pd.__version__, 'numpy': np.__version__, 'pyarrow': pa.__version__,
         'authorization': 'Participant requested derived cleaning of customer identifiers and exposure; capital review only.'})
    dump(out / 'task_origin.json', {'source': 'Human instruction in Codex chat, 2026-10-16',
        'request_excerpt': 'Ahora limpiemos los datos sin tocar los originales. Empecemos por los identificadores de clientes y la exposición; documenta y valida cada cambio, y revisemos los capitales antes de corregirlos.',
        'ai_contribution': 'Codex generated preparation code, validations and report; no full API conversation export available.',
        'references': ['D30', 'IAA Documentation section 2', 'IAA Governance sections 2.8–2.10']})
    dump(BASE / 'current_run.json', {'workspace_relative_run': out.relative_to(ROOT).as_posix(),
                                    'status': 'pending_verification'})
    print('RUN=' + str(out), flush=True)


if __name__ == '__main__':
    main()
