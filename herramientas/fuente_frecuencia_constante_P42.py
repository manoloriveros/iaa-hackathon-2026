"""Ablación estándar: Poisson guardado por peril y severidad constante correcta."""
from datetime import datetime, timezone
import argparse
import gc
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
INNER = BASE/'P28_fuente_frecuencia_marca_20261026'; FULL = BASE/'P29_fuente_frecuencia_completa_20261026'
OUT = BASE/'P42_frecuencia_marca_constante_20261026'
PLAN = R/'registro/semana2_frecuencia_marca_constante_privada_plan.json'
INDEX = R/'registro/semana2_frecuencia_marca_constante_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P42_FRECUENCIA_Y_MARCA_CONSTANTE.md'
sp = importlib.util.spec_from_file_location('p42_saved_GLM_pure', R/'herramientas/fuente_frecuencia_marca_P28.py')
m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
w = m.w; pd = m.pd; np = m.np; LINES = m.LINES
from scipy.special import logsumexp


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def constant_mark(n, c, en, ec, train):
    selected, rr, y, weight = m.p27.transformed_mark(n, c, en, ec)
    use = train[selected]; assert use.any()
    value = float(np.sum(c[selected][use]/np.sqrt(rr[use]))/np.sum(n[selected][use]*np.sqrt(rr[use])))
    independent = math.fsum(float(a*b) for a, b in zip(y[use], weight[use]))/math.fsum(weight[use])
    assert math.isclose(value, independent, rel_tol=3e-14) and value > 0
    # Mean-score condition for a Tweedie constant, including zero-cost marks.
    derivative = math.fsum(float(a*(math.sqrt(value)-b/math.sqrt(value))) for a, b in zip(weight[use], y[use]))/math.fsum(weight[use])
    assert abs(derivative) < 1e-10
    return value


def synthetic():
    n = np.array([0., 1., 2., 4., 1.]); en = np.array([.2, .3, .5, .8, 1.]); rr = np.array([.7, .8, 1.1, .6, 1.])
    c = np.array([0., 0., 400., 800., 100.]); ec = en*rr; train = np.array([True, True, True, True, False])
    a = constant_mark(n, c, en, ec, train)
    poisoned = c.copy(); poisoned[~train] = 1e15
    assert a == constant_mark(n, poisoned, en, ec, train)
    lam = np.array([.1, .7, .5, 1., 2.]); assert np.allclose(ec*lam*a, en*lam*(ec/en)*a, rtol=2e-15)
    assert math.isclose(a, constant_mark(n[::-1], c[::-1], en[::-1], ec[::-1], train[::-1]), rel_tol=3e-14)
    return {'paired_constant_mark_scalar_and_score_exact': True, 'zero_cost_positive_count_retained': True,
        'held_cost_not_in_constant': True, 'row_order_invariant': True, 'period_cost_identity_exposure_once': True, 'new_GLM_fits': 0}


