"""Poisson fijo y marca Tweedie reducida al valor asegurado, por peril."""
from datetime import datetime, timezone
import argparse
import gc
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
INNER = BASE/'P28_fuente_frecuencia_marca_20261026'; FULL = BASE/'P29_fuente_frecuencia_completa_20261026'
OUT = BASE/'P43_marca_capital_20261026'
PLAN = R/'registro/semana2_marca_capital_privada_plan.json'
INDEX = R/'registro/semana2_marca_capital_privada_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P43_MARCA_SOLO_CAPITAL.md'
sp = importlib.util.spec_from_file_location('p43_glm_math', R/'herramientas/fuente_frecuencia_marca_P28.py')
m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
w = m.w; np = m.np; pd = m.pd; LINES = m.LINES
from scipy.special import logsumexp
CAPITAL = {'motor': 'vehicle_value_group', 'buildings': 'log_si', 'contents': 'log_si'}


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def select_capital(matrix, names, line):
    field = CAPITAL[line]; selected = [field]+([field+'__is_missing'] if field+'__is_missing' in names else [])
    assert all(names.count(c) == 1 for c in selected)
    return matrix[:, [names.index(c) for c in selected]], selected


def mark_payload(n, c, en, ec, train, matrix):
    chosen, ratio, y, weight = m.p27.transformed_mark(n[train], c[train], en[train], ec[train])
    positions = np.flatnonzero(train)[chosen]
    return matrix[positions], y, weight, positions


