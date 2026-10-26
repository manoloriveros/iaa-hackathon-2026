"""Contrasta PS1 completo con150calibradores cerrados y sus controles adversos."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.util
import json
import math
import os
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
OUT = BASE/'P48_validacion_pareada_20261026'
PLAN = R/'registro/semana2_algoritmo_pareado_validacion_plan.json'
INDEX = R/'registro/semana2_algoritmo_pareado_validacion_actual.json'
DOC = R/'docs/semana2/PRIVADA_P48_VALIDACION_PAREADA.md'
sp = importlib.util.spec_from_file_location('p48_paired_learning', R/'herramientas/preparar_algoritmo_pareado_P47.py')
p = importlib.util.module_from_spec(sp); sp.loader.exec_module(p)
cp = importlib.util.spec_from_file_location('p48_standard_cohorts', R/'herramientas/validar_canal_privada_P23.py')
coh = importlib.util.module_from_spec(cp); cp.loader.exec_module(coh)
w = p.w; pd = p.pd; np = p.np; e = coh.e; e.OUT = OUT; coh.OUT = OUT
REFERENCE = BASE/'P15_validacion_ausentes_20261026'


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value): return p.dump(path, value)


def check_sources(plan):
    bad = [k for k, v in plan['sources'].items() if w.sha(ROOT/k) != v]; assert not bad, bad


def frame_for(binding, canonical):
    data = pd.read_parquet(ROOT/binding['inputs'])
    assert data.row_id.is_unique and canonical.row_id.is_unique and set(data.row_id).issubset(set(canonical.row_id))
    frame = canonical.set_index('row_id', drop=False).loc[data.row_id].reset_index(drop=True)
    assert np.array_equal(frame.year, data.year) and np.array_equal(frame.group_id, data.group_id)
    for name in ['is_held', 'annual_paired', 'q_paired']: frame[name] = data[name].to_numpy()
    train = frame.loc[~frame.is_held]
    assert p.b.digest(sorted(train.row_id)) == binding['training_row_digest']
    assert p.b.digest(sorted(set(train.group_id))) == binding['training_groups_digest']
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held, 'group_id']))
    return frame


def event(kind, **values):
    with (OUT/'events.jsonl').open('a', encoding='utf8') as f: f.write(json.dumps({'utc': utc(), 'kind': kind, **values})+'\n')


def execution_state(execution):
    archive = R/'privado'/('p48_state_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    path = R/'registro/semana2_mision017_fase2_actual.json'
    jobs = [] if execution is None else [execution]
    w.update(path, {'active_execution': execution, 'active_jobs': jobs}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(active_jobs=jobs)
    w.update(state, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': execution}, archive)


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json'); assert not phase.get('active_jobs') and not phase.get('active_execution')
    pre = w.read(p.OUT/'report.json'); closed = w.read(p.OUT/'completion_receipt.json')
    assert closed['report_sha256'] == w.sha(p.OUT/'report.json') and len(pre['bindings']) == 150 and len(pre['outer_adapters']) == 30
    assert all(w.sha(ROOT/k) == v for k, v in pre['outputs'].items())
    ancestor = w.read(p.PLAN); assert pre['plan_sha256'] == w.sha(p.PLAN) and all(w.sha(ROOT/k) == v for k, v in ancestor['sources'].items())
    template = w.read(R/'registro/semana2_marca_capital_validacion_privada_plan.json'); OUT.mkdir()
    sources = dict(ancestor['sources']); sources.update(pre['outputs'])
    paths = [Path(__file__), Path(p.__file__), Path(coh.__file__), Path(e.__file__), p.PLAN, p.OUT/'report.json',
        p.OUT/'completion_receipt.json', p.OUT/'synthetic.json', R/'registro/semana2_marca_capital_validacion_privada_plan.json',
        BASE/'estimando_cartera2025_v3/weights.parquet', BASE/'P19_cohortes_broker_20261026/group_universe.json',
        BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy']
    cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet', filters=[('year', 'in', [2023, 2024])])
    assert not cov.is_test.any() and cov.row_id.is_unique
    cov.to_parquet(OUT/'covariates.parquet', index=False); paths.append(OUT/'covariates.parquet')
    for evaluation in ['POOLED', 'TRANSFER']: paths.append(REFERENCE/(evaluation+'_prices.parquet'))
    sources.update({w.rel(k): w.sha(k) for k in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'PS1_standalone_paired_source_nested5_closed_main_effects',
        'hypothesis': 'A complete simple cost model with one coherent paired-source peril observation link for learning, ultimate forward and the delivered five-member mean may transfer more robustly than changing source risk under the old FSp link. This is a new whole algorithm, not a causal single-effect test.',
        'configuration': ancestor['formula'], 'calendar': ancestor['calendar'], 'contrast': ancestor['contrast'],
        'scope': 'The exact150P47member inputs,150own C0objects,30outer adapters and stored global/inner partitions. No existing calibrator copied as if adapted to the new exposure.',
        'learning': 'Fixed inherited K300shape/residual and K400business credibility; all numeric functions frozen inP47. No extra variables, coefficients, weights, source models, C0curves, hyperparameter search, dropping claims or clipping.',
        'primary_comparator': 'Original protected A1S/S2/H1 complete reference on identical historical rows; not reconstructed deliveredF3c.',
        'observation': 'Each member learns under its OWN q_scope from paired source rates and saved scoped C0. Forward ultimate ignores oldvaluation qand uses calendar exposure exactly once. Average5ultimate costs, then outer qfor evaluation only.',
        'sensitivity': 'Ultimate means fixed after nominal learning. Same four reserve/tail scenarios with each algorithms own original/new fixed profile and saved outerC0costCDFbranches. Nominal source mark weights frozen; not refitting all source/target pieces under reserve branches.',
        **{k: template[k] for k in ['criteria', 'bootstrap', 'level_sensitivity', 'cohort_guard']},
        'budget': {'new_source_fits': 0, 'new_C0_fits': 0, 'primary_closed_learners': 150, 'adverse_closed_learners_separate': 150,
            'new2025inference': 0, 'new_submissions': 0, 'new_hyperparameter_trials': 0},
        'bindings': pre['bindings'], 'sources': sources,
        'controls': ['Exact own scoped q/year/group digests before each calibrator, no outer C0in member input.',
            'Save every invoked primary/adverse checkpoint and learned object; no blind repeat of partial work.',
            'Held T0/reserve poison leaves actual learned artifact/ultimate member unchanged; training sensitivity already checked on full new synthetic flow.',
            'Independent scalar Tweedie line-level moment, learned count accounting, complete five-member mean and observation composition.',
            'Replay with all learning/source application entry points blocked; exact saved member outputs/normalizers and group intervals, no new bootstrap.'],
        'limits': ancestor['limits']+['150models at64percent training in nested pooled validation versus80percent production models; future transfer conditional on source2024.',
            'Fixed source estimates/observation assumptions and repeated adaptive search not covered by conditional bootstrap. No professional independent validation.'],
        'after_failure': 'Preserve adverses; no retuning K, weights, variables, model family or line/segment rescue withinP48.',
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P48preinscribe PS1 completo antes de ajustar o puntuar:150calibradores cerrados primarios y150controles adversos, con las entradas y C0propios P47. Suma fuente pareada, NCB/previos/negocio y residuales estándar, calendario una vez, media aritmética de cinco últimos y qexterior solo para evaluación. Sin N3directo o cocienteH1/G3; es otro algoritmo completo y no prueba causal de un cambio. P24/HET/P44/P45adversos permanecen. Criterios globales y NB/broker/historia cero/familia16, escenarios, nivel y concentración sin cambios. Se guardará cada miembro y su contador real; no se repetirá un checkpoint parcial sin conciliar. Replays con aprendizaje bloqueado. Cero ajustes fuente/C0, inferencias2025 o envíos. No elegir K/pesos/ramos tras el score. B00/F3cconservados;2024abierto adaptativo y privada prioritaria. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P48registered_before_contest_fit_and_score', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': p.post(body, 'COD-S2-20261026-PRIVADA-P48-PAREADO-PREVIO', 'P48: comparación completa PS1,150miembros propios y guardas intactas')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps({'registered': True, 'primary': 150, 'adverse': 150, 'forum': receipt['forum']}))


def fit_member(binding, canonical):
    tag = f"{binding['evaluation']}_{binding['line']}_{binding['outer']}_{binding['member']}"; folder = OUT/tag
    if (folder/'committed.json').exists():
        saved = w.read(folder/'committed.json'); assert saved['binding'] == binding
        assert all(w.sha(ROOT/k) == v for k, v in saved['outputs'].items()); return
    folder.mkdir(exist_ok=True); frame = frame_for(binding, canonical); held = frame.loc[frame.is_held].copy()
    for role in ['primary', 'poison']:
        invoke = folder/(role+'_invoked.json'); modelpath = folder/(role+'_learning.json')
        assert not invoke.exists(), 'Partial invocation: reconcile before any resume or refit'
        dump(invoke, {'author': 'Codex', 'utc': utc(), 'role': role, 'binding': binding, 'plan_sha256': w.sha(PLAN)})
        data = frame.copy()
        if role == 'poison': data.loc[data.is_held, ['T0', 'reserve']] = -1e30
        a = p.learn(data, binding['line']); dump(modelpath, a); counts = p.constant_counts(a)
        event('closed_completed', member=tag, role=role, constants=counts)
        u, norms = p.forward(data.loc[data.is_held], a, True)
        assert a['fit_row_ids_digest'] == binding['training_row_digest'] and a['fit_groups_digest'] == binding['training_groups_digest']
        if role == 'primary': primary = a; expected = u; expected_norms = norms
        else: assert a == primary and np.array_equal(u, expected) and norms == expected_norms
    train = frame.loc[~frame.is_held].copy(); value = p.base(train)
    for shape in primary['shape']: value = p.b.shape_apply(train, value, shape)
    moment = math.fsum((train.T0.to_numpy()/np.sqrt(value)).tolist())/math.fsum(np.sqrt(value).tolist())
    assert math.isclose(moment, primary['level'], rel_tol=3e-12)
    result = held[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id']].copy(); result['ultimate'] = expected
    result.to_parquet(folder/'ultimate.parquet', index=False)
    dump(folder/'committed.json', {'binding': binding, 'held_poison_learning_and_ultimate_exact': True, 'ultimate_normalizers': expected_norms,
        'moment_relative_error': abs(moment/primary['level']-1), 'outputs': {w.rel(k): w.sha(k) for k in folder.iterdir() if k.is_file()}})


def evaluate(plan):
    results = {}
    for evaluation in ['POOLED', 'TRANSFER']:
        reference = pd.read_parquet(REFERENCE/(evaluation+'_prices.parquet')); canonical = pd.concat([pd.read_parquet(p.P1/f'canonical_{line}.parquet') for line in p.prev.p.LINES]).set_index('row_id')
        pieces = []
        for line in p.prev.p.LINES:
            for outer in range(5):
                adapter = pd.read_parquet(p.OUT/f'{evaluation}_{line}_{outer}_outer_adapter.parquet')
                members = [pd.read_parquet(OUT/f'{evaluation}_{line}_{outer}_{member}/ultimate.parquet').set_index('row_id').loc[adapter.row_id] for member in range(5)]
                for member in members:
                    assert np.array_equal(member.line, adapter.line) and np.array_equal(member.group_id, adapter.group_id)
                ultimate = np.column_stack([member.ultimate.to_numpy() for member in members]).mean(axis=1)
                f = adapter[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']].copy(); f['new_nominal'] = ultimate*adapter.NOMINAL_q.to_numpy()
                f['ultimate_mean'] = ultimate
                for name in e.NAMES[1:]: f[name+'_new'] = ultimate*adapter[name+'_q'].to_numpy()
                pieces.append(f)
        combined = pd.concat(pieces).set_index('row_id').loc[reference.row_id].reset_index(drop=True)
        for key in ['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']: assert np.array_equal(combined[key], reference[key]), key
        saved = combined.copy(); saved['old_nominal'] = reference.old_nominal.to_numpy()
        y = saved.T0.to_numpy(float); reserve = canonical.loc[saved.row_id].reserve.to_numpy(float); ys = [y, y-.25*reserve, y+.25*reserve, y, y]
        data = [(y, saved.old_nominal.to_numpy(), saved.new_nominal.to_numpy())]
        for j, name in enumerate(e.NAMES[1:], 1):
            saved[name+'_old'] = reference[name+'_old'].to_numpy(); data.append((ys[j], saved[name+'_old'].to_numpy(), saved[name+'_new'].to_numpy()))
        saved.to_parquet(OUT/(evaluation+'_prices.parquet'), index=False)
        weights = pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[saved.row_id]
        assert np.array_equal(weights.group_id, saved.group_id)
        results[evaluation] = e.metrics(saved, data, evaluation, weights.weight.to_numpy(float), plan)
    return results


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN); check_sources(plan)
    assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    if not (OUT/'started.json').exists(): dump(OUT/'started.json', {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'script': w.rel(Path(__file__)), 'kind': 'P48nested_standard_cost_algorithm'})
    execution = {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'script': w.rel(Path(__file__)), 'kind': 'P48nested_standard_cost_algorithm', 'output': w.rel(OUT)}
    execution_state(execution)
    try:
        for line in p.prev.p.LINES:
            canonical = pd.read_parquet(p.P1/f'canonical_{line}.parquet')
            for binding in [x for x in plan['bindings'] if x['line'] == line]:
                fit_member(binding, canonical)
            print(json.dumps({'line': line, 'committed_members': 50}), flush=True)
    except BaseException as exc:
        dump(OUT/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'), {'exception': type(exc).__name__, 'message': str(exc),
            'committed_members': len(list(OUT.glob('*/committed.json'))), 'instruction': 'Reconcile saved primary/adverse invocations and job handle; never blindly repeat fits.'})
        execution_state(None)
        raise
    assert len(list(OUT.glob('*/committed.json'))) == 150
    results = evaluate(plan); cohorts = coh.cohort_analysis(); check_sources(plan)
    a = results['POOLED']['NOMINAL']; t = results['TRANSFER']['NOMINAL']; crit = plan['criteria']
    gates = {'pooled_delta_ge002': a['delta'] >= crit['nominal_pooled_delta_min'], 'pooled_lower95_positive': a['bootstrap95'][0] > 0,
        'pooled_atleast4positive_folds': sum(v > 0 for v in a['folds'].values()) >= 4, 'both_pooled_years_nonnegative': min(a['years'].values()) >= 0,
        'pooled_post31_nonnegative': a['post31_delta'] >= 0, 'conditional_transfer_nonnegative': t['delta'] >= 0,
        'all_nominal_and_stress_cell_floors': all(x['worst_cell_delta'] >= crit['all_nominal_and_stress_cell_floors'] for z in results.values() for x in z.values())}
    calls = Counter(); counts = {'primary': Counter(), 'poison': Counter()}
    for row in (OUT/'events.jsonl').read_text(encoding='utf8').splitlines():
        obj = json.loads(row); calls[obj['role']] += 1; counts[obj['role']].update(obj['constants'])
    assert calls == {'primary': 150, 'poison': 150} and counts['primary'] == counts['poison']
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P48complete_standard_paired_algorithm', 'plan_sha256': w.sha(PLAN),
        'results': results, 'global_gates': gates, 'new_business_gates': cohorts['gates'], 'all_exploratory_gates_pass': all(gates.values()) and all(cohorts['gates'].values()),
        'new_primary_closed_learners': 150, 'adverse_closed_learners_separate': 150, 'primary_constants': dict(counts['primary']),
        'new_source_fits': 0, 'new_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0, 'adopted': False,
        'private_improvement_established': False, '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    execution_state(None)
    print(json.dumps({'complete': True, 'nominal': {k:{j:v['NOMINAL'][j] for j in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for k, v in results.items()}, 'global_gates': gates, 'NB_gates': cohorts['gates'], 'primary_constants': report['primary_constants']}))


def replay():
    assert not (OUT/'replay_report.json').exists(); plan = w.read(PLAN); check_sources(plan); report = w.read(OUT/'report.json')
    before = w.sha(OUT/'events.jsonl')
    def reject(*a, **kw): raise AssertionError('No fitting or source application during P48replay')
    for module, key in [(p, 'learn'), (p.b, 'shape_fit'), (p.b, 'cell_levels'), (p.b, 'factor'), (p.g, 'fit_stage'),
        (p.prev.p.m, 'coefficients'), (p.prev.p.m, 'predict')]: setattr(module, key, reject)
    for line in p.prev.p.LINES:
        canonical = pd.read_parquet(p.P1/f'canonical_{line}.parquet')
        for binding in [x for x in plan['bindings'] if x['line'] == line]:
            folder = OUT/f"{binding['evaluation']}_{line}_{binding['outer']}_{binding['member']}"; commit = w.read(folder/'committed.json')
            assert all(w.sha(ROOT/k) == v for k, v in commit['outputs'].items())
            frame = frame_for(binding, canonical); frame.loc[frame.is_held, ['T0', 'reserve']] = 1e30
            value, norms = p.forward(frame.loc[frame.is_held], w.read(folder/'primary_learning.json'), True)
            saved = pd.read_parquet(folder/'ultimate.parquet'); assert np.array_equal(value, saved.ultimate) and norms == commit['ultimate_normalizers']
    for evaluation in ['POOLED', 'TRANSFER']:
        f = pd.read_parquet(OUT/(evaluation+'_prices.parquet')); draws = np.load(OUT/(evaluation+'_joint_bootstrap.npy'))
        yy = f.T0.to_numpy(float); old = f.old_nominal.to_numpy(float); new = f.new_nominal.to_numpy(float)
        gain = math.fsum(4*float(y)*(1/math.sqrt(float(a))-1/math.sqrt(float(b)))+4*(math.sqrt(float(a))-math.sqrt(float(b))) for y, a, b in zip(yy, old, new))
        den = 8*(math.sqrt(len(yy)*math.fsum(yy.tolist()))-math.fsum(math.sqrt(float(y)) for y in yy))
        assert math.isclose(gain/den, report['results'][evaluation]['NOMINAL']['delta'], rel_tol=1e-9, abs_tol=1e-12)
        for j, name in enumerate(e.NAMES): assert np.array_equal(np.quantile(draws[:, j], [.025, .975]), report['results'][evaluation][name]['bootstrap95'])
    totals, desc, _, _ = coh.cohort_blocks(); weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy'); draws = np.load(OUT/'cohort_bootstrap.npy')
    assert np.allclose(coh.score_cohort_sums(weights@totals), draws[:4], rtol=2e-12, atol=2e-13)
    cohort = w.read(OUT/'cohort_report.json')
    for j, z in enumerate(cohort['comparisons']):
        assert desc[j]['delta'] == z['delta'] and np.array_equal(np.quantile(draws[:, j], [.025/16, 1-.025/16]), z['family16_band95'])
    assert w.sha(OUT/'events.jsonl') == before; check_sources(plan)
    dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P48all150saved_flow_replays_exact',
        'report_sha256': w.sha(OUT/'report.json'), 'learning_and_source_inference_blocked': True, 'held_target_poison': True,
        'new_fits': 0, 'new_resampling': 0, 'all_saved_intervals_and_first4cohort_multiplicities_exact': True, 'events_unchanged': True})
    print(json.dumps({'replay': 'exact', 'members': 150, 'new_fits': 0, 'new_resampling': 0}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); d = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert replay['report_sha256'] == w.sha(OUT/'report.json'); passed = d['all_exploratory_gates_pass']
    number = sum(d['primary_constants'].values())
    next_unit = ('Audit exact PS1production and dataset/recipe reproducibility before admission; passing exploratory checks alone does not prove private performance or authorize automatic promotion.' if passed else
        'P49: review the new PS1failure with its saved member parameters, training support and fixed-profile assumption before any further recipe. Diagnose whether new observation/level effects or unstable target shapes dominate, using a preregistered algebraic decomposition of these NEW predictions only; do not repeat old HET/P13/P31audits or source fits. Keep exact candidate, all adverse cells and unchanged guards. No K/weight/profile rescue, source capacity search or upload from this failed PS1.')
    text = '# P48: algoritmo estándar pareado completo\n\nCodex, '+utc()+'. '+('Las guardas exploratorias conjuntas pasan; falta revisar producción y admisión exactas.' if passed else 'El algoritmo no supera las guardas conjuntas; se conserva sin adopción o envío.')
    text += '\n\nSe ajustaron150calibradores cerrados primarios y150controles adversos separados. Cada miembro usa su propia observación por peril y su C0interno; calendario una vez, avance a último, media aritmética de cinco y adaptador exterior propio solo para evaluar. Es un algoritmo completo distinto: suma GLM pareada, formas y residuales estándar, sin N3directo o cocienteH1/G3. No permite atribuir el resultado a un solo componente.\n\n| Nominal | Δ D² | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    nominal = {}
    for evaluation in ['POOLED', 'TRANSFER']:
        z = d['results'][evaluation]['NOMINAL']; nominal[evaluation] = {k:z[k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']}
        text += f"| {evaluation} | {z['delta']:+.7f} | [{z['bootstrap95'][0]:+.7f}; {z['bootstrap95'][1]:+.7f}] | {z['post31_delta']:+.7f} | {z['worst_cell_delta']:+.7f} |\n"
    text += '\nGuardas globales: '+json.dumps(d['global_gates'])+'. Guardas NB/broker/historia cero: '+json.dumps(d['new_business_gates'])+'. Se conservan todos los ramos/folds/años/negocios, reservas/cola y sensibilidad de nivel, sin rescatar una celda o probar otros pesos.\n\n'
    text += f'Se aprendieron{number}constantes primarias; los controles adversos se registran aparte. Los150objetos/precios fueron invariantes a alterar T0/reservas retenidos, los niveles se cotejaron por sumas escalares y el replay completo bloqueó todo aprendizaje/inferencia fuente. Los intervalos y cuatro multiplicidades guardadas se verificaron sin otro remuestreo. No hubo ajustes fuente/C0, inferencias2025 o envíos.\n\n'
    text += 'La fuente2024, maestros sin fecha, mezcla última, cola/reservas y búsqueda adaptativa siguen limitando la interpretación. Miembros con64%de entrenamiento frente al80%de producción, sin fingir equivalencia.2024abierto adaptativo, sin mejora privada acreditada o revisión profesional independiente. B00, F3c y todos los adversos conservados.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P48complete_not_automatically_admitted', 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'nominal': nominal, 'all_exploratory_gates_pass': passed, 'global_gates': d['global_gates'], 'new_business_gates': d['new_business_gates'],
        'primary_closed_learners': 150, 'adverse_closed_learners_separate': 150, 'new_primary_constants': number, 'primary_constants': d['primary_constants'],
        'new_source_fits': 0, 'new_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0, 'next_unit': next_unit, 'goal_achieved': False, '2024_open': True,
        'forum': p.post(body, 'COD-S2-20261026-PRIVADA-P48-PAREADO-RESULTADO', 'P48: algoritmo pareado completo, adversos y150replays guardados')}
    archive = R/'privado'/('corte_P48_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    counts_path = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(counts_path); assert 'phase2_private_P48_paired_cost_target' not in counts
    w.update(counts_path, {'as_of_utc': utc(), 'cumulative_closed_form_constants': counts['cumulative_closed_form_constants']+number,
        'phase2_private_P48_paired_cost_target': {'primary_closed_learners': 150, 'adverse_closed_learners_separate': 150, 'new_primary_constants': number, 'new_source_fits': 0, 'new_C0_fits': 0}}, archive)
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P48': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P48': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P48=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P48: algoritmo pareado completo\n\nCodex, '+receipt['utc']+'. Guardas conjuntas='+str(passed)+f'.150calibradores primarios/150adversos,{number}constantes primarias; replay completo exacto sin reajuste o remuestreo. Cero fuente/C0/inferencias2025/envíos. B00/adversos conservados. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_paired_algorithm_validation_index': w.rel(INDEX), 'week_2_private_paired_algorithm_validation_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'all_gates_pass': passed, 'new_primary_constants': number, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); a = argparse.ArgumentParser(description=__doc__); a.add_argument('mode', choices=['prepare', 'run', 'replay', 'close']); mode = a.parse_args().mode
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay, 'close': close}[mode]()
