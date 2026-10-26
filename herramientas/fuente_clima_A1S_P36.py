"""Clima anual en los árboles A1S existentes, con capacidad/rondas fijas."""
from datetime import datetime, timezone
import argparse
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
ORIGINAL = HOME/'source_models'; INPUT = BASE/'P35_entradas_clima_20261026'
OUT = BASE/'P36_fuente_clima_20261026'
PLAN = R/'registro/semana2_fuente_clima_A1S_privada_plan.json'
INDEX = R/'registro/semana2_fuente_clima_A1S_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P36_CLIMA_EN_ARBOL_FUENTE.md'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.special import logsumexp
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits


def load(name, path):
    sp = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


previous = load('p36_saved_tree_math', R/'herramientas/fuente_ausencias_P25.py')
w = previous.w; LINES = ['motor', 'buildings', 'contents']; SEEDS = [11, 12, 13]
FIELDS = ['annual_'+v for v in ['hail_days', 'wind_exposure_index', 'freezing_days', 'dry_summer_index', 'wildfire_index', 'rainfall_mm', 'mean_temperature_c']]


def utc(): return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    with path.open('x', encoding='utf8') as f: json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def digest(values): return hashlib.sha256('\n'.join(sorted(map(str, values))).encode()).hexdigest()


def attach(x, rows, cov):
    assert rows.row_id.is_unique and cov.row_id.is_unique and np.array_equal(rows.row_id, cov.row_id)
    assert np.array_equal(rows.year, cov.year) and len(x) == len(rows)
    assert not set(FIELDS).intersection(x.columns) and np.isfinite(cov[FIELDS].to_numpy(float)).all()
    result = x.copy()
    for c in FIELDS: result[c] = cov[c].to_numpy(float)
    assert result.drop(columns=FIELDS).equals(x)
    return result


def payload(x, y, exposure, selected, initial):
    return x.loc[selected], np.asarray(y)[selected], np.log(np.asarray(exposure)[selected])+initial


def argument_control(x, y, exposure, selected, initial):
    a = payload(x, y, exposure, selected, initial)
    yy = y.copy(); ee = exposure.copy(); xx = x.copy()
    yy[~selected] = 1e15; ee[~selected] = 1e-10
    xx.loc[~selected, FIELDS] = -1e9
    b = payload(xx, yy, ee, selected, initial)
    pd.testing.assert_frame_equal(a[0], b[0], check_exact=True)
    assert np.array_equal(a[1], b[1]) and np.array_equal(a[2], b[2])
    return {'held_source_cost_exposure_weather_do_not_change_fit_arguments': True,
        'response_sha256': hashlib.sha256(a[1].tobytes()).hexdigest(),
        'init_score_sha256': hashlib.sha256(a[2].tobytes()).hexdigest(),
        'scope': 'Exact actual Dataset arguments, not a second fitted model or independent validation.'}


def sources():
    paths = [Path(__file__), Path(previous.__file__), INPUT/'report.json',
        R/'registro/semana2_mision017_A1S_fuente_plan_v1.json',
        R/'registro/semana2_mision017_fase2_tanda7_plan_v2.json', R/'registro/semana2_mision017_fase2_tanda8_plan_v2.json',
        R/'src/semana2/lineas/ml_independiente_20261023/codigo/e13_clima_anual.py']
    for line in LINES:
        paths += [HOME/f'{kind}_s1_{line}.parquet' for kind in ['matrix', 'rows']]
        paths += [HOME/f'rows_s2_{line}.parquet', HOME/f'matrix_s2_{line}.parquet', HOME/f'partition_source/folds_{line}.parquet']
        paths += [INPUT/f'weather_{mk}_{line}.parquet' for mk in ['s1', 's2_historical']]
        for seed in SEEDS:
            paths += [ORIGINAL/f'{line}_seed{seed}_{kind}/fit_record.json' for kind in ['inner', 'full']]
            paths += [ORIGINAL/f'{line}_seed{seed}_inner/model.txt']
    return paths


