"""Un contraste contractual nuevo sobre S2, sin reajustar sus padres ni H1."""
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
OUT = BASE/'P23_canal_principal_20261026'
PLAN = R/'registro/semana2_canal_privada_plan.json'
INDEX = R/'registro/semana2_canal_privada_actual.json'
spec = importlib.util.spec_from_file_location('p23_complete_paired_engine', R/'herramientas/validar_ablacion_fuente_P10.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
w = e.w; np = e.np; pd = e.pd
ORIGINAL_GET = e.get_scope; ORIGINAL_LEARN = e.core.learn
e.OUT = OUT; e.P9 = OUT/'source_inputs'; e.PLAN = PLAN; e.INDEX = INDEX
COV = None


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def broker_key(channel):
    return np.select([channel.eq('broker'), channel.isin(['direct', 'comparison_site'])],
        ['broker', 'other'], default='__UNKNOWN_CHANNEL__')


def get_scope(cohort, line, outer, relative):
    global COV
    f, held, n3 = ORIGINAL_GET(cohort, line, outer, relative)
    if COV is None: COV = pd.read_parquet(OUT/'covariates.parquet').set_index('row_id')
    extra = COV.loc[f.row_id]
    for name in ['year', 'new_business']:
        assert np.array_equal(f[name], extra[name])
    assert extra.line.eq(line).all()
    f['broker_group'] = broker_key(extra.channel).astype(str)
    path = HOME/f'target_complete_core/learning_{line}_fold{outer}.json' if cohort == 'POOLED' else e.P4/f'scope_{line}_outer{outer}_member-1/primary/learning_S2.json'
    f.attrs['cached_parent_path'] = w.rel(path)
    return f, held, n3


def learn_changed_stage(f, held, line):
    path = ROOT/f.attrs['cached_parent_path']; parent = w.read(path)
    train = f.loc[f.fold.ne(held)].copy(); valid = f.loc[f.fold.eq(held)].copy()
    assert not set(train.group_id).intersection(valid.group_id)
    assert parent['line'] == line and parent['held_fold'] == held
    assert parent['fit_row_ids_digest'] == e.b.digest(sorted(train.row_id))
    assert parent['fit_groups_digest'] == e.b.digest(sorted(set(train.group_id)))
    training, nt = e.core.replay(train, parent); previous, nv = e.core.replay(valid, parent)
    assert nt == parent['training_normalizers'] and nv == parent['held_normalizers']
    assert all(stage['variable'] != 'broker_group' for stage in parent['stages'])
    stage = e.core.g.fit_stage(train, training['S2'], 'broker_group')
    _, training_norm = e.core.g.apply_stage(train, training['S2'], stage)
    changed, valid_norm = e.core.g.apply_stage(valid, previous['S2'], stage)
    artifact = json.loads(json.dumps(parent))
    artifact['stages'].append(stage)
    artifact['training_normalizers']['broker_group'] = training_norm
    artifact['held_normalizers']['broker_group'] = valid_norm
    artifact.update(cached_parent_path=w.rel(path), cached_parent_sha256=w.sha(path),
        changed_learning='one broker_group residual stage only; all parent parameters reused')
    return {**previous, 'S2': changed}, artifact


def changed_constants(artifact):
    stage = artifact['stages'][-1]; assert stage['variable'] == 'broker_group'
    return {'shape_factors': 0, 'level_constants': 0, 'residual_factors': len(stage['factors']),
        'training_nuisance_levels': len(stage['nuisance_year_business']),
        'shape_training_normalizers_separate': 0,
        'training_stage_normalizers_separate': len(artifact['training_normalizers']['broker_group']),
        'held_stage_normalizers_separate': len(artifact['held_normalizers']['broker_group'])}


e.get_scope = get_scope
e.core.learn = learn_changed_stage
e.constants = changed_constants


def synthetic():
    rng = np.random.default_rng(2026102663); n = 1600; i = np.arange(n)
    f = pd.DataFrame({'row_id': ['toy'+str(j) for j in i], 'group_id': ['toygroup'+str(j) for j in i],
        'fold': i % 5, 'year': 2023+(i//5) % 2, 'new_business': (i//10) % 2,
        'T0': rng.gamma(2, 100, n)*(rng.random(n) < .3), 'reserve': 0.,
        'exposure': rng.uniform(.2, 1, n), 'exposure_calendar': rng.uniform(.2, 1, n),
        'annual_raw_T2b': rng.uniform(50, 200, n), 'e_cost_scope': rng.uniform(.1, 1, n),
        'log_relative_A1S': rng.normal(0, .4, n), 'base_N3': rng.uniform(30, 200, n),
        'ncb_years': rng.integers(0, 15, n), 'prior_claims_5y': rng.integers(0, 4, n),
        'gender': rng.choice(['F', 'M'], n), 'works_from_home': rng.integers(0, 2, n),
        'marketing_segment': rng.choice(['a', 'b', 'c'], n),
        'broker_group': rng.choice(['broker', 'other'], n)})
    checks = []
    for line in e.h.LINES:
        folder = OUT/'synthetic'/line; folder.mkdir(parents=True)
        _, parent = ORIGINAL_LEARN(f, 0, line)
        path = folder/'parent.json'; dump(path, parent); f.attrs['cached_parent_path'] = w.rel(path)
        predicted, artifact = learn_changed_stage(f, 0, line)
        bad = f.copy(); bad.loc[bad.fold.eq(0), ['T0', 'reserve']] = -1e20
        other_predicted, other = learn_changed_stage(bad, 0, line)
        assert e.b.digest(artifact) == e.b.digest(other)
        assert np.array_equal(predicted['S2'], other_predicted['S2'])
        loaded = json.loads(json.dumps(artifact)); valid = f.loc[f.fold.eq(0)].copy()
        replayed, norms = e.core.replay(valid, loaded)
        assert np.array_equal(replayed['S2'], predicted['S2']) and norms == artifact['held_normalizers']
        n3 = {'shape': [], 'cellshape': {'0': 1., '1': 1.}}
        ids, u, _ = e.forward(f, 0, loaded, n3)
        sf = valid.copy(); sf['e_cost_scope'] = sf.exposure_calendar
        sf['base_N3'] = sf.annual_raw_T2b*sf.exposure_calendar
        before, _ = e.core.replay(sf, parent)
        stage = loaded['stages'][-1]
        factor = np.array([stage['factors'][k] for k in sf.broker_group])
        scalar = before['S2'].copy()
        for year in [2023, 2024]:
            for nb in [0, 1]:
                keep = sf.year.eq(year).to_numpy() & sf.new_business.eq(nb).to_numpy()
                norm = math.fsum((scalar[keep]*factor[keep]).tolist())/math.fsum(scalar[keep].tolist())
                scalar[keep] *= factor[keep]/norm
        assert np.allclose(scalar, u, rtol=3e-13, atol=1e-10)
        ratio = np.tile([.98, 1.02, 1., 1.01, .99], (len(u), 1)); q = np.linspace(.7, .95, len(u))
        composed = (u[:, None]*ratio).mean(axis=1)*q
        independent = np.array([math.fsum((uu*rr).tolist())/5*qq for uu, rr, qq in zip(u, ratio, q)])
        assert np.allclose(composed, independent, rtol=2e-15)
        untouched, _ = e.core.g.apply_stage(valid.assign(broker_group='__UNKNOWN_CHANNEL__'), before['S2'], stage)
        assert np.array_equal(untouched, before['S2'])
        checks.append({'line': line, 'cached_parent_and_changed_stage_poison_exact': True,
            'saved_JSON_full_observed_and_ultimate_flow': True, 'scalar_normalization_and_mean_bridge': True,
            'unknown_channel_neutral': True, 'normalizers_require_complete_application_cohort': True})
    return {'checks': checks, 'synthetic_parent_closed_learners_separate': 3,
        'synthetic_new_stage_calls_separate': 6, 'contest_fits': 0}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(e.state.PHASE).get('active_jobs')
    OUT.mkdir(); (OUT/'source_inputs').mkdir()
    fixture = synthetic(); dump(OUT/'synthetic_report.json', fixture)
    covpath = BASE/'P19_cohortes_broker_20261026/covariates.parquet'
    cov = pd.read_parquet(covpath, filters=[('year', 'in', [2023, 2024])])
    assert cov.row_id.is_unique and not cov.is_test.any()
    assert set(cov.channel.unique()) == {'broker', 'direct', 'comparison_site'}
    cov.to_parquet(OUT/'covariates.parquet', index=False)
    paths = [Path(__file__), Path(e.__file__), Path(e.parent.__file__), Path(e.core.__file__),
        Path(e.b.__file__), Path(e.g.__file__), Path(e.core.g.__file__), Path(e.state.__file__),
        covpath, OUT/'covariates.parquet', OUT/'synthetic_report.json',
        R/'registro/semana2_robustez2023_ciclo13_plan.json',
        R/'docs/semana2/BALANCE_ROBUSTEZ_2023_20261025.md']
    paths += [BASE/'P19_cohortes_broker_20261026'/name for name in ['group_universe.json', 'first4_group_weights.npy']]
    template = w.read(R/'registro/semana2_ablacion_fuente_validacion_plan.json')
    # Preserve the exact unchanged evaluation/C0/N3/H1 dependencies of the existing engine.
    sources = {p: h for p, h in template['sources'].items() if 'P9_fuente_sin_exposicion_' not in p}
    scopes = []; support = []
    for line in e.h.LINES:
        path = HOME/f'source_models/target_{line}_three_seed_components.parquet'; paths.append(path)
        relative = pd.read_parquet(path, filters=[('is_test', '==', False)])
        assert relative.row_id.is_unique and relative.year.isin([2023, 2024]).all()
        out = OUT/f'source_inputs/historical_{line}_three_seed.parquet'
        relative.to_parquet(out, index=False); paths.append(out)
        for scope in [a for a in template['scopes'] if a['line'] == line]:
            f, held, n3 = get_scope(scope['cohort'], line, scope['outer'], relative)
            train = f.loc[f.fold.ne(held)]
            assert e.b.digest(sorted(train.row_id)) == scope['training_row_digest']
            assert e.b.digest(sorted(set(train.group_id))) == scope['training_groups_digest']
            parentpath = ROOT/f.attrs['cached_parent_path']; paths.append(parentpath)
            parent = w.read(parentpath)
            assert parent['fit_row_ids_digest'] == scope['training_row_digest']
            assert parent['fit_groups_digest'] == scope['training_groups_digest']
            _, trnorm = e.core.replay(train, parent); assert trnorm == parent['training_normalizers']
            ids, previous_u, _ = e.forward(f, held, parent, n3)
            expected_u, _ = e.old_scope(scope['cohort'], line, scope['outer'], ids)
            error = float(np.max(np.abs(previous_u/expected_u-1))); assert error <= 3e-14
            for label, group in train.groupby('broker_group'):
                positives = group.loc[group.T0.gt(0), 'group_id'].nunique()
                support.append({'cohort': scope['cohort'], 'line': line, 'outer': scope['outer'],
                    'label': label, 'positive_groups': int(positives)})
                assert positives >= 30, 'Stop rather than pool levels to meet support'
            scopes.append({**scope, 'cached_parent_sha256': w.sha(parentpath), 'parent_replay_max_relative_error': error})
    dump(OUT/'support_preflight.json', support); paths.append(OUT/'support_preflight.json')
    sources.update({w.rel(p): w.sha(p) for p in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'A1S_S2_broker_main_effect_with_unchanged_H1mean',
        'hypothesis': 'La relación contractual broker/no broker puede cambiar entre mercados. La mezcla de adquisición privada exige medir una corrección local sencilla de esa relación, sin otra familia fuente.',
        'prior_adverse': 'Ciclo13R49/R50ensayó cuatro variables juntas en otro maestro/mezcla2023; falló. No se repite ni se atribuye su resultado exclusivamente a canal.',
        'change': 'Solo una etapa residual broker_group al final de S2, antes de multiplicar la misma media de cinco cocientes H1/G3. Padres S2, fuente, C0, N3y H1/G3se reutilizan sin reajuste tras verificar sus ancestros.',
        'primary_comparator': 'A1S/S2/H1original, idénticos grupos y qSource de observación.',
        'configuration': {'levels': ['broker', 'other=direct_or_comparison_site'], 'unknown': 'neutral1',
            'K': 300, 'credibility': 'exp(n_positive_periods/(n_positive_periods+300)*log(conditional_Tweedie_optimum))',
            'nuisance': 'Tweedie scalar levels by training year/business, never transferred',
            'interaction_by_business': False, 'source_model_change': False,
            'normalization': 'Prediction-only per year/business on complete application cohort; no rowwise/batch-invariance claim'},
        'changed_learning': '30new residual-stage calls only, plus30separate held-poison controls; unchanged parent learning is reused, not counted as fresh fitting.',
        'budget': {'primary_changed_stage_calls': 30, 'adverse_changed_stage_calls_separate': 30,
            'new_source_fits': 0, 'new_C0_fits': 0, 'new_future2025inference': 0, 'new_final_prices': 0, 'new_submissions': 0},
        'criteria': template['criteria'], 'bootstrap': template['bootstrap'],
        'level_sensitivity': template['level_sensitivity'],
        'cohort_guard': {'cohorts': ['NB', 'NB_BROKER', 'NB_BROKER_ZERO'],
            'evaluations': ['POOLED', 'TRANSFER'], 'point_floor': -.001,
            'marginal95_lower_floor': -.001, 'replicates': 2000, 'seed': 2026102660,
            'family16_lower_floor': -.001, 'all_stress_point_floor': -.001,
            'pooled_family16_lower_positive': True,
            'same_group_multiplicities_as_P19': True, 'no_support_claim_from_passing_points': True,
            'family16': '10global scenario comparisons plus6nominal cohort comparisons; exploratory Bonferroni percentile bands, limited by2000draw resolution'},
        'scopes': scopes, 'preflight': {'all30parent_membership_and_replay_checks': True,
            'minimum_positive_groups_per_level_all_business': min(a['positive_groups'] for a in support),
            'synthetic_report': w.rel(OUT/'synthetic_report.json')},
        'sources': sources, 'limits': template['limits']+[
            'Un efecto compartido entre negocio nuevo y renovación puede omitir una selección distinta; no se busca una interacción tras ver el resultado.',
            'Los grupos positivos de edificios/contenidos nuevos siguen escasos; los intervalos siguen condicionados a precios/objetivos y búsqueda adaptativa.',
            'Esto evalúa el algoritmo propio estricto, no reconstruye exactamente F3c.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text(
        'Codex. P23preinscrito: un único efecto broker/no broker conK300al final de S2, antes de '
        'la misma media H1/G3. Sin interacción por negocio ni cambio fuente/C0/N3/H1. Reutilizar '
        'padres exactos, aprender solo30etapas nuevas y30controles adversos separados. El ciclo13 '
        'con cuatro variables y otra arquitectura falló y se conserva; esta es una prueba '
        'distinta de un solo efecto sobre el algoritmo completo actual. Criterios globales '
        'intactos (mínimo0,002, IC, folds/años, concentración y escenarios), más guardas en '
        'negocio nuevo/broker/historia cero: punto, límite95inferior y banda de familia16 '
        'no menores de−0,001, incluidos puntos bajo escenarios; límite de familia16del '
        'nominal combinado positivo. '
        'Cero fuente/C0, inferencias2025, precios finales o envíos. Pasaron el fixture completo '
        'con padres sintéticos, alteración de etiquetas retenidas, JSON, normalización por '
        'sumas escalares y media/enlace observado. Los30padres reales coinciden en ancestros '
        'y tasas iniciales; cada nivel tiene al menos30grupos positivos de entrenamiento. '
        'La normalización requiere la cohorte completa, no es una función de tarifa por fila '
        'aislada.2024abierto adaptativo, B00/F3cy adversos conservados. Plan '+w.rel(PLAN)+'; SHA '+w.sha(PLAN), encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P23-CANAL-PREVIO',
        '--asunto', 'P23: aislar canal contractual con padres congelados y guardas de nuevo negocio',
        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    registration = {'author': 'Codex', 'utc': utc(), 'status': 'P23registered_before_real_stage_learning',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout)}
    dump(OUT/'registration.json', registration); dump(INDEX, registration)
    print(json.dumps({'registered': True, 'scopes': 30, 'minimum_positive_groups': plan['preflight']['minimum_positive_groups_per_level_all_business'], 'forum': registration['forum']}))


def cohort_blocks():
    cov = pd.read_parquet(OUT/'covariates.parquet').set_index('row_id')
    universe = w.read(BASE/'P19_cohortes_broker_20261026/group_universe.json')
    blocks = []; descriptors = []; stress_points = []
    reserve = pd.concat([pd.read_parquet(e.P1/f'canonical_{line}.parquet',
        columns=['row_id', 'reserve']) for line in e.h.LINES]).set_index('row_id')
    for evaluation in ['POOLED', 'TRANSFER']:
        f = pd.read_parquet(OUT/f'{evaluation}_prices.parquet')
        extra = cov.loc[f.row_id]
        assert np.array_equal(extra.year, f.year) and np.array_equal(extra.new_business, f.new_business)
        f['channel'] = extra.channel.to_numpy(); f['f1_anios_observados'] = extra.f1_anios_observados.to_numpy()
        for cohort in ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']:
            keep = f.new_business.to_numpy(bool).copy()
            if cohort != 'NB': keep &= f.channel.eq('broker').to_numpy()
            if cohort == 'NB_BROKER_ZERO': keep &= f.f1_anios_observados.eq(0).to_numpy()
            z = f.loc[keep]; y = z.T0.to_numpy(float)
            old = z.old_nominal.to_numpy(float); new = z.new_nominal.to_numpy(float)
            null = e.unit(y, np.full(len(y), y.mean())).sum()
            value = np.column_stack([np.ones(len(y)), y, np.sqrt(y), e.unit(y, old)-e.unit(y, new)])
            independent = (e.mean_tweedie_deviance(y, old, power=1.5)-e.mean_tweedie_deviance(y, new, power=1.5))/e.mean_tweedie_deviance(y, np.full(len(y), y.mean()), power=1.5)
            assert math.isclose(value[:, 3].sum()/null, independent, rel_tol=2e-10, abs_tol=2e-13)
            aggregate = pd.DataFrame(value).assign(group=z.group_id.to_numpy()).groupby('group', sort=True).sum().reindex(universe, fill_value=0).to_numpy()
            blocks.append(aggregate)
            descriptors.append({'evaluation': evaluation, 'cohort': cohort, 'rows': len(z),
                'groups': int(z.group_id.nunique()), 'delta': float(value[:, 3].sum()/null)})
            rv = reserve.loc[z.row_id, 'reserve'].to_numpy(float)
            for scenario in e.NAMES[1:]:
                yy = y-.25*rv if scenario == 'RESERVE075' else y+.25*rv if scenario == 'RESERVE125' else y
                den = e.unit(yy, np.full(len(yy), yy.mean())).sum()
                gain = e.unit(yy, z[scenario+'_old'].to_numpy(float))-e.unit(yy, z[scenario+'_new'].to_numpy(float))
                stress_points.append({'evaluation': evaluation, 'cohort': cohort, 'scenario': scenario,
                    'delta': float(gain.sum()/den)})
    return np.concatenate(blocks, axis=1), descriptors, stress_points, universe


def score_cohort_sums(values):
    columns = []
    for j in range(6):
        n, sy, sq, gain = values[:, j*4:(j+1)*4].T
        null = 8*np.sqrt(sy*n)-8*sq
        assert np.isfinite(null).all() and (null > 1e-9).all()
        columns.append(gain/null)
    return np.column_stack(columns)


def cohort_analysis():
    totals, descriptors, stress, universe = cohort_blocks()
    rng = np.random.default_rng(2026102660); draws = []
    expected_first = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    for start in range(0, 2000, 32):
        weights = rng.multinomial(len(universe), np.full(len(universe), 1/len(universe)), size=min(32, 2000-start))
        if start == 0: assert np.array_equal(weights[:4], expected_first)
        draws.append(score_cohort_sums(weights@totals))
    draws = np.concatenate(draws); np.save(OUT/'cohort_bootstrap.npy', draws)
    for j, result in enumerate(descriptors):
        result['marginal95'] = np.quantile(draws[:, j], [.025, .975]).tolist()
        result['family16_band95'] = np.quantile(draws[:, j], [.025/16, 1-.025/16]).tolist()
    pooled = np.load(OUT/'POOLED_joint_bootstrap.npy')
    family16_lower = float(np.quantile(pooled[:, 0], .025/16))
    gates = {'cohort_nominal_points_above_floor': all(a['delta'] >= -.001 for a in descriptors),
        'cohort_nominal_lower95_above_floor': all(a['marginal95'][0] >= -.001 for a in descriptors),
        'cohort_family16_lower_above_floor': all(a['family16_band95'][0] >= -.001 for a in descriptors),
        'cohort_all_stress_points_above_floor': all(a['delta'] >= -.001 for a in stress),
        'pooled_nominal_family16_lower_positive': family16_lower > 0}
    result = {'author': 'Codex', 'utc': utc(), 'comparisons': descriptors, 'stress_points': stress,
        'gates': gates, 'pooled_nominal_family16_lower': family16_lower,
        'group_weights_same_design_as_P19_first4_exact': True,
        'new_bootstrap_contrasts': 6, 'replicates': 2000,
        'cohort_draws_sha256': w.sha(OUT/'cohort_bootstrap.npy'),
        'low_tail_resolution': 'Bonferroni16bounds use approximately3tail draws per2000; exploratory, no precision refinement or private confirmation.'}
    dump(OUT/'cohort_report.json', result)
    return result


def run():
    assert not w.read(e.state.PHASE).get('active_jobs')
    dump(OUT/'P23_execution_context.json', {'author': 'Codex', 'utc': utc(),
        'script': w.rel(Path(__file__)), 'script_sha256': w.sha(Path(__file__)),
        'changed_learning': 'one broker stage only; unchanged parents reused', 'raw_driver': w.rel(Path(e.__file__))})
    e.run()
    raw = w.read(OUT/'report.json'); cohort = cohort_analysis()
    dump(OUT/'P23_context_report.json', {'author': 'Codex', 'utc': utc(),
        'candidate': 'A1S_S2_broker_main_effect_with_unchanged_H1mean',
        'status': 'P23complete_algorithm_with_one_changed_stage_evaluated',
        'raw_engine_report': w.rel(OUT/'report.json'), 'raw_engine_report_sha256': w.sha(OUT/'report.json'),
        'raw_driver_prefix_P10_retained_not_candidate_identity': True,
        'global_gates': raw['diagnostic_gates'], 'new_business_gates': cohort['gates'],
        'all_exploratory_gates_pass': all(raw['diagnostic_gates'].values()) and all(cohort['gates'].values()),
        'new_primary_changed_stages': 30, 'adverse_changed_stages_separate': 30,
        'unchanged_parent_learning_reused_not_repeated': True,
        'new_source_fits': 0, 'new_C0_fits': 0, 'new_future_inference': 0, 'new_final_prices': 0,
        'new_submissions': 0, 'formal_promotion': False, 'private_improvement_established': False,
        'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True})
    print(json.dumps({'candidate': 'P23', 'global_gates': raw['diagnostic_gates'],
        'new_business_gates': cohort['gates'], 'cohort_points': descriptors_for_output(cohort)}))


def descriptors_for_output(cohort):
    return [{k: a[k] for k in ['evaluation', 'cohort', 'delta', 'marginal95']} for a in cohort['comparisons']]


def replay():
    e.replay()
    report = w.read(OUT/'cohort_report.json')
    saved = np.load(OUT/'cohort_bootstrap.npy')
    assert w.sha(OUT/'cohort_bootstrap.npy') == report['cohort_draws_sha256']
    totals, descriptors, _, _ = cohort_blocks()
    weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    assert np.allclose(score_cohort_sums(weights@totals), saved[:4], rtol=2e-12, atol=2e-13)
    for j, a in enumerate(report['comparisons']):
        assert descriptors[j]['delta'] == a['delta']
        assert np.array_equal(np.quantile(saved[:, j], [.025, .975]), a['marginal95'])
        assert np.array_equal(np.quantile(saved[:, j], [.025/16, 1-.025/16]), a['family16_band95'])
    dump(OUT/'P23_replay_context.json', {'author': 'Codex', 'utc': utc(),
        'raw_engine_replay': w.rel(OUT/'replay_report.json'),
        'raw_engine_replay_sha256': w.sha(OUT/'replay_report.json'),
        'cohort_points_saved_weights_and_intervals_verified': True,
        'new_resampling': 0, 'new_fits': 0, 'new_source_queries': 0,
        'context_report_sha256': w.sha(OUT/'P23_context_report.json')})
    print(json.dumps({'P23replay': 'exact', 'new_fits': 0, 'new_resampling': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    args = parser.parse_args()
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[args.mode]()
