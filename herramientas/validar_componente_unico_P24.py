"""Ablación fija: componente A1S solo, con residuales reaprendidos y H1 congelado."""
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
OUT = BASE/'P24_componente_unico_20261026'
PLAN = R/'registro/semana2_componente_unico_privada_plan.json'
INDEX = R/'registro/semana2_componente_unico_privada_actual.json'
spec = importlib.util.spec_from_file_location('p24_shared_evaluation', R/'herramientas/validar_canal_privada_P23.py')
previous = importlib.util.module_from_spec(spec); spec.loader.exec_module(previous)
e = previous.e; w = e.w; np = e.np; pd = e.pd
OLD_REPLAY = e.core.replay; OLD_LEARN = previous.ORIGINAL_LEARN
previous.OUT = OUT; previous.PLAN = PLAN; previous.INDEX = INDEX; previous.COV = None
e.OUT = OUT; e.P9 = OUT/'source_inputs'; e.PLAN = PLAN; e.INDEX = INDEX


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def pure_replay(f, artifact):
    assert artifact['direct_N3_weight'] == 0. and artifact['source_component_weight'] == 1.
    value = e.core.apply_component(f, artifact['component'])
    result = value.copy(); normalizers = {}
    for stage in artifact['stages']:
        result, norm = e.core.g.apply_stage(f, result, stage)
        normalizers[stage['variable']] = norm
    return {'S0': value, 'S1': value, 'S2': result}, normalizers


def learn_changed_residuals(f, held, line):
    path = ROOT/f.attrs['cached_parent_path']; parent = w.read(path)
    train = f.loc[f.fold.ne(held)].copy(); valid = f.loc[f.fold.eq(held)].copy()
    assert parent['line'] == line and parent['held_fold'] == held
    assert parent['fit_row_ids_digest'] == e.b.digest(sorted(train.row_id))
    assert parent['fit_groups_digest'] == e.b.digest(sorted(set(train.group_id)))
    assert parent['component']['fit_row_ids_digest'] == parent['fit_row_ids_digest']
    assert not set(train.group_id).intersection(valid.group_id)
    training = e.core.apply_component(train, parent['component'])
    applied = e.core.apply_component(valid, parent['component'])
    base_valid = applied.copy(); stages = []; training_norms = {}; held_norms = {}
    for variable in e.core.g.STAGES[line]:
        stage = e.core.g.fit_stage(train, training, variable)
        training, nt = e.core.g.apply_stage(train, training, stage)
        applied, nv = e.core.g.apply_stage(valid, applied, stage)
        stages.append(stage); training_norms[variable] = nt; held_norms[variable] = nv
    artifact = {'line': line, 'held_fold': held, 'component': parent['component'],
        'stages': stages, 'training_normalizers': training_norms, 'held_normalizers': held_norms,
        'fit_row_ids_digest': parent['fit_row_ids_digest'], 'fit_groups_digest': parent['fit_groups_digest'],
        'source_component_weight': 1., 'direct_N3_weight': 0.,
        'cached_parent_path': w.rel(path), 'cached_parent_sha256': w.sha(path),
        'changed_learning': 'Only residual stages whose base changed; source component and H1/G3 reused'}
    return {'S0': base_valid, 'S1': base_valid, 'S2': applied}, artifact


def new_constants(artifact):
    return {'shape_factors': 0, 'level_constants': 0,
        'residual_factors': sum(len(s['factors']) for s in artifact['stages']),
        'training_nuisance_levels': sum(len(s['nuisance_year_business']) for s in artifact['stages']),
        'new_residual_stage_calls': len(artifact['stages']),
        'shape_training_normalizers_separate': 0,
        'training_stage_normalizers_separate': sum(len(x) for x in artifact['training_normalizers'].values()),
        'held_stage_normalizers_separate': sum(len(x) for x in artifact['held_normalizers'].values())}


e.core.learn = learn_changed_residuals; e.core.replay = pure_replay; e.constants = new_constants


