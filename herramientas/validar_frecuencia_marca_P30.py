"""Evalúa la fuente GLM por peril dentro del algoritmo completo congelado."""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
spec = importlib.util.spec_from_file_location('p30_strict_adapter_and_engine', R/'herramientas/validar_ausencias_privada_P26.py')
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
e = prior.e; previous = prior.previous; w = prior.w; np = prior.np; pd = prior.pd
BASE = prior.BASE; SOURCE = BASE/'P29_fuente_frecuencia_completa_20261026'
OUT = BASE/'P30_validacion_frecuencia_marca_20261026'
PLAN = R/'registro/semana2_frecuencia_marca_validacion_privada_plan.json'
INDEX = R/'registro/semana2_frecuencia_marca_validacion_privada_actual.json'
e.OUT = OUT; e.P9 = SOURCE; e.PLAN = PLAN; e.INDEX = INDEX
previous.OUT = OUT; previous.PLAN = PLAN; previous.INDEX = INDEX; previous.COV = None


def utc(): return datetime.now(timezone.utc).isoformat()


def execution_state(execution):
    if execution is not None:
        execution = {**execution, 'script': w.rel(Path(__file__)), 'kind': 'P30complete_peril_GLM_source_validation', 'raw_driver': w.rel(Path(e.__file__))}
    prior.ORIGINAL_STATE(execution)


e.state.state_execution = execution_state


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(e.state.PHASE).get('active_jobs')
    source = w.read(SOURCE/'report.json'); closed = w.read(SOURCE/'completion_receipt.json')
    assert source['new_source_GLM_fits'] == 30 and source['new_target_scores'] == 0
    assert closed['report_sha256'] == w.sha(SOURCE/'report.json')
    assert all(w.sha(ROOT/p) == z for p, z in source['outputs'].items())
    assert all(w.sha(ROOT/p) == z for p, z in closed['model_hashes'].items())
    OUT.mkdir(); template = w.read(R/'registro/semana2_ausencias_validacion_privada_plan.json')
    common = w.read(R/'registro/semana2_canal_privada_plan.json')
    sources = {p: z for p, z in common['sources'].items() if 'P23_canal_principal_20261026/' not in p}
    assert all(w.sha(ROOT/p) == z for p, z in sources.items())
    paths = [Path(__file__), Path(prior.__file__), Path(previous.__file__),
        SOURCE/'report.json', SOURCE/'completion_receipt.json',
        R/'registro/semana2_fuente_frecuencia_completa_privada_plan.json',
        R/'herramientas/completar_fuente_frecuencia_P29.py',
        BASE/'P28_fuente_frecuencia_marca_20261026/numerical_replay.json',
        BASE/'P26_validacion_ausencias_20261026/synthetic_adapter.json',
        BASE/'P26_validacion_ausencias_20261026/P26_replay_context.json']
    cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet', filters=[('year', 'in', [2023, 2024])])
    assert not cov.is_test.any() and cov.row_id.is_unique
    cov.to_parquet(OUT/'covariates.parquet', index=False); paths.append(OUT/'covariates.parquet')
    scopes = []
    for line in e.h.LINES:
        path = SOURCE/f'historical_{line}_three_seed.parquet'; relative = pd.read_parquet(path)
        prior.strict_relative(relative); paths += [path, SOURCE/line/'preprocessor.json', SOURCE/line/'application.json']
        canonical = pd.read_parquet(e.P1/f'canonical_{line}.parquet', columns=['row_id', 'year'])
        assert set(relative.row_id) == set(canonical.row_id); prior.attach_relative(canonical, relative)
        for scope in [x for x in template['scopes'] if x['line'] == line]:
            frame, held, _ = e.get_scope(scope['cohort'], line, scope['outer'], relative)
            train = frame.fold.ne(held)
            assert e.b.digest(sorted(frame.loc[train, 'row_id'])) == scope['training_row_digest']
            assert e.b.digest(sorted(set(frame.loc[train, 'group_id']))) == scope['training_groups_digest']
            scopes.append(scope)
    assert len(scopes) == 30; sources.update({w.rel(p): w.sha(p) for p in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Peril_GLM_paired_reporting_source_original_50_50_S2_H1',
        'hypothesis': 'A sum of standard count/mark GLMs under paired source observation links may transfer better than aggregate source trees, but source gain does not establish whole-algorithm private robustness.',
        'change': 'Only saved P29source annual cost relativities change. Relearn source-dependent target shape/levels and the same residual stages. Original50/50N3mix and5H1/G3mean, C0and qSource unchanged.',
        'source_identity': '15fixed Poisson/Tweedie1.5pairs, one deterministic sum perline. Historical three_seed name is compatibility, no3seed ensemble or selection.',
        'primary_comparator': template['primary_comparator'], 'configuration': template['configuration'],
        'changed_learning': template['changed_learning'], 'budget': template['budget'],
        'exposure': template['exposure'], 'sensitivity': template['sensitivity'],
        'criteria': template['criteria'], 'bootstrap': template['bootstrap'],
        'level_sensitivity': template['level_sensitivity'], 'cohort_guard': template['cohort_guard'],
        'preflight': {'all30new_source_scope_bindings_exact': True,
            'unchanged_strict_source_adapter_fixture_reused': w.rel(BASE/'P26_validacion_ausencias_20261026/synthetic_adapter.json'),
            'unchanged_complete_learning_forward_replays_reused': w.rel(BASE/'P26_validacion_ausencias_20261026/P26_replay_context.json'),
            'new_source_full_JSONand_annual_composition_verified': True, 'new_synthetic_fits': 0,
            'reason': 'Only fixed source numbers change; same strict keys/years and identical learning/forward code verified by hashes. No repeat unchanged fixtures.'},
        'scopes': scopes, 'sources': sources,
        'limits': common['limits']+[
            'Source gate compared same-contract peril constants, not target or public results; historical A1Strees were contextual.',
            'Source-observation ancestors include source-held groups; source claims/factors conditional, not identified ultimate-event frequency.',
            'Target still uses fixed aggregate C0observation mixture and oldH1ratios; this isolates source allocation, not a new target per-peril observation/adaptation model.',
            'Adaptive2023/2024 and insufficient future-weight support remain; no private certification or exact whole F3creconstruction.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    prior.dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text(
        'Codex. Registro P30 antes de aprender o puntuar destino: sustituir solo '
        'relatividades fuente por la suma fija de GLM número/marca P29, conservar '
        'mezcla50/50, residuales originales, N3/C0, media H1/G3y qSource. No es un '
        'nuevo modelo C0por peril en destino.30calibraciones S2primarias y30controles '
        'adversos; cero nuevos modelos fuente/C0, inferencias2025, precios o envíos. '
        'Criterios globales/NB/broker/historia cero y familia16idénticos a P26, sin '
        'reducir mínimos o buscar perils/pesos favorables. Los30ámbitos y años '
        'coinciden; se reutilizan fixture del adaptador y replays completos sin '
        'cambios, con SHA. P29consumió sus JSONy verificó composición anual/centro. '
        'El veto fuente fue frente a constantes por peril y no acredita mejora '
        'privada. Una suma fija por ramo, no tres semillas pese al nombre de caché. '
        'B00/F3cy adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P30-FRECUENCIA-PREVIO',
        '--asunto', 'P30: contraste completo del GLM fuente por peril con las mismas guardas privadas',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P30registered_before_target_learning',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)}
    prior.dump(OUT/'registration.json', receipt); prior.dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'scopes': 30, 'forum': receipt['forum']}))


