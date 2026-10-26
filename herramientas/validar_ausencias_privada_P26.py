"""Contrasta P25 dentro de la mezcla S2/H1 completa, sin nueva búsqueda fuente."""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
SOURCE = BASE/'P25_fuente_ausencias_20261026'
OUT = BASE/'P26_validacion_ausencias_20261026'
PLAN = R/'registro/semana2_ausencias_validacion_privada_plan.json'
INDEX = R/'registro/semana2_ausencias_validacion_privada_actual.json'
spec = importlib.util.spec_from_file_location('p26_cohort_evidence', R/'herramientas/validar_canal_privada_P23.py')
previous = importlib.util.module_from_spec(spec); spec.loader.exec_module(previous)
e = previous.e; w = e.w; np = e.np; pd = e.pd
ORIGINAL_GET = previous.ORIGINAL_GET
e.core.learn = previous.ORIGINAL_LEARN
e.OUT = OUT; e.P9 = SOURCE; e.PLAN = PLAN; e.INDEX = INDEX
previous.OUT = OUT; previous.PLAN = PLAN; previous.INDEX = INDEX; previous.COV = None


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def strict_relative(relative):
    required = {'row_id', 'year', 'is_test', 'log_relative_A1S'}
    assert required.issubset(relative) and set(relative).issubset(required|{'raw_log_rate'})
    assert len(relative) and relative.row_id.notna().all() and relative.row_id.is_unique
    assert relative.is_test.eq(False).all() and relative.year.isin([2023, 2024]).all()
    logs = relative.log_relative_A1S.to_numpy(float)
    assert np.isfinite(logs).all() and (np.exp(logs) > 0).all() and np.isfinite(np.exp(logs)).all()
    if 'raw_log_rate' in relative: assert np.isfinite(relative.raw_log_rate).all()
    return relative


def attach_relative(frame, relative):
    strict_relative(relative)
    assert frame.row_id.notna().all() and frame.row_id.is_unique
    keyed = relative.set_index('row_id').loc[frame.row_id]
    assert np.array_equal(frame.year, keyed.year)
    result = frame.copy(); result['log_relative_A1S'] = keyed.log_relative_A1S.to_numpy()
    return result


def get_scope(cohort, line, outer, relative):
    strict_relative(relative)
    frame, held, n3 = ORIGINAL_GET(cohort, line, outer, relative)
    checked = attach_relative(frame, relative)
    assert np.array_equal(checked.log_relative_A1S, frame.log_relative_A1S)
    return checked, held, n3


def constants(artifact):
    comp = artifact['component']
    return {'shape_factors': comp['shape_factor_constants'], 'level_constants': comp['level_constants'],
        'residual_factors': sum(len(x['factors']) for x in artifact['stages']),
        'training_nuisance_levels': sum(len(x['nuisance_year_business']) for x in artifact['stages']),
        'new_source_component_calls': 1, 'new_residual_stage_calls': len(artifact['stages']),
        'shape_training_normalizers_separate': comp['shape_training_normalizers'],
        'training_stage_normalizers_separate': sum(len(x) for x in artifact['training_normalizers'].values()),
        'held_stage_normalizers_separate': sum(len(x) for x in artifact['held_normalizers'].values())}


e.get_scope = get_scope; e.constants = constants
ORIGINAL_STATE = e.state.state_execution


def execution_state(execution):
    if execution is not None:
        execution = {**execution, 'script': w.rel(Path(__file__)),
            'kind': 'P26complete_source_missingness_validation', 'raw_driver': w.rel(Path(e.__file__))}
    ORIGINAL_STATE(execution)


e.state.state_execution = execution_state


