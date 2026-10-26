"""FSp aislado con calibración contraída, sobre factores G3 ya guardados."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'FSp_REN_G3_contraste_20261026_v1'
PLAN = R / 'registro/semana2_mision017_FSp_REN_G3_plan_v1.json'
MC = BASE / 'FSp_MC_recuperacion_20261026_v1'
BP = BASE / 'FSp_edificios_productor_20261026_v1'
CV = BASE / 'tanda2_20261025_v1'; SC = BASE / 'tanda6_pendiente_20261025_v1'
G3 = BASE / 'tanda10_factores_20261026_v1'
PREP = R / 'privado/semana2/preparacion/base_20261023T164102Z_b3e6c2a3'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.metrics import mean_tweedie_deviance


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


w = load('writer_FSp_G3', R / 'herramientas/registrar_avance_mision017_fase2.py')
old = load('pure_completion_FSp', R / 'herramientas/contrastar_FSp_edificios_REN.py')
WEIGHTS = {'motor': .25, 'buildings': .25, 'contents': .5}
KP = 100.
unit = old.unit


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def apply_G3(frame, stages):
    """Replay the frozen outer-scope factors; never inspect outcome fields."""
    value = frame.base_N3.to_numpy(float).copy()
    for stage in stages:
        labels = frame[stage['variable']].astype('string').fillna('__MISSING__').astype(str)
        factor = labels.map(stage['factors']).fillna(1.).to_numpy(float)
        result = value.copy()
        for year in [2023, 2024]:
            for nb in [0, 1]:
                mask = frame.year.eq(year).to_numpy() & frame.new_business.eq(nb).to_numpy()
                assert mask.any()
                norm = np.sum(value[mask] * factor[mask]) / np.sum(value[mask])
                result[mask] = value[mask] * factor[mask] / norm
        value = result
    return value


def prepare():
    assert not OUT.exists(); OUT.mkdir()
    paths = [Path(__file__), Path(old.__file__), G3 / 'oof_2023_2024.parquet', G3 / 'validation_v1/report.json',
             MC / 'productor/report.json', BP / 'report.json', MC / 'calibracion_recibida_contrato.json',
             PREP / 'claim_assignment_audit.parquet']
    reference = pd.read_parquet(G3 / 'oof_2023_2024.parquet').set_index('row_id')
    claims = pd.read_parquet(PREP / 'claim_assignment_audit.parquet')
    claims = claims.loc[claims.included_in_T0].copy()
    assert claims.claim_id.is_unique
    scopes = []; perils_by_line = {}; stage_apply_rows = 0
    for line in WEIGHTS:
        producer = BP if line == 'buildings' else MC / 'productor'
        pro = w.read(producer / 'report.json'); parts = []
        for phase, year in [('dev', 2023), ('prod', 2024)]:
            name = f'components_{phase}.parquet' if line == 'buildings' else f'components_{line}_{phase}.parquet'
            path = producer / name; paths.append(path); assert w.sha(path) == pro['outputs'][name]['sha256']
            part = pd.read_parquet(path); parts.append(part.loc[part.year.eq(year)])
        comp = pd.concat(parts, ignore_index=True).set_index('row_id'); assert comp.index.is_unique
        perils = sorted(c[2:] for c in comp if c.startswith('f_')); perils_by_line[line] = perils
        raw_path = BASE / f'linaje_T2b_v1/raw_rates_{line}.parquet'; paths.append(raw_path)
        raw = pd.read_parquet(raw_path).set_index('row_id')
        rowpath = BASE / 'FSp_edificios_matrices_20261026_v1/rows_target_prod.parquet' if line == 'buildings' else MC / f'matrices/rows_{line}_target_prod.parquet'
        paths.append(rowpath); periods = pd.read_parquet(rowpath).set_index('row_id')
        cl = claims.loc[claims.line.eq(line)]; assert cl.row_id.isin(comp.index).all()
        y = cl.pivot_table(index='row_id', columns='peril', values='T0_cents', aggfunc='sum').fillna(0)
        n = cl.groupby(['row_id', 'peril']).size().unstack(fill_value=0)
        if line != 'buildings':
            path = G3 / f'covariates_{line}.parquet'; paths.append(path); cov = pd.read_parquet(path).set_index('row_id')
        for held in range(5):
            path = SC / f'inputs_{line}_fold{held}.parquet'; parent = CV / f'learning_{line}_fold{held}.json'
            paths += [path, parent]; f = pd.read_parquet(path); tr = f.fold.ne(held)
            c0 = w.read(parent)['artifact']['C0']
            assert c0['excluded_fold'] == held and sorted(f.loc[tr, 'row_id']) == c0['fit_row_ids']
            assert not set(f.loc[tr, 'group_id']).intersection(f.loc[~tr, 'group_id'])
            assert not set(cl.loc[cl.row_id.isin(f.loc[~tr, 'row_id']), 'claim_id']).intersection(c0['fit_claim_ids'])
            if line == 'buildings':
                f['baseline_G3'] = f.base_N3
                savedpath = BASE / f'FSp_edificios_REN_contraste_20261026_v1/inputs_fold{held}.parquet'
                paths.append(savedpath); savedq = pd.read_parquet(savedpath).set_index('row_id')
            else:
                for col in cov: f[col] = cov.loc[f.row_id, col].to_numpy()
                learned = G3 / f'learning_{line}_fold{held}.json'; paths.append(learned)
                stages = w.read(learned)['stages']; f['baseline_G3'] = np.nan
                # Normalization was separate on train and held in the actual G3 flow.
                f.loc[tr, 'baseline_G3'] = apply_G3(f.loc[tr], stages)
                f.loc[~tr, 'baseline_G3'] = apply_G3(f.loc[~tr], stages)
                stage_apply_rows += len(f)
            assert np.array_equal(f.loc[~tr, 'baseline_G3'], reference.loc[f.loc[~tr, 'row_id'], 'G3'])
            p = periods.loc[f.row_id].reset_index(); fs = comp.loc[f.row_id]
            assert np.array_equal(p.exposure, fs.exposure)
            scale = f.exposure.to_numpy() / fs.exposure.to_numpy()
            mix = np.zeros(len(f)); support = {}
            for peril in perils:
                if line == 'buildings':
                    q = savedq.loc[f.row_id, 'q_' + peril].to_numpy()
                else:
                    q = old.completion(p, c0['curves'][peril])
                    # Independent period summation for this new line only.
                    for i in [0, len(p) // 2, len(p) - 1]:
                        ages = (pd.Timestamp('2024-12-31') - pd.date_range(p.period_start.iloc[i], p.period_end.iloc[i])).days.to_numpy()
                        curve = c0['curves'][peril]; k = np.searchsorted(curve['delay_days'], ages, side='right') - 1
                        values = np.where(k >= 0, np.asarray(curve['cost_cdf']['1.0'])[np.maximum(k, 0)], 0.)
                        assert abs(values.mean() - q[i]) < 2e-12
                f['q_' + peril] = q
                f['f_' + peril] = fs['f_' + peril].to_numpy() * scale
                f['s_' + peril] = fs['s_' + peril].to_numpy()
                f['y_' + peril] = y[peril].reindex(f.row_id).fillna(0).to_numpy() / 100.
                f['n_' + peril] = n[peril].reindex(f.row_id).fillna(0).to_numpy(dtype=int)
                assert f.loc[tr, 'n_' + peril].sum() > 0 and f.loc[tr, 'y_' + peril].sum() > 0
                support[peril] = int(f.loc[tr, 'n_' + peril].sum())
                mix += c0['mixture'][peril] * q
            assert np.allclose(f[[f'y_{p}' for p in perils]].sum(axis=1), f.T0, rtol=0, atol=1e-9)
            assert np.allclose(mix * f.exposure.to_numpy(), f.e_cost_scope, rtol=0, atol=2e-12)
            f['unshaped_T2b'] = raw.loc[f.row_id, 'annual_raw_T2b'].to_numpy() * f.e_cost_scope.to_numpy()
            assert f.unshaped_T2b.gt(0).all() and f.baseline_G3.gt(0).all()
            outpath = OUT / f'inputs_{line}_fold{held}.parquet'; f.to_parquet(outpath, index=False)
            scopes.append({'line': line, 'held': held, 'input': w.rel(outpath), 'sha256': w.sha(outpath),
                           'training_rows': int(tr.sum()), 'held_rows': int((~tr).sum()), 'training_observed_counts': support})
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'scopes': scopes,
              'perils': perils_by_line, 'saved_G3_held_prices_bit_exact': True,
              'replayed_saved_G3_application_rows_not_new_estimates': stage_apply_rows,
              'source_exposure_once_and_C0_mixture_parity': True,
              'buildings_q_reused_without_repeating_unchanged_integration_tests': True,
              'new_parameter_estimates': 0, 'new_C0_fits': 0, 'new_scores': 0, 'new_test_prices': 0,
              'sources': {w.rel(p): w.sha(p) for p in paths}}
    dump(OUT / 'preflight.json', report)
    print(json.dumps({'preflight': 'passed', 'scopes': len(scopes), 'saved_G3_replay_exact': True, 'new_estimates': 0, 'new_scores': 0}))


def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists()
    pre = w.read(OUT / 'preflight.json')
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
            'hypothesis': 'A single all-renewal insertion of recovered source FSp shape may add information beyond the frozen G3 factors, with the received count/mark credibility rule instead of the previous unshrunk cost calibration.',
            'reference': 'G3 outer-group factor surrogate, not complete F3c/C1/F2',
            'need_for_distinct_trial': 'New numeric MC outputs; source code shows kf/ks/kg with n/(n+100), materially different from the earlier buildings cost matching. Reuse all60source models, not train again or adjust K/weights from losses.',
            'configuration': {'weights_REN': WEIGHTS, 'NB_weights': 0, 'KP': KP,
                              'years': [2023, 2024], 'folds': 'saved global customer/address components',
                              'G3_factors': 'saved outer-scope stages; no refitting before or after FSp',
                              'shape': 'baseline_G3*(sum(kappa_p*f_p*s_p*q_p)/unshaped_T2b)^w, normalized by year/REN without held labels',
                              'exposure': 'Divide producer calendar exposure and apply canonical scope exposure once',
                              'peril_kappa': {'kg': 'sum(T0)/sum_p,sum_i(f_i*s_i*q_i)', 'kf_p': 'sum(n_i)/sum(f_i*q_i)',
                                              'ks_p': 'sum(y_i)/sum(n_i*s_i)', 'z_p': 'sum(n_i)/(sum(n_i)+100)',
                                              'kappa_p': 'exp(z_p*log(max(kf_p*ks_p/kg,1e-3)))'},
                              'C0': 'cached target outer-training cost CDF, not received source cp; no C0 estimation',
                              'calibration_scope': 'Training rows only, pooled2023/24; held costs/counts/reserves excluded before calculations'},
            'not_exact_F4b_F4c_or_K_replay': True,
            'source_phase': {'target2023': 'dev source2021–23', 'target2024': 'prod source2021–24',
                             'limits': 'common end2024snapshot; conditional retrospective development, not prospective temporal validation'},
            'criterion': w.read(R / 'registro/semana2_mision017_fase2_tanda10_plan_v1.json')['criterion'],
            'criterion_cell_denominator': 'within-cell null, as explicitly used in prior buildings screen',
            'formal_promotion_requires_complete_comparator_and_vetoes': True,
            'bootstrap': {'replicates': 2000, 'seed': 2026102613, 'unit': 'saved connected component',
                          'null_refitted_by_closed_form_per_resample': True, 'conditional_on_fixed_source': True},
            'budget': {'new_iterative_price_fits': 0, 'new_C0_fits': 0, 'new_test_prices': 0, 'new_submissions': 0,
                       'learning_scopes': 15, 'empirical_global_cost_levels': 15, 'frequency_moment_constants': 75,
                       'mark_moment_constants': 75, 'derived_shrunk_peril_factors_not_independent_fits': 75,
                       'held_prediction_only_normalizers': 30, 'control_recomputations_separate': 'same165momentconstants for full-flow held-payload invariance'},
            'limits': ['Cost-completion Poisson proxy; n calibration does not identify ultimate event frequency',
                       'Ultimate tail and reserve adequacy not identified', 'Undated masters',
                       'No new choice of K/weights and no borrowing forecasts from received compound CSVs'],
            'sources': {**pre['sources'], **{s['input']: s['sha256'] for s in pre['scopes']},
                        w.rel(OUT / 'preflight.json'): w.sha(OUT / 'preflight.json')},
            'B00_all_alternatives_preserved': True, '2024_open': True}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. Antes de estimar o puntuar registro un único contraste de FSp aislado sobre G3. '
        'Se conservan los factores G3 guardados: no se reestiman y sus precios retenidos se reprodujeron exactamente en 15 ámbitos. '
        'Solo renovación, pesos fijos recibidos motor/edificios 0,25 y contenidos 0,5; nuevo negocio y niveles por año intactos. '
        'La receta recibida usa kf/ks/kg y n/(n+100), distinta de la igualación de coste no contraída del contraste anterior de edificios. '
        'Este cambio de calibración queda explícito; K y pesos no se eligen por aquel resultado ni por el público. '
        'Se adapta a los C0 protegidos por grupos, en lugar del cp fuente original, por lo que tampoco es un replay exacto de F4c/K. '
        'Se reutilizan los 60 modelos fuente ya completos y no se repiten los tests de integración de edificios sin cambios. '
        'Coste: 15 niveles de coste, 75 constantes de frecuencia y 75 de marca, 75 factores derivados, 30 normalizadores de predicciones; '
        'cero árboles/C0/precios de2025/envíos. Se conservan los criterios, incluido +0,002 global, intervalo positivo y cuatro folds. '
        'El comparador es G3, no F3c completo; un pase parcial no autoriza promoción o envío. Plan: ' + w.rel(PLAN) + '.', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-FSP-REN-G3-CONTRASTE-PREVIO',
        '--asunto', 'FSp aislado: un contraste de renovaciones con credibilidad recibida y G3 fijo', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(response.stdout)})
    print(json.dumps({'registered': True, 'scopes': 15, 'new_iterative_fits': 0, 'forum': json.loads(response.stdout)}))


def apply(f, perils, artifact, line, weight=None):
    risk = sum(artifact['perils'][p]['kappa'] * f['f_' + p].to_numpy() * f['s_' + p].to_numpy() * f['q_' + p].to_numpy() for p in perils)
    assert np.isfinite(risk).all() and (risk > 0).all()
    base = f.baseline_G3.to_numpy(float); result = base.copy(); norms = {}
    weight = WEIGHTS[line] if weight is None else weight
    for year in [2023, 2024]:
        mask = f.year.eq(year).to_numpy() & f.new_business.eq(0).to_numpy(); assert mask.any()
        factor = (risk[mask] / f.unshaped_T2b.to_numpy()[mask]) ** weight
        norm = float(np.sum(base[mask] * factor) / np.sum(base[mask]))
        result[mask] = base[mask] * factor / norm; norms[str(year)] = norm
        assert abs(result[mask].sum() / base[mask].sum() - 1) < 1e-12
    assert np.array_equal(result[f.new_business.eq(1)], base[f.new_business.eq(1)])
    return result, norms


def learn(f, held, perils, line):
    tr = f.loc[f.fold.ne(held)].copy(); valid = f.loc[f.fold.eq(held)].copy()
    assert not set(tr.group_id).intersection(valid.group_id)
    assert tr.T0.ge(0).all()
    observed = sum(tr['f_' + p].to_numpy() * tr['s_' + p].to_numpy() * tr['q_' + p].to_numpy() for p in perils)
    kg = float(tr.T0.sum() / observed.sum()); assert kg > 0
    fields = {}
    for p in perils:
        n = tr['n_' + p].to_numpy(float); y = tr['y_' + p].to_numpy(float)
        ef = tr['f_' + p].to_numpy(float) * tr['q_' + p].to_numpy(float); s = tr['s_' + p].to_numpy(float)
        assert (n >= 0).all() and (y >= 0).all() and n.sum() > 0 and y.sum() > 0
        kf = float(n.sum() / ef.sum()); ks = float(y.sum() / (n * s).sum()); z = float(n.sum() / (n.sum() + KP))
        relative = kf * ks / kg; kappa = float(np.exp(z * np.log(max(relative, 1e-3))))
        assert abs(kf * ef.sum() / n.sum() - 1) < 1e-12 and abs(ks * (n * s).sum() / y.sum() - 1) < 1e-12
        # Independent summation, distinct arithmetic and log-space calculation.
        fk = math.fsum(n.tolist()) / math.fsum(ef.tolist())
        sk = math.fsum(y.tolist()) / math.fsum((n * s).tolist())
        gk = math.fsum(tr.T0.tolist()) / math.fsum(observed.tolist())
        independent = math.exp(z * math.log(max(fk * sk / gk, 1e-3)))
        assert abs(independent / kappa - 1) < 1e-12
        fields[p] = {'observed_N': int(n.sum()), 'cost': float(y.sum()), 'kf': kf, 'ks': ks, 'z': z,
                     'relative_unshrunk': relative, 'floor_active': relative < 1e-3, 'kappa': kappa}
    artifact = {'line': line, 'held': held, 'kg': kg, 'perils': fields, 'training_row_ids': sorted(tr.row_id),
                'training_groups': sorted(set(tr.group_id)), 'new_C0_fits': 0}
    pred, norm = apply(valid, perils, artifact, line)
    return pred, {**artifact, 'held_normalizers': norm}


def run():
    assert not (OUT / 'started.json').exists()
    registration = w.read(OUT / 'registration.json'); assert w.sha(PLAN) == registration['plan_sha256']
    plan = w.read(PLAN); assert all(w.sha(ROOT / path) == sha for path, sha in plan['sources'].items())
    dump(OUT / 'started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'plan_sha256': w.sha(PLAN)})
    pre = w.read(OUT / 'preflight.json'); oof = pd.read_parquet(G3 / 'oof_2023_2024.parquet'); oof['RFS1'] = oof.G3
    checks = []; artifacts = []
    for scope in pre['scopes']:
        line = scope['line']; held = scope['held']; perils = pre['perils'][line]
        f = pd.read_parquet(ROOT / scope['input']); pred, a = learn(f, held, perils, line)
        path = OUT / f'learning_{line}_fold{held}.json'; dump(path, a); artifacts.append(a)
        valid = f.loc[f.fold.eq(held)]; ix = pd.Series(oof.index.to_numpy(), index=oof.row_id).loc[valid.row_id].to_numpy()
        assert np.array_equal(oof.loc[ix, 'G3'], valid.baseline_G3)
        oof.loc[ix, 'RFS1'] = pred
        bad = f.copy(); bad.loc[bad.fold.eq(held), ['T0', 'reserve', *['y_' + p for p in perils], *['n_' + p for p in perils]]] = -1e30
        other, same = learn(bad, held, perils, line); assert a == same and np.array_equal(pred, other)
        replay, norms = apply(valid, perils, w.read(path), line)
        assert np.array_equal(replay, pred) and norms == a['held_normalizers']
        identity, _ = apply(valid, perils, a, line, weight=0.)
        assert np.array_equal(identity, valid.baseline_G3.to_numpy())
        shuffle = valid.iloc[::-1]; backwards, _ = apply(shuffle, perils, a, line)
        assert np.allclose(backwards[::-1], pred, rtol=2e-15, atol=1e-10)
        # Distinct matrix/log-space expression for the held application.
        matrix = np.column_stack([valid['f_' + p].to_numpy() * valid['s_' + p].to_numpy() * valid['q_' + p].to_numpy() for p in perils])
        risk = matrix @ np.array([a['perils'][p]['kappa'] for p in perils])
        for year in [2023, 2024]:
            mask = valid.year.eq(year).to_numpy() & valid.new_business.eq(0).to_numpy()
            independent = np.exp(np.log(valid.baseline_G3.to_numpy()[mask]) + WEIGHTS[line] * (np.log(risk[mask]) - np.log(valid.unshaped_T2b.to_numpy()[mask])))
            independent *= valid.baseline_G3.to_numpy()[mask].sum() / independent.sum()
            assert np.allclose(independent, pred[mask], rtol=1e-12, atol=1e-10)
        checks.append({'line': line, 'fold': held, 'full_learning_held_cost_count_reserve_invariant': True,
                       'saved_replay_exact': True, 'zero_weight_identity_exact': True, 'shuffled_keys_invariant_to_float_summation': True,
                       'independent_moment_and_application_math_passed': True})
    y = oof.T0.to_numpy(float); ref = oof.G3.to_numpy(float); pred = oof.RFS1.to_numpy(float)
    null = unit(y, np.full(len(y), y.mean())); den = null.sum(); gain = unit(y, ref) - unit(y, pred)
    for x in [ref, pred]: assert abs(unit(y, x).mean() - mean_tweedie_deviance(y, x, power=1.5)) < 1e-10
    group = pd.DataFrame({'group': oof.group_id, 'gain': gain, 'N': np.ones(len(y)), 'Y': y, 'sqrtY': np.sqrt(y)}).groupby('group').sum()
    assert abs((8 * np.sqrt(group.N.sum() * group.Y.sum()) - 8 * group.sqrtY.sum()) / den - 1) < 1e-12
    rng = np.random.default_rng(plan['bootstrap']['seed']); v = group.to_numpy(); boot = []
    for i in range(2000):
        ix = rng.integers(0, len(group), len(group)); sums = v[ix].sum(axis=0)
        dd = 8 * np.sqrt(sums[1] * sums[2]) - 8 * sums[3]; assert dd > 0
        boot.append(float(sums[0] / dd))
    delta = float(gain.sum() / den); ci = np.quantile(boot, [.025, .975]).tolist()
    folds = {str(k): float(gain[oof.fold.eq(k)].sum() / den) for k in range(5)}
    years = {str(k): float(gain[oof.year.eq(k)].sum() / den) for k in [2023, 2024]}
    cells = []
    for (line, year, nb), ix in oof.groupby(['line', 'year', 'new_business']).groups.items():
        ii = np.asarray(list(ix)); yy = y[ii]; dd = unit(yy, np.full(len(yy), yy.mean())).sum()
        cells.append({'line': line, 'year': int(year), 'NB': int(nb), 'rows': len(ii),
                      'delta_global': float(gain[ii].sum() / den), 'delta_cell_null': float(gain[ii].sum() / dd),
                      'AE_ref': float(yy.sum() / ref[ii].sum()), 'AE_RFS1': float(yy.sum() / pred[ii].sum())})
    influence = group.sort_values('gain', ascending=False)
    post31 = float((group.gain.sum() - influence.gain.iloc[:31].sum()) / den)
    highcost = set(oof.groupby('group_id').T0.sum().nlargest(31).index)
    removed = float(gain[~oof.group_id.isin(highcost)].sum() / den)
    criteria = {'delta_min': delta >= plan['criterion']['delta_min'], 'lower95_positive': ci[0] > 0,
                'positive_folds_min4': sum(x > 0 for x in folds.values()) >= 4,
                'both_years_nonnegative': all(x >= 0 for x in years.values()), 'post31_nonnegative': post31 >= 0,
                'cell_min': min(x['delta_cell_null'] for x in cells) >= -.001,
                'full_F3c_comparator_and_additional_vetoes': False}
    ratios = {}
    for line in WEIGHTS:
        mask = oof.line.eq(line) & oof.new_business.eq(0)
        ratios[line] = np.quantile(pred[mask] / ref[mask], [0, .01, .5, .99, 1]).tolist()
    assert np.array_equal(pred[oof.new_business.eq(1)], ref[oof.new_business.eq(1)])
    scores = {name: float(1 - unit(y, oof[name].to_numpy()).sum() / den) for name in ['N3', 'G3', 'RFS1']}
    oof.to_parquet(OUT / 'oof_2023_2024.parquet', index=False); influence.to_parquet(OUT / 'group_influence.parquet')
    dump(OUT / 'report.json', {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'exploratory_single_contrast_complete_no_formal_admission', 'scores': scores, 'delta_vs_G3': delta,
        'bootstrap95': ci, 'fold_contributions': folds, 'year_contributions': years, 'cells': cells,
        'post31_favorable_groups_delta': post31, 'remove31highest_cost_groups_delta': removed,
        'criteria': criteria, 'all_criteria_pass': all(criteria.values()), 'ratios_REN': ratios,
        'all_NB_exact': True, 'numeric_controls': checks, 'new_iterative_price_fits': 0, 'new_C0_fits': 0,
        'empirical_global_cost_levels': 15, 'frequency_moment_constants': 75, 'mark_moment_constants': 75,
        'derived_shrunk_peril_factors': 75, 'held_prediction_only_normalizers': 30,
        'control_recomputation_same_moment_constants_separate': 165,
        'source_model_refits': 0, 'new_test_prices': 0, 'new_submissions': 0,
        'plan_sha256': w.sha(PLAN), 'reference': plan['reference'], '2024_open': True,
        'B00_all_alternatives_preserved': True, 'goal_achieved': False,
        'not_exact_received_F4_replay': True, 'conditional_source_and_master_availability_limits': plan['limits']})
    assert all(w.sha(ROOT / path) == sha for path, sha in plan['sources'].items())
    print(json.dumps({'scores': scores, 'delta': delta, 'bootstrap95': ci, 'folds': folds, 'years': years,
                      'post31': post31, 'criteria': criteria, 'new_model_fits': 0, 'new_C0_fits': 0, 'new_submissions': 0}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'register', 'run'])
    args = parser.parse_args(); {'prepare': prepare, 'register': register, 'run': run}[args.mode]()
