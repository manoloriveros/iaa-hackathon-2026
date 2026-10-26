"""Prueba completa de P36 con las guardas privadas y el rango climático declarado."""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
sp = importlib.util.spec_from_file_location('p37_strict_adapter', R/'herramientas/validar_ausencias_privada_P26.py')
prior = importlib.util.module_from_spec(sp); sp.loader.exec_module(prior)
e = prior.e; previous = prior.previous; w = prior.w; pd = prior.pd; np = prior.np
BASE = prior.BASE; SOURCE = BASE/'P36_fuente_clima_20261026'; WEATHER = BASE/'P35_entradas_clima_20261026'
OUT = BASE/'P37_validacion_clima_20261026'
PLAN = R/'registro/semana2_clima_A1S_validacion_privada_plan.json'
INDEX = R/'registro/semana2_clima_A1S_validacion_privada_actual.json'
e.OUT = OUT; e.P9 = SOURCE; e.PLAN = PLAN; e.INDEX = INDEX
previous.OUT = OUT; previous.PLAN = PLAN; previous.INDEX = INDEX; previous.COV = None


def utc(): return datetime.now(timezone.utc).isoformat()


def execution_state(execution):
    if execution is not None: execution = {**execution, 'script': w.rel(Path(__file__)), 'kind': 'P37complete_climate_source_validation', 'raw_driver': w.rel(Path(e.__file__))}
    prior.ORIGINAL_STATE(execution)


e.state.state_execution = execution_state


