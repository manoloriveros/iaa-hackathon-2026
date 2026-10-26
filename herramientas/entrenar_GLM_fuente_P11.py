"""GLM fuente de efectos principales, cuatro años, contrato actual A1S.

Sin búsqueda de penalización, interacciones o calibraciones destino en esta etapa.
Coeficientes y preprocesamiento quedan en JSON; no requiere pickle para reproducir.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
import warnings

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P11_GLM_fuente_20261026'; PLAN = R/'registro/semana2_GLM_fuente_privada_plan.json'
INDEX = R/'registro/semana2_GLM_fuente_privada_actual.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.special import logsumexp
import sklearn
from sklearn.linear_model import TweedieRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits

spec = importlib.util.spec_from_file_location('p11_state', R/'herramientas/ablar_exposicion_fuente_P9.py')
state = importlib.util.module_from_spec(spec); spec.loader.exec_module(state); w = state.w
LINES = ['motor', 'buildings', 'contents']
OTHER = '__P11_OTHER__'; MISSING = '__P11_MISSING__'
PARAMS = dict(power=1.5, alpha=1., link='log', solver='lbfgs', max_iter=3000, tol=1e-7)


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)


def event(kind, **fields):
    with (OUT/'events.jsonl').open('a', encoding='utf8') as f:
        f.write(json.dumps({'utc': utc(), 'kind': kind, **fields})+'\n')


def catvalues(s):
    a = s.astype(object).where(s.notna(), MISSING).astype(str)
    assert not (a.eq(OTHER)).any()
    return a


def fit_preprocessor(x):
    assert x.columns.is_unique and not {'T0', 'T0_cents', 'e_cost', 'reserve', 'row_id'}.intersection(x)
    numeric = {}; categorical = {}
    for name in x:
        s = x[name]
        if isinstance(s.dtype, pd.CategoricalDtype) or not pd.api.types.is_numeric_dtype(s):
            a = catvalues(s); counts = a.value_counts()
            ordered = sorted(counts.items(), key=lambda p: (-p[1], p[0]))
            top = sorted([key for key, value in ordered if value >= 100][:39])
            # Unknown and rare levels share a fixed bucket, never learned from target covariates.
            categorical[name] = top+[OTHER]
        else:
            a = pd.to_numeric(s, errors='coerce').to_numpy(float); finite = np.isfinite(a)
            median = float(np.median(a[finite])) if finite.any() else 0.
            a = np.where(finite, a, median)
            lo, hi = np.quantile(a, [.005, .995]); z = np.clip(a, lo, hi)
            scale = float(z.std()); scale = scale if scale > 1e-12 else 1.
            numeric[name] = {'median': median, 'lo': float(lo), 'hi': float(hi), 'mean': float(z.mean()), 'scale': scale}
    return {'columns': list(x), 'numeric': numeric, 'categorical': categorical,
            'penalty': 1., 'winsor_quantiles': [.005, .995], 'category_min_frequency': 100, 'max_categories': 40}


def transform(x, prep):
    assert list(x) == prep['columns']
    blocks = []; names = []
    for name, p in prep['numeric'].items():
        a = pd.to_numeric(x[name], errors='coerce').to_numpy(float)
        a = np.where(np.isfinite(a), a, p['median'])
        blocks.append(sparse.csr_matrix(((np.clip(a, p['lo'], p['hi'])-p['mean'])/p['scale'])[:, None]))
        names.append(name)
    for name, levels in prep['categorical'].items():
        lookup = {value: i for i, value in enumerate(levels)}; default = len(levels)-1
        codes = catvalues(x[name]).map(lookup).fillna(default).to_numpy(int)
        use = codes > 0; indices = np.flatnonzero(use)
        block = sparse.csr_matrix((np.ones(len(indices)), (indices, codes[use]-1)), shape=(len(x), len(levels)-1))
        blocks.append(block); names += [name+'='+value for value in levels[1:]]
    mat = sparse.hstack(blocks, format='csr'); assert np.isfinite(mat.data).all()
    return mat, names


def gradient(mat, rate, weight, coef, intercept):
    pred = np.exp(mat@coef+intercept)
    z = weight*(np.sqrt(pred)-rate/np.sqrt(pred))/weight.sum()
    return np.r_[np.asarray(mat.T@z).ravel()+coef, z.sum()]


def objective(mat, rate, weight, theta):
    pred = np.exp(mat@theta[:-1]+theta[-1])
    return float(.5*np.average(4*rate/np.sqrt(pred)+4*np.sqrt(pred)-8*np.sqrt(rate), weights=weight)+.5*np.dot(theta[:-1], theta[:-1]))


def fit_source(x, y, exposure):
    assert np.isfinite(y).all() and (y >= 0).all() and (exposure > 0).all()
    prep = fit_preprocessor(x); mat, names = transform(x, prep)
    annual = y/exposure; weight = np.sqrt(exposure)
    estimator = TweedieRegressor(**PARAMS)
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always'); estimator.fit(mat, annual, sample_weight=weight)
    assert not any(issubclass(z.category, ConvergenceWarning) for z in notes)
    raw = np.asarray(mat@estimator.coef_).ravel()+float(estimator.intercept_)
    assert np.isfinite(raw).all() and np.isfinite(np.exp(raw)).all()
    grad = gradient(mat, annual, weight, estimator.coef_, estimator.intercept_)
    assert float(np.max(np.abs(grad))) <= 1e-4
    assert np.allclose(estimator.predict(mat), np.exp(raw), rtol=2e-14)
    model = {'preprocessor': prep, 'feature_names': names, 'coef': estimator.coef_.tolist(),
             'intercept': float(estimator.intercept_), 'parameters': PARAMS,
             'iterations': int(estimator.n_iter_), 'max_abs_gradient': float(np.max(np.abs(grad)))}
    ii = np.unique(np.linspace(0, len(x)-1, min(16, len(x)), dtype=int))
    dense = mat[ii].toarray()
    manual = np.asarray([math.fsum((row*estimator.coef_).tolist())+float(estimator.intercept_) for row in dense])
    assert np.allclose(manual, raw[ii], rtol=1e-13, atol=1e-12)
    # Rate weighting equals actual cost deviance with a log-exposure offset for p=1.5.
    mu = exposure[ii]*np.exp(raw[ii])
    lhs = np.sum(4*y[ii]/np.sqrt(mu)+4*np.sqrt(mu)-8*np.sqrt(y[ii]))
    rhs = np.sum(np.sqrt(exposure[ii])*(4*annual[ii]/np.sqrt(np.exp(raw[ii]))+4*np.sqrt(np.exp(raw[ii]))-8*np.sqrt(annual[ii])))
    assert math.isclose(float(lhs), float(rhs), rel_tol=1e-12, abs_tol=1e-8)
    return model, raw, {'manual_linear_predictor_exact_tolerance': True, 'offset_deviance_homogeneity_checked': True,
                        'source_rows': len(x), 'parameters': len(names)+1, 'warnings': [str(z.message) for z in notes]}


def predict(x, model):
    mat, names = transform(x, model['preprocessor']); assert names == model['feature_names']
    return np.asarray(mat@np.asarray(model['coef'])).ravel()+model['intercept']


def synthetic():
    x = pd.DataFrame({'numeric': np.arange(120, dtype=float), 'exposure_model': .3+np.arange(120)/200,
                      'cat': pd.Categorical(['a', 'b']*60)})
    x.loc[3, 'numeric'] = np.nan
    y = np.where(np.arange(120) % 7 == 0, 7., 0.); e = x.exposure_model.to_numpy()
    model, raw, controls = fit_source(x, y, e)
    loaded = json.loads(json.dumps(model)); assert np.array_equal(predict(x, loaded), raw)
    perm = np.arange(120)[::-1]; assert np.array_equal(predict(x.iloc[perm], loaded), raw[perm])
    foreign = x.iloc[:3].copy(); foreign['cat'] = pd.Categorical(['UNSEEN', 'a', None])
    assert np.isfinite(predict(foreign, loaded)).all()
    mat, _ = transform(x, model['preprocessor']); theta = np.r_[model['coef'], model['intercept']]
    grad = gradient(mat, y/e, np.sqrt(e), theta[:-1], theta[-1]); errors = []
    for j in range(len(theta)):
        plus = theta.copy(); minus = theta.copy(); plus[j] += 1e-5; minus[j] -= 1e-5
        numeric = (objective(mat, y/e, np.sqrt(e), plus)-objective(mat, y/e, np.sqrt(e), minus))/2e-5
        errors.append(abs(numeric-grad[j]))
    assert max(errors) < 1e-7
    return {'synthetic_source_GLM_fits_separate': 1, 'whole_fit_transform_predict_JSONreplay_order_checked': True,
            'unknown_missing_categories_handled': True, 'penalized_gradient_finite_difference_max_error': max(errors),
            'rate_offset_two_methods': True, 'new_contest_fits': 0}


def prepare():
    assert not PLAN.exists() and not OUT.exists()
    assert not w.read(state.PHASE).get('active_jobs') and not w.read(state.PHASE).get('active_execution')
    OUT.mkdir()
    old = R/'src/semana2/modelo_profesor_comun2023.py'
    guard = R/'src/semana2/modelo_transferencia2023_v2.py'
    paths = [Path(__file__), Path(state.__file__), old, guard, HOME/'report.json', HOME/'source_models/report.json',
             BASE/'P10_validacion_sin_exposicion_20261026/report.json']
    scopes = []
    for line in LINES:
        for market in ['s1', 's2']:
            paths += [HOME/f'matrix_{market}_{line}.parquet', HOME/f'rows_{market}_{line}.parquet']
        rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet')
        assert rows.year.isin([2021, 2022, 2023, 2024]).all() and not rows.is_test.any() and rows.row_id.is_unique
        scopes.append({'line': line, 'source_rows': len(rows), 'source_years': sorted(map(int, rows.year.unique()))})
    fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'GLM4_main_effects',
            'hypothesis': 'A penalized main-effects backbone can reduce fragile source tree interactions during the large future business-mix shift; evaluate complete S2/H1prices rather than infer benefit from simplicity.',
            'necessity': 'P10did not support dropping duration. Existing source GLM physical teachers use source2023-only and older feature/observation contracts; this uses current source2021-2024matrices/history/e_cost rather than repeating identical recipes.',
            'features': 'All current A1Spredictors including exposure_model, capital/history and source-only categories; main effects, no interactions, splines, region or IDs added.',
            'preprocessing': 'Source-only numeric median, fixed0.5/99.5percentwinsor and standardization; category minimum100,max40, OTHERbucket/dropfirst. Frozen JSON applied without target fitting.',
            'estimator': PARAMS, 'objective': 'Source T0/e_cost annual rate, sample_weight=sqrt(e_cost) exactly equals cost Tweedie1.5deviance with log(e_cost) offset; alpha1 fixed from existing standard sourceGLMrecipe, no hypersearch.',
            'normalization': 'Exposure_model-weighted source mean exp(linearpredictor) one; the target S2component later learns the original shapes/levels on its own fold, no target sourcecentering.',
            'budget': {'source_GLM_fits': 3, 'new_C0_fits': 0, 'target_calibrations': 0, 'target_scores': 0,
                       'future2025inference': 0, 'finaltestprices': 0, 'submissions': 0},
            'criteria': 'Technical source stage only: convergence, gradient<=1e-4, scalar math, JSONreload/order exact, positive finite components, source centering. No predictiveadoption until separate complete group/year/stress comparison with current S2/H1and same gates.',
            'scopes': scopes, 'preflight': fixture, 'sources': {w.rel(p): w.sha(p) for p in paths},
            'limits': ['Source2021-2024labels and whole-source C0 are conditional, not prospective2023.',
                       'Undated source masters and emerging adaptive2024limits remain.',
                       'Main effects and fixed penalty may underfit; simplicity alone does not establish private improvement.',
                       'Not the exact historical delivered F3c backbone, no publicscore decision.'],
            '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P11, GLM fuente de efectos principales sobre matrices actuales2021–2024. '
                    'Los GLMprofesores históricos fuente2023solo no se repiten: cambian ámbito temporal, historia y enlace de coste actuales. '
                    'Se conserva exposure_modelcomo predictor tras el adverso P10. Modelo Tweedie1,5, penalización1fija, sin interacciones, splines o búsqueda;3fits, uno por ramo. '
                    'El objetivo T0/e_costcon peso sqrt(e_cost) concilia exactamente la desviación de coste con offset log(e_cost). '
                    'Medianas, winsorización0,5/99,5%, escalas y categorías se aprenden solo en fuente. Parámetros y predicciones reproducibles medianteJSON, sin pickle. '
                    'El fixture comprobó flujo, valores desconocidos, orden, gradiente por diferencias finitas y álgebra del offset. '
                    'Aquí no se calibra/puntúa destino, no se infiere2025ni se producen precios o envíos. '
                    'La comparación completa posterior mantendrá grupos, años, sensibilidades y mínimos, sin elegir por público o totales. '
                    'B00/F3c/P6y alternativas intactos,2024abierto adaptativo, privada prioritaria. '
                    'Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P11-GLM-PREVIO', '--asunto',
                             'P11 previo: GLM estándar fuente de cuatro años, sin búsqueda de capacidad', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P11registered_before_sourcefit', 'plan': w.rel(PLAN),
               'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'preflight': 'passed', 'new_source_fits': 0, 'planned_source_fits': 3, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'kind': 'P11standard_source_GLM',
                 'script': w.rel(Path(__file__)), 'output': w.rel(OUT)}
    dump(OUT/'started.json', execution); state.state_execution(execution)
    try:
        records = []
        for line in LINES:
            folder = OUT/line; folder.mkdir()
            x = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet')
            rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet'); assert len(x) == len(rows)
            dump(folder/'fit_invoked.json', {'utc': utc(), 'plan_sha256': w.sha(PLAN), 'line': line})
            event('source_GLM_started', line=line); started = time.monotonic()
            model, raw, controls = fit_source(x, rows.T0.to_numpy(float), rows.e_cost.to_numpy(float))
            dump(folder/'model.json', model)
            record = {'utc': utc(), 'line': line, 'seconds': time.monotonic()-started,
                      'model_sha256': w.sha(folder/'model.json'), 'sklearn_version': sklearn.__version__,
                      'parameters': len(model['coef'])+1, 'max_abs_gradient': model['max_abs_gradient'],
                      'iterations': model['iterations'], 'controls': controls}
            dump(folder/'fit_record.json', record); event('source_GLM_completed', **record)
            weight = rows.exposure_model.to_numpy(float)
            center = float(logsumexp(raw, b=weight)-np.log(weight.sum()))
            independent = state.scalar_center(raw, weight); assert abs(center-independent) < 1e-12
            assert abs(np.average(np.exp(raw-center), weights=weight)-1) < 2e-12
            source = rows[['row_id', 'year']].copy(); source['raw_log_rate'] = raw
            source.to_parquet(folder/'source_raw.parquet', index=False)
            # No target row enters preprocessing or fit_source above.
            target_rows = pd.read_parquet(HOME/f'rows_s2_{line}.parquet')
            use = ~target_rows.is_test.to_numpy(bool)
            tx = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet').loc[use].copy()
            metadata = target_rows.loc[use, ['row_id', 'year', 'is_test']].copy().reset_index(drop=True)
            assert metadata.year.isin([2023, 2024]).all() and metadata.row_id.is_unique
            traw = predict(tx, model); loaded = w.read(folder/'model.json')
            assert np.array_equal(traw, predict(tx, loaded))
            ii = np.unique(np.linspace(0, len(tx)-1, 32, dtype=int))
            assert np.array_equal(traw[ii[::-1]], predict(tx.iloc[ii[::-1]], loaded))
            metadata['raw_log_rate'] = traw; metadata['log_relative_A1S'] = traw-center
            assert np.isfinite(np.exp(metadata.log_relative_A1S)).all() and np.exp(metadata.log_relative_A1S).gt(0).all()
            metadata.to_parquet(OUT/f'historical_{line}_three_seed.parquet', index=False)
            # Filename is an adapter interface, not three GLM fits or an ensemble.
            dump(folder/'application.json', {'line': line, 'source_center': center, 'scalar_center': independent,
                                            'source_rows': len(rows), 'historical_rows': len(metadata), 'source_GLMs': 1,
                                            'adapter_filename_three_seed_means_interface_only': True,
                                            'raw_source_sha256': w.sha(folder/'source_raw.parquet'),
                                            'historical_components_sha256': w.sha(OUT/f'historical_{line}_three_seed.parquet'),
                                            'new_future2025inference': 0})
            records.append(record); del x, rows, source, raw, tx, traw; gc.collect()
            print(json.dumps({'line': line, 'complete': True, 'parameters': record['parameters'],
                              'gradient': record['max_abs_gradient'], 'seconds': record['seconds']}), flush=True)
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P11standard_source_GLMs_complete_target_validation_pending',
                  'new_source_GLM_fits': 3, 'new_C0_fits': 0, 'new_target_calibrations': 0, 'new_target_scores': 0,
                  'new_future2025inference': 0, 'new_finaltestprices': 0, 'new_submissions': 0,
                  'records': records, 'source_models_per_line': 1, 'predictive_adoption': False,
                  'private_improvement_established': False, 'plan_sha256': w.sha(PLAN), 'limits': plan['limits'],
                  '2024_open': True, 'B00_all_alternatives_preserved': True}
        dump(OUT/'report.json', report); print(json.dumps({'status': report['status'], 'new_source_fits': 3}))
    except BaseException as exc:
        dump(OUT/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),
             {'exception': type(exc).__name__, 'message': str(exc), 'fit_invocations': len(list(OUT.glob('*/fit_invoked.json'))),
              'saved_models': len(list(OUT.glob('*/model.json'))), 'next': 'Preserve all attempts; reconcile source cache before any further fit'})
        raise
    finally: state.state_execution(None)


def replay():
    assert (OUT/'report.json').exists() and not (OUT/'replay_report.json').exists()
    plan = w.read(PLAN); before = w.sha(OUT/'events.jsonl')
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    old = TweedieRegressor.fit
    def reject(*a, **kw): raise AssertionError('GLM fitting forbidden during replay')
    TweedieRegressor.fit = reject
    try:
        for line in LINES:
            folder = OUT/line; model = w.read(folder/'model.json'); app = w.read(folder/'application.json')
            assert w.sha(folder/'model.json') == w.read(folder/'fit_record.json')['model_sha256']
            raw = pd.read_parquet(folder/'source_raw.parquet').raw_log_rate.to_numpy(float)
            ew = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['exposure_model']).exposure_model.to_numpy(float)
            assert abs(state.scalar_center(raw, ew)-app['source_center']) < 1e-12
            tr = pd.read_parquet(HOME/f'rows_s2_{line}.parquet'); hist = ~tr.is_test.to_numpy(bool)
            tx = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet').loc[hist]
            saved = pd.read_parquet(OUT/f'historical_{line}_three_seed.parquet')
            rerun = predict(tx, model)
            assert np.array_equal(rerun, saved.raw_log_rate) and np.array_equal(rerun-app['source_center'], saved.log_relative_A1S)
    finally: TweedieRegressor.fit = old
    assert w.sha(OUT/'events.jsonl') == before
    dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P11JSONhistorical_flow_replay_exact',
                                  'all3lines_exact': True, 'new_fits': 0, 'new_test_inference': 0,
                                  'recomputed_historical_GLM_rows_separate': 109296,
                                  'report_sha256': w.sha(OUT/'report.json'), 'events_unchanged': True})
    print(json.dumps({'replay': 'exact', 'new_fits': 0, 'new_test_inference': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
