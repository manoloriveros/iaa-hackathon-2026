"""Cobertura y variación de covariables oficiales; no ajusta, infiere o puntúa precios."""
from pathlib import Path
from datetime import datetime, timezone
import gc
import hashlib
import json
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

OUT = R / 'privado/semana2/mision017_fase2/clima2025_auditoria_20261026_v1'
PAGE = OUT.parent / 'fuentes_clima2025_20261026_v1/official_pages.json'
FIELDS = ['hail_days', 'wind_exposure_index', 'freezing_days', 'dry_summer_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
rel = lambda p: p.relative_to(ROOT).as_posix()

def main():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    verified_path = R / 'privado/semana2/integridad_oficial/contenido_20261024_v1/report.json'
    verified = read(verified_path); ver = {z['name']: z for z in verified['results']}
    sources = [Path(__file__), PAGE, verified_path,
        R / 'registro/semana2_F05_clima2023_actual.json', R / 'registro/semana2_F05_busqueda_foro_actual.json',
        ROOT / 'Hackaton/Semana 2/Claude/ml_independiente_20261023/codigo/e13_clima_anual.py',
        ROOT / 'Hackaton/Semana 2/Claude/ml_independiente_20261023/e13_clima_anual.json']
    summaries = []; changes = []; coverage = []; markets = []; math = []
    for market, raw, historical_years in [
        ('developed', ROOT / 'Hackaton/Semana 1/Datos', [2021, 2022, 2023, 2024]),
        ('emerging', ROOT / 'Hackaton/Semana 2/Datos/emerging', [2023, 2024])]:
        path = raw / 'weather.parquet'; sources.append(path)
        parent = ver[f'{market}/weather.parquet']
        assert sha(path) == parent['local_sha256'] == parent['fresh_sha256'] and parent['official_md5_matches_received']
        w = pd.read_parquet(path, columns=['address_id', 'year', *FIELDS])
        assert not w.duplicated(['address_id', 'year']).any()
        assert w[FIELDS].notna().all().all() and np.isfinite(w[FIELDS].to_numpy()).all()
        assert len(w) == pq.ParquetFile(path).metadata.num_rows
        years = sorted(int(y) for y in w.year.unique()); assert years == historical_years + [2025]
        for year, group in w.groupby('year', observed=True):
            for field in FIELDS:
                x = group[field].to_numpy(float)
                summaries.append({'market': market, 'year': int(year), 'field': field, 'rows': len(x),
                    'mean': float(x.mean()), 'sd': float(x.std()), 'min': float(x.min()),
                    'p05': float(np.quantile(x, .05)), 'p50': float(np.quantile(x, .5)),
                    'p95': float(np.quantile(x, .95)), 'max': float(x.max())})
        historical = w.loc[w.year.isin(historical_years)].copy()
        means = historical.groupby('address_id', observed=True)[FIELDS].mean()
        counts = historical.groupby('address_id', observed=True).size(); assert counts.eq(len(historical_years)).all()
        future = w.loc[w.year.eq(2025)].set_index('address_id')
        assert set(future.index) == set(means.index)
        train_mean = historical.address_id.map(means[FIELDS[0]]).to_numpy(float)
        # Independent spot checks use explicit arrays rather than groupby means.
        for address in list(means.index[:3]):
            rows = historical.loc[historical.address_id.eq(address)]
            for field in FIELDS:
                assert abs(np.mean(rows[field].to_numpy(float)) - means.loc[address, field]) < 1e-10
        for field in FIELDS:
            baseline = historical.address_id.map(means[field]).to_numpy(float)
            residual = historical[field].to_numpy(float) - baseline
            centered = pd.Series(residual).groupby(historical.address_id.to_numpy()).mean()
            assert centered.abs().max() < 1e-8
            scale = float(np.std(residual)); assert scale > 0
            delta = future[field].to_numpy(float) - means[field].reindex(future.index).to_numpy(float)
            z = delta / scale
            changes.append({'market': market, 'field': field, 'addresses_2025': len(future),
                'history_years': ','.join(str(y) for y in historical_years), 'historical_anomaly_sd': scale,
                'delta2025_mean': float(delta.mean()), 'delta2025_sd': float(delta.std()),
                'delta2025_p05': float(np.quantile(delta, .05)), 'delta2025_p50': float(np.quantile(delta, .5)),
                'delta2025_p95': float(np.quantile(delta, .95)), 'fraction_abs_delta_gt3_history_sd': float(np.mean(abs(z) > 3)),
                'fraction_outside_historical_anomaly_range': float(np.mean((delta < residual.min()) | (delta > residual.max())))})
        for line in ['motor', 'buildings', 'contents']:
            paths = [(raw / f'policies_{line}.parquet', historical_years)]
            if market == 'emerging': paths += [(raw / f'test_{line}.parquet', [2025])]
            for policy, allowed in paths:
                sources.append(policy)
                f = pd.read_parquet(policy, columns=['row_id', 'address_id', 'period_start'])
                f['year'] = pd.to_datetime(f.period_start).dt.year
                assert f.year.isin(allowed).all() and f.row_id.is_unique
                join = f.merge(w[['address_id', 'year']], on=['address_id', 'year'], how='left', indicator=True, validate='many_to_one')
                assert join._merge.eq('both').all()
                coverage.append({'market': market, 'line': line, 'file': rel(policy), 'rows': len(f),
                    'all_weather_keys_matched': True, 'years': sorted(int(y) for y in f.year.unique())})
        markets.append({'market': market, 'path': rel(path), 'sha256': sha(path), 'rows': len(w),
            'year_counts': {str(k): int(v) for k, v in w.year.value_counts().sort_index().items()},
            'same_bytes_as_officially_verified20261024': True, 'new_file_content_claim': False,
            'unique_address_year': True, 'null_numeric_cells': 0})
        math.append({'market': market, 'spot_means_by_independent_array_method': True,
            'historical_address_residual_means_zero': True, 'new_model_fits': 0})
        del w, historical, means, future, train_mean, residual, centered, baseline, delta, z; gc.collect()
    pd.DataFrame(summaries).to_csv(OUT / 'year_summary.csv', index=False)
    pd.DataFrame(changes).to_csv(OUT / 'annual_anomaly_summary.csv', index=False)
    pd.DataFrame(coverage).to_csv(OUT / 'policy_weather_coverage.csv', index=False)
    prior_page = R / 'privado/semana2/revision_F05_2023/f05_20261024_v1/data_description_part2_response.json'
    old = read(prior_page); current = read(PAGE)['data_description']
    # MCP archives may wrap their JSON payload in a content/text block.
    def unwrap(obj):
        if 'content' in obj:
            for part in obj['content']:
                if part.get('type') == 'text': return json.loads(part['text'])
        return obj
    old = unwrap(old)
    old_content = next(p['content'] for p in old['pages'] if p['name'] == 'data-description')
    current_content = next(p['content'] for p in current['pages'] if p['name'] == 'data-description')
    same = old_content == current_content
    sources.append(prior_page)
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Official supplied covariates, no claims/labels/prices or external realized weather',
        'markets': markets, 'coverage': coverage, 'mathematics': math,
        'documentation_discrepancy': 'Current data page says weather developed2021–2024/emerging2023–2024, while both unchanged official Parquets also contain2025',
        'current_dictionary_same_as_F05': same,
        'source_page_content_sha256': hashlib.sha256(current_content.encode()).hexdigest(),
        '2025_quote_time_or_forecast_vintage_established': False,
        'official_2025_covariate_presence_established': True,
        'F05_prospective_availability_finding_closed': False,
        'E13_annual_weather_trial_preserved_not_repeated': True,
        'sources': {rel(p): sha(p) for p in sources}, 'new_fits': 0, 'new_C0_fits': 0,
        'new_model_inferences': 0, 'new_price_scores': 0, 'new_submissions': 0,
        'B00_preserved': True, 'all_alternatives_preserved': True,
        'prior_goal_turn_classification': 'progress: Tanda6 completed and public receipt57651126 improved best from.16033 to.16519',
        'goal_achieved': False}
    with (OUT / 'report.json').open('x', encoding='utf8') as out: json.dump(result, out, ensure_ascii=False, indent=2)
    print(json.dumps({'weather2025_present_in_unchanged_verified_files': True, 'dictionary_same_as_F05': same,
        'markets': markets, 'coverage_scopes': len(coverage), 'new_fits': 0, 'new_price_scores': 0,
        'emerging2025_anomalies': [x for x in changes if x['market'] == 'emerging']}))

if __name__ == '__main__':
    main()