def paths():
    result = [Path(__file__), Path(m.__file__), Path(m.p14.__file__), Path(m.p27.__file__), m.P27/'report.json',
        INNER/'report.json', INNER/'numerical_replay.json', FULL/'report.json', FULL/'completion_receipt.json',
        BASE/'P30_validacion_frecuencia_marca_20261026/completion_receipt.json', BASE/'P42_frecuencia_marca_constante_20261026/report.json',
        BASE/'P42_frecuencia_marca_constante_20261026/completion_receipt.json',
        R/'src/semana2/lineas/ml_independiente_20261023/codigo/e25_severidad.py', R/'registro/semana2_desarrollo2023_plan_v6.json']
    for line in LINES:
        result += [HOME/f'matrix_s1_{line}.parquet', HOME/f'rows_s1_{line}.parquet', HOME/f'partition_source/folds_{line}.parquet',
            HOME/f'matrix_s2_{line}.parquet', HOME/f'rows_s2_{line}.parquet', m.COUNTS/f'counts_{line}.parquet', m.LINKS/f'rkm_links_{line}.parquet',
            INNER/line/'preprocessor.json', INNER/line/'held_predictions.parquet', FULL/line/'preprocessor.json']
        for p in [a['peril'] for a in w.read(m.P27/'report.json')['by_line_peril'] if a['line'] == line]:
            for folder in [INNER, FULL]: result += [folder/line/f'{line}_{p}_frequency'/k for k in ['model.json', 'fit_record.json']]
    return result


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists(); assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    assert not w.read(BASE/'P42_frecuencia_marca_constante_20261026/report.json')['source_veto_all_pass']
    OUT.mkdir()
    from scipy.sparse import csr_matrix
    toy = csr_matrix(np.arange(18, dtype=float).reshape(6, 3)); z, cols = select_capital(toy, ['unrelated', 'log_si', 'log_si__is_missing'], 'buildings')
    assert cols == ['log_si', 'log_si__is_missing'] and np.array_equal(z.toarray(), toy.toarray()[:, [1, 2]])
    dump(OUT/'selection_fixture.json', {'only_prespecified_capital_and_its_missing_flag_selected': True, 'no_GLM_fit': True})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Saved_Poisson_plus_capital_only_Tweedie_mark_peril',
        'hypothesis': 'P42constant mark lost1.01%inbuildings and1.69%incontents source deviance, so a constant was inadequate under the frozen source gate. Retain one physically motivated value predictor while reducing P30high-dimensional conditional marks. This does not prove capital caused the loss or that it will transport.',
        'prior_scope': 'Capital main effects and sourceGamma/FS severity already studied, including2023capital audits and E25larger Gamma-tree search. This is a reduced paired E_C/E_Nsource2021-2024Tweedie mark under current observed-count semantics, not a first capital/severity idea or repeat of their configuration.',
        'frequency': 'Exact existing P28inner/P29full Poisson models and source preprocessor; no new frequency fitting or curves.',
        'mark_predictors': CAPITAL, 'feature_rule': 'Exactly the prespecified standardized source value field and its original P14missing indicator if present, plus intercept. No age/broker/NCB/region/weather/history, feature screening, polynomial, interactions or value exponent search. Reuse exact source-scope medians/clips/scales fromP28/P29.',
        'mark_objective': 'Same P27paired likelihood: response C/(N*r), r=E_C/E_N; weight=N*sqrt(r). PositiveNwith positive offsets; zeroCkept. Tweedie1.5log-link, nominalalpha1 rescaled as sumN/sum(N*sqrt(r)), exact P28solver max3000tol1e-7, no tuning.',
        'source_gate': 'All3lines: held total-period sum(E_C*lambda*mark) meanTweedie1.5deviance<=1.002originalA1Sthree-seed held baseline; original source group masks. Any failure stops all full refits/target application. No source-family reciprocal ablation or favorable-line/peril rescue.',
        'if_pass': '15full-source reduced mark GLMs only, same configuration, no frequency re-fit. Three source centers and historical2023/2024components. Separate whole-target preregistration retains all global/business/transfer/tail/influence gates.',
        'budget': {'inner_mark_GLM_fits': 15, 'conditional_full_mark_GLM_fits': 15, 'max_new_source_GLM_fits': 30,
            'new_frequency_fits': 0, 'new_C0_fits': 0, 'new_target_fits': 0, 'new_target_scores': 0, 'new2025inference': 0, 'new_submissions': 0},
        'controls': ['Exact source/group/key and frequency-model hashes; selected feature columns recorded per fit.',
            'Fit payload constructed from training rows before mark transformations; held cost/count poisoning leaves actual arguments identical.',
            'Every actual fit invocation counted; saveJSONbefore numerical controls, no automatic repeat of a partial invocation.',
            'Gradient threshold1e-4, first peril perline finite differences, save/load/reversal/manual linear predictor checks.',
            'Source loss and saved output replay by scalar math; unchanged objective checks reused, no new synthetic model fits.'],
        'sources': {w.rel(p): w.sha(p) for p in paths()}, 'limits': ['Adaptive conditional source holdout and common sourceCDFancestry; no independent confirmation.',
            'Capital normalization/undated vintages and market transport assumptions persist; motor valuegroup is ordinal, not exact vehicle monetary value.',
            'This reduces the existing multivariate mark model; it does not remove the need for target robustness or repair P30by assertion.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. P43preinscribe severidad reducida al valor asegurado, tras el veto fuente de severidad constante P42. Se conservan todos los Poisson; las marcas usan solo vehicle_value_groupenautos ylog_sienhogar, con su indicador de ausencia original si existe. Es una reducción del modelo P30, no una búsqueda de interacciones o árboles. No se presume capital como causa demostrada. Mismo objetivo pareado, cero marcas positivas descartadas por coste cero, alpha1normalizado y solver original.15GLMinternos; solo si todos los ramos pasan desviación<=1,002veces A1S,15refits de marca y componentes históricos. Máximo30GLMfuente, cero frecuencia/C0, ajuste/score destino, inferencia2025o envíos. B00/F3c/alternativas conservados,2024abierto. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P43-MARCA-CAPITAL-PREVIO', '--asunto', 'P43: marca con un predictor de valor, Poisson fijo y veto previo', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P43registered_reduced_mark', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps({'registered': True, 'max_fits': 30, 'forum': receipt['forum']}))


def state(status, execution):
    archive = R/'privado'/('p43_state_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    attempted = sorted(p.parent.relative_to(OUT).as_posix() for p in OUT.glob('*/*/fit_invoked.json'))
    completed = sorted(p.parent.relative_to(OUT).as_posix() for p in OUT.glob('*/*/fit_record.json'))
    assert len(attempted) == len(set(attempted))
    cp = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(cp); old = counts.get('phase2_private_P43_capital_mark', {}).get('counted_fit_keys', [])
    assert set(old).issubset(attempted); added = len(set(attempted)-set(old))
    phasepath = R/'registro/semana2_mision017_fase2_actual.json'; phase = w.read(phasepath)
    current = {'author': 'Codex', 'utc': utc(), 'status': status, 'plan': w.rel(PLAN), 'attempts': len(attempted), 'completed': len(completed), 'execution': execution, 'new_C0_fits': 0, 'new2025inference': 0, 'new_submissions': 0}
    w.update(cp, {'as_of_utc': utc(), 'cumulative_price_base_fits': counts['cumulative_price_base_fits']+added,
        'phase2_private_P43_capital_mark': {'counted_fit_keys': attempted, 'attempts': len(attempted), 'completed': len(completed), 'new_frequency_fits': 0, 'plan': w.rel(PLAN)}}, archive)
    w.update(INDEX, current, archive); jobs = [] if execution is None else [execution]
    w.update(phasepath, {'private_P43': current, 'new_price_fits': phase['new_price_fits']+added, 'active_execution': execution, 'active_jobs': jobs}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P43=current, active_jobs=jobs)
    w.update(path, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': execution}, archive)


def compose(matrix, cap, pairs):
    total = np.zeros(matrix.shape[0])
    for p in pairs: total += m.predict(matrix, p['frequency'])*m.predict(cap, p['mark'])
    assert np.isfinite(total).all() and (total > 0).all(); return total


def fit(folder, mat, y, weight, meta, first=False):
    assert not (folder/'fit_invoked.json').exists(), 'Reconcile partial invocation; no automatic refit'
    dump(folder/'fit_invoked.json', {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'plan_sha256': w.sha(PLAN), **meta})
    execution = {'author': 'Codex', 'pid': os.getpid(), 'script': w.rel(Path(__file__)), 'checkpoint': folder.parent.name+'/'+folder.name, 'kind': 'P43reduced_source_mark'}
    state('P43mark_training_running', execution); start = time.monotonic()
    model, estimator = m.coefficients(mat, y, weight, 'mark', meta['alpha'])
    dump(folder/'model.json', model); dump(folder/'fit_record.json', {'utc': utc(), 'seconds': time.monotonic()-start, 'model_sha256': w.sha(folder/'model.json'), 'plan_sha256': w.sha(PLAN), **meta})
    checked = m.controls(mat, y, weight, model, estimator, finite_difference=first); dump(folder/'controls.json', checked)
    state('P43mark_saved_and_checked', execution); print(json.dumps({'completed': folder.parent.name+'/'+folder.name, 'seconds': round(time.monotonic()-start, 2)}), flush=True)
    return model


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists(); plan = w.read(PLAN)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}; dump(OUT/'started.json', {'utc': utc(), 'pid': os.getpid()})
    outputs = {}; gates = []
    try:
        for full in [False, True]:
            if full and not all(a['pass'] for a in gates): break
            parent = FULL if full else INNER; kind = 'full' if full else 'inner'
            for line in LINES:
                rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'year', 'T0', 'T0_cents', 'exposure_model'])
                part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'source_group', 'internal_validation'])
                count = pd.read_parquet(m.COUNTS/f'counts_{line}.parquet'); link = pd.read_parquet(m.LINKS/f'rkm_links_{line}.parquet')
                assert all(np.array_equal(z.row_id, rows.row_id) for z in [part, count, link]) and np.array_equal(rows.T0_cents, count.T0_cents_total)
                held = part.internal_validation.to_numpy(bool); train = np.ones(len(rows), dtype=bool) if full else ~held
                if not full: assert set(part.loc[train, 'source_group']).isdisjoint(set(part.loc[held, 'source_group']))
                prep = w.read(parent/line/'preprocessor.json'); matrix, names = m.p14.transform(pd.read_parquet(HOME/f'matrix_s1_{line}.parquet'), prep)
                cap, features = select_capital(matrix, names, line); pairs = []; mu = np.zeros(held.sum())
                perils = [a['peril'] for a in w.read(m.P27/'report.json')['by_line_peril'] if a['line'] == line]
                for j, peril in enumerate(perils):
                    freqpath = parent/line/f'{line}_{peril}_frequency/model.json'; freqrecord = w.read(freqpath.parent/'fit_record.json')
                    assert freqrecord['model_sha256'] == w.sha(freqpath) and freqrecord['scope_training_row_digest'] == m.digest(rows.loc[train, 'row_id'])
                    assert freqrecord['scope_training_group_digest'] == m.digest(part.loc[train, 'source_group'].unique()) and freqrecord['columns'] == names
                    frequency = w.read(freqpath)
                    n = count['N_'+peril].to_numpy(float); c = count['T0_cents_'+peril].to_numpy(float)/100
                    en = link['E_count_rkm_'+peril].to_numpy(float); ec = count['E_cost_'+peril].to_numpy(float)
                    mat, y, weight, positions = mark_payload(n, c, en, ec, train, cap)
                    nn = n.copy(); cc = c.copy(); nn[~train] = 1e8; cc[~train] = 1e15
                    poisoned = mark_payload(nn, cc, en, ec, train, cap)
                    assert np.array_equal(y, poisoned[1]) and np.array_equal(weight, poisoned[2]) and np.array_equal(positions, poisoned[3]) and (mat != poisoned[0]).nnz == 0
                    alpha = float(n[positions].sum()/weight.sum()); folder = OUT/line/f'{peril}_{kind}'
                    meta = {'line': line, 'peril': peril, 'kind': kind, 'features': features, 'rows': len(y), 'alpha': alpha,
                        'scope_training_row_digest': m.digest(rows.loc[train, 'row_id']), 'fit_row_digest': m.digest(rows.iloc[positions].row_id),
                        'fit_group_digest': m.digest(part.iloc[positions].source_group.unique()), 'preprocessor_sha256': w.sha(parent/line/'preprocessor.json'),
                        'held_count_cost_fit_arguments_invariant': True}
                    mark = fit(folder, mat, y, weight, meta, first=j == 0); pairs.append({'peril': peril, 'frequency': frequency, 'mark': mark})
                    if not full: mu += ec[held]*m.predict(matrix[held], frequency)*m.predict(cap[held], mark)
                if not full:
                    old = pd.read_parquet(INNER/line/'held_predictions.parquet'); assert np.array_equal(old.row_id, rows.loc[held, 'row_id'])
                    y = rows.loc[held, 'T0'].to_numpy(float); baseline = old.original_tree.to_numpy(float)
                    a = float(m.mean_tweedie_deviance(y, mu, power=1.5)); b = float(m.mean_tweedie_deviance(y, baseline, power=1.5))
                    frame = rows.loc[held, ['row_id', 'year', 'T0']].copy(); frame['baseline'] = baseline; frame['candidate'] = mu
                    frame.to_parquet(OUT/f'held_{line}.parquet', index=False)
                    gates.append({'line': line, 'rows': len(y), 'candidate_deviance': a, 'baseline_deviance': b, 'relative_loss': a/b-1, 'pass': a <= 1.002*b})
                    print(json.dumps({'source_gate': gates[-1]}), flush=True)
                else:
                    annual = compose(matrix, cap, pairs); weights = rows.exposure_model.to_numpy(float)
                    center = float(logsumexp(np.log(annual), b=weights)-np.log(weights.sum()))
                    assert abs(center-math.log(math.fsum(annual*weights)/math.fsum(weights))) < 1e-12
                    target = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'year', 'is_test']); tx = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet')
                    keep = ~target.is_test; target = target.loc[keep].reset_index(drop=True); tx = tx.loc[keep].reset_index(drop=True)
                    assert target.year.isin([2023, 2024]).all(); tm, cols = m.p14.transform(tx, prep); tc, fs = select_capital(tm, cols, line); assert cols == names and fs == features
                    raw = np.log(compose(tm, tc, pairs)); sample = np.unique(np.linspace(0, len(target)-1, 24, dtype=int))
                    assert np.array_equal(raw[sample], np.log(compose(tm[sample], tc[sample], json.loads(json.dumps(pairs)))))
                    target['raw_log_rate'] = raw; target['log_relative_A1S'] = raw-center; path = OUT/f'historical_{line}_three_seed.parquet'
                    target.to_parquet(path, index=False); outputs[w.rel(path)] = w.sha(path)
                    dump(OUT/f'application_{line}.json', {'source_center': center, 'historical_rows': len(target), 'features': features, 'one_peril_sum_not_three_seeds': True, 'new2025inference': 0})
                    del target, tx, tm, tc
                del rows, part, count, link, matrix, cap, pairs; gc.collect()
            if not full: dump(OUT/'source_veto.json', {'author': 'Codex', 'utc': utc(), 'results': gates, 'all_pass': all(a['pass'] for a in gates)})
        assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}
        passed = all(a['pass'] for a in gates); attempts = len(list(OUT.glob('*/*/fit_invoked.json')))
        assert attempts == len(list(OUT.glob('*/*/controls.json'))) == (30 if passed else 15)
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P43reduced_mark_source_complete_not_admitted' if passed else 'P43source_veto_failed_no_full_refit',
            'source_veto_all_pass': passed, 'source_veto': gates, 'new_source_GLM_fits': attempts, 'new_frequency_fits': 0, 'new_C0_fits': 0,
            'new_target_fits': 0, 'new_target_scores': 0, 'new2025inference': 0, 'new_submissions': 0, 'source_centers': 3 if passed else 0,
            'outputs': outputs, 'plan_sha256': w.sha(PLAN), '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False}
        dump(OUT/'report.json', report); state(report['status'], None); print(json.dumps(report))
    finally:
        if not (OUT/'report.json').exists(): state('P43unfinished_reconcile_saved_attempts', None)