def paths():
    result = [Path(__file__), Path(m.__file__), Path(m.p14.__file__), Path(m.p27.__file__),
        INNER/'report.json', INNER/'numerical_replay.json', FULL/'report.json', FULL/'completion_receipt.json',
        BASE/'P30_validacion_frecuencia_marca_20261026/completion_receipt.json',
        BASE/'P41_grafo_fuente_recuperada_20261026/completion_receipt.json', m.P27/'report.json']
    for line in LINES:
        result += [HOME/f'matrix_s1_{line}.parquet', HOME/f'rows_s1_{line}.parquet', HOME/f'partition_source/folds_{line}.parquet',
            HOME/f'matrix_s2_{line}.parquet', HOME/f'rows_s2_{line}.parquet', m.COUNTS/f'counts_{line}.parquet', m.LINKS/f'rkm_links_{line}.parquet',
            INNER/line/'preprocessor.json', INNER/line/'held_predictions.parquet', FULL/line/'preprocessor.json']
        for peril in [x['peril'] for x in w.read(m.P27/'report.json')['by_line_peril'] if x['line'] == line]:
            result.append(INNER/line/(peril+'_constant.json'))
            for folder in [INNER, FULL]: result += [folder/line/f'{line}_{peril}_frequency'/name for name in ['model.json', 'fit_record.json']]
    return result


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    OUT.mkdir(); fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Saved_peril_Poisson_frequency_with_paired_constant_mark',
        'hypothesis': 'P30whole-algorithm count/conditional-mark source failed private robustness despite favorable source context. Removing conditional severity is one simpler standard ablation, testing whether its covariate allocation is necessary; do not assume it caused the target failure.',
        'intervention': 'Retain exact saved Poisson frequency models and preprocessors: P28inner for source gate, P29full only after all gates. Replace15conditional Tweedie severity models by peril constants; no new iterative model fit, new exposure, peril selection or reciprocal ablation search.',
        'mark_formula': 'r=E_C/E_N, positiveNand positive offsets; mark0=sum(C/sqrt(r))/sum(N*sqrt(r)). Includes zeroCpositiveN. It is the weighted constant mean under P27paired Tweedie likelihood, not sumC/sumNwithout reporting correction.',
        'observed_source_cost': 'sum_peril(E_C*lambda(x)*mark0), applying effective exposure once. Annual proxy=sum_peril(lambda(x)*mark0).',
        'source_gate': 'All3lines: saved source-held total-periodT0meanTweedie1.5deviance<=1.002originalA1Sthree-seed held baseline. No seed/line/peril selection. Reuse exact P28inner mark constants and train masks; no new constants before source gate.',
        'if_pass': 'Compute15full-source mark constants only and3source relative centers; reuse15P29Poisson models, export only historical2023/2024components. Separately preregister full target comparison; no destination benefit inferred from source gate.',
        'if_fail': 'Stop without full-source constants, historical target inference, target fitting or scoring. Preserve all outcomes and no threshold/mix changes.',
        'budget': {'new_iterative_source_fits': 0, 'inner_constants_reused': 15, 'conditional_new_full_source_mark_constants': 15,
            'conditional_new_source_centers': 3, 'new_C0_fits': 0, 'new_target_fits': 0, 'new_target_scores': 0, 'new2025inference': 0, 'new_submissions': 0},
        'controls': ['Source SHAand keys, model record scopes, source-only preprocessor feature names, fixed inner groups.',
            'JSON/row-order prediction, independent exponential linear predictor samples, constant two-method scalar/score and held-cost poisoning.',
            'Source cost by scalar deviance and sklearn, replay saved gate without models/inference or resampling.',
            'Block fit functions; any scalar estimation invocation counted separately. No producer scripts that read all years or refit curves.'],
        'limits': ['Source-held CDFancestors common and already adaptive; source gate is conditional, not independent confirmation.',
            'Peril constant severity cannot capture physical capital effects; the source veto may reject it.',
            'Annual proxy depends on source count/mark reporting assumptions, does not identify true ultimate claim frequency.',
            'Private transfer, NBsupport, reporting tail/reserves and undated masters remain unproved.'],
        'sources': {w.rel(p): w.sha(p) for p in paths()}, '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. P42preinscribe una simplificación del P30fallido: conservar Poisson por peril y sustituir la severidad condicionada por una constante. No se presume que severidad explique el fallo. Veto fuente en los mismos grupos: desviación<=1,002veces el A1Soriginal en los tres ramos; si falla alguno, no hay estimación de constantes completas o aplicación destino. Las15constantes internas ya existen y se reutilizan. Fórmula corregida por reporte: sum(C/sqrt(E_C/E_N))/sum(N*sqrt(E_C/E_N)), conserva marcas de coste cero. Solo si pasan todos, máximo15medias fuente completas y3centros; cero nuevos GLM/C0, ajustes/scores destino, inferencias2025o envíos. Una sola ablación, sin elegir perils/recíprocas/pesos a posteriori. B00/F3c/alternativas conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P42-FRECUENCIA-PREVIO', '--asunto', 'P42: frecuencia guardada con severidad constante, antes del veto fuente', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P42registered_source_ablation', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps({'registered': True, 'new_GLM_fits': 0, 'forum': receipt['forum']}))


