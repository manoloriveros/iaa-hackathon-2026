"""GLM fuente de clima residual, conservando el riesgo base y los niveles por año/negocio."""
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
spec = importlib.util.spec_from_file_location('parent4', R / 'herramientas/mision017_fase2_tanda4_marketing.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
import numpy as np
import pandas as pd
from scipy import sparse, optimize
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_limits

OUT = R / 'privado/semana2/mision017_fase2/tanda7_clima_20261026_v2'
PLAN = R / 'registro/semana2_mision017_fase2_tanda7_plan_v2.json'
WEIGHTS = OUT.parent / 'estimando_cartera2025_v3'
SCOPE = R / 'registro/semana2_alcance_covariables_oficiales2025_v3.json'
FIELDS = ['hail_days', 'wind_exposure_index', 'freezing_days', 'dry_summer_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c']
CORE = ['wind_anomaly', 'wildfire_anomaly', 'lograin_anomaly', 'temperature_anomaly']
EXTRA = ['log_hail', 'log_freezing', 'dry_summer']
ALPHA = 1.
sha = m.sha; read = m.read; dump = m.dump; rel = m.rel
now = lambda: datetime.now(timezone.utc).isoformat()

def weather_features(f):
    assert f.annual_rainfall_mm.ge(0).all() and f.annual_hail_days.ge(0).all() and f.annual_freezing_days.ge(0).all()
    return pd.DataFrame({
        'wind_anomaly': f.annual_wind_exposure_index.to_numpy(float) - f.clima_wind_exposure_index.to_numpy(float),
        'wildfire_anomaly': f.annual_wildfire_index.to_numpy(float) - f.clima_wildfire_index.to_numpy(float),
        'lograin_anomaly': np.log1p(f.annual_rainfall_mm.to_numpy(float)) - np.log1p(f.clima_rainfall_mm.to_numpy(float)),
        'temperature_anomaly': f.annual_mean_temperature_c.to_numpy(float) - f.clima_mean_temperature_c.to_numpy(float),
        'log_hail': np.log1p(f.annual_hail_days.to_numpy(float)),
        'log_freezing': np.log1p(f.annual_freezing_days.to_numpy(float)),
        'dry_summer': f.annual_dry_summer_index.to_numpy(float)}, index=f.index)

def fit(f, extended):
    assert f.market.eq('developed').all() and f.year.isin([2021, 2022, 2023, 2024]).all()
    columns = CORE + (EXTRA if extended else [])
    a = f[columns].to_numpy(float); center = a.mean(axis=0); scale = a.std(axis=0)
    assert np.isfinite(a).all() and (scale > 1e-8).all()
    z = (a - center) / scale
    region = OneHotEncoder(drop='first', sparse_output=True)
    xr = region.fit_transform(f[['source_region']].astype(str))
    year = OneHotEncoder(drop=None, sparse_output=True); xy = year.fit_transform(f[['year']])
    X = sparse.hstack([sparse.csr_matrix(z), xr, xy], format='csr')
    penalty = np.r_[np.ones(len(columns)), np.zeros(xr.shape[1] + xy.shape[1])]
    y = f.T0.to_numpy(float); offset = f.offset.to_numpy(float); off = np.log(offset)
    beta = np.zeros(X.shape[1])
    for j, y0 in enumerate(year.categories_[0]):
        mask = f.year.eq(y0).to_numpy()
        k = float(np.sum(y[mask] / np.sqrt(offset[mask])) / np.sum(np.sqrt(offset[mask]))); assert k > 0
        beta[len(columns) + xr.shape[1] + j] = np.log(k)
    def objective(coef):
        root = np.exp((off + X @ coef) / 2)
        value = 2 * np.mean(root + y / root - 2 * np.sqrt(y)) + .5 * ALPHA * np.dot(penalty * coef, coef)
        gradient = np.asarray(X.T @ ((root - y / root) / len(y))).ravel() + ALPHA * penalty * coef
        return float(value), gradient
    result = optimize.minimize(objective, beta, method='L-BFGS-B', jac=True,
        options={'maxiter': 2000, 'gtol': 1e-7, 'ftol': 1e-13, 'maxls': 40})
    value, gradient = objective(result.x)
    assert result.success and np.abs(gradient).max() < 1e-4, str(result.message)
    root = np.exp((off + X @ result.x) / 2)
    curvature = .5 * (root + y / root) / len(y)
    H = (X.T @ X.multiply(curvature[:, None])).toarray() + ALPHA * np.diag(penalty)
    inverse = np.linalg.inv(H)
    keys = f.source_region.astype(str).to_numpy() + '|' + f.year.astype(str).to_numpy()
    residual = (root - y / root) / len(y); scores = []
    for key in sorted(set(keys)):
        mask = keys == key; scores.append(np.asarray(X[mask].T @ residual[mask]).ravel())
    U = np.stack(scores); covariance = inverse @ (U.T @ U) @ inverse * len(U) / (len(U) - 1)
    influence = U @ inverse.T
    return {'extended': extended, 'features': columns, 'coef': result.x.tolist(), 'center': center.tolist(), 'scale': scale.tolist(),
        'source_regions': region.categories_[0].tolist(), 'source_years': year.categories_[0].tolist(),
        'penalty': penalty.tolist(), 'alpha': ALPHA, 'objective': value, 'iterations': int(result.nit),
        'max_abs_gradient': float(np.abs(gradient).max()), 'rows': len(f), 'price_estimator_fits': 1,
        'weather_coefficient': {name: float(result.x[j]) for j, name in enumerate(columns)},
        'source_region_year_clusters': len(U), 'weather_cluster_sandwich_sd': np.sqrt(np.diag(covariance)[:len(columns)]).tolist(),
        'weather_cluster_covariance': covariance[:len(columns), :len(columns)].tolist(),
        'max_linearized_cluster_coefficient_change': np.max(abs(influence[:, :len(columns)]), axis=0).tolist(),
        'cluster_variance_is_approximate_not_refitted_or_independent_validation': True,
        'feature_min': a.min(axis=0).tolist(), 'feature_max': a.max(axis=0).tolist()}

def apply(f, base, artifact, strength):
    a = f[artifact['features']].to_numpy(float)
    z = (a - np.asarray(artifact['center'])) / np.asarray(artifact['scale'])
    factor = np.exp(strength * (z @ np.asarray(artifact['coef'][:len(artifact['features'])])))
    out = base.copy(); norms = {}
    for year in sorted(f.year.unique()):
        for nb in [0, 1]:
            mask = f.year.eq(year).to_numpy() & f.new_business.to_numpy(dtype=int).__eq__(nb)
            assert mask.any(); norm = float(np.sum(base[mask] * factor[mask]) / np.sum(base[mask]))
            out[mask] = base[mask] * factor[mask] / norm; norms[f'{int(year)}|{nb}'] = norm
            assert np.isclose(out[mask].sum(), base[mask].sum(), rtol=1e-12, atol=1e-6)
    assert np.isfinite(out).all() and (out > 0).all()
    return out, norms

def synthetic():
    rng = np.random.default_rng(2026102601); n = 800
    f = pd.DataFrame({'market': 'developed', 'year': np.arange(n) % 4 + 2021,
        'source_region': rng.choice(['r0', 'r1', 'r2'], n), 'new_business': (np.arange(n) // 4) % 2,
        'T0': rng.gamma(2, 120, n) * (rng.random(n) < .4), 'offset': rng.uniform(30, 200, n)})
    for c in CORE + EXTRA: f[c] = rng.normal(size=n)
    for extended in [False, True]:
        a = fit(f, extended); pred, norm = apply(f, f.offset.to_numpy(float), a, 1.)
        other, norm2 = apply(f.assign(T0=-1e30), f.offset.to_numpy(float), a, 1.)
        assert np.array_equal(pred, other) and norm == norm2
        null = dict(a); null['coef'] = [0.] * len(a['coef'])
        p0, _ = apply(f, f.offset.to_numpy(float), null, 1.); assert np.array_equal(p0, f.offset.to_numpy(float))
    dump(OUT / 'synthetic.json', {'pass': True, 'null_effect_reproduces_base': True, 'held_labels_unused': True,
        'source_year_region_objective_and_sandwich_exercised': True, 'year_business_totals_preserved': True,
        'synthetic_price_fits': 2, 'contest_price_fits': 0})

def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir(parents=True)
    assert read(SCOPE)['new_fits'] == 0
    with threadpool_limits(limits=2): synthetic()
    assert not read(WEIGHTS / 'report.json')['proposed_weighted_primary_estimand_eligibility']
    sources = [Path(__file__), Path(m.__file__), SCOPE, WEIGHTS / 'report.json', WEIGHTS / 'weights.parquet',
        OUT.parent / 'clima2025_auditoria_20261026_v1/report.json', m.CV / 'oof_2023_2024.parquet', m.data.OUT / 'report.json',
        m.data.RAW / 'weather.parquet', m.data.RAW / 'addresses.parquet',
        ROOT / 'Hackaton/Semana 2/Datos/emerging/weather.parquet',
        OUT.parent.parent / 'claude_validacion_nocturna_20261023/predicciones_2024.parquet']
    for line in m.data.LINES:
        sources += [m.data.OUT / f'{line}.parquet', m.PARENT / f'features_{line}.parquet', m.PARENT / f'modelos/prod/T2b_{line}.txt']
    plan = {'id': 'S2-MISION017-FASE2-TANDA7-CLIMA-v2', 'author': 'Codex', 'utc': now(),
        'hypothesis': 'Official2025weather varies materially from the persistent2023/2024mean used by F2. Preserve that baseline and test source-trained main-effect residual weather, rather than repeat E13 replacing the baseline with another GBM.',
        'source': 'Developed2021–2024 price rows, same frozen T2b and observation link, no2025weather in source learning',
        'models': {'W1': 'Four anomalies: current wind/wildfire/temp minus persistent mean, log1p current rain minus log1p persistent rain; full effect',
            'W2': 'W1 plus log1p current hail/freezing days and current dry_summer index, absent from the baseline; full effect',
            'W3': 'Half W2 effect, no additional fit'},
        'configuration': {'objective': 'half Tweedie1.5 deviance of source net observed period cost', 'offset': 'source_e_cost * frozen T2b_rate',
            'feature_scaling': 'source mean/SD, no labels', 'alpha_weather': ALPHA,
            'nuisance': 'free source-region main effects(drop reference) and four free source-year intercepts; no interactions; no nuisance transferred',
            'optimizer': {'method': 'L-BFGS-B', 'maxiter': 2000, 'gtol': 1e-7, 'ftol': 1e-13, 'maxls': 40},
            'target': 'Existing held N3 prices; normalize each line/year/new_business cell using only input covariates and predicted costs',
            'no_clipping_or_target_changes': True},
        'criterion': {'primary': 'Original unweighted D2, frozen five componentfolds across2023/2024; no weighted rescue of failures',
            'delta_min': .002, 'lower95_gt': 0., 'positive_folds_min': 4, 'min_cell_delta_full_null': -.001,
            'post31_nonnegative': True, 'both_years_nonnegative': True,
            'additional_veto': '2025composition weighted sensitivity must have positive point difference; originalA1_2024 proxy must not deteriorate',
            'submission_not_automatic': 'One remaining slot requires separate substantial evidence; passing this exploratory screen alone is insufficient'},
        'bootstrap': {'replicates': 2000, 'seed': 2026102601, 'unit': 'saved connected component', 'quantiles': [.025, .975]},
        'weighted_estimand': {'role': 'diagnostic only, not accepted as primary', 'unchanged_failed_gate': 'row/group ESS fractions>=.1',
            'row_ESS': read(WEIGHTS / 'report.json')['row_ESS'], 'group_ESS': read(WEIGHTS / 'report.json')['group_ESS'],
            'no_clipping_rebinning_or_retroactive_admission': True},
        'budget': {'new_source_price_GLM_fits': 6, 'new_target_price_fits': 0, 'new_C0_fits': 0,
            'new_source_T2b_offset_inferences_cached': 3, 'covariate_only_year_business_normalizers': 180,
            'new_test_price_predictions': 0, 'submissions': 0},
        'limits': ['Conditional use of official annual covariates, not prospective quote-time validation; F05 vintage unresolved',
            '2024adaptive development and source includes developed2024, not pristine temporal confirmation',
            'N3 reference is not the complete submitted F2; originalA1_2024 is only a proxy for model dependence',
            'Source covariance clustered in region×year is approximate; fixed-source target bootstrap omits some source/C0/reserve/master uncertainty',
            'Target2025composition has low effective historical support; no positive result may conceal that limit'],
        'sources': {rel(p): sha(p) for p in sources}, 'B00_preserved': True, 'all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('La propuesta de usar la mezcla2025 como validación primaria falló su control previo: ESS de unas2.921filas y1.572componentes, pesos hasta73,18. '
        'El fallo se conserva. No se recortan pesos ni se cambian bandas para hacerlo pasar. La validación primaria conserva los criterios originales sin ponderación; '
        'la mezcla2025 se informa solo como sensibilidad y no rescata candidatos fallidos.\n\n'
        'Se preinscriben seis GLM fuente (dos por ramo), sin rehacer C0: W1 añade solo cuatro anomalías anuales sobre el riesgo persistente; '
        'W2 incorpora además granizo, heladas y sequedad del año; W3 aplica la mitad de W2 sin otro ajuste. '
        'Cada GLM tiene controles libres de región y año, penalización1 en efectos climáticos y variables estandarizadas con la fuente. '
        'Los efectos se aplican a los precios N3 retenidos, conservando el total de cada ramo/año/negocio con covariables y predicciones.\n\n'
        'Se revisará matemática, coeficientes y dependencia de48bloques región×año de la fuente, así como el efecto sobre A1 original2024 como sustituto imperfecto. '
        'Esto difiere de E13: no sustituye el tronco ni descarta su clima persistente, usa fuente2021–2024 y un overlay GLM sencillo. '
        'El ámbito es condicional a covariables oficiales entregadas, sin afirmación de disponibilidad antes de cotizar ni etiquetas2025. '
        'Cero envíos y cero precios nuevos de test en esta tanda. Plan: ' + rel(PLAN) + '.\n', encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261025-MISION017-FASE2-TANDA7-PREVIO', '--asunto',
        'Clima residual con GLM; se conserva el fallo de soporte de la ponderación2025', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': sha(PLAN), 'forum': json.loads(p.stdout)})
    print(json.dumps({'registered': rel(PLAN), 'real_price_fits': 0, 'submissions': 0}))

def run():
    plan = read(PLAN); assert read(OUT / 'registration.json')['plan_sha256'] == sha(PLAN)
    for p, digest in plan['sources'].items(): assert sha(ROOT / p) == digest, p
    assert not (OUT / 'started.json').exists(); dump(OUT / 'started.json', {'utc': now(), 'pid': os.getpid()})
    source_weather = pd.read_parquet(m.data.RAW / 'weather.parquet', filters=[('year', '<=', 2024)])
    source_weather = source_weather.rename(columns={c: 'annual_' + c for c in FIELDS})
    target_weather = pd.read_parquet(ROOT / 'Hackaton/Semana 2/Datos/emerging/weather.parquet', filters=[('year', '<=', 2024)])
    target_weather = target_weather.rename(columns={c: 'annual_' + c for c in FIELDS})
    assert source_weather.year.le(2024).all() and target_weather.year.le(2024).all()
    regions = pd.read_parquet(m.data.RAW / 'addresses.parquet', columns=['address_id', 'region']).rename(columns={'region': 'source_region'})
    old = pd.read_parquet(m.CV / 'oof_2023_2024.parquet'); weights = pd.read_parquet(WEIGHTS / 'weights.parquet', columns=['row_id', 'weight'])
    outputs = []; fits = 0
    with threadpool_limits(limits=2):
        for line in m.data.LINES:
            f = pd.read_parquet(m.data.OUT / f'{line}.parquet')
            model = m.lgb.Booster(model_file=str(m.PARENT / f'modelos/prod/T2b_{line}.txt'))
            f['offset'] = f.e_cost.to_numpy(float) * np.exp(model.predict(m.source_matrix(f, model), raw_score=True, num_threads=2))
            f = f.merge(regions, on='address_id', validate='many_to_one').merge(source_weather, on=['address_id', 'year'], validate='many_to_one')
            x = weather_features(f)
            for col in x: f[col] = x[col]
            keep = ['row_id', 'market', 'year', 'address_id', 'source_region', 'T0', 'offset', *CORE, *EXTRA]
            small = f[keep].copy(); small.to_parquet(OUT / f'source_inputs_{line}.parquet', index=False)
            del f, model, x
            artifacts = {}
            for extended, name in [(False, 'anomalies'), (True, 'extended')]:
                a = fit(small, extended); artifacts[name] = a; fits += 1
                dump(OUT / f'{name}_{line}.json', {'line': line, 'source_input_sha256': sha(OUT / f'source_inputs_{line}.parquet'), **a})
                print(json.dumps({'line': line, 'family': name, 'fits_total': fits, 'weather_coefficient': a['weather_coefficient'],
                    'max_gradient': a['max_abs_gradient']}), flush=True)
            f = pd.read_parquet(m.PARENT / f'features_{line}.parquet')
            f = f.merge(target_weather, on=['address_id', 'year'], validate='many_to_one')
            x = weather_features(f)
            for col in x: f[col] = x[col]
            covariates = f[['row_id', *CORE, *EXTRA]].copy()
            t = old.loc[old.line.eq(line)].merge(covariates, on='row_id', validate='one_to_one').merge(weights, on='row_id', validate='one_to_one')
            for name in ['W1', 'W2', 'W3']: t[name] = np.nan
            for held in range(5):
                mask = t.fold.eq(held); valid = t.loc[mask]; normalizers = {}
                for name, family, strength in [('W1', 'anomalies', 1.), ('W2', 'extended', 1.), ('W3', 'extended', .5)]:
                    pred, norm = apply(valid, valid.N3.to_numpy(float), artifacts[family], strength)
                    t.loc[mask, name] = pred; normalizers[name] = norm
                dump(OUT / f'normalizers_{line}_fold{held}.json', normalizers)
            outputs.append(t)
    p = pd.concat(outputs, ignore_index=True); assert len(p) == 109296 and p.row_id.is_unique and fits == 6
    p.to_parquet(OUT / 'oof_2023_2024.parquet', index=False)
    y = p.T0.to_numpy(float); den = m.unit(y, np.full(len(y), y.mean())).sum()
    scores = {name: float(1 - m.unit(y, p[name].to_numpy(float)).sum() / den) for name in ['N3', 'W1', 'W2', 'W3']}
    dump(OUT / 'price_report.json', {'author': 'Codex', 'utc': now(), 'status': 'prices_scored_validation_pending',
        'scores': scores, 'new_source_GLM_fits': fits, 'new_C0_fits': 0, 'new_T2b_source_offset_inferences': 3,
        'year_business_covariate_normalizers': 180, 'new_test_predictions': 0, 'new_submissions': 0, 'B00_preserved': True, 'goal_achieved': False})
    print(json.dumps({'scores': scores, 'new_GLM_fits': fits, 'new_C0_fits': 0, 'new_test_predictions': 0, 'submissions': 0}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['register', 'run']); args = parser.parse_args()
    try: register() if args.mode == 'register' else run()
    except Exception as exc:
        if OUT.exists(): dump(OUT / f'failure_{args.mode}_{time.time_ns()}.json', {'utc': now(), 'mode': args.mode,
            'error': type(exc).__name__, 'message': str(exc)})
        raise
