"""Preflight del cache fuente: claves, escala, clima y límites; cero aprendizaje."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
LEGACY = BASE/'linaje_T2b_v1'; CANON = BASE/'preflight_anidado_H1_20261026_v1'
HOME = BASE/'A1S_nucleo_20261026_v1'; RAW = ROOT/'Hackaton/Semana 2/Datos/emerging'
OUT = BASE/'P21_cache_T2b_20261026'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

spec = importlib.util.spec_from_file_location('p21_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']
WEATHER = ['wind_exposure_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c']


def dump(path, value):
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def read(path, columns, filters=None):
    result = pd.read_parquet(path, columns=columns, filters=filters)
    IO.append({'path': w.rel(path), 'columns': columns, 'filters': filters, 'rows': len(result)})
    return result


def model_names_only(path):
    # Read text header only; no model library or predictor is constructed.
    with path.open('r', encoding='utf8') as handle:
        for i, line in enumerate(handle):
            if line.startswith('feature_names='):
                return line.rstrip('\n').split('=', 1)[1].split()
            assert i < 20 and not line.startswith('Tree='), 'Unexpected header format'
    raise AssertionError('Missing feature header')


def main():
    global IO
    IO = []
    assert not OUT.exists(); OUT.mkdir()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    legacy_report = w.read(LEGACY/'replay_report.json')
    source_code = R/'herramientas/reconciliar_padre_F2_2024.py'
    paths = [Path(__file__), source_code, LEGACY/'replay_report.json',
        R/'registro/semana2_mision017_padre_F2_replay_v1.json', RAW/'weather.parquet']
    paths += [LEGACY/f'{kind}_{line}.parquet' for line in LINES for kind in ['raw_rates', 'features']]
    paths += [LEGACY/f'modelos/prod/T2b_{line}.txt' for line in LINES]
    paths += [CANON/f'canonical_{line}.parquet' for line in LINES]
    paths += [HOME/f'rows_s2_{line}.parquet' for line in LINES]
    before = {w.rel(path): w.sha(path) for path in paths}
    assert before[w.rel(RAW/'weather.parquet')] == legacy_report['sources'][w.rel(RAW/'weather.parquet')]
    for line in LINES:
        for kind in ['raw_rates', 'features']:
            path = LEGACY/f'{kind}_{line}.parquet'
            assert w.sha(path) == legacy_report['outputs'][path.name]
    weather = read(RAW/'weather.parquet', ['address_id', 'year']+WEATHER,
        filters=[('year', 'in', [2023, 2024])])
    assert weather.year.isin([2023, 2024]).all()
    assert not weather.duplicated(['address_id', 'year']).any()
    climate = weather.groupby('address_id', sort=True)[WEATHER].mean()
    results = []
    for line in LINES:
        rawpath = LEGACY/f'raw_rates_{line}.parquet'; featurepath = LEGACY/f'features_{line}.parquet'
        schema = pq.read_schema(rawpath).names
        rates = read(rawpath, ['row_id', 'year', 'exposure_legacy', 'annual_raw_T2b', 'legacy_fold'])
        c = read(CANON/f'canonical_{line}.parquet', ['row_id', 'year', 'group_id', 'fold',
            'annual_raw_T2b', 'exposure', 'exposure_calendar'])
        f = read(featurepath, ['row_id', 'policy_id', 'address_id', 'year', 'period_start',
            'period_end', 'exposure', 'hist_pol_12m', 'hist_cli_12m']+['clima_'+name for name in WEATHER])
        rows = read(HOME/f'rows_s2_{line}.parquet', ['row_id', 'year', 'is_test', 'policy_id',
            'address_id', 'period_start', 'period_end', 'exposure_calendar'])
        rows = rows.loc[~rows.is_test].copy()
        for frame in [rates, c, f, rows]:
            assert frame.row_id.is_unique and frame.year.isin([2023, 2024]).all()
        assert set(rates.row_id) == set(c.row_id) == set(f.row_id) == set(rows.row_id)
        c = c.sort_values('row_id').reset_index(drop=True)
        rates = rates.set_index('row_id').loc[c.row_id].reset_index()
        f = f.set_index('row_id').loc[c.row_id].reset_index()
        rows = rows.set_index('row_id').loc[c.row_id].reset_index()
        for frame in [rates, f, rows]: assert np.array_equal(frame.year, c.year)
        for name in ['policy_id', 'address_id', 'period_start', 'period_end']:
            assert np.array_equal(f[name], rows[name]), name
        annual_exact = np.array_equal(c.annual_raw_T2b.to_numpy(float), rates.annual_raw_T2b.to_numpy(float))
        assert annual_exact and rates.annual_raw_T2b.gt(0).all()
        calendar = ((pd.to_datetime(f.period_end)-pd.to_datetime(f.period_start)).dt.days+1).to_numpy(float)/365
        assert np.array_equal(calendar, f.exposure.to_numpy(float))
        assert np.array_equal(calendar, rates.exposure_legacy.to_numpy(float))
        assert np.array_equal(calendar, c.exposure_calendar.to_numpy(float))
        assert np.array_equal(np.round(calendar, 4), c.exposure.to_numpy(float))
        wanted = climate.loc[f.address_id].to_numpy(float)
        actual = f[['clima_'+name for name in WEATHER]].to_numpy(float)
        assert np.allclose(wanted, actual, rtol=0, atol=1e-12, equal_nan=True)
        finite = np.isfinite(wanted) & np.isfinite(actual)
        error = float(np.max(np.abs(wanted[finite]-actual[finite])))
        # Independent scalar averages on a deterministic metadata sample.
        for i in np.unique(np.linspace(0, len(f)-1, 12, dtype=int)):
            selected = weather.loc[weather.address_id.eq(f.address_id.iloc[i])]
            for j, name in enumerate(WEATHER):
                values = selected[name].dropna().to_numpy(float)
                expected = math.fsum(values.tolist())/len(values) if len(values) else float('nan')
                assert (math.isnan(expected) and math.isnan(actual[i, j])) or math.isclose(expected, actual[i, j], rel_tol=2e-15, abs_tol=1e-12)
        names = model_names_only(LEGACY/f'modelos/prod/T2b_{line}.txt')
        keys = set(['row_id', 'customer_id', 'address_id', 'policy_id', 'year', 'period_start', 'period_end', 'exposure'])
        assert set(pq.read_schema(featurepath).names)-keys == set(names)
        # The old customer-only fold is not a current global customer/address partition.
        cross = pd.crosstab(rates.legacy_fold, c.fold)
        histories_missing_by_year = {str(year): {
            name: int(group[name].isna().sum()) for name in ['hist_pol_12m', 'hist_cli_12m']
        } for year, group in f.groupby('year')}
        results.append({'line': line, 'rows': len(c), 'row_keys_periods_exposure_bound': True,
            'annual_raw_exactly_already_in_current_canonical': annual_exact,
            'raw_output_columns': schema, 'peril_outputs_available': any(name.startswith(('f_', 's_')) for name in schema),
            'source_model_feature_count': len(names), 'model_header_read_only_no_inference': True,
            'features_with_unresolved_quote_availability': [n for n in ['discount_applied', 'missed_payments_12m'] if n in names],
            'fixed_climate_mean_2023_2024_exact': True, 'climate_max_absolute_error': error,
            'history_missing_by_year': histories_missing_by_year,
            'calendar_vs_rounded_exposure_max_abs': float(np.max(np.abs(calendar-c.exposure.to_numpy(float)))),
            'legacy_to_current_fold_crosstab': {str(a): {str(b): int(v) for b, v in row.items()} for a, row in cross.iterrows()},
            'old_fold_labels_cannot_certify_current_grouped_target_learning': True})
    assert before == {w.rel(path): w.sha(path) for path in paths}
    dump(OUT/'read_receipt.json', IO)
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'P21cache_preflight_complete_no_new_model_evidence', 'results': results,
        'sources': before, 'read_receipt': w.rel(OUT/'read_receipt.json'),
        'read_receipt_sha256': w.sha(OUT/'read_receipt.json'),
        'weather_years_loaded': [2023, 2024], 'future2025covariates_read': False,
        'new_model_fits': 0, 'new_C0_fits': 0, 'model_objects_constructed': 0,
        'new_inference': 0, 'new_scores': 0, 'new_submissions': 0,
        'conclusions': [
            'All current canonical raw T2b annual rates already equal this saved cache; treating the same rates as a newly obtained source would duplicate existing information.',
            'Climate uses address mean of2023/2024, available as a retrospective climatology at start2025; it includes held-year weather and cannot support a prospective2023or2024claim.',
            'The cache has one annual total rate, not frequency/severity per-peril objects; FSp is a different source recipe.',
            'Calendar exposure is stored exactly; current learning uses its4decimal version. Preserve the verified ultimate/observed bridge, rather than multiplying exposure a second time.',
            'Saved old fold-specific levels are not part of raw rates and cannot replace protected current target calibration.',
            'Undated masters and some administrative inputs have unresolved quote-time provenance; this audit neither proves them inadmissible nor establishes their prospective availability.',
        ], '2024_open': True, 'B00_all_alternatives_preserved': True,
        'complete_F3c_replay_proven': False, 'private_improvement_established': False, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    print(json.dumps({'status': report['status'], 'rows': sum(a['rows'] for a in results),
        'all_cached_rates_already_used': all(a['annual_raw_exactly_already_in_current_canonical'] for a in results),
        'peril_outputs': any(a['peril_outputs_available'] for a in results), 'new_fits': 0, 'new_scores': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    main()