def score_range_sums(sums):
    values = []
    for j in range(sums.shape[1]//4):
        n, sy, sq, gain = sums[:, 4*j:4*j+4].T; null = 8*(np.sqrt(n*sy)-sq)
        assert np.isfinite(null).all() and (null > 1e-9).all(), 'No replacing unsupported bootstrap draws'
        values.append(gain/null)
    return np.column_stack(values)


def synthetic_range():
    y = np.array([0., 1., 2., 0., 5., 10.]); old = np.full(6, 2.); new = old*1.1
    gain = e.unit(y, old)-e.unit(y, new)
    sums = np.array([[6., y.sum(), np.sqrt(y).sum(), gain.sum()]])
    value = float(score_range_sums(sums)[0, 0]); null = e.unit(y, np.full(6, y.mean())).sum()
    assert math.isclose(value, gain.sum()/null, rel_tol=2e-13)
    assert math.isclose(value, (e.mean_tweedie_deviance(y, old, power=1.5)-e.mean_tweedie_deviance(y, new, power=1.5))/e.mean_tweedie_deviance(y, np.full(6, y.mean()), power=1.5), rel_tol=2e-13)
    return {'range_block_metric_two_methods': True, 'no_fits': True}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(e.state.PHASE).get('active_jobs')
    source = w.read(SOURCE/'report.json'); closed = w.read(SOURCE/'completion_receipt.json')
    assert source['source_veto_all_pass'] and source['new_source_fits'] == 18
    assert closed['report_sha256'] == w.sha(SOURCE/'report.json')
    assert all(w.sha(ROOT/p) == sha for p, sha in source['outputs'].items())
    OUT.mkdir(); template = w.read(R/'registro/semana2_frecuencia_marca_validacion_privada_plan.json')
    common = w.read(R/'registro/semana2_canal_privada_plan.json')
    sources = {p: sha for p, sha in common['sources'].items() if 'P23_canal_principal_20261026/' not in p}
    assert all(w.sha(ROOT/p) == sha for p, sha in sources.items())
    paths = [Path(__file__), Path(prior.__file__), Path(previous.__file__), SOURCE/'report.json', SOURCE/'completion_receipt.json',
        SOURCE/'scalar_replay.json', SOURCE/'pre_fit_covariate_warning.json', SOURCE/'pre_fit_covariate_warning_receipt.json',
        R/'registro/semana2_fuente_clima_A1S_privada_plan.json', R/'herramientas/fuente_clima_A1S_P36.py',
        BASE/'P26_validacion_ausencias_20261026/synthetic_adapter.json', BASE/'P26_validacion_ausencias_20261026/P26_replay_context.json']
    cov = pd.read_parquet(BASE/'P19_cohortes_broker_20261026/covariates.parquet', filters=[('year', 'in', [2023, 2024])])
    assert not cov.is_test.any() and cov.row_id.is_unique
    cov.to_parquet(OUT/'covariates.parquet', index=False); paths.append(OUT/'covariates.parquet')
    scopes = []; flags = []; bounds = {}
    for line in e.h.LINES:
        path = SOURCE/f'historical_{line}_three_seed.parquet'; relative = pd.read_parquet(path); prior.strict_relative(relative); paths.append(path)
        canonical = pd.read_parquet(e.P1/f'canonical_{line}.parquet', columns=['row_id', 'year'])
        assert set(relative.row_id) == set(canonical.row_id); prior.attach_relative(canonical, relative)
        for scope in [a for a in template['scopes'] if a['line'] == line]:
            f, held, _ = e.get_scope(scope['cohort'], line, scope['outer'], relative); train = f.fold.ne(held)
            assert e.b.digest(sorted(f.loc[train, 'row_id'])) == scope['training_row_digest']
            assert e.b.digest(sorted(set(f.loc[train, 'group_id']))) == scope['training_groups_digest']; scopes.append(scope)
        weather = pd.read_parquet(WEATHER/f'weather_s1_{line}.parquet', columns=['annual_wildfire_index'])
        lo = float(weather.annual_wildfire_index.min()); hi = float(weather.annual_wildfire_index.max()); bounds[line] = {'source_full_min': lo, 'source_full_max': hi}
        target = pd.read_parquet(WEATHER/f'weather_s2_historical_{line}.parquet', columns=['row_id', 'year', 'annual_wildfire_index'])
        assert target.year.isin([2023, 2024]).all() and set(target.row_id) == set(canonical.row_id)
        target['outside_wildfire_source_range'] = (target.annual_wildfire_index < lo)|(target.annual_wildfire_index > hi)
        flags.append(target[['row_id', 'year', 'outside_wildfire_source_range']])
        paths += [WEATHER/f'weather_s1_{line}.parquet', WEATHER/f'weather_s2_historical_{line}.parquet']
        for seed in [11, 12, 13]:
            folder = SOURCE/f'{line}_seed{seed}_full'; record = w.read(folder/'fit_record.json')
            assert record['model_sha256'] == w.sha(folder/'model.txt')
            paths += [folder/'model.txt', folder/'fit_record.json', folder/'application.json']
    assert len(scopes) == 30
    flags = pd.concat(flags, ignore_index=True); assert flags.row_id.is_unique
    flags.to_parquet(OUT/'range_flags.parquet', index=False); paths.append(OUT/'range_flags.parquet')
    fixture = synthetic_range(); prior.dump(OUT/'synthetic_range.json', fixture); paths.append(OUT/'synthetic_range.json')
    sources.update({w.rel(p): w.sha(p) for p in paths})
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'Annual_weather_source_original_50_50_S2_H1',
        'hypothesis': 'The same-capacity source tree with annual climate may transport risk allocation better than current A1S. Source veto and full-target robustness are distinct requirements.',
        'change': 'Only P36source annual relativities; original50/50N3, residual stages,5H1/G3mean and original qsource observation/evaluation bridge unchanged. No new risk-dependent observation link.',
        'primary_comparator': template['primary_comparator'], 'configuration': template['configuration'], 'changed_learning': template['changed_learning'],
        'budget': template['budget'], 'exposure': template['exposure'], 'sensitivity': template['sensitivity'], 'criteria': template['criteria'],
        'bootstrap': template['bootstrap'], 'level_sensitivity': template['level_sensitivity'], 'cohort_guard': template['cohort_guard'],
        'source_identity': 'Original3seeds11/12/13geometric mean; same parameters/rounds plus seven annual weather fields. Related E13/T7/T8adverses retained.',
        'additional_wildfire_range_guard': {'bounds': bounds, 'rule': 'Inside/outside the FULLsource historical empirical min/max, no learned cutoff. Only historical emerging rows evaluated.',
            'contrasts': 'POOLED/TRANSFER xinside/outside=4nominal contrasts, plus all4stress points in each. Also report positive groups by line/period/business; no cross-market support substitution.',
            'positive_cost_groups_aggregate_each_contrast_min': 100, 'nominal_point_floor': -.001, 'nominal_lower95_floor': -.001, 'family20_lower_floor': -.001,
            'stress_point_floor': -.001, 'bootstrap_replicates': 2000, 'bootstrap_seed': 2026102660,
            'family': 'Existing10global+6NB+4range=20; keep original family16gates and additionally inspect stricter family20bands for pooled nominal and6NBcontrasts. No claim of a private risk interval.',
            'limit': 'Marginal range does not certify multivariate support or the actual future outcome response. Sparse line/cell warnings and source/commonC0uncertainty persist.'},
        'preflight': {'new30scope_memberships_exact': True, 'unchanged_strict_adapter_fixture': w.rel(BASE/'P26_validacion_ausencias_20261026/synthetic_adapter.json'),
            'unchanged_learning_forward_replays': w.rel(BASE/'P26_validacion_ausencias_20261026/P26_replay_context.json'), 'changed_range_metric_fixture': fixture,
            'new_synthetic_price_fits': 0},
        'scopes': scopes, 'sources': sources, 'limits': common['limits']+[
            'Future wildfire exceeds source range on about23%of official2025rows; target range diagnostics are necessary but do not identify future extrapolation.',
            'Source-held round selection/observation/category ancestors and climate region/year dependence remain conditional/adaptive.',
            'Annual weather is conditional retrospective official input, not quote-time forecasts. Target2024alreadyadaptive; no private guarantee.'],
        'B00_all_alternatives_preserved': True, '2024_open': True}
    prior.dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. Registro P37antes del aprendizaje destino: solo cambian las relatividades P36; mezcla50/50N3, residuales originales, media H1/G3y qsource quedan fijos.30calibraciones primarias y30adversas, sin nuevos modelos fuente/C0o inferencias2025. Se conservan todas las guardas P30globales, NB/broker/historia cero y familia16. Por el soporte wildfire conocido antes del ajuste, se añaden cuatro contrastes dentro/fuera del rango fuente completo, mínimo100grupos positivos agregados y pisos de diferencia/intervalos -0,001; familia20incluye los16contrastes previos. También se conservarán celdas pequeñas por ramo. No se ajusta el rango para pasar ni se interpreta como soporte multivariante o prueba privada. Adaptador/flujos sin cambios reutilizados por SHA; solo se comprobó la métrica adicional nueva. B00/F3c/alternativas conservados,2024abierto. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    post = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P37-CLIMA-VALIDACION-PREVIO', '--asunto', 'P37: algoritmo completo con clima y guardas de rango antes de ajustar', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P37registered_before_target_learning', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(post.stdout)}
    prior.dump(OUT/'registration.json', receipt); prior.dump(INDEX, receipt); print(json.dumps({'registered': True, 'scopes': 30, 'forum': receipt['forum']}))


