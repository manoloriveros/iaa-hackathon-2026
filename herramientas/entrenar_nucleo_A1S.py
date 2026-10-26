"""Nueva alternativa A1S: fuente solamente, receta fija y puntos de continuación."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import gc
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = Path('C:/dev/Hakaton')
R = ROOT / 'Hackaton/Repositorio_IAA2026'
BASE = R / 'privado/semana2/mision017_fase2'
HOME = BASE / 'A1S_nucleo_20261026_v1'
OUT = HOME / 'source_models'
PLAN = R / 'registro/semana2_mision017_A1S_fuente_plan_v1.json'
PHASE = R / 'registro/semana2_mision017_fase2_actual.json'
COUNTER = R / 'registro/semana2_contadores_propios_actual.json'
INDEX = R / 'registro/semana2_mision017_A1S_actual.json'
sys.path.insert(0, str(ROOT / 'Preparación/.cache/parquet-reader'))
sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.special import logsumexp
from sklearn.metrics import mean_tweedie_deviance
from threadpoolctl import threadpool_limits

spec = importlib.util.spec_from_file_location('A1S_state_writer', R / 'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
LINES = ['motor', 'buildings', 'contents']
SEEDS = [11, 12, 13]
PARAMS = dict(objective='tweedie', metric='tweedie', tweedie_variance_power=1.5,
              learning_rate=0.02, num_leaves=31, min_data_in_leaf=1000,
              feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
              lambda_l2=10.0, min_data_per_group=1000, cat_smooth=50,
              verbosity=-1, deterministic=True, force_row_wise=True, num_threads=2)


def utc():
    return datetime.now(timezone.utc).isoformat()


def dump(path, value):
    encoded = json.dumps(value, ensure_ascii=False, indent=2)
    tmp = path.with_name(path.name + '.A1S.tmp')
    with tmp.open('x', encoding='utf8') as f:
        f.write(encoded)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def sources():
    p = [Path(__file__), HOME / 'report.json', HOME / 'partition_source/report.json']
    for line in LINES:
        p += [HOME / f'{kind}_{market}_{line}.parquet'
              for kind in ['matrix', 'rows'] for market in ['s1', 's2']]
        p.append(HOME / f'partition_source/folds_{line}.parquet')
    return {w.rel(x): w.sha(x) for x in p}


def scalar_checks():
    y = np.array([0., 1., 4., 100., 0.])
    e = np.array([.3, .9, 1., .1, .7])
    raw = np.array([-.2, .4, 1.1, -.3, .8])
    base = np.log(y.sum() / e.sum())
    mu = np.exp(raw + np.log(e) + base)
    loss = np.mean(2 * y / np.sqrt(mu) + 2 * np.sqrt(mu))
    independent = .5 * mean_tweedie_deviance(y, mu, power=1.5) + 4 * np.mean(np.sqrt(y))
    assert abs(loss - independent) < 1e-12
    center = logsumexp(raw, b=e) - np.log(e.sum())
    assert abs(np.average(np.exp(raw - center), weights=e) - 1) < 1e-14
    assert np.allclose(mu, np.exp(raw) * e * np.exp(base), rtol=2e-15)
    return {'tweedie_loss_two_methods': True, 'offset_exposure_once': True,
            'relative_center_unit_weighted_mean': True, 'synthetic_model_fits': 0}


def register():
    assert not PLAN.exists() and not OUT.exists()
    phase = w.read(PHASE)
    assert phase.get('active_execution') is None and not phase.get('active_jobs')
    partition = w.read(HOME / 'partition_source/report.json')
    assert partition['status'] == 'source_partition_complete_no_labels_or_fit'
    assert partition['all_shared_customer_address_edges_protected']
    assert partition['transitive_and_reversal_synthetic_passed']
    OUT.mkdir()
    plan = {'author': 'Codex', 'utc': utc(), 'candidate': 'A1S',
            'hypothesis': 'A source-only, saved and reproducible complete A1-family core permits evaluating full calibrated prices instead of treating residual gains on the incomplete G3 surrogate as gains over delivered F3c.',
            'necessity': 'Corrected historical A1 three-seed models, per-row relativities and source round metadata were not found in the already archived bounded inventory. This is a NEW explicit alternative, not exact historical A1 reproduction.',
            'market': 'Developed source2021-2024 only for all fitted tree labels, offsets, categories and source early stopping. Emerging2023/2024/2025 covariates for application only at this stage.',
            'objective': 'T0 incurred net recoveries, no reserve adjustment; log existing source-only e_cost plus source training base as init_score, no second exposure.',
            'inputs': 'Existing frozen A1S matrices and source T0/e_cost, no reconstruction or new reporting curves.',
            'partition': {'report': w.rel(HOME / 'partition_source/report.json'),
                          'inner_held_fold': partition['inner_held_fold'],
                          'grouping': partition['group_definition']},
            'parameters': PARAMS, 'seeds': SEEDS, 'source_years': [2021, 2022, 2023, 2024],
            'early_stopping': {'max_rounds': 4000, 'patience': 400, 'metric': 'tweedie',
                               'initial_base_learned_only_on_inner_training': True,
                               'one_round_choice_per_line_seed': True},
            'full_refit': 'Same parameters/seed; selected source-only round count; full-source log(sumT0/sum_e_cost) initialization.',
            'relative': 'Raw full Booster delta minus log source exposure_model-weighted mean exp(delta), per seed. Geometric mean across all3seeds with no seed selection.',
            'history': 'Notifications irrespective of eventual status, before min(period_start,2024-12-31); observed history duration clipped at same cutoff; no future weather.',
            'budget': {'source_internal_earlystop_fits': 9, 'source_full_refits': 9,
                       'total_real_model_fit_calls': 18, 'new_C0_fits': 0,
                       'new_target_calibration_fits': 0, 'new_target_scores': 0,
                       'final_test_price_CSVs': 0, 'new_submissions': 0},
            'criteria': ['All input SHA unchanged and schemas/key ordering exact',
                         'Every started fit accounted and every completed model saved before downstream checks',
                         'Held source LightGBM Tweedie metric reproduced by manual loss and sklearn deviance',
                         'Save/load, row-order and independent leaf-sum checks; exposure applied exactly once',
                         'All finite positive relativities; source exposure-weighted mean one per model',
                         'Fixed three-seed aggregation without label/score-based seed selection'],
            'predictive_admission': 'NONE from this source stage. Next separately preregister complete group-held emerging calibration and comparison with stored baselines, per year/line/business, concentration and level sensitivity. Do not infer improvement over publicF3c from G3 alone.',
            'limits': ['Inner early stopping is conditional on whole-source frozen observation link; not independent end-to-end confirmation',
                       'Source2024 and full-snapshot histories are retrospective development inputs, not prospective2023 forecasting',
                       'Undated master snapshots, reporting tail and reserve adequacy remain assumptions',
                       'Emerging2024 is explicitly open/adaptive development, not pristine holdout',
                       'Stored full-model future relativities are components, not validated final prices or permission to submit'],
            'max_cycle_minutes': 45, 'checkpoint': 'Finish current fit, then yield between fits; never automatically repeat an incomplete attempted fit.',
            'B00_all_alternatives_preserved': True, '2024_open': True,
            'preflight': scalar_checks(), 'sources': sources()}
    dump(PLAN, plan)
    body = OUT / 'forum_previo.md'
    body.write_text('Codex. Registro A1S como alternativa nueva de la familia A1, con matrices y enlace de exposición fuente ya fijados. '
        'La partición por componentes cliente/dirección contiene476.444grupos, máximo37filas; reserva aproximadamente20%sin leer respuestas para elegirla. '
        'Presupuesto cerrado:9ajustes internos y9refits fuente, semillas11/12/13, Tweedie1,5, parámetros fijos, máximo4.000rondas y paciencia400. '
        'La base inicial interna usa solo su subconjunto de ajuste; las rondas no miran respuestas emergentes. '
        'Se guardará cada modelo, relatividades por fila y media geométrica fija de semillas. Ningún C0 nuevo ni score emergente en esta etapa. '
        'No es reproducción exacta ni certificación del A1 legado: faltan sus modelos/rondas y aquí se declara un enlace fuente-only e historia conocida sin aceptación futura. '
        'La evaluación interna está condicionada al enlace de observación fuente existente. La validación global de precios completos se registrará después por grupos emergentes. '
        'B00/F3c0,16914y alternativas intactos;2024abierto y adaptativo. No se genera CSV de entrega ni se consume cupo. Plan/hash: '+w.rel(PLAN)+'.', encoding='utf8')
    result = subprocess.run([sys.executable, str(ROOT / 'Hackaton/Semana 2/Foro/comentar.py'),
        '--autor', 'Codex', '--id', 'COD-S2-20261026-MISION017-A1S-FUENTE-PREVIO',
        '--asunto', 'A1S: receta fuente fija, grupos y18ajustes presupuestados', '--cuerpo', str(body)],
        check=True, capture_output=True, text=True, encoding='utf8')
    registration = {'utc': utc(), 'plan_sha256': w.sha(PLAN), 'forum': json.loads(result.stdout)}
    dump(OUT / 'registration.json', registration)
    update_state('source_recipe_registered_no_fit', None)
    print(json.dumps(registration, ensure_ascii=True), flush=True)


def update_state(status, execution):
    stamp = datetime.now(timezone.utc)
    archive = OUT / 'state_cuts' / (stamp.strftime('%Y%m%dT%H%M%S%fZ'))
    archive.mkdir(parents=True)
    records = sorted(OUT.glob('*/fit_record.json'))
    attempted = sorted(OUT.glob('*/fit_invoked.json'))
    receipt = dict(w.read(INDEX))
    receipt.update(utc=stamp.isoformat(), status=status, plan=w.rel(PLAN), plan_sha256=w.sha(PLAN),
                   source_output=w.rel(OUT), source_attempts=len(attempted),
                   source_completed_fits=len(records), execution=execution,
                   new_C0_fits=0, new_scores=0, new_final_test_prices=0, new_submissions=0,
                   next_unit='Finish saved A1S source model checkpoints, then preregister complete target group-held calibrated comparison; do not repeat earlier G3 residual trials.')
    w.update(INDEX, receipt, archive)
    phase = w.read(PHASE)
    counter = w.read(COUNTER)
    old = counter.get('phase2_A1S_source', {})
    keys = [p.parent.name for p in attempted]
    counted = old.get('counted_fit_keys', [])
    assert set(counted).issubset(keys)
    added = len(set(keys) - set(counted))
    w.update(COUNTER, {'as_of_utc': stamp.isoformat(),
        'cumulative_price_base_fits': counter['cumulative_price_base_fits'] + added,
        'phase2_A1S_source': {'counted_fit_keys': keys, 'attempts': len(keys),
                              'completed': len(records), 'plan': w.rel(PLAN),
                              'new_C0_fits': 0, 'note': 'Counts actual fit invocation checkpoints including failed/interrupted attempts, not just saved full models.'}}, archive)
    w.update(PHASE, {'utc': stamp.isoformat(), 'A1S_core': receipt,
                     'new_price_fits': phase['new_price_fits'] + added,
                     'active_execution': execution, 'active_jobs': [] if execution is None else [execution],
                     'next_unit': receipt['next_unit'], '2024_open': True, '2024_closed': False}, archive)
    state = ROOT / 'Preparación/ESTADO_PROYECTO.json'
    existing = w.read(state)['week_2_mission017_phase2_20261025']
    existing.update(A1S_core=receipt, next_unit=receipt['next_unit'], active_jobs=[] if execution is None else [execution])
    w.update(state, {'week_2_mission017_phase2_20261025': existing,
                     'week_2_mission017_phase2_execution': execution}, archive)


def fit_once(folder, params, data, rounds, valid=None, initial_base=None):
    assert not (folder / 'fit_invoked.json').exists(), 'Attempt exists: reconcile; no automatic retraining.'
    dump(folder / 'fit_invoked.json', {'utc': utc(), 'pid': os.getpid(), 'rounds_limit': rounds, 'initial_base': initial_base})
    update_state('source_training_running', {'pid': os.getpid(), 'started_utc': w.read(OUT / 'started.json')['utc'], 'checkpoint': folder.name})
    started = time.monotonic()
    def progress(env):
        if (env.iteration + 1) % 100 == 0:
            dump(folder / 'progress.json', {'utc': utc(), 'iteration': env.iteration+1,
                                           'elapsed_seconds': time.monotonic()-started,
                                           'evaluation': [[x[0], x[1], float(x[2])] for x in env.evaluation_result_list]})
        if (env.iteration + 1) % 500 == 0:
            print(json.dumps({'fit': folder.name, 'iteration': env.iteration+1, 'seconds': round(time.monotonic()-started, 1)}), flush=True)
    callbacks = [progress]
    if valid is not None:
        callbacks.append(lgb.early_stopping(400, verbose=False))
    try:
        model = lgb.train(params, data, num_boost_round=rounds,
                          valid_sets=None if valid is None else [valid],
                          valid_names=None if valid is None else ['source_internal'], callbacks=callbacks)
        model.save_model(str(folder / 'model.txt'))
        record = {'utc': utc(), 'pid': os.getpid(), 'parameters': params,
                  'best_iteration': int(model.best_iteration), 'current_iteration': int(model.current_iteration()),
                  'best_score': model.best_score, 'seconds': time.monotonic()-started,
                  'initial_base': initial_base, 'model_sha256': w.sha(folder / 'model.txt'),
                  'lightgbm_version': lgb.__version__, 'plan_sha256': w.sha(PLAN)}
        dump(folder / 'fit_record.json', record)
        update_state('source_training_running', {'pid': os.getpid(), 'started_utc': w.read(OUT / 'started.json')['utc'], 'checkpoint': folder.name+' saved'})
        print(json.dumps({'completed': folder.name, 'rounds': model.current_iteration(), 'seconds': round(record['seconds'], 1)}), flush=True)
        return model
    except BaseException as error:
        dump(folder / 'fit_failure.json', {'utc': utc(), 'error_type': type(error).__name__, 'error': str(error), 'seconds': time.monotonic()-started})
        raise


def leaf_sum(model, x):
    leaf = model.predict(x, pred_leaf=True, num_threads=2)
    total = np.zeros(len(x))
    for j, tree in enumerate(model.dump_model()['tree_info']):
        values = {}
        def visit(node):
            if 'leaf_index' in node:
                values[node['leaf_index']] = node['leaf_value']
            else:
                visit(node['left_child']); visit(node['right_child'])
        visit(tree['tree_structure'])
        total += np.array([values[int(k)] for k in leaf[:, j]])
    return total


def validate_inner(folder, model, x, rows, mask):
    if (folder / 'validation.json').exists():
        return
    record = w.read(folder / 'fit_record.json')
    raw = model.predict(x.loc[mask], raw_score=True, num_threads=2)
    y = rows.T0.to_numpy(float)[mask]
    mu = np.exp(raw + np.log(rows.e_cost.to_numpy(float)[mask]) + record['initial_base'])
    manual = float(np.mean(2*y/np.sqrt(mu) + 2*np.sqrt(mu)))
    independent = float(.5*mean_tweedie_deviance(y, mu, power=1.5) + 4*np.mean(np.sqrt(y)))
    builtin = record['best_score']['source_internal']['tweedie']
    assert abs(manual/builtin - 1) < 2e-6, (manual, builtin)
    assert abs(manual/independent - 1) < 1e-12
    baseline = np.full(len(y), y.mean())
    d2 = 1 - mean_tweedie_deviance(y, mu, power=1.5) / mean_tweedie_deviance(y, baseline, power=1.5)
    dump(folder / 'validation.json', {'utc': utc(), 'loss_manual': manual,
         'loss_sklearn_conversion': independent, 'loss_lightgbm': builtin,
         'conditional_source_internal_D2': float(d2), 'target_scores': 0,
         'source_internal_rows': len(y), 'conditional_on_frozen_source_observation_link': True})


def apply_full(folder, model, x, rows, target_x, target_rows):
    if (folder / 'application.json').exists():
        return
    record = w.read(folder / 'fit_record.json')
    loaded = lgb.Booster(model_file=str(folder / 'model.txt'))
    raw = model.predict(x, raw_score=True, num_threads=2)
    e = rows.exposure_model.to_numpy(float)
    center = float(logsumexp(raw, b=e) - np.log(e.sum()))
    relative = raw-center
    assert abs(np.average(np.exp(relative), weights=e) - 1) < 2e-12
    target_raw = model.predict(target_x, raw_score=True, num_threads=2)
    sample = np.unique(np.linspace(0, len(target_x)-1, 32, dtype=int))
    assert np.array_equal(target_raw[sample], loaded.predict(target_x.iloc[sample], raw_score=True, num_threads=2))
    assert np.array_equal(target_raw[sample[::-1]], loaded.predict(target_x.iloc[sample[::-1]], raw_score=True, num_threads=2))
    independent = leaf_sum(loaded, target_x.iloc[sample[:6]])
    leaf_error = float(np.max(np.abs(independent-target_raw[sample[:6]])))
    assert leaf_error < 1e-10
    mu = np.exp(raw + np.log(rows.e_cost.to_numpy(float)) + record['initial_base'])
    assert np.isfinite(mu).all() and (mu > 0).all()
    assert np.isfinite(target_raw).all() and np.isfinite(np.exp(target_raw-center)).all()
    source = rows[['row_id', 'year']].copy()
    source['raw_delta'] = raw; source['log_relative'] = relative; source['conditional_source_mu'] = mu
    target = target_rows[['row_id', 'year', 'is_test']].copy()
    target['raw_delta'] = target_raw; target['log_relative'] = target_raw-center
    source.to_parquet(folder / 'source_components.parquet', index=False)
    target.to_parquet(folder / 'target_components.parquet', index=False)
    dump(folder / 'application.json', {'utc': utc(), 'center': center,
        'source_prediction_rows': len(source), 'target_component_prediction_rows': len(target),
        'target_test_component_rows': int(target.is_test.sum()), 'final_test_prices': 0,
        'save_load_and_order_exact': True, 'independent_leaf_sum_max_abs_error': leaf_error,
        'source_weighted_relative_mean': float(np.average(np.exp(relative), weights=e)),
        'outputs': {n: w.sha(folder/n) for n in ['source_components.parquet', 'target_components.parquet']}})


def run(resume=False):
    assert not (OUT / 'report.json').exists(), 'Completed source unit; do not repeat.'
    registration = w.read(OUT / 'registration.json')
    assert w.sha(PLAN) == registration['plan_sha256']
    plan = w.read(PLAN)
    assert sources() == plan['sources'], 'Source changed since registration; no training.'
    if resume:
        import psutil
        previous = w.read(OUT / 'started.json')
        if psutil.pid_exists(previous['pid']):
            process = psutil.Process(previous['pid'])
            assert not any(str(Path(__file__)) == str(Path(a)) for a in process.cmdline()), 'Previous producer still alive.'
        assert not any((f.parent / 'fit_record.json').exists() is False for f in OUT.glob('*/fit_invoked.json')), 'Incomplete attempted fit must be reconciled explicitly.'
        dump(OUT / ('resume_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'), {'utc': utc(), 'pid': os.getpid(), 'previous': previous})
    else:
        assert not (OUT / 'started.json').exists(), 'Reconcile current execution before resume.'
        dump(OUT / 'started.json', {'utc': utc(), 'pid': os.getpid(), 'plan_sha256': w.sha(PLAN)})
    start = time.monotonic()
    with threadpool_limits(limits=2):
        for line in LINES:
            x = pd.read_parquet(HOME / f'matrix_s1_{line}.parquet')
            rows = pd.read_parquet(HOME / f'rows_s1_{line}.parquet')
            tx = pd.read_parquet(HOME / f'matrix_s2_{line}.parquet')
            tr = pd.read_parquet(HOME / f'rows_s2_{line}.parquet')
            partition = pd.read_parquet(HOME / f'partition_source/folds_{line}.parquet')
            assert len(x) == len(rows) and len(tx) == len(tr)
            assert np.array_equal(partition.row_id, rows.row_id)
            assert list(x) == list(tx) and not {'T0','reserve','claim_count','e_cost'}.intersection(tx)
            assert not {'T0', 'T0_cents', 'reserve', 'e_cost'}.intersection(tr)
            mask = partition.internal_validation.to_numpy(bool)
            y = rows.T0.to_numpy(float); e = rows.e_cost.to_numpy(float)
            assert (y >= 0).all() and (e > 0).all() and np.isfinite(e).all()
            inner_base = float(np.log(y[~mask].sum()/e[~mask].sum()))
            full_base = float(np.log(y.sum()/e.sum()))
            for seed in SEEDS:
                params = dict(PARAMS, seed=seed)
                for stage in ['inner', 'full']:
                    folder = OUT / f'{line}_seed{seed}_{stage}'
                    folder.mkdir(exist_ok=True)
                    if not (folder / 'fit_record.json').exists():
                        if stage == 'inner':
                            data = lgb.Dataset(x.loc[~mask], label=y[~mask], init_score=np.log(e[~mask])+inner_base)
                            valid = lgb.Dataset(x.loc[mask], label=y[mask], init_score=np.log(e[mask])+inner_base, reference=data)
                            model = fit_once(folder, params, data, 4000, valid, inner_base)
                        else:
                            inner = w.read(OUT / f'{line}_seed{seed}_inner/fit_record.json')
                            rounds = inner['best_iteration']
                            assert 0 < rounds <= 4000
                            data = lgb.Dataset(x, label=y, init_score=np.log(e)+full_base)
                            model = fit_once(folder, params, data, rounds, initial_base=full_base)
                        del data
                    else:
                        record = w.read(folder / 'fit_record.json')
                        assert record['plan_sha256'] == w.sha(PLAN) and record['model_sha256'] == w.sha(folder / 'model.txt')
                        model = lgb.Booster(model_file=str(folder / 'model.txt'))
                    if stage == 'inner':
                        validate_inner(folder, model, x, rows, mask)
                    else:
                        apply_full(folder, model, x, rows, tx, tr)
                    del model
                    gc.collect()
                    if time.monotonic()-start > 45*60:
                        update_state('source_training_checkpoint_between_fits', None)
                        print(json.dumps({'checkpoint': folder.name, 'status': 'cycle_checkpoint_not_complete', 'attempts': len(list(OUT.glob('*/fit_invoked.json')))}), flush=True)
                        return
            del x, rows, tx, tr, partition
            gc.collect()
    assert len(list(OUT.glob('*/fit_record.json'))) == 18
    outputs = {}
    for line in LINES:
        for market in ['source', 'target']:
            frames = [pd.read_parquet(OUT / f'{line}_seed{s}_full/{market}_components.parquet') for s in SEEDS]
            assert all(np.array_equal(f.row_id, frames[0].row_id) for f in frames)
            out = frames[0].drop(columns=['raw_delta', 'log_relative', 'conditional_source_mu'], errors='ignore').copy()
            out['log_relative_A1S'] = np.mean(np.stack([f.log_relative.to_numpy() for f in frames]), axis=0)
            assert np.isfinite(out.log_relative_A1S).all()
            name = f'{market}_{line}_three_seed_components.parquet'
            out.to_parquet(OUT/name, index=False)
            outputs[name] = {'sha256': w.sha(OUT/name), 'rows': len(out)}
    assert sources() == plan['sources']
    records = {p.parent.name: w.read(p) for p in sorted(OUT.glob('*/fit_record.json'))}
    validation = {p.parent.name: w.read(p) for p in sorted(OUT.glob('*/validation.json'))}
    applications = {p.parent.name: w.read(p) for p in sorted(OUT.glob('*/application.json'))}
    report = {'author': 'Codex', 'utc': utc(), 'status': 'source_models_and_components_complete_not_predictively_admitted',
              'plan': w.rel(PLAN), 'plan_sha256': w.sha(PLAN), 'new_source_model_fits': 18,
              'source_earlystop_fits': 9, 'source_full_refits': 9, 'new_C0_fits': 0,
              'new_target_scores': 0, 'new_final_test_prices': 0, 'new_submissions': 0,
              'records': records, 'conditional_source_validation': validation, 'applications': applications,
              'outputs': outputs, '2024_open': True, 'B00_all_alternatives_preserved': True,
              'limits': plan['limits']}
    dump(OUT/'report.json', report)
    update_state('source_complete_target_calibration_pending', None)
    print(json.dumps({'complete': True, 'models_saved': 18, 'rounds': {k:v['current_iteration'] for k,v in records.items()},
                      'outputs': outputs, 'target_scores': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['register', 'run', 'resume'])
    arg = parser.parse_args()
    if arg.mode == 'register':
        register()
    else:
        try:
            run(arg.mode == 'resume')
        except BaseException as error:
            if OUT.exists():
                dump(OUT / ('execution_failure_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'),
                     {'utc': utc(), 'pid': os.getpid(), 'type': type(error).__name__, 'error': str(error)})
                update_state('source_execution_failed_reconcile_without_retraining', None)
            raise
