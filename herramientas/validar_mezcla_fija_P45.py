"""Contrasta una mezcla geométrica fija de dos algoritmos protegidos guardados."""
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
PARENT = BASE/'P15_validacion_ausentes_20261026'
OUT = BASE/'P45_mezcla_fija_20261026'
PLAN = R/'registro/semana2_mezcla_fija_privada_plan.json'
INDEX = R/'registro/semana2_mezcla_fija_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P45_MEZCLA_FIJA.md'
sp = importlib.util.spec_from_file_location('p45_saved_metrics', R/'herramientas/validar_canal_privada_P23.py')
coh = importlib.util.module_from_spec(sp); sp.loader.exec_module(coh)
e = coh.e; w = e.w; np = e.np; pd = e.pd
e.OUT = OUT; coh.OUT = OUT
KEYS = ['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def post(body, identifier, subject):
    a = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', identifier, '--asunto', subject, '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    return json.loads(a.stdout)


def pool(first, second):
    """No outcomes, fitted weights, levels, clipping or batch normalizer."""
    a = np.asarray(first, dtype=float); b = np.asarray(second, dtype=float)
    assert a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
    assert (a > 0).all() and (b > 0).all()
    result = np.exp(.5*np.log(a)+.5*np.log(b))
    assert np.isfinite(result).all() and (result > 0).all()
    return result


def bind(reference, candidate):
    assert reference.row_id.is_unique and candidate.row_id.is_unique
    assert reference.row_id.notna().all() and candidate.row_id.notna().all()
    assert set(reference.row_id) == set(candidate.row_id)
    aligned = candidate.set_index('row_id', drop=False).loc[reference.row_id].reset_index(drop=True)
    for key in KEYS: assert np.array_equal(reference[key], aligned[key]), key
    assert reference.year.isin([2023, 2024]).all()
    return aligned


def synthetic():
    # D(y,mu)=4*y/sqrt(mu)+4*sqrt(mu)-8*sqrt(y).
    # D''(mu)=(3*y-mu)/mu**(5/2); D''(eta)=y*exp(-eta/2)+exp(eta/2)>0.
    # Therefore equal geometric pooling is <= the mean parent loss, NOT necessarily <= reference loss.
    arithmetic_loss = float(e.unit(np.array([0.]), np.array([5.]))[0])
    parent_mean_loss = float(.5*(e.unit(np.array([0.]), np.array([1.]))[0]+e.unit(np.array([0.]), np.array([9.]))[0]))
    assert arithmetic_loss > parent_mean_loss
    rng = np.random.default_rng(2026102645)
    a, b = np.exp(rng.uniform(-8, 12, (2, 4096))); y = np.exp(rng.uniform(-10, 14, 4096)); y[::3] = 0
    mixed = pool(a, b)
    gap = .5*(e.unit(y, a)+e.unit(y, b))-e.unit(y, mixed)
    assert (gap >= -2e-8).all()
    for old, new, geom in zip(a[:64], b[:64], mixed[:64]):
        assert math.isclose(geom, math.sqrt(old)*math.sqrt(new), rel_tol=3e-15)
    assert math.isclose(e.unit(y, mixed).mean(), e.mean_tweedie_deviance(y, mixed, power=1.5), rel_tol=2e-14)
    eta = np.linspace(-5, 8, 100); yy = np.linspace(0, 100, 100); step = 1e-3
    direct = (e.unit(yy, np.exp(eta+step))-2*e.unit(yy, np.exp(eta))+e.unit(yy, np.exp(eta-step)))/step**2
    hessian = yy*np.exp(-eta/2)+np.exp(eta/2)
    assert np.allclose(direct, hessian, rtol=1e-6, atol=2e-5)
    ratios = np.exp(rng.uniform(-2, 2, (4096, 5))); q = np.exp(rng.uniform(-1, 1, 4096))
    adapter = ratios.mean(axis=1)*q
    price_pool = pool(a*adapter, b*adapter)
    ultimate_first = mixed*adapter
    explicit_member_mean = np.mean(mixed[:, None]*ratios*q[:, None], axis=1)
    assert np.allclose(price_pool, ultimate_first, rtol=4e-15, atol=1e-12)
    assert np.allclose(price_pool, explicit_member_mean, rtol=4e-15, atol=1e-12)
    fixture = pd.DataFrame({'row_id': ['x'+str(i) for i in range(10)], 'line': 'motor', 'year': 2023,
        'new_business': True, 'fold': 0, 'group_id': ['g'+str(i) for i in range(10)], 'T0': np.arange(10.)})
    assert bind(fixture, fixture.iloc[::-1]).row_id.tolist() == fixture.row_id.tolist()
    rejected = []
    bad_frames = {'duplicate': pd.concat([fixture, fixture.iloc[:1]], ignore_index=True),
        'missing': fixture.iloc[:-1].copy(), 'year': fixture.assign(year=2024),
        'group': fixture.assign(group_id='different'), 'fold': fixture.assign(fold=1),
        'target': fixture.assign(T0=-1.), 'line': fixture.assign(line='buildings')}
    for name, bad in bad_frames.items():
        try: bind(fixture, bad)
        except AssertionError: rejected.append(name)
        else: raise AssertionError('Adverse binding accepted: '+name)
    for value in [0., -1., float('nan'), float('inf')]:
        try: pool([1.], [value])
        except AssertionError: pass
        else: raise AssertionError('Invalid parent price accepted')
    return {'author': 'Codex', 'utc': utc(), 'arithmetic_counterexample_y0_prices1_9':
        {'loss_arithmetic_mean': arithmetic_loss, 'mean_parent_loss': parent_mean_loss},
        'D_eta_hessian': 'y*exp(-eta/2)+exp(eta/2)>0 for finite eta,y>=0',
        'minimum_geometric_Jensen_gap_fixture': float(gap.min()),
        'finite_difference_hessian_pass': True, 'independent_scalar_pool_and_sklearn_metric_pass': True,
        'common_adapter_and_five_member_flow_pass': True, 'adverse_key_controls_rejected': rejected,
        'invalid_prices_rejected': 4, 'new_fits': 0, 'contest_candidate_scores_computed': 0,
        'limit': 'Jensen bounds average parent loss; no guaranteed improvement over reference or private performance.'}


def check_sources(plan):
    changed = [k for k, v in plan['sources'].items() if w.sha(ROOT/k) != v]
    assert not changed, changed


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json')
    assert not phase.get('active_execution') and not phase.get('active_jobs')
    OUT.mkdir(); fixture = synthetic(); dump(OUT/'synthetic.json', fixture)
    parent_plan_path = R/'registro/semana2_GLM_ausentes_validacion_plan.json'; old = w.read(parent_plan_path)
    assert all(w.sha(ROOT/k) == v for k, v in old['sources'].items())
    replay = w.read(PARENT/'replay_report.json'); assert replay['learning_and_source_inference_blocked'] and replay['held_payload_poisoned'] and replay['scopes'] == 30
    assert replay['report_sha256'] == w.sha(PARENT/'report.json')
    assert w.read(PARENT/'registration.json')['plan_sha256'] == w.sha(parent_plan_path)
    sources = dict(old['sources']); paths = [Path(__file__), Path(e.__file__), Path(coh.__file__), parent_plan_path,
        PARENT/'registration.json', PARENT/'report.json', PARENT/'context_report.json', PARENT/'completion_receipt.json',
        PARENT/'replay_report.json', PARENT/'P15_replay_context.json', OUT/'synthetic.json',
        R/'registro/semana2_marca_capital_validacion_privada_plan.json',
        BASE/'P19_cohortes_broker_20261026/group_universe.json', BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy']
    bindings = []; template = w.read(R/'registro/semana2_marca_capital_validacion_privada_plan.json')
    assert old['scopes'] == template['scopes'] and old['criteria'] == template['criteria']
    for s in old['scopes']:
        folder = PARENT/f"{s['cohort']}_{s['line']}_{s['outer']}"; commit = w.read(folder/'committed.json')
        assert commit['scope'] == s and commit['held_poison_current_learning_exact'] and commit['unchanged_C0_N3_H1_not_reestimated']
        assert all(w.sha(ROOT/k) == v for k, v in commit['outputs'].items())
        a = w.read(folder/'learning.json'); bad = w.read(folder/'poison_learning.json')
        assert a == bad and a['fit_groups_digest'] == s['training_groups_digest'] and a['fit_row_ids_digest'] == s['training_row_digest']
        f = pd.read_parquet(folder/'prices.parquet'); assert f.row_id.is_unique
        assert all(np.isfinite(f[k]).all() and f[k].gt(0).all() for k in ['old_ultimate', 'new_ultimate', 'fixed_adapter', 'old_nominal', 'new_nominal'])
        assert np.array_equal(f.new_ultimate*f.fixed_adapter, f.new_nominal)
        assert np.allclose(f.old_ultimate*f.fixed_adapter, f.old_nominal, rtol=2e-15)
        bindings.append({'cohort': s['cohort'], 'line': s['line'], 'outer': s['outer'], 'rows': len(f),
            'parents_held_poison_identical': True, 'common_adapter_positive': True, 'training_groups_digest': s['training_groups_digest']})
        paths += list(folder.iterdir())
    for evaluation in ['POOLED', 'TRANSFER']:
        path = PARENT/(evaluation+'_prices.parquet'); paths.append(path); f = pd.read_parquet(path)
        assert f.row_id.is_unique and f.year.isin([2023, 2024]).all()
        original = pd.read_parquet(e.P2/'held_nested_prices.parquet' if evaluation == 'POOLED' else e.P4/'held2024_transfer_prices.parquet')
        original = bind(f[KEYS], original)
        assert np.array_equal(f.old_nominal, original.T_B if evaluation == 'POOLED' else original.nominal_mean)
        scoped = pd.concat([pd.read_parquet(PARENT/f'{evaluation}_{line}_{k}/prices.parquet') for line in e.h.LINES for k in range(5)]).set_index('row_id').loc[f.row_id]
        assert np.array_equal(f.new_nominal, scoped.new_nominal) and np.array_equal(f.old_nominal, scoped.old_nominal)
        ratio = f.new_nominal.to_numpy()/f.old_nominal.to_numpy()
        for name in e.NAMES[1:]:
            assert np.allclose(f[name+'_new']/f[name+'_old'], ratio, rtol=3e-15)
        bindings.append({'evaluation': evaluation, 'rows': len(f), 'exact_common_reference_keys_and_prices': True,
            'common_scenario_adapter_ratio': True, 'new_candidate_prices_or_scores': 0})
    cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet', filters=[('year', 'in', [2023, 2024])])
    assert not cov.is_test.any() and cov.row_id.is_unique
    cov.to_parquet(OUT/'covariates.parquet', index=False); paths.append(OUT/'covariates.parquet')
    dump(OUT/'binding_preflight.json', {'author': 'Codex', 'utc': utc(), 'bindings': bindings,
        'new_learning_or_inference': 0, 'ancestry': 'P15 source/target/C0/N3/H1 parents reused by hashes and unchanged replay; not refitted or independently reviewed.'})
    paths.append(OUT/'binding_preflight.json')
    novelty = []
    for path in sorted((R/'registro').glob('semana2_*plan*.json')):
        z = w.read(path)
        wording = ' '.join(str(z.get(k, '')) for k in ['candidate', 'hypothesis', 'change', 'configuration', 'primary_comparator'])
        if 'P15' in wording or 'GLM4_MI' in wording: novelty.append({'path': w.rel(path), 'sha256': w.sha(path)})
        assert not ('GLM4_MI' in wording and 'geometric' in wording.lower() and 'complete-price' in wording.lower())
    dump(OUT/'novelty.json', {'author': 'Codex', 'utc': utc(), 'scope': 'Current registered semana2_*plan*.json candidate/hypothesis/change/configuration/comparator fields, plus bounded code search recorded in session.',
        'related_plans': novelty, 'same_registered_whole_price_recipe_found': False,
        'prior_arithmetic_proposal_not_tested': True, 'reason_for_prospective_change': 'Analytic log-link convexity and synthetic arithmetic counterexample before any new contest price or score; no outcome-based choice.'})
    paths.append(OUT/'novelty.json'); sources.update({w.rel(k): w.sha(k) for k in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Equal_log_cost_pool_protected_reference_and_P15_GLM4_MI',
        'hypothesis': 'A fixed equal log-cost pool of standard tree-transfer and additive-GLM-transfer complete algorithms may reduce functional-family error without extra training or learned weights. Individual failed gates remain; pooling needs its own full gates.',
        'change': 'One fixed geometric complete-price mixture only: exp(0.5*log(reference)+0.5*log(P15)). Same C0/N3/source-known adapter/ultimate bridge and mean five H1/G3 ratios; no new levels, normalizers, weights or recipes.',
        'prospective_amendment': 'P44 future text proposed arithmetic pooling but was not a registered experiment. Before scoring, replace by geometric pooling on log-convex Tweedie1.5 grounds; no arithmetic contest candidate is scored.',
        'formula': {'ultimate': 'U_pool=sqrt(U_reference*U_P15)', 'observed': 'P_pool=A_common*U_pool=sqrt(P_reference*P_P15)',
            'five_member': 'For the SAME five ratios, A_common=q_source*mean(R_j). This does not replace the H1 arithmetic member mean by a geometric member mean.'},
        'primary_comparator': 'Original complete protected A1S/S2/H1 reference, unchanged. Not delivered F3c reconstruction or hidden-private score.',
        'configuration': {'log_weights': [.5, .5], 'new_level_or_normalizer': None, 'selection_by_line_fold_or_cohort': False,
            'after_failure': 'Keep adverse; no weight search, arithmetic fallback, clipping or favorable-line rescue within P45.'},
        'budget': {'new_source_fits': 0, 'new_target_fits': 0, 'new_C0_fits': 0, 'new_constants': 0,
            'new2025inference': 0, 'new_submissions': 0, 'new_primary_candidate': 1,
            'global_bootstrap_replicates': 2000, 'cohort_bootstrap_replicates': 2000},
        **{k: template[k] for k in ['criteria', 'bootstrap', 'level_sensitivity', 'sensitivity', 'cohort_guard', 'limits']},
        'scopes': old['scopes'], 'sources': sources,
        'preflight': {'synthetic': w.rel(OUT/'synthetic.json'), 'binding': w.rel(OUT/'binding_preflight.json'), 'new_candidate_scores': 0},
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'private_improvement_established': False}
    plan['limits'] += ['Geometric Jensen bound is versus average parent deviance, not the reference, and cannot prove private improvement.',
        'Source includes developed2024; destination2023-to2024 transfer is conditional, not prospective.',
        'Adaptive model search, source reporting/peril-mixture assumptions, rare NBsupport, undated masters and tail/reserve uncertainty remain.']
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. P45 preinscrito antes de producir precios o puntuar la mezcla. Dos familias estándar ya guardadas: referencia completa y GLM con indicadores de ausencia P15. Pesos fijos 1/2 sobre log-coste, sin aprender pesos, normalizadores o niveles. La propuesta aritmética futura de P44 se corrige antes del resultado: D(y,mu) no es convexa en mu; sí lo es en log(mu). Contraejemplo sintético y derivada por diferencias finitas guardados. La cota es frente al promedio de pérdidas de ambos padres, no una garantía frente a la referencia. Se verificaron treinta ámbitos, padres/adversos, claves y adaptador común; se conserva la media aritmética de cinco H1/G3. Mismos mínimos/intervalos/folds/años/celdas/Post31 y guardas NB/broker/historia cero, reservas/cola y familia16. Cero ajustes fuente/destino/C0, constantes nuevas, inferencias2025 o envíos. No probar otros pesos o mezcla aritmética si falla. B00/F3c y adversos conservados;2024 abierto adaptativo, privada prioritaria. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P45registered_before_pool_prices_or_scores', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN),
        'forum': post(body, 'COD-S2-20261026-PRIVADA-P45-MEZCLA-PREVIO', 'P45: mezcla fija de dos familias, corrección matemática antes de puntuar')}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps(receipt))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); check_sources(plan); assert w.read(OUT/'registration.json')['plan_sha256'] == w.sha(PLAN)
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json'); assert not phase.get('active_jobs') and not phase.get('active_execution')
    # Guard the actual entry points, even though only saved row predictions are consumed.
    def reject(*args, **kwargs): raise AssertionError('P45 prohibits training and source model inference')
    for module, key in [(e.core, 'learn'), (e.core, 'fit_component'), (e.b, 'shape_fit'), (e.b, 'cell_levels'),
        (e.b, 'factor'), (e.g, 'fit_stage'), (e.parent.v, 'fit_reporting'), (e.state.lgb, 'Booster'), (e.state.lgb, 'train')]:
        setattr(module, key, reject)
    dump(OUT/'started.json', {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'script': w.rel(Path(__file__)), 'kind': 'P45saved_price_pool_no_fit'})
    results = {}; flow = []
    for evaluation in ['POOLED', 'TRANSFER']:
        f = pd.read_parquet(PARENT/(evaluation+'_prices.parquet')); saved = f.copy()
        old = f.old_nominal.to_numpy(float); parent = f.new_nominal.to_numpy(float); mixed = pool(old, parent)
        saved['new_nominal'] = mixed
        reserves = pd.concat([pd.read_parquet(e.P1/f'canonical_{line}.parquet', columns=['row_id', 'reserve']) for line in e.h.LINES]).set_index('row_id').loc[f.row_id].reserve.to_numpy(float)
        y = f.T0.to_numpy(float); ys = [y, y-.25*reserves, y+.25*reserves, y, y]
        data = [(y, old, mixed)]
        for j, name in enumerate(e.NAMES[1:], 1):
            base = f[name+'_old'].to_numpy(float); other = f[name+'_new'].to_numpy(float)
            m = pool(base, other); saved[name+'_new'] = m
            assert np.allclose(m/base, mixed/old, rtol=4e-15)
            data.append((ys[j], base, m))
        scopes = []
        for line in e.h.LINES:
            for k in range(5):
                scoped = pd.read_parquet(PARENT/f'{evaluation}_{line}_{k}/prices.parquet')
                u = pool(scoped.old_ultimate, scoped.new_ultimate); bridged = u*scoped.fixed_adapter.to_numpy()
                target = saved.set_index('row_id').loc[scoped.row_id].new_nominal.to_numpy()
                assert np.allclose(target, bridged, rtol=4e-15, atol=1e-12)
                scopes.append(float(np.max(np.abs(target/bridged-1))))
        saved.to_parquet(OUT/(evaluation+'_prices.parquet'), index=False)
        weights = pd.read_parquet(BASE/'estimando_cartera2025_v3/weights.parquet').set_index('row_id').loc[f.row_id]
        assert np.array_equal(weights.group_id, f.group_id)
        results[evaluation] = e.metrics(f[KEYS], data, evaluation, weights.weight.to_numpy(float), plan)
        flow.append({'evaluation': evaluation, 'scopes': 15, 'max_ultimate_bridge_relative_error': max(scopes),
            'price_function_has_no_outcome_input': True, 'learn_and_source_model_entry_points_blocked': True})
    a = results['POOLED']['NOMINAL']; t = results['TRANSFER']['NOMINAL']; crit = plan['criteria']
    gates = {'pooled_delta_ge002': a['delta'] >= crit['nominal_pooled_delta_min'], 'pooled_lower95_positive': a['bootstrap95'][0] > 0,
        'pooled_atleast4positive_folds': sum(v > 0 for v in a['folds'].values()) >= 4,
        'both_pooled_years_nonnegative': min(a['years'].values()) >= 0, 'pooled_post31_nonnegative': a['post31_delta'] >= 0,
        'conditional_transfer_nonnegative': t['delta'] >= 0,
        'all_nominal_and_stress_cell_floors': all(v['worst_cell_delta'] >= crit['all_nominal_and_stress_cell_floors'] for z in results.values() for v in z.values())}
    cohorts = coh.cohort_analysis(); check_sources(plan)
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P45fixed_pool_complete', 'plan_sha256': w.sha(PLAN),
        'results': results, 'global_gates': gates, 'new_business_gates': cohorts['gates'],
        'all_exploratory_gates_pass': all(gates.values()) and all(cohorts['gates'].values()), 'flow': flow,
        'new_fits': 0, 'new_C0_fits': 0, 'new_constants': 0, 'new2025inference': 0, 'new_submissions': 0,
        'adopted': False, 'private_improvement_established': False, 'goal_achieved': False,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(OUT/'report.json', report)
    print(json.dumps({'status': report['status'], 'nominal': {k: {j:v['NOMINAL'][j] for j in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']} for k, v in results.items()}, 'global_gates': gates, 'new_business_gates': cohorts['gates']}))


def replay():
    assert not (OUT/'replay_report.json').exists(); plan = w.read(PLAN); check_sources(plan); report = w.read(OUT/'report.json')
    errors = []; semantic = []
    for evaluation in ['POOLED', 'TRANSFER']:
        old = pd.read_parquet(PARENT/(evaluation+'_prices.parquet')); saved = pd.read_parquet(OUT/(evaluation+'_prices.parquet'))
        bind(old, saved)
        for first, second, target in [('old_nominal', 'new_nominal', 'new_nominal')]+[(n+'_old', n+'_new', n+'_new') for n in e.NAMES[1:]]:
            independent = np.sqrt(old[first].to_numpy())*np.sqrt(old[second].to_numpy())
            assert np.allclose(independent, saved[target], rtol=4e-15, atol=1e-12)
            assert np.array_equal(pool(old[first], old[second]), saved[target])
            # Poisoned targets cannot change a two-price-only function.
            bad = old.assign(T0=-1e30); assert np.array_equal(pool(bad[first], bad[second]), saved[target])
            errors.append(float(np.max(np.abs(independent/saved[target]-1))))
        reserve = pd.concat([pd.read_parquet(e.P1/f'canonical_{line}.parquet', columns=['row_id', 'reserve']) for line in e.h.LINES]).set_index('row_id').loc[saved.row_id].reserve.to_numpy(float)
        yy = saved.T0.to_numpy(float); ys = [yy, yy-.25*reserve, yy+.25*reserve, yy, yy]
        draws = np.load(OUT/(evaluation+'_joint_bootstrap.npy'))
        for j, n in enumerate(e.NAMES):
            a = saved.old_nominal.to_numpy() if j == 0 else saved[n+'_old'].to_numpy()
            b = saved.new_nominal.to_numpy() if j == 0 else saved[n+'_new'].to_numpy(); y = ys[j]
            scalar_gain = math.fsum((4*float(yv)*(1/math.sqrt(float(av))-1/math.sqrt(float(bv)))+4*(math.sqrt(float(av))-math.sqrt(float(bv)))) for yv, av, bv in zip(y, a, b))
            scalar_den = 8*(math.sqrt(len(y)*math.fsum(y.tolist()))-math.fsum(math.sqrt(float(v)) for v in y))
            assert math.isclose(scalar_gain/scalar_den, report['results'][evaluation][n]['delta'], rel_tol=1e-9, abs_tol=1e-12)
            assert np.array_equal(np.quantile(draws[:, j], [.025, .975]), report['results'][evaluation][n]['bootstrap95'])
        semantic.append({'evaluation': evaluation, 'scalar_metric_and_saved_intervals_exact': True})
    totals, desc, _, _ = coh.cohort_blocks(); weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    saved = np.load(OUT/'cohort_bootstrap.npy'); cohorts = w.read(OUT/'cohort_report.json')
    assert np.allclose(coh.score_cohort_sums(weights@totals), saved[:4], rtol=2e-12, atol=2e-13)
    for j, z in enumerate(cohorts['comparisons']):
        assert desc[j]['delta'] == z['delta'] and np.array_equal(np.quantile(saved[:, j], [.025/16, 1-.025/16]), z['family16_band95'])
    check_sources(plan)
    dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(), 'status': 'P45replay_pass',
        'report_sha256': w.sha(OUT/'report.json'), 'max_scalar_pool_relative_error': max(errors), 'cohort_points_and_saved_first4_weights_exact': True,
        'results': semantic, 'new_fits': 0, 'new_source_inference': 0, 'new_resampling': 0,
        'held_target_poison_invariant_new_pool_only_parent_flow_by_unchanged_hash': True})
    print(json.dumps({'replay': 'passed', 'max_relative_error': max(errors), 'new_fits': 0, 'new_resampling': 0}))


def close():
    assert not (OUT/'completion_receipt.json').exists(); d = w.read(OUT/'report.json'); replay = w.read(OUT/'replay_report.json')
    assert replay['report_sha256'] == w.sha(OUT/'report.json')
    passed = d['all_exploratory_gates_pass']
    next_unit = ('Audit exact production and admission; exploratory gates alone do not authorize automatic promotion.' if passed else
        'P46: inspect the complete target observation/response contract and the already saved P13allocated-loss cells alongside group support, before selecting another model. All standard source-family changes and this fixed mixture failed current whole-algorithm robustness. Isolate whether one material observation/exposure or validation-target uncertainty can be resolved with existing legitimate evidence, or document a concrete standard target-level hypothesis with protected prospective comparison. Do not repeat prior audits on unchanged inputs, search mixture weights or add source capacity to chase public/private proxies. Preserve failed P45 and no automatic upload.')
    text = '# P45: mezcla fija entre referencia y GLM\n\nCodex, '+utc()+'. '+('Pasan las guardas exploratorias; falta revisar producción y admisión exactas.' if passed else 'La mezcla no supera las guardas conjuntas y no se adopta ni se envía.')
    text += '\n\nSe combinan por media geométrica los costes completos de la referencia y el GLM P15. Los pesos son fijos e iguales sobre log-coste; no hay ajustes, niveles o normalizadores nuevos. La media de cinco cocientes H1/G3 y el adaptador común se conservan. La propuesta aritmética futura de P44 se corrigió por la convexidad de la pérdida respecto al log-coste antes de calcular o puntuar esta mezcla. Esa cota limita la pérdida frente al promedio de ambos padres; no garantiza mejora frente a la referencia.\n\n| Nominal | Δ D² frente a referencia | IC95 por grupos | Post31 | Peor celda |\n|---|---:|---|---:|---:|\n'
    nominal = {}
    for evaluation in ['POOLED', 'TRANSFER']:
        z = d['results'][evaluation]['NOMINAL']; nominal[evaluation] = {k:z[k] for k in ['delta', 'bootstrap95', 'post31_delta', 'worst_cell_delta']}
        text += f"| {evaluation} | {z['delta']:+.7f} | [{z['bootstrap95'][0]:+.7f}; {z['bootstrap95'][1]:+.7f}] | {z['post31_delta']:+.7f} | {z['worst_cell_delta']:+.7f} |\n"
    text += '\nGuardas globales: '+json.dumps(d['global_gates'])+'. Guardas NB/broker/historia cero: '+json.dumps(d['new_business_gates'])+'. Se guardan todos los folds, años, ramos, escenarios y sensibilidades de nivel, incluidos los adversos. No se probaron pesos alternativos o una mezcla aritmética tras conocer el resultado.\n\n'
    text += 'Se cotejaron treinta ámbitos y sus padres/adversos por hash. El nuevo flujo consume únicamente precios guardados; ajustes e inferencia fuente bloqueados. La composición en coste último y observado concuerda, con controles de claves, precios inválidos y etiquetas alteradas; replay por raíces escalares, métrica por sumas independientes y cuatro multiplicidades de remuestreo guardadas, sin ajustes o remuestreo nuevos. Los replays de aprendizaje de padres se reutilizan por bytes idénticos, no se presentan como repetidos hoy. Cero ajustes fuente/destino/C0, constantes nuevas, inferencias2025 y envíos.\n\n'
    text += '2024 es desarrollo abierto y adaptativo. La transferencia es condicional a fuente desarrollada que incluye2024; no prueba prospectiva. Persisten maestros sin fecha, soporte escaso en algunas cohortes y reservas/cola no identificadas. No hay demostración de mejora privada ni revisión profesional independiente. B00, F3c y todas las alternativas se conservan.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'replay_report.json')+'.\n'
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P45complete_not_automatically_admitted', 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'replay': w.rel(OUT/'replay_report.json'), 'replay_sha256': w.sha(OUT/'replay_report.json'), 'document': w.rel(DOC),
        'nominal': nominal, 'all_exploratory_gates_pass': passed, 'global_gates': d['global_gates'], 'new_business_gates': d['new_business_gates'],
        'new_fits': 0, 'new_C0_fits': 0, 'new_constants': 0, 'new2025inference': 0, 'new_submissions': 0, 'adopted': False,
        'next_unit': next_unit, 'goal_achieved': False, '2024_open': True, 'B00_all_alternatives_preserved': True,
        'forum': post(body, 'COD-S2-20261026-PRIVADA-P45-MEZCLA-RESULTADO', 'P45: resultado de la mezcla fija y replay sin reentrenar')}
    archive = R/'privado'/('corte_P45_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P45': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P45': receipt, 'next_unit': next_unit}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']; own.update(private_P45=receipt, next_unit=next_unit)
    w.update(path, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P45: mezcla fija sin entrenamiento\n\nCodex, '+receipt['utc']+'. Guardas conjuntas='+str(passed)+'. Mezcla geométrica fija de referencia/GLM P15, corrección matemática previa al resultado, treinta ámbitos protegidos. Cero ajustes/constantes/inferencias2025/envíos; adversos y B00 conservados. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_fixed_pool_index': w.rel(INDEX), 'week_2_private_fixed_pool_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'all_gates_pass': passed, 'new_fits': 0, 'new_submissions': 0, 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'replay', 'close']); mode = parser.parse_args().mode
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay, 'close': close}[mode]()