def check(): assert w.read(PLAN)['sources'] == {w.rel(p): w.sha(p) for p in sources()}


def prepare():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    assert w.read(INPUT/'report.json')['all_keys_and_values_complete']
    OUT.mkdir(); rounds = {}; params = {}; bases = {}
    for line in LINES:
        for seed in SEEDS:
            key = f'{line}_seed{seed}'; old = w.read(ORIGINAL/f'{key}_inner/fit_record.json')
            rounds[key] = old['best_iteration']; params[key] = old['parameters']
            bases[key] = {kind: w.read(ORIGINAL/f'{key}_{kind}/fit_record.json')['initial_base'] for kind in ['inner', 'full']}
    # New join invariance only; no repeated historical synthetic model training.
    rows = pd.DataFrame({'row_id': ['a', 'b', 'c'], 'year': [2023, 2024, 2024]})
    cov = rows.copy()
    for j, c in enumerate(FIELDS): cov[c] = np.arange(3)+j*.5
    x = pd.DataFrame({'existing': [1., 2., 3.]})
    toy = attach(x, rows, cov)
    pd.testing.assert_frame_equal(attach(x.iloc[::-1], rows.iloc[::-1], cov.iloc[::-1]), toy.iloc[::-1], check_exact=True)
    selected = np.array([True, False, True]); boundary = argument_control(toy, np.array([0., 5., 2.]), np.array([.3, .8, 1.]), selected, 0.)
    rejected = False
    try: attach(x, rows, cov.iloc[::-1])
    except AssertionError: rejected = True
    assert rejected
    fixture = {'join_reversal_and_protected_columns_exact': True, 'wrong_key_order_rejected': True, 'actual_payload_function': boundary, 'new_fits': 0}
    dump(OUT/'synthetic.json', fixture)
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'A1S_same_capacity_seven_official_annual_weather_fields',
        'hypothesis': 'Current A1S omits climate entirely; its source approximation cannot represent climate-by-physical-risk relationships. Add seven official same-year weather covariates to the same trees, with no extra leaves, rounds, alpha search or importance weights.',
        'necessity': 'P30source count/mark main effects harmed newbusiness brokers; P32did not support a source NB-by-broker interaction, P33target support failed, P34source weighting failed. Existing T7/T8standard weather overlays did not transfer stably. This motivates a bounded feature-representation test, not proof of cause or another unconditional complexity increase.',
        'related_prior': 'E13already tested annual weather in old T2bsource2021-2023. Current A1Sdiffers in source-only offset, notification histories, customer/address groups,2021-2024source and complete target algorithm. Preserve that negative precedent; no claim of independent new weather discovery.',
        'features': 'Original matrices unchanged, append exactly seven raw official annual fields fromP35. All existing categories, exposure, histories/costs unchanged. No target- or held-label preprocessing, nuisance weather coefficients, region/year identifiers or new features.',
        'fields': FIELDS, 'parameters': params, 'rounds': rounds, 'reused_initial_bases': bases,
        'inner_split': 'Exact saved source connected customer/address groups, exclude internal_validation. All3seeds form one fixed geometric mean; no seed selection or early stopping.',
        'source_veto': 'Mean total-period Tweedie1.5deviance of three-seed geometric mean on exact original held rows <=1.002original ensemble in EACH line. All3required; no selecting lines, seasons or perils. Same veto asP25, not a private-generalization certificate.',
        'full_refit_if_all_pass': 'Nine full-source models, same original parameters/rounds and full initial bases. Center each raw delta by original exposure_model weighted source arithmetic risk mean. Geometric mean all3seeds, export only historical2023/2024components.',
        'objective': 'Original total-periodT0 Tweedie1.5with log(e_cost)+source-only base as init_score. No second exposure, sample_weight or recalculation ofC0.',
        'budget': {'inner_fits': 9, 'conditional_full_fits': 9, 'max_real_fits': 18, 'new_C0_fits': 0, 'new_target_fits': 0, 'new_target_scores': 0, 'new2025inference': 0, 'new_submissions': 0},
        'controls': ['Hash each exact input before/after; per-fit invocation before call, save model before downstream checks.',
            'Poison held labels/exposure/weather at Dataset argument boundary; exclude held groups, compare actual training row/group digests.',
            'Save/load/reversed-order/independent leaf sum; total-period loss via scalar and sklearn.',
            'Replay saved ensemble source loss by scalar sums with ML blocked; retain adverse and failed attempts.'],
        'limits': ['Annual weather is retrospective conditional competition input; availability at quote time not established.',
            'Source holdout already used for original rounds, labels inspected adaptively; same region/year weather affects many groups.',
            'Source e_cost/frozen category vocabulary have whole-source ancestry; no independent source end-to-end confirmation.',
            '2024target is open adaptive development, not pristine holdout; fine-weight ESS, sparse target NB, reserve/tail/undated masters remain.',
            'No target benefit or public/private readiness established by a source veto alone.'],
        'sources': {w.rel(p): w.sha(p) for p in sources()}, '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'; body.write_text('Codex. Registro P36: agregar solo siete campos climáticos oficiales anuales al A1Sactual, con idénticos árboles, parámetros y rondas por semilla. E13/T7/T8adversos conservados; cambia el núcleo completo declarado, no se presume novedad por renombrar clima. Primero9ajustes internos sobre los grupos fuente guardados, sin early stopping, pesos de dominio o nuevas curvas C0. Veto conjunto: desviación del ensemble geométrico de3semillas no mayor de1,002veces la original en cada ramo. Solo si pasan los tres se permiten9refits y componentes históricos2023/2024. Máximo18ajustes, cero calibraciones/scores destino, inferencias2025o envíos. La fuente y el clima siguen condicionales/adaptativos; no disponibilidad prospectiva o mejora privada probada. B00/F3c/alternativas conservados,2024abierto. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN), encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P36-CLIMA-FUENTE-PREVIO', '--asunto', 'P36: clima anual en A1S con capacidad fija y veto fuente previo', '--cuerpo', str(body)], check=True, capture_output=True, text=True, encoding='utf8')
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P36registered_no_fit', 'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(p.stdout)}
    dump(OUT/'registration.json', receipt); dump(INDEX, receipt); print(json.dumps({'registered': True, 'max_fits': 18, 'forum': receipt['forum']}))


