"""Contraste completo de Poisson fijo y severidad reducida al capital."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
sp = importlib.util.spec_from_file_location('p44_adapter', R/'herramientas/validar_ausencias_privada_P26.py')
p = importlib.util.module_from_spec(sp); sp.loader.exec_module(p)
e = p.e; previous = p.previous; w = p.w; pd = p.pd; np = p.np
BASE = p.BASE; SOURCE = BASE/'P43_marca_capital_20261026'
OUT = BASE/'P44_validacion_marca_capital_20261026'
PLAN = R/'registro/semana2_marca_capital_validacion_privada_plan.json'
INDEX = R/'registro/semana2_marca_capital_validacion_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P44_MARCA_CAPITAL_COMPLETA.md'
e.OUT = OUT; e.P9 = SOURCE; e.PLAN = PLAN; e.INDEX = INDEX
previous.OUT = OUT; previous.PLAN = PLAN; previous.INDEX = INDEX; previous.COV = None


def utc(): return datetime.now(timezone.utc).isoformat()


def state(execution):
    if execution is not None: execution = {**execution, 'script': w.rel(Path(__file__)), 'kind': 'P44complete_capital_mark_validation'}
    p.ORIGINAL_STATE(execution)


e.state.state_execution = state


def post(body, identifier, subject):
    a = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', identifier, '--asunto', subject, '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    return json.loads(a.stdout)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists() and not w.read(e.state.PHASE).get('active_jobs')
    source = w.read(SOURCE/'report.json'); closed = w.read(SOURCE/'completion_receipt.json')
    assert source['source_veto_all_pass'] and source['new_source_GLM_fits'] == 30 and closed['report_sha256'] == w.sha(SOURCE/'report.json')
    assert all(w.sha(ROOT/k) == v for k, v in source['outputs'].items())
    sourceplan = w.read(R/'registro/semana2_marca_capital_privada_plan.json'); assert all(w.sha(ROOT/k) == v for k, v in sourceplan['sources'].items())
    OUT.mkdir(); template = w.read(R/'registro/semana2_frecuencia_marca_validacion_privada_plan.json'); common = w.read(R/'registro/semana2_canal_privada_plan.json')
    sources = {k: v for k, v in common['sources'].items() if 'P23_canal_principal_20261026/' not in k}; assert all(w.sha(ROOT/k) == v for k, v in sources.items())
    paths = [Path(__file__), Path(p.__file__), Path(previous.__file__), SOURCE/'report.json', SOURCE/'completion_receipt.json', SOURCE/'scalar_replay.json',
        R/'registro/semana2_marca_capital_privada_plan.json', R/'herramientas/fuente_marca_capital_P43.py',
        BASE/'P26_validacion_ausencias_20261026/synthetic_adapter.json', BASE/'P26_validacion_ausencias_20261026/P26_replay_context.json']
    cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet', filters=[('year', 'in', [2023, 2024])]); assert not cov.is_test.any() and cov.row_id.is_unique
    cov.to_parquet(OUT/'covariates.parquet', index=False); paths.append(OUT/'covariates.parquet'); scopes = []
    for line in e.h.LINES:
        file = SOURCE/f'historical_{line}_three_seed.parquet'; relative = pd.read_parquet(file); p.strict_relative(relative)
        canonical = pd.read_parquet(e.P1/f'canonical_{line}.parquet', columns=['row_id', 'year']); assert set(relative.row_id) == set(canonical.row_id); p.attach_relative(canonical, relative)
        paths += [file, SOURCE/f'application_{line}.json']
        for recordpath in sorted((SOURCE/line).glob('*_full/fit_record.json')):
            record = w.read(recordpath); assert record['model_sha256'] == w.sha(recordpath.parent/'model.json')
            paths += [recordpath, recordpath.parent/'model.json', recordpath.parent/'controls.json']
        for scope in [s for s in template['scopes'] if s['line'] == line]:
            f, held, _ = e.get_scope(scope['cohort'], line, scope['outer'], relative); train = f.fold.ne(held)
            assert e.b.digest(sorted(f.loc[train, 'row_id'])) == scope['training_row_digest']
            assert e.b.digest(sorted(set(f.loc[train, 'group_id']))) == scope['training_groups_digest']; scopes.append(scope)
    assert len(scopes) == 30; sources.update({w.rel(path): w.sha(path) for path in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Fixed_Poisson_capital_only_mark_original_50_50_S2_H1',
        'hypothesis': 'Source severity constant was inadequate; a value-only mark passed source veto with lower complexity thanP30. Test its full-algorithm transfer, without attributing P30failure causally or inferring private gain.',
        'change': 'Only source annual relativities fromP43. Frequency models fixed; reduced marks already fit. Same target shape/level/residual rules,50/50N3, fiveH1/G3mean, original qsourcebridge and all saved folds.',
        'source_identity': 'One fixed15peril Poisson/mark sum across3lines, no seed ensemble despite compatibility filenames. Motorvehicle_value_group/home log_siand their original missing flags only in marks.',
        'primary_comparator': template['primary_comparator'], 'configuration': template['configuration'], 'changed_learning': template['changed_learning'],
        'budget': template['budget'], 'exposure': template['exposure'], 'sensitivity': template['sensitivity'], 'criteria': template['criteria'],
        'bootstrap': template['bootstrap'], 'level_sensitivity': template['level_sensitivity'], 'cohort_guard': template['cohort_guard'],
        'scopes': scopes, 'sources': sources, 'preflight': {'all30new_source_bindings_exact': True, 'unchanged_adapter_and_complete_flow_fixtures_reused_by_SHA': True, 'new_synthetic_fits': 0},
        'limits': common['limits']+['Source gate is conditional/adaptive and not independent; current complete comparator is not automatically deliveredF3c.',
            'Paired source count/mark observation assumptions, rare target NBsupport, undated masters, reserves/tail remain.',
            'New F3csource-presence/retraining evidence is separate; no borrowed foreign score changes this frozen recipe.'],
        'new_source_fits': 0, 'new_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0, '2024_open': True, 'B00_all_alternatives_preserved': True}
    p.dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P44preinscrito: contrastar la fuente P43con Poisson fijo y marcas reducidas al capital dentro de la mezcla original50/50S2/H1. Fuente ya ajustada y vetada; no hay entrenamiento fuente/C0nuevo.30calibraciones cerradas primarias y30adversas, mismos ámbitos y criterios globales/NB/broker/historia cero/familia16de P30. qsource, media H1/G3, objetivo/exposición y referencia permanecen. No escoger perils, pesos o ramos tras ver resultados. Pasar el veto fuente no prueba transferencia. Adaptador/flujo sin cambios reutilizados por SHA;30nuevas membresías coinciden. Cero inferencias2025o envíos. B00/F3c/alternativas conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P44registered_before_target_learning', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': post(body, 'COD-S2-20261026-PRIVADA-P44-MARCA-CAPITAL-PREVIO', 'P44: marca reducida al capital en el algoritmo completo, antes de ajustar')}
    p.dump(OUT/'registration.json', receipt); p.dump(INDEX, receipt); print(json.dumps({'registered': True, 'scopes': 30, 'forum': receipt['forum']}))


def run():
    assert not w.read(e.state.PHASE).get('active_jobs'); p.dump(OUT/'P44_execution_context.json', {'author': 'Codex', 'utc': utc(), 'script': w.rel(Path(__file__)), 'source': w.rel(SOURCE)})
    e.run(); raw = w.read(OUT/'report.json'); cohort = previous.cohort_analysis()
    context = {'author': 'Codex', 'utc': utc(), 'candidate': 'Fixed_Poisson_capital_only_mark_original_50_50_S2_H1',
        'raw_report_sha256': w.sha(OUT/'report.json'), 'global_gates': raw['diagnostic_gates'], 'new_business_gates': cohort['gates'],
        'all_exploratory_gates_pass': all(raw['diagnostic_gates'].values()) and all(cohort['gates'].values()),
        'new_primary_closed_learners': 30, 'adverse_closed_learners_separate': 30, 'new_source_fits': 0, 'new_C0_fits': 0,
        'new2025inference': 0, 'new_submissions': 0, 'private_improvement_established': False, 'goal_achieved': False, '2024_open': True}
    p.dump(OUT/'P44_context_report.json', context); print(json.dumps(context))


def replay():
    e.replay(); report = w.read(OUT/'cohort_report.json'); saved = np.load(OUT/'cohort_bootstrap.npy')
    assert report['cohort_draws_sha256'] == w.sha(OUT/'cohort_bootstrap.npy')
    totals, desc, _, _ = previous.cohort_blocks(); weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    assert np.allclose(previous.score_cohort_sums(weights@totals), saved[:4], rtol=2e-12, atol=2e-13)
    for j, a in enumerate(report['comparisons']):
        assert desc[j]['delta'] == a['delta'] and np.array_equal(np.quantile(saved[:, j], [.025, .975]), a['marginal95'])
        assert np.array_equal(np.quantile(saved[:, j], [.025/16, 1-.025/16]), a['family16_band95'])
    p.dump(OUT/'P44_replay_context.json', {'author': 'Codex', 'utc': utc(), 'context_sha256': w.sha(OUT/'P44_context_report.json'), 'replay_sha256': w.sha(OUT/'replay_report.json'), 'new_fits': 0, 'new_inference': 0, 'new_resampling': 0})
    print(json.dumps({'replay': 'exact', 'new_fits': 0, 'new_resampling': 0}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); raw = w.read(OUT/'report.json'); c = w.read(OUT/'P44_context_report.json'); r = w.read(OUT/'P44_replay_context.json')
    assert c['raw_report_sha256'] == w.sha(OUT/'report.json') and r['context_sha256'] == w.sha(OUT/'P44_context_report.json') and r['replay_sha256'] == w.sha(OUT/'replay_report.json')
    calls = Counter(); primary = Counter(); adverse = Counter()
    for a in [json.loads(z) for z in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines()]:
        if a['kind'] == 'closed_completed': calls[a['role']] += 1; (primary if a['role'] == 'primary' else adverse).update(a['constants'])
    assert calls == {'primary': 30, 'poison': 30} and primary == adverse
    number = sum(primary[k] for k in ['shape_factors', 'level_constants', 'residual_factors', 'training_nuisance_levels']); passed = c['all_exploratory_gates_pass']
    next_unit = ('Audit exact future production and admission forP44under the unchanged private-first plan; no publicscore success claim, automatic promotion or upload from adaptive gates alone.' if passed else
        'P45: before more source capacity or mark feature searches, inspect a prespecified standard two-family equal-cost ensemble of the protected reference and the existing P15missing-indicator aggregate GLM. Verify no identical whole-algorithm recipe already exists, exact common keys/adapter/ultimate price bridge and no held-label learned weights. Freeze one50/50arithmetic complete-price mixture and current gates before computing new prices or scores; no line/cohort-dependent tuning. Use only saved protected artifacts, zero new source/target/C0fits. P44adverse retained; no missingf3_evalblock, new public probes or upload.')
    text = '# P44: marca reducida al capital en el algoritmo completo\n\nCodex, '+utc()+'. '+('Las guardas exploratorias pasan; falta auditar/admitir el archivo exacto, sin promoción automática.' if passed else 'Las guardas conjuntas fallan. Se conserva la prueba sin adopción o envío.')
    text += '\n\nSolo cambiaron relatividades fuente P43; objetivo, exposición, mezcla50/50N3, residuales, media H1/G3y qsource quedaron fijos.\n\n| Nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    nominal = {}
    for evaluation in ['POOLED', 'TRANSFER']:
        a = raw['results'][evaluation]['NOMINAL']; nominal[evaluation] = {k: a[k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']}
        text += f"| {evaluation} | {a['delta']:+.7f} | [{a['bootstrap95'][0]:+.7f}; {a['bootstrap95'][1]:+.7f}] | {a['post31_delta']:+.7f} | {a['worst_cell_delta']:+.7f} |\n"
    text += ('\nSe conservaron resultados por ramo/fold/año/negocio, NB/broker/historia cero, cuatro escenarios de reservas/cola, sensibilidad de nivel y bandas16. '
        'Guardas globales: '+json.dumps(c['global_gates'])+'. Guardas de negocio: '+json.dumps(c['new_business_gates'])+'.\n\n'
        '30calibraciones primarias,30adversas y '+str(number)+'constantes primarias nuevas; los30GLMde fuente P43no se cuentan otra vez. '
        'Los30flujos fueron invariantes a contaminación retenida; replay con aprendizaje/inferencia fuente bloqueados, precios/normalizadores y puntos/intervalos guardados exactos sin remuestreo. '
        'No se demuestra que el capital explique el fallo anterior o que la privada mejore. Fuente/cost-curvas comunes, maestros sin fecha, colas/reservas y búsqueda adaptativa permanecen. '
        'No es validación profesional independiente. B00/F3c/alternativas conservados;2024abierto. Cero nuevos ajustes fuente/C0, inferencias2025o envíos.\n\n'
        'Próximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'P44_context_report.json')+'; '+w.rel(OUT/'cohort_report.json')+'; '+w.rel(OUT/'P44_replay_context.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P44complete_not_automatically_admitted', 'report': w.rel(OUT/'P44_context_report.json'), 'report_sha256': w.sha(OUT/'P44_context_report.json'),
        'document': w.rel(DOC), 'all_exploratory_gates_pass': passed, 'nominal': nominal, 'global_gates': c['global_gates'], 'new_business_gates': c['new_business_gates'],
        'new_primary_closed_learners': 30, 'adverse_closed_learners_separate': 30, 'new_primary_constants': number, 'constants': dict(primary),
        'new_source_fits': 0, 'new_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0, 'next_unit': next_unit, 'goal_achieved': False, '2024_open': True,
        'forum': post(body, 'COD-S2-20261026-PRIVADA-P44-MARCA-CAPITAL-RESULTADO', 'P44: prueba completa de severidad reducida, con adversos y replay')}
    archive = R/'privado'/('corte_P44_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(cp); assert 'phase2_private_P44_capital_mark_target' not in counts
    w.update(cp, {'as_of_utc': utc(), 'cumulative_closed_form_constants': counts['cumulative_closed_form_constants']+number,
        'phase2_private_P44_capital_mark_target': {'primary_closed_learners': 30, 'adverse_closed_learners_separate': 30, 'new_primary_constants': number, 'new_source_fits': 0, 'new_C0_fits': 0}}, archive)
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P44': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P44': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P44=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P44: marca capital en el algoritmo completo\n\nCodex, '+receipt['utc']+'. Guardas conjuntas='+str(passed)+';30calibraciones primarias/30adversas y '+str(number)+'constantes primarias. Replay exacto, cero entrenamiento fuente/C0/inferencias2025/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_capital_mark_target_index': w.rel(INDEX), 'week_2_private_capital_mark_target_report': w.rel(DOC)}, archive)
    p.dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'all_gates_pass': passed, 'new_primary_constants': number, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('mode', choices=['prepare', 'run', 'replay', 'close']); a = parser.parse_args()
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay, 'close': close}[a.mode]()
