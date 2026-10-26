"""GLM de efectos principales con indicadores estándar de ausencia numérica.

Reutiliza el productor P11 con nuevos preprocesamientos declarados y probados.
Los archivos del productor original no se modifican.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; P11 = BASE/'P11_GLM_fuente_20261026'
P13 = BASE/'P13_atribucion_GLM_20261026'
OUT = BASE/'P14_GLM_ausentes_20261026'
PLAN = R/'registro/semana2_GLM_ausentes_fuente_plan.json'
INDEX = R/'registro/semana2_GLM_ausentes_fuente_actual.json'
sp = importlib.util.spec_from_file_location('p14_source_engine_P11', R/'herramientas/entrenar_GLM_fuente_P11.py')
old = importlib.util.module_from_spec(sp); sp.loader.exec_module(old)
np = old.np; pd = old.pd; sparse = old.sparse; w = old.w
ORIGINAL_PREP = old.fit_preprocessor; ORIGINAL_TRANSFORM = old.transform


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)


def fit_preprocessor(x):
    result = ORIGINAL_PREP(x)
    flags = {}
    for name in result['numeric']:
        values = pd.to_numeric(x[name], errors='coerce').to_numpy(float)
        missing = ~np.isfinite(values); p = float(missing.mean())
        if 0 < p < 1:
            flags[name] = {'mean': p, 'scale': float(np.sqrt(p*(1-p)))}
    result['numeric_missing_indicators'] = flags
    result['indicator_policy'] = 'All nonconstant source numeric missing flags, source-only centered/scaled; same alpha1.'
    return result


def transform(x, prep):
    mat, names = ORIGINAL_TRANSFORM(x, prep)
    blocks = [mat]
    for name, z in prep['numeric_missing_indicators'].items():
        values = pd.to_numeric(x[name], errors='coerce').to_numpy(float)
        indicator = (~np.isfinite(values)).astype(float)
        blocks.append(sparse.csr_matrix(((indicator-z['mean'])/z['scale'])[:, None]))
        names.append(name+'__is_missing')
    result = sparse.hstack(blocks, format='csr'); assert np.isfinite(result.data).all()
    return result, names


# Bindings are process-local and part of this new recipe, not changes to P11files.
old.fit_preprocessor = fit_preprocessor; old.transform = transform
old.OUT = OUT; old.PLAN = PLAN; old.INDEX = INDEX


def synthetic():
    result = old.synthetic()  # One new synthetic GLM, end-to-end with the new bindings.
    x = pd.DataFrame({'numeric': [1., 2., 3., np.nan, 5., 6.], 'exposure_model': [.5]*6})
    prep = fit_preprocessor(x)
    pair = x.iloc[[0, 0]].copy().reset_index(drop=True)
    pair.loc[0, 'numeric'] = np.nan; pair.loc[1, 'numeric'] = prep['numeric']['numeric']['median']
    previous, _ = ORIGINAL_TRANSFORM(pair, prep)
    current, names = transform(pair, prep)
    assert np.array_equal(previous.toarray()[0], previous.toarray()[1])
    assert not np.array_equal(current.toarray()[0], current.toarray()[1])
    assert 'numeric__is_missing' in names and 'exposure_model__is_missing' not in names
    result.update(old_missing_and_observed_median_collision_proved=True, new_indicator_distinguishes_pair=True,
                  constant_missing_indicators_not_added=True)
    return result


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert not w.read(old.state.PHASE).get('active_execution') and not w.read(old.state.PHASE).get('active_jobs')
    OUT.mkdir()
    previous_path = R/'registro/semana2_GLM_fuente_privada_plan.json'; previous = w.read(previous_path)
    assert all(w.sha(ROOT/p) == z for p, z in previous['sources'].items())
    sources = dict(previous['sources'])
    paths = [Path(__file__), Path(old.__file__), previous_path, P11/'report.json', P13/'report.json',
             P13/'bounded_missing_indicator_review.json']
    sources.update({w.rel(p): w.sha(p) for p in paths})
    fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'GLM4_MI',
            'hypothesis': 'A plain median-imputed GLM cannot distinguish observed median from missing numeric data. Explicit source-learned missing main effects may improve transport with12percent missing target versus2.5percent source, without interactions or changed data.',
            'necessity': 'P13shows a representation limitation and a continuing missingness gap, not causal proof of P12loss. Current sourceGLMhas no numeric missing indicators. Do not repeat historical source2023masking fits.',
            'change': 'Add centered/scaled binary is_missing columns for every numeric variable with nonconstant source missingness. Feature selection uses source covariates only; no missingness-outcome screening.',
            'retained': 'All source2021-2024matrices,T0,e_cost, original median/0.5-99.5clip/scales/categories, duration predictor and alpha1main-effects GLM parameters.',
            'source_engine': {'path': w.rel(Path(old.__file__)), 'sha256': w.sha(Path(old.__file__)),
                              'process_local_bindings': ['fit_preprocessor=P14function', 'transform=P14function', 'OUT/PLAN/INDEX=P14paths'],
                              'note': 'Raw report/status/cache interface identifies the reused P11engine; context_report identifies this new candidate. One sourceGLMperline, not3seeds.'},
            'estimator': old.PARAMS, 'scopes': previous['scopes'],
            'budget': {'source_GLM_fits': 3, 'new_C0_fits': 0, 'target_calibrations': 0, 'target_scores': 0,
                       'future2025inference': 0, 'finaltestprices': 0, 'submissions': 0},
            'criteria': 'Same source convergence/gradient/scalar/JSONreplay controls. No predictive adoption without separately preregistered complete primary comparison versus A1S/S2/H1and secondary versus plainP12GLM. All original gates/stresses remain.',
            'preflight': fixture, 'sources': sources,
            'limits': previous['limits']+['Source missingness may have a different mechanism from target; flags do not restore lost values or establish transportability.',
                                         'Standardized indicator penalty is fixed alpha1, not selected by score.',
                                         'No P13oracle levels or per-line selection are used.'],
            '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P14antes de ajustar: GLM4_MIañade solo indicadores numéricos de ausencia a P11, centrados/escalados por fuente. '
                    'Se añaden todas las ausencias numéricas no constantes en fuente, sin elegir variables por resultados. '
                    'P13comprobó el mayor porcentaje de ausentes y una limitación de representación; no demostró que cause el adverso. '
                    'Se conservan datos2021–2024,T0,e_cost, medianas, recortes, categorías y penalización1. Sin máscaras, interacciones, splines o búsqueda. '
                    'Presupuesto3GLMfuente, ceroC0/calibraciones/scoredestino/inferencias2025/precios/envíos. '
                    'El fixture nuevo ejerció ajuste,predictor,gradiente,JSONyorden; también probó que el par ausente/mediana colisiona antes y se distingue con el indicador. '
                    'El productor P11se reutiliza mediante enlaces locales de funciones, sin modificar sus archivos; los recibos nuevos identificarán ambos códigos. '
                    'La validación completa posterior tendrá como primario A1S/S2/H1y secundario GLM4/S2/H1, con criterios intactos. '
                    'No se usan niveles oráculo, celdas positivas o público para rescatar. B00/F3c/P6y adversos intactos,2024abierto adaptativo. '
                    'Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P14-AUSENTES-PREVIO', '--asunto',
                             'P14 previo: indicadores estándar de ausencia, tres GLM fuente y capacidad fija', '--cuerpo', str(body)],
                            check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P14registered_before_sourcefits', 'plan': w.rel(PLAN),
               'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'planned_fits': 3, 'new_contest_fits': 0, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'context_report.json').exists()
    if not (OUT/'report.json').exists(): old.run()
    # If the engine finished before a context write failed, no source model is refitted.
    raw = w.read(OUT/'report.json'); plan = w.read(PLAN)
    assert raw['plan_sha256'] == w.sha(PLAN) and raw['new_source_GLM_fits'] == 3
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    indicators = {}; parameters = {}
    for line in old.LINES:
        model = w.read(OUT/line/'model.json')
        indicators[line] = list(model['preprocessor']['numeric_missing_indicators'])
        assert len(model['coef']) == len(model['feature_names'])
        assert all(name+'__is_missing' in model['feature_names'] for name in indicators[line])
        parameters[line] = len(model['coef'])+1
    context = {'author': 'Codex', 'utc': utc(), 'status': 'P14source_missing_indicators_complete_target_validation_pending',
               'candidate': 'GLM4_MI', 'engine_report': w.rel(OUT/'report.json'), 'engine_report_sha256': w.sha(OUT/'report.json'),
               'indicators': indicators, 'parameters': parameters, 'source_models_per_line': 1,
               'new_source_GLM_fits': 3, 'new_C0_fits': 0, 'new_target_calibrations': 0, 'new_target_scores': 0,
               'new_future2025inference': 0, 'new_finaltestprices': 0, 'new_submissions': 0,
               'predictive_adoption': False, 'private_improvement_established': False, '2024_open': True,
               'B00_all_alternatives_preserved': True, 'plan_sha256': w.sha(PLAN), 'limits': plan['limits']}
    dump(OUT/'context_report.json', context)
    print(json.dumps({'status': context['status'], 'indicators': indicators, 'parameters': parameters}))


def replay():
    old.replay()
    dump(OUT/'P14_replay_context.json', {'author': 'Codex', 'utc': utc(), 'candidate': 'GLM4_MI',
                                       'new_preprocessing_bindings_applied': True,
                                       'source_models_per_line': 1, 'engine_receipt': w.rel(OUT/'replay_report.json'),
                                       'engine_receipt_sha256': w.sha(OUT/'replay_report.json'),
                                       'context_report_sha256': w.sha(OUT/'context_report.json'),
                                       'new_fits': 0, 'new_test_inference': 0})


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with old.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