def state(status, execution):
    archive = R/'privado'/('p36_state_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    attempts = sorted(p.parent.name for p in OUT.glob('*/fit_invoked.json')); saved = sorted(p.parent.name for p in OUT.glob('*/fit_record.json'))
    cp = R/'registro/semana2_contadores_propios_actual.json'; counts = w.read(cp)
    prior = counts.get('phase2_private_P36_source_climate', {}).get('counted_fit_keys', [])
    assert set(prior).issubset(attempts); added = len(set(attempts)-set(prior))
    phasepath = R/'registro/semana2_mision017_fase2_actual.json'; phase = w.read(phasepath)
    current = {'author': 'Codex', 'utc': utc(), 'status': status, 'plan': w.rel(PLAN), 'output': w.rel(OUT),
        'attempts': len(attempts), 'completed': len(saved), 'execution': execution, 'new_C0_fits': 0, 'new_target_scores': 0, 'new_submissions': 0}
    w.update(cp, {'as_of_utc': utc(), 'cumulative_price_base_fits': counts['cumulative_price_base_fits']+added,
        'phase2_private_P36_source_climate': {'counted_fit_keys': attempts, 'attempts': len(attempts), 'completed': len(saved), 'plan': w.rel(PLAN)}}, archive)
    w.update(INDEX, current, archive); jobs = [] if execution is None else [execution]
    w.update(phasepath, {'private_P36_source': current, 'new_price_fits': phase['new_price_fits']+added, 'active_jobs': jobs, 'active_execution': execution}, archive)
    path = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(path)['week_2_mission017_phase2_20261025']
    own.update(private_P36_source=current, active_jobs=jobs, new_price_fits=phase['new_price_fits']+added)
    w.update(path, {'week_2_mission017_phase2_20261025': own, 'week_2_mission017_phase2_execution': execution}, archive)


def fit(folder, x, rows, part, selected, initial, params, rounds):
    assert not (folder/'fit_invoked.json').exists(), 'Existing attempt must be reconciled, never repeated automatically'
    y = rows.T0.to_numpy(float); e = rows.e_cost.to_numpy(float)
    assert math.isclose(initial, float(np.log(y[selected].sum()/e[selected].sum())), rel_tol=0, abs_tol=1e-14)
    control = argument_control(x, y, e, selected, initial)
    xx, yy, off = payload(x, y, e, selected, initial)
    dump(folder/'fit_invoked.json', {'author': 'Codex', 'utc': utc(), 'pid': os.getpid(), 'rounds': rounds,
        'plan_sha256': w.sha(PLAN), 'rows': int(selected.sum()), 'features': list(xx),
        'fit_row_digest': digest(rows.loc[selected, 'row_id']), 'fit_group_digest': digest(part.loc[selected, 'source_group'].unique()), 'argument_control': control})
    execution = {'author': 'Codex', 'pid': os.getpid(), 'script': w.rel(Path(__file__)), 'checkpoint': folder.name, 'kind': 'P36source_climate'}
    state('P36source_training_running', execution); start = time.monotonic()
    try:
        model = lgb.train(params, lgb.Dataset(xx, label=yy, init_score=off), num_boost_round=rounds)
        model.save_model(str(folder/'model.txt'))
        dump(folder/'fit_record.json', {'author': 'Codex', 'utc': utc(), 'parameters': params,
            'current_iteration': model.current_iteration(), 'initial_base': initial, 'source_rows': len(yy),
            'model_sha256': w.sha(folder/'model.txt'), 'seconds': time.monotonic()-start, 'lightgbm_version': lgb.__version__, 'plan_sha256': w.sha(PLAN)})
        assert model.current_iteration() == rounds
        state('P36fit_saved', execution); print(json.dumps({'completed': folder.name, 'seconds': round(time.monotonic()-start, 1)}), flush=True)
        return model
    except BaseException as exc:
        dump(folder/'failure.json', {'utc': utc(), 'exception': type(exc).__name__, 'message': str(exc)}); raise


def veto():
    results = []
    for line in LINES:
        rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'T0'])
        part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['row_id', 'internal_validation'])
        assert np.array_equal(rows.row_id, part.row_id); held = part.internal_validation.to_numpy(bool)
        fs = [pd.read_parquet(OUT/f'{line}_seed{seed}_inner/validation_predictions.parquet') for seed in SEEDS]
        assert all(np.array_equal(f.row_id, rows.loc[held, 'row_id']) for f in fs)
        losses = {kind: float(mean_tweedie_deviance(rows.loc[held, 'T0'], np.exp(np.mean([f[kind].to_numpy() for f in fs], axis=0)), power=1.5)) for kind in ['old', 'new']}
        results.append({'line': line, 'rows': int(held.sum()), 'baseline_mean_deviance': losses['old'], 'candidate_mean_deviance': losses['new'],
            'relative_loss': losses['new']/losses['old']-1, 'pass': losses['new'] <= 1.002*losses['old']})
    result = {'author': 'Codex', 'utc': utc(), 'results': results, 'all_pass': all(a['pass'] for a in results)}
    dump(OUT/'source_veto.json', result); return result


