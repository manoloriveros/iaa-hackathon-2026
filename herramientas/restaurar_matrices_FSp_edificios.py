"""Restaura matrices de edificios desde los originales, sin ajustar ni inferir."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import gc
import hashlib
import json
import sys

ROOT = Path('C:/dev/Hakaton')
R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'
OUT = BASE / 'FSp_edificios_matrices_20261026_v1'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd

DEV = ROOT / 'Hackaton/Semana 1/Datos'
EM = ROOT / 'Hackaton/Semana 2/Datos/emerging'
OLD = ROOT / 'Hackaton/Semana 2/Claude/ml_independiente_20261023/codigo'
CLIMATE = ['wind_exposure_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c']
V = pd.Timestamp('2024-12-31')
CONSTRUCTION = {'brick': 'brick', 'brk': 'brick', 'stone': 'stone', 'stn': 'stone',
                't': 'timber', 'w': 'timber', 'wod': 'timber',
                'non_standard': 'non_standard', 'mix': 'non_standard'}


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(2 ** 20), b''):
            h.update(block)
    return h.hexdigest()


def rel(p):
    return str(p.relative_to(ROOT)).replace('\\', '/')


def dump(p, a):
    p.write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding='utf8')


def constants():
    out = {}
    for node in ast.parse((OLD / 'variables.py').read_text(encoding='utf8')).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ['POLIZA', 'CLIENTE', 'DIRECCION', 'RAMO', 'CATEGORICAS']:
                out[name] = ast.literal_eval(node.value)
    return out


def base_frame(raw, emerging):
    f = pd.read_parquet(raw / 'policies_buildings.parquet')
    f['is_test'] = False
    if emerging:
        test = pd.read_parquet(raw / 'test_buildings.parquet')
        test['is_test'] = True
        f = pd.concat([f, test], ignore_index=True)
    f['period_start'] = pd.to_datetime(f.period_start)
    f['period_end'] = pd.to_datetime(f.period_end)
    f['year'] = f.period_start.dt.year
    assert f.year.isin([2023, 2024, 2025] if emerging else [2021, 2022, 2023, 2024]).all()
    f['exposure'] = ((f.period_end - f.period_start).dt.days + 1) / 365.
    customers = pd.read_parquet(raw / 'customers.parquet')
    if emerging:
        customers['occupation'] = (customers.occupation.str.lower().str.strip()
                                   .str.replace('self-employed ', '', regex=False).str.strip())
    else:
        customers['occupation'] = customers.occupation.str.lower().str.strip()
    addresses = pd.read_parquet(raw / 'addresses.parquet')
    n = len(f)
    f = f.merge(customers, on='customer_id', how='left', validate='many_to_one', sort=False)
    f = f.merge(addresses, on='address_id', how='left', validate='many_to_one', sort=False)
    assert len(f) == n and f.customer_since_year.notna().all() and f.year_built.notna().all()
    f['tenure_years'] = f.year - f.customer_since_year
    f['property_age'] = f.year - f.year_built
    f['start_month'] = f.period_start.dt.month
    f['full_year'] = (f.exposure >= .99).astype(int)
    f['log_days_quote'] = np.log1p(f.days_quote_to_inception.clip(lower=0))
    f['log_si'] = np.log(np.where(f.sum_insured > 5e6, f.sum_insured / 1000., f.sum_insured))
    if emerging:
        f['age_band'] = f.policyholder_age_band
    else:
        f['age_band'] = pd.cut(f.policyholder_age, [-1, 24, 34, 49, 64, 200],
                               labels=['17-24', '25-34', '35-49', '50-64', '65+']).astype(str)
    f['construction'] = f.construction_type.str.lower().map(CONSTRUCTION)
    assert f.construction.notna().all()
    assert f.row_id.is_unique and f.exposure.gt(0).all()
    return f


def window_counts(keys, ends, events, event_key):
    """Counts [end-365 days,end), by key, retaining notifications of every status."""
    ends = pd.to_datetime(ends).to_numpy(dtype='datetime64[ns]')
    lo = ends - np.timedelta64(365, 'D')
    grouped = {k: np.sort(v.to_numpy(dtype='datetime64[ns]'))
               for k, v in events.groupby(event_key, sort=False).report_date}
    result = np.zeros(len(keys), dtype='float64')
    for k, positions in pd.Series(np.arange(len(keys))).groupby(np.asarray(keys), sort=False):
        ix = positions.to_numpy()
        dates = grouped.get(k)
        if dates is not None:
            result[ix] = (np.searchsorted(dates, ends[ix], side='left')
                          - np.searchsorted(dates, lo[ix], side='left'))
    known = lo >= np.datetime64('2023-01-01', 'ns')
    result[~known] = np.nan
    return result


def histories(target):
    claims = pd.read_parquet(EM / 'claims.parquet', columns=['policy_id', 'line', 'report_date'])
    claims['report_date'] = pd.to_datetime(claims.report_date)
    assert claims.report_date.le(V).all()
    maps = []
    for line in ['motor', 'buildings', 'contents']:
        for prefix in ['policies', 'test']:
            f = pd.read_parquet(EM / f'{prefix}_{line}.parquet', columns=['policy_id', 'customer_id'])
            f['line'] = line
            maps.append(f)
    mapping = pd.concat(maps, ignore_index=True).drop_duplicates()
    assert not mapping.duplicated(['policy_id', 'line']).any()
    customer_events = claims.merge(mapping, on=['policy_id', 'line'], how='inner', validate='many_to_one')
    ends = target.period_start.where(target.period_start <= V, V)
    pol_events = claims.loc[claims.line.eq('buildings')]
    target['hist_pol_12m'] = window_counts(target.policy_id, ends, pol_events, 'policy_id')
    target['hist_cli_12m'] = window_counts(target.customer_id, ends, customer_events, 'customer_id')
    # A different, direct Boolean calculation on a fixed sample, including future rows.
    ix = np.unique(np.r_[np.linspace(0, len(target) - 1, 32, dtype=int),
                          np.flatnonzero(target.year.eq(2025))[:16]])
    for i in ix:
        end = ends.iloc[i]
        known = end - pd.Timedelta(days=365) >= pd.Timestamp('2023-01-01')
        for field, ev, key in [('hist_pol_12m', pol_events, 'policy_id'),
                                ('hist_cli_12m', customer_events, 'customer_id')]:
            expected = int((ev[key].eq(target[key].iloc[i]) & ev.report_date.lt(end)
                            & ev.report_date.ge(end - pd.Timedelta(days=365))).sum())
            actual = target[field].iloc[i]
            assert (actual == expected) if known else np.isnan(actual)
    return {'sample_rows_boolean_crosscheck': len(ix), 'mode': 'historia2',
            'end': 'min(period_start,2024-12-31)', 'interval': '[end-365days,end)',
            'all_status_notifications': True, 'mapped_customer_notifications': len(customer_events),
            'unmapped_notifications_excluded_customer_history': len(claims) - len(customer_events),
            'original_FSp_environment_history_mode_not_established': True,
            'new_reconstruction_not_claimed_exact_original_2025_replay': True}


def with_climate(frame, raw, years):
    weather = pd.read_parquet(raw / 'weather.parquet', columns=['address_id', 'year', *CLIMATE],
                              filters=[('year', 'in', years)])
    assert set(weather.year.unique()) == set(years) and 2025 not in years
    climate = weather.groupby('address_id')[CLIMATE].mean().add_prefix('clima_').reset_index()
    out = frame.merge(climate, on='address_id', how='left', validate='many_to_one', sort=False)
    assert np.array_equal(out.row_id, frame.row_id)
    assert out[['clima_' + c for c in CLIMATE]].notna().all().all()
    return out


def compare(frame, cached, features, categorical, name):
    frame = frame.set_index('row_id').loc[cached.row_id].reset_index()
    checks = []
    for c in features:
        if c in categorical:
            a = frame[c].astype('string').fillna('<NA>').to_numpy()
            b = cached[c].astype('string').fillna('<NA>').to_numpy()
            mismatches = int(np.count_nonzero(a != b))
            checks.append({'column': c, 'method': 'string_exact', 'mismatches': mismatches})
            assert mismatches == 0, (name, c, mismatches)
        else:
            a = pd.to_numeric(frame[c], errors='coerce').to_numpy(float)
            b = cached[c].to_numpy(float)
            if str(cached[c].dtype) == 'float32':
                check = a.astype('float32').astype(float)
                mode = 'raw_float64_forward_cast32_exact'
            else:
                check = a
                mode = 'raw_float64_exact_or_absolute_1e-12'
            same = np.isclose(check, b, rtol=0, atol=0 if mode.endswith('exact') else 1e-12, equal_nan=True)
            checks.append({'column': c, 'method': mode, 'mismatches': int((~same).sum()),
                           'max_finite_abs_difference_before_cast': float(np.max(np.abs(a - b)[np.isfinite(a - b)]))
                           if np.isfinite(a - b).any() else None})
            assert same.all(), (name, c, int((~same).sum()), a[~same][:3], b[~same][:3])
    return checks


def main():
    assert not OUT.exists(), 'Do not repeat a completed preparation.'
    OUT.mkdir(parents=True)
    paths = [Path(__file__), OLD / 'variables.py', OLD / 'preparar_datos.py', OLD / 'historia2.py',
             BASE / 'fuente_f2_2024_v2/buildings.parquet',
             BASE / 'linaje_T2b_v1/features_buildings.parquet',
             BASE / 'FSp_edificios_recuperacion_entradas_20261026_v1/report.json']
    for raw in [DEV, EM]:
        paths += [raw / (n + '.parquet') for n in ['policies_buildings', 'customers', 'addresses', 'weather']]
    paths += [EM / 'claims.parquet', EM / 'test_buildings.parquet']
    paths += [EM / f'{prefix}_{line}.parquet' for line in ['motor', 'contents'] for prefix in ['policies', 'test']]
    before = {rel(p): sha(p) for p in paths}
    dump(OUT / 'sources_before.json', before)
    c = constants()
    features = c['POLIZA'] + c['CLIENTE'] + c['DIRECCION'] + c['RAMO']['buildings']
    cat = c['CATEGORICAS'].intersection(features)
    source = base_frame(DEV, False)
    cached = pd.read_parquet(BASE / 'fuente_f2_2024_v2/buildings.parquet')
    assert np.array_equal(source.row_id, cached.row_id)
    # These are exact integer notification counts or missing; no lost precision.
    for field in ['hist_pol_12m', 'hist_cli_12m']:
        value = cached[field].to_numpy(float)
        assert np.all(value[np.isfinite(value)] == np.floor(value[np.isfinite(value)]))
        source[field] = value
    target = base_frame(EM, True)
    history = histories(target)
    outputs = {}
    checks = {}
    category_levels = {}
    for phase, source_years, target_years in [('prod', [2021, 2022, 2023, 2024], [2023, 2024]),
                                              ('dev', [2021, 2022, 2023], [2023])]:
        s = with_climate(source.loc[source.year.isin(source_years)].copy(), DEV, source_years)
        t = with_climate(target, EM, target_years)
        if phase == 'prod':
            checks['source_prod'] = compare(s, cached, features, cat, 'source_prod')
            old_target = pd.read_parquet(BASE / 'linaje_T2b_v1/features_buildings.parquet')
            checks['target_prod_historical'] = compare(t, old_target, features, cat, 'target_prod_historical')
            del old_target
        levels = {col: sorted(set(s[col].dropna().astype(str)) | set(t[col].dropna().astype(str))) for col in cat}
        category_levels[phase] = levels
        for kind, frame in [('source', s), ('target', t)]:
            X = pd.DataFrame(index=frame.index)
            for col in features:
                if col in cat:
                    X[col] = pd.Categorical(frame[col].astype(str).where(frame[col].notna(), None), categories=levels[col])
                else:
                    X[col] = pd.to_numeric(frame[col], errors='coerce').astype('float64')
            assert X.shape == (len(frame), 45)
            assert all(str(X[col].dtype) == 'float64' for col in features if col not in cat)
            assert not np.isinf(X.select_dtypes('number').to_numpy()).any()
            path = OUT / f'matrix_{kind}_{phase}.parquet'
            X.reset_index(drop=True).to_parquet(path, index=False)
            rows = frame[['row_id', 'customer_id', 'policy_id', 'address_id', 'year', 'period_start',
                          'period_end', 'exposure', 'is_test', 'new_business']].reset_index(drop=True)
            rowpath = OUT / f'rows_{kind}_{phase}.parquet'
            rows.to_parquet(rowpath, index=False)
            outputs[path.name] = {'sha256': sha(path), 'rows': len(X), 'columns': 45}
            outputs[rowpath.name] = {'sha256': sha(rowpath), 'rows': len(rows)}
        print(json.dumps({'phase': phase, 'source_rows': len(s), 'target_rows': len(t), 'matrices_saved': True}), flush=True)
        del s, t, X, rows
        gc.collect()
    # Check exact boundary inclusion independently of real portfolio support.
    ends = pd.Series(pd.to_datetime(['2024-01-01', '2024-01-01', '2025-01-01']))
    ev = pd.DataFrame({'key': ['a'] * 4, 'report_date': pd.to_datetime(['2023-01-01', '2023-12-31', '2024-01-01', '2024-12-31'])})
    got = window_counts(pd.Series(['a', 'missing', 'a']), ends, ev, 'key')
    assert np.array_equal(got, [2., 0., 1.])
    assert before == {rel(p): sha(p) for p in paths}, 'Source changed during preparation.'
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'status': 'matrices_restored_no_fit_no_inference',
              'source_prod_years': [2021, 2022, 2023, 2024], 'source_dev_years': [2021, 2022, 2023],
              'target_years': [2023, 2024, 2025], 'features': features, 'category_levels': category_levels,
              'checks': checks, 'history': history, 'synthetic_window_boundaries_passed': True,
              'source_history_reused_exact_counts_from_previous_verified_cache': True,
              'source_raw_precision_restored_and_forward32_parity_passed': True,
              'historical_target64_parity_passed': True,
              'original_tree_bitwise_replay_not_established': True,
              'source_climate_2025_read': False, 'target_weather_2025_read': False,
              'category_union_uses_unlabelled_target_covariates': True,
              'new_fits': 0, 'new_C0_fits': 0, 'new_model_inferences': 0, 'new_scores': 0, 'new_submissions': 0,
              'not_a_training_recipe_or_predictive_admission': True, '2024_open': True,
              'B00_all_alternatives_preserved': True, 'sources': before, 'outputs': outputs,
              'next': 'Freeze fixed-round numerical-producer recovery recipe and budget, register forum before any fit. Preserve cached C0 and fixed rounds; save models and row outputs.'}
    dump(OUT / 'report.json', report)
    print(json.dumps({'checks': {k: len(v) for k, v in checks.items()}, 'all_passed': True,
                      'new_fits': 0, 'new_C0_fits': 0, 'new_scores': 0, 'new_submissions': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
