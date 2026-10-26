"""Una comparación exploratoria preinscrita del componente recuperado, sin nuevos árboles."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'
OUT = BASE / 'FSp_edificios_REN_contraste_20261026_v1'
PLAN = R / 'registro/semana2_mision017_FSp_edificios_REN_contraste_plan_v1.json'
CV = BASE / 'tanda2_20261025_v1'
SCOPE = BASE / 'tanda6_pendiente_20261025_v1'
MATRIX = BASE / 'FSp_edificios_matrices_20261026_v1'
PRODUCER = BASE / 'FSp_edificios_productor_20261026_v1'
PREPARED = R / 'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
spec = importlib.util.spec_from_file_location('writer_buildings_contrast', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance

WEIGHT = .25


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def unit(y, m):
    return 4 * y / np.sqrt(m) + 4 * np.sqrt(m) - 8 * np.sqrt(y)


def completion(periods, curve):
    """Integration of the saved step CDF; does not estimate reporting parameters."""
    start = (pd.Timestamp('2024-12-31') - pd.to_datetime(periods.period_start)).dt.days.to_numpy()
    end = (pd.Timestamp('2024-12-31') - pd.to_datetime(periods.period_end)).dt.days.to_numpy()
    assert (start >= end).all() and (end >= 0).all()
    support = np.asarray(curve['delay_days'])
    values = np.asarray(curve['cost_cdf']['1.0'])
    positions = np.searchsorted(support, np.arange(int(start.max()) + 1), side='right') - 1
    daily = np.where(positions >= 0, values[np.maximum(positions, 0)], 0.)
    integral = np.r_[0., np.cumsum(daily)]
    q = (integral[start + 1] - integral[end]) / (start - end + 1)
    assert (q >= -1e-12).all() and (q <= 1 + 1e-12).all()
    return np.clip(q, 0, 1)


def prepare():
    assert not OUT.exists()
    OUT.mkdir(parents=True)
    paths = [Path(__file__), PRODUCER / 'report.json', CV / 'oof_2023_2024.parquet',
             BASE / 'linaje_T2b_v1/raw_rates_buildings.parquet',
             PREPARED / 'claim_assignment_audit.parquet', MATRIX / 'rows_target_prod.parquet',
             R / 'registro/semana2_politica_desarrollo2024_v2.json']
    source = w.read(PRODUCER / 'report.json')
    assert source['new_source_component_model_fits'] == 24
    pieces = []
    for phase, year in [('dev', 2023), ('prod', 2024)]:
        path = PRODUCER / f'components_{phase}.parquet'; paths.append(path)
        assert w.sha(path) == source['outputs'][path.name]['sha256']
        f = pd.read_parquet(path)
        pieces.append(f.loc[f.year.eq(year)].copy())
    components = pd.concat(pieces, ignore_index=True).set_index('row_id')
    assert components.index.is_unique and len(components) == 27447
    perils = sorted(c[2:] for c in components if c.startswith('f_'))
    assert len(perils) == 6
    raw = pd.read_parquet(BASE / 'linaje_T2b_v1/raw_rates_buildings.parquet').set_index('row_id')
    periods = pd.read_parquet(MATRIX / 'rows_target_prod.parquet').set_index('row_id')
    claims = pd.read_parquet(PREPARED / 'claim_assignment_audit.parquet')
    claims = claims.loc[claims.line.eq('buildings') & claims.included_in_T0].copy()
    assert claims.row_id.isin(components.index).all() and claims.claim_id.is_unique
    targets = claims.pivot_table(index='row_id', columns='peril', values='T0_cents', aggfunc='sum').fillna(0)
    scopes = []
    for held in range(5):
        path = SCOPE / f'inputs_buildings_fold{held}.parquet'
        learning = CV / f'learning_buildings_fold{held}.json'
        paths += [path, learning]
        f = pd.read_parquet(path)
        a = w.read(learning)['artifact']['C0']
        train = f.fold.ne(held)
        assert sorted(f.loc[train, 'row_id']) == a['fit_row_ids'] and a['excluded_fold'] == held
        assert not set(f.loc[train, 'group_id']).intersection(f.loc[~train, 'group_id'])
        assert not set(claims.loc[claims.row_id.isin(f.loc[~train, 'row_id']), 'claim_id']).intersection(a['fit_claim_ids'])
        p = periods.loc[f.row_id].reset_index()
        fs = components.loc[f.row_id]
        exposure_scale = f.exposure.to_numpy(float) / fs.exposure.to_numpy(float)
        assert np.array_equal(p.exposure, fs.exposure)
        mixture = np.zeros(len(f))
        for peril in perils:
            q = completion(p, a['curves'][peril])
            f['q_' + peril] = q
            f['risk_' + peril] = fs['f_' + peril].to_numpy() * fs['s_' + peril].to_numpy() * exposure_scale
            f['y_' + peril] = targets[peril].reindex(f.row_id).fillna(0).to_numpy() / 100.
            mixture += a['mixture'][peril] * q
            # Independent finite sum of the step CDF over one complete period.
            for i in [0, len(p) // 2, len(p) - 1]:
                ages = (pd.Timestamp('2024-12-31') - pd.date_range(p.period_start.iloc[i], p.period_end.iloc[i])).days.to_numpy()
                curve = a['curves'][peril]
                k = np.searchsorted(curve['delay_days'], ages, side='right') - 1
                v = np.where(k >= 0, np.asarray(curve['cost_cdf']['1.0'])[np.maximum(k, 0)], 0.)
                assert abs(v.mean() - q[i]) < 2e-12
        assert np.allclose(f[[f'y_{p}' for p in perils]].sum(axis=1), f.T0, rtol=0, atol=1e-9)
        assert np.allclose(mixture * f.exposure.to_numpy(), f.e_cost_scope, rtol=0, atol=2e-12)
        f['unshaped_T2b'] = raw.loc[f.row_id, 'annual_raw_T2b'].to_numpy() * f.e_cost_scope.to_numpy()
        assert f.unshaped_T2b.gt(0).all()
        outpath = OUT / f'inputs_fold{held}.parquet'
        f.to_parquet(outpath, index=False)
        scopes.append({'held_fold': held, 'rows': len(f), 'training_rows': int(train.sum()),
                       'path': w.rel(outpath), 'sha256': w.sha(outpath), 'C0': w.rel(learning), 'C0_sha256': w.sha(learning)})
    result = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'perils': perils, 'scopes': scopes,
              'no_fit_or_score': True, 'no_C0_reestimated': True, 'no_2025_rows_in_contrast_inputs': True,
              'all_period_exposure_and_peril_C0_checks_passed': True,
              'sources': {w.rel(p): w.sha(p) for p in paths}}
    dump(OUT / 'preflight.json', result)
    print(json.dumps({'preflight': 'passed', 'scopes': 5, 'new_fits': 0, 'new_scores': 0}))


def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists()
    pre = w.read(OUT / 'preflight.json')
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
            'hypothesis': 'The recovered buildings cost-proxy shape may improve renewal ranking on saved global held groups. Test exactly one .25 insertion without diluting prior-claims multipliers or changing new business/levels.',
            'reference': 'Frozen N3 research comparator, not full F3c/C1/F2 and not exact K replay',
            'version_semantics': 'F4b-style preservation of N3 shape: N3*(FSp_observed/unshaped_T2b_observed)^.25, only REN; per-year held prediction-only level preservation.',
            'peril_calibration': 'Training-only kappa_p=sum(y_p)/sum(risk_p*q_p), 6perils x5saved folds; no held labels.',
            'exposure': 'Producer f includes original calendar exposure; divide that exposure and apply canonical scope exposure once.',
            'source': {'2023_target': 'dev source2021–2023', '2024_target': 'prod source2021–2024',
                       'availability': 'common December2024 snapshot; conditional retrospective development, not clean prospective backtest'},
            'configuration': {'weight': WEIGHT, 'new_business_weight': 0, 'folds': 'saved global customer/address groups',
                              'years': [2023, 2024], 'new_C0_fits': 0, 'no_test_inference_or_price_CSV': True,
                              'normalization': 'separately by year on held REN, preserve N3 totals without held outcomes'},
            'criterion': w.read(R / 'registro/semana2_mision017_fase2_tanda10_plan_v1.json')['criterion'],
            'formal_admission_not_possible_from_this_proxy_alone': True,
            'bootstrap': {'replicates': 2000, 'seed': 2026102612, 'unit': 'saved connected component',
                          'conditional_on_fixed_source_models': True},
            'budget': {'iterative_price_fits': 0, 'peril_calibration_constants': 30,
                       'learning_calls': 5, 'held_prediction_only_normalizers': 10,
                       'new_C0_fits': 0, 'new_test_prices': 0, 'new_submissions': 0},
            'control': 'Full real learn/apply entry point excludes held labels before every calculation; poison held total/peril labels. Replay saved calibration without estimation. Independent loss and arithmetic.',
            'preflight': {'path': w.rel(OUT / 'preflight.json'), 'sha256': w.sha(OUT / 'preflight.json')},
            'sources': {**pre['sources'], **{s['path']: s['sha256'] for s in pre['scopes']}},
            'B00_all_alternatives_preserved': True, '2024_open': True}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. Antes de estimar o puntuar, registro un único contraste del FSp recuperado de edificios, '
        'peso fijo0,25solo en renovación, nuevo negocio intacto y niveles por año conservados mediante predicciones. '
        'Se conservan los multiplicadores de N3 dividiendo por su T2b sin forma antes de insertar FSp. '
        'Se estiman30constantes de peligro solo con los grupos de entrenamiento; C0 y cinco folds globales quedan fijos. '
        'Se corrige expresamente la exposición: f del productor ya incluye el periodo original. '
        'Las entradas por peligro y su integración de C0 pasaron el preflight. '
        'El comparador es N3 reproducible, no el F3c/F2 completo ni el K original. Se mantienen los criterios anteriores, incluido+0,002global, '
        'cuatro folds positivos y ambos años no negativos; esta investigación parcial no permite promoción formal o envío. '
        'Cero árboles, C0, precios de2025o envíos adicionales. Fuente y criterios: ' + w.rel(PLAN) + '.', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-EDIFICIOS-REN-CONTRASTE-PREVIO',
        '--asunto', 'Contraste único de edificios en renovación, grupos y nivel fijos', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(response.stdout)})
    print(json.dumps({'registered': True, 'budget_calibration_constants': 30, 'forum': json.loads(response.stdout)}))


def apply(f, perils, artifact):
    risk = np.zeros(len(f))
    for p in perils:
        risk += artifact['kappa'][p] * f['risk_' + p].to_numpy(float) * f['q_' + p].to_numpy(float)
    assert (risk > 0).all() and np.isfinite(risk).all()
    base = f.base_N3.to_numpy(float)
    result = base.copy(); normalizers = {}
    for year in [2023, 2024]:
        mask = f.year.eq(year).to_numpy() & f.new_business.eq(0).to_numpy()
        assert mask.any()
        factor = (risk[mask] / f.unshaped_T2b.to_numpy()[mask]) ** WEIGHT
        norm = float(np.sum(base[mask] * factor) / np.sum(base[mask]))
        result[mask] = base[mask] * factor / norm
        assert abs(result[mask].sum() / base[mask].sum() - 1) < 1e-12
        normalizers[str(year)] = norm
    assert np.array_equal(result[f.new_business.eq(1)], base[f.new_business.eq(1)])
    return result, normalizers


def learn(f, held, perils):
    train = f.loc[f.fold.ne(held)].copy()
    valid = f.loc[f.fold.eq(held)].copy()
    assert not set(train.group_id).intersection(valid.group_id)
    kappa = {}
    for p in perils:
        y = train['y_' + p].to_numpy(float)
        assert (y >= 0).all() and np.isfinite(y).all()
        risk = train['risk_' + p].to_numpy(float) * train['q_' + p].to_numpy(float)
        kappa[p] = float(y.sum() / risk.sum())
        assert kappa[p] > 0 and np.isfinite(kappa[p])
        assert abs((kappa[p] * risk).sum() / y.sum() - 1) < 1e-12
    artifact = {'held': held, 'kappa': kappa, 'training_rows': len(train),
                'training_row_ids': sorted(train.row_id), 'training_groups': sorted(set(train.group_id))}
    pred, normalizers = apply(valid, perils, artifact)
    return pred, {**artifact, 'held_normalizers': normalizers}


def run():
    assert not (OUT / 'report.json').exists() and not (OUT / 'started.json').exists()
    registration = w.read(OUT / 'registration.json'); assert w.sha(PLAN) == registration['plan_sha256']
    plan = w.read(PLAN); pre = w.read(OUT / 'preflight.json')
    assert all(w.sha(ROOT / path) == sha for path, sha in plan['sources'].items())
    dump(OUT / 'started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'plan_sha256': w.sha(PLAN)})
    perils = pre['perils']
    oof = pd.read_parquet(CV / 'oof_2023_2024.parquet'); oof['ER1'] = oof.N3
    replays = []; scopes = []
    for scope in pre['scopes']:
        held = scope['held_fold']; f = pd.read_parquet(ROOT / scope['path'])
        pred, artifact = learn(f, held, perils)
        dump(OUT / f'learning_fold{held}.json', artifact)
        valid = f.loc[f.fold.eq(held)]
        ix = pd.Series(oof.index.to_numpy(), index=oof.row_id).loc[valid.row_id].to_numpy()
        assert np.array_equal(oof.loc[ix, 'N3'], valid.base_N3)
        oof.loc[ix, 'ER1'] = pred
        # Actual full estimator, held costs invalidated before its train exclusion.
        poison = f.copy(); held_mask = poison.fold.eq(held)
        poison.loc[held_mask, ['T0', *['y_' + p for p in perils]]] = -1e30
        other, same = learn(poison, held, perils)
        assert artifact == same and np.array_equal(pred, other)
        # Replay only application; this branch calls no estimator.
        replay, norms = apply(valid, perils, w.read(OUT / f'learning_fold{held}.json'))
        assert np.array_equal(replay, pred) and norms == artifact['held_normalizers']
        # Direct log-space formula checks the multiplicative arithmetic separately.
        matrix = np.column_stack([valid['risk_' + p].to_numpy() * valid['q_' + p].to_numpy() for p in perils])
        raw = matrix @ np.array([artifact['kappa'][p] for p in perils])
        for year in [2023, 2024]:
            mask = valid.year.eq(year).to_numpy() & valid.new_business.eq(0).to_numpy()
            independent = np.exp(np.log(valid.base_N3.to_numpy()[mask]) + WEIGHT *
                (np.log(raw[mask]) - np.log(valid.unshaped_T2b.to_numpy()[mask])))
            independent *= valid.base_N3.to_numpy()[mask].sum() / independent.sum()
            assert np.allclose(independent, pred[mask], rtol=1e-12, atol=1e-10)
        scopes.append({'fold': held, 'kappa': artifact['kappa'], 'held_normalizers': norms,
                       'held_rows': len(valid), 'held_group_exclusion_exact': True})
        replays.append({'fold': held, 'full_learning_held_label_poison_invariant': True,
                        'saved_artifact_apply_replay_exact': True, 'independent_log_space_math_passed': True})
    y = oof.T0.to_numpy(float); base = oof.N3.to_numpy(float); pred = oof.ER1.to_numpy(float)
    den = unit(y, np.full(len(y), y.mean())).sum()
    u0 = unit(y, base); u1 = unit(y, pred); gain = u0 - u1
    assert abs(u0.mean() - mean_tweedie_deviance(y, base, power=1.5)) < 1e-10
    assert abs(u1.mean() - mean_tweedie_deviance(y, pred, power=1.5)) < 1e-10
    scores = {'N3': float(1 - u0.sum() / den), 'ER1': float(1 - u1.sum() / den)}
    group = pd.DataFrame({'group': oof.group_id, 'gain': gain,
                          'den': unit(y, np.full(len(y), y.mean()))}).groupby('group')[['gain', 'den']].sum()
    rng = np.random.default_rng(plan['bootstrap']['seed']); vals = []
    g = group.gain.to_numpy(); d = group.den.to_numpy()
    for i in range(2000):
        ix = rng.integers(0, len(group), len(group)); vals.append(float(g[ix].sum() / d[ix].sum()))
    ci = np.quantile(vals, [.025, .975]).tolist()
    folds = {str(k): float(gain[oof.fold.eq(k)].sum() / den) for k in range(5)}
    years = {str(k): float(gain[oof.year.eq(k)].sum() / den) for k in [2023, 2024]}
    cells = []
    for (line, year, nb), ix in oof.groupby(['line', 'year', 'new_business']).groups.items():
        mask = np.asarray(list(ix)); yy = y[mask]
        null = unit(yy, np.full(len(yy), yy.mean())).sum()
        cells.append({'line': line, 'year': int(year), 'new_business': int(nb), 'rows': len(mask),
                      'delta_contribution_global_den': float(gain[mask].sum() / den),
                      'delta_within_cell_null': float(gain[mask].sum() / null),
                      'AE_base': float(yy.sum() / base[mask].sum()), 'AE_ER1': float(yy.sum() / pred[mask].sum())})
    influence = group.sort_values('gain', ascending=False)
    post31 = float((group.gain.sum() - influence.gain.iloc[:31].sum()) / den)
    building = oof.line.eq('buildings').to_numpy()
    ratios = pred[building & oof.new_business.eq(0).to_numpy()] / base[building & oof.new_business.eq(0).to_numpy()]
    positive = oof.T0.gt(0)
    tail_groups = set(oof.loc[positive].groupby('group_id').T0.sum().nlargest(31).index)
    no_tail = ~oof.group_id.isin(tail_groups)
    delta = float(gain.sum() / den)
    checks = {'delta_min': delta >= plan['criterion']['delta_min'], 'lower95_positive': ci[0] > 0,
              'at_least4positive_folds': sum(v > 0 for v in folds.values()) >= 4,
              'both_years_nonnegative': all(v >= 0 for v in years.values()),
              'post31_nonnegative': post31 >= 0,
              'min_cell_delta': all(c['delta_within_cell_null'] >= -.001 for c in cells),
              'complete_F3c_comparator_and_vetoes_available': False}
    oof.to_parquet(OUT / 'oof_2023_2024.parquet', index=False)
    group.to_parquet(OUT / 'group_influence.parquet')
    influence.head(50).to_csv(OUT / 'top50_influence.csv')
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
              'status': 'exploratory_contrast_complete_no_promotion', 'reference': plan['reference'],
              'scores': scores, 'delta': delta, 'bootstrap95': ci, 'fold_global_contributions': folds,
              'year_global_contributions': years, 'cells': cells, 'post31_favorable_groups_global_delta': post31,
              'remove31highest_actual_cost_groups_global_delta': float(gain[no_tail].sum() / den),
              'renewal_building_price_ratio_quantiles': np.quantile(ratios, [0, .01, .5, .99, 1]).tolist(),
              'all_new_business_unchanged': bool(np.array_equal(pred[oof.new_business.eq(1)], base[oof.new_business.eq(1)])),
              'other_lines_unchanged': bool(np.array_equal(pred[~building], base[~building])),
              'checks': checks, 'all_checks_passed': all(checks.values()), 'scopes': scopes, 'replays': replays,
              'independent_sklearn_loss_passed': True, 'plan_sha256': w.sha(PLAN),
              'new_real_peril_calibration_constants': 30, 'new_iterative_price_fits': 0,
              'new_C0_fits': 0, 'held_prediction_only_normalizers': 10,
              'controls_recompute_same_30closed_form_constants_separately': 30,
              'new_test_prices': 0, 'new_submissions': 0, 'B00_preserved': True,
              '2024_open': True, 'goal_achieved': False,
              'limits': ['N3 proxy, no complete F3c/C1/F2 replay', 'Source-model uncertainty not refitted by group bootstrap',
                         'Adaptive development using2024, no pristine temporal validation', 'Cost-completion frequency proxy, tail/reserve adequacy unresolved',
                         'No automatic transfer of received K forecasts or source-model QA to predictive admission']}
    dump(OUT / 'report.json', report)
    assert all(w.sha(ROOT / path) == sha for path, sha in plan['sources'].items())
    print(json.dumps({'scores': scores, 'delta': delta, 'bootstrap95': ci, 'folds': folds, 'years': years,
                      'post31': post31, 'checks': checks, 'new_fits': 0, 'new_C0_fits': 0, 'new_submissions': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'register', 'run'])
    args = parser.parse_args(); {'prepare': prepare, 'register': register, 'run': run}[args.mode]()