def synthetic():
    rng = np.random.default_rng(2026102664); n = 1600; i = np.arange(n)
    E = rng.uniform(.2, 1, n)
    f = pd.DataFrame({'row_id': ['toy'+str(j) for j in i], 'group_id': ['toygroup'+str(j) for j in i],
        'fold': i % 5, 'year': 2023+(i//5) % 2, 'new_business': (i//10) % 2,
        'T0': rng.gamma(2, 100, n)*(rng.random(n) < .3), 'reserve': 0.,
        'exposure': np.round(E, 4), 'exposure_calendar': E,
        'annual_raw_T2b': rng.uniform(50, 200, n), 'e_cost_scope': np.round(E, 4)*.8,
        'log_relative_A1S': rng.normal(0, .4, n), 'base_N3': rng.uniform(30, 200, n),
        'ncb_years': rng.integers(0, 15, n), 'prior_claims_5y': rng.integers(0, 4, n),
        'gender': rng.choice(['F', 'M'], n), 'works_from_home': rng.integers(0, 2, n),
        'marketing_segment': rng.choice(['a', 'b', 'c'], n)})
    checks = []
    for line in e.h.LINES:
        folder = OUT/'synthetic'/line; folder.mkdir(parents=True)
        _, parent = OLD_LEARN(f, 0, line)
        path = folder/'parent.json'; dump(path, parent); f.attrs['cached_parent_path'] = w.rel(path)
        pred, artifact = learn_changed_residuals(f, 0, line)
        bad = f.copy(); bad.loc[bad.fold.eq(0), ['T0', 'reserve']] = -1e20
        other_pred, other = learn_changed_residuals(bad, 0, line)
        assert e.b.digest(artifact) == e.b.digest(other) and np.array_equal(pred['S2'], other_pred['S2'])
        unused = f.copy(); unused['base_N3'] *= 7.; unused['annual_raw_T2b'] *= 3.
        inactive_pred, inactive = learn_changed_residuals(unused, 0, line)
        assert e.b.digest(inactive) == e.b.digest(artifact) and np.array_equal(inactive_pred['S2'], pred['S2'])
        valid = f.loc[f.fold.eq(0)].copy(); loaded = json.loads(json.dumps(artifact))
        replayed, norms = pure_replay(valid, loaded)
        assert np.array_equal(replayed['S2'], pred['S2']) and norms == artifact['held_normalizers']
        n3 = {'shape': [], 'cellshape': {'0': 1., '1': 1.}}
        ids, u, _ = e.forward(f, 0, loaded, n3)
        _, unused_u, _ = e.forward(unused, 0, inactive, n3)
        assert np.array_equal(u, unused_u)
        sf = valid.copy(); sf['e_cost_scope'] = sf.exposure_calendar
        scalar = e.core.apply_component(sf, parent['component'])
        for stage in loaded['stages']:
            factors = np.array([stage['factors'].get(str(v), 1.) for v in e.core.g.key(sf[stage['variable']])])
            for year in [2023, 2024]:
                for nb in [0, 1]:
                    keep = sf.year.eq(year).to_numpy() & sf.new_business.eq(nb).to_numpy()
                    norm = math.fsum((scalar[keep]*factors[keep]).tolist())/math.fsum(scalar[keep].tolist())
                    scalar[keep] *= factors[keep]/norm
        assert np.allclose(u, scalar, rtol=5e-13, atol=1e-10)
        ratio = np.tile([.98, 1.02, 1., 1.01, .99], (len(u), 1)); q = np.linspace(.7, .95, len(u))
        result = (u[:, None]*ratio).mean(axis=1)*q
        independent = np.array([math.fsum((a*b).tolist())/5*c for a, b, c in zip(u, ratio, q)])
        assert np.allclose(result, independent, rtol=2e-15)
        checks.append({'line': line, 'whole_changed_learning_held_poison_exact': True,
            'new_base_direct_N3_input_inactive': True, 'JSON_observed_and_ultimate_replay': True,
            'scalar_normalization_mean_observation_bridge': True,
            'unchanged_N3_H1_ancestry_not_claimed_removed': True})
    return {'checks': checks, 'synthetic_parent_closed_learners_separate': 3,
        'synthetic_changed_stage_calls_separate': 12, 'contest_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(e.state.PHASE).get('active_jobs')
    OUT.mkdir(); (OUT/'source_inputs').mkdir()
    fixture = synthetic(); dump(OUT/'synthetic_report.json', fixture)
    old_report_path = HOME/'target_complete_core/report.json'; old_plan_path = R/'registro/semana2_mision017_A1S_completo_plan_v1.json'
    old_plan = w.read(old_plan_path); old_report = w.read(old_report_path)
    assert old_report['plan_sha256'] == w.sha(old_plan_path)
    precedent = {'author': 'Codex', 'utc': utc(), 'existing_recipe': old_plan['models'],
        'old_observed_scores': old_report['scores'], 'old_S0_delta_vs_G3': old_report['declared_ablations_delta_vs_G3']['S0'],
        'why_not_identical': 'S0was source component without residual stages or five-member H1mean, scored under its observed mapping. P24relearns residuals on source-only base and applies the exact ultimate/observation bridge and frozen H1mean.',
        'prior_adverse_preserved': True, 'not_new_evidence_of_private_gain': True}
    dump(OUT/'precedent_review.json', precedent)
    covpath = BASE/'P19_cohortes_broker_20261026/covariates.parquet'
    cov = pd.read_parquet(covpath, filters=[('year', 'in', [2023, 2024])])
    assert cov.row_id.is_unique and not cov.is_test.any(); cov.to_parquet(OUT/'covariates.parquet', index=False)
    previous_plan = w.read(R/'registro/semana2_canal_privada_plan.json')
    sources = {p: h for p, h in previous_plan['sources'].items() if 'P23_canal_principal_20261026/' not in p}
    paths = [Path(__file__), Path(previous.__file__), old_report_path, old_plan_path,
        OUT/'precedent_review.json', OUT/'synthetic_report.json', OUT/'covariates.parquet']
    scopes = []
    for line in e.h.LINES:
        path = HOME/f'source_models/target_{line}_three_seed_components.parquet'; paths.append(path)
        relative = pd.read_parquet(path, filters=[('is_test', '==', False)])
        target = OUT/f'source_inputs/historical_{line}_three_seed.parquet'
        relative.to_parquet(target, index=False); paths.append(target)
        for scope in [a for a in previous_plan['scopes'] if a['line'] == line]:
            f, held, n3 = e.get_scope(scope['cohort'], line, scope['outer'], relative)
            train = f.loc[f.fold.ne(held)]
            path = ROOT/f.attrs['cached_parent_path']; parent = w.read(path); paths.append(path)
            assert e.b.digest(sorted(train.row_id)) == parent['fit_row_ids_digest'] == scope['training_row_digest']
            assert e.b.digest(sorted(set(train.group_id))) == parent['fit_groups_digest'] == scope['training_groups_digest']
            _, norms = OLD_REPLAY(train, parent); assert norms == parent['training_normalizers']
            try:
                e.core.replay = OLD_REPLAY
                ids, replayed, _ = e.forward(f, held, parent, n3)
            finally: e.core.replay = pure_replay
            original, _ = e.old_scope(scope['cohort'], line, scope['outer'], ids)
            error = float(np.max(np.abs(replayed/original-1))); assert error <= 3e-14
            scopes.append({**scope, 'cached_parent_sha256': w.sha(path), 'parent_replay_max_relative_error': error})
    sources.update({w.rel(p): w.sha(p) for p in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'A1S_only_base_original_residuals_frozen_H1mean',
        'hypothesis': 'Eliminar la mezcla directa de dos bases reduce la dependencia de relatividades condicionales y puede mejorar la transferencia al nuevo negocio sin añadir capacidad. El adverso S0anterior hace que la hipótesis necesite contraste, no que pueda suponerse buena.',
        'change': 'Peso A1S1y N3directo0antes de los mismos residuales, que se reaprenden por cambiar su base. No se incorpora la etapa de canal P23. Fuente, forma/nivel A1S, C0y cocientes H1/G3se reutilizan.',
        'fixed_structural_ablation': 'One recipe for all lines/business; no lambda grid or favorable-cell selection. N3remains an alternative and a frozen ancestor of H1.',
        'primary_comparator': previous_plan['primary_comparator'],
        'configuration': {'source_component_weight': 1., 'direct_N3_weight': 0.,
            'residual_stages': e.core.g.STAGES, 'K': 300,
            'normalization': 'Prediction-only year/business totals on complete application cohort',
            'H1mean_and_observation_contract': 'unchanged'},
        'changed_learning': '40new residual stages (10motor plus30contents); buildings has no new stage.30source components reused, no refit.40adverse stage calls separately.',
        'budget': {'primary_changed_stage_calls': 40, 'adverse_changed_stage_calls_separate': 40,
            'new_source_fits': 0, 'new_C0_fits': 0, 'new_future2025inference': 0, 'new_final_prices': 0, 'new_submissions': 0},
        'criteria': previous_plan['criteria'], 'bootstrap': previous_plan['bootstrap'],
        'level_sensitivity': previous_plan['level_sensitivity'], 'cohort_guard': previous_plan['cohort_guard'],
        'scopes': scopes, 'preflight': {'all30cached_parent_membership_and_full_replay': True,
            'new_synthetic_flow': w.rel(OUT/'synthetic_report.json'), 'precedent_review': w.rel(OUT/'precedent_review.json')},
        'sources': sources, 'limits': previous_plan['limits']+[
            'QSource/H1and A1Sretain conditional features and source2024; dropping a direct component does not remove all N3ancestry or establish prospective purity.',
            'Old S0underperformed, but the current whole source-only algorithm is not that old incomplete ablation. No private gain is assumed.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text(
        'Codex. P24previo: ablación estructural fija, base A1Scalibrada sola en vez de mezcla '
        'directa50/50A1S+N3, seguida de los residuales originales reaprendidos sobre esa base '
        'y la misma media H1/G3. Sin etapa canal, pesos por negocio/ramo o búsqueda de lambda. '
        'El S0antiguo sin residuales/H1perdió frente a G3; ese adverso se conserva y no '
        'representa esta receta completa. Se revisaron sus fuentes y las30ascendencias '
        'actuales, con replay de los padres exacto. El nuevo fixture comprobó toda la '
        'etapa, alteración retenida, JSON, avance a último, normalización por sumas '
        'escalares y media/enlace, además de inactividad de la entrada N3directa en la '
        'base nueva. No se afirma eliminar sus ancestros congelados de H1ni todas las '
        'variables condicionales. Presupuesto40etapas residuales primarias y40adversas '
        'separadas; edificios solo reutiliza su componente. Cero fuente/C0, inferencias2025, '
        'precios finales o envíos. Criterios globales y guardas NB/broker P23intactos, '
        'incluida familia16. B00/F3c/N3y todos los adversos conservados;2024abierto '
        'adaptativo. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P24-COMPONENTE-PREVIO',
        '--asunto', 'P24: una base directa, sin búsqueda de pesos y con guardas de nuevo negocio',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    registration = {'author': 'Codex', 'utc': utc(), 'status': 'P24registered_before_real_learning',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    dump(OUT/'registration.json', registration); dump(INDEX, registration)
    print(json.dumps({'registered': True, 'scopes': 30, 'new_source_fits': 0, 'forum': registration['forum']}))


def run():
    assert not w.read(e.state.PHASE).get('active_jobs')
    dump(OUT/'P24_execution_context.json', {'author': 'Codex', 'utc': utc(),
        'script': w.rel(Path(__file__)), 'script_sha256': w.sha(Path(__file__)),
        'new_stage_calls_budget': 40, 'parent_components_reused': 30})
    e.run()
    raw = w.read(OUT/'report.json'); cohort = previous.cohort_analysis()
    dump(OUT/'P24_context_report.json', {'author': 'Codex', 'utc': utc(),
        'candidate': 'A1S_only_base_original_residuals_frozen_H1mean',
        'status': 'P24complete_single_direct_component_algorithm_evaluated',
        'raw_engine_report': w.rel(OUT/'report.json'), 'raw_engine_report_sha256': w.sha(OUT/'report.json'),
        'raw_driver_prefix_P10_retained_not_candidate_identity': True,
        'global_gates': raw['diagnostic_gates'], 'new_business_gates': cohort['gates'],
        'all_exploratory_gates_pass': all(raw['diagnostic_gates'].values()) and all(cohort['gates'].values()),
        'new_primary_changed_stages': 40, 'adverse_changed_stages_separate': 40,
        'unchanged_parent_components_reused': 30, 'new_buildings_stage_fits': 0,
        'new_source_fits': 0, 'new_C0_fits': 0, 'new_future_inference': 0, 'new_final_prices': 0,
        'new_submissions': 0, 'formal_promotion': False, 'private_improvement_established': False,
        'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True})
    print(json.dumps({'candidate': 'P24', 'global_gates': raw['diagnostic_gates'],
        'new_business_gates': cohort['gates'], 'cohort_points': previous.descriptors_for_output(cohort)}))


def replay():
    e.replay()
    report = w.read(OUT/'cohort_report.json'); saved = np.load(OUT/'cohort_bootstrap.npy')
    assert w.sha(OUT/'cohort_bootstrap.npy') == report['cohort_draws_sha256']
    totals, descriptors, _, _ = previous.cohort_blocks()
    weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    assert np.allclose(previous.score_cohort_sums(weights@totals), saved[:4], rtol=2e-12, atol=2e-13)
    for j, a in enumerate(report['comparisons']):
        assert descriptors[j]['delta'] == a['delta']
        assert np.array_equal(np.quantile(saved[:, j], [.025, .975]), a['marginal95'])
        assert np.array_equal(np.quantile(saved[:, j], [.025/16, 1-.025/16]), a['family16_band95'])
    dump(OUT/'P24_replay_context.json', {'author': 'Codex', 'utc': utc(),
        'raw_engine_replay': w.rel(OUT/'replay_report.json'), 'raw_engine_replay_sha256': w.sha(OUT/'replay_report.json'),
        'cohort_points_saved_weights_and_intervals_verified': True,
        'new_resampling': 0, 'new_fits': 0, 'new_source_queries': 0,
        'context_report_sha256': w.sha(OUT/'P24_context_report.json')})
    print(json.dumps({'P24replay': 'exact', 'new_fits': 0, 'new_resampling': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    args = parser.parse_args()
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[args.mode]()