def run(resume=False):
    assert not (OUT/'report.json').exists(); check(); plan = w.read(PLAN)
    if resume:
        assert all((p.parent/'fit_record.json').exists() for p in OUT.glob('*/fit_invoked.json'))
        dump(OUT/('resume_'+datetime.now(timezone.utc).strftime('%H%M%S%f')+'.json'), {'utc': utc(), 'pid': os.getpid()})
    else: dump(OUT/'started.json', {'utc': utc(), 'pid': os.getpid(), 'plan_sha256': w.sha(PLAN)})
    start = time.monotonic(); checkpointed = False
    try:
        for full in [False, True]:
            if full and not w.read(OUT/'source_veto.json')['all_pass']: break
            for line in LINES:
                native = pd.read_parquet(HOME/f'matrix_s1_{line}.parquet')
                rows = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['row_id', 'year', 'T0', 'e_cost', 'exposure_model'])
                part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet')
                assert np.array_equal(rows.row_id, part.row_id) and rows.year.isin([2021, 2022, 2023, 2024]).all()
                held = part.internal_validation.to_numpy(bool); selected = np.ones(len(rows), dtype=bool) if full else ~held
                assert set(part.loc[held, 'source_group']).isdisjoint(set(part.loc[~held, 'source_group']))
                x = attach(native, rows, pd.read_parquet(INPUT/f'weather_s1_{line}.parquet'))
                y = rows.T0.to_numpy(float); e = rows.e_cost.to_numpy(float)
                assert np.isfinite(y).all() and (y >= 0).all() and np.isfinite(e).all() and (e > 0).all()
                for seed in SEEDS:
                    key = f'{line}_seed{seed}'; kind = 'full' if full else 'inner'; folder = OUT/f'{key}_{kind}'; folder.mkdir(exist_ok=True)
                    initial = plan['reused_initial_bases'][key][kind]
                    if (folder/'fit_record.json').exists():
                        assert w.read(folder/'fit_record.json')['model_sha256'] == w.sha(folder/'model.txt')
                        model = lgb.Booster(model_file=str(folder/'model.txt'))
                    else: model = fit(folder, x, rows, part, selected, initial, plan['parameters'][key], plan['rounds'][key])
                    if not full and not (folder/'validation.json').exists():
                        baseline = lgb.Booster(model_file=str(ORIGINAL/f'{key}_inner/model.txt'))
                        z = x.loc[held]; sample = np.unique(np.linspace(0, len(z)-1, 32, dtype=int))
                        loaded = lgb.Booster(model_file=str(folder/'model.txt')); raw = loaded.predict(z, raw_score=True, num_threads=2)
                        assert np.array_equal(raw[sample], model.predict(z.iloc[sample], raw_score=True, num_threads=2))
                        assert np.array_equal(raw[sample[::-1]], loaded.predict(z.iloc[sample[::-1]], raw_score=True, num_threads=2))
                        err = float(np.max(np.abs(previous.leaf_sum(loaded, z.iloc[sample[:6]])-raw[sample[:6]]))); assert err < 1e-10
                        old = baseline.predict(native.loc[held], raw_score=True, num_threads=2)
                        saved = pd.DataFrame({'row_id': rows.loc[held, 'row_id'].to_numpy(), 'new': raw+np.log(e[held])+initial, 'old': old+np.log(e[held])+initial})
                        yy = y[held]; mu = np.exp(saved.new.to_numpy())
                        manual = float(np.mean(2*yy/np.sqrt(mu)+2*np.sqrt(mu)))
                        assert math.isclose(manual, .5*mean_tweedie_deviance(yy, mu, power=1.5)+4*np.mean(np.sqrt(yy)), rel_tol=2e-13)
                        old_loss = float(np.mean(2*yy/np.exp(.5*saved.old.to_numpy())+2*np.exp(.5*saved.old.to_numpy())))
                        old_record = w.read(ORIGINAL/f'{key}_inner/fit_record.json')
                        assert abs(old_loss/old_record['best_score']['source_internal']['tweedie']-1) < 2e-6
                        saved.to_parquet(folder/'validation_predictions.parquet', index=False)
                        dump(folder/'validation.json', {'utc': utc(), 'manual_sklearn_cost_loss_exact': True, 'baseline_metric_reconciled': True, 'save_load_order_exact': True, 'leaf_error': err})
                    if full and not (folder/'application.json').exists():
                        target = pd.read_parquet(HOME/f'rows_s2_{line}.parquet', columns=['row_id', 'year', 'is_test'])
                        tx = pd.read_parquet(HOME/f'matrix_s2_{line}.parquet'); keep = ~target.is_test
                        target = target.loc[keep].reset_index(drop=True); tx = tx.loc[keep].reset_index(drop=True)
                        assert target.year.isin([2023, 2024]).all()
                        tx = attach(tx, target, pd.read_parquet(INPUT/f'weather_s2_historical_{line}.parquet'))
                        assert list(tx) == list(x)
                        raw = model.predict(x, raw_score=True, num_threads=2); ww = rows.exposure_model.to_numpy(float)
                        center = float(logsumexp(raw, b=ww)-np.log(ww.sum()))
                        independent = math.log(math.fsum(np.exp(raw)*ww)/math.fsum(ww))
                        assert abs(center-independent) < 1e-12 and abs(np.average(np.exp(raw-center), weights=ww)-1) < 2e-12
                        applied = model.predict(tx, raw_score=True, num_threads=2)
                        loaded = lgb.Booster(model_file=str(folder/'model.txt')); sample = np.unique(np.linspace(0, len(tx)-1, 32, dtype=int))
                        assert np.array_equal(applied[sample], loaded.predict(tx.iloc[sample], raw_score=True, num_threads=2))
                        assert np.array_equal(applied[sample[::-1]], loaded.predict(tx.iloc[sample[::-1]], raw_score=True, num_threads=2))
                        err = float(np.max(np.abs(previous.leaf_sum(loaded, tx.iloc[sample[:6]])-applied[sample[:6]]))); assert err < 1e-10
                        target['raw_log_rate'] = applied+initial; target['log_relative_A1S'] = applied-center
                        assert np.isfinite(target[['raw_log_rate', 'log_relative_A1S']].to_numpy()).all()
                        target.to_parquet(folder/'historical_components.parquet', index=False)
                        dump(folder/'application.json', {'utc': utc(), 'source_center': center, 'historical_rows': len(target), 'future2025inference': 0,
                            'source_normalizer_scalar_exact': True, 'save_load_order_exact': True, 'leaf_error': err, 'components_sha256': w.sha(folder/'historical_components.parquet')})
                        del tx, target
                    del model; gc.collect()
                    if time.monotonic()-start >= 45*60:
                        checkpointed = True; state('P36checkpoint_between_completed_fits', None); return
                del native, x, rows, part; gc.collect()
            if not full and not (OUT/'source_veto.json').exists(): veto()
        result = w.read(OUT/'source_veto.json'); outputs = {}
        if result['all_pass']:
            for line in LINES:
                fs = [pd.read_parquet(OUT/f'{line}_seed{seed}_full/historical_components.parquet') for seed in SEEDS]
                assert all(np.array_equal(f.row_id, fs[0].row_id) for f in fs)
                z = fs[0][['row_id', 'year', 'is_test']].copy()
                for name in ['raw_log_rate', 'log_relative_A1S']: z[name] = np.mean([f[name].to_numpy() for f in fs], axis=0)
                path = OUT/f'historical_{line}_three_seed.parquet'; z.to_parquet(path, index=False); outputs[w.rel(path)] = w.sha(path)
        check(); attempts = len(list(OUT.glob('*/fit_invoked.json'))); assert attempts == (18 if result['all_pass'] else 9)
        report = {'author': 'Codex', 'utc': utc(), 'status': 'P36source_complete_not_admitted' if result['all_pass'] else 'P36source_veto_failed_no_full_refit',
            'source_veto_all_pass': result['all_pass'], 'source_veto': result['results'], 'new_source_fits': attempts, 'new_source_normalizers': 9 if result['all_pass'] else 0,
            'new_C0_fits': 0, 'new_target_fits': 0, 'new_target_scores': 0, 'new2025inference': 0, 'new_submissions': 0,
            'outputs': outputs, 'plan_sha256': w.sha(PLAN), 'B00_all_alternatives_preserved': True, '2024_open': True, 'goal_achieved': False}
        dump(OUT/'report.json', report); state(report['status'], None); print(json.dumps(report), flush=True)
    finally:
        if not (OUT/'report.json').exists() and not checkpointed: state('P36unfinished_reconcile_before_resume', None)


