"""GAM fuente estándar con curvas fijas, ausencia observable y JSONportable.

Añade solo curvas univariadas a la receta MI; no interacciones ni tuning.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; P14 = BASE/'P14_GLM_ausentes_20261026'
OUT = BASE/'P16_GAM_fuente_20261026'
PLAN = R/'registro/semana2_GAM_fuente_privada_plan.json'
INDEX = R/'registro/semana2_GAM_fuente_privada_actual.json'
sp = importlib.util.spec_from_file_location('p16_missing_source_helpers', R/'herramientas/GLM_ausentes_privada_P14.py')
mi = importlib.util.module_from_spec(sp); sp.loader.exec_module(mi)
producer = mi.old; np = mi.np; pd = mi.pd; sparse = mi.sparse; w = mi.w
from sklearn.preprocessing import SplineTransformer
from scipy.interpolate import BSpline

CURVES = {'motor': ['ncb_years', 'vehicle_age', 'years_licensed', 'vehicle_value_group', 'engine_size_cc'],
          'buildings': ['log_si', 'prop_age', 'distance_to_river_km', 'elevation_m'],
          'contents': ['log_si', 'bedrooms', 'distance_to_river_km', 'elevation_m']}


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)


def line_from_columns(x):
    if 'vehicle_value_group' in x: return 'motor'
    if 'days_unoccupied' in x: return 'buildings'
    if 'high_value_items' in x: return 'contents'
    raise AssertionError('Source line cannot be determined from the fixed physical schema')


def basis_input(x, prep, name):
    p = prep['numeric'][name]; value = pd.to_numeric(x[name], errors='coerce').to_numpy(float)
    value = np.where(np.isfinite(value), value, p['median']); value = np.clip(value, p['lo'], p['hi'])
    if name == 'distance_to_river_km':
        assert (value >= 0).all(); value = np.log1p(value)
    return value


def fit_preprocessor(x):
    prep = mi.fit_preprocessor(x); line = line_from_columns(x)
    prep['spline_line'] = line; prep['splines'] = {}
    for name in CURVES[line]:
        assert name in prep['numeric']
        value = basis_input(x, prep, name)
        knots = np.quantile(value, np.linspace(0, 1, 4)); assert np.all(np.diff(knots) > 0), name
        estimator = SplineTransformer(n_knots=4, degree=2, knots='quantile', include_bias=False, extrapolation='constant')
        basis = estimator.fit_transform(value[:, None]); spline = estimator.bsplines_[0]
        # JSON stores the scipy spline data, not a pickle or a fitted sklearn object.
        restored = BSpline(spline.t, spline.c, spline.k, extrapolate=False)(value)[:, :-1]
        assert np.array_equal(basis, restored)
        mean = basis.mean(axis=0); scale = basis.std(axis=0); assert (scale > 1e-12).all()
        prep['splines'][name] = {'t': spline.t.tolist(), 'c': spline.c.tolist(), 'k': int(spline.k),
                                'mean': mean.tolist(), 'scale': scale.tolist(),
                                'input_min': float(value.min()), 'input_max': float(value.max()),
                                'log1p_distance': name == 'distance_to_river_km', 'drop_last_basis': True,
                                'sklearn_to_scipy_source_basis_exact': True}
    return prep


def transform(x, prep):
    linear = dict(prep); linear['numeric'] = {k: v for k, v in prep['numeric'].items() if k not in prep['splines']}
    base, names = mi.transform(x, linear); blocks = [base]
    for name, z in prep['splines'].items():
        value = basis_input(x, prep, name)
        assert value.min() >= z['input_min']-1e-12 and value.max() <= z['input_max']+1e-12
        basis = BSpline(np.asarray(z['t']), np.asarray(z['c']), z['k'], extrapolate=False)(value)[:, :-1]
        normalized = (basis-np.asarray(z['mean']))/np.asarray(z['scale'])
        assert np.isfinite(normalized).all(); blocks.append(sparse.csr_matrix(normalized))
        names += [name+'__spline_'+str(i) for i in range(normalized.shape[1])]
    return sparse.hstack(blocks, format='csr'), names


producer.fit_preprocessor = fit_preprocessor; producer.transform = transform
producer.OUT = OUT; producer.PLAN = PLAN; producer.INDEX = INDEX


def synthetic():
    idx = np.arange(240)
    x = pd.DataFrame({'log_si': np.log(50000+idx*500), 'prop_age': idx.astype(float)/2,
                      'distance_to_river_km': .05+idx/50, 'elevation_m': idx.astype(float),
                      'days_unoccupied': (idx % 31).astype(float), 'exposure_model': .3+(idx % 31)/50,
                      'category': pd.Categorical(['a', 'b']*120)})
    x.loc[3, 'prop_age'] = np.nan
    y = np.where(idx % 7 == 0, 10.+idx/20, 0.); e = x.exposure_model.to_numpy()
    model, raw, controls = producer.fit_source(x, y, e)
    assert len(model['preprocessor']['splines']) == 4
    loaded = json.loads(json.dumps(model)); assert np.array_equal(producer.predict(x, loaded), raw)
    ii = idx[::-1]; assert np.array_equal(producer.predict(x.iloc[ii], loaded), raw[ii])
    extreme = x.iloc[[0, -1]].copy(); extreme.loc[:, 'prop_age'] = [-1e8, 1e8]
    assert np.isfinite(producer.predict(extreme, loaded)).all()
    mat, _ = transform(x, model['preprocessor']); theta = np.r_[model['coef'], model['intercept']]
    grad = producer.gradient(mat, y/e, np.sqrt(e), theta[:-1], theta[-1]); errors = []
    for j in range(len(theta)):
        plus = theta.copy(); minus = theta.copy(); plus[j] += 1e-5; minus[j] -= 1e-5
        check = (producer.objective(mat, y/e, np.sqrt(e), plus)-producer.objective(mat, y/e, np.sqrt(e), minus))/2e-5
        errors.append(abs(check-grad[j]))
    assert max(errors) < 1e-7
    return {'synthetic_source_GAM_fits_separate': 1, 'four_actual_source_spline_variables_exercised': True,
            'sklearn_scipy_JSONbasis_exact': True, 'complete_fit_predict_replay_order_exact': True,
            'extreme_input_clip_endpoint_checked': True, 'missing_indicator_retained': 'prop_age__is_missing' in model['feature_names'],
            'penalized_gradient_finite_difference_max_error': max(errors), 'new_contest_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert not w.read(producer.state.PHASE).get('active_jobs') and not w.read(producer.state.PHASE).get('active_execution')
    OUT.mkdir()
    previous_path = R/'registro/semana2_GLM_ausentes_fuente_plan.json'; previous = w.read(previous_path)
    assert all(w.sha(ROOT/p) == z for p, z in previous['sources'].items())
    sources = dict(previous['sources'])
    paths = [Path(__file__), Path(mi.__file__), previous_path, P14/'context_report.json',
             BASE/'P15_validacion_ausentes_20261026/context_report.json',
             R/'src/semana2/modelos_robustos2023.py', R/'src/semana2/modelo_fuente_aditivo2023.py']
    sources.update({w.rel(p): w.sha(p) for p in paths})
    fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'GAM4_MI',
            'hypothesis': 'Fixed univariate functional flexibility can improve current standardGLMallocation loss without interactions or target-selected variables; missing indicators alone did not establish improvement.',
            'necessity': 'P13shows some current GLMcell losses remain even at oracle scalar, and P15does not establish missingness-only correction. This motivates testing shape flexibility but does not prove nonlinear causality.',
            'curves': CURVES, 'curve_origin': 'Historical sourceGAMdomain variable list in modelos_robustos2023.SPLINE, mapped to current A1Scommon features; no selection from current target gains.',
            'basis': {'n_knots': 4, 'degree': 2, 'knots': 'source quantiles after existing source imputation/clip',
                      'include_bias': False, 'extrapolation': 'constant through existing input clipping',
                      'basis_standardization': 'source mean/std per basis column',
                      'distance': 'log1p nonnegative distance, matching historical log-distance domain specification',
                      'duplicate_quantile_rule': 'Fail before model fitting, never silently change knots or select another shape'},
            'retained': 'P14source2021-2024data/T0/e_cost, alpha1 and numeric missing indicators; original other linear/categorical predictors and no interactions. Old source2023GAMfits not repeated on identical data.',
            'engine': {'source': w.rel(Path(producer.__file__)), 'process_local_bindings': ['P16fit_preprocessor', 'P16transform', 'P16paths'],
                       'raw_engine_identity': 'P11', 'new_candidate_identity': 'GAM4_MI'},
            'estimator': producer.PARAMS, 'scopes': previous['scopes'], 'preflight': fixture,
            'budget': {'source_GAM_fits': 3, 'new_C0_fits': 0, 'target_calibrations': 0, 'target_scores': 0,
                       'future2025inference': 0, 'finaltestprices': 0, 'submissions': 0},
            'criteria': 'Same convergence/gradient/offset/centering/JSONflow controls, plus source spline basis exact and endpoint checks. No predictive adoption before complete preinscribed group/year/stress comparison versus A1Sprimary and linear-MIsecondary.',
            'sources': sources, 'limits': previous['limits']+['More flexible main effects can still underfit interactions or overfit source patterns.',
                                                            'Fixed historical domain list and knots are not optimized for current validation; source2024and target adaptation remain conditional.'],
            '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P16antes de ajustar: GAMfuente de efectos principales, mismo contrato2021–2024e indicadores P14. '
                    'Se usan curvas univariadas de la lista física GAMhistórica, no elegidas por resultados actuales:5variables autos,4edificios y4contenidos. '
                    'Cuatro nudos por cuantiles fuente, grado2, sininteracciones, alpha1fijo, extrapolación constante mediante el recorte fuente existente. '
                    'La distancia usa log1pcomo especificación de dominio previa. Todas las demás variables/categorías e indicadores se conservan. '
                    'P13/P15justifican comprobar forma funcional; no demuestran causalidad no lineal. '
                    'Presupuesto3GAMfuente, ceroC0/calibraciones/scoredestino/inferencias2025/precios/envíos. '
                    'El fixture nuevo ejerció las4curvas de edificios, ajuste, gradiente, serialización exacta sklearn→scipy→JSON, ausentes, extremos y orden. '
                    'Antes de puntuar se registrará comparación completa frente a A1Scomo primario y GLMconindicadores como secundario, con criterios intactos. '
                    'No hay búsqueda de nudos, variables, máscaras, pesos o niveles oráculo. B00/F3c/P6y adversos intactos,2024abierto adaptativo. '
                    'Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P16-GAM-PREVIO', '--asunto',
                             'P16 previo: forma aditiva estándar de cuatro años, curvas físicas fijas y sin interacciones',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P16registered_before_sourcefits', 'plan': w.rel(PLAN),
               'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'planned_source_GAMfits': 3, 'new_contest_fits': 0, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'context_report.json').exists()
    if not (OUT/'report.json').exists(): producer.run()
    raw = w.read(OUT/'report.json'); assert raw['plan_sha256'] == w.sha(PLAN)
    models = {}
    for line in producer.LINES:
        model = w.read(OUT/line/'model.json')
        assert set(model['preprocessor']['splines']) == set(CURVES[line])
        assert all(name not in model['feature_names'] for name in CURVES[line])
        models[line] = {'parameters': len(model['coef'])+1, 'curves': CURVES[line],
                        'missing_indicators': list(model['preprocessor']['numeric_missing_indicators']),
                        'max_abs_gradient': model['max_abs_gradient']}
    context = {'author': 'Codex', 'utc': utc(), 'status': 'P16source_GAMcomplete_target_validation_pending',
               'candidate': 'GAM4_MI', 'engine_report': w.rel(OUT/'report.json'), 'engine_report_sha256': w.sha(OUT/'report.json'),
               'models': models, 'source_models_per_line': 1, 'new_source_GAMfits': 3, 'new_C0_fits': 0,
               'new_target_calibrations': 0, 'new_target_scores': 0, 'new_future2025inference': 0,
               'new_finaltestprices': 0, 'new_submissions': 0, 'predictive_adoption': False,
               'private_improvement_established': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
               'plan_sha256': w.sha(PLAN)}
    dump(OUT/'context_report.json', context); print(json.dumps({'status': context['status'], 'models': models}))


def replay():
    producer.replay()
    dump(OUT/'P16_replay_context.json', {'author': 'Codex', 'utc': utc(), 'candidate': 'GAM4_MI',
                                       'new_spline_missingness_bindings_applied': True,
                                       'engine_receipt': w.rel(OUT/'replay_report.json'),
                                       'engine_receipt_sha256': w.sha(OUT/'replay_report.json'),
                                       'context_report_sha256': w.sha(OUT/'context_report.json'),
                                       'new_fits': 0, 'new_test_inference': 0})


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with producer.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
