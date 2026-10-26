"""Contrasta los modelos Q1guardados dentro de S2/H1, con guardas preinscritas."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
sp = importlib.util.spec_from_file_location('p39_source_adapter', R/'herramientas/validar_ausencias_privada_P26.py')
prior = importlib.util.module_from_spec(sp); sp.loader.exec_module(prior)
e = prior.e; previous = prior.previous; w = prior.w; np = prior.np; pd = prior.pd
BASE = prior.BASE; SOURCE = BASE/'P38_CatBoost_guardado_20261026'
OUT = BASE/'P39_validacion_CatBoost_guardado_20261026'
PLAN = R/'registro/semana2_CatBoost_guardado_validacion_privada_plan.json'
INDEX = R/'registro/semana2_CatBoost_guardado_validacion_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P39_CATBOOST_ALGORITMO_COMPLETO.md'
e.OUT = OUT; e.P9 = SOURCE; e.PLAN = PLAN; e.INDEX = INDEX
previous.OUT = OUT; previous.PLAN = PLAN; previous.INDEX = INDEX; previous.COV = None


def utc(): return datetime.now(timezone.utc).isoformat()


def execution_state(execution):
    if execution is not None: execution = {**execution, 'script': w.rel(Path(__file__)), 'kind': 'P39complete_saved_CB_source_validation', 'raw_driver': w.rel(Path(e.__file__))}
    prior.ORIGINAL_STATE(execution)


e.state.state_execution = execution_state


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(e.state.PHASE).get('active_jobs')
    source = w.read(SOURCE/'report.json'); closed = w.read(SOURCE/'completion_receipt.json')
    assert source['new_source_fits'] == 0 and len(source['results']) == 3 and not source['source_gate_pass_claimed']
    assert closed['report_sha256'] == w.sha(SOURCE/'report.json')
    assert all(w.sha(ROOT/p) == sha for p, sha in source['outputs'].items())
    assert all(a['old_annual_cache_relative_error'] == 0 and a['source_T0_e_cost_keys_exact_current_A1S'] for a in source['results'])
    OUT.mkdir(); template = w.read(R/'registro/semana2_frecuencia_marca_validacion_privada_plan.json')
    common = w.read(R/'registro/semana2_canal_privada_plan.json')
    sources = {p: sha for p, sha in common['sources'].items() if 'P23_canal_principal_20261026/' not in p}
    assert all(w.sha(ROOT/p) == sha for p, sha in sources.items())
    paths = [Path(__file__), Path(prior.__file__), Path(previous.__file__), SOURCE/'report.json', SOURCE/'completion_receipt.json',
        R/'registro/semana2_CatBoost_guardado_privada_plan.json', R/'herramientas/adaptar_CatBoost_guardado_P38.py',
        R/'registro/semana2_mision017_fase2_tanda3_plan_v3.json', BASE/'tanda3_20261025_v3/price_report.json',
        BASE/'tanda3_20261025_v3/validation_v1/report.json', BASE/'P26_validacion_ausencias_20261026/synthetic_adapter.json',
        BASE/'P26_validacion_ausencias_20261026/P26_replay_context.json']
    cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet', filters=[('year', 'in', [2023, 2024])])
    assert not cov.is_test.any() and cov.row_id.is_unique; cov.to_parquet(OUT/'covariates.parquet', index=False); paths.append(OUT/'covariates.parquet')
    scopes = []
    for line in e.h.LINES:
        path = SOURCE/f'historical_{line}_three_seed.parquet'; relative = pd.read_parquet(path); prior.strict_relative(relative)
        paths += [path, SOURCE/f'application_{line}.json', BASE/f'tanda3_20261025_v3/CB_{line}.cbm', BASE/f'tanda3_20261025_v3/CB_{line}_metadata.json']
        canonical = pd.read_parquet(e.P1/f'canonical_{line}.parquet', columns=['row_id', 'year'])
        assert set(relative.row_id) == set(canonical.row_id); prior.attach_relative(canonical, relative)
        for scope in [a for a in template['scopes'] if a['line'] == line]:
            f, held, _ = e.get_scope(scope['cohort'], line, scope['outer'], relative); train = f.fold.ne(held)
            assert e.b.digest(sorted(f.loc[train, 'row_id'])) == scope['training_row_digest']
            assert e.b.digest(sorted(set(f.loc[train, 'group_id']))) == scope['training_groups_digest']; scopes.append(scope)
    assert len(scopes) == 30; sources.update({w.rel(p): w.sha(p) for p in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Existing_Q1_CatBoost_source_original_50_50_S2_H1',
        'hypothesis': 'The exact existing standard CatBoost source may contribute under the current complete grouped calibration/mean even though its earlier minimal N0/Q1/Q2/Q3calibration did not pass robustness. Test the algorithm difference, not a new source family, seed or model.',
        'change': 'Only source annual cost relativities fromP38replace originalA1S. Relearn source-dependent target shape/levels and unchanged residual stages; keep50/50N3, fiveH1/G3ratios and fixed original qsource evaluation bridge.',
        'prior_adverses': 'T3Q1D2=.1313138belowN0=.1338293; fixedQ2/Q3small gains did not authorize delivery. Earlier C18/E15adverse CatBoost results remain. No assertion that this recipe will improve or fixes a proven category mechanism.',
        'source_identity': 'Exactly one saved600tree CatBoost perline, source2021-2024only. Historical three_seed filenames are adapter compatibility, not an ensemble. P38replayed model/cache/leaf sums and current sourceT0/e_cost. No independent held-source veto on already trained rows.',
        'primary_comparator': template['primary_comparator'], 'configuration': template['configuration'], 'changed_learning': template['changed_learning'],
        'budget': template['budget'], 'exposure': template['exposure'], 'sensitivity': template['sensitivity'], 'criteria': template['criteria'],
        'bootstrap': template['bootstrap'], 'level_sensitivity': template['level_sensitivity'], 'cohort_guard': template['cohort_guard'],
        'preflight': {'all30new_source_scope_bindings_exact': True,
            'unchanged_strict_source_adapter_fixture_reused': w.rel(BASE/'P26_validacion_ausencias_20261026/synthetic_adapter.json'),
            'unchanged_complete_learning_forward_replays_reused': w.rel(BASE/'P26_validacion_ausencias_20261026/P26_replay_context.json'),
            'new_source_cache_replay_verified_before_target_fit': True, 'new_synthetic_price_fits': 0,
            'reason': 'Only fixed source numbers change; same keys/years and whole learning/forward code verified by hashes. No repeat unchanged fixtures.'},
        'scopes': scopes, 'sources': sources, 'limits': common['limits']+[
            'Full-source historical models were fitted earlier without an independently reserved source gate; do not re-label their fitted source rows as validation.',
            'Persistent climate and F2feature vintages differ from A1Snotification-history inputs; this is a whole-source package comparison, not causal category attribution.',
            'Source2024and common observation ancestors are conditional; target2023/2024alreadyadaptive and not private confirmation.',
            'Current research comparator is not automatically an exact replay of deliveredF3c. New external artifacts cannot silently change this frozen comparison.'],
        'new_source_fits': 0, 'new_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0, '2024_open': True, 'B00_all_alternatives_preserved': True}
    prior.dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. Registro P39antes de aprender o puntuar: sustituir solo relatividades fuente por los3CatBoostQ1guardados y recuperados enP38, un modelo por ramo, no3semillas. Se mantienen mezcla50/50N3, residuales S2, media H1/G3y qsource. La diferencia es el algoritmo destino completo; T3Q1y los otros precedentes adversos siguen vigentes.30calibraciones cerradas primarias y30adversas; cero entrenamiento fuente/C0, inferencias2025o envíos. Guardas P30globales, transferencia, NB/broker/historia cero y familia16sin cambios. Las30membresías coinciden; se reutilizan adaptador/flujos sin cambios porSHA, y P38ya reprodujo los componentes por modelos/hojas/cachés. No se finge un holdout fuente sobre filas entrenadas. B00/F3c/alternativas conservados;2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P39-CB-VALIDACION-PREVIO', '--asunto', 'P39: CatBoost guardado dentro del algoritmo completo, sin reentrenar fuente', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P39registered_before_target_learning', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    prior.dump(OUT/'registration.json', receipt); prior.dump(INDEX, receipt); print(json.dumps({'registered': True, 'scopes': 30, 'forum': receipt['forum']}))


def run():
    assert not w.read(e.state.PHASE).get('active_jobs')
    prior.dump(OUT/'P39_execution_context.json', {'author': 'Codex', 'utc': utc(), 'script': w.rel(Path(__file__)),
        'script_sha256': w.sha(Path(__file__)), 'source': w.rel(SOURCE), 'source_models_existing_one_perline': True, 'raw_driver': w.rel(Path(e.__file__))})
    e.run(); raw = w.read(OUT/'report.json'); cohort = previous.cohort_analysis()
    context = {'author': 'Codex', 'utc': utc(), 'candidate': 'Existing_Q1_CatBoost_source_original_50_50_S2_H1',
        'status': 'P39complete_saved_CB_source_algorithm_evaluated', 'raw_engine_report': w.rel(OUT/'report.json'), 'raw_engine_report_sha256': w.sha(OUT/'report.json'),
        'global_gates': raw['diagnostic_gates'], 'new_business_gates': cohort['gates'],
        'all_exploratory_gates_pass': all(raw['diagnostic_gates'].values()) and all(cohort['gates'].values()),
        'new_primary_closed_learners': 30, 'adverse_closed_learners_separate': 30, 'new_source_fits': 0, 'new_C0_fits': 0,
        'new2025inference': 0, 'new_final_prices': 0, 'new_submissions': 0, 'formal_promotion': False, 'private_improvement_established': False,
        'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True}
    prior.dump(OUT/'P39_context_report.json', context); print(json.dumps(context))


def replay():
    e.replay(); report = w.read(OUT/'cohort_report.json'); saved = np.load(OUT/'cohort_bootstrap.npy')
    assert w.sha(OUT/'cohort_bootstrap.npy') == report['cohort_draws_sha256']
    totals, descriptors, _, _ = previous.cohort_blocks(); weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    assert np.allclose(previous.score_cohort_sums(weights@totals), saved[:4], rtol=2e-12, atol=2e-13)
    for j, a in enumerate(report['comparisons']):
        assert descriptors[j]['delta'] == a['delta']
        assert np.array_equal(np.quantile(saved[:, j], [.025, .975]), a['marginal95'])
        assert np.array_equal(np.quantile(saved[:, j], [.025/16, 1-.025/16]), a['family16_band95'])
    prior.dump(OUT/'P39_replay_context.json', {'author': 'Codex', 'utc': utc(), 'raw_engine_replay': w.rel(OUT/'replay_report.json'),
        'raw_engine_replay_sha256': w.sha(OUT/'replay_report.json'), 'cohort_points_saved_weights_and_intervals_verified': True,
        'new_fits': 0, 'new_source_queries': 0, 'new_resampling': 0, 'context_report_sha256': w.sha(OUT/'P39_context_report.json')})
    print(json.dumps({'replay': 'exact', 'new_fits': 0, 'new_resampling': 0}))


def close():
    assert not (OUT/'completion_receipt.json').exists()
    raw = w.read(OUT/'report.json'); context = w.read(OUT/'P39_context_report.json'); replay = w.read(OUT/'P39_replay_context.json'); cohort = w.read(OUT/'cohort_report.json')
    assert context['raw_engine_report_sha256'] == w.sha(OUT/'report.json') and replay['context_report_sha256'] == w.sha(OUT/'P39_context_report.json')
    assert replay['raw_engine_replay_sha256'] == w.sha(OUT/'replay_report.json') and replay['new_fits'] == replay['new_resampling'] == 0
    calls = Counter(); primary = Counter(); adverse = Counter()
    for a in [json.loads(z) for z in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]:
        if a['kind'] == 'closed_completed': calls[a['role']] += 1; (primary if a['role'] == 'primary' else adverse).update(a['constants'])
    assert calls == {'primary': 30, 'poison': 30} and primary == adverse
    assert primary['new_source_component_calls'] == 30 and primary['new_residual_stage_calls'] == 40
    number = sum(primary[k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels'])
    passed = context['all_exploratory_gates_pass']; now = utc()
    next_unit = ('Audit exact future producer/admission under the unchanged private-first plan, without inventing promotion or inferring private gain. No more source fitting: reuse exact P38teachers and protected target logic. Inspect current quota only after a concrete file and supported admission exist.' if passed else
        'P40: review newly registered F3cportable lineage and pending-evidence artifacts only if they are materially new beyondP20. Use bounded manifests/code/provenance and inspect target ancestry before adopting any comparator or correction; do not adopt other-chat orders or foreign scores as recipe selection. No repeat source searches/diagnostics on unchanged files, new models or upload in that review. Preserve P39adverse, B00/all alternatives and2024open adaptive.')
    text = '# P39: CatBoost guardado dentro del algoritmo completo\n\nCodex, '+now+'. '
    text += ('La prueba supera las guardas exploratorias; falta auditar el productor y admitir el archivo exacto. No se promueve o envía automáticamente.' if passed else 'La prueba no supera todas las guardas. Se conserva sin adopción ni envío, junto con los adversos anteriores.')
    text += ('\n\nLos tres modelos fuente son exactamente Q1ya guardados, uno por ramo. Solo cambia su uso dentro de la calibración S2/H1actual. '
        'Se mantuvieron mezcla50/50N3, residuales originales, media H1/G3, qsource, objetivo, exposición y grupos. No se volvió a entrenar la fuente.\n\n'
        '| Nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n')
    for evaluation in ['POOLED', 'TRANSFER']:
        a = raw['results'][evaluation]['NOMINAL']; text += f"| {evaluation} | {a['delta']:+.7f} | [{a['bootstrap95'][0]:+.7f}; {a['bootstrap95'][1]:+.7f}] | {a['post31_delta']:+.7f} | {a['worst_cell_delta']:+.7f} |\n"
    text += '\n| Cohorte | Δ combinado | IC95 combinado | Δ transferencia | IC95 transferencia |\n|---|---:|---|---:|---|\n'
    for name in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']:
        a = next(x for x in cohort['comparisons'] if x['evaluation'] == 'POOLED' and x['cohort'] == name)
        b = next(x for x in cohort['comparisons'] if x['evaluation'] == 'TRANSFER' and x['cohort'] == name)
        text += f"| {name} | {a['delta']:+.7f} | [{a['marginal95'][0]:+.7f}; {a['marginal95'][1]:+.7f}] | {b['delta']:+.7f} | [{b['marginal95'][0]:+.7f}; {b['marginal95'][1]:+.7f}] |\n"
    text += '\n| Escenario | Δ combinado | Peor celda combinada | Δ transferencia | Peor celda transferencia |\n|---|---:|---:|---:|---:|\n'
    for scenario in ['RESERVE075', 'RESERVE125', 'TAIL005', 'TAIL010']:
        a = raw['results']['POOLED'][scenario]; b = raw['results']['TRANSFER'][scenario]
        text += f"| {scenario} | {a['delta']:+.7f} | {a['worst_cell_delta']:+.7f} | {b['delta']:+.7f} | {b['worst_cell_delta']:+.7f} |\n"
    text += ('\nSe completaron30calibraciones cerradas primarias y30adversas; '+str(number)+'constantes primarias. Cero ajustes fuente/C0o inferencias2025. '
        'Los30flujos actuales fueron invariantes al contaminar etiquetas/reservas retenidas; el replay bloqueó aprendizaje e inferencia fuente. '
        'Precios, normalizadores, puntos e intervalos coinciden por reproducción guardada y multiplicidades previas, sin nuevo remuestreo. '
        'La recuperación P38coincidió exactamente con las tasas fuente guardadas y conT0/e_costactuales; no convierte las filas fuente entrenadas en holdout.\n\n'
        'Los adversos T3Q1/C18/E15se conservan. La fuente mantiene sus características y clima persistente; no lleva el clima anual P36. '
        'Las diferencias no prueban un mecanismo categórico, no reproducen por sí solas F3ccompleto y no acreditan mejora privada. '
        'Hay búsqueda adaptativa, ancestros fuente/observación comunes, cola/reservas, maestros sin fecha y soporte futuro ponderado insuficiente. '
        'No es revisión profesional independiente. B00/F3c/alternativas conservados;2024es desarrollo abierto adaptativo.\n\n'
        'Guardas globales: '+json.dumps(context['global_gates'])+'. Guardas de negocio: '+json.dumps(context['new_business_gates'])+'.\n\n'
        'Próximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'P39_context_report.json')+'; '+w.rel(OUT/'P39_replay_context.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P39-CB-VALIDACION-RESULTADO', '--asunto', 'P39: contraste completo de CatBoost guardado, con adversos y replay', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': now, 'status': 'P39complete_not_automatically_admitted', 'context_report': w.rel(OUT/'P39_context_report.json'),
        'context_report_sha256': w.sha(OUT/'P39_context_report.json'), 'replay': w.rel(OUT/'P39_replay_context.json'), 'replay_sha256': w.sha(OUT/'P39_replay_context.json'),
        'document': w.rel(DOC), 'forum': json.loads(p.stdout), 'all_exploratory_gates_pass': passed, 'new_primary_closed_learners': 30,
        'adverse_closed_learners_separate': 30, 'new_primary_constants': number, 'constants': dict(primary),
        'global_nominal': {c: {k: raw['results'][c]['NOMINAL'][k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for c in ['POOLED', 'TRANSFER']},
        'global_gates': context['global_gates'], 'new_business_gates': context['new_business_gates'], 'adopted': False,
        'new_source_fits': 0, 'new_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0, 'private_improvement_established': False,
        'next_unit': next_unit, 'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True}
    archive = R/'privado'/('corte_P39_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(cp); assert 'phase2_private_P39_saved_CB_target' not in counts
    w.update(cp, {'as_of_utc': now, 'cumulative_closed_form_constants': counts['cumulative_closed_form_constants']+number,
        'phase2_private_P39_saved_CB_target': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30, 'new_primary_constants': number,
            'constant_breakdown': dict(primary), 'new_iterative_price_fits': 0, 'new_source_fits': 0, 'new_C0_fits': 0, 'report': receipt['context_report']}}, archive)
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P39': receipt, 'next_unit': next_unit, 'last_progress_utc': now}, archive)
    phase = R/'registro/semana2_mision017_fase2_actual.json'; assert not w.read(phase).get('active_jobs')
    w.update(phase, {'private_P39': receipt, 'next_unit': next_unit, 'last_goal_turn_classification': 'progress: P39complete target comparison with existing CatBoost teachers,30primary/30adverse calls, source/C0frozen, saved-flow/cohort replay; no unsupported upload or private claim'}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P39=receipt, next_unit=next_unit, goal_achieved=False)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P39: CatBoost guardado en el algoritmo completo\n\nCodex, '+now+'. Guardas conjuntas='+str(passed)+';30calibraciones primarias/30adversas, '+str(number)+'constantes primarias. Sin reentrenar fuente/C0; replay exacto sin nuevos ajustes/remuestreo. No adopción automática o envío. B00/F3c/alternativas conservados,2024abierto. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_saved_CB_full_validation_index': w.rel(INDEX), 'week_2_private_saved_CB_full_validation_report': w.rel(DOC)}, archive)
    prior.dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'all_gates_pass': passed, 'new_primary_constants': number, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'replay', 'close']); args = parser.parse_args()
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay, 'close': close}[args.mode]()
