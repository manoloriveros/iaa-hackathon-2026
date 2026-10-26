"""Frecuencia meteorológica Poisson por peril, con nuisance fuente que no se transfiere."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
spec = importlib.util.spec_from_file_location('m4', R / 'herramientas/mision017_fase2_tanda4_marketing.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
import numpy as np
import pandas as pd
from scipy import sparse, optimize, special
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits

BASE = R / 'privado/semana2/mision017_fase2'
OUT = BASE / 'tanda8_poisson_20261026_v1'; PLAN = R / 'registro/semana2_mision017_fase2_tanda8_plan_v1.json'
COUNTS = BASE / 'recuentos_fuente2024_v1'; LINKS = BASE / 'recuentos_fuente2024_rkm_reuse_v1'
W7 = BASE / 'tanda7_clima_20261026_v2'; WEIGHTS = BASE / 'estimando_cartera2025_v3'
SCOPE = R / 'registro/semana2_alcance_covariables_oficiales2025_v3.json'
RAW = ROOT / 'Hackaton/Semana 1/Datos'; TARGET = ROOT / 'Hackaton/Semana 2/Datos/emerging'
RAW_FIELDS = ['wind_exposure_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c', 'hail_days', 'freezing_days', 'dry_summer_index']
DELTA = ['d_wind', 'd_wildfire', 'd_lograin', 'd_temperature', 'd_loghail', 'd_logfreezing', 'd_dry']
MAP = {
    'motor': {'bodily_injury': ['d_logfreezing', 'd_lograin'], 'glass_hail': ['d_loghail', 'd_wind'],
        'own_damage': ['d_loghail', 'd_wind', 'd_logfreezing', 'd_lograin'], 'third_party_prop': ['d_logfreezing', 'd_lograin']},
    'buildings': {'escape_of_water': ['d_logfreezing', 'd_temperature'], 'fire': ['d_wildfire', 'd_dry'],
        'flood': ['d_lograin'], 'storm': ['d_wind'], 'subsidence': ['d_dry', 'd_lograin']},
    'contents': {'escape_of_water': ['d_logfreezing', 'd_temperature'], 'flood': ['d_lograin']}}
CATS = ['source_region', 'age_band', 'credit_band', 'start_month']; NUM = ['risk_log', 'new_business', 'full_year']
WEATHER_PRECISION = 25.; NUISANCE_PRECISION = 4.
sha = m.sha; read = m.read; dump = m.dump; rel = m.rel
now = lambda: datetime.now(timezone.utc).isoformat()

def climate(raw, years):
    w = pd.read_parquet(raw / 'weather.parquet', columns=['address_id', 'year', *RAW_FIELDS], filters=[('year', 'in', years)])
    assert w.year.isin(years).all() and not w.duplicated(['address_id', 'year']).any()
    for field, new in zip(RAW_FIELDS, DELTA):
        x = w[field].to_numpy(float)
        if field in ['rainfall_mm', 'hail_days', 'freezing_days']: assert (x >= 0).all(); x = np.log1p(x)
        w[new] = x
    means = w.groupby('address_id', observed=True)[DELTA].transform('mean')
    for name in DELTA: w[name] = w[name].to_numpy(float) - means[name].to_numpy(float)
    assert np.isfinite(w[DELTA].to_numpy()).all()
    return w[['address_id', 'year', *DELTA]]

def preflight():
    assert not OUT.exists(); OUT.mkdir(parents=True)
    assert read(LINKS / 'report.json')['count_likelihood_input_positivity_pass']
    assert len(read(COUNTS / 'validation_v1/report.json')['checks']) == 15
    source_weather = climate(RAW, [2021, 2022, 2023, 2024]); target_weather = climate(TARGET, [2023, 2024])
    credit = pd.read_parquet(RAW / 'customers.parquet', columns=['customer_id', 'credit_band'])
    credit['customer_id'] = credit.customer_id.str.zfill(8); assert credit.customer_id.is_unique
    assert credit.credit_band.dropna().isin(list('ABCDE')).all()
    sources = [Path(__file__), Path(m.__file__), SCOPE, RAW / 'weather.parquet', RAW / 'customers.parquet', TARGET / 'weather.parquet',
        COUNTS / 'report.json', LINKS / 'report.json', m.CV / 'oof_2023_2024.parquet', WEIGHTS / 'weights.parquet', WEIGHTS / 'report.json',
        BASE.parent / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet']
    outputs = []; membership = []
    for line in MAP:
        source_path = m.data.OUT / f'{line}.parquet'; count_path = COUNTS / f'counts_{line}.parquet'; link_path = LINKS / f'rkm_links_{line}.parquet'
        offset_path = W7 / f'source_inputs_{line}.parquet'; feature_path = m.PARENT / f'features_{line}.parquet'
        sources += [source_path, count_path, link_path, offset_path, W7 / f'extended_{line}.json', feature_path]
        assert sha(offset_path) == read(W7 / f'extended_{line}.json')['source_input_sha256']
        f = pd.read_parquet(source_path, columns=['row_id', 'customer_id', 'address_id', 'year', 'market', 'age_band', 'new_business', 'full_year', 'start_month', 'e_cost'])
        offset = pd.read_parquet(offset_path, columns=['row_id', 'offset', 'source_region'])
        assert np.array_equal(f.row_id, offset.row_id)
        f = f.merge(offset, on='row_id', validate='one_to_one').merge(credit, on='customer_id', validate='many_to_one')
        f['credit_band'] = f.credit_band.astype('string').fillna('__MISSING__')
        f['risk_log'] = np.log(f.offset.to_numpy(float) / f.e_cost.to_numpy(float))
        f = f.merge(source_weather, on=['address_id', 'year'], validate='many_to_one')
        cols = ['row_id'] + [c for p in MAP[line] for c in [f'N_{p}', f'E_count_{p}']]
        count = pd.read_parquet(count_path, columns=cols)
        link = pd.read_parquet(link_path, columns=['row_id'] + [f'E_count_rkm_{p}' for p in MAP[line]])
        f = f.merge(count, on='row_id', validate='one_to_one').merge(link, on='row_id', validate='one_to_one')
        assert f.market.eq('developed').all() and f.year.isin([2021, 2022, 2023, 2024]).all()
        assert np.isfinite(f[[*DELTA, *NUM]].to_numpy(float)).all()
        for p in MAP[line]: assert not ((f[f'N_{p}'] > 0) & (f[f'E_count_rkm_{p}'] <= 0)).any()
        source_output = OUT / f'source_{line}.parquet'; f.to_parquet(source_output, index=False); outputs.append(source_output)
        t = pd.read_parquet(feature_path, columns=['row_id', 'address_id', 'year']).merge(target_weather, on=['address_id', 'year'], validate='many_to_one')
        assert t.year.isin([2023, 2024]).all() and np.isfinite(t[DELTA].to_numpy()).all()
        target_output = OUT / f'target_{line}.parquet'; t.to_parquet(target_output, index=False); outputs.append(target_output)
        for held in range(5): sources.append(m.CV / f'learning_{line}_fold{held}.json')
        membership.append({'line': line, 'source_rows': len(f), 'target_rows': len(t), 'source_offsets_reused_no_inference': True,
            'source_credit_missing_rows': int(f.credit_band.eq('__MISSING__').sum()), 'target_credit_required': False})
    dump(OUT / 'preflight.json', {'author': 'Codex', 'utc': now(), 'sources': {rel(p): sha(p) for p in sources},
        'outputs': {rel(p): sha(p) for p in outputs}, 'membership': membership, 'source_years': [2021, 2022, 2023, 2024],
        'target_development_years': [2023, 2024], 'new_fits': 0, 'new_C0_fits': 0, 'new_inferences': 0, 'new_scores': 0})
    print(json.dumps({'preflight': 'complete', 'membership': membership, 'new_fits': 0, 'new_C0_fits': 0}))

def design(f, weather, learned=None):
    a = f[weather].to_numpy(float); z0 = f[NUM].to_numpy(float)
    if learned is None:
        center = a.mean(axis=0); scale = a.std(axis=0); nc = z0.mean(axis=0); ns = z0.std(axis=0)
        assert (scale > 1e-8).all() and (ns > 1e-8).all()
        categorical = OneHotEncoder(drop='first', sparse_output=True)
        xc = categorical.fit_transform(f[CATS].astype('string').fillna('__MISSING__').astype(str))
        year = OneHotEncoder(drop=None, sparse_output=True); xy = year.fit_transform(f[['year']])
        state = {'weather_center': center.tolist(), 'weather_scale': scale.tolist(), 'nuisance_center': nc.tolist(),
            'nuisance_scale': ns.tolist(), 'categories': [c.tolist() for c in categorical.categories_], 'years': year.categories_[0].tolist()}
    else: raise AssertionError('Independent replay is implemented in validator, not another learned encoder')
    X = sparse.hstack([sparse.csr_matrix((a - center) / scale), sparse.csr_matrix((z0 - nc) / ns), xc, xy], format='csr')
    precision = np.r_[np.full(len(weather), WEATHER_PRECISION), np.full(len(NUM) + xc.shape[1], NUISANCE_PRECISION), np.zeros(xy.shape[1])]
    return X, precision, state

def fit(f, line, peril, exposure_kind='rkm'):
    assert f.market.eq('developed').all() and f.year.isin([2021, 2022, 2023, 2024]).all()
    weather = MAP[line][peril]; e_col = f'E_count_rkm_{peril}' if exposure_kind == 'rkm' else f'E_count_{peril}'
    n0 = f[f'N_{peril}'].to_numpy(float); e0 = f[e_col].to_numpy(float)
    assert not ((n0 > 0) & (e0 <= 0)).any()
    active = e0 > 0; tr = f.loc[active].copy(); y = n0[active]; exposure = e0[active]
    X, precision, state = design(tr, weather); events = float(y.sum()); assert events > 0
    off = np.log(exposure); constant = float(np.sum(special.xlogy(y, y) - y)); beta = np.zeros(X.shape[1])
    for j, year in enumerate(state['years']):
        mask = tr.year.eq(year).to_numpy(); assert y[mask].sum() > 0
        beta[-len(state['years']) + j] = np.log(y[mask].sum() / exposure[mask].sum())
    def objective(coef):
        eta = off + X @ coef; mu = np.exp(eta)
        value = (np.sum(mu - y * eta) + constant + .5 * np.dot(precision * coef, coef)) / events
        gradient = (np.asarray(X.T @ (mu - y)).ravel() + precision * coef) / events
        return float(value), gradient
    result = optimize.minimize(objective, beta, method='L-BFGS-B', jac=True,
        options={'maxiter': 2000, 'gtol': 1e-8, 'ftol': 1e-12, 'maxls': 50})
    value, gradient = objective(result.x)
    assert result.success and np.abs(gradient).max() < 1e-6, str(result.message)
    mu = np.exp(off + X @ result.x)
    H = (X.T @ X.multiply((mu / events)[:, None])).toarray() + np.diag(precision / events)
    inverse = np.linalg.inv(H); keys = tr.source_region.astype(str).to_numpy() + '|' + tr.year.astype(str).to_numpy()
    U = []
    for key in sorted(set(keys)):
        mask = keys == key; U.append(np.asarray(X[mask].T @ ((mu[mask] - y[mask]) / events)).ravel())
    U = np.stack(U); cov = inverse @ (U.T @ U) @ inverse * len(U) / (len(U) - 1); nw = len(weather)
    return {'line': line, 'peril': peril, 'exposure_kind': exposure_kind, 'weather': weather, **state,
        'coef': result.x.tolist(), 'precision': precision.tolist(), 'objective': value, 'iterations': int(result.nit),
        'max_abs_gradient': float(np.abs(gradient).max()), 'events': int(events), 'training_rows': len(tr),
        'all_policy_rows_retained_in_input': len(f), 'zero_exposure_zero_count_noninformative_rows': int((~active).sum()),
        'weather_coefficient': dict(zip(weather, result.x[:nw].tolist())), 'source_clusters': len(U),
        'weather_cluster_covariance': cov[:nw, :nw].tolist(), 'weather_cluster_sd': np.sqrt(np.diag(cov)[:nw]).tolist(),
        'cluster_variance_approximate_not_independent_validation': True,
        'source_only_nuisance_not_required_or_transferred_to_target': True, 'new_GLM_fits': 1}

def apply(f, base, models, mixture, strength):
    assert abs(sum(mixture.values()) - 1) < 1e-12
    factor = np.ones(len(f))
    for peril, a in models.items():
        assert peril in mixture
        z = f[a['weather']].to_numpy(float) / np.asarray(a['weather_scale'])
        # Annual minus historical weather; source centers/nuisance cancel.
        eta = strength * (z @ np.asarray(a['coef'][:len(a['weather'])]))
        factor += mixture[peril] * np.expm1(eta)
    assert np.isfinite(factor).all() and (factor > 0).all()
    out = base.copy(); normalizers = {}
    for year in sorted(f.year.unique()):
        for nb in [0, 1]:
            mask = f.year.eq(year).to_numpy() & (f.new_business.to_numpy(dtype=int) == nb); assert mask.any()
            norm = float(np.sum(base[mask] * factor[mask]) / np.sum(base[mask]))
            out[mask] = base[mask] * factor[mask] / norm; normalizers[f'{int(year)}|{nb}'] = norm
            assert np.isclose(out[mask].sum(), base[mask].sum(), rtol=1e-12, atol=1e-6)
    assert np.isfinite(out).all() and (out > 0).all()
    return out, normalizers

def synthetic():
    rng = np.random.default_rng(2026102602); n = 800
    f = pd.DataFrame({'market': 'developed', 'year': np.arange(n) % 4 + 2021, 'source_region': rng.choice(['R01', 'R02'], n),
        'credit_band': rng.choice(list('ABCDE'), n), 'age_band': rng.choice(['17-24', '35-49', '65+'], n),
        'start_month': np.arange(n) % 12 + 1, 'new_business': (np.arange(n) // 4) % 2,
        'full_year': rng.integers(0, 2, n), 'risk_log': rng.normal(5, .7, n),
        'N_glass_hail': rng.poisson(.2, n), 'E_count_rkm_glass_hail': rng.uniform(.1, 1., n)})
    for col in DELTA: f[col] = rng.normal(size=n)
    with threadpool_limits(limits=2): a = fit(f, 'motor', 'glass_hail')
    base = rng.uniform(50, 300, n); mix = {'glass_hail': .2, 'other': .8}
    pred, norm = apply(f, base, {'glass_hail': a}, mix, 1.)
    poison, norm2 = apply(f.assign(T0=-1e30), base, {'glass_hail': a}, mix, 1.)
    assert np.array_equal(pred, poison) and norm == norm2
    zero = f.copy()
    for col in DELTA: zero[col] = 0.
    identity, _ = apply(zero.drop(columns=['credit_band']), base, {'glass_hail': a}, mix, 1.)
    assert np.array_equal(identity, base)
    dump(OUT / 'synthetic.json', {'pass': True, 'zero_weather_delta_identity': True, 'target_credit_not_required': True,
        'target_labels_unused': True, 'year_business_totals_preserved': True, 'synthetic_GLM_fits': 1, 'real_GLM_fits': 0})

def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists(); pre = read(OUT / 'preflight.json')
    with threadpool_limits(limits=2): synthetic()
    sources = {**pre['sources'], **pre['outputs'], rel(OUT / 'preflight.json'): sha(OUT / 'preflight.json')}
    for path, digest in sources.items(): assert sha(ROOT / path) == digest, path
    plan = {'id': 'S2-MISION017-FASE2-TANDA8-POISSON-v1', 'author': 'Codex', 'utc': now(),
        'hypothesis': 'A count response by physical peril can reduce aggregate-mark noise in weather effects. Transfer only frequency ratios for annual-vs-persistent weather, preserving C1/F2 levels; not another full FS/FSp backbone.',
        'reference': 'Held N3 research benchmark, not complete C1/F2; originalA1_2024 proxy checked separately',
        'source': 'All developed2021–2024 counts, existing source RKM count exposure reused without refit; no2025price labels or source-weather cells',
        'physical_map': MAP, 'neutral_perils': 'All perils not in the physical map have factor1',
        'configuration': {'objective': 'Half Poisson deviance summed and divided by observed events',
            'offset': 'log existing E_count_RKM; all positive counts retained; zero-exposure zero-count rows noninformative only',
            'weather': 'Seven official transformed annual measures minus same-address historical mean of the same transforms; log1p rain/hail/freezing, others native',
            'source_weather_years': [2021, 2022, 2023, 2024], 'target_historical_weather_years': [2023, 2024],
            'nuisance_numeric': NUM, 'nuisance_categorical': CATS, 'free_year_intercepts': [2021, 2022, 2023, 2024],
            'source_only_credit': 'Control in source only; never imputed in target or needed for a weather ratio',
            'precision_weather': WEATHER_PRECISION, 'precision_nuisance': NUISANCE_PRECISION, 'precision_year': 0,
            'scaling': 'Source-only mean/SD for weather/numeric nuisance; source category levels, no target encoding',
            'optimizer': {'method': 'L-BFGS-B', 'maxiter': 2000, 'gtol': 1e-8, 'ftol': 1e-12, 'maxls': 50},
            'mixture': 'Use cost-peril weights of frozen training-fold C0, no held claim or mixture learning',
            'normalization': 'Input/prediction-only, per line/year/new_business; preserves baseline totals', 'no_clipping': True},
        'models': {'P1': 'Full frequency-weather coefficients', 'P2': 'Half coefficients', 'P3': 'Quarter coefficients'},
        'criterion': {'delta_min': .002, 'lower95_gt': 0., 'positive_folds_min': 4, 'min_cell_delta_full_null': -.001,
            'post31_nonnegative': True, 'both_years_nonnegative': True,
            'additional_veto': 'Weighted2025 sensitivity point positive and originalA1_2024 proxy not negative; weighted-primary ESS gate remains failed'},
        'bootstrap': {'replicates': 2000, 'seed': 2026102602, 'unit': 'saved connected component', 'quantiles': [.025, .975]},
        'conditional_observation_stress': 'Only if at least one primary candidate passes all exploratory checks: repeat source fits with already prepared empirical1095 E_count, no new curve fit. No selecting the stress coefficients as a new winner.',
        'budget': {'primary_source_Poisson_fits': 11, 'conditional_stress_fits_max': 11, 'new_C0_fits': 0,
            'new_source_T2b_inferences': 0, 'target_model_fits': 0, 'primary_year_business_normalizers': 180,
            'new_test_prices': 0, 'submissions': 0},
        'limits': ['Official annual covariates used conditionally, no quote-time vintage claim', '2024adaptive development; no independent prospective confirmation',
            'Source risk nuisance was learned on the fixed source itself, target-bootstrap conditional on source',
            'Frequency-only weather assumes no additional weather-severity correction; global peril mix is approximate row decomposition',
            'RKM tail beyond1361 and cost-curve1095 tail/case-reserve adequacy remain unproven',
            'Only weather ratios transfer, no unavailable credit labels reconstructed', 'No automatic admission, test CSV or use of the last slot'],
        'sources': sources, 'B00_preserved': True, 'all_alternatives_preserved': True}
    dump(PLAN, plan); body = OUT / 'forum_previo.md'
    body.write_text('Se preinscribe una corrección de frecuencia meteorológica con Poisson GLM para 11 perils físicos. '
        'La respuesta es número de siniestros, con E_count_RKM ya conciliado; no se ajustan nuevas curvas ni severidades. '
        'Se reutilizan los offsets T2b fuente guardados. El clima es anual menos su media histórica por dirección, por lo que no se incorporan los efectos estáticos nuevos que deterioraron W7.\n\n'
        'Los controles fuente de región, edad, crédito, mes, año y riesgo base no se trasladan. El crédito es nuisance fuente: no se inventa un valor emergente. '
        'Los únicos efectos aplicados son cocientes de frecuencia meteorológica, combinados con las mezclas de coste C0 que excluyen el fold retenido y normalizados sin etiquetas por año/negocio.\n\n'
        'Se conservan los criterios principales y los vetos de la sensibilidad2025 y A1 original2024. El fallo de ESS sigue vigente y no rescata modelos. '
        'Presupuesto: 11 GLM; otros 11 solo como control de observación si el candidato pasa todos los controles principales, usando la exposición empírica ya guardada. '
        'Cero C0, nuevas inferencias T2b, precios de test o envíos. Plan y mapa físico: ' + rel(PLAN) + '.\n', encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA8-PREVIO', '--asunto',
        'Poisson por peril para cambios meteorológicos: 11 GLM estándar, curvas y base conservadas', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(p.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'source_GLM_budget': 11, 'new_fits': 0, 'submissions': 0}))

def run():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    for path, digest in plan['sources'].items(): assert sha(ROOT / path) == digest, path
    assert not (OUT / 'started.json').exists(); dump(OUT / 'started.json', {'utc': now(), 'pid': os.getpid()})
    old = pd.read_parquet(m.CV / 'oof_2023_2024.parquet')
    weights = pd.read_parquet(WEIGHTS / 'weights.parquet', columns=['row_id', 'weight']); outputs = []; fits = 0
    with threadpool_limits(limits=2):
        for line in MAP:
            f = pd.read_parquet(OUT / f'source_{line}.parquet'); models = {}
            for peril in MAP[line]:
                print(json.dumps({'event': 'fit_started', 'line': line, 'peril': peril}), flush=True)
                a = fit(f, line, peril); models[peril] = a; fits += 1
                dump(OUT / f'{line}_{peril}.json', {**a, 'source_input_sha256': sha(OUT / f'source_{line}.parquet')})
                print(json.dumps({'event': 'fit_completed', 'line': line, 'peril': peril, 'fits': fits,
                    'weather_coefficient': a['weather_coefficient'], 'max_gradient': a['max_abs_gradient']}), flush=True)
            t = old.loc[old.line.eq(line)].merge(pd.read_parquet(OUT / f'target_{line}.parquet')[['row_id', *DELTA]], on='row_id', validate='one_to_one')
            t = t.merge(weights, on='row_id', validate='one_to_one')
            for name in ['P1', 'P2', 'P3']: t[name] = np.nan
            for held in range(5):
                parent = m.CV / f'learning_{line}_fold{held}.json'; c0 = read(parent)['artifact']['C0']
                assert sorted(t.loc[t.fold.ne(held), 'row_id']) == c0['fit_row_ids']
                valid = t.loc[t.fold.eq(held)]; normalizers = {}
                for name, strength in [('P1', 1.), ('P2', .5), ('P3', .25)]:
                    prediction, norm = apply(valid, valid.N3.to_numpy(float), models, c0['mixture'], strength)
                    t.loc[t.fold.eq(held), name] = prediction; normalizers[name] = norm
                dump(OUT / f'normalizers_{line}_fold{held}.json', {'parent_C0': rel(parent), 'parent_C0_sha256': sha(parent), 'normalizers': normalizers})
            outputs.append(t)
    p = pd.concat(outputs, ignore_index=True); assert len(p) == 109296 and p.row_id.is_unique and fits == 11
    p.to_parquet(OUT / 'oof_2023_2024.parquet', index=False)
    y = p.T0.to_numpy(float); den = m.unit(y, np.full(len(y), y.mean())).sum()
    scores = {name: float(1 - m.unit(y, p[name].to_numpy(float)).sum() / den) for name in ['N3', 'P1', 'P2', 'P3']}
    dump(OUT / 'price_report.json', {'author': 'Codex', 'utc': now(), 'status': 'prices_scored_validation_pending',
        'scores': scores, 'new_source_frequency_GLM_fits': fits, 'new_source_severity_fits': 0,
        'new_C0_fits': 0, 'new_source_T2b_inferences': 0, 'covariate_only_normalizers': 180,
        'new_test_predictions': 0, 'new_submissions': 0, 'B00_preserved': True, 'goal_achieved': False})
    print(json.dumps({'scores': scores, 'source_GLM_fits': fits, 'new_C0_fits': 0, 'new_test_prices': 0, 'submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['preflight', 'register', 'run']); args = parser.parse_args()
    try: {'preflight': preflight, 'register': register, 'run': run}[args.mode]()
    except Exception as exc:
        if OUT.exists(): dump(OUT / f'failure_{args.mode}_{time.time_ns()}.json', {'utc': now(), 'mode': args.mode,
            'error': type(exc).__name__, 'message': str(exc), 'do_not_repeat_completed_fits_on_retry': True})
        raise