def run():
    assert not w.read(e.state.PHASE).get('active_jobs')
    prior.dump(OUT/'P30_execution_context.json', {'author': 'Codex', 'utc': utc(),
        'script': w.rel(Path(__file__)), 'script_sha256': w.sha(Path(__file__)), 'source': w.rel(SOURCE),
        'raw_driver': w.rel(Path(e.__file__)), 'source_is_one_peril_sum_not_three_seeds': True})
    e.run(); raw = w.read(OUT/'report.json'); cohort = previous.cohort_analysis()
    context = {'author': 'Codex', 'utc': utc(), 'candidate': 'Peril_GLM_paired_reporting_source_original_50_50_S2_H1',
        'status': 'P30complete_peril_GLM_source_algorithm_evaluated',
        'raw_engine_report': w.rel(OUT/'report.json'), 'raw_engine_report_sha256': w.sha(OUT/'report.json'),
        'global_gates': raw['diagnostic_gates'], 'new_business_gates': cohort['gates'],
        'all_exploratory_gates_pass': all(raw['diagnostic_gates'].values()) and all(cohort['gates'].values()),
        'new_primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
        'new_source_component_calibrations': 30, 'new_residual_stages': 40,
        'new_source_fits': 0, 'new_C0_fits': 0, 'new_future_inference': 0,
        'new_final_prices': 0, 'new_submissions': 0, 'formal_promotion': False,
        'private_improvement_established': False, 'goal_achieved': False,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    prior.dump(OUT/'P30_context_report.json', context)
    print(json.dumps({'candidate': 'P30', 'global_gates': raw['diagnostic_gates'], 'new_business_gates': cohort['gates']}))


def replay():
    e.replay(); report = w.read(OUT/'cohort_report.json'); saved = np.load(OUT/'cohort_bootstrap.npy')
    assert w.sha(OUT/'cohort_bootstrap.npy') == report['cohort_draws_sha256']
    totals, descriptors, _, _ = previous.cohort_blocks()
    weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    assert np.allclose(previous.score_cohort_sums(weights@totals), saved[:4], rtol=2e-12, atol=2e-13)
    for j, result in enumerate(report['comparisons']):
        assert descriptors[j]['delta'] == result['delta']
        assert np.array_equal(np.quantile(saved[:, j], [.025, .975]), result['marginal95'])
        assert np.array_equal(np.quantile(saved[:, j], [.025/16, 1-.025/16]), result['family16_band95'])
    prior.dump(OUT/'P30_replay_context.json', {'author': 'Codex', 'utc': utc(),
        'raw_engine_replay': w.rel(OUT/'replay_report.json'), 'raw_engine_replay_sha256': w.sha(OUT/'replay_report.json'),
        'cohort_points_saved_weights_and_intervals_verified': True, 'new_resampling': 0,
        'new_fits': 0, 'new_source_queries': 0, 'context_report_sha256': w.sha(OUT/'P30_context_report.json')})
    print(json.dumps({'P30replay': 'exact', 'new_fits': 0, 'new_resampling': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'replay']); args = parser.parse_args()
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[args.mode]()