def range_blocks():
    flags = pd.read_parquet(OUT/'range_flags.parquet').set_index('row_id')
    universe = w.read(BASE/'P19_cohortes_broker_20261026/group_universe.json')
    reserves = pd.concat([pd.read_parquet(e.P1/f'canonical_{line}.parquet', columns=['row_id', 'reserve']) for line in e.h.LINES]).set_index('row_id')
    blocks = []; desc = []; stresses = []
    for evaluation in ['POOLED', 'TRANSFER']:
        f = pd.read_parquet(OUT/f'{evaluation}_prices.parquet'); extra = flags.loc[f.row_id]
        assert np.array_equal(extra.year, f.year)
        for outside in [False, True]:
            z = f.loc[extra.outside_wildfire_source_range.to_numpy(bool) == outside]; y = z.T0.to_numpy(float)
            assert len(z) and (y > 0).any(), 'Retain insufficient range cohort, no pseudo-events'
            gains = e.unit(y, z.old_nominal.to_numpy())-e.unit(y, z.new_nominal.to_numpy()); null = e.unit(y, np.full(len(y), y.mean())).sum()
            vals = np.column_stack([np.ones(len(y)), y, np.sqrt(y), gains])
            blocks.append(pd.DataFrame(vals).assign(group=z.group_id.to_numpy()).groupby('group').sum().reindex(universe, fill_value=0).to_numpy())
            independent = (e.mean_tweedie_deviance(y, z.old_nominal, power=1.5)-e.mean_tweedie_deviance(y, z.new_nominal, power=1.5))/e.mean_tweedie_deviance(y, np.full(len(y), y.mean()), power=1.5)
            assert math.isclose(gains.sum()/null, independent, rel_tol=2e-10, abs_tol=2e-13)
            bycell = []
            for keys, cell in z.groupby(['line', 'year', 'new_business']):
                n = int(cell.loc[cell.T0.gt(0), 'group_id'].nunique())
                bycell.append({'line': keys[0], 'year': int(keys[1]), 'new_business': int(keys[2]), 'rows': len(cell), 'positive_cost_groups': n, 'below30_warning': n < 30})
            desc.append({'evaluation': evaluation, 'outside_source_wildfire_range': outside, 'rows': len(z), 'groups': int(z.group_id.nunique()),
                'positive_cost_groups': int(z.loc[z.T0.gt(0), 'group_id'].nunique()), 'delta': float(gains.sum()/null), 'cells': bycell})
            rv = reserves.loc[z.row_id, 'reserve'].to_numpy(float)
            for scenario in e.NAMES[1:]:
                yy = y-.25*rv if scenario == 'RESERVE075' else y+.25*rv if scenario == 'RESERVE125' else y
                gain = e.unit(yy, z[scenario+'_old'].to_numpy())-e.unit(yy, z[scenario+'_new'].to_numpy())
                stresses.append({'evaluation': evaluation, 'outside_source_wildfire_range': outside, 'scenario': scenario, 'delta': float(gain.sum()/e.unit(yy, np.full(len(yy), yy.mean())).sum())})
    return np.concatenate(blocks, axis=1), desc, stresses, universe