def load_line(line, full=False):
    rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'year', 'T0', 'T0_cents', 'exposure_model'])
    part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'source_group', 'internal_validation'])
    count = pd.read_parquet(m.COUNTS/f'counts_{line}.parquet'); link = pd.read_parquet(m.LINKS/f'rkm_links_{line}.parquet')
    assert all(np.array_equal(z.row_id, rows.row_id) for z in [part, count, link]) and np.array_equal(rows.T0_cents, count.T0_cents_total)
    assert rows.year.isin([2021, 2022, 2023, 2024]).all()
    train = np.ones(len(rows), dtype=bool) if full else ~part.internal_validation.to_numpy(bool)
    if not full: assert set(part.loc[train, 'source_group']).isdisjoint(set(part.loc[~train, 'source_group']))
    folder = FULL if full else INNER; prep = w.read(folder/line/'preprocessor.json')
    matrix, names = m.p14.transform(pd.read_parquet(HOME/f'matrix_s1_{line}.parquet'), prep)
    pairs = []
    for peril in [x['peril'] for x in w.read(m.P27/'report.json')['by_line_peril'] if x['line'] == line]:
        record = w.read(folder/line/f'{line}_{peril}_frequency/fit_record.json')
        assert record['scope_training_row_digest'] == m.digest(rows.loc[train, 'row_id'])
        assert record['scope_training_group_digest'] == m.digest(part.loc[train, 'source_group'].unique())
        assert record['preprocessor_sha256'] == w.sha(folder/line/'preprocessor.json') and record['columns'] == names
        model_path = folder/line/f'{line}_{peril}_frequency/model.json'; assert record['model_sha256'] == w.sha(model_path)
        model = w.read(model_path)
        n = count['N_'+peril].to_numpy(float); c = count['T0_cents_'+peril].to_numpy(float)/100
        en = link['E_count_rkm_'+peril].to_numpy(float); ec = count['E_cost_'+peril].to_numpy(float)
        if full:
            dump(OUT/f'constant_attempts/{line}_{peril}.json', {'author': 'Codex', 'utc': utc(), 'kind': 'new_full_source_scalar_mark', 'training_rows_digest': m.digest(rows.row_id)})
            mark = constant_mark(n, c, en, ec, train)
        else:
            mark = w.read(INNER/line/(peril+'_constant.json'))['mark']; check = constant_mark(n, c, en, ec, train)
            assert mark == check, 'Previously estimated mark must be reused exactly, not changed'
        pairs.append({'peril': peril, 'frequency': model, 'mark': mark, 'ec': ec})
    return rows, part, matrix, names, prep, pairs


def predict_annual(matrix, pairs):
    value = np.zeros(matrix.shape[0])
    for p in pairs: value += m.predict(matrix, p['frequency'])*p['mark']
    assert np.isfinite(value).all() and (value > 0).all(); return value