def close():
    assert not (OUT/'completion_receipt.json').exists(); report = w.read(OUT/'report.json'); plan = w.read(PLAN)
    assert plan['sources'] == {w.rel(p): w.sha(p) for p in paths()}; replay = []
    for a in report['source_veto']:
        frame = pd.read_parquet(OUT/f"held_{a['line']}.parquet"); y = frame.T0.to_numpy(float)
        loss = {k: math.fsum(4*c/math.sqrt(v)-8*math.sqrt(c)+4*math.sqrt(v) for c, v in zip(y, frame[k]))/len(y) for k in ['baseline', 'candidate']}
        assert math.isclose(loss['baseline'], a['baseline_deviance'], rel_tol=2e-13) and math.isclose(loss['candidate'], a['candidate_deviance'], rel_tol=2e-13)
        replay.append({'line': a['line'], 'scalar_loss_exact': True})
    for p in OUT.glob('*/*/fit_record.json'):
        record = w.read(p); assert record['model_sha256'] == w.sha(p.parent/'model.json') and (p.parent/'controls.json').exists()
    dump(OUT/'scalar_replay.json', {'author': 'Codex', 'utc': utc(), 'replay': replay, 'new_fits': 0, 'new_inference': 0, 'new_resampling': 0})
    passed = report['source_veto_all_pass']; next_unit = ('P44: preregister complete original50/50S2/H1comparison with P43reduced marks, same30scopes and all P39global/business/family16gates; reuse source frequencies/C0and verified adapter, no source refit or2025prices before evaluation.' if passed else
        'Review the new reduced-mark failure in existing source artifacts before a distinct standard proposal; do not rescue lines or add mark predictors iteratively from held-source gains. P42/P43show that overly simple marks may fail source risk allocation, not that another larger tree is justified. Preserve current source-safe reference, whole-learning and private-first constraints; no repeated source reconstruction or publicscore probes.')
    text = '# P43: severidad reducida al valor asegurado\n\nCodex, '+utc()+'.\n\n'+('El veto conjunto fuente pasa; se completaron los15refits de marca permitidos y componentes históricos. Falta evaluar el algoritmo destino completo.' if passed else 'El veto conjunto fuente falla. Se detiene con15GLMinternos; no hay refits completos o inferencias destino.')
    text += '\n\n| Ramo | Cambio relativo de desviación | Pasa |\n|---|---:|---|\n'
    for a in report['source_veto']: text += f"| {a['line']} | {100*a['relative_loss']:+.4f}% | {a['pass']} |\n"
    text += ('\nSe conservaron las frecuencias Poisson guardadas y el contrato pareado. Cada marca tiene solo capital/valor y su indicador de ausencia original, más intercepto, con alpha1original y sin búsqueda. '
        'Es una reducción del P30multivariado; no una prueba de que capital explique causalmente el fallo P42. Las ideas de capital y Gamma/FSya tenían precedentes y se conservan. '
        'Las marcas de coste cero permanecen. Se comprobó el payload real frente a contaminación de costes/conteos retenidos, gradiente y diferencias finitas por ramo, JSON/orden/suma lineal y reproducción escalar guardada. '
        'El holdout y sus curvas fuente son condicionales/adaptativos; no evidencia privada independiente.\n\n'
        'Ajustes GLMnuevos: '+str(report['new_source_GLM_fits'])+'; frecuencia/C0nuevos:0/0; sourcecenters='+str(report['source_centers'])+'. Cero ajustes/scores destino, inferencias2025o envíos. '
        'B00/F3c/alternativas conservados,2024abierto.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'scalar_replay.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P43-MARCA-CAPITAL-RESULTADO', '--asunto', 'P43: marca reducida al capital, veto y controles preservados', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': report['status'], 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'new_source_GLM_fits': report['new_source_GLM_fits'], 'source_veto_all_pass': passed, 'forum': json.loads(p.stdout),
        'next_unit': next_unit, 'new_submissions': 0, 'goal_achieved': False, '2024_open': True}
    archive = R/'privado'/('corte_P43_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P43': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P43': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P43=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P43: marca reducida al capital\n\nCodex, '+receipt['utc']+'. Veto conjunto='+str(passed)+'; nuevos GLM='+str(report['new_source_GLM_fits'])+', cero frecuencia/C0/envíos. Payload/gradiente/JSONy replay escalar verificados. B00/F3c/alternativas conservados. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_capital_only_mark_index': w.rel(INDEX), 'week_2_private_capital_only_mark_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'source_veto_pass': passed, 'new_GLM_fits': report['new_source_GLM_fits'], 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); p = argparse.ArgumentParser(description=__doc__); p.add_argument('mode', choices=['prepare', 'run', 'close']); a = p.parse_args()
    with m.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'close': close}[a.mode]()
