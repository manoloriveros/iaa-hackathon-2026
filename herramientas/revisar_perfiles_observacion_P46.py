"""Recupera perfiles por peril de P43 y revisa su enlace, sin nuevos precios o scores."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.util
import json
import math
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
OUT = BASE/'P46_perfiles_observacion_20261026'
PLAN = R/'registro/semana2_perfiles_observacion_privada_plan.json'
INDEX = R/'registro/semana2_perfiles_observacion_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P46_PERFILES_Y_OBSERVACION.md'
sp = importlib.util.spec_from_file_location('p46_existing_pair_application', R/'herramientas/fuente_marca_capital_P43.py')
p = importlib.util.module_from_spec(sp); sp.loader.exec_module(p)
w = p.w; np = p.np; pd = p.pd
fp = importlib.util.spec_from_file_location('p46_existing_completion', R/'herramientas/sensibilidad_congelada_media_H1.py')
frozen = importlib.util.module_from_spec(fp); fp.loader.exec_module(frozen)


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def post(body, identifier, subject):
    a = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', identifier,
        '--asunto', subject, '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    return json.loads(a.stdout)


def weighted_q(rates, q):
    assert rates.shape == q.shape and rates.ndim == 2 and rates.shape[1] > 0
    assert np.isfinite(rates).all() and (rates > 0).all()
    assert np.isfinite(q).all() and (q >= 0).all() and (q <= 1+1e-12).all()
    result = (rates*q).sum(axis=1)/rates.sum(axis=1)
    assert np.isfinite(result).all() and (result >= 0).all() and (result <= 1+1e-12).all()
    return result


def synthetic():
    rates = np.array([[1., 3., 7.], [100., 2., 1.], [.2, .3, .4]])
    q = np.array([[0., .4, .9], [.1, 0., 1.], [.4, .4, .4]])
    v = weighted_q(rates, q)
    scalar = np.array([math.fsum(float(a)*float(b) for a, b in zip(rr, qq))/math.fsum(rr.tolist()) for rr, qq in zip(rates, q)])
    assert np.allclose(v, scalar, rtol=2e-15) and math.isclose(v[2], .4, rel_tol=2e-15)
    assert np.allclose(weighted_q(rates*123.4, q), v, rtol=2e-15)
    zero = weighted_q(rates, np.zeros_like(q)); assert np.array_equal(zero, np.zeros(3))
    exposure = np.array([.2, .8, 1.]); lhs = exposure*(rates*q).sum(axis=1); rhs = exposure*rates.sum(axis=1)*v
    assert np.allclose(lhs, rhs, rtol=2e-15)
    for rr, qq in [(rates*0, q), (rates, q+2), (rates, q-2), (rates, q*np.nan)]:
        try: weighted_q(rr, qq)
        except AssertionError: pass
        else: raise AssertionError('Invalid profile accepted')
    return {'author': 'Codex', 'utc': utc(), 'sum_of_peril_observation_equals_common_cost_link': True,
        'scalar_and_scale_invariance': True, 'equal_q_and_legitimate_zero_q': True, 'invalid_controls_rejected': 4,
        'new_fits': 0, 'contest_inference': 0, 'limits': 'Conditional identity under proposed ultimate-risk weights; does not identify true ultimate composition.'}


def perils_by_line():
    d = w.read(p.m.P27/'report.json')['by_line_peril']
    return {line: [x['peril'] for x in d if x['line'] == line] for line in p.LINES}


def c0_path(evaluation, line, outer):
    return (BASE/f'tanda2_20261025_v1/learning_{line}_fold{outer}.json' if evaluation == 'POOLED' else
        BASE/f'P4_transferencia_anual_H1_20261026_v1/scope_{line}_outer{outer}_member-1/primary/C0.json')


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json'); assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert (BASE/'P45_mezcla_fija_20261026/completion_receipt.json').exists()
    OUT.mkdir(); dump(OUT/'synthetic.json', synthetic())
    source = w.read(p.OUT/'report.json'); assert source['source_veto_all_pass'] and source['new_source_GLM_fits'] == 30
    assert w.read(p.OUT/'completion_receipt.json')['report_sha256'] == w.sha(p.OUT/'report.json')
    paths = [Path(__file__), Path(p.__file__), Path(p.m.__file__), Path(p.m.p14.__file__), Path(frozen.__file__),
        R/'src/semana2/variables_ultimo.py', R/'registro/semana2_marca_capital_privada_plan.json',
        p.OUT/'report.json', p.OUT/'completion_receipt.json', p.m.P27/'report.json', OUT/'synthetic.json',
        BASE/'P31_compatibilidad_puente_20261026/report.json', BASE/'P45_mezcla_fija_20261026/completion_receipt.json']
    for line, perils in perils_by_line().items():
        paths += [HOME/f'matrix_s2_{line}.parquet', HOME/f'rows_s2_{line}.parquet', p.FULL/line/'preprocessor.json',
            p.OUT/f'historical_{line}_three_seed.parquet', p.OUT/f'application_{line}.json',
            BASE/f'preflight_anidado_H1_20261026_v1/canonical_{line}.parquet']
        for peril in perils:
            paths += [p.FULL/line/f'{line}_{peril}_frequency'/k for k in ['model.json', 'fit_record.json']]
            paths += [p.OUT/line/f'{peril}_full'/k for k in ['model.json', 'fit_record.json', 'controls.json']]
        for evaluation in ['POOLED', 'TRANSFER']:
            paths += [c0_path(evaluation, line, k) for k in range(5)]
    plan = {'author': 'Codex', 'utc': utc(), 'status': 'P46registered_no_new_fit_or_target_score',
        'question': 'Does the newly fitted P43paired GLM imply materially different peril-specific observation weights than the original FSp profile kept in P44?',
        'new_evidence': 'P43 full reduced-mark coefficients and their current paired count observation contract did not exist at HET/P31. P31 identified that historical aggregate caches discard per-peril rates. Recover precisely this missing object; do not repeat old FSp/HET diagnostics or source fits.',
        'scope': 'Historical emerging2023/2024covariates only for source coefficient application,109296rows. Thirty saved outer C0 scopes; report held rows only. No2025model inference or candidate prices.',
        'observed_link': 'q_new_i=sum_p(lambda_ip*mark_ip*q_ip)/sum_p(lambda_ip*mark_ip). q_ip is the SAME saved outer C0cost-completion average; no target kappa, C0refit, calibration or fitted mix.',
        'comparator': 'Existing FSp f*s risk-weighted q_source in the SAME canonical row and outer C0. Compare completion ratios, not losses or prices. All source/cache parents remain unchanged.',
        'screen': {'ratio_threshold': 1.05, 'fraction_in_cell': .05,
            'interpretation': 'Same descriptive5percent/5percent screen as prior link review. A material difference justifies reviewing a new observation recipe, not claiming improvement or adopting GLM weights.'},
        'controls': ['Full model JSON/fit-record/preprocessor SHA and recorded columns.', 'Historical per-peril sum reconstructs exact P43raw log annual cache within2e-13relative tolerance.',
            'Canonical keys/year/source rate keys; outer fit_row_ids exactly training group scope, held groups excluded.',
            'Numerical scalar dot products/logsumexp, scale invariance, equal completion and legitimate zero-peril completion.',
            'No response/outcome fields enter profile or completion functions; poison historical T0/reserve without changing them.'],
        'budget': {'new_source_coefficient_applications': 15, 'new_source_fits': 0, 'new_target_fits': 0, 'new_C0_fits': 0,
            'new_constants': 0, 'new_candidate_prices': 0, 'new_scores': 0, 'new2025inference': 0, 'new_submissions': 0},
        'sources': {w.rel(k): w.sha(k) for k in paths}, 'perils': perils_by_line(),
        'limits': ['Source coefficients/reporting contract conditional on developed2021-2024; not proven prospective2023availability.',
            'A changed peril mix remains a modeling assumption and does not solve undated masters, reserves or unidentified late tail.',
            'A subsequent coherent complete algorithm must address training observation exposure, ultimate forward and every H1member scope; substituting q only at scoring is not sufficient.',
            'No automatic re-estimation or recipe test follows from a materiality screen. Prior HET/P30/P44/P45adverses remain.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan); body = OUT/'forum_previo.md'
    body.write_text('Codex. P46 registra una carencia concreta, no otra variante de capacidad: P31 conservó el perfil FSp porque el caché GLM solo guardaba la suma. Los nuevos coeficientes pareados y marcas reducidas P43 permiten recuperar sus quince tasas por peril. Se exportarán en2023/2024 y se cotejará la suma con el caché exacto antes de revisar la completitud que implican sobre los mismos treinta C0exteriores. Solo diferencias de q, por ramo/año/negocio y pantalla descriptiva5%/5% fijada; no precios, scores, kappas o niveles. Quince aplicaciones de coeficientes existentes, cero ajustes fuente/destino/C0, inferencias2025 o envíos. No se adopta la nueva mezcla como verdad última: un eventual modelo tendría que revisar exposición de aprendizaje, avance a último y todos los miembros H1 antes de puntuar. B00/F3c/adversos conservados;2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P46registered_before_profile_export', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': post(body, 'COD-S2-20261026-PRIVADA-P46-PERFILES-PREVIO', 'P46: recuperar perfiles GLM por peril antes de otra prueba de observación')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
    # Explicitly block producer fit functions. JSON matrix products are the only new model applications.
    def reject(*a, **kw): raise AssertionError('No estimation in P46')
    p.fit = reject; p.m.coefficients = reject; p.m.fit = reject
    results = []; checks = []; outputs = {}
    for line in p.LINES:
        rows = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'year', 'is_test'])
        keep = (~rows.is_test & rows.year.isin([2023, 2024])).to_numpy(); selected = rows.loc[keep].reset_index(drop=True)
        # Matrix storage has no year keys. Select known historical positions BEFORE preprocessing/inference.
        matrix = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet').iloc[np.flatnonzero(keep)].reset_index(drop=True)
        prep = w.read(p.FULL/line/'preprocessor.json'); design, names = p.m.p14.transform(matrix, prep)
        capital, cap_names = p.select_capital(design, names, line); rates = []; perils = plan['perils'][line]
        for peril in perils:
            ff = p.FULL/line/f'{line}_{peril}_frequency'; mm = p.OUT/line/f'{peril}_full'
            freq = w.read(ff/'model.json'); mark = w.read(mm/'model.json')
            assert w.read(ff/'fit_record.json')['model_sha256'] == w.sha(ff/'model.json') and w.read(ff/'fit_record.json')['columns'] == names
            record = w.read(mm/'fit_record.json'); assert record['model_sha256'] == w.sha(mm/'model.json') and record['features'] == cap_names
            assert record['preprocessor_sha256'] == w.sha(p.FULL/line/'preprocessor.json')
            rates.append(p.m.predict(design, freq)*p.m.predict(capital, mark))
        rate = np.column_stack(rates); total = rate.sum(axis=1)
        old = pd.read_parquet(p.OUT/f'historical_{line}_three_seed.parquet')
        assert np.array_equal(selected.row_id, old.row_id) and np.array_equal(selected.year, old.year) and not selected.is_test.any()
        error = float(np.max(np.abs(total/np.exp(old.raw_log_rate.to_numpy())-1)))
        assert error < 2e-13
        profile = selected.copy()
        for j, peril in enumerate(perils): profile['annual_'+peril] = rate[:, j]
        path = OUT/f'peril_rates_{line}.parquet'; profile.to_parquet(path, index=False); outputs[w.rel(path)] = w.sha(path)
        canonical = pd.read_parquet(BASE/f'preflight_anidado_H1_20261026_v1/canonical_{line}.parquet')
        assert canonical.row_id.is_unique and set(canonical.row_id) == set(profile.row_id)
        rate_frame = profile.set_index('row_id'); assert np.array_equal(rate_frame.loc[canonical.row_id].year, canonical.year)
        for evaluation in ['POOLED', 'TRANSFER']:
            for outer in range(5):
                c0 = w.read(c0_path(evaluation, line, outer)); c0 = c0['artifact']['C0'] if evaluation == 'POOLED' else c0
                train = canonical.fold.ne(outer) & (True if evaluation == 'POOLED' else canonical.year.eq(2023))
                held = canonical.fold.eq(outer) & (True if evaluation == 'POOLED' else canonical.year.eq(2024))
                assert c0['fit_row_ids'] == sorted(canonical.loc[train, 'row_id'])
                assert set(canonical.loc[train, 'group_id']).isdisjoint(set(canonical.loc[held, 'group_id']))
                f = canonical.loc[held].copy(); ordered_perils = sorted(c0['curves']); assert set(ordered_perils) == set(perils)
                q = np.column_stack([frozen.v.average_completion(f, c0['curves'][name], 'cost', 1.) for name in ordered_perils])
                rr = rate_frame.loc[f.row_id, ['annual_'+name for name in ordered_perils]].to_numpy(float)
                qnew = weighted_q(rr, q); _, qold = frozen.completion(f, c0)
                assert (qold > 0).all() and (qnew > 0).all(); ratio = qnew/qold
                take = np.unique(np.linspace(0, len(f)-1, 24, dtype=int)); scalar = [math.fsum(float(v)*float(z) for v, z in zip(rr[i], q[i]))/math.fsum(rr[i].tolist()) for i in take]
                assert np.allclose(qnew[take], scalar, rtol=3e-15)
                bad = f.assign(T0=-1e30, reserve=1e30); qbad = np.column_stack([frozen.v.average_completion(bad, c0['curves'][name], 'cost', 1.) for name in ordered_perils])
                assert np.array_equal(q, qbad) and np.array_equal(qnew, weighted_q(rr, qbad))
                out = f[['row_id', 'line', 'year', 'new_business', 'fold', 'group_id']].copy()
                out['q_FSp'] = qold; out['q_GLM'] = qnew; out['ratio'] = ratio
                path = OUT/f'{evaluation}_{line}_{outer}_completion.parquet'; out.to_parquet(path, index=False); outputs[w.rel(path)] = w.sha(path)
                for (year, nb), ix in out.groupby(['year', 'new_business']).groups.items():
                    z = out.loc[ix, 'ratio'].to_numpy(); fraction = float(np.mean((z > 1.05)|(z < 1/1.05)))
                    results.append({'evaluation': evaluation, 'line': line, 'outer': outer, 'year': int(year), 'NB': int(nb), 'rows': len(z),
                        'ratio_quantiles_p0_p05_p50_p95_p100': np.quantile(z, [0, .05, .5, .95, 1]).tolist(),
                        'fraction_outside_5pct': fraction, 'material_screen': fraction >= .05})
        checks.append({'line': line, 'historical_rows': len(selected), 'source_peril_applications': len(perils), 'source_sum_max_relative_error': error,
            'scalar_q_and_held_outcome_poison_pass': True, 'outer_C0_training_keys_groups_exact': True})
    assert all(w.sha(ROOT/k) == v for k, v in plan['sources'].items())
    dump(OUT/'report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P46peril_profiles_and_completion_review_complete', 'plan_sha256': w.sha(PLAN),
        'checks': checks, 'cells': results, 'material_cells': sum(x['material_screen'] for x in results), 'cell_count': len(results), 'outputs': outputs,
        'new_source_coefficient_applications': 15, 'new_fits': 0, 'new_C0_fits': 0, 'new_constants': 0, 'new_prices': 0, 'new_scores': 0,
        'new2025inference': 0, 'new_submissions': 0, 'adopted': False, 'private_improvement_established': False, '2024_open': True, 'goal_achieved': False})
    print(json.dumps({'complete': True, 'material_cells': sum(x['material_screen'] for x in results), 'cells': len(results), 'checks': checks, 'new_fits': 0, 'new_scores': 0}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); d = w.read(OUT/'report.json')
    assert d['plan_sha256'] == w.sha(PLAN) and all(w.sha(ROOT/k) == v for k, v in d['outputs'].items())
    next_unit = ('P47: prepare a coherent paired-profile observation contract using these exported P43peril rates and each already fitted C0scope. Before any new target fit or score, map every required outer/inner member to its own protected C0and original global groups; prove synthetic whole learning/exposure/ultimate/mean/observation invariance. Define whether the source component alone changes or a new whole target algorithm, with explicit original reference, fixed configuration/cost and all gates. Do not merely replace q at scoring or reuse outer C0inside inner learners. This review authorizes no automatic fit, new curves, weights or upload.' if d['material_cells'] else
        'Peril-profile completion screen found no material cells under frozen5percent/5percent rule; do not launch an observation-change recipe from this review. Preserve exported rates and investigate a distinct materially supported target uncertainty, no repeated HETorC0audits on unchanged inputs.')
    text = '# P46: perfiles por peril y enlace de observación\n\nCodex, '+utc()+'. Se recuperaron las quince tasas anuales por peril de los coeficientes P43 ya guardados. Su suma reproduce el caché agregado original, sin volver a entrenar o centrar.\n\n'
    text += 'La revisión responde a la carencia concreta registrada en P31: la suma GLM no identificaba los pesos internos y el enlace seguía usando el perfil FSp. No se repitió el ajuste HET ni se midió otro rendimiento predictivo. Se comparó q_GLM frente a q_FSp con los mismos treinta C0 exteriores y solo sus filas retenidas2023/2024. Se verificaron las claves de entrenamiento/exclusión por grupos, sumas escalares, ceros legítimos y la invariancia a alterar T0/reservas retenidos.\n\n'
    text += f"La pantalla descriptiva prefijada (diferencia multiplicativa mayor del5%en al menos5%de una celda ramo/fold/año/negocio) se cumple en {d['material_cells']} de {d['cell_count']} celdas. Esto muestra que los perfiles implican una observación distinta; no identifica cuál representa la verdadera mezcla última ni demuestra una mejora.\n\n| Ámbito | Ramo | Celdas materiales / revisadas |\n|---|---|---:|\n"
    for evaluation in ['POOLED', 'TRANSFER']:
        for line in p.LINES:
            z = [x for x in d['cells'] if x['evaluation'] == evaluation and x['line'] == line]
            text += f"| {evaluation} | {line} | {sum(x['material_screen'] for x in z)} / {len(z)} |\n"
    text += '\nQuince aplicaciones de coeficientes fuente existentes sobre109.296filas históricas; cero ajustes fuente/destino/C0, constantes nuevas, precios, scores, inferencias2025 o envíos. B00, F3c y todos los adversos permanecen.2024 es desarrollo abierto adaptativo; fuente2024, maestros sin fecha y reservas/cola siguen como límites. Las identidades de mezcla son condicionales al modelo, no una verdad última o revisión profesional independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; los artefactos por fila permanecen privados.\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': d['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'material_cells': d['material_cells'], 'cell_count': d['cell_count'], 'new_source_coefficient_applications': 15,
        'new_fits': 0, 'new_C0_fits': 0, 'new_constants': 0, 'new_prices': 0, 'new_scores': 0, 'new2025inference': 0, 'new_submissions': 0,
        'next_unit': next_unit, '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False,
        'forum': post(body, 'COD-S2-20261026-PRIVADA-P46-PERFILES-RESULTADO', 'P46: perfiles recuperados y diferencia de observación, sin nuevos scores')}
    archive = R/'privado'/('corte_P46_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P46': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P46': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P46=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P46: perfiles por peril recuperados\n\nCodex, '+receipt['utc']+f". Tasas P43 recuperadas por15aplicaciones de coeficientes; pantalla descriptiva material en {d['material_cells']}/{d['cell_count']}celdas con C0exterior propio. Cero ajustes/C0/precios/scores/inferencias2025/envíos. No se identifica la verdadera mezcla última. Informe: "+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_peril_observation_index': w.rel(INDEX), 'week_2_private_peril_observation_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'material_cells': d['material_cells'], 'new_scores': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); a = argparse.ArgumentParser(description=__doc__); a.add_argument('mode', choices=['prepare', 'run', 'close']); mode = a.parse_args().mode
    with p.m.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'close': close}[mode]()
