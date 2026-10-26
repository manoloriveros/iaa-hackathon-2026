"""Entradas de motor/contenidos: restaura precisión, no ajusta ni puntúa."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import gc
import importlib.util
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'
OUT = BASE / 'FSp_MC_recuperacion_20261026_v1'
MATRIX = OUT / 'matrices'
OLD = ROOT / 'Hackaton/Semana 2/Claude/ml_independiente_20261023/codigo'
ORIGINAL = ROOT / 'Hackaton/Semana 2/Claude/mision017_20261025/exp26_20261026/ml2'
DEV = ROOT / 'Hackaton/Semana 1/Datos'; EM = ROOT / 'Hackaton/Semana 2/Datos/emerging'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


# Shared, already inspected pure functions; neither module's main is called.
common = load('restored_buildings_matrix_helpers', R / 'herramientas/restaurar_matrices_FSp_edificios.py')
w = load('writer_MC_matrices', R / 'herramientas/registrar_avance_mision017_fase2.py')
CLIMATE = common.CLIMATE
V = pd.Timestamp('2024-12-31')


def dump(p, a):
    p.write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding='utf8')


def base_frame(raw, line, emerging, features):
    keycols = ['row_id', 'policy_id', 'customer_id', 'address_id', 'period_start', 'period_end']
    age = ('driver_age' if line == 'motor' else 'policyholder_age') + ('_band' if emerging else '')
    schema = pq.ParquetFile(raw / f'policies_{line}.parquet').schema_arrow.names
    cols = list(dict.fromkeys(keycols + [age, 'days_quote_to_inception'] +
                              (['sum_insured'] if line == 'contents' else []) + [c for c in features if c in schema]))
    f = pd.read_parquet(raw / f'policies_{line}.parquet', columns=cols); f['is_test'] = False
    if emerging:
        test = pd.read_parquet(raw / f'test_{line}.parquet', columns=cols); test['is_test'] = True
        f = pd.concat([f, test], ignore_index=True)
    elif line == 'motor':
        f['customer_id'] = f.customer_id.str.zfill(8)
    f['period_start'] = pd.to_datetime(f.period_start); f['period_end'] = pd.to_datetime(f.period_end)
    f['year'] = f.period_start.dt.year
    assert f.year.isin([2023, 2024, 2025] if emerging else [2021, 2022, 2023, 2024]).all()
    f['exposure'] = ((f.period_end - f.period_start).dt.days + 1) / 365.
    cu_schema = pq.ParquetFile(raw / 'customers.parquet').schema_arrow.names
    ad_schema = pq.ParquetFile(raw / 'addresses.parquet').schema_arrow.names
    customers = pd.read_parquet(raw / 'customers.parquet', columns=list(dict.fromkeys(
        ['customer_id', 'customer_since_year'] + [c for c in features if c in cu_schema])))
    addresses = pd.read_parquet(raw / 'addresses.parquet', columns=list(dict.fromkeys(
        ['address_id', 'year_built'] + [c for c in features if c in ad_schema])))
    customers['occupation'] = customers.occupation.str.lower().str.strip()
    if emerging:
        customers['occupation'] = customers.occupation.str.replace('self-employed ', '', regex=False).str.strip()
    before = len(f)
    f = f.merge(customers, on='customer_id', how='left', validate='many_to_one', sort=False)
    f = f.merge(addresses, on='address_id', how='left', validate='many_to_one', sort=False)
    assert len(f) == before and f.customer_since_year.notna().all() and f.year_built.notna().all()
    f['tenure_years'] = f.year - f.customer_since_year; f['property_age'] = f.year - f.year_built
    f['start_month'] = f.period_start.dt.month; f['full_year'] = (f.exposure >= .99).astype(int)
    f['log_days_quote'] = np.log1p(f.days_quote_to_inception.clip(lower=0))
    if emerging:
        f['age_band'] = f[age]
    else:
        f['age_band'] = pd.cut(f[age], [-1, 24, 34, 49, 64, 200],
                               labels=['17-24', '25-34', '35-49', '50-64', '65+']).astype(str)
    if line == 'contents':
        f['log_si'] = np.log(np.where(f.sum_insured > 2e6, f.sum_insured / 1000., f.sum_insured))
    assert f.row_id.is_unique and f.exposure.gt(0).all()
    return f


def notification_events():
    claims = pd.read_parquet(EM / 'claims.parquet', columns=['policy_id', 'line', 'report_date'])
    claims['report_date'] = pd.to_datetime(claims.report_date); assert claims.report_date.le(V).all()
    maps = []
    for line in ['motor', 'buildings', 'contents']:
        for prefix in ['policies', 'test']:
            f = pd.read_parquet(EM / f'{prefix}_{line}.parquet', columns=['policy_id', 'customer_id'])
            f['line'] = line; maps.append(f)
    mapping = pd.concat(maps, ignore_index=True).drop_duplicates()
    assert not mapping.duplicated(['policy_id', 'line']).any()
    customer_events = claims.merge(mapping, on=['policy_id', 'line'], how='inner', validate='many_to_one')
    return claims, customer_events


def history(f, line, claims, customer_events):
    ends = f.period_start.where(f.period_start <= V, V)
    pol = claims.loc[claims.line.eq(line)]
    f['hist_pol_12m'] = common.window_counts(f.policy_id, ends, pol, 'policy_id')
    f['hist_cli_12m'] = common.window_counts(f.customer_id, ends, customer_events, 'customer_id')
    sample = np.unique(np.r_[np.linspace(0, len(f) - 1, 32, dtype=int), np.flatnonzero(f.year.eq(2025))[:16]])
    for i in sample:
        end = ends.iloc[i]; known = end - pd.Timedelta(days=365) >= pd.Timestamp('2023-01-01')
        for field, events, key in [('hist_pol_12m', pol, 'policy_id'), ('hist_cli_12m', customer_events, 'customer_id')]:
            expected = int((events[key].eq(f[key].iloc[i]) & events.report_date.lt(end) &
                            events.report_date.ge(end - pd.Timedelta(days=365))).sum())
            assert (f[field].iloc[i] == expected) if known else np.isnan(f[field].iloc[i])
    return {'sample_boolean_crosschecks': len(sample) * 2, 'end': 'min(period_start,2024-12-31)',
            'mode': 'historia2', 'original_runtime_mode_not_established': True}


def scalar_parity(line):
    path = BASE / f'recuentos_fuente2024_v1/counts_{line}.parquet'
    counts = pd.read_parquet(path); checks = []
    for phase, years, suffix in [('dev', [2021, 2022, 2023], ''), ('prod', [2021, 2022, 2023, 2024], '_prod')]:
        meta = w.read(ORIGINAL / f'trabajo/pred/fsp/{line}{suffix}_meta.json')
        f = counts.loc[counts.year.isin(years)]
        for peril, saved in meta.items():
            n = f['N_' + peril].to_numpy(float); cost = f['T0_cents_' + peril].to_numpy(float) / 100.
            e = f.exposure.to_numpy(float); q = f['E_cost_' + peril].to_numpy(float) / e
            b0 = float(np.log(n.sum() / np.sum(e * np.maximum(q, 1e-4))))
            positive = (n > 0) & (cost > 0); mean = float(cost[positive].sum() / n[positive].sum())
            assert int(n.sum()) == saved['n_dev'] and abs(b0 - saved['b0']) < 1e-12
            assert abs(mean / saved['sev_media'] - 1) < 1e-10
            checks.append({'line': line, 'phase': phase, 'peril': peril, 'rows': len(f),
                           'N': int(n.sum()), 'b0_error': b0 - saved['b0'], 'mean_mark_relative_error': mean / saved['sev_media'] - 1,
                           'fixed_rounds_frequency': saved['rondas_f'], 'fixed_rounds_severity': saved['rondas_s']})
    return checks


def main():
    assert OUT.exists() and not MATRIX.exists()
    assert not w.read(OUT / 'received_output_inventory.json')['matches']
    MATRIX.mkdir()
    constants = common.constants(); paths = [Path(__file__), Path(common.__file__), OLD / 'variables.py',
        OLD / 'preparar_datos.py', OLD / 'historia2.py', OUT / 'received_output_inventory.json',
        ORIGINAL / 'codigo/fsp_light.py', ORIGINAL / 'codigo/fsp_light_prod.py']
    for raw in [DEV, EM]:
        paths += [raw / (n + '.parquet') for n in ['customers', 'addresses', 'weather', 'policies_motor', 'policies_contents']]
    paths += [EM / 'claims.parquet', EM / 'policies_buildings.parquet', EM / 'test_buildings.parquet',
              EM / 'test_motor.parquet', EM / 'test_contents.parquet']
    for line in ['motor', 'contents']:
        paths += [BASE / f'fuente_f2_2024_v2/{line}.parquet', BASE / f'linaje_T2b_v1/features_{line}.parquet',
                  BASE / f'recuentos_fuente2024_v1/counts_{line}.parquet']
        paths += [ORIGINAL / f'trabajo/pred/fsp/{line}{suffix}_meta.json' for suffix in ['', '_prod']]
    before = {w.rel(p): w.sha(p) for p in paths}; dump(MATRIX / 'sources_before.json', before)
    claims, customer_events = notification_events()
    results = {}; outputs = {}; categories = {}
    for line in ['motor', 'contents']:
        cols = constants['POLIZA'] + constants['CLIENTE'] + constants['DIRECCION'] + constants['RAMO'][line]
        cat = constants['CATEGORICAS'].intersection(cols)
        source = base_frame(DEV, line, False, cols)
        cached = pd.read_parquet(BASE / f'fuente_f2_2024_v2/{line}.parquet')
        assert np.array_equal(source.row_id, cached.row_id)
        for field in ['hist_pol_12m', 'hist_cli_12m']:
            value = cached[field].to_numpy(float)
            assert np.all(value[np.isfinite(value)] == np.floor(value[np.isfinite(value)]))
            source[field] = value
        target = base_frame(EM, line, True, cols)
        history_check = history(target, line, claims, customer_events)
        checks = {}; counts = []
        for phase, source_years, target_years in [('prod', [2021, 2022, 2023, 2024], [2023, 2024]),
                                                ('dev', [2021, 2022, 2023], [2023])]:
            s = common.with_climate(source.loc[source.year.isin(source_years)].copy(), DEV, source_years)
            t = common.with_climate(target, EM, target_years)
            if phase == 'prod':
                checks['source_prod'] = common.compare(s, cached, cols, cat, line + '_source')
                historical = pd.read_parquet(BASE / f'linaje_T2b_v1/features_{line}.parquet')
                checks['historical_target_prod'] = common.compare(t, historical, cols, cat, line + '_target')
                del historical
            levels = {c: sorted(set(s[c].dropna().astype(str)) | set(t[c].dropna().astype(str))) for c in cat}
            categories[line + '_' + phase] = levels
            for market, frame in [('source', s), ('target', t)]:
                X = pd.DataFrame(index=frame.index)
                for c in cols:
                    X[c] = pd.Categorical(frame[c].astype(str).where(frame[c].notna(), None), categories=levels[c]) if c in cat else pd.to_numeric(frame[c], errors='coerce').astype('float64')
                assert all(str(X[c].dtype) == 'float64' for c in cols if c not in cat)
                assert not np.isinf(X.select_dtypes('number').to_numpy()).any()
                mpath = MATRIX / f'matrix_{line}_{market}_{phase}.parquet'
                X.reset_index(drop=True).to_parquet(mpath, index=False)
                rows = frame[['row_id', 'customer_id', 'policy_id', 'address_id', 'year', 'period_start', 'period_end',
                              'exposure', 'is_test', 'new_business']].reset_index(drop=True)
                rpath = MATRIX / f'rows_{line}_{market}_{phase}.parquet'; rows.to_parquet(rpath, index=False)
                outputs[mpath.name] = {'sha256': w.sha(mpath), 'rows': len(X), 'features': len(cols)}
                outputs[rpath.name] = {'sha256': w.sha(rpath), 'rows': len(rows)}
                counts.append({'phase': phase, 'market': market, 'rows': len(frame), 'test_rows': int(frame.is_test.sum())})
            print(json.dumps({'line': line, 'phase': phase, 'source_rows': len(s), 'target_rows': len(t), 'features': len(cols)}), flush=True)
            del s, t, X, rows; gc.collect()
        results[line] = {'features': cols, 'checks': checks, 'history': history_check, 'row_counts': counts,
                         'scalars': scalar_parity(line), 'raw_precision_restored': True}
        del source, target, cached; gc.collect()
    assert before == {w.rel(p): w.sha(p) for p in paths}
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'status': 'MC_matrices_and_source_scalars_reconciled_no_fit', 'lines': results,
              'category_levels': categories, 'sources': before, 'outputs': outputs,
              'new_fits': 0, 'new_C0_fits': 0, 'new_inferences': 0, 'new_scores': 0, 'new_submissions': 0,
              '2024_open': True, 'no_weather_2025_read': True, 'B00_all_alternatives_preserved': True,
              'numeric_recovery_budget_if_registered': 36, 'new_early_stopping_searches': 0,
              'not_a_training_recipe_or_predictive_admission': True,
              'limits': ['history2 explicitly fixed; original2025mode not proven', 'undated master vintage',
                         'cost-completion Poisson offset: f*s cost proxy, not identified ultimate count/mark',
                         'source tail1095 and case reserve adequacy not identified',
                         'raw capital screen retained for parity, not all cases newly certified']}
    dump(MATRIX / 'report.json', report)
    print(json.dumps({'status': report['status'], 'feature_parity_checks': sum(len(v) for a in results.values() for v in a['checks'].values()),
                      'scalar_checks': sum(len(a['scalars']) for a in results.values()), 'new_fits': 0, 'new_scores': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
