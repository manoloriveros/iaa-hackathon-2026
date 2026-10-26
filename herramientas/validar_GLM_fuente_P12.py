"""GLM estándar frente a A1S dentro del mismo algoritmo S2/H1 completo.

Reusa el motor numérico ya verificado en P10, con fuentes y receta propias.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
OUT = BASE/'P12_validacion_GLM_20261026'; SOURCE = BASE/'P11_GLM_fuente_20261026'
PLAN = R/'registro/semana2_GLM_fuente_validacion_plan.json'
INDEX = R/'registro/semana2_GLM_fuente_validacion_actual.json'
spec = importlib.util.spec_from_file_location('p12_same_complete_engine', R/'herramientas/validar_ablacion_fuente_P10.py')
engine = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
np = engine.np; pd = engine.pd; w = engine.w; core = engine.core; b = engine.b; h = engine.h
engine.OUT = OUT; engine.P9 = SOURCE; engine.PLAN = PLAN; engine.INDEX = INDEX


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(d, f, ensure_ascii=False, indent=2)


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert (SOURCE/'report.json').exists() and (SOURCE/'replay_report.json').exists()
    assert not w.read(engine.state.PHASE).get('active_execution') and not w.read(engine.state.PHASE).get('active_jobs')
    OUT.mkdir()
    previous_path = R/'registro/semana2_ablacion_fuente_validacion_plan.json'
    previous = w.read(previous_path)
    # The numerical helpers, original inputs and original comparator have not changed.
    sources = {p: z for p, z in previous['sources'].items() if 'P9_fuente_sin_exposicion_' not in p}
    assert all(w.sha(ROOT/p) == z for p, z in sources.items())
    extra = [Path(__file__), Path(engine.__file__), previous_path, SOURCE/'report.json', SOURCE/'replay_report.json',
             R/'herramientas/entrenar_GLM_fuente_P11.py', R/'registro/semana2_GLM_fuente_privada_plan.json',
             BASE/'P10_validacion_sin_exposicion_20261026/synthetic.json',
             BASE/'P10_validacion_sin_exposicion_20261026/replay_report.json']
    scopes = []
    for line in h.LINES:
        extra.append(SOURCE/f'historical_{line}_three_seed.parquet')
        relative = pd.read_parquet(SOURCE/f'historical_{line}_three_seed.parquet')
        assert not relative.is_test.any() and relative.year.isin([2023, 2024]).all() and relative.row_id.is_unique
        for scope in [a for a in previous['scopes'] if a['line'] == line]:
            f, held, _ = engine.get_scope(scope['cohort'], line, scope['outer'], relative)
            tr = f.fold.ne(held)
            assert b.digest(sorted(f.loc[tr, 'row_id'])) == scope['training_row_digest']
            assert b.digest(sorted(set(f.loc[tr, 'group_id']))) == scope['training_groups_digest']
            scopes.append(scope)
    sources.update({w.rel(p): w.sha(p) for p in extra})
    plan = {k: v for k, v in previous.items() if k not in ['author', 'utc', 'hypothesis', 'preflight', 'sources', 'scopes']}
    plan.update(author='Codex', utc=utc(), candidate='GLM4_complete_S2_H1',
                hypothesis='A source-only fixed-penalty main-effects GLM on the current four-year contract can generalize more stably than A1Strees inside the same complete target algorithm; test all original gates and adverses.',
                change='Replace only annual source relativities with one fixed GLM per line, including duration as a main effect. Keep S2halfsource/halfN3, shapes, levels, residuals and five-member H1ratios unchanged in definition.',
                primary_comparator='GLM4/S2/five-member-H1 versus original A1S/S2/five-member-H1 on identical held groups.',
                source_models_per_line=1, legacy_component_filename_not_ensemble=True,
                preflight={'all30new_source_components_key_scope_bindings_exact': True,
                           'prior_unchanged_complete_helpers_fixture_and_original_replay_reused': True,
                           'new_synthetic_closed_fits': 0, 'new_contest_fits': 0},
                scopes=scopes, sources=sources,
                limits=previous['limits']+['All source numeric predictors are linear; genuine nonlinear risk and interactions may be lost.',
                                            'Current four-year source GLM is new, not a replay of source2023physical-teacher GLMs.',
                                            'P10and earlier adaptive searches remain; per-recipe intervals are exploratory, not global search-adjusted confirmation.'])
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P12antes de calibrar/puntuar: GLMfuente estándar de cuatro años dentro del mismo S2/H1completo, frente a A1S/S2/H1original. '
                    'Un GLMpor ramo, no una media de tres semillas. El nombre de caché heredado es solo interfaz; el linaje declara un modelo. '
                    'C0/N3y los cinco cocientes H1/G3no cambian ni se reajustan. Se fijan30calibraciones S2más30controles con T0/reservas retenidos alterados. '
                    'Se conservan mínimo0,002, intervalos por grupo, folds, años, Post31, pisos por celda y cuatro escenarios; no se rescatará con pesos o mezcla posterior. '
                    'Se comprobó la identidad de claves/ámbitos de los30bloques nuevos; se reutilizan controles de funciones y replay originales sin cambios, sin repetir el fixture. '
                    'Las penalizaciones, variables y preprocesamiento fuente ya están congelados. No se cambia la receta al conocer un score. '
                    'No hay inferencias2025, precios finales, C0nuevos o envíos. B00/F3c/P6intactos,2024abierto adaptativo; no se afirma desempeño privado. '
                    'Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P12-GLM-PREVIO', '--asunto',
                             'P12 previo: contrastar GLM fuente estándar en el flujo completo, criterios intactos',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P12registered_before_target_learning',
               'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'preflight': 'passed', 'scopes': 30, 'new_synthetic_fits': 0, 'forum': receipt['forum']}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
    execution = {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'script': w.rel(Path(__file__)),
                 'kind': 'P12complete_standard_GLM_validation', 'output': w.rel(OUT)}
    dump(OUT/'started.json', execution); engine.state.state_execution(execution)
    try:
        for scope in plan['scopes']:
            cohort, line, outer, held = [scope[k] for k in ['cohort', 'line', 'outer', 'held']]
            folder = OUT/f'{cohort}_{line}_{outer}'; folder.mkdir()
            relative = pd.read_parquet(SOURCE/f'historical_{line}_three_seed.parquet')
            f, current_held, n3 = engine.get_scope(cohort, line, outer, relative); assert held == current_held
            train = f.fold.ne(held)
            assert b.digest(sorted(f.loc[train, 'row_id'])) == scope['training_row_digest']
            engine.event('closed_started', cohort=cohort, line=line, outer=outer, role='primary')
            observed, a = core.learn(f, held, line); dump(folder/'learning.json', a)
            engine.event('closed_completed', cohort=cohort, line=line, outer=outer, role='primary', constants=engine.constants(a))
            assert a['fit_groups_digest'] == scope['training_groups_digest']
            ids, u, norms = engine.forward(f, held, a, n3)
            expected_old, old_price = engine.old_scope(cohort, line, outer, ids)
            adapter = old_price/expected_old; new_price = u*adapter
            bad = f.copy(); bad.loc[~train, ['T0', 'reserve']] = -1e20
            engine.event('closed_started', cohort=cohort, line=line, outer=outer, role='poison')
            adverse_observed, aa = core.learn(bad, held, line); dump(folder/'poison_learning.json', aa)
            engine.event('closed_completed', cohort=cohort, line=line, outer=outer, role='poison', constants=engine.constants(aa))
            _, adverse_u, adverse_norm = engine.forward(bad, held, aa, n3)
            assert b.digest(a) == b.digest(aa) and np.array_equal(observed['S2'], adverse_observed['S2'])
            assert np.array_equal(u, adverse_u) and norms == adverse_norm
            tr = f.loc[train]; comp = a['component']; raw = np.exp(tr.log_relative_A1S.to_numpy())*tr.e_cost_scope.to_numpy()
            for shape in comp['shape']: raw = b.shape_apply(tr, raw, shape)
            moment = math.fsum((tr.T0.to_numpy()/np.sqrt(raw)).tolist())/math.fsum(np.sqrt(raw).tolist())
            assert math.isclose(moment, comp['level'], rel_tol=3e-12)
            pp = pd.DataFrame({'row_id': ids, 'new_ultimate': u, 'old_ultimate': expected_old,
                               'fixed_adapter': adapter, 'old_nominal': old_price, 'new_nominal': new_price})
            pp.to_parquet(folder/'prices.parquet', index=False)
            dump(folder/'committed.json', {'scope': scope, 'held_poison_current_learning_exact': True,
                                           'unchanged_C0_N3_H1_not_reestimated': True,
                                           'moment_relative_error': abs(moment/comp['level']-1), 'ultimate_normalizers': norms,
                                           'outputs': {w.rel(p): w.sha(p) for p in folder.glob('*') if p.is_file()}})
            print(json.dumps({'scope': cohort+'|'+line+'|'+str(outer), 'complete': True}), flush=True)
        results = engine.evaluate_outputs(plan); a = results['POOLED']['NOMINAL']; t = results['TRANSFER']['NOMINAL']
        gates = {'pooled_delta_ge002': a['delta'] >= .002, 'pooled_lower95_positive': a['bootstrap95'][0] > 0,
                 'pooled_atleast4positive_folds': sum(v > 0 for v in a['folds'].values()) >= 4,
                 'both_pooled_years_nonnegative': min(a['years'].values()) >= 0,
                 'pooled_post31_nonnegative': a['post31_delta'] >= 0, 'conditional_transfer_nonnegative': t['delta'] >= 0,
                 'all_nominal_and_stress_cell_floors': all(x['worst_cell_delta'] >= -.001 for c in results.values() for x in c.values())}
        assert all(w.sha(ROOT/p) == z for p, z in plan['sources'].items())
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P12complete_standard_source_GLM_evaluated', 'results': results,
                  'diagnostic_gates': gates, 'new_primary_closed_learners': 30, 'new_adverse_closed_learners_separate': 30,
                  'new_source_fits': 0, 'new_C0_fits': 0, 'new_future2025inference': 0, 'new_finaltestprices': 0,
                  'new_submissions': 0, 'source_models_per_line': 1, 'formal_promotion': False, 'submission_allowed': False,
                  'private_improvement_established': False, 'goal_achieved': False, '2024_open': True,
                  'B00_all_alternatives_preserved': True, 'limits': plan['limits'], 'plan_sha256': w.sha(PLAN)}
        dump(OUT/'report.json', report)
        print(json.dumps({'status': report['status'], 'gates': gates, 'results':
                           {k: {name: {q: v[q] for q in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']}
                                for name, v in d.items()} for k, d in results.items()}}))
    except BaseException as exc:
        dump(OUT/('failure_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'),
             {'exception': type(exc).__name__, 'message': str(exc), 'committed_scopes': len(list(OUT.glob('*/committed.json'))),
              'next': 'Reconcile saved learners/receipts before any resume; do not repeat committed work'})
        raise
    finally: engine.state.state_execution(None)


def replay():
    # Same real saved-flow proof and entry-point blockers, all hashes include this wrapper.
    engine.replay()
    dump(OUT/'P12_replay_context.json', {'author': 'Codex', 'utc': utc(), 'candidate': 'GLM4_complete_S2_H1',
                                       'engine_identity': 'P10saved_flow_replay',
                                       'receipt': w.rel(OUT/'replay_report.json'),
                                       'receipt_sha256': w.sha(OUT/'replay_report.json'),
                                       'source_models_per_line': 1, 'new_fits': 0})


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with engine.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