def run():
    assert not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
    def reject(*a, **kw): raise AssertionError('No iterative source model fitting in P42')
    m.coefficients = reject; m.PoissonRegressor.fit = reject; m.TweedieRegressor.fit = reject
    gates = []
    for line in LINES:
        rows, part, matrix, names, prep, pairs = load_line(line)
        held = part.internal_validation.to_numpy(bool); mu = np.zeros(held.sum())
        for p in pairs: mu += p['ec'][held]*m.predict(matrix[held], p['frequency'])*p['mark']
        old = pd.read_parquet(INNER/line/'held_predictions.parquet'); assert np.array_equal(old.row_id, rows.loc[held, 'row_id'])
        y = rows.loc[held, 'T0'].to_numpy(float); base = old.original_tree.to_numpy(float)
        a = float(m.mean_tweedie_deviance(y, mu, power=1.5)); b = float(m.mean_tweedie_deviance(y, base, power=1.5))
        scalar = math.fsum(4*c/math.sqrt(v)-8*math.sqrt(c)+4*math.sqrt(v) for c, v in zip(y, mu))/len(y)
        assert math.isclose(a, scalar, rel_tol=2e-13)
        sample = np.unique(np.linspace(0, int(held.sum())-1, 12, dtype=int)); hm = matrix[held][sample]
        for p in pairs:
            predicted = m.predict(hm, p['frequency']); model = json.loads(json.dumps(p['frequency']))
            brute = np.array([math.exp(math.fsum(row*np.asarray(model['coef']))+model['intercept']) for row in hm.toarray()])
            assert np.allclose(predicted, brute, rtol=3e-13) and np.array_equal(predicted[::-1], m.predict(hm[::-1], model))
        saved = rows.loc[held, ['row_id', 'year', 'T0']].copy(); saved['baseline'] = base; saved['candidate'] = mu
        saved.to_parquet(OUT/f'held_{line}.parquet', index=False)
        gates.append({'line': line, 'rows': len(y), 'candidate_deviance': a, 'baseline_deviance': b, 'relative_loss': a/b-1, 'pass': a <= 1.002*b})
        print(json.dumps({'source_gate': gates[-1]}), flush=True); del rows, part, matrix, pairs; gc.collect()
    passed = all(a['pass'] for a in gates); dump(OUT/'source_veto.json', {'author': 'Codex', 'utc': utc(), 'results': gates, 'all_pass': passed})
    outputs = {}
    if passed:
        for line in LINES:
            rows, part, matrix, names, prep, pairs = load_line(line, full=True)
            annual = predict_annual(matrix, pairs); weights = rows.exposure_model.to_numpy(float)
            center = float(logsumexp(np.log(annual), b=weights)-np.log(weights.sum()))
            assert abs(center-math.log(math.fsum(annual*weights)/math.fsum(weights))) < 1e-12
            target = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'year', 'is_test'])
            tx = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet'); keep = ~target.is_test
            target = target.loc[keep].reset_index(drop=True); tx = tx.loc[keep].reset_index(drop=True)
            assert target.year.isin([2023, 2024]).all()
            tm, columns = m.p14.transform(tx, prep); assert columns == names
            raw = np.log(predict_annual(tm, pairs)); sample = np.unique(np.linspace(0, len(target)-1, 24, dtype=int))
            assert np.array_equal(raw[sample], np.log(predict_annual(tm[sample], json.loads(json.dumps([{k: v for k, v in p.items() if k != 'ec'} for p in pairs])))))
            target['raw_log_rate'] = raw; target['log_relative_A1S'] = raw-center
            path = OUT/f'historical_{line}_three_seed.parquet'; target.to_parquet(path, index=False); outputs[w.rel(path)] = w.sha(path)
            dump(OUT/f'application_{line}.json', {'source_center': center, 'historical_rows': len(target), 'one_fixed_peril_sum_not_three_seeds': True,
                'constant_marks': {p['peril']: p['mark'] for p in pairs}, 'new_source_GLM_fits': 0, 'new_source_constant_marks': len(pairs), 'new2025inference': 0})
            del rows, part, matrix, pairs, tx, target, tm; gc.collect()
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
    constants = len(list(OUT.glob('constant_attempts/*.json'))); assert constants == (15 if passed else 0)
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P42source_ablation_complete_not_admitted' if passed else 'P42source_veto_failed_no_full_estimation',
        'source_veto_all_pass': passed, 'source_veto': gates, 'outputs': outputs, 'new_source_GLM_fits': 0,
        'new_source_scalar_marks': constants, 'new_source_covariate_centers': 3 if passed else 0,
        'new_C0_fits': 0, 'new_target_fits': 0, 'new_target_scores': 0, 'new2025inference': 0, 'new_submissions': 0,
        'plan_sha256': w.sha(PLAN), '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', report); print(json.dumps(report))


