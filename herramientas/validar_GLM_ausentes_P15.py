"""Valida GLM4_MI en el mismo flujo completo y contra el GLM sin indicadores."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
SOURCE = BASE/'P14_GLM_ausentes_20261026'; PREVIOUS = BASE/'P12_validacion_GLM_20261026'
OUT = BASE/'P15_validacion_ausentes_20261026'
PLAN = R/'registro/semana2_GLM_ausentes_validacion_plan.json'
INDEX = R/'registro/semana2_GLM_ausentes_validacion_actual.json'
sp = importlib.util.spec_from_file_location('p15_complete_engine_P12', R/'herramientas/validar_GLM_fuente_P12.py')
old = importlib.util.module_from_spec(sp); sp.loader.exec_module(old)
engine = old.engine; w = old.w; np = old.np; pd = old.pd
old.SOURCE = SOURCE; old.OUT = OUT; old.PLAN = PLAN; old.INDEX = INDEX
engine.P9 = SOURCE; engine.OUT = OUT; engine.PLAN = PLAN; engine.INDEX = INDEX


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)


def prepare():
    assert not OUT.exists() and not PLAN.exists()
    assert (SOURCE/'context_report.json').exists() and (SOURCE/'P14_replay_context.json').exists()
    assert not w.read(engine.state.PHASE).get('active_execution') and not w.read(engine.state.PHASE).get('active_jobs')
    OUT.mkdir()
    previous_path = R/'registro/semana2_GLM_fuente_validacion_plan.json'; previous = w.read(previous_path)
    assert all(w.sha(ROOT/p) == z for p, z in previous['sources'].items())
    sources = {p: z for p, z in previous['sources'].items() if 'P11_GLM_fuente_20261026/historical_' not in p}
    extra = [Path(__file__), Path(old.__file__), previous_path, SOURCE/'context_report.json',
             SOURCE/'report.json', SOURCE/'replay_report.json', SOURCE/'P14_replay_context.json',
             R/'herramientas/GLM_ausentes_privada_P14.py', R/'registro/semana2_GLM_ausentes_fuente_plan.json',
             PREVIOUS/'report.json']
    for cohort in ['POOLED', 'TRANSFER']:
        extra += [PREVIOUS/(cohort+'_prices.parquet'), PREVIOUS/(cohort+'_joint_bootstrap.npy')]
    scopes = []
    for line in engine.h.LINES:
        path = SOURCE/f'historical_{line}_three_seed.parquet'; extra.append(path)
        relative = pd.read_parquet(path)
        assert relative.row_id.is_unique and not relative.is_test.any() and relative.year.isin([2023, 2024]).all()
        for scope in [a for a in previous['scopes'] if a['line'] == line]:
            f, held, _ = engine.get_scope(scope['cohort'], line, scope['outer'], relative)
            assert engine.b.digest(sorted(f.loc[f.fold.ne(held), 'row_id'])) == scope['training_row_digest']
            assert engine.b.digest(sorted(set(f.loc[f.fold.ne(held), 'group_id']))) == scope['training_groups_digest']
            scopes.append(scope)
    sources.update({w.rel(p): w.sha(p) for p in extra})
    plan = {k: v for k, v in previous.items() if k not in ['author', 'utc', 'candidate', 'hypothesis', 'change', 'preflight', 'scopes', 'sources', 'limits']}
    plan.update(author='Codex', utc=utc(), candidate='GLM4_MI_complete_S2_H1',
                hypothesis='Explicit numeric missingness main effects may improve the current sourceGLMtransport limitation while preserving the complete target algorithm; test against incumbent and plainGLM.',
                change='Replace only source relativities with the3fixed P14GLMs (6/5/5missing indicators). Same S2halfsource/halfN3and five-member H1, C0, target exposure and calibration recipes.',
                primary_comparator='Original A1S/S2/H1 versus GLM4_MI/S2/H1. All prior gates remain, including minimum incremental .002 and cell floor -.001.',
                secondary_comparator='Plain P12GLM4/S2/H1 versus GLM4_MI/S2/H1, to attribute this preprocessing change. Improvement only here cannot admit candidate.',
                paired_secondary_bootstrap='Subtract existing P12draws from new primary draws with identical groups, outcomes, sample order, seeds and null denominator. No second resampling or source refit.',
                budget={'new_source_fits': 0, 'new_C0_fits': 0, 'primary_closed_learner_calls': 30,
                        'adverse_closed_learner_calls_separate': 30, 'new_future2025inference': 0,
                        'new_finaltestprices': 0, 'new_submissions': 0},
                preflight={'all30new_source_scope_bindings_exact': True, 'new_synthetic_fits': 0,
                           'unchanged_complete_helpers_and_prior_fixtures_reused': True,
                           'new_missingness_transform_full_fixture_and_JSONreplay_in_P14': True},
                scopes=scopes, sources=sources,
                limits=previous['limits']+['Missingness mechanism can differ across markets; indicators do not recover unavailable values.',
                                            'Secondary paired intervals condition on fitted functions and reuse the same group resampling; not independent replication.',
                                            'P13oracle scalars are not inputs or adopted levels. No masks, new features chosen by outcomes, line selection or new tuning.'])
    assert plan['bootstrap'] == previous['bootstrap']
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro P15antes de calibrar o puntuar GLM4_MIen el flujo completo. '
                    'Primario frente a A1S/S2/H1original; secundario frente a GLM4/S2/H1deP12. Una mejora secundaria no permite adoptar si falla el primario. '
                    'Los tres modelos fuente quedan congelados con6/5/5indicadores definidos solo por fuente. '
                    'Se conservan C0/N3, mezcla50/50, cinco cocientes H1/G3, grupos y ambas validaciones (combinada y destino2023→2024condicional). '
                    '30calibraciones cerradas más30controles adversos; cero modelos fuente/C0/inferencias2025/precios finales/envíos. '
                    'Mínimo0,002, intervalos por grupos, folds, años, Post31, piso−0,001y cuatro escenarios intactos. '
                    'Los intervalos secundarios se derivarán de diferencias de draws emparejados con las mismas semillas, grupos y denominadores; no se repite el remuestreo de P12. '
                    'No se usan niveles oráculo, máscaras, celdas positivas o cambios de penalización. '
                    'B00/F3c/P6y adversos intactos,2024abierto adaptativo y privada prioritaria. '
                    'Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
                             '--id', 'COD-S2-20261026-PRIVADA-P15-AUSENTES-PREVIO', '--asunto',
                             'P15 previo: indicadores de ausencia frente a referencia y GLM simple, sin cambiar criterios',
                             '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P15registered_before_target_learning',
               'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout), 'output': w.rel(OUT)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt)
    print(json.dumps({'registered': True, 'scopes': 30, 'new_fits': 0, 'forum': receipt['forum']}))


def secondary_results(primary_report):
    results = {}; previous = w.read(PREVIOUS/'report.json'); plan = w.read(PLAN)
    assert plan['bootstrap'] == w.read(R/'registro/semana2_GLM_fuente_validacion_plan.json')['bootstrap']
    for cohort in ['POOLED', 'TRANSFER']:
        f = pd.read_parquet(OUT/(cohort+'_prices.parquet'))
        ref = pd.read_parquet(PREVIOUS/(cohort+'_prices.parquet'))
        for col in ['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']:
            assert np.array_equal(f[col], ref[col])
        now = np.load(OUT/(cohort+'_joint_bootstrap.npy')); before = np.load(PREVIOUS/(cohort+'_joint_bootstrap.npy'))
        assert now.shape == before.shape == (2000, 5)
        draws = now-before; np.save(OUT/(cohort+'_secondary_paired_draws.npy'), draws)
        reserves = pd.concat([pd.read_parquet(engine.P1/f'canonical_{line}.parquet', columns=['row_id', 'reserve']) for line in engine.h.LINES]).set_index('row_id').loc[f.row_id].reserve.to_numpy(float)
        ys = [f.T0.to_numpy(float), f.T0.to_numpy(float)-.25*reserves, f.T0.to_numpy(float)+.25*reserves,
              f.T0.to_numpy(float), f.T0.to_numpy(float)]
        cohort_results = {}
        for j, name in enumerate(engine.NAMES):
            y = ys[j]; baseline = ref.new_nominal.to_numpy() if j == 0 else ref[name+'_new'].to_numpy()
            candidate = f.new_nominal.to_numpy() if j == 0 else f[name+'_new'].to_numpy()
            gain = engine.unit(y, baseline)-engine.unit(y, candidate)
            den = engine.unit(y, np.full(len(y), y.mean())).sum()
            delta = float(gain.sum()/den)
            expected = primary_report['results'][cohort][name]['delta']-previous['results'][cohort][name]['delta']
            assert abs(delta-expected) < 1e-11
            by_group = pd.DataFrame({'group_id': f.group_id, 'gain': gain}).groupby('group_id', sort=True).gain.sum()
            cells = []
            for (line, year, nb), ix in f.groupby(['line', 'year', 'new_business']).groups.items():
                ii = np.asarray(ix); yy = y[ii]; null = engine.unit(yy, np.full(len(ii), yy.mean())).sum()
                cells.append({'line': line, 'year': int(year), 'NB': int(nb), 'delta_cell_null': float(gain[ii].sum()/null)})
            cohort_results[name] = {'delta': delta, 'bootstrap95_paired_existing_draws': np.quantile(draws[:, j], [.025, .975]).tolist(),
                                    'simultaneous95_secondary_family10': np.quantile(draws[:, j], [.0025, .9975]).tolist(),
                                    'post31_delta': float((by_group.sum()-by_group.nlargest(31).sum())/den),
                                    'folds': {str(k): float(gain[f.fold.eq(k)].sum()/den) for k in range(5)},
                                    'years': {str(int(k)): float(gain[f.year.eq(k)].sum()/den) for k in sorted(f.year.unique())},
                                    'cells': cells, 'worst_cell_delta': min(z['delta_cell_null'] for z in cells),
                                    'new_resampling': 0, 'admission_from_secondary_alone': False}
        results[cohort] = cohort_results
    return results


def run():
    assert not (OUT/'context_report.json').exists()
    if not (OUT/'report.json').exists(): old.run()
    report = w.read(OUT/'report.json'); assert report['plan_sha256'] == w.sha(PLAN)
    secondary = secondary_results(report)
    assert all(w.sha(ROOT/p) == z for p, z in w.read(PLAN)['sources'].items())
    context = {'author': 'Codex', 'utc': utc(), 'status': 'P15complete_missing_indicator_GLM_evaluated',
               'candidate': 'GLM4_MI_complete_S2_H1', 'engine_report': w.rel(OUT/'report.json'),
               'engine_report_sha256': w.sha(OUT/'report.json'), 'primary_diagnostic_gates': report['diagnostic_gates'],
               'primary_nominal': {c: report['results'][c]['NOMINAL'] for c in ['POOLED', 'TRANSFER']},
               'secondary_vs_plain_GLM': secondary, 'new_primary_closed_learners': 30,
               'new_adverse_closed_learners_separate': 30, 'new_source_fits': 0, 'new_C0_fits': 0,
               'new_secondary_resampling': 0, 'new_future2025inference': 0, 'new_finaltestprices': 0, 'new_submissions': 0,
               'formal_promotion': False, 'submission_allowed': False, 'private_improvement_established': False,
               '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False,
               'plan_sha256': w.sha(PLAN)}
    dump(OUT/'context_report.json', context)
    print(json.dumps({'status': context['status'], 'primary_gates': context['primary_diagnostic_gates'],
                      'secondary_nominal': {c: {k: d['NOMINAL'][k] for k in ['delta', 'bootstrap95_paired_existing_draws', 'post31_delta', 'worst_cell_delta']}
                                            for c, d in secondary.items()}}))


def replay():
    engine.replay()  # Frozen complete-flow numerical engine; no source model application.
    context = w.read(OUT/'context_report.json')
    # Verify paired-interval arithmetic from saved draws, without redoing any resampling.
    for cohort in ['POOLED', 'TRANSFER']:
        expected = np.load(OUT/(cohort+'_joint_bootstrap.npy'))-np.load(PREVIOUS/(cohort+'_joint_bootstrap.npy'))
        saved = np.load(OUT/(cohort+'_secondary_paired_draws.npy')); assert np.array_equal(saved, expected)
        for j, name in enumerate(engine.NAMES):
            assert np.array_equal(np.quantile(saved[:, j], [.025, .975]),
                                  context['secondary_vs_plain_GLM'][cohort][name]['bootstrap95_paired_existing_draws'])
    dump(OUT/'P15_replay_context.json', {'author': 'Codex', 'utc': utc(), 'candidate': 'GLM4_MI_complete_S2_H1',
                                       'engine_receipt': w.rel(OUT/'replay_report.json'),
                                       'engine_receipt_sha256': w.sha(OUT/'replay_report.json'),
                                       'context_report_sha256': w.sha(OUT/'context_report.json'),
                                       'paired_secondary_intervals_exact': True, 'new_resampling': 0,
                                       'new_fits': 0, 'new_source_queries': 0})
    print(json.dumps({'replay': 'passed', 'paired_intervals': 'exact', 'new_resampling': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    with engine.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[parser.parse_args().mode]()