def close():
    assert not (OUT/'completion_receipt.json').exists(); check(); report = w.read(OUT/'report.json'); plan = w.read(PLAN)
    assert len(list(OUT.glob('*/fit_invoked.json'))) == len(list(OUT.glob('*/fit_record.json'))) == report['new_source_fits']
    for record_path in OUT.glob('*/fit_record.json'):
        a = w.read(record_path); key, kind = record_path.parent.name.rsplit('_', 1)
        assert a['parameters'] == plan['parameters'][key] and a['current_iteration'] == plan['rounds'][key]
        assert a['model_sha256'] == w.sha(record_path.parent/'model.txt') and a['plan_sha256'] == w.sha(PLAN)
        assert a['initial_base'] == plan['reused_initial_bases'][key][kind]
    replay = []
    for line in LINES:
        y = pd.read_parquet(HOME/f'rows_s1_{line}.parquet', columns=['T0']).T0.to_numpy(float)
        part = pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet', columns=['internal_validation'])
        y = y[part.internal_validation.to_numpy(bool)]
        frames = [pd.read_parquet(OUT/f'{line}_seed{seed}_inner/validation_predictions.parquet') for seed in SEEDS]
        losses = {}
        for kind in ['old', 'new']:
            logs = [math.fsum(v)/3 for v in zip(*[f[kind].to_numpy(float) for f in frames])]
            losses[kind] = math.fsum(4*a/math.exp(.5*b)-8*math.sqrt(a)+4*math.exp(.5*b) for a, b in zip(y, logs))/len(y)
        original = next(x for x in report['source_veto'] if x['line'] == line)
        assert math.isclose(losses['old'], original['baseline_mean_deviance'], rel_tol=2e-13)
        assert math.isclose(losses['new'], original['candidate_mean_deviance'], rel_tol=2e-13)
        replay.append({'line': line, 'relative_loss': losses['new']/losses['old']-1, 'pass': losses['new'] <= 1.002*losses['old'], 'scalar_ensemble_loss_exact': True})
    assert all(x['pass'] for x in replay) == report['source_veto_all_pass']
    dump(OUT/'scalar_replay.json', {'author': 'Codex', 'utc': utc(), 'checks': replay, 'new_fits': 0, 'new_inference': 0, 'new_resampling': 0})
    next_unit = ('P37: preregister the whole original50/50S2/H1target assay with P36source only changed; keep nestedC0/N3/H1and original qsource/evaluation mapping. Reuse verified source-swap adapter and test only changed bindings, not old fixtures. Preserve all pooled/transfer/cohort/tail/31group gates; no2025inference or CSVbefore acceptance.' if report['source_veto_all_pass'] else
        'Keep the complete source veto; no full refit, favorable-line rescue, weather feature search or target scoring. Review a distinct documented modeling failure before another preregistered recipe, preserving all adverse evidence and the private-first objective.')
    text = '# P36: clima anual en el árbol fuente\n\nCodex, '+utc()+'.\n\n'
    text += ('Los tres vetos fuente pasan; se completaron los nueve refits permitidos y se guardaron componentes históricos. Falta comprobar el algoritmo destino completo.' if report['source_veto_all_pass'] else 'El veto conjunto fuente falla. Se conservan los nueve ajustes internos y no se hacen refits completos o evaluación destino.')
    text += '\n\n| Ramo | Cambio relativo de desviación fuente | Veto |\n|---|---:|---|\n'
    for a in replay: text += f"| {a['line']} | {100*a['relative_loss']:+.4f}% | {a['pass']} |\n"
    text += ('\nSe agregaron solo siete medidas climáticas oficiales del año, manteniendo capacidad y rondas originales por semilla, costes, exposición y grupos. '
        'Todas las semillas entraron en el ensemble geométrico. Pasar admite hasta0,2%de deterioro y no equivale a mejorar. '
        'Los precedentes E13/T7/T8y los fallos P33/P34se conservan. No hay ponderación de dominio o nueva curva C0.\n\n'
        'Se comprobaron los argumentos reales de entrenamiento contra contaminación de etiquetas, exposición y clima retenidos; los modelos se guardaron antes de validar. '
        'Guardado/carga, inversión de orden, suma independiente de hojas y desviación por otro método coincidieron. El cierre reproduce las predicciones guardadas por suma escalar, sin ajustes o inferencias nuevas. '
        'La fuente tiene un único holdout ya adaptativo y un enlace de observación con ancestros fuente completos; el clima es condicional y no un pronóstico disponible al cotizar. '
        'No se acredita mejora privada o revisión profesional independiente. Esta distinción sigue Gobernanza IAA§2.8y Documentación§3.\n\n'
        'Ajustes nuevos: '+str(report['new_source_fits'])+'; normalizadores fuente: '+str(report['new_source_normalizers'])+'. Cero C0, calibraciones/scores destino, inferencias2025o envíos. '
        'B00/F3c/alternativas conservados,2024abierto adaptativo. Evidencia: '+w.rel(OUT/'report.json')+' y '+w.rel(OUT/'scalar_replay.json')+'.\n\nPróximo: '+next_unit+'\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    p = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex', '--id', 'COD-S2-20261026-PRIVADA-P36-CLIMA-FUENTE-RESULTADO', '--asunto', 'P36: clima en la fuente, veto y replay completos; aún sin entrega', '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': utc(), 'status': 'P36closed_not_admitted', 'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'),
        'document': w.rel(DOC), 'source_veto_all_pass': report['source_veto_all_pass'], 'new_source_fits': report['new_source_fits'],
        'new_submissions': 0, 'forum': json.loads(p.stdout), 'next_unit': next_unit, 'goal_achieved': False, '2024_open': True}
    archive = R/'privado'/('corte_P36_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(INDEX, receipt, archive); w.update(R/'registro/semana2_mision_privada_actual.json', {'P36': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P36_source': receipt, 'next_unit': next_unit}, archive)
    statepath = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(statepath)['week_2_mission017_phase2_20261025']; own.update(private_P36_source=receipt, next_unit=next_unit)
    w.update(statepath, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P36: clima en el árbol fuente\n\nCodex, '+receipt['utc']+'. Veto fuente conjunto='+str(report['source_veto_all_pass'])+'; ajustes='+str(report['new_source_fits'])+'. Replay escalar guardado, cero C0/inferencias2025/envíos. B00/F3c/alternativas conservados. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_source_weather_index': w.rel(INDEX), 'week_2_private_source_weather_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt); print(json.dumps({'closed': True, 'source_veto_pass': report['source_veto_all_pass'], 'forum': receipt['forum']}))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf8'); parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'run', 'resume', 'close']); args = parser.parse_args()
    with threadpool_limits(limits=2):
        if args.mode in ['prepare', 'close']: {'prepare': prepare, 'close': close}[args.mode]()
        else: run(resume=args.mode == 'resume')
