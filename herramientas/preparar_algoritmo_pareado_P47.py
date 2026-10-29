"""Preflight numérico de un modelo estándar con observación por peril y media anidada."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.util
import json
import math
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
OUT = BASE/'P47_preflight_pareado_20261026'
PLAN = R/'registro/semana2_algoritmo_pareado_preflight_plan.json'
INDEX = R/'registro/semana2_algoritmo_pareado_preflight_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P47_ALGORITMO_PAREADO_PREFLIGHT.md'
sp = importlib.util.spec_from_file_location('p47_peril_profile_helpers', R/'herramientas/revisar_perfiles_observacion_P46.py')
prev = importlib.util.module_from_spec(sp); sp.loader.exec_module(prev)
w = prev.w; np = prev.np; pd = prev.pd; b = prev.frozen.b; g = prev.frozen.h.g
P1 = BASE/'preflight_anidado_H1_20261026_v1'
P2 = BASE/'media_anidada_H1_20261026_v3'; P4 = BASE/'P4_transferencia_anual_H1_20261026_v1'
LINK = prev.OUT


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def post(body, identifier, subject): return prev.post(body, identifier, subject)


def base(frame, ultimate=False):
    # Annual cost rate is already sum(lambda_p * mark_p); calendar exposure enters once.
    value = frame.annual_paired.to_numpy(float)*frame.exposure_calendar.to_numpy(float)
    if not ultimate: value = value*frame.q_paired.to_numpy(float)
    assert np.isfinite(value).all() and (value > 0).all()
    return value


def forward(frame, artifact, ultimate=False):
    value = base(frame, ultimate)
    for shape in artifact['shape']: value = b.shape_apply(frame, value, shape)
    value *= np.asarray([artifact['cellshape'][str(int(nb))] for nb in frame.new_business])
    norms = {}
    for stage in artifact['stages']:
        value, norm = g.apply_stage(frame, value, stage); norms[stage['variable']] = norm
    assert np.isfinite(value).all() and (value > 0).all()
    return value, norms


def learn(frame, line):
    train = frame.loc[~frame.is_held].copy(); held = frame.loc[frame.is_held].copy()
    assert train.T0.ge(0).all() and set(train.group_id).isdisjoint(set(held.group_id))
    value = base(train); shapes = []
    for which in (['ncb', 'prior'] if line == 'motor' else ['prior']):
        obj, value = b.shape_fit(train, value, which); shapes.append(obj)
    level = b.factor(train.T0.to_numpy(float), value); cell = b.cell_levels(train, value, level)
    value *= np.asarray([cell[str(int(nb))] for nb in train.new_business])
    stages = []; norms = {}
    for variable in g.STAGES[line]:
        obj = g.fit_stage(train, value, variable); value, norm = g.apply_stage(train, value, obj)
        stages.append(obj); norms[variable] = norm
    artifact = {'line': line, 'shape': shapes, 'level': level, 'cellshape': cell, 'stages': stages,
        'training_normalizers': norms, 'fit_row_ids_digest': b.digest(sorted(train.row_id)),
        'fit_groups_digest': b.digest(sorted(set(train.group_id))),
        'contract': 'PS1_calendar_paired_profile_standard_closed_calibration_no_N3_or_H1_ratio'}
    return artifact


def constant_counts(a):
    return {'shape_factors': sum(len(x['factors']) for x in a['shape']), 'level_constants': 3,
        'residual_factors': sum(len(x['factors']) for x in a['stages']),
        'training_nuisance_levels': sum(len(x['nuisance_year_business']) for x in a['stages'])}


def synthetic():
    rng = np.random.default_rng(2026102647); n = 1600
    frame = pd.DataFrame({'row_id': ['synthetic'+str(i) for i in range(n)], 'group_id': ['g'+str(i) for i in range(n)],
        'is_held': np.arange(n)%5 == 0, 'year': 2023+(np.arange(n)//5)%2, 'new_business': (np.arange(n)//10)%2,
        'T0': rng.gamma(2, 100, n)*(rng.random(n) < .3), 'reserve': 0., 'exposure_calendar': rng.uniform(.2, 1, n),
        'ncb_years': rng.integers(0, 15, n), 'prior_claims_5y': rng.integers(0, 3, n),
        'gender': rng.choice(['F', 'M'], n), 'works_from_home': rng.integers(0, 2, n),
        'marketing_segment': rng.choice(['a', 'b', 'c'], n)})
    rates = np.exp(rng.normal(3, .3, (n, 3))); q = rng.uniform(.2, 1, (n, 3)); q[::5, 0] = 0
    frame['annual_paired'] = rates.sum(axis=1); frame['q_paired'] = prev.weighted_q(rates, q)
    assert np.allclose(base(frame), frame.exposure_calendar.to_numpy()*(rates*q).sum(axis=1), rtol=3e-15)
    checks = []
    for line in prev.p.LINES:
        a = learn(frame, line); bad = frame.copy(); bad.loc[bad.is_held, ['T0', 'reserve']] = -1e30
        aa = learn(bad, line); assert a == aa
        held = frame.loc[frame.is_held].copy(); u, norms = forward(held, a, True)
        up, np_ = forward(bad.loc[bad.is_held], aa, True); assert np.array_equal(u, up) and norms == np_
        changed = frame.copy(); changed.loc[~changed.is_held, 'T0'] *= 1.7
        assert learn(changed, line) != a
        serial = json.loads(json.dumps(a)); replay, nr = forward(held, serial, True)
        assert np.array_equal(u, replay) and nr == norms
        # Unknown old-valuation completion may be zero for future covariates; ultimate uses no division by it.
        future = held.copy(); future['year'] = 2025; future['q_paired'] = 0.
        fu, _ = forward(future, a, True); assert np.isfinite(fu).all() and (fu > 0).all()
        assert np.array_equal(base(future, True), future.annual_paired.to_numpy()*future.exposure_calendar.to_numpy())
        members = np.column_stack([u*(1+i*.02) for i in range(5)]); outer_q = np.linspace(.1, 1, len(held))
        assert np.allclose(members.mean(axis=1)*outer_q, (members*outer_q[:, None]).mean(axis=1), rtol=2e-15)
        checks.append({'line': line, 'held_payload_poison_invariance': True, 'training_outcome_changes_model': True,
            'JSON_ultimate_replay_exact': True, 'zero_old_valuation_future_link_positive_ultimate': True,
            'five_member_observation_composition': True, 'learned_constants_one_fixture': constant_counts(a)})
    # A combined incomplete calendar period with equal peril completions recovers the scalar link exactly.
    common = np.tile(np.linspace(.2, .8, n)[:, None], (1, 3)); assert np.allclose(prev.weighted_q(rates, common), common[:, 0], rtol=2e-15)
    return {'author': 'Codex', 'utc': utc(), 'checks': checks, 'synthetic_closed_learners': 9,
        'new_iterative_model_fits': 0, 'new_C0_fits': 0, 'contest_fits_or_scores': 0,
        'limit': 'C0curves are saved parents reused by hash and scoped training keys; synthetic fixture verifies new learning/forward/composition, not a new C0estimator.'}


def make_scope(canonical, evaluation, outer, member):
    inner = pd.read_parquet(P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
    train = canonical.fold.ne(outer)
    if evaluation == 'TRANSFER': train &= canonical.year.eq(2023)
    if member >= 0: train &= canonical.group_id.map(inner).ne(member)
    held = canonical.fold.eq(outer)
    if evaluation == 'TRANSFER': held &= canonical.year.eq(2024)
    frame = canonical.loc[train | held].copy().reset_index(drop=True)
    frame['is_held'] = frame.fold.eq(outer)
    assert set(frame.loc[~frame.is_held, 'group_id']).isdisjoint(set(frame.loc[frame.is_held, 'group_id']))
    if evaluation == 'TRANSFER': assert frame.loc[~frame.is_held, 'year'].eq(2023).all()
    return frame


def member_c0(evaluation, line, outer, member):
    return (P2 if evaluation == 'POOLED' else P4)/f'scope_{line}_outer{outer}_member{member}/primary/C0.json'


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json'); assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert w.read(LINK/'report.json')['material_cells'] > 0
    OUT.mkdir(); fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    paths = [Path(__file__), Path(prev.__file__), Path(prev.frozen.__file__), Path(b.__file__), Path(g.__file__),
        R/'src/semana2/variables_ultimo.py', LINK/'report.json', LINK/'completion_receipt.json', OUT/'synthetic.json',
        P2/'completion_receipt.json', P2/'report.json', P4/'report.json',
        R/'registro/semana2_marca_capital_validacion_privada_plan.json']
    paths += [P1/f'inner_groups_outer{k}.parquet' for k in range(5)]
    for line in prev.p.LINES:
        paths += [P1/f'canonical_{line}.parquet', LINK/f'peril_rates_{line}.parquet']
        for evaluation in ['POOLED', 'TRANSFER']:
            for outer in range(5):
                paths += [prev.c0_path(evaluation, line, outer)]
                for member in range(5): paths += [member_c0(evaluation, line, outer, member)]
    plan = {'author': 'Codex', 'utc': utc(), 'status': 'P47preflight_only_not_registered_for_contest_fit',
        'candidate_design': 'PS1: standalone paired-source sum with closed target main-effect calibration and nested five-member arithmetic cost mean.',
        'need': 'P46recovered the missing current paired-source peril profile; its implied observation differs materially in30/90cells. Previous source changes retained another profile. Test physical observation/ultimate coherence before more source capacity, without treating this descriptive result as prediction evidence.',
        'contrast': 'New complete standard algorithm versus original protected A1S/S2/H1 reference. Not a one-variable causal ablation: unlike P44 it removes N3mix and H1/G3ratio, uses paired-source risk rates and consistent calendar exposure. Prior pure-componentP24and HETadverses retained; no claim this is the first risk-dependent link.',
        'formula': {'training_base': 'calendar_exposure_i * sum_p(source_lambda_ip*source_mark_ip*q_scope_ip)',
            'ultimate_base': 'calendar_exposure_i * sum_p(source_lambda_ip*source_mark_ip)',
            'target': 'T0incurred net recovery, unchanged; b.shape_fit fixed NCB/prior main effects K300, Tweedie-optimal line level, NB/RENlevels K400; same gender/WFH/marketing residuals K300.',
            'ensemble': 'Fit a separate standard calibrator in each of5inner training groups with its OWN saved C0, forward held to ultimate, arithmetic mean5(U_member). Evaluate mean with own outerC0weighted by same paired source risk. No fitted weights, recentering or H1/G3ratios.',
            'production_later': 'Five original global-fold models trained on80percent of historicaltarget, mean ultimate costs. Nested evaluation uses64percent per member; no equality-of-sample-size claim.'},
        'data': 'Emerging2023/2024historical and source2021-2024conditional rates, existing global/inner groups, original claims/labels untouched;2024adaptiveopen.',
        'calendar': 'Nominal inclusive calendar exposure from canonical input enters once in training and future. Rounded legacy exposure remains evidence, not reused as a monetary denominator.',
        'preflight': 'Map150inner C0objects plus30outer evaluation C0objects; validate exact training keys/excluded groups, per-row qpositive or legitimate perilzero. OuterC0must never supply member-training q. Save keyed qand annual rates without target fitting.',
        'budget_this_preflight': {'synthetic_closed_learner_calls': 9, 'contest_source_fits': 0, 'contest_target_fits': 0, 'new_C0_fits': 0,
            'new_source_inference': 0, 'new_prices': 0, 'new_scores': 0, 'new2025inference': 0, 'new_submissions': 0},
        'later_test_cost_if_separately_registered': {'primary_closed_learners': 150, 'adverse_closed_learners_separate': 150,
            'new_source_or_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0},
        'acceptance_later': 'Same P44/P45global and NB/broker/hist0 family16 gates, reserve/tail scenarios, level/influence checks, no weight/line rescue or weakened threshold.',
        'sources': {w.rel(k): w.sha(k) for k in paths}, 'limits': ['Future hidden performance unobserved; completed synthetic/provenance checks are not predictive validation.',
            'Fixed source2024and undated master fields, paired observation assumptions, limited target support, tail/reserve uncertainty and adaptive search remain.',
            'Changing several linked components defines a distinct whole algorithm; results cannot attribute effects to any one component.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P47 registra solo preflight numérico y de ámbitos de un algoritmo estándar coherente: suma de costes fuente por peril, observación por su propio C0de entrenamiento y avance a último con exposición calendario una vez. Calibraciones cerradas NCB/previos/negocio y residuales existentes, sin N3directo o cocienteH1/G3. Es un algoritmo nuevo con varios componentes relacionados, no una atribución causal ni una repetición de P24/HET; esos adversos quedan. Media fija de cinco precios últimos. Antes de cualquier fit destino se cotejarán150C0internos y30exteriores: ningún miembro toma C0exterior. El fixture comprobó aprendizaje/JSON/alteración retenida, calendario, futuro con completitud cero y media/enlace. Solo9llamadas cerradas sintéticas; cero ajustes reales, C0nuevos, inferencias fuente/2025, precios, scores o envíos. Una prueba predictiva posterior necesitará su propia preinscripción y las mismas guardas completas. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P47registered_before_real_input_preflight', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': post(body, 'COD-S2-20261026-PRIVADA-P47-PAREADO-PREVIO', 'P47: contrato estándar pareado, media completa y C0 propio por ámbito')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps({'registered': True, 'synthetic_closed_learners': 9, 'contest_fits': 0, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN) and all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
    bindings = []; outputs = {}; outer_diagnostics = []
    for line in prev.p.LINES:
        canonical = pd.read_parquet(P1/f'canonical_{line}.parquet'); profile = pd.read_parquet(LINK/f'peril_rates_{line}.parquet').set_index('row_id')
        assert canonical.row_id.is_unique and profile.index.is_unique and set(canonical.row_id) == set(profile.index)
        perils = sorted(x.removeprefix('annual_') for x in profile if x.startswith('annual_'))
        assert np.array_equal(profile.loc[canonical.row_id].year, canonical.year)
        for evaluation in ['POOLED', 'TRANSFER']:
            for outer in range(5):
                outer_path = prev.c0_path(evaluation, line, outer); exterior = w.read(outer_path)
                exterior = exterior['artifact']['C0'] if evaluation == 'POOLED' else exterior
                outer_frame = make_scope(canonical, evaluation, outer, -1)
                assert exterior['fit_row_ids'] == sorted(outer_frame.loc[~outer_frame.is_held, 'row_id'])
                for member in range(5):
                    f = make_scope(canonical, evaluation, outer, member); cp = member_c0(evaluation, line, outer, member); c0 = w.read(cp)
                    train = ~f.is_held; ids = sorted(f.loc[train, 'row_id']); assert c0['fit_row_ids'] == ids
                    assert c0['fit_row_ids'] != exterior['fit_row_ids'], 'No outer C0 inside member'
                    rates = profile.loc[f.row_id, ['annual_'+name for name in perils]].to_numpy(float)
                    qq = np.column_stack([prev.frozen.v.average_completion(f, c0['curves'][name], 'cost', 1.) for name in perils])
                    q = prev.weighted_q(rates, qq); assert (q > 0).all()
                    out = f[['row_id', 'year', 'group_id', 'is_held']].copy(); out['annual_paired'] = rates.sum(axis=1); out['q_paired'] = q
                    path = OUT/f'{evaluation}_{line}_{outer}_{member}_inputs.parquet'; out.to_parquet(path, index=False); outputs[w.rel(path)] = w.sha(path)
                    binding = {'evaluation': evaluation, 'line': line, 'outer': outer, 'member': member, 'training_rows': int(train.sum()),
                        'held_rows': int(f.is_held.sum()), 'training_row_digest': b.digest(ids), 'training_groups_digest': b.digest(sorted(set(f.loc[train, 'group_id']))),
                        'C0': w.rel(cp), 'C0_sha256': w.sha(cp), 'outer_C0_not_used_in_training': True, 'q_min': float(q.min()),
                        'q_max': float(q.max()), 'positive_train_by_business': {str(nb):int((f.new_business.eq(nb)&train&f.T0.gt(0)).sum()) for nb in [0, 1]},
                        'inputs': w.rel(path), 'inputs_sha256': w.sha(path)}
                    assert min(binding['positive_train_by_business'].values()) > 0; bindings.append(binding)
                held = outer_frame.loc[outer_frame.is_held].copy(); rates = profile.loc[held.row_id, ['annual_'+name for name in perils]].to_numpy(float)
                for name, branch, tail in [('NOMINAL', 1., 0.), ('RESERVE075', .75, 0.), ('RESERVE125', 1.25, 0.), ('TAIL005', 1., .05), ('TAIL010', 1., .10)]:
                    qq = np.column_stack([prev.frozen.v.average_completion(held, exterior['curves'][peril], 'cost', branch) for peril in perils])
                    qq *= 1-tail*np.asarray([peril in ['bodily_injury', 'subsidence'] for peril in perils])
                    q = prev.weighted_q(rates, qq); assert (q > 0).all()
                    if name == 'NOMINAL': adapter = held[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0', 'reserve']].copy()
                    adapter[name+'_q'] = q
                path = OUT/f'{evaluation}_{line}_{outer}_outer_adapter.parquet'; adapter.to_parquet(path, index=False); outputs[w.rel(path)] = w.sha(path)
                outer_diagnostics.append({'evaluation': evaluation, 'line': line, 'outer': outer, 'outer_training_rows': len(exterior['fit_row_ids']),
                    'held_rows': len(held), 'C0_sha256': w.sha(outer_path), 'new_prices_or_scores': 0})
    assert len(bindings) == 150 and len(outer_diagnostics) == 30
    assert all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
    dump(OUT/'report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P47synthetic_flow_and150member_inputs_preflight_complete',
        'plan_sha256': w.sha(PLAN), 'bindings': bindings, 'outer_adapters': outer_diagnostics, 'outputs': outputs,
        'new_contest_fits': 0, 'new_C0_fits': 0, 'new_source_inference': 0, 'new_prices': 0, 'new_scores': 0,
        'synthetic_closed_learners': 9, 'new_submissions': 0, 'private_improvement_established': False, 'goal_achieved': False, '2024_open': True})
    print(json.dumps({'complete': True, 'members': len(bindings), 'outer': len(outer_diagnostics), 'minimum_training_positive_business': min(min(x['positive_train_by_business'].values()) for x in bindings), 'new_contest_fits': 0}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); d = w.read(OUT/'report.json')
    assert d['plan_sha256'] == w.sha(PLAN) and all(w.sha(ROOT/k) == v for k, v in d['outputs'].items())
    next_unit = 'P48: separately preregister the exact PS1standalone paired-source nested five-member algorithm with P47saved scoped inputs and outer adapters.150primary closed calibrators+150poison controls, no source/C0fit; all original global/NB/broker/hist0family16gates and scenarios. Commit code/configuration before any contest fit/price/score. Validate actual new learner/ultimate means/scalar level and replay with learning blocked, preserve each member checkpoint and every adverse. Do not substitute another model or weight if it fails; no2025inference/upload without later exact-file review.'
    text = '# P47: contrato y entradas del algoritmo pareado\n\nCodex, '+utc()+'. El flujo nuevo pasó las comprobaciones sintéticas; se prepararon150entradas de miembros internos y30adaptadores exteriores. Cada miembro usa el C0cuyas claves coinciden exactamente con su entrenamiento, distinto del C0exterior. No se ajustaron modelos reales ni se midió rendimiento.\n\n'
    text += 'La propuesta PS1 usa la suma anual de los GLM pareados fuente P43. Aprende las formas cerradas NCB/previos, niveles de negocio contraídos y los residuales estándar, con observación por peril y exposición calendario una vez. Avanza cada miembro a último y promedia cinco costes. El C0exterior se reserva para evaluar ese promedio. Se prescinde de N3directo y del cocienteH1/G3: es otro algoritmo completo con varios componentes ligados, no una atribución causal a un único cambio o una repetición de P24/HET.\n\n'
    text += 'Se conservaron las curvas, respuestas, grupos y particiones; no se retocaron colas o reservas. Los escenarios exteriores nominal/reservas75/125/cola5/10 quedan guardados antes de aprender. Las tasas por peril ya estaban exportadas: aquí no se aplicaron modelos fuente otra vez. El fixture incluyó nueve calibraciones cerradas sintéticas, alteración de respuestas retenidas, sensibilidad al entrenamiento, JSON, exposición, futuro sintético con completitud cero y composición de la media. No acredita independencia de la revisión ni mejora privada.\n\n'
    text += 'Cero ajustes reales fuente/destino/C0, inferencias nuevas, precios, scores o envíos. Los miembros del backtest usarán64%del histórico frente al80%de los cinco de producción; los datos2024son desarrollo adaptativo y fuente2024condicional. Reservas/cola, maestros sin fecha y soporte siguen como límites. B00, F3c y todos los fallos permanecen.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': d['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'member_inputs': 150, 'outer_adapters': 30, 'new_contest_fits': 0, 'new_C0_fits': 0, 'new_prices': 0, 'new_scores': 0,
        'synthetic_closed_learners': 9, 'new_submissions': 0, 'next_unit': next_unit, '2024_open': True, 'goal_achieved': False,
        'forum': post(body, 'COD-S2-20261026-PRIVADA-P47-PAREADO-RESULTADO', 'P47: flujo sintético y150miembros con C0 propio, listos para preinscribir contraste')}
    archive = R/'privado'/('corte_P47_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P47': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P47': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P47=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P47: algoritmo pareado, preflight completo\n\nCodex, '+receipt['utc']+'.150miembros/30adaptadores preparados, C0propios y fixture del nuevo aprendizaje/media/último.9calibraciones sintéticas, cero ajustes reales/C0/precios/scores/envíos. No es mejora predictiva acreditada. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_paired_algorithm_preflight_index': w.rel(INDEX), 'week_2_private_paired_algorithm_preflight_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'members': 150, 'new_contest_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); a = argparse.ArgumentParser(description=__doc__); a.add_argument('mode', choices=['prepare', 'run', 'close']); mode = a.parse_args().mode
    with prev.p.m.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'close': close}[mode]()