def range_analysis():
    totals, descriptors, stress, universe = range_blocks(); rng = np.random.default_rng(2026102660); draws = []
    first4 = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    for start in range(0, 2000, 32):
        weights = rng.multinomial(len(universe), np.full(len(universe), 1/len(universe)), size=min(32, 2000-start))
        if start == 0: assert np.array_equal(first4, weights[:4])
        draws.append(score_range_sums(weights@totals))
    draws = np.concatenate(draws); np.save(OUT/'range_bootstrap.npy', draws)
    for j, a in enumerate(descriptors):
        a['marginal95'] = np.quantile(draws[:, j], [.025, .975]).tolist(); a['family20_band95'] = np.quantile(draws[:, j], [.025/20, 1-.025/20]).tolist()
    nb = np.load(OUT/'cohort_bootstrap.npy'); global_draws = np.load(OUT/'POOLED_joint_bootstrap.npy')
    gates = {'range_positive_group_support_min100': all(a['positive_cost_groups'] >= 100 for a in descriptors),
        'range_nominal_point_floor': all(a['delta'] >= -.001 for a in descriptors), 'range_nominal_lower95_floor': all(a['marginal95'][0] >= -.001 for a in descriptors),
        'range_family20_lower_floor': all(a['family20_band95'][0] >= -.001 for a in descriptors), 'range_all_stress_points_floor': all(a['delta'] >= -.001 for a in stress),
        'pooled_nominal_stricter_family20_lower_positive': float(np.quantile(global_draws[:, 0], .025/20)) > 0,
        'NB_stricter_family20_lower_floor': bool((np.quantile(nb, .025/20, axis=0) >= -.001).all())}
    report = {'author': 'Codex', 'utc': utc(), 'comparisons': descriptors, 'stress_points': stress, 'gates': gates,
        'draws_sha256': w.sha(OUT/'range_bootstrap.npy'), 'replicates': 2000, 'range_masks_frozen_before_target_fit': True,
        'low_tail_resolution_and_adaptive_not_private_confirmation': True}
    prior.dump(OUT/'range_report.json', report); return report


