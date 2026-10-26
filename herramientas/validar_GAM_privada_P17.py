"""Contraste completo del GAM fuente, con criterios y comparadores fijados."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
SOURCE = BASE/'P16_GAM_bedrooms_lineal_20261026'
PREVIOUS = BASE/'P15_validacion_ausentes_20261026'
OUT = BASE/'P17_validacion_GAM_20261026'
PLAN = R/'registro/semana2_GAM_validacion_privada_plan.json'
INDEX = R/'registro/semana2_GAM_validacion_privada_actual.json'
sp = importlib.util.spec_from_file_location('p17_paired_complete_helpers', R/'herramientas/validar_GLM_ausentes_P15.py')
paired = importlib.util.module_from_spec(sp); sp.loader.exec_module(paired)
driver = paired.old; engine = paired.engine; w = paired.w; np = paired.np; pd = paired.pd
paired.OUT = OUT; paired.SOURCE = SOURCE; paired.PREVIOUS = PREVIOUS; paired.PLAN = PLAN; paired.INDEX = INDEX
driver.OUT = OUT; driver.SOURCE = SOURCE; driver.PLAN = PLAN; driver.INDEX = INDEX
engine.OUT = OUT; engine.P9 = SOURCE; engine.PLAN = PLAN; engine.INDEX = INDEX


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert not w.read(engine.state.PHASE).get('active_execution') and not w.read(engine.state.PHASE).get('active_jobs')
    source_report = w.read(SOURCE/'report.json'); replay = w.read(SOURCE/'amendment_replay_context.json')
    assert source_report['combined_source_GAMfits'] == 3 and replay['new_fits'] == 0
    assert w.sha(ROOT/replay['engine_receipt']) == replay['engine_receipt_sha256']
    OUT.mkdir()
    previous_path = R/'registro/semana2_GLM_ausentes_validacion_plan.json'; previous = w.read(previous_path)
    assert all(w.sha(ROOT/p) == z for p, z in previous['sources'].items())
    source_plan_path = R/'registro/semana2_GAM_bedrooms_lineal_plan.json'; source_plan = w.read(source_plan_path)
    assert source_report['plan_sha256'] == w.sha(source_plan_path)
    assert all(w.sha(ROOT/p) == z for p, z in source_plan['sources'].items())
    sources = {p: z for p, z in previous['sources'].items() if 'P14_GLM_ausentes_20261026/historical_' not in p}
    extra = [Path(__file__), Path(paired.__file__), source_plan_path, SOURCE/'report.json',
             SOURCE/'replay_report.json', SOURCE/'amendment_replay_context.json', PREVIOUS/'report.json',
             R/'herramientas/GAM_fuente_privada_P16.py', R/'herramientas/GAM_continuar_bedrooms_P16.py']
    for cohort in ['POOLED', 'TRANSFER']:
        extra += [PREVIOUS/(cohort+'_prices.parquet'), PREVIOUS/(cohort+'_joint_bootstrap.npy')]
    scopes = []
    for line in engine.h.LINES:
        path = SOURCE/f'historical_{line}_three_seed.parquet'; extra.append(path)
        extra += [SOURCE/line/'model.json', SOURCE/line/'fit_record.json', SOURCE/line/'application.json']
        relative = pd.read_parquet(path)
        assert relative.row_id.is_unique and not relative.is_test.any() and relative.year.isin([2023, 2024]).all()
        assert np.isfinite(relative.log_relative_A1S).all() and (np.exp(relative.log_relative_A1S) > 0).all()
        for scope in [a for a in previous['scopes'] if a['line'] == line]:
            f, held, _ = engine.get_scope(scope['cohort'], line, scope['outer'], relative)
            train = f.fold.ne(held)
            assert engine.b.digest(sorted(f.loc[train, 'row_id'])) == scope['training_row_digest']
            assert engine.b.digest(sorted(set(f.loc[train, 'group_id']))) == scope['training_groups_digest']
            scopes.append(scope)
    assert len(scopes) == 30
    sources.update({w.rel(p): w.sha(p) for p in extra})
    plan = {k: v for k, v in previous.items() if k not in ['author', 'utc', 'candidate', 'hypothesis', 'change', 'preflight', 'scopes', 'sources', 'limits']}
    plan.update(author='Codex', utc=utc(), candidate='GAM4_MI_bedrooms_linear_complete_S2_H1',
                hypothesis='Fixed source additive main effects can address current linear-GLMallocation limitations while retaining missingness representation; test against incumbent without selecting a line or changing levels.',
                change='Only source annual relativities change to the3saved GAMs, with5/4/3fixed curves, bedrooms linear and alpha1; same target S2/H1algorithm.',
                primary_comparator='Original A1S/S2/five-member-H1 versus GAM4_MI_bedrooms_linear/S2/five-member-H1 on identical held groups.',
                secondary_comparator='P15linear-GLM-with-missing-indicators/S2/H1 versus current GAM/S2/H1; improved secondary alone cannot admit candidate.',
                source_models_per_line=1, source_curves=source_report['curves'],
                source_amendment='Bedrooms linear due tied source quantiles; two saved models reused and contents fitted once. No target-score choice.',
                budget={'new_source_fits': 0, 'new_C0_fits': 0, 'primary_closed_learner_calls': 30,
                        'adverse_closed_learner_calls_separate': 30, 'new_future2025inference': 0,
                        'new_finaltestprices': 0, 'new_submissions': 0},
                preflight={'all30new_source_scope_bindings_exact': True, 'new_synthetic_fits': 0,
                           'unchanged_complete_engine_fixtures_reused': True,
                           'new_source_GAM_and_amended_contents_full_JSONreplay_verified': True},
                paired_secondary_bootstrap='New primary draws minus stored P15primary draws; same connected groups, outcomes, row order, seeds and null denominators. No second resampling.',
                scopes=scopes, sources=sources,
                limits=previous['limits']+['Current additive curves may underfit interactions or overfit developed patterns; this is not a causal test of nonlinearity.',
                                            'Source GAMengine raw report may retain P12GLMidentity; this context and source plans identify the current family exactly.',
                                            'The source amendment used source quantile feasibility, not validation gains; original failure is preserved.'])
    assert plan['bootstrap'] == previous['bootstrap']
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P17antes de ajustar o puntuar el GAMcompleto: primario frente a A1S/S2/H1original y secundario frente al GLMconindicadores P15. '
                    'Se congelan los3modelos fuente, curvas5/4/3, dormitorios lineales e indicadores. No se retoma el intento fallido ni se reajusta fuente. '
                    'Mismos grupos, C0/N3, exposición, mezcla50/50y cinco cocientes H1/G3. Presupuesto30calibraciones cerradas más30controles adversos, ceroC0/modelos fuente/inferencias2025/precios finales/envíos. '
                    'Criterios intactos: mínimo0,002, intervalos por grupos, cuatrofolds, ambos años, Post31,piso−0,001y cuatro escenarios. '
                    'La transferencia de destino2023a2024es condicional porque fuente y marcas incluyen2024; no se presenta como backtest prospectivo completo. '
                    'Los intervalos secundarios usarán diferencias de draws emparejados de P15, sin otro remuestreo ni selección de semillas. '
                    'Las30claves/ámbitos nuevos se conciliaron y el replayJSONde fuente ya está verificado; no se repite el fixture numérico sin cambios. '
                    'No se emplean niveles oráculo, celdas positivas o público para modificar la receta. B00/F3c/P6y adversos preservados,2024abierto adaptativo. '
                    'Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P17-GAM-PREVIO', '--asunto',
                             'P17 previo: GAM completo contra referencia y GLM con indicadores, mismos criterios',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P17registered_before_target_learning',
               'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'scopes': 30, 'new_source_fits': 0, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'context_report.json').exists()
    if not (OUT/'report.json').exists(): driver.run()
    raw = w.read(OUT/'report.json'); assert raw['plan_sha256'] == w.sha(PLAN)
    secondary = paired.secondary_results(raw)
    assert all(w.sha(ROOT/p) == z for p, z in w.read(PLAN)['sources'].items())
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P17complete_additive_source_algorithm_evaluated',
              'candidate': 'GAM4_MI_bedrooms_linear_complete_S2_H1',
              'engine_report': w.rel(OUT/'report.json'), 'engine_report_sha256': w.sha(OUT/'report.json'),
              'primary_diagnostic_gates': raw['diagnostic_gates'],
              'primary_nominal': {c: raw['results'][c]['NOMINAL'] for c in ['POOLED', 'TRANSFER']},
              'secondary_vs_linear_MI': secondary, 'new_primary_closed_learners': 30,
              'new_adverse_closed_learners_separate': 30, 'new_source_fits': 0, 'new_C0_fits': 0,
              'new_secondary_resampling': 0, 'new_future2025inference': 0, 'new_finaltestprices': 0,
              'new_submissions': 0, 'formal_promotion': False, 'submission_allowed': False,
              'private_improvement_established': False, '2024_open': True,
              'B00_all_alternatives_preserved': True, 'goal_achieved': False, 'plan_sha256': w.sha(PLAN)}
    dump(OUT/'context_report.json', report)
    print(json.dumps({'status': report['status'], 'primary_gates': report['primary_diagnostic_gates'],
                      'secondary_nominal': {c: {k: d['NOMINAL'][k] for k in ['delta', 'bootstrap95_paired_existing_draws', 'post31_delta', 'worst_cell_delta']}
                                            for c, d in secondary.items()}}))


def replay():
    engine.replay()
    context = w.read(OUT/'context_report.json')
    for cohort in ['POOLED', 'TRANSFER']:
        expected = np.load(OUT/(cohort+'_joint_bootstrap.npy'))-np.load(PREVIOUS/(cohort+'_joint_bootstrap.npy'))
        saved = np.load(OUT/(cohort+'_secondary_paired_draws.npy')); assert np.array_equal(saved, expected)
        for j, name in enumerate(engine.NAMES):
            assert np.array_equal(np.quantile(saved[:, j], [.025, .975]),
                                  context['secondary_vs_linear_MI'][cohort][name]['bootstrap95_paired_existing_draws'])
    dump(OUT/'P17_replay_context.json', {'author': 'Codex', 'utc': utc(), 'candidate': 'GAM4_MI_bedrooms_linear_complete_S2_H1',
                                       'engine_receipt': w.rel(OUT/'replay_report.json'),
                                       'engine_receipt_sha256': w.sha(OUT/'replay_report.json'),
                                       'context_report_sha256': w.sha(OUT/'context_report.json'),
                                       'paired_secondary_intervals_exact': True, 'new_resampling': 0,
                                       'new_fits': 0, 'new_source_queries': 0})
    print(json.dumps({'replay': 'passed', 'paired_intervals': 'exact', 'new_resampling': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with engine.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
