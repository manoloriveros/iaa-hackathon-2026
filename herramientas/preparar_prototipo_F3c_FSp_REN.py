"""Prototipo revisable de2025; no contiene una vía de envío ni una admisión."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import argparse
import importlib.util
import json
import math
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'; OUT = BASE / 'F3c_FSp_REN_prototipo_20261026_v1'
PLAN = R / 'registro/semana2_mision017_F3c_FSp_REN_prototipo_plan_v1.json'
CV = BASE / 'FSp_REN_G3_prod_contraste_20261026_v1'
PARENT = BASE / 'entrega_F3c_investigacion_20261026_v1/codex_F3c_residual_2025.csv'
COHORT = BASE / 'renovacion_fsp_recepcion_20261026_v1/cohort_2025.parquet'
SAMPLE = R / 'privado/semana2/envios/g4_20261025_v1/official_sample_format.csv'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


io = load('canonical_CSV_io', R / 'herramientas/preparar_F3c_REN_MC.py')
w = io.w
WEIGHTS = {'motor': .25, 'buildings': .25, 'contents': .5}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def locations(line):
    if line == 'buildings':
        matrix = BASE / 'FSp_edificios_matrices_20261026_v1'
        return (matrix / 'matrix_target_prod.parquet', matrix / 'rows_target_prod.parquet',
                BASE / 'FSp_edificios_productor_20261026_v1/components_prod.parquet')
    matrix = BASE / 'FSp_MC_recuperacion_20261026_v1/matrices'
    return (matrix / f'matrix_{line}_target_prod.parquet', matrix / f'rows_{line}_target_prod.parquet',
            BASE / f'FSp_MC_recuperacion_20261026_v1/productor/components_{line}_prod.parquet')


def align_matrix(frame, model):
    columns = model.feature_name(); result = frame[columns].copy()
    cats = [c for c in columns if str(result[c].dtype) == 'category']
    assert len(cats) == len(model.pandas_categorical)
    for c in columns:
        if c in cats:
            result[c] = pd.Categorical(result[c].astype('string'), categories=model.pandas_categorical[cats.index(c)])
        else:
            result[c] = pd.to_numeric(result[c], errors='coerce').astype('float64')
    return result


def prepare():
    assert not OUT.exists(); OUT.mkdir()
    parent = pd.read_csv(PARENT, dtype=str); io.ticks(parent)
    assert w.sha(PARENT) == '5ab5e4e34290cf6ed6a7a792f59e1e55a4f056400bbbdf8401933afd236b3276'
    sample = pd.read_csv(SAMPLE, dtype=str)
    assert np.array_equal(parent.row_id, sample.row_id) and len(parent) == 209063
    cohort = pd.read_parquet(COHORT).set_index('row_id').loc[parent.row_id].reset_index()
    assert cohort.row_id.is_unique and set(cohort.row_id) == set(parent.row_id)
    paths = [Path(__file__), Path(io.__file__), PARENT, COHORT, SAMPLE, CV / 'report.json', CV / 'additional_veto_points.json']
    inputs = {}; counts = {}
    for line in WEIGHTS:
        matrixpath, rowpath, componentpath = locations(line)
        modelpath = BASE / f'linaje_T2b_v1/modelos/prod/T2b_{line}.txt'
        paths += [matrixpath, rowpath, componentpath, modelpath, BASE / f'linaje_T2b_v1/raw_rates_{line}.parquet']
        rows = pd.read_parquet(rowpath); future = rows.loc[rows.is_test & rows.new_business.eq(0)]
        assert future.year.eq(2025).all() and future.row_id.is_unique
        expected = cohort.loc[cohort.line.eq(line) & cohort.new_business.eq(0), 'row_id']
        assert set(future.row_id) == set(expected)
        model = lgb.Booster(model_file=str(modelpath))
        frame = pd.read_parquet(matrixpath); assert len(frame) == len(rows)
        X = align_matrix(frame.iloc[np.flatnonzero(rows.is_test & rows.new_business.eq(0))[:2]], model)
        assert list(X.columns) == model.feature_name()  # no predict call in preflight
        inputs[line] = {'matrix': w.rel(matrixpath), 'rows': w.rel(rowpath), 'components': w.rel(componentpath),
                        'model': w.rel(modelpath), 'features': model.feature_name(), 'future_REN_rows': len(future)}
        counts[line] = len(future)
        paths += [CV / f'learning_{line}_fold{k}.json' for k in range(5)]
    assert sum(counts.values()) == 50083
    original = BASE.parent / 'claude_ml_independiente_20261023/prediccion_2025_mlind.csv'; paths.append(original)
    dump(OUT / 'preflight.json', {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'inputs': inputs, 'counts_REN': counts, 'no_new_inference_or_prices': True,
        'sources': {w.rel(path): w.sha(path) for path in paths}, 'published_T2b_CSV': w.rel(original)})
    print(json.dumps({'preflight': 'passed', 'rows': len(parent), 'future_REN_rows': sum(counts.values()), 'inferences': 0, 'new_prices': 0}))


def register():
    assert not PLAN.exists() and not (OUT / 'registration.json').exists()
    pre = w.read(OUT / 'preflight.json'); cv = w.read(CV / 'report.json'); vetos = w.read(CV / 'additional_veto_points.json')
    assert not cv['all_criteria_pass']
    plan = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'candidate_id': 'F3c-FSp-REN-PROTOTYPE',
            'hypothesis': 'Build a concrete reproducible2025artifact from frozen components, to inspect actual production plumbing before any external delivery; not another fit or a claim that failed statistical gates passed.',
            'parent': {'path': w.rel(PARENT), 'sha256': w.sha(PARENT), 'source_recipe_author': 'Claude', 'new_composition_author': 'Codex'},
            'weights': WEIGHTS, 'NB': 'copy exact parent price strings', 'C0': 'none; future ultimate convention q=1 for allperils',
            'source': 'Frozen prod2021–2024FSp/T2b; target climatemean2023–24; explicit historia2',
            'formula': 'For each line and saved outer-fold k: annual_FSp=sum(kappa_kp*f_period_p/exposure_original*s_p). Ratio to annual_raw_T2b, power w, multiply actual F3c REN and normalize to its REN total. Equal arithmetic mean of5normalized member prices, then6decimals.',
            'why_annualization': 'Producer f already includes calendar exposure; annualize before dimensionless ratio. Parent remains a period price. No second exposure and no cp2025=0.',
            'fold_ensemble': {'weights': [.2] * 5, 'learned_weights': False,
                              'limit': 'Historical OOF used a single held-scope estimator. Final5member mean has not been assessed by a nested held ensemble; do not claim an exact OOF replay of this ensemble.'},
            'denominator': 'New T2b inference using restored fullprecision prod matrix and explicit stored categorical levels. Compare fixed historical samples to saved annual raw rates; inspect compatibility with rounded original2025T2b CSV without changing recipe after seeing errors.',
            'budget': {'new_model_fits': 0, 'new_C0_fits': 0, 'new_calibration_constants': 0, 'primary_T2b_inference_calls': 3,
                       'primary_T2b_future_REN_rows': 50083, 'historical_replay_rows': 192, 'future_shuffle_check_rows': 96,
                       'new_member_normalizers': 15, 'new_CSVs': 1, 'new_derived_price_rows': 50083, 'new_submissions': 0},
            'numeric_checks': ['Exact official keys/order209063', 'Positive finite prices', 'Exact NB strings',
                               'Parent REN totals before rounding, half-microCU tolerance per row after rounding',
                               'Zero weight identity, key-shuffle invariance, outside-scope component changes ignored',
                               'Independent log-space and Decimal rounding checks', 'CSV readback and SHA, source hashes unchanged'],
            'rounding': 'IEEEfloat64 model algebra, exact as_integer_ratio rational conversion to microCU with ties-to-even. Independent Decimal precision100check. Preserve NB ticks without floating round trip.',
            'source_validation': {'report': w.rel(CV / 'report.json'), 'sha256': w.sha(CV / 'report.json'),
                                  'local_delta_vs_G3': cv['delta_vs_G3'], 'all_checks_pass': False,
                                  'weighted2025_diagnostic_delta': vetos['weighted2025_incremental_delta_vs_G3'],
                                  'original_A1_proxy_veto_pass': False, 'complete_F3c_comparator_missing': True},
            'submission_allowed': False, 'submission_ready': False, 'formal_promotion': False,
            'predictive_goal_achieved': False, 'B00_all_alternatives_preserved': True, '2024_open': True,
            'sources': {**pre['sources'], w.rel(OUT / 'preflight.json'): w.sha(OUT / 'preflight.json')}}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. Registro un prototipo2025 revisable, antes de inferir o crear precios. No está admitido ni autorizado para enviar por esta receta. '
        'Se mantiene el F3c medido como padre real, todo NB exacto y los totales REN por ramo. Se insertan FSp con pesos fijos .25/.25/.5 y '
        'los cinco kappa de ámbitos guardados, sin volver a ajustar modelos, C0 o constantes; se promedian los cinco miembros con pesos iguales. '
        'El OOF evaluó un miembro por retenido, por lo que no se presenta esa media final como un ensemble validado por un flujo anidado. '
        'Tres inferencias T2b sobre50.083REN de2025, más controles puntuales; el resto de precios se copia. Se anualiza f una sola vez y se usa q=1, '
        'nunca cp2025cero. Se comprobarán claves, orden, NB, totales, identidad, aritmética y replay histórico del denominador. '
        'La mejora local+0,00185 sigue fallando mínimo/influencia; el veto A1 original es ligeramente negativo y falta el F3c completo. '
        'La sensibilidad2025 es solo+0,00038 y el76%del test es NB, que esta receta no cambia. Este archivo no resuelve esos límites ni habilita otro envío. '
        'B00 y alternativas se conservan;2024abierto. Plan: ' + w.rel(PLAN) + '.', encoding='utf8')
    response = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-MISION017-F3c-FSP-REN-PROTOTIPO-PREVIO',
        '--asunto', 'Prototipo2025 con padre F3c: flujo revisable, sin admisión para enviar', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    dump(OUT / 'registration.json', {'plan_sha256': w.sha(PLAN), 'forum': json.loads(response.stdout)})
    print(json.dumps({'registered': True, 'submission_allowed': False, 'new_fits': 0, 'future_inference_rows': 50083, 'forum': json.loads(response.stdout)}))


def combine(parent, cohort, kernels, rates, kappas, weights):
    assert cohort.row_id.is_unique and set(cohort.row_id) == set(parent.row_id)
    assert rates.row_id.is_unique
    parent_ticks = io.ticks(parent); base = parent_ticks / 1e6; output = base.copy()
    c = cohort.set_index('row_id').loc[parent.row_id]; members = np.tile(base[:, None], (1, 5)); norms = {}
    assert c.line.isin(weights).all() and c.new_business.notna().all()
    for line in weights:
        mask = c.line.eq(line).to_numpy() & c.new_business.eq(0).to_numpy(); ids = parent.row_id[mask]
        assert kernels[line].index.is_unique
        kernel = kernels[line].loc[ids]; annual = rates.set_index('row_id').loc[ids, 'annual_T2b'].to_numpy()
        assert np.isfinite(annual).all() and (annual > 0).all()
        for held in range(5):
            risk = sum(kappas[line][held][p] * kernel[p].to_numpy() for p in kernel.columns)
            assert np.isfinite(risk).all() and (risk > 0).all()
            factor = (risk / annual) ** weights[line]
            norm = float(np.dot(base[mask], factor) / base[mask].sum()); norms[f'{line}|{held}'] = norm
            members[mask, held] = base[mask] * factor / norm
            assert abs(members[mask, held].sum() / base[mask].sum() - 1) < 1e-12
        output[mask] = members[mask].mean(axis=1)
    nb = c.new_business.to_numpy(dtype=bool); ticks = parent_ticks.copy()
    for i in np.flatnonzero(~nb):
        numerator, denominator = float(output[i]).as_integer_ratio()
        ticks[i] = io.round_ratio_even(numerator * 1000000, denominator)
    assert (ticks > 0).all() and np.isfinite(output).all()
    return ticks, output, members, norms


def run():
    assert not (OUT / 'started.json').exists()
    assert w.sha(PLAN) == w.read(OUT / 'registration.json')['plan_sha256']
    plan = w.read(PLAN); pre = w.read(OUT / 'preflight.json')
    assert all(w.sha(ROOT / p) == sha for p, sha in plan['sources'].items())
    dump(OUT / 'started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'plan_sha256': w.sha(PLAN)})
    parent = pd.read_csv(PARENT, dtype=str); parent_ticks = io.ticks(parent); cohort = pd.read_parquet(COHORT)
    rates = []; kernels = {}; kappas = {}; denominator_checks = []; legacy = pd.read_csv(ROOT / pre['published_T2b_CSV'], dtype={'row_id': str}).set_index('row_id')
    for line, meta in pre['inputs'].items():
        rows = pd.read_parquet(ROOT / meta['rows']); matrix = pd.read_parquet(ROOT / meta['matrix'])
        mask = rows.is_test & rows.new_business.eq(0); future_rows = rows.loc[mask].copy()
        assert future_rows.year.eq(2025).all()
        model = lgb.Booster(model_file=str(ROOT / meta['model']))
        X = align_matrix(matrix.loc[mask], model)
        annual = np.exp(model.predict(X, raw_score=True, num_threads=2))
        assert np.isfinite(annual).all() and (annual > 0).all()
        # The new2025input wrapper is checked against a fixed historic sample.
        oldrates = pd.read_parquet(BASE / f'linaje_T2b_v1/raw_rates_{line}.parquet').set_index('row_id')
        historic = np.flatnonzero(~rows.is_test)
        sample = historic[np.linspace(0, len(historic) - 1, 64, dtype=int)]
        replay = np.exp(model.predict(align_matrix(matrix.iloc[sample], model), raw_score=True, num_threads=2))
        expected = oldrates.loc[rows.iloc[sample].row_id, 'annual_raw_T2b'].to_numpy()
        assert np.array_equal(replay, expected)
        order = np.linspace(0, len(X) - 1, 32, dtype=int)[::-1]
        shuffled = np.exp(model.predict(X.iloc[order], raw_score=True, num_threads=2))
        assert np.array_equal(shuffled, annual[order])
        rates.append(pd.DataFrame({'row_id': future_rows.row_id.to_numpy(), 'line': line, 'annual_T2b': annual,
                                   'exposure_original': future_rows.exposure.to_numpy()}))
        f = pd.read_parquet(ROOT / meta['components']).set_index('row_id').loc[future_rows.row_id]
        assert np.array_equal(f.exposure, future_rows.exposure)
        kappas[line] = {held: {p:q['kappa'] for p,q in w.read(CV / f'learning_{line}_fold{held}.json')['perils'].items()} for held in range(5)}
        perils = sorted(kappas[line][0]); kernel = pd.DataFrame(index=f.index)
        for p in perils: kernel[p] = f['f_' + p].to_numpy() / f.exposure.to_numpy() * f['s_' + p].to_numpy()
        assert np.isfinite(kernel.to_numpy()).all() and (kernel.to_numpy() > 0).all()
        kernels[line] = kernel
        kernel.to_parquet(OUT / f'annual_FSp_kernel_REN_{line}.parquet')
        # Compatibility evidence only: no calibration or recipe change from it.
        old = legacy.loc[future_rows.row_id, 'prediction'].to_numpy()
        ratio = old / (annual * future_rows.exposure.to_numpy()); centre = float(np.median(ratio))
        error = old - centre * annual * future_rows.exposure.to_numpy()
        denominator_checks.append({'line': line, 'future_REN_rows': len(future_rows),
            'historical64_bit_exact': True, 'future32_shuffle_bit_exact': True,
            'legacy_T2b_level_for_comparison_only': centre, 'legacy_max_abs_price_error_after_single_level': float(np.max(np.abs(error))),
            'legacy_rows_within_1microCU': int((np.abs(error) <= 1e-6).sum()),
            'legacy_shape_exact_not_required_or_asserted_for_new_historia2_denominator': True})
    rate = pd.concat(rates, ignore_index=True); assert len(rate) == 50083 and rate.row_id.is_unique
    rate.to_parquet(OUT / 'annual_T2b_REN_2025.parquet', index=False); rate_index = rate.set_index('row_id')
    ticks, unrounded, members, norms = combine(parent, cohort, kernels, rate, kappas, WEIGHTS)
    identity, _, _, _ = combine(parent, cohort, kernels, rate, kappas, dict.fromkeys(WEIGHTS, 0.))
    assert np.array_equal(identity, io.ticks(parent))
    shuffled, _, _, _ = combine(parent, cohort.iloc[::-1], {l:k.iloc[::-1] for l,k in kernels.items()}, rate.iloc[::-1], kappas, WEIGHTS)
    assert np.array_equal(shuffled, ticks)
    # Extra NB component values can be arbitrarily wrong: they are outside the
    # affected population and must never change copied NB or REN output.
    badkernels = {}; extra_rates = []
    for line in WEIGHTS:
        ids = cohort.loc[cohort.line.eq(line) & cohort.new_business.eq(1), 'row_id'].iloc[:3]
        badkernels[line] = pd.concat([kernels[line], pd.DataFrame(1e30, index=ids, columns=kernels[line].columns)])
        extra_rates.append(pd.DataFrame({'row_id': ids, 'line': line, 'annual_T2b': 1e-30, 'exposure_original': 1.}))
    badrate = pd.concat([rate, *extra_rates], ignore_index=True)
    assert np.array_equal(combine(parent, cohort, badkernels, badrate, kappas, WEIGHTS)[0], ticks)
    for bad in [rate.iloc[1:].copy(), pd.concat([rate, rate.iloc[:1]], ignore_index=True), rate.assign(annual_T2b=-1.)]:
        try: combine(parent, cohort, kernels, bad, kappas, WEIGHTS)
        except (AssertionError, KeyError, ValueError): pass
        else: raise AssertionError('Invalid denominator input accepted')
    c = cohort.set_index('row_id').loc[parent.row_id]; nb = c.new_business.to_numpy(dtype=bool)
    assert np.array_equal(ticks[nb], io.ticks(parent)[nb])
    sample = np.linspace(0, len(parent) - 1, 256, dtype=int)
    for i in sample:
        if not nb[i]:
            with localcontext() as ctx:
                ctx.prec = 100
                independent = int((Decimal.from_float(float(unrounded[i])) * Decimal(1000000)).quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
            assert int(ticks[i]) == independent
    cells = []
    for line in WEIGHTS:
        mask = c.line.eq(line).to_numpy() & ~nb
        parent_value = io.ticks(parent)[mask]
        assert abs(unrounded[mask].sum() / (parent_value.sum() / 1e6) - 1) < 1e-12
        diff = int(ticks[mask].sum() - parent_value.sum())
        assert abs(diff) <= mask.sum() / 2 + 1
        ratio = ticks[mask] / parent_value
        for i in np.flatnonzero(mask)[np.linspace(0, int(mask.sum()) - 1, 16, dtype=int)]:
            rid = parent.row_id.iloc[i]; independent_members = []
            for held in range(5):
                risk = math.fsum(kappas[line][held][p] * float(kernels[line].loc[rid, p]) for p in kernels[line].columns)
                annual = float(rate_index.loc[rid, 'annual_T2b'])
                independent = math.exp(math.log(float(parent_ticks[i]) / 1e6) + WEIGHTS[line] *
                    (math.log(risk) - math.log(annual)) - math.log(norms[f'{line}|{held}']))
                assert np.isclose(independent, members[i, held], rtol=2e-12, atol=1e-10)
                independent_members.append(independent)
            assert np.isclose(math.fsum(independent_members) / 5, unrounded[i], rtol=2e-12, atol=1e-10)
        cells.append({'line': line, 'REN_rows': int(mask.sum()), 'changed_rows': int((ticks[mask] != parent_value).sum()),
                      'rounding_total_error_microCU': diff, 'ratio_quantiles': np.quantile(ratio, [0, .01, .5, .99, 1]).tolist()})
    path = OUT / 'F3c_FSp_REN_prototipo_2025.csv'; io.write_csv(path, parent.row_id, ticks)
    back = pd.read_csv(path, dtype=str); assert np.array_equal(back.row_id, parent.row_id) and np.array_equal(io.ticks(back), ticks)
    assert np.array_equal(back.prediction[nb], parent.prediction[nb])
    pd.DataFrame({'row_id': parent.row_id, **{f'member{k}':members[:, k] for k in range(5)}, 'unrounded_mean': unrounded}).to_parquet(OUT / 'member_prices_2025.parquet', index=False)
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(), 'status': 'prototype_numeric_QA_complete_not_submission_ready',
        'CSV': {'path': w.rel(path), 'sha256': w.sha(path), 'rows': len(back), 'bytes': path.stat().st_size, 'total_CU': int(ticks.sum()) / 1e6},
        'cells': cells, 'NB_exact_strings': True, 'NB_rows': int(nb.sum()), 'official_order_exact': True,
        'identity_and_key_shuffle_CSV_exact': True, 'historical_T2b_replay_and_future_shuffle': denominator_checks,
        'arbitrary_extra_NB_component_values_ignored': True, 'missing_duplicate_negative_denominator_rejected': True,
        'independent_Decimal_rounding_exact': True, 'independent_scalar_log_space_application_passed': True,
        'new_T2b_future_model_inference_rows': 50083, 'historic_wrapper_check_rows': 192, 'future_shuffle_check_rows': 96,
        'new_model_fits': 0, 'new_C0_fits': 0, 'new_calibration_constants': 0, 'new_member_normalizers': 15,
        'new_derived_REN_price_rows': 50083, 'new_CSVs': 1, 'new_submissions': 0,
        'saved_kappa_scope_ensemble_not_nested_OOF_validated': True, 'predictive_admission_established': False,
        'submission_allowed': False, 'submission_ready': False, 'formal_promotion': False,
        'source_validation_failures_preserved': plan['source_validation'], 'B00_all_alternatives_preserved': True,
        '2024_open': True, 'goal_achieved': False, 'plan_sha256': w.sha(PLAN), 'sources_unchanged': True}
    assert all(w.sha(ROOT / p) == sha for p, sha in plan['sources'].items())
    dump(OUT / 'report.json', report)
    print(json.dumps({k:report[k] for k in ['status','CSV','cells','NB_rows','new_model_fits','new_C0_fits','new_submissions','submission_allowed']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); p = argparse.ArgumentParser(); p.add_argument('mode', choices=['prepare','register','run'])
    a = p.parse_args(); {'prepare':prepare,'register':register,'run':run}[a.mode]()