def synthetic_adapter():
    relative = pd.DataFrame({'row_id': ['fixture'+str(i) for i in range(40)],
        'year': [2023+i%2 for i in range(40)], 'is_test': False,
        'log_relative_A1S': np.arange(40)/50.-.4})
    frame = relative[['row_id', 'year']].iloc[::-1].copy()
    frame['T0'] = np.arange(40)*7.; frame['reserve'] = 2.; frame['protected_exposure'] = .8
    expected = attach_relative(frame, relative)
    reversed_result = attach_relative(frame, relative.iloc[::-1])
    pd.testing.assert_frame_equal(expected, reversed_result, check_exact=True)
    pd.testing.assert_frame_equal(expected.drop(columns='log_relative_A1S'), frame, check_exact=True)
    poisoned = frame.copy(); poisoned[['T0', 'reserve']] = -1e30
    assert np.array_equal(attach_relative(poisoned, relative).log_relative_A1S, expected.log_relative_A1S)
    bad_cases = []
    bad_cases.append(('duplicate', pd.concat([relative, relative.iloc[:1]]), frame))
    bad = relative.copy(); bad.loc[0, 'is_test'] = True; bad_cases.append(('future_flag', bad, frame))
    bad = relative.copy(); bad.loc[0, 'year'] = 2025; bad_cases.append(('future_year', bad, frame))
    bad = relative.copy(); bad.loc[0, 'log_relative_A1S'] = np.inf; bad_cases.append(('infinite', bad, frame))
    bad = relative.copy(); bad['T0'] = 0.; bad_cases.append(('label_in_source_schema', bad, frame))
    bad = relative.copy(); bad.loc[0, 'year'] = 2024; bad_cases.append(('year_key_mismatch', bad, frame))
    bad_cases.append(('missing_key', relative.iloc[1:], frame))
    for name, bad, application in bad_cases:
        try: attach_relative(application, bad)
        except (AssertionError, KeyError): pass
        else: raise AssertionError('Adverse source contract accepted: '+name)
    return {'author': 'Codex', 'utc': utc(), 'actual_adapter_functions_exercised': True,
        'key_order_and_protected_payload_exact': True, 'adverse_cases_rejected': [x[0] for x in bad_cases],
        'new_synthetic_model_fits': 0, 'new_contest_fits': 0,
        'unchanged_full_learning_fixture_reused_not_rerun': True}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(e.state.PHASE).get('active_jobs') and not w.read(e.state.PHASE).get('active_execution')
    source = w.read(SOURCE/'report.json'); closed = w.read(SOURCE/'completion_receipt.json')
    assert source['source_veto_all_pass'] and closed['source_veto_all_pass']
    assert closed['report_sha256'] == w.sha(SOURCE/'report.json')
    assert closed['replay_sha256'] == w.sha(SOURCE/'scalar_replay.json')
    assert source['new_source_fits'] == 18 and source['new_target_scores'] == 0
    assert all(w.sha(ROOT/p) == z for p, z in source['outputs'].items())
    OUT.mkdir(); fixture = synthetic_adapter(); dump(OUT/'synthetic_adapter.json', fixture)
    template = w.read(R/'registro/semana2_canal_privada_plan.json')
    original = w.read(R/'registro/semana2_ablacion_fuente_validacion_plan.json')
    assert all(w.sha(ROOT/p) == z for p, z in template['sources'].items())
    assert all(w.sha(ROOT/p) == z for p, z in original['sources'].items())
    paths = [Path(__file__), Path(previous.__file__), Path(e.__file__),
        SOURCE/'report.json', SOURCE/'scalar_replay.json', SOURCE/'completion_receipt.json',
        R/'registro/semana2_fuente_ausencias_privada_plan.json',
        R/'herramientas/fuente_ausencias_P25.py', R/'herramientas/cerrar_fuente_ausencias_P25.py',
        BASE/'P10_validacion_sin_exposicion_20261026/synthetic.json',
        BASE/'P24_componente_unico_20261026/P24_replay_context.json', OUT/'synthetic_adapter.json']
    cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet', filters=[('year', 'in', [2023, 2024])])
    assert cov.row_id.is_unique and not cov.is_test.any()
    cov.to_parquet(OUT/'covariates.parquet', index=False); paths.append(OUT/'covariates.parquet')
    scopes = []
    for line in e.h.LINES:
        path = SOURCE/f'historical_{line}_three_seed.parquet'; relative = pd.read_parquet(path)
        strict_relative(relative); paths.append(path)
        canonical = pd.read_parquet(e.P1/f'canonical_{line}.parquet', columns=['row_id', 'year'])
        assert set(relative.row_id) == set(canonical.row_id)
        attach_relative(canonical, relative)
        for seed in [11, 12, 13]:
            paths += [SOURCE/f'{line}_seed{seed}_full/{name}' for name in ['fit_record.json', 'application.json', 'historical_components.parquet']]
        for scope in [x for x in template['scopes'] if x['line'] == line]:
            frame, held, _ = get_scope(scope['cohort'], line, scope['outer'], relative)
            train = frame.fold.ne(held)
            assert e.b.digest(sorted(frame.loc[train, 'row_id'])) == scope['training_row_digest']
            assert e.b.digest(sorted(set(frame.loc[train, 'group_id']))) == scope['training_groups_digest']
            assert not set(frame.loc[train, 'group_id']).intersection(frame.loc[~train, 'group_id'])
            scopes.append({k: v for k, v in scope.items() if k in original['scopes'][0]})
    assert len(scopes) == 30
    sources = {p: z for p, z in template['sources'].items() if 'P23_canal_principal_20261026/' not in p}
    sources.update({w.rel(p): w.sha(p) for p in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'P25_source_missingness_original_50_50_S2_H1',
        'human_priority': 'Private generalization first; public score secondary,2024open/adaptive. Stale app goal text does not override direct instructions.',
        'previous_goal_turn_classification': 'progress:18P25source fits, fixed veto passed, scalar replay and local forum closure/version receipts completed; no target admission claimed.',
        'hypothesis': 'Una menor dependencia de campos observados solo es útil si resiste el cambio de mercado en el algoritmo completo. El veto fuente admite pequeños deterioros y no garantiza este resultado.',
        'change': 'Solo relatividades fuente: ensemble geométrico de las mismas3semillas P25, sin elegir ramos. Se reaprenden forma/nivel del componente A1S y los mismos residuales S2. Mezcla50/50N3, C0, H1/G3 y enlace qSource congelados.',
        'primary_comparator': 'Original A1S/S2/five-member-H1 on identical stored held groups; not exact delivered F3c.',
        'source_recipe': 'P25fully frozen:10percent entity-consistent missingness on16numeric field/line pairs, original native tree parameters and original fixed source rounds. No new source fit, mask/seed/capacity/weight search.',
        'source_veto_adverses_retained': source['source_veto'],
        'configuration': {'source_weight': .5, 'N3_weight': .5, 'residual_stages': e.core.g.STAGES,
            'shape_and_residual_credibility_K': 300, 'new_business_level_credibility_K': 400,
            'H1mean': 'same5members arithmetic mean of frozen ultimate ratios',
            'normalization': 'Prediction-only complete application cohort by year/business, recomputed for changed predictions; no rowwise tariff claim'},
        'changed_learning': '30whole S2closed learners (15pooled+15conditionaltransfer), comprising30changed source component calibrations and40residual stage calls;30separate held-poison whole learners. N3/C0/H1reused, not refitted or recounted.',
        'budget': {'primary_closed_learner_calls': 30, 'adverse_closed_learner_calls_separate': 30,
            'new_source_fits': 0, 'new_C0_fits': 0, 'new_synthetic_fits': 0,
            'new_future2025inference': 0, 'new_final_prices': 0, 'new_submissions': 0},
        'exposure': original['exposure'], 'sensitivity': original['sensitivity'],
        'criteria': template['criteria'], 'bootstrap': template['bootstrap'],
        'level_sensitivity': template['level_sensitivity'], 'cohort_guard': template['cohort_guard'],
        'preflight': {'strict_source_adapter': w.rel(OUT/'synthetic_adapter.json'),
            'all30new_source_memberships_and_group_boundaries_exact': True,
            'unchanged_complete_learning_fixture': w.rel(BASE/'P10_validacion_sin_exposicion_20261026/synthetic.json'),
            'unchanged_parent_numerical_replays_reused': w.rel(BASE/'P24_componente_unico_20261026/P24_replay_context.json'),
            'reuse_reason': 'Same original50/50learning/forward code and frozen ancestor inputs by SHA; only new strict source-key binding changed. No repeat of unchanged fixture or original parent suite.'},
        'scopes': scopes, 'sources': sources,
        'limits': template['limits']+[
            'La fuente P25empeora ligeramente en las3vistas nativas; no se interpreta el margen de no inferioridad como mejora.',
            'Artificial missingness does not establish MCAR or availability at quote time; source2024and undated snapshots remain conditional.',
            'Reference is a reproducible own algorithm, not a faithful reconstruction of all missing F3c learning dependencies.',
            'Gobernanza IAA2.8and Documentación IAA3: own adaptive checks, configuration/provenance/limits documented, no independent professional approval.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text(
        'Codex. Registro P26 antes de aprender o puntuar destino. Solo cambia el componente '
        'fuente a P25, con sus tres semillas y todos los ramos, manteniendo la mezcla 50/50 '
        'con N3, las etapas residuales originales y la misma media H1/G3. El veto fuente '
        'pasó con deterioros pequeños en las tres vistas nativas, que se conservan; no '
        'prueba mejora privada. Sin búsqueda de máscaras, pesos, semillas o subconjuntos. '
        'Se aprenderán 30 calibraciones S2 completas en los grupos guardados, más 30 '
        'controles adversos separados; cambian forma/nivel fuente y sus residuales. Cero '
        'nuevos modelos fuente/C0, inferencias2025, precios finales o envíos. Se mantienen '
        'mínimo incremental0,002, IC por componentes, folds/años, Post31, pisos por celda '
        'y cuatro escenarios, más todas las guardas NB/broker/historia cero y familia16. '
        'El nuevo adaptador sintético rechazó claves duplicadas/ausentes, año incoherente, '
        'futuro, infinitos y etiquetas en su esquema; invariancia de orden/payload exacta. '
        'Los30ámbitos nuevos coinciden en filas y grupos. Fixture completo y replays de '
        'padres sin cambios se reutilizan con sus SHA, sin repetirlos.2024abierto '
        'adaptativo; fuente incluye2024, no backtest prospectivo completo. B00/F3c y '
        'todos los adversos conservados. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P26-AUSENCIAS-PREVIO',
        '--asunto', 'P26: contrastar ausencias en el algoritmo completo, con guardas privadas intactas',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    registration = {'author': 'Codex', 'utc': utc(), 'status': 'P26registered_before_target_learning',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)}
    dump(OUT/'registration.json', registration); dump(INDEX, registration)
    print(json.dumps({'registered': True, 'scopes': 30, 'new_source_fits': 0, 'forum': registration['forum']}))


def run():
    assert not w.read(e.state.PHASE).get('active_jobs')
    dump(OUT/'P26_execution_context.json', {'author': 'Codex', 'utc': utc(),
        'script': w.rel(Path(__file__)), 'script_sha256': w.sha(Path(__file__)),
        'source_frozen': w.rel(SOURCE), 'source_weight': .5, 'N3_weight': .5,
        'raw_driver': w.rel(Path(e.__file__)), 'new_source_fits': 0})
    e.run(); raw = w.read(OUT/'report.json'); cohort = previous.cohort_analysis()
    context = {'author': 'Codex', 'utc': utc(), 'candidate': 'P25_source_missingness_original_50_50_S2_H1',
        'status': 'P26complete_missingness_source_algorithm_evaluated',
        'raw_engine_report': w.rel(OUT/'report.json'), 'raw_engine_report_sha256': w.sha(OUT/'report.json'),
        'raw_driver_prefix_P10_retained_not_candidate_identity': True,
        'global_gates': raw['diagnostic_gates'], 'new_business_gates': cohort['gates'],
        'all_exploratory_gates_pass': all(raw['diagnostic_gates'].values()) and all(cohort['gates'].values()),
        'new_primary_closed_learners': 30, 'adverse_closed_learners_separate': 30,
        'new_source_component_calibrations': 30, 'new_residual_stages': 40,
        'new_source_fits': 0, 'new_C0_fits': 0, 'new_future_inference': 0,
        'new_final_prices': 0, 'new_submissions': 0, 'formal_promotion': False,
        'private_improvement_established': False, 'goal_achieved': False,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(OUT/'P26_context_report.json', context)
    print(json.dumps({'candidate': 'P26', 'global_gates': raw['diagnostic_gates'],
        'new_business_gates': cohort['gates'], 'cohort_points': previous.descriptors_for_output(cohort)}))


def replay():
    e.replay()
    report = w.read(OUT/'cohort_report.json'); saved = np.load(OUT/'cohort_bootstrap.npy')
    assert w.sha(OUT/'cohort_bootstrap.npy') == report['cohort_draws_sha256']
    totals, descriptors, _, _ = previous.cohort_blocks()
    weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    assert np.allclose(previous.score_cohort_sums(weights@totals), saved[:4], rtol=2e-12, atol=2e-13)
    for j, result in enumerate(report['comparisons']):
        assert descriptors[j]['delta'] == result['delta']
        assert np.array_equal(np.quantile(saved[:, j], [.025, .975]), result['marginal95'])
        assert np.array_equal(np.quantile(saved[:, j], [.025/16, 1-.025/16]), result['family16_band95'])
    dump(OUT/'P26_replay_context.json', {'author': 'Codex', 'utc': utc(),
        'raw_engine_replay': w.rel(OUT/'replay_report.json'), 'raw_engine_replay_sha256': w.sha(OUT/'replay_report.json'),
        'cohort_points_saved_weights_and_intervals_verified': True,
        'new_resampling': 0, 'new_fits': 0, 'new_source_queries': 0,
        'context_report_sha256': w.sha(OUT/'P26_context_report.json')})
    print(json.dumps({'P26replay': 'exact', 'new_fits': 0, 'new_resampling': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'replay']); args = parser.parse_args()
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[args.mode]()