def run():
    assert not w.read(e.state.PHASE).get('active_jobs')
    prior.dump(OUT/'P37_execution_context.json', {'author': 'Codex', 'utc': utc(), 'script': w.rel(Path(__file__)),
        'script_sha256': w.sha(Path(__file__)), 'source': w.rel(SOURCE), 'raw_driver': w.rel(Path(e.__file__))})
    e.run(); raw = w.read(OUT/'report.json'); cohort = previous.cohort_analysis(); climate = range_analysis()
    context = {'author': 'Codex', 'utc': utc(), 'candidate': 'Annual_weather_source_original_50_50_S2_H1', 'status': 'P37complete_climate_source_algorithm_evaluated',
        'global_gates': raw['diagnostic_gates'], 'new_business_gates': cohort['gates'], 'range_gates': climate['gates'],
        'all_exploratory_gates_pass': all(raw['diagnostic_gates'].values()) and all(cohort['gates'].values()) and all(climate['gates'].values()),
        'new_primary_closed_learners': 30, 'adverse_closed_learners_separate': 30, 'new_source_fits': 0, 'new_C0_fits': 0,
        'new2025inference': 0, 'new_prices': 0, 'new_submissions': 0, 'formal_promotion': False, 'private_improvement_established': False,
        'B00_all_alternatives_preserved': True, '2024_open': True, 'goal_achieved': False}
    prior.dump(OUT/'P37_context_report.json', context); print(json.dumps(context))


def replay():
    e.replay()
    weights = np.load(BASE/'P19_cohortes_broker_20261026/first4_group_weights.npy')
    totals, desc, _, _ = previous.cohort_blocks(); stored = np.load(OUT/'cohort_bootstrap.npy')
    assert np.allclose(previous.score_cohort_sums(weights@totals), stored[:4], rtol=2e-12, atol=2e-13)
    report = w.read(OUT/'cohort_report.json'); assert w.sha(OUT/'cohort_bootstrap.npy') == report['cohort_draws_sha256']
    for j, a in enumerate(report['comparisons']):
        assert a['delta'] == desc[j]['delta'] and np.array_equal(np.quantile(stored[:, j], [.025, .975]), a['marginal95'])
        assert np.array_equal(np.quantile(stored[:, j], [.025/16, 1-.025/16]), a['family16_band95'])
    totals, desc, _, _ = range_blocks(); stored = np.load(OUT/'range_bootstrap.npy')
    assert np.allclose(score_range_sums(weights@totals), stored[:4], rtol=2e-12, atol=2e-13)
    report = w.read(OUT/'range_report.json'); assert w.sha(OUT/'range_bootstrap.npy') == report['draws_sha256']
    for j, a in enumerate(report['comparisons']):
        assert a['delta'] == desc[j]['delta'] and np.array_equal(np.quantile(stored[:, j], [.025, .975]), a['marginal95'])
        assert np.array_equal(np.quantile(stored[:, j], [.025/20, 1-.025/20]), a['family20_band95'])
    prior.dump(OUT/'P37_replay_context.json', {'author': 'Codex', 'utc': utc(), 'raw_engine_replay': w.rel(OUT/'replay_report.json'),
        'new_fits': 0, 'new_model_inference': 0, 'new_resampling': 0, 'cohort_and_range_points_weights_intervals_exact': True,
        'context_report_sha256': w.sha(OUT/'P37_context_report.json')})
    print(json.dumps({'replay': 'exact', 'new_fits': 0, 'new_resampling': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'replay']); args = parser.parse_args()
    with e.threadpool_limits(limits=2): {'prepare': prepare, 'run': run, 'replay': replay}[args.mode]()
