"""Audita cohortes nuevas con OOF guardadas; no aprende ni produce tarifas."""
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
os.environ.setdefault('OMP_NUM_THREADS', '2')
ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
HOME = BASE/'A1S_nucleo_20261026_v1'
CANON = BASE/'preflight_anidado_H1_20261026_v1'
OUT = BASE/'P19_cohortes_broker_20261026'
PLAN = R/'registro/semana2_cohortes_broker_privada_plan.json'
INDEX = R/'registro/semana2_cohortes_broker_privada_actual.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance

spec = importlib.util.spec_from_file_location('p19_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']
ALGORITHMS = {
    'D0': 'P10_validacion_sin_exposicion_20261026',
    'GLM': 'P12_validacion_GLM_20261026',
    'GLM_MI': 'P15_validacion_ausentes_20261026',
    'GAM': 'P17_validacion_GAM_20261026',
    'JOINT': 'P18_calibracion_conjunta_20261026',
}
COHORTS = ['NB', 'NB_BROKER', 'NB_BROKER_ZERO']
META = ['row_id', 'line', 'year', 'new_business', 'fold', 'group_id', 'T0']
READ_COVARIATES = ['channel', 'new_business', 'f1_anios_observados']


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def digest(values):
    return hashlib.sha256(json.dumps(list(values), separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def mask(frame, cohort):
    result = frame.new_business.to_numpy(bool).copy()
    if cohort != 'NB': result &= frame.channel.eq('broker').to_numpy()
    if cohort == 'NB_BROKER_ZERO': result &= frame.f1_anios_observados.eq(0).to_numpy()
    assert cohort in COHORTS
    return result


def read_covariates():
    parts = []
    for line in LINES:
        # Explicit allow-list: no test outcome or future model output is read.
        x = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet', columns=READ_COVARIATES)
        rows = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=[
            'row_id', 'year', 'is_test', 'new_business', 'exposure_calendar'])
        assert len(rows) == len(x) and rows.row_id.is_unique
        assert np.array_equal(rows.new_business.astype(bool), x.new_business.astype(bool))
        assert rows.year.isin([2023, 2024, 2025]).all()
        assert np.array_equal(rows.is_test, rows.year.eq(2025))
        assert x.f1_anios_observados.ge(0).all() and x.channel.notna().all()
        rows['line'] = line
        rows['channel'] = x.channel.astype(str).to_numpy()
        rows['f1_anios_observados'] = x.f1_anios_observados.to_numpy(float)
        parts.append(rows)
    frame = pd.concat(parts, ignore_index=True)
    assert frame.row_id.is_unique
    return frame


def bind(frame, covariates):
    assert frame.row_id.is_unique and covariates.row_id.is_unique
    assert frame.year.isin([2023, 2024]).all()
    c = covariates.set_index('row_id').loc[frame.row_id]
    assert not c.is_test.any()
    for key in ['line', 'year', 'new_business']:
        assert np.array_equal(c[key], frame[key]), key
    result = frame.copy()
    for key in ['channel', 'f1_anios_observados', 'exposure_calendar']:
        result[key] = c[key].to_numpy()
    return result


def input_paths():
    paths = [Path(__file__), R/'herramientas/preparar_nucleo_A1S.py', HOME/'report.json']
    paths += [HOME/f'{kind}_s2_{line}.parquet' for line in LINES for kind in ['rows', 'matrix']]
    paths += [CANON/f'canonical_{line}.parquet' for line in LINES]
    paths += [BASE/d/f'{evaluation}_prices.parquet' for d in ALGORITHMS.values() for evaluation in ['POOLED', 'TRANSFER']]
    return paths


def check_sources(plan):
    expected = dict(plan['sources'])
    code = w.rel(Path(__file__))
    if w.sha(Path(__file__)) != expected[code]:
        correction = w.read(OUT/'implementation_correction.json')
        assert correction['frozen_plan_sha256'] == w.sha(PLAN)
        assert correction['previous_code_sha256'] == expected[code]
        assert correction['new_code_sha256'] == w.sha(Path(__file__))
        assert correction['forum']['id'] == 'COD-S2-20261026-PRIVADA-P19-ENMIENDA-TIPOS'
        expected[code] = correction['new_code_sha256']
    assert expected == {w.rel(path): w.sha(path) for path in input_paths()}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    OUT.mkdir()
    frame = read_covariates()
    summaries = []
    for (line, year), group in frame.groupby(['line', 'year'], sort=True):
        before = group.new_business.to_numpy().copy()
        summaries.append({'line': line, 'year': int(year), 'rows': len(group),
            'exposure_calendar': float(group.exposure_calendar.sum()),
            'broker_rows': int(group.channel.eq('broker').sum()),
            'cohort_rows': {name: int(mask(group, name).sum()) for name in COHORTS}})
        assert np.array_equal(before, group.new_business.to_numpy())
    # Metadata-only canonical binding; the preflight does not inspect target values.
    for line in LINES:
        meta = pd.read_parquet(CANON/f'canonical_{line}.parquet', columns=['row_id', 'line', 'year', 'new_business'])
        bound = bind(meta, frame)
        assert len(bound) == int(((frame.line == line) & ~frame.is_test).sum())
    frame.to_parquet(OUT/'covariates.parquet', index=False)
    preflight = {'author': 'Codex', 'utc': utc(), 'future_covariates_only': True,
        'summaries': summaries, 'training_or_scoring_calls': 0,
        'channel_is_not_unique_acquisition_identifier': True,
        'history_definition': 'Prepared A1S years from first policy start visible in this market, capped at 2024-12-31 and clipped at zero; zero does not prove no previous insurance experience.',
        'definition_source': w.rel(R/'herramientas/preparar_nucleo_A1S.py'),
        'covariates_sha256': w.sha(OUT/'covariates.parquet')}
    dump(OUT/'covariate_preflight.json', preflight)
    plan = {'author': 'Codex', 'utc': utc(), 'status': 'frozen_before_new_cohort_scoring',
        'hypothesis': 'New-business and little-history cases dominate the 2025portfolio; global adaptive scores may conceal failures in comparable historical cohorts. Audit existing complete algorithms before another fit.',
        'cohorts': {'NB': 'new_business is true', 'NB_BROKER': 'NB and channel equals broker',
            'NB_BROKER_ZERO': 'NB_BROKER and prepared f1_anios_observados equals exactly zero'},
        'cohort_interpretation': 'Nested descriptive proxies, not a label identifying the acquired portfolio; no unseen private outcome or private/public membership is known.',
        'algorithms': ALGORITHMS, 'comparator': 'Fixed A1S/S2/H1 old_nominal, same observation chain qSource as every saved candidate',
        'evaluations': ['POOLED2023_2024global_group_OOF', 'TRANSFERtarget2023_to_2024conditional_source2024'],
        'primary': 'Nominal point deltaD2 inside the three fixed cohorts; line/year/fold descriptive breakdown and group support. Do not repeat global score or claim causality.',
        'uncertainty': {'replicates': 2000, 'seed': 2026102660,
            'groups': 'One shared multinomial bootstrap of all NB global customer/address groups; use the same multiplicities for all 30 comparisons across overlapping cohorts/evaluations.',
            'null': 'Recompute cohort-specific weighted mean target and null deviance for each draw.',
            'family': '30 nominal comparisons; marginal percentile95 and a shared max-absolute-standardized-deviation simultaneous95 exploratory band.',
            'training_uncertainty': 'OOF prices fixed; fitted source and training-stage uncertainty not re-estimated.'},
        'descriptive_support_flag': {'minimum_positive_groups_per_line_year_cohort': 30,
            'minimum_positive_groups_in_each_stored_fold': 10,
            'meaning': 'Screen for obvious thin support only; passing does not establish transfer, causality, an adequate tail or private improvement.'},
        'decisions': 'No automatic promotion, line selection, model weights, threshold relaxation or submission from this audit. Retain all adverse cells and nested-cohort dependence.',
        'cost': {'price_fits': 0, 'C0_fits': 0, 'source_queries': 0, 'new_future_prices': 0,
            'submissions': 0, 'new_bootstrap_families': 1},
        'preflight': w.rel(OUT/'covariate_preflight.json'), 'preflight_sha256': w.sha(OUT/'covariate_preflight.json'),
        'sources': {w.rel(path): w.sha(path) for path in input_paths()},
        'covariates_sha256': w.sha(OUT/'covariates.parquet'),
        'limits': ['2023/2024have already been used adaptively; no pristine holdout is restored.',
            'Current source data and common claim marks include2024; annual transfer remains conditional.',
            'Marginal cohort resemblance cannot establish joint covariate/outcome support.',
            'F3c full historical replay is still missing; this audit does not directly compare F3c private performance.',
            'Broker status does not identify only the new acquisition; zero history concerns this dataset only.'],
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    text = ('Codex. Preinscripción P19: revisar tres cohortes fijas (negocio nuevo; nuevo/broker; '
        'nuevo/broker/sin años previos observados en esta base), con OOF guardadas de D0, GLM, '
        'GLMcon ausentes, GAM y calibración conjunta frente al mismo A1S/S2/H1. Cero ajustes, '
        'C0, inferencias fuente o2025, precios finales o envíos. Un solo bootstrap emparejado '
        'por los grupos globales de negocio nuevo,2000réplicas/semilla2026102660;30comparaciones '
        'nominales con banda simultánea exploratoria. Se guardan soporte por ramo/año/fold y '
        'todos los adversos; ninguna selección o ponderación derivará de celdas pequeñas.\n\n'
        'El preflight solo leyó covariables. Broker ronda70%en los tres años y no identifica '
        'de forma exclusiva la adquisición.2025tiene aproximadamente76%de negocio nuevo, '
        'frente a12–15%histórico. La historia cero es la disponible en esta base, no ausencia '
        'de experiencia asegurada. No cambia el objetivo ni los folds.2024abierto adaptativo; '
        'B00/F3c/todas las alternativas conservadas. Plan: '+w.rel(PLAN)+'; SHA '+w.sha(PLAN)+'.\n')
    body = OUT/'forum_previo.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P19-COHORTES-PREVIO',
        '--asunto', 'P19: preinscribir revisión de negocio nuevo y broker con OOF guardadas',
        '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    dump(INDEX, {'author': 'Codex', 'utc': utc(), 'status': 'P19registered_before_cohort_scoring',
        'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(posted.stdout), 'output': w.rel(OUT)})
    print(json.dumps({'prepared': True, 'forum': w.read(INDEX)['forum'], 'new_fits': 0}))


def load_prices(covariates):
    result = {}
    for evaluation in ['POOLED', 'TRANSFER']:
        joint = None
        for name, directory in ALGORITHMS.items():
            f = pd.read_parquet(BASE/directory/f'{evaluation}_prices.parquet', columns=META+['old_nominal', 'new_nominal'])
            assert f.row_id.is_unique and f.year.isin([2023, 2024]).all()
            f = f.sort_values('row_id').reset_index(drop=True)
            if joint is None:
                joint = f[META+['old_nominal']].copy()
            else:
                pd.testing.assert_frame_equal(joint[META+['old_nominal']], f[META+['old_nominal']], check_exact=True)
            joint[name] = f.new_nominal.to_numpy(float)
        joint = bind(joint, covariates)
        assert np.isfinite(joint[['T0', 'old_nominal']+list(ALGORITHMS)].to_numpy(dtype=float)).all()
        assert joint.T0.ge(0).all() and (joint[['old_nominal']+list(ALGORITHMS)] > 0).all().all()
        result[evaluation] = joint
    # Validate actual joins and folds against the authoritative grouped canonical metadata.
    canonical = pd.concat([pd.read_parquet(CANON/f'canonical_{line}.parquet', columns=META) for line in LINES])
    canonical = canonical.sort_values('row_id').reset_index(drop=True)
    pd.testing.assert_frame_equal(canonical, result['POOLED'][META], check_exact=True)
    a = result['POOLED'].set_index('row_id', drop=False).loc[result['TRANSFER'].row_id]
    pd.testing.assert_frame_equal(a[META].reset_index(drop=True), result['TRANSFER'][META], check_exact=True)
    assert result['TRANSFER'].year.eq(2024).all()
    return result


def unit(y, price): return 4*y/np.sqrt(price)+4*np.sqrt(price)-8*np.sqrt(y)


def sufficient(y, old, new):
    y = np.asarray(y, dtype=float)
    old = np.asarray(old, dtype=float)
    new = np.asarray(new, dtype=float)
    return np.column_stack([np.ones(len(y)), y, np.sqrt(y), unit(y, old)[:, None]-unit(y[:, None], new)])


def score(values):
    n, sy, sq = values[..., 0], values[..., 1], values[..., 2]
    null = 8*np.sqrt(sy*n)-8*sq
    assert np.isfinite(null).all() and (null > 1e-9).all()
    return values[..., 3:]/null[..., None]


def support(f, cohort):
    out = []
    for (line, year), z in f.loc[mask(f, cohort)].groupby(['line', 'year'], sort=True):
        totals = z.groupby('group_id', sort=True).T0.sum()
        positive = z.loc[z.T0.gt(0)].groupby('fold').group_id.nunique().reindex(range(5), fill_value=0)
        out.append({'line': line, 'year': int(year), 'cohort': cohort, 'rows': len(z),
            'groups': int(z.group_id.nunique()), 'positive_rows': int(z.T0.gt(0).sum()),
            'positive_groups': int(totals.gt(0).sum()), 'positive_groups_by_fold': {str(k): int(v) for k, v in positive.items()},
            'T0': float(z.T0.sum()), 'largest_cost_group_share': float(totals.max()/totals.sum()),
            'top5_cost_group_share': float(totals.nlargest(5).sum()/totals.sum()),
            'passes_descriptive_support_screen': bool(totals.gt(0).sum() >= 30 and positive.min() >= 10)})
    return out


def calculate():
    assert not (OUT/'report.json').exists() and not (OUT/'started.json').exists()
    plan = w.read(PLAN); check_sources(plan)
    assert w.sha(OUT/'covariates.parquet') == plan['covariates_sha256']
    covariates = pd.read_parquet(OUT/'covariates.parquet')
    frames = load_prices(covariates)
    dump(OUT/'started.json', {'utc': utc(), 'pid': os.getpid(), 'plan_sha256': w.sha(PLAN),
        'new_fits': 0, 'new_predictions': 0, 'new_resampling_families': 1})
    universe = sorted(frames['POOLED'].loc[frames['POOLED'].new_business.astype(bool), 'group_id'].unique())
    blocks, descriptors, points, support_rows, cell_rows = [], [], [], [], []
    for evaluation, frame in frames.items():
        for cohort in COHORTS:
            support_rows.extend([dict(evaluation=evaluation, **a) for a in support(frame, cohort)])
            z = frame.loc[mask(frame, cohort)]
            y = z.T0.to_numpy(float); old = z.old_nominal.to_numpy(float)
            new = z[list(ALGORITHMS)].to_numpy(float)
            values = sufficient(y, old, new)
            aggregated = pd.DataFrame(values).assign(group=z.group_id.to_numpy()).groupby('group', sort=True).sum().reindex(universe, fill_value=0).to_numpy()
            assert np.allclose(aggregated.sum(axis=0), values.sum(axis=0), rtol=2e-13, atol=1e-6)
            current = score(values.sum(axis=0))
            # Independent metric implementation, direct joins and row-order control on the real cohort.
            null = mean_tweedie_deviance(y, np.full(len(y), y.mean()), power=1.5)
            for j, name in enumerate(ALGORITHMS):
                independent = (mean_tweedie_deviance(y, old, power=1.5)-mean_tweedie_deviance(y, new[:, j], power=1.5))/null
                assert math.isclose(current[j], independent, rel_tol=2e-10, abs_tol=2e-13)
                permuted = z.iloc[::-1]
                reversed_value = score(sufficient(permuted.T0.to_numpy(), permuted.old_nominal.to_numpy(), permuted[list(ALGORITHMS)].to_numpy()).sum(axis=0))[j]
                assert math.isclose(current[j], reversed_value, rel_tol=2e-10, abs_tol=2e-13)
                descriptors.append({'evaluation': evaluation, 'cohort': cohort, 'algorithm': name})
            blocks.append(aggregated); points.extend(current.tolist())
            for (line, year), cell in z.groupby(['line', 'year'], sort=True):
                cell_value = score(sufficient(cell.T0.to_numpy(), cell.old_nominal.to_numpy(), cell[list(ALGORITHMS)].to_numpy()).sum(axis=0))
                cell_rows.append({'evaluation': evaluation, 'cohort': cohort, 'line': line, 'year': int(year),
                    'deltaD2': dict(zip(ALGORITHMS, map(float, cell_value)))})
    totals = np.concatenate(blocks, axis=1)
    rng = np.random.default_rng(plan['uncertainty']['seed'])
    draws = []; first_weights = None; mathematical_errors = []
    for start in range(0, 2000, 32):
        count = min(32, 2000-start)
        weights = rng.multinomial(len(universe), np.full(len(universe), 1/len(universe)), size=count)
        if first_weights is None: first_weights = weights[:4].copy()
        weighted = weights@totals
        draw = np.concatenate([score(weighted[:, j*8:(j+1)*8]) for j in range(6)], axis=1)
        draws.append(draw)
        if start == 0:
            for index, (evaluation, cohort) in enumerate((e, c) for e in frames for c in COHORTS):
                z = frames[evaluation].loc[mask(frames[evaluation], cohort)]
                rw = pd.Series(first_weights[0], index=universe).loc[z.group_id].to_numpy()
                y = z.T0.to_numpy(dtype=float); old = z.old_nominal.to_numpy(dtype=float)
                null = mean_tweedie_deviance(y, np.full(len(y), np.average(y, weights=rw)), sample_weight=rw, power=1.5)
                for j, name in enumerate(ALGORITHMS):
                    direct = (mean_tweedie_deviance(y, old, sample_weight=rw, power=1.5)-mean_tweedie_deviance(y, z[name].to_numpy(), sample_weight=rw, power=1.5))/null
                    mathematical_errors.append(abs(direct-draw[0, index*5+j]))
    draws = np.concatenate(draws); point = np.asarray(points)
    assert draws.shape == (2000, 30) and max(mathematical_errors) < 2e-12
    spread = draws.std(axis=0, ddof=1); assert (spread > 0).all()
    critical = float(np.quantile(np.max(np.abs((draws-point)/spread), axis=1), .95))
    results = []
    for j, info in enumerate(descriptors):
        results.append(dict(info, delta=float(point[j]), marginal95=np.quantile(draws[:, j], [.025, .975]).tolist(),
            simultaneous95=[float(point[j]-critical*spread[j]), float(point[j]+critical*spread[j])]))
    np.save(OUT/'paired_group_draws.npy', draws)
    np.save(OUT/'first4_group_weights.npy', first_weights)
    dump(OUT/'group_universe.json', universe)
    dump(OUT/'support.json', support_rows); dump(OUT/'cells.json', cell_rows)
    check_sources(plan)
    report = {'author': 'Codex', 'utc': utc(), 'status': 'P19new_cohort_audit_complete',
        'comparisons': results, 'simultaneous95_critical': critical, 'family_size': 30,
        'bootstrap_replicates': 2000, 'bootstrap_seed': plan['uncertainty']['seed'],
        'global_NB_group_count': len(universe), 'global_NB_group_digest': digest(universe),
        'independent_weighted_metric_max_error': max(mathematical_errors),
        'strict_same_rows_targets_folds_oldprices': True, 'real_row_order_invariance': True,
        'support_screen_failed_cells': sum(not a['passes_descriptive_support_screen'] for a in support_rows),
        'support_records': len(support_rows), 'plan_sha256': w.sha(PLAN),
        'new_model_fits': 0, 'new_C0_fits': 0, 'new_inference': 0, 'new_final_prices': 0,
        'new_submissions': 0, 'private_improvement_established': False, 'goal_achieved': False,
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'limits': plan['limits'],
        'artifacts': {w.rel(OUT/name): w.sha(OUT/name) for name in [
            'paired_group_draws.npy', 'first4_group_weights.npy', 'group_universe.json', 'support.json', 'cells.json']}}
    dump(OUT/'report.json', report)
    print(json.dumps({'status': report['status'], 'failed_support_cells': report['support_screen_failed_cells'],
        'comparisons': results[:5], 'new_fits': 0, 'new_submissions': 0}))


def replay():
    plan = w.read(PLAN); check_sources(plan)
    report = w.read(OUT/'report.json')
    for path, expected in report['artifacts'].items(): assert w.sha(ROOT/path) == expected
    frame = read_covariates()
    pd.testing.assert_frame_equal(frame, pd.read_parquet(OUT/'covariates.parquet'))
    data = load_prices(frame.sample(frac=1, random_state=2026102661))
    weights = np.load(OUT/'first4_group_weights.npy'); universe = w.read(OUT/'group_universe.json')
    actual, point = [], []
    for evaluation, f in data.items():
        for cohort in COHORTS:
            z = f.loc[mask(f, cohort)]
            value = sufficient(z.T0.to_numpy(), z.old_nominal.to_numpy(), z[list(ALGORITHMS)].to_numpy())
            aggregated = pd.DataFrame(value).assign(group=z.group_id.to_numpy()).groupby('group', sort=True).sum().reindex(universe, fill_value=0).to_numpy()
            actual.append(score(weights@aggregated)); point.extend(score(value.sum(axis=0)))
    draws = np.load(OUT/'paired_group_draws.npy'); point = np.asarray(point)
    assert np.allclose(np.concatenate(actual, axis=1), draws[:4], rtol=2e-12, atol=2e-13)
    assert np.array_equal(point, np.array([a['delta'] for a in report['comparisons']]))
    spread = draws.std(axis=0, ddof=1)
    critical = float(np.quantile(np.max(np.abs((draws-point)/spread), axis=1), .95))
    assert critical == report['simultaneous95_critical']
    for j, a in enumerate(report['comparisons']):
        assert np.array_equal(np.quantile(draws[:, j], [.025, .975]), a['marginal95'])
        assert [float(point[j]-critical*spread[j]), float(point[j]+critical*spread[j])] == a['simultaneous95']
    # Actual keyed joins reject duplicate identifiers and future records, rather than silently broadening cohorts.
    for bad in [pd.concat([frame, frame.iloc[:1]]), frame.assign(year=2025)]:
        failed = False
        try: bind(data['POOLED'][META], bad)
        except AssertionError: failed = True
        assert failed
    dump(OUT/'replay_report.json', {'author': 'Codex', 'utc': utc(),
        'status': 'P19points_joins_saved_draws_intervals_replayed',
        'covariate_reproduction_exact': True, 'shuffled_keyed_join_exact': True,
        'duplicate_and_future_join_controls_rejected': True,
        'first4_saved_bootstrap_weight_flows_verified': True,
        'new_fits': 0, 'new_resampling': 0, 'new_inference': 0,
        'report_sha256': w.sha(OUT/'report.json')})
    print(json.dumps({'replay': True, 'new_fits': 0, 'new_resampling': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'replay'])
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf8')
    {'prepare': prepare, 'run': calculate, 'replay': replay}[args.mode]()