def close():
    assert not (OUT/'completion_receipt.json').exists(); report = w.read(OUT/'report.json'); plan = w.read(PLAN)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
    replay = []
    for a in report['source_veto']:
        frame = pd.read_parquet(OUT/f"held_{a['line']}.parquet"); y = frame.T0.to_numpy(float)
        losses = {key: math.fsum(4*c/math.sqrt(v)-8*math.sqrt(c)+4*math.sqrt(v) for c, v in zip(y, frame[key]))/len(y) for key in ['baseline', 'candidate']}
        assert math.isclose(losses['baseline'], a['baseline_deviance'], rel_tol=2e-13) and math.isclose(losses['candidate'], a['candidate_deviance'], rel_tol=2e-13)
        passed = losses['candidate'] <= 1.002*losses['baseline']; assert passed == a['pass']
        replay.append({'line': a['line'], 'scalar_deviance_matches': True, 'pass': passed})
    dump(OUT/'scalar_replay.json', {'author': 'Codex', 'utc': utc(), 'checks': replay, 'new_fits': 0, 'new_inference': 0, 'new_resampling': 0})
    passed = report['source_veto_all_pass']; next_unit = ('P43: pre-register the complete original50/50S2/H1target comparison using P42fixed frequency-only source, same scopes/guards asP39. No new source fitting/C0or future inference; reuse existing adapter checks bySHA.' if passed else
        'P43: review the remaining paired count/mark source observation assumptions and saved P30/P42source evidence before another model. Constant severity failed; do not pursue an opportunistic reciprocal ablation, relax the veto, rescue a line or increase capacity from this source result alone. Use current source-safe reference and materially new evidence, not the superseded f3_evalabsence, to choose the next concrete standard mechanism.')
    text = '# P42: frecuencia Poisson con severidad constante\n\nCodex, '+utc()+'.\n\n'
    text += ('El veto conjunto fuente pasa; se guardaron componentes históricos con15medias completas nuevas, sin refit de Poisson. Falta evaluación destino completa.' if passed else 'El veto conjunto fuente falla. No se estiman medias completas ni se infiere el histórico destino; se conserva el resultado sin elegir ramos favorables.')
    text += '\n\n| Ramo | Cambio relativo de desviación fuente | Pasa |\n|---|---:|---|\n'
    for a in report['source_veto']: text += f"| {a['line']} | {100*a['relative_loss']:+.4f}% | {a['pass']} |\n"
    text += ('\nSe conservaron los Poisson existentes y sus exposiciones de número. Las constantes de marca respetan la razón E_C/E_Ny el peso N*sqrt(r), incluidos costes cero con siniestros positivos. '
        'Las constantes internas ya calculadas se cotejaron y reutilizaron; no se contaron otra vez. Se comprobaron claves, ámbitos, JSON, predicción por suma lineal y exposición una sola vez. '
        'El cierre reproduce la desviación guardada por sumas escalares, sin aprendizaje, inferencias nuevas o remuestreo. '
        'No se atribuye automáticamente el fallo de P30a severidad ni se busca la ablación recíproca tras ver este resultado.\n\n'
        'El holdout fuente ya fue inspeccionado adaptativamente y hereda curvas fuente comunes. No es validación independiente o evidencia privada. '
        'Nuevos GLM/C0='+str(report['new_source_GLM_fits'])+'/0; medias fuente completas='+str(report['new_source_scalar_marks'])+'. Cero ajustes/scores destino, inferencias2025o envíos. '
        'B00/F3c/alternativas conservados;2024abierto adaptativo.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'scalar_replay.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P42-FRECUENCIA-RESULTADO', '--asunto', 'P42: veto de frecuencia con marca constante, sin ampliar modelos', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': report['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'source_veto_all_pass': passed, 'new_source_GLM_fits': 0, 'new_source_scalar_marks': report['new_source_scalar_marks'],
        'new_submissions': 0, 'forum': json.loads(p.stdout), 'next_unit': next_unit, '2024_open': True, 'goal_achieved': False}
    archive = R/'privado'/('corte_P42_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    cp = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(cp); assert 'phase2_private_P42_frequency_constant_mark' not in counts
    w.update(cp, {'as_of_utc': utc(), 'cumulative_closed_form_constants': counts['cumulative_closed_form_constants']+report['new_source_scalar_marks'],
        'phase2_private_P42_frequency_constant_mark': {'new_GLM_fits': 0, 'inner_mark_constants_reused': 15, 'new_full_source_mark_constants': report['new_source_scalar_marks'],
            'source_centers_separate': report['new_source_covariate_centers'], 'new_C0_fits': 0, 'new_target_scores': 0, 'report': receipt['report']}}, archive)
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P42': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P42': receipt, 'next_unit': next_unit}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']; own.update(private_P42=receipt, next_unit=next_unit)
    w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P42: frecuencia guardada y severidad constante\n\nCodex, '+receipt['utc']+'. Veto conjunto='+str(passed)+'; cero nuevos GLM/C0, '+str(report['new_source_scalar_marks'])+'medias fuente completas, cero inferencias2025/envíos. Fuente original/constantes internas reutilizadas y replay escalar verificado. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_frequency_constant_mark_index': w.rel(INDEX), 'week_2_private_frequency_constant_mark_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'source_gate_pass': passed, 'new_GLM_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); p = argparse.ArgumentParser(description=__doc__); p.add_argument('mode', choices=['prepare', 'run', 'close']); a = p.parse_args()
    with m.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'close': close}[a.mode]()
